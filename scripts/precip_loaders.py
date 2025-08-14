# precip_loaders.py
# -*- coding: utf-8 -*-
"""
Utilities to load and standardize precipitation from GPM and MPAS.

Goals
-----
- Put **GPM** (typically mm/h instantaneous or rate) and **MPAS** (cumulative mm)
  on the same **rate base** (default: mm/h; option: mm/day).
- Be robust to variable time cadence (e.g., MPAS 3-hourly) and accumulator resets.
- Provide time-mean fields for spatial spectral analysis, or full time series.

Typical usage
-------------
>>> from precip_loaders import load_gpm_rate, load_mpas_rate
>>> gpm  = load_gpm_rate("GPM.nc",  out_unit="mm/h",  time_mean=True)
>>> mpas = load_mpas_rate("MPAS.nc", out_unit="mm/h", time_mean=True)
# gpm and mpas are now directly comparable (same unit).
"""

from __future__ import annotations
import os
import numpy as np
import xarray as xr


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pick_time_name(ds: xr.Dataset) -> str:
    """
    Return a sensible time dimension/coordinate name present in *ds*.

    Order of attempts: "time", "Time", "valid_time".

    Raises
    ------
    KeyError
        If no suitable time dimension/coordinate is found.
    """
    for name in ("time", "Time", "valid_time"):
        if name in ds.dims or name in ds.coords:
            return name
    raise KeyError("No time dimension/coord named 'time', 'Time', or 'valid_time' found.")


def _hours_between(times: xr.DataArray, tname: str) -> xr.DataArray:
    """
    Compute Δt in hours between consecutive time stamps.

    Parameters
    ----------
    times : xr.DataArray
        1D time coordinate or variable with datetime64 dtype.
    tname : str
        Name of the time dimension.

    Returns
    -------
    xr.DataArray
        Length N-1 array (aligned to `diff`) with time intervals in hours.
    """
    dt = times.diff(tname)
    # Convert timedeltas to seconds → hours
    return (dt / np.timedelta64(1, "s")).astype("float64") / 3600.0


def _to_mm_per_hour(da: xr.DataArray) -> xr.DataArray:
    """
    Convert common precipitation rate units to mm/h using `da.attrs['units']`.

    Recognized units (case/spacing-insensitive):
        - "mm/h" or "mm/hr"      → as-is
        - "mm/day" or "mm/d"     → divided by 24
        - "kg m-2 s-1" variants  → multiplied by 3600 (1 kg m-2 == 1 mm)

    Parameters
    ----------
    da : xr.DataArray
        Precipitation variable with a 'units' attribute.

    Returns
    -------
    xr.DataArray
        Same shape as input, converted to mm/h.

    Raises
    ------
    ValueError
        If the units attribute is missing or unrecognized.
    """
    units = (da.attrs.get("units") or "").lower().replace(" ", "")
    if units in ("mm/hr", "mm/h"):
        return da
    if units in ("mm/day", "mm/d"):
        return da / 24.0
    if units in ("kgm-2s-1", "kgm^-2s^-1", "kg/m^2/s", "mm/s"):
        # 1 kg m-2 = 1 mm water depth; s → h
        return da * 3600.0
    raise ValueError(f"Unrecognized precip units: {da.attrs.get('units')!r}. "
                     "Please set a proper 'units' attribute.")


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------

