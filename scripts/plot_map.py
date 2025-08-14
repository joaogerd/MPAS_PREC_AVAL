# scripts/plot_map.py

from __future__ import annotations
import argparse
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from .common import resolve_paths, get_spatial_dims, print_field_stats


def plot_map(
    input_path: str,
    varname: str,
    time_index: int = 0,
    save: bool = False,
    debug: bool = False
) -> None:
    """
    Plot a 2D variable from a NetCDF file using Cartopy.

    Parameters
    ----------
    input_path : str
        Relative path to the NetCDF file inside the project's `data_dir`.
        Example: `"gpm_smoothed.nc"`.
    varname : str
        Name of the variable to plot. Must exist in the dataset.
    time_index : int, optional
        Time index to plot (default is 0).
    save : bool, optional
        If True, saves the plot to `figs_dir` instead of showing it interactively.
    debug : bool, optional
        If True, prints basic statistics of the variable before plotting.

    Raises
    ------
    ValueError
        If `varname` is not found in the dataset.
    """
    P = resolve_paths()
    ds = xr.open_dataset(P.data_dir / input_path)

    if varname is None:
        print("[ERROR] You must specify a variable name using --var")
        print("Available variables:", list(ds.data_vars))
        return

    if varname not in ds:
        raise ValueError(
            f"Variable '{varname}' not found in dataset. "
            f"Available: {list(ds.data_vars)}"
        )

    var = ds[varname].isel(time=time_index)

    if debug:
        print_field_stats(var)

    lat_name, lon_name = get_spatial_dims(ds)
    lat = ds[lat_name]
    lon = ds[lon_name]

    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    mesh = ax.pcolormesh(lon, lat, var, cmap="viridis", shading="auto")
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.set_title(f"{varname} - Time index {time_index}")

    plt.colorbar(mesh, ax=ax, orientation="vertical", label=var.attrs.get("units", ""))
    plt.tight_layout()

    if save:
        out_path = P.figs_dir / f"{varname}_t{time_index}.png"
        plt.savefig(out_path, dpi=300)
        print(f"[INFO] Saved: {out_path}")
    else:
        plt.show()


def main() -> None:
    """
    Command-line entry point for plotting NetCDF variables.

    This script allows visualizing a variable from a NetCDF file located in
    the project's `data_dir`, with optional saving and debug mode.

    Examples
    --------
    Show plot interactively:

    >>> python plot_map.py --input gpm_smoothed.nc --var precipitation_movmean_3x3 --time 0

    Save plot to `figs_dir`:

    >>> python plot_map.py --input gpm_smoothed.nc --var precipitation_movmean_3x3 --time 0 --save
    """
    parser = argparse.ArgumentParser(
        description="Plot precipitation maps from NetCDF using Cartopy."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Relative path to NetCDF file inside data_dir (e.g., gpm_smoothed.nc)"
    )
    parser.add_argument(
        "--var",
        required=False,
        help="Variable name to plot (e.g., precipitation_movmean_3x3)"
    )
    parser.add_argument(
        "--time",
        type=int,
        default=0,
        help="Time index to plot"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the plot instead of showing it"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print statistics of the field"
    )
    args = parser.parse_args()

    plot_map(
        args.input,
        args.var,
        args.time,
        save=args.save,
        debug=args.debug
    )


if __name__ == "__main__":
    main()

