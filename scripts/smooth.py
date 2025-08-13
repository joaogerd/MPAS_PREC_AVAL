from __future__ import annotations
import argparse
import xarray as xr
import numpy as np
from scipy.ndimage import uniform_filter, gaussian_filter
from .common import resolve_paths, setup_logging

def main() -> None:
    p = argparse.ArgumentParser(description="Smooth GPM precipitation (3x3 movmean & Gaussian).")
    p.add_argument("--sigma", type=float, default=1.0, help="Gaussian sigma")
    p.add_argument("--root", default=None, help="Project root (auto if omitted)")
    args = p.parse_args()

    setup_logging()
    P = resolve_paths(args.root)
    in_path = P.data_dir / "gpm_remap_to_mpas.nc"
    out_path = P.data_dir / "gpm_smoothed.nc"

    print("[INFO] Reading:", in_path)
    ds = xr.open_dataset(in_path)
    prec = ds["precipitation"]

    print("[INFO] Applying 3x3 moving average...")
    mov = xr.DataArray(
        uniform_filter(prec.data, size=3, mode="nearest"),
        coords=prec.coords, dims=prec.dims, name="precipitation_movmean_3x3"
    )

    print("[INFO] Applying Gaussian filter...")
    gauss = xr.DataArray(
        gaussian_filter(prec.data, sigma=args.sigma, mode="nearest"),
        coords=prec.coords, dims=prec.dims, name=f"precipitation_gauss_sigma{args.sigma:g}"
    )

    ds_out = xr.Dataset({"precipitation_movmean_3x3": mov, f"precipitation_gauss_sigma{args.sigma:g}": gauss})
    ds_out.to_netcdf(out_path)
    print("[INFO] Saved:", out_path)

if __name__ == "__main__":
    main()

