# scripts/inspect_fields.py

from __future__ import annotations
import argparse
import xarray as xr
import matplotlib.pyplot as plt
from .common import resolve_paths, load_mpas_precip_daily


def show_stats(name: str, data: xr.DataArray) -> None:
    """
    Print basic statistics of a given field.

    Parameters
    ----------
    name : str
        Name or label of the dataset/field (used in printed output).
    data : xarray.DataArray
        Data array containing the variable values.

    Notes
    -----
    The statistics include:
    - Minimum value
    - Maximum value
    - Mean value
    - Number of NaNs
    """
    print(f"{name} stats:")
    print(f"  min: {data.min().item():.2f}")
    print(f"  max: {data.max().item():.2f}")
    print(f"  mean: {data.mean().item():.2f}")
    print(f"  NaNs: {data.isnull().sum().item()}")
    print("")


def plot_field(data: xr.DataArray, title: str) -> None:
    """
    Plot a 2D field using Matplotlib's default xarray plotting.

    Parameters
    ----------
    data : xarray.DataArray
        The field to be plotted.
    title : str
        Title for the plot.

    Notes
    -----
    This function uses a Viridis colormap and a fixed figure size.
    """
    plt.figure(figsize=(10, 4))
    data.plot(cmap="viridis")
    plt.title(title)
    plt.tight_layout()
    plt.show()


def main() -> None:
    """
    Inspect and plot GPM and MPAS precipitation fields.

    The script loads original and smoothed GPM precipitation datasets,
    prints statistics, and plots each field for visual inspection.

    Examples
    --------
    Default run using data in the project's default data directory:

    >>> python inspect_fields.py

    Specify a custom root directory:

    >>> python inspect_fields.py --root /path/to/project
    """
    parser = argparse.ArgumentParser(description="Inspect GPM and MPAS fields.")
    # parser.add_argument("--mpas", required=True, help="Path to MPAS NetCDF")
    parser.add_argument("--root", default=None, help="Optional custom project root path.")
    args = parser.parse_args()

    P = resolve_paths(args.root)

    # GPM original
    ds_gpm = xr.open_dataset(P.data_dir / "gpm_remap_to_mpas.nc")
    gpm = ds_gpm["precipitation"].isel(time=0)
    show_stats("GPM", gpm)
    plot_field(gpm, "GPM (original)")

    # GPM smoothed
    ds_sm = xr.open_dataset(P.data_dir / "gpm_smoothed.nc")
    mov = ds_sm["precipitation_movmean_3x3"].isel(time=0)
    gau_var = [v for v in ds_sm.data_vars if v.startswith("precipitation_gauss_sigma")][0]
    gau = ds_sm[gau_var].isel(time=0)

    show_stats("MOV", mov)
    plot_field(mov, "GPM (moving average 3x3)")

    show_stats("GAU", gau)
    plot_field(gau, "GPM (gaussian smoothed)")

    # MPAS (commented out for optional use)
    # mpas = load_mpas_precip_daily(args.mpas).isel(time=0)
    # show_stats("MPAS", mpas)
    # plot_field(mpas, "MPAS")


if __name__ == "__main__":
    main()

