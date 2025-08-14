# scripts/smooth.py

from __future__ import annotations
import argparse
import xarray as xr
import numpy as np
from joblib import Parallel, delayed
from scipy.ndimage import uniform_filter, gaussian_filter
from .common import resolve_paths, setup_logging, get_spatial_dims


def apply_filters(slice_2d: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    mov = uniform_filter(slice_2d, size=3, mode="nearest")
    gau = gaussian_filter(slice_2d, sigma=sigma, mode="nearest")
    return mov, gau

def main() -> None:
    p = argparse.ArgumentParser(description="Smooth GPM precipitation (3x3 movmean & Gaussian).")
    p.add_argument("--sigma", type=float, default=1.0, help="Gaussian sigma")
    p.add_argument("--root", default=None, help="Project root (auto if omitted)")
    p.add_argument("--n_jobs", type=int, default=16, help="Número de núcleos para paralelização")
    args = p.parse_args()

    setup_logging()
    P = resolve_paths(args.root)
    in_path = P.data_dir / "gpm_remap_to_mpas.nc"
    out_path = P.data_dir / "gpm_smoothed.nc"

    print("[INFO] Reading:", in_path)
    ds = xr.open_dataset(in_path)
    prec = ds["precipitation"]
    lat_dim, lon_dim = get_spatial_dims(prec)

    print(f"[INFO] Aplicando suavizações com {args.n_jobs} núcleos...")

    results = Parallel(n_jobs=args.n_jobs)(
        delayed(apply_filters)(prec.isel(time=t).values, args.sigma) for t in range(prec.sizes["time"])
    )

    mov_stack, gau_stack = zip(*results)
    mov = xr.DataArray(np.stack(mov_stack), coords=prec.coords, dims=prec.dims, name="precipitation_movmean_3x3")
    gau = xr.DataArray(np.stack(gau_stack), coords=prec.coords, dims=prec.dims, name=f"precipitation_gauss_sigma{args.sigma:g}")

    ds_out = xr.Dataset({mov.name: mov, gau.name: gau})
    ds_out.to_netcdf(out_path)
    print("[INFO] Saved:", out_path)

if __name__ == "__main__":
    main()

