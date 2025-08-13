from __future__ import annotations
import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from .common import resolve_paths, setup_logging, compute_spectrum, radial_mean, trim_edges, load_mpas_precip_daily

def _load_fields(P, mpas_path: str, sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ds_gpm = xr.open_dataset(P.data_dir / "gpm_remap_to_mpas.nc")
    ds_sm  = xr.open_dataset(P.data_dir / "gpm_smoothed.nc")
    gpm = ds_gpm["precipitation"].values
    # nomes canônicos definidos no smooth.py
    gpm_mov = ds_sm["precipitation_movmean_3x3"].values
    gpm_gau = ds_sm[[v for v in ds_sm.data_vars if v.startswith("precipitation_gauss_sigma")][0]].values
    mpas = load_mpas_precip_daily(mpas_path).values
    return gpm, gpm_mov, gpm_gau, mpas

def _radial_spectra(gpm, mov, gau, mpas, trim: int):
    gpm  = trim_edges(gpm, trim)
    mov  = trim_edges(mov, trim)
    gau  = trim_edges(gau, trim)
    mpas = trim_edges(mpas, trim)
    Sgpm  = radial_mean(compute_spectrum(gpm))
    Smov  = radial_mean(compute_spectrum(mov))
    Sgau  = radial_mean(compute_spectrum(gau))
    Smpas = radial_mean(compute_spectrum(mpas))
    return Sgpm, Smov, Sgau, Smpas

def plot_power(P, Sgpm, Smov, Sgau, Smpas):
    plt.figure(figsize=(10,5))
    plt.plot(Sgpm, label="GPM (orig)", linewidth=2)
    plt.plot(Smov, label="GPM (mov 3x3)", linestyle="--")
    plt.plot(Sgau, label="GPM (gauss)", linestyle=":")
    plt.plot(Smpas, label="MPAS", color="black")
    plt.xlabel("Wavenumber (arb.)")
    plt.ylabel("Power spectrum")
    plt.xscale("log"); plt.yscale("log")
    plt.grid(True, which="both", linestyle=":")
    plt.legend(); plt.tight_layout()
    out = P.figs_dir / "espectros_precipitacao.png"
    plt.savefig(out, dpi=300)
    print("[INFO] Saved:", out)

def plot_efficiency(P, Sgpm, Smov, Sgau, Smpas):
    Smpas = np.where(Smpas==0, 1e-10, Smpas)
    plt.figure(figsize=(10,5))
    plt.plot(Sgpm/Smpas, label="GPM (orig)", linewidth=2)
    plt.plot(Smov/Smpas, label="GPM (mov 3x3)", linestyle="--")
    plt.plot(Sgau/Smpas, label="GPM (gauss)", linestyle=":")
    plt.xlabel("Wavenumber (arb.)")
    plt.ylabel("Spectral efficiency (GPM/MPAS)")
    plt.xscale("log"); plt.yscale("log")
    plt.grid(True, which="both", linestyle=":")
    plt.legend(); plt.tight_layout()
    out = P.figs_dir / "eficiencia_espectral.png"
    plt.savefig(out, dpi=300)
    print("[INFO] Saved:", out)

def main() -> None:
    p = argparse.ArgumentParser(description="Spectral analyses for GPM×MPAS.")
    p.add_argument("mode", choices=["power","efficiency","all"], help="Which plots to generate")
    p.add_argument("--mpas", required=True, help="Path to MPAS NetCDF")
    p.add_argument("--trim", type=int, default=10, help="Trim border width")
    p.add_argument("--sigma", type=float, default=1.0, help="Gaussian sigma used in smoothing")
    p.add_argument("--root", default=None)
    args = p.parse_args()

    setup_logging()
    P = resolve_paths(args.root)
    gpm, mov, gau, mpas = _load_fields(P, args.mpas, args.sigma)
    Sgpm, Smov, Sgau, Smpas = _radial_spectra(gpm, mov, gau, mpas, args.trim)

    if args.mode in ("power", "all"):
        plot_power(P, Sgpm, Smov, Sgau, Smpas)
    if args.mode in ("efficiency", "all"):
        plot_efficiency(P, Sgpm, Smov, Sgau, Smpas)

if __name__ == "__main__":
    main()

