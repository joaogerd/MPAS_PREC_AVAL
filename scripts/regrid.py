# regrid_gpm_to_mpas.py
# -*- coding: utf-8 -*-
"""
Remap GPM precipitation onto the MPAS grid using xESMF (bilinear).

- Uses `load_gpm_rate` to standardize GPM to a rate base (default: mm/h).
- Optionally preserves the time dimension or returns a time-mean field.
- Builds the destination grid from MPAS lat/lon, supporting common coord names.

Requirements
------------
- xarray
- xesmf (and its ESMF dependency properly installed)
"""

from __future__ import annotations
import argparse
from pathlib import Path
import xarray as xr
import xesmf as xe

from .common import resolve_paths, setup_logging, pick_latlon
from .precip_loaders import load_gpm_rate  # MPAS loader not needed for remap itself

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remap GPM onto MPAS grid (bilinear) with unit/time handling."
    )
    parser.add_argument("--gpm", required=True, help="Path to GPM NetCDF")
    parser.add_argument("--mpas", required=True, help="Path to MPAS NetCDF (for target grid)")
    parser.add_argument(
        "--weights",
        default="data_processed/weights_gpm_to_mpas.nc",
        help="Path to regridding weights file (created if missing)",
    )
    parser.add_argument("--root", default=None, help="Project root (auto if omitted)")
    parser.add_argument(
        "--out-unit",
        default="mm/h",
        choices=["mm/h", "mm/day"],
        help="Common precipitation rate unit to use for GPM before remapping.",
    )
    parser.add_argument(
        "--time-mean",
        action="store_true",
        help="If set, average over time BEFORE regridding (good for spatial spectra). "
             "If not set, keep the full time series and regrid all time steps.",
    )
    parser.add_argument(
        "--periodic",
        action="store_true",
        help="Treat longitudes as periodic when building weights (use for global grids).",
    )
    args = parser.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    # --- Load source (GPM) as a rate in the requested unit.
    #     If time_mean=False, we keep the full time dimension and xESMF will
    #     broadcast over it, regridding all timestamps in one go.
    gpm_rate = load_gpm_rate(
        args.gpm,
        out_unit=args.out_unit,
        time_mean=args.time_mean,
    )

    # --- Build destination grid from MPAS lat/lon
    ds_mpas = xr.open_dataset(args.mpas)
    lat_name, lon_name = pick_latlon(ds_mpas)
    dest_grid = xr.Dataset(
        {
            "lat": ds_mpas[lat_name],
            "lon": ds_mpas[lon_name],
        }
    )

    # --- Prepare weights / regridder
    weights_path = Path(args.weights)
    weights_path.parent.mkdir(parents=True, exist_ok=True)

    if weights_path.exists():
        print("[INFO] Reusing existing weights:", weights_path)
        regridder = xe.Regridder(
            gpm_rate, dest_grid, "bilinear", reuse_weights=True, filename=str(weights_path)
        )
    else:
        print("[INFO] Creating new weights:", weights_path)
        regridder = xe.Regridder(
            gpm_rate,
            dest_grid,
            "bilinear",
            periodic=args.periodic,
            filename=str(weights_path),
        )

    # --- Apply regridding (works for 2D fields or 3D with leading 'time')
    gpm_on_mpas = regridder(gpm_rate)

    # Name and attrs for clarity
    varname = "precipitation_rate"
    gpm_on_mpas.name = varname
    gpm_on_mpas.attrs.update(
        {
            "long_name": f"GPM precipitation rate remapped to MPAS grid ({args.out_unit})",
            "units": args.out_unit,
            "source": "GPM (standardized via load_gpm_rate)",
            "regridding": "xESMF bilinear",
        }
    )

    # --- Save
    out_name = "gpm_remap_to_mpas_timemean.nc" if args.time_mean else "gpm_remap_to_mpas_timeseries.nc"
    out_path = P.data_dir / out_name
    xr.Dataset({varname: gpm_on_mpas}).to_netcdf(out_path)
    print(f"[INFO] Saved: {out_path}")

    # Explicitly clean up regridder resources (good practice with ESMF)
    regridder.clean()


if __name__ == "__main__":
    main()

