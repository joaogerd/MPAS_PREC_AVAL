from __future__ import annotations
"""
Compute 2D and radial power spectra for GPM (remapped to MPAS grid) and MPAS.

This script loads:
- GPM remapped file produced by `regrid_gpm_to_mpas.py`
- MPAS precipitation (accumulators), converted to a rate via `load_mpas_rate`

Both fields are standardized to the same unit base (`mm/day` by default) to ensure
amplitude comparability. Optionally, fields can be normalized by their spatial
standard deviation to compare spectral *shape* independent of amplitude.

Outputs
-------
- A PNG figure with (optional) 2D spectra and a 1D radial spectrum comparison.
- File saved under <figs>/espectros_precipitacao_<style>.png by default.

Notes
-----
- For spatial spectral analysis, time means are typically used to get a single 2D field.
- Use `--normalize` to emphasize differences in spectral slope rather than magnitude.
"""

import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from .common import (
    resolve_paths,
    setup_logging,
    compute_spectrum,
    radial_mean,
    trim_edges,
    print_field_stats,
)
from .precip_loaders import load_mpas_rate


# --------------------------------------------------------------------------- #
# Internal utilities
# --------------------------------------------------------------------------- #
def _pick_var(ds: xr.Dataset, candidates=("precipitation_rate", "precipitation")) -> str:
    """
    Select the first matching precipitation variable present in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset.
    candidates : tuple of str, optional
        Variable names to try in order.

    Returns
    -------
    str
        Name of the first variable found in `candidates`.

    Raises
    ------
    KeyError
        If none of the candidates is present in `ds`.
    """
    for v in candidates:
        if v in ds:
            return v
    raise KeyError(f"None of {candidates} found in dataset variables: {list(ds.data_vars)}")


def _ensure_unit_mm_per_day(da: xr.DataArray) -> xr.DataArray:
    """
    Ensure precipitation rate is in mm/day.

    Parameters
    ----------
    da : xr.DataArray
        Precipitation rate with a 'units' attribute or known base.

    Returns
    -------
    xr.DataArray
        DataArray in mm/day.

    Raises
    ------
    ValueError
        If units are unexpected/unsupported.
    """
    units = (da.attrs.get("units") or "").lower().replace(" ", "")
    if units in ("mm/d", "mm/day", "mm_per_day"):
        return da
    if units in ("mm/h", "mmhr", "mm_per_hour"):
        out = da * 24.0
        out.attrs["units"] = "mm/day"
        return out
    if units == "":
        # No units: assume pipeline default (mm/h) for remapped GPM; convert to mm/day.
        out = da * 24.0
        out.attrs["units"] = "mm/day"
        return out
    raise ValueError(f"Unexpected units for precipitation rate: {da.attrs.get('units')!r}")


def _maybe_time_mean(da: xr.DataArray) -> xr.DataArray:
    """
    Reduce a time-varying field to its time mean if a 'time' dimension exists.

    Parameters
    ----------
    da : xr.DataArray
        2D field or 3D field with a leading 'time' dimension.

    Returns
    -------
    xr.DataArray
        2D time-mean field if `time` exists; otherwise input unchanged.
    """
    return da.mean("time") if "time" in da.dims else da


