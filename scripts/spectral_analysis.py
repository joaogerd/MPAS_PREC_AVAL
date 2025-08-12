# spectral_analysis.py
# --------------------------------------------------
# Análise espectral 2D dos campos de precipitação:
# - GPM reamostrado
# - GPM suavizado
# - MPAS
# Salva os espectros e compara em um único gráfico.
# --------------------------------------------------

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift
import os

# Diretórios de entrada e saída
DATA_DIR = "../data_processed"
FIG_DIR = "../figs"
os.makedirs(FIG_DIR, exist_ok=True)

# Função para calcular espectro de energia 2D
def compute_spectrum(field):
    ft = fft2(field)
    spectrum = np.abs(ft) ** 2
    spectrum = fftshift(spectrum)  # centraliza o zero
    return spectrum

# Carrega os campos
ds_gpm = xr.open_dataset(f"{DATA_DIR}/gpm_remap_to_mpas.nc")
ds_gpm_smooth = xr.open_dataset(f"{DATA_DIR}/gpm_smoothed.nc")
ds_mpas = xr.open_dataset("/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4")

prec_gpm = ds_gpm['precipitation'].values
prec_gpm_mov = ds_gpm_smooth['precipitation_movmean'].values
prec_gpm_gauss = ds_gpm_smooth['precipitation_gaussian'].values
prec_mpas = (ds_mpas['rainc'] + ds_mpas['rainnc']).diff('Time').mean(dim='Time') * 8

# Corta bordas nulas, se houver (evita interferência nos espectros)
def trim_field(field):
    return field[10:-10, 10:-10]

prec_gpm = trim_field(prec_gpm)
prec_gpm_mov = trim_field(prec_gpm_mov)
prec_gpm_gauss = trim_field(prec_gpm_gauss)
prec_mpas = trim_field(prec_mpas.values)

# Calcula espectros
spec_gpm = compute_spectrum(prec_gpm)
spec_mov = compute_spectrum(prec_gpm_mov)
spec_gauss = compute_spectrum(prec_gpm_gauss)
spec_mpas = compute_spectrum(prec_mpas)

# Calcula espectro radial médio

def radial_average(spectrum):
    ny, nx = spectrum.shape
    y, x = np.indices((ny, nx))
    center = (ny // 2, nx // 2)
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2)
    r = r.astype(int)
    radial_prof = np.bincount(r.ravel(), spectrum.ravel()) / np.bincount(r.ravel())
    return radial_prof

k_gpm = radial_average(spec_gpm)
k_mov = radial_average(spec_mov)
k_gauss = radial_average(spec_gauss)
k_mpas = radial_average(spec_mpas)

# Frequências normalizadas
freqs = np.arange(len(k_gpm))

# Plota gráfico
plt.figure(figsize=(8, 5))
plt.loglog(freqs, k_gpm, label="GPM (original)", color="blue")
plt.loglog(freqs, k_mov, label="GPM (média móvel)", color="green")
plt.loglog(freqs, k_gauss, label="GPM (gaussiano)", color="lime")
plt.loglog(freqs, k_mpas, label="MPAS", color="red")

plt.xlabel("Frequência espacial (arbitrária)")
plt.ylabel("Espectro de energia")
plt.title("Análise Espectral 2D da Precipitação")
plt.legend()
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.tight_layout()

plt.savefig(f"{FIG_DIR}/espectro_precipitacao.png", dpi=300)
print("[INFO] Figura salva em figs/espectro_precipitacao.png")

