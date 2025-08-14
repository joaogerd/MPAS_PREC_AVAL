from __future__ import annotations

"""
Apply spatial smoothing to GPM precipitation remapped to the MPAS grid.

This script reads a NetCDF produced by `regrid.py`, selects the
precipitation variable (supports either "precipitation_rate" or "precipitation"),
and applies:
- 3x3 moving mean (uniform filter)
- Gaussian smoothing (user-defined sigma)

If the input field has a time dimension, smoothing is applied to each time slice
in parallel. If the input is already a time-mean 2D field, smoothing is applied
once.

Output: data_processed/gpm_smoothed.nc
"""

import argparse
import numpy as np
import xarray as xr
from joblib import Parallel, delayed
from scipy.ndimage import uniform_filter, gaussian_filter

from .common import resolve_paths, setup_logging


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


def apply_filters(slice_2d: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Apply 3x3 moving average and Gaussian smoothing to a 2D array.

    Parameters
    ----------
    slice_2d : np.ndarray
        2D array to be smoothed.
    sigma : float
        Standard deviation for the Gaussian kernel.

    Returns
    -------
    tuple of np.ndarray
        (moving_mean_3x3, gaussian_sigmaN) arrays with the same shape as `slice_2d`.
    """
    mov = uniform_filter(slice_2d, size=3, mode="nearest")
    gau = gaussian_filter(slice_2d, sigma=sigma, mode="nearest")
    return mov, gau


def _smooth_timeseries(da: xr.DataArray, sigma: float, n_jobs: int) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Smooth a time-varying 3D field by applying filters to each time slice.

    Parameters
    ----------
    da : xr.DataArray
        3D field with dims like ('time', 'lat', 'lon') or ('time', y, x).
    sigma : float
        Standard deviation for the Gaussian kernel.
    n_jobs : int
        Number of parallel jobs to use.

    Returns
    -------
    tuple of xr.DataArray
        Two DataArrays with the same dims/coords as `da`:
        - moving-mean (3x3)
        - gaussian (sigma)
    """
    results = Parallel(n_jobs=n_jobs)(
        delayed(apply_filters)(da.isel(time=t).values, sigma) for t in range(da.sizes["time"])
    )
    mov_stack, gau_stack = zip(*results)

    mov = xr.DataArray(
        np.stack(mov_stack),
        coords=da.coords,
        dims=da.dims,
        name=f"{da.name or 'precipitation'}_movmean_3x3",
    )
    gau = xr.DataArray(
        np.stack(gau_stack),
        coords=da.coords,
        dims=da.dims,
        name=f"{da.name or 'precipitation'}_gauss_sigma{sigma:g}",
    )
    return mov, gau


def _smooth_2d(da: xr.DataArray, sigma: float) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Smooth a single 2D field.

    Parameters
    ----------
    da : xr.DataArray
        2D field with dims like ('lat', 'lon') or (y, x).
    sigma : float
        Standard deviation for the Gaussian kernel.

    Returns
    -------
    tuple of xr.DataArray
        Two 2D DataArrays (moving-mean and gaussian) with same dims/coords as `da`.
    """
    mov, gau = apply_filters(da.values, sigma)
    mov_da = xr.DataArray(
        mov, coords=da.coords, dims=da.dims, name=f"{da.name or 'precipitation'}_movmean_3x3"
    )
    gau_da = xr.DataArray(
        gau, coords=da.coords, dims=da.dims, name=f"{da.name or 'precipitation'}_gauss_sigma{sigma:g}"
    )
    return mov_da, gau_da


def main() -> None:
    """
    Entry point: smooth remapped GPM precipitation and write a NetCDF file.

    Command-line options
    --------------------
    --sigma : float, default=1.0
        Gaussian sigma.
    --root : str or None, default=None
        Project root (auto-resolved if omitted).
    --n_jobs : int, default=16
        Number of CPU cores for parallel processing.
    """
    parser = argparse.ArgumentParser(
        description="Smooth GPM precipitation (3x3 moving mean & Gaussian)."
    )
    parser.add_argument("--sigma", type=float, default=1.0, help="Gaussian sigma.")
    parser.add_argument("--root", default=None, help="Project root (auto if omitted).")
    parser.add_argument("--n_jobs", type=int, default=16, help="Number of CPU cores for parallel processing.")
    args = parser.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    in_path = P.data_dir / "gpm_remap_to_mpas.nc"
    out_path = P.data_dir / "gpm_smoothed.nc"

    print("[INFO] Reading:", in_path)
    ds = xr.open_dataset(in_path)

    var_name = _pick_var(ds)
    da = ds[var_name]

    print(f"[INFO] Applying smoothing filters (sigma={args.sigma}, n_jobs={args.n_jobs})...")

    if "time" in da.dims:
        mov, gau = _smooth_timeseries(da, sigma=args.sigma, n_jobs=args.n_jobs)
    else:
        mov, gau = _smooth_2d(da, sigma=args.sigma)

    xr.Dataset({mov.name: mov, gau.name: gau}).to_netcdf(out_path)
    print("[INFO] Saved:", out_path)


if __name__ == "__main__":
    main()