def load_gpm_rate(
    path: str | os.PathLike,
    var_candidates: tuple[str, ...] = ("precipitation", "precipitationCal"),
    out_unit: str = "mm/h",
    time_mean: bool = True,
) -> xr.DataArray:
    """
    Load GPM precipitation and return a rate on a common base (mm/h or mm/day).

    This function:
    1) Locates one of the candidate variables (e.g., 'precipitation').
    2) Converts units to **mm/h** using the variable's 'units' attribute.
    3) Optionally converts to **mm/day** (×24).
    4) Optionally averages over time (for spatial spectral analysis).

    Parameters
    ----------
    path : str | os.PathLike
        Path to a GPM NetCDF file.
    var_candidates : tuple of str, optional
        Variable names to try in order. First match is used.
    out_unit : {"mm/h", "mm/day"}, optional
        Desired output unit base.
    time_mean : bool, optional
        If True, return the time mean (collapsing the time dimension).
        If False, return the full time series of rates.

    Returns
    -------
    xr.DataArray
        Precipitation as a rate in the requested unit, either time-mean or time-varying.

    Raises
    ------
    KeyError
        If none of the candidate variables is present.
    ValueError
        If units are missing/unrecognized or `out_unit` is invalid.
    """
    ds = xr.open_dataset(path)
    # Find a precipitation variable
    var = next((ds[v] for v in var_candidates if v in ds), None)
    if var is None:
        raise KeyError(f"None of {var_candidates} found in {path}.")

    # Standardize to mm/h
    rate_h = _to_mm_per_hour(var)

    # Convert to requested base
    out_unit_norm = out_unit.strip().lower()
    if out_unit_norm in ("mm/h", "mmhr", "mm_per_hour"):
        out = rate_h
    elif out_unit_norm in ("mm/d", "mm/day", "mm_per_day"):
        out = rate_h * 24.0
    else:
        raise ValueError("out_unit must be 'mm/h' or 'mm/day'.")

    # Time mean if requested
    tname = _pick_time_name(ds)
    return out.mean(tname) if time_mean else out


def load_mpas_rate(
    path: str | os.PathLike,
    rainc_name: str = "rainc",
    rainnc_name: str = "rainnc",
    out_unit: str = "mm/h",
    time_mean: bool = True,
    drop_negative_increments: bool = True,
) -> xr.DataArray:
    """
    Convert MPAS cumulative precipitation to a rate on a common base (mm/h or mm/day).

    MPAS typically stores accumulated precipitation (mm) in variables like 'rainc'
    (convective) and 'rainnc' (non-convective). This function:
    1) Sums these accumulators.
    2) Computes increments via `diff(time)` (mm per step).
    3) Divides by the actual time step Δt (hours) inferred from the time coordinate,
       yielding a rate in **mm/h** (robust to 3-hourly, hourly, etc.).
    4) Optionally treats accumulator resets by dropping negative increments.
    5) Optionally converts to **mm/day** (×24).
    6) Optionally averages over time.

    Parameters
    ----------
    path : str | os.PathLike
        Path to an MPAS NetCDF file containing cumulative rain fields.
    rainc_name : str, optional
        Name of the convective accumulated rain variable.
    rainnc_name : str, optional
        Name of the non-convective accumulated rain variable.
    out_unit : {"mm/h", "mm/day"}, optional
        Desired output unit base.
    time_mean : bool, optional
        If True, return the time mean (collapsing the time dimension).
        If False, return the full time series of rates (length N-1 along time).
    drop_negative_increments : bool, optional
        If True (default), negative `diff` values (typical of accumulator resets)
        are discarded (set to NaN) before averaging.

    Returns
    -------
    xr.DataArray
        Precipitation rate in the requested unit, either time-mean or time-varying.

    Raises
    ------
    KeyError
        If time coord is missing, or expected rain variables are absent.
    ValueError
        If `out_unit` is invalid.
    """
    ds = xr.open_dataset(path)
    tname = _pick_time_name(ds)

    if rainc_name not in ds or rainnc_name not in ds:
        raise KeyError(f"Expected '{rainc_name}' and '{rainnc_name}' in {path}.")

    # Accumulated precipitation (mm)
    acc = ds[rainc_name] + ds[rainnc_name]

    # Increments (mm per time interval); length N-1 along time
    inc = acc.diff(tname)

    # Δt in hours (aligns with .diff result)
    hours = _hours_between(ds[tname], tname)

    # Rate in mm/h for each interval (broadcasting handles dims)
    rate_h = inc / hours

    # Handle accumulator resets (negative diffs)
    if drop_negative_increments:
        rate_h = rate_h.where(rate_h >= 0)

    # Convert to requested base
    out_unit_norm = out_unit.strip().lower()
    if out_unit_norm in ("mm/h", "mmhr", "mm_per_hour"):
        out = rate_h
    elif out_unit_norm in ("mm/d", "mm/day", "mm_per_day"):
        out = rate_h * 24.0
    else:
        raise ValueError("out_unit must be 'mm/h' or 'mm/day'.")

    # Time mean if requested (note: time length is N-1 due to diff)
    return out.mean(tname) if time_mean else out

