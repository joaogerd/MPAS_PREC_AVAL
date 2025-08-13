from __future__ import annotations
import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import BoundaryNorm, ListedColormap
from .common import resolve_paths, setup_logging, load_mpas_precip_daily

def main() -> None:
    p = argparse.ArgumentParser(description="Compare GPM (remapped) vs MPAS precip (daily).")
    p.add_argument("--mpas", required=True, help="Path to MPAS NetCDF")
    p.add_argument("--style", choices=["black", "light"], default="black")
    p.add_argument("--root", default=None)
    args = p.parse_args()

    setup_logging()
    P = resolve_paths(args.root)

    ds_gpm = xr.open_dataset(P.data_dir / "gpm_remap_to_mpas.nc")
    prec_gpm = ds_gpm["precipitation"].mean("time") * 24

    prec_mpas = load_mpas_precip_daily(args.mpas)
    lat = prec_mpas["latitude"]
    lon = prec_mpas["longitude"]

    bounds = [0.0,1.0,1.5,2,2.5,3,4,6,8,10,14,18,22,26,30,40,50]
    colors = [
        "#000000","#e6e6ff","#b3b3ff","#6666ff","#000066",
        "#004000","#008000","#00cc00","#66ff66","#ffff00",
        "#ffcc00","#ff9900","#ff3300","#cc0000","#990000",
        "#660000","#bfbfbf"
    ]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, len(colors))

    face = "black" if args.style == "black" else "white"
    textc = "white" if args.style == "black" else "black"

    fig = plt.figure(figsize=(12,5), facecolor=face)
    ax1 = fig.add_subplot(1,2,1, projection=ccrs.PlateCarree())
    ax1.set_facecolor(face)
    lon2d_gpm, lat2d_gpm = np.meshgrid(ds_gpm["lon"], ds_gpm["lat"])
    cf1 = ax1.pcolormesh(lon2d_gpm, lat2d_gpm, prec_gpm.T, cmap=cmap, norm=norm)
    ax1.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor=textc)
    ax1.set_title("GPM Remapped", color=textc)
    cb1 = plt.colorbar(cf1, ax=ax1, orientation="horizontal", pad=0.05, ticks=bounds)
    cb1.set_label("mm/day", color=textc)
    plt.setp(cb1.ax.get_xticklabels(), color=textc)

    ax2 = fig.add_subplot(1,2,2, projection=ccrs.PlateCarree())
    ax2.set_facecolor(face)
    cf2 = ax2.pcolormesh(lon, lat, prec_mpas, cmap=cmap, norm=norm)
    ax2.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor=textc)
    ax2.set_title("MPAS", color=textc)
    cb2 = plt.colorbar(cf2, ax=ax2, orientation="horizontal", pad=0.05, ticks=bounds)
    cb2.set_label("mm/day", color=textc)
    plt.setp(cb2.ax.get_xticklabels(), color=textc)

    out = P.figs_dir / f"comparacao_gpm_mpas_{args.style}.png"
    plt.tight_layout()
    plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
    print("[INFO] Saved:", out)

if __name__ == "__main__":
    main()

