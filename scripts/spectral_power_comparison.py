# Script: spectral_power_analysis.py
# Descricao: Analisa os espectros de potencia (2D) da precipitacao simulada (MPAS)
#            e observada (GPM), com opcao de suavizacao. Salva espectros em escala log-log.

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift
from scipy.ndimage import uniform_filter, gaussian_filter
import os

# Diretórios
fig_dir = "figs"
data_dir = "data_processed"
os.makedirs(fig_dir, exist_ok=True)

# Função auxiliar

def radial_mean(power_spectrum):
    ny, nx = power_spectrum.shape
    y, x = np.indices((ny, nx))
    center = np.array([(ny-1)/2.0, (nx-1)/2.0])
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2).astype(int)
    tbin = np.bincount(r.ravel(), power_spectrum.ravel())
    nr = np.bincount(r.ravel())
    return tbin / np.maximum(nr, 1)

# Carrega campos
prec_gpm = xr.open_dataset(os.path.join(data_dir, "gpm_remap_to_mpas.nc"))['precipitation']
prec_mpas = xr.open_dataset("/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4")
prec_mpas = (prec_mpas['rainc'] + prec_mpas['rainnc']).diff('Time').mean('Time') * 8

# GPM suavizados
prec_gpm_mov = xr.DataArray(uniform_filter(prec_gpm, size=3), coords=prec_gpm.coords)
prec_gpm_gauss = xr.DataArray(gaussian_filter(prec_gpm, sigma=1), coords=prec_gpm.coords)

# Espectros
spec_gpm = radial_mean(np.abs(fftshift(fft2(prec_gpm)))**2)
spec_mov = radial_mean(np.abs(fftshift(fft2(prec_gpm_mov)))**2)
spec_gauss = radial_mean(np.abs(fftshift(fft2(prec_gpm_gauss)))**2)
spec_mpas = radial_mean(np.abs(fftshift(fft2(prec_mpas)))**2)

# Plot
plt.figure(figsize=(10, 5))
plt.plot(spec_gpm, label='GPM (Original)', linewidth=2)
plt.plot(spec_mov, label='GPM (Média Móvel 3x3)', linestyle='--')
plt.plot(spec_gauss, label='GPM (Gaussiana σ=1)', linestyle=':')
plt.plot(spec_mpas, label='MPAS', color='black')
plt.xlabel('Número de onda (arbitrário)')
plt.ylabel('Espectro de Potência')
plt.yscale('log')
plt.xscale('log')
plt.title('Espectro de Potência da Precipitação (log-log)')
plt.grid(True, which="both", linestyle=':')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "espectros_precipitacao.png"), dpi=300)
print("[INFO] Figura salva em figs/espectros_precipitacao.png")

