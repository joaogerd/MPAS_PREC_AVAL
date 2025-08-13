from __future__ import annotations
import argparse
from pathlib import Path
import xarray as xr
import xesmf as xe
from .common import resolve_paths, setup_logging, load_gpm

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remap GPM onto MPAS grid (bilinear)."
    )
    parser.add_argument("--gpm", required=True, help="Path to GPM NetCDF")
    parser.add_argument("--mpas", required=True, help="Path to MPAS NetCDF")
    parser.add_argument("--weights", default="data_processed/weights_gpm_to_mpas.nc",
                        help="Path to regridding weights file (will be created if absent)")
    parser.add_argument("--root", default=None, help="Project root (auto if omitted)")
    args = parser.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    ds_gpm = xr.open_dataset(args.gpm)
    ds_mpas = xr.open_dataset(args.mpas)

    prec_gpm = load_gpm(args.gpm)  # mantém tempo para média posterior
    dest_grid = xr.Dataset({"lat": ds_mpas["latitude"], "lon": ds_mpas["longitude"]})

    weights_path = Path(args.weights)
    if weights_path.exists():
        print("[INFO] Reusing existing weights")
        regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear",
                                 reuse_weights=True, filename=str(weights_path))
    else:
        print("[INFO] Creating new weights")
        regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear",
                                 periodic=True, filename=str(weights_path))

    out = regridder(prec_gpm)
    xr.Dataset({"precipitation": out}).to_netcdf(P.data_dir / "gpm_remap_to_mpas.nc")
    print(f"[INFO] Saved: {P.data_dir / 'gpm_remap_to_mpas.nc'}")

if __name__ == "__main__":
    main()

