from __future__ import annotations
"""
Compare remapped GPM precipitation against MPAS precipitation (daily rate).

This script:
- Loads a GPM field already remapped to the MPAS grid (time-mean or time series).
- Loads MPAS accumulated precipitation and converts it to a daily rate.
- Ensures both fields are in mm/day.
- Produces a side-by-side map comparison and saves a PNG under <figs>/.

Notes
-----
If the remapped GPM file still has a time dimension, the time mean is computed
to compare spatial climatology against MPAS daily rate.
"""

import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import BoundaryNorm, ListedColormap

from .common import resolve_paths, setup_logging, pick_latlon
from .precip_loaders import load_mpas_rate


def _pick_var(ds: xr.Dataset, candidates=("precipitation_rate", "precipitation")) -> str:
    """
    Select the first matching precipitation variable present in the dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset containing precipitation variables.
    candidates : tuple of str, optional
        Variable names to try in order. Default is
        ("precipitation_rate", "precipitation").

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


def _to_2d_latlon(ds: xr.Dataset) -> tuple[np.ndarray, np.ndarray]:
    """
    Return 2D latitude/longitude arrays from dataset coordinates or variables.

    Accepts either 1D (rectilinear) or 2D (curvilinear) lat/lon. If lat/lon are
    1D, this function creates 2D arrays via `numpy.meshgrid`.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset that contains latitude and longitude variables or coordinates.

    Returns
    -------
    tuple of np.ndarray
        (lat2d, lon2d) arrays with identical shape, suitable for pcolormesh.

    Raises
    ------
    ValueError
        If latitude/longitude have unsupported shapes (e.g., one 1D and the other 2D).
    KeyError
        If latitude/longitude names cannot be found (see `pick_latlon`).
    """
    lat_name, lon_name = pick_latlon(ds)
    lat = ds[lat_name]
    lon = ds[lon_name]

    if lat.ndim == 1 and lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon.values, lat.values)
        return lat2d, lon2d
    if lat.ndim == 2 and lon.ndim == 2:
        return lat.values, lon.values

    raise ValueError(
        f"Unsupported lat/lon shapes: {lat_name} {lat.shape}, {lon_name} {lon.shape} "
        "(expected both 1D or both 2D)."
    )


def main() -> None:
    """
    Entry point: compare remapped GPM vs MPAS daily precipitation and save a PNG.

    Command-line options
    --------------------
    --mpas : str (required)
        Path to MPAS NetCDF with accumulated precipitation (rainc + rainnc).
    --gpm-file : str, optional
        Path to GPM remapped file. If omitted, tries:
        <data_processed>/gpm_remap_to_mpas_timemean.nc
        <data_processed>/gpm_remap_to_mpas_timeseries.nc
    --style : {'black', 'light'}, default 'black'
        Figure style (face/label colors).
    --root : str or None, default None
        Project root (auto-resolved if omitted).

    Side Effects
    ------------
    Saves a PNG to <figs>/comparacao_gpm_mpas_<style>.png.
    """
    p = argparse.ArgumentParser(description="Compare GPM (remapped) vs MPAS precipitation (daily).")
    p.add_argument("--mpas", required=True, help="Path to MPAS NetCDF")
    p.add_argument(
        "--gpm-file",
        default=None,
        help="Path to remapped GPM file (default: <data_processed>/gpm_remap_to_mpas_*.nc)",
    )
    p.add_argument("--style", choices=["black", "light"], default="black", help="Figure style.")
    p.add_argument("--root", default=None, help="Project root (auto if omitted)")
    args = p.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    # ------------------------------------------------------------
    # Load GPM (already remapped to MPAS grid)
    # ------------------------------------------------------------
    if args.gpm_file is not None:
        gpm_path = P.root / args.gpm_file if not str(args.gpm_file).startswith("/") else args.gpm_file
    else:
        # Try time-mean first, then timeseries (matches regrid script defaults)
        cand1 = P.data_dir / "gpm_remap_to_mpas_timemean.nc"
        cand2 = P.data_dir / "gpm_remap_to_mpas_timeseries.nc"
        gpm_path = cand1 if cand1.exists() else cand2

    ds_gpm = xr.open_dataset(gpm_path)
    gpm_var = _pick_var(ds_gpm, candidates=("precipitation_rate", "precipitation"))

    # If the dataset still has time, take the mean to compare spatial climatology
    da_gpm = ds_gpm[gpm_var]
    if "time" in da_gpm.dims:
        da_gpm = da_gpm.mean("time")

    # Ensure mm/day for plotting
    units = (da_gpm.attrs.get("units") or "").lower().replace(" ", "")
    if units in ("mm/d", "mm/day", "mm_per_day"):
        gpm_day = da_gpm
    elif units in ("mm/h", "mmhr", "mm_per_hour"):
        gpm_day = da_gpm * 24.0
        gpm_day.attrs["units"] = "mm/day"
    elif units == "":
        # No units attr: assume rate already remapped in mm/h as per our pipeline
        gpm_day = da_gpm * 24.0
        gpm_day.attrs["units"] = "mm/day"
    else:
        raise ValueError(f"Unexpected GPM units in {gpm_var!r}: {da_gpm.attrs.get('units')!r}")

    lat_gpm, lon_gpm = _to_2d_latlon(ds_gpm)

    # ------------------------------------------------------------
    # Load MPAS and convert to daily rate (time mean)
    # ------------------------------------------------------------
    mpas_day = load_mpas_rate(args.mpas, out_unit="mm/day", time_mean=True)

    # Try to get lat/lon from the same MPAS source for pcolormesh
    # (GPM is already on MPAS grid; we just plot both with their own lat/lon)
    lat_mpas, lon_mpas = _to_2d_latlon(mpas_day.to_dataset(name="tmp"))

    # ------------------------------------------------------------
    # Plot style & colormap
    # ------------------------------------------------------------
    bounds = [0.0, 1.0, 1.5, 2, 2.5, 3, 4, 6, 8, 10, 14, 18, 22, 26, 30, 40, 50]
    colors = [
        "#000000", "#e6e6ff", "#b3b3ff", "#6666ff", "#000066",
        "#004000", "#008000", "#00cc00", "#66ff66", "#ffff00",
        "#ffcc00", "#ff9900", "#ff3300", "#cc0000", "#990000",
        "#660000", "#bfbfbf",
    ]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, len(colors))

    face = "black" if args.style == "black" else "white"
    textc = "white" if args.style == "black" else "black"

    # ------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------
    fig = plt.figure(figsize=(12, 5), facecolor=face)

    # GPM panel
    ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax1.set_facecolor(face)
    cf1 = ax1.pcolormesh(lon_gpm, lat_gpm, gpm_day.values, cmap=cmap, norm=norm, shading="auto")
    ax1.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor=textc)
    ax1.set_title("GPM (Remapped → MPAS grid)", color=textc)
    cb1 = plt.colorbar(cf1, ax=ax1, orientation="horizontal", pad=0.05, ticks=bounds)
    cb1.set_label("mm/day", color=textc)
    plt.setp(cb1.ax.get_xticklabels(), color=textc)

    # MPAS panel
    ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
    ax2.set_facecolor(face)
    cf2 = ax2.pcolormesh(lon_mpas, lat_mpas, mpas_day.values, cmap=cmap, norm=norm, shading="auto")
    ax2.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor=textc)
    ax2.set_title("MPAS", color=textc)
    cb2 = plt.colorbar(cf2, ax=ax2, orientation="horizontal", pad=0.05, ticks=bounds)
    cb2.set_label("mm/day", color=textc)
    plt.setp(cb2.ax.get_xticklabels(), color=textc)

    out = resolve_paths(args.root).figs_dir / f"comparacao_gpm_mpas_{args.style}.png"
    plt.tight_layout()
    plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
    print("[INFO] Saved:", out)


if __name__ == "__main__":
    main()