def _to_numpy_2d(da: xr.DataArray) -> np.ndarray:
    """
    Convert an xarray DataArray (2D) to a NumPy array, preserving shape.

    Parameters
    ----------
    da : xr.DataArray
        2D field.

    Returns
    -------
    np.ndarray
        2D array.

    Raises
    ------
    ValueError
        If `da` is not 2D after potential time-mean reduction.
    """
    if da.ndim != 2:
        raise ValueError(f"Expected 2D array, got {da.ndim}D with dims {da.dims}")
    return np.asarray(da.values)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry point: compute and plot power spectra for GPM (remapped) and MPAS.

    Command-line options
    --------------------
    --mpas : str (required)
        Path to MPAS NetCDF with accumulated precipitation (rainc + rainnc).
    --gpm-file : str, optional
        Path to remapped GPM file. If omitted, tries:
        <data_processed>/gpm_remap_to_mpas_timemean.nc
        <data_processed>/gpm_remap_to_mpas_timeseries.nc
    --unit : {'mm/day', 'mm/h'}, default 'mm/day'
        Common unit base for both datasets prior to spectra.
    --normalize : store_true
        Normalize each field by its spatial standard deviation before FFT.
        Useful to compare spectral *shape* independently of amplitude.
    --trim : int, default 0
        Number of grid points to trim from each border before FFT.
    --show-2d : store_true
        Include 2D power spectrum panels in the figure.
    --style : {'black', 'light'}, default 'black'
        Figure face color style.
    --root : str or None, default None
        Project root (auto-resolved if omitted).
    --outfile : str or None, default None
        Custom output filename (placed under <figs>/ if relative).
    """
    parser = argparse.ArgumentParser(
        description="Spatial power spectra: GPM (remapped) vs MPAS (daily)."
    )
    parser.add_argument("--mpas", required=True, help="Path to MPAS NetCDF (accumulated rain).")
    parser.add_argument("--gpm-file", default=None, help="Path to GPM remapped NetCDF.")
    parser.add_argument("--unit", choices=["mm/day", "mm/h"], default="mm/day",
                        help="Common precipitation rate unit prior to spectra.")
    parser.add_argument("--normalize", action="store_true",
                        help="Normalize each field by its spatial std before FFT.")
    parser.add_argument("--trim", type=int, default=0,
                        help="Trim N grid points from each edge before FFT.")
    parser.add_argument("--show-2d", action="store_true",
                        help="Plot 2D spectra panels in addition to radial spectra.")
    parser.add_argument("--style", choices=["black", "light"], default="black",
                        help="Figure color style.")
    parser.add_argument("--root", default=None, help="Project root (auto if omitted).")
    parser.add_argument("--outfile", default=None, help="Custom output PNG name.")
    args = parser.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    # -----------------------------
    # Load GPM (remapped → MPAS grid)
    # -----------------------------
    if args.gpm_file is not None:
        gpm_path = P.root / args.gpm_file if not str(args.gpm_file).startswith("/") else args.gpm_file
    else:
        cand1 = P.data_dir / "gpm_remap_to_mpas_timemean.nc"
        cand2 = P.data_dir / "gpm_remap_to_mpas_timeseries.nc"
        gpm_path = cand1 if cand1.exists() else cand2

    ds_gpm = xr.open_dataset(gpm_path)
    gpm_var = _pick_var(ds_gpm)

    gpm = ds_gpm[gpm_var]
    gpm = _maybe_time_mean(gpm)

    # Convert to desired base unit
    if args.unit == "mm/day":
        gpm = _ensure_unit_mm_per_day(gpm)
    else:  # mm/h
        # If it is already mm/day, convert back to mm/h; else leave as mm/h
        units = (gpm.attrs.get("units") or "").lower().replace(" ", "")
        if units in ("mm/d", "mm/day", "mm_per_day"):
            gpm = gpm / 24.0
            gpm.attrs["units"] = "mm/h"

    # -----------------------------
    # Load MPAS & convert to rate
    # -----------------------------
    out_unit = "mm/day" if args.unit == "mm/day" else "mm/h"
    mpas = load_mpas_rate(args.mpas, out_unit=out_unit, time_mean=True)

    # -----------------------------
    # Optional normalization
    # -----------------------------
    if args.normalize:
        gpm = (gpm - gpm.mean()) / (gpm.std() + 1e-12)
        mpas = (mpas - mpas.mean()) / (mpas.std() + 1e-12)
        gpm.attrs["units"] = "normalized"
        mpas.attrs["units"] = "normalized"

    # -----------------------------
    # Prepare 2D arrays and optional trimming
    # -----------------------------
    gpm2d = _to_numpy_2d(gpm)
    mpas2d = _to_numpy_2d(mpas)

    if args.trim > 0:
        gpm2d = trim_edges(gpm2d, n=args.trim)
        mpas2d = trim_edges(mpas2d, n=args.trim)

    # Diagnostics
    print_field_stats(gpm2d, label=f"GPM [{gpm.attrs.get('units', '')}]")
    print_field_stats(mpas2d, label=f"MPAS [{mpas.attrs.get('units', '')}]")

    # -----------------------------
    # Spectra
    # -----------------------------
    spec_gpm = compute_spectrum(gpm2d)
    spec_mpas = compute_spectrum(mpas2d)

    radial_gpm = radial_mean(spec_gpm)
    radial_mpas = radial_mean(spec_mpas)

    # -----------------------------
    # Plot
    # -----------------------------
    face = "black" if args.style == "black" else "white"
    textc = "white" if args.style == "black" else "black"

    ncols = 3 if args.show_2d else 1
    figsize = (15, 5) if args.show_2d else (6.5, 5)
    fig = plt.figure(figsize=figsize, facecolor=face)

    col = 1
    if args.show_2d:
        ax2d_1 = fig.add_subplot(1, 3, col)
        ax2d_1.set_facecolor(face)
        im1 = ax2d_1.imshow(np.log10(spec_gpm + 1e-12), origin="lower")
        ax2d_1.set_title("GPM: log10 Power 2D", color=textc)
        ax2d_1.tick_params(colors=textc)
        fig.colorbar(im1, ax=ax2d_1, fraction=0.046, pad=0.04)
        col += 1

        ax2d_2 = fig.add_subplot(1, 3, col)
        ax2d_2.set_facecolor(face)
        im2 = ax2d_2.imshow(np.log10(spec_mpas + 1e-12), origin="lower")
        ax2d_2.set_title("MPAS: log10 Power 2D", color=textc)
        ax2d_2.tick_params(colors=textc)
        fig.colorbar(im2, ax=ax2d_2, fraction=0.046, pad=0.04)
        col += 1

    ax1d = fig.add_subplot(1, ncols, col)
    ax1d.set_facecolor(face)
    ax1d.plot(np.arange(radial_gpm.size), np.log10(radial_gpm + 1e-12), label="GPM")
    ax1d.plot(np.arange(radial_mpas.size), np.log10(radial_mpas + 1e-12), label="MPAS")
    ax1d.set_xlabel("Wavenumber index", color=textc)
    ax1d.set_ylabel("log10 Power", color=textc)
    ax1d.set_title(
        f"Radial Spectrum ({'normalized' if args.normalize else out_unit})",
        color=textc,
    )
    ax1d.grid(alpha=0.3, color=textc)
    ax1d.legend()
    ax1d.tick_params(colors=textc)

    plt.tight_layout()

    # -----------------------------
    # Save
    # -----------------------------
    if args.outfile:
        out_path = (P.figs_dir / args.outfile) if not str(args.outfile).startswith("/") else args.outfile
    else:
        out_path = P.figs_dir / f"espectros_precipitacao_{args.style}.png"

    plt.savefig(out_path, dpi=300, facecolor=fig.get_facecolor())
    print("[INFO] Saved:", out_path)


if __name__ == "__main__":
    main()

