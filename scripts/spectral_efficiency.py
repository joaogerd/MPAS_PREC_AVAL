# Script: spectral_efficiency.py
# Descricao: Calcula a eficiencia espectral entre os campos de precipitacao do GPM (original e suavizados)
#            e do MPAS. A eficiencia espectral e definida como a razao entre os espectros GPM/MPAS.

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from scipy.fft import fft2, fftshift
from scipy.ndimage import uniform_filter, gaussian_filter
import os

# Diretórios
data_dir = "data_processed"
fig_dir = "figs"
os.makedirs(fig_dir, exist_ok=True)

# Funções auxiliares
def radial_mean(power_spectrum):
    ny, nx = power_spectrum.shape
    y, x = np.indices((ny, nx))
    center = np.array([(ny-1)/2.0, (nx-1)/2.0])
    r = np.sqrt((x - center[1])**2 + (y - center[0])**2)
    r = r.astype(int)
    tbin = np.bincount(r.ravel(), power_spectrum.ravel())
    nr = np.bincount(r.ravel())
    radialprofile = tbin / np.maximum(nr, 1)
    return radialprofile

# Carrega campos
gpm_path = os.path.join(data_dir, "gpm_remap_to_mpas.nc")
mpas_path = os.path.join("/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha", "mpas10km.nc4")

ds_gpm = xr.open_dataset(gpm_path)
ds_mpas = xr.open_dataset(mpas_path)

prec_gpm = ds_gpm['precipitation']
prec_gpm_mediamovel = xr.DataArray(uniform_filter(prec_gpm, size=3), coords=prec_gpm.coords)
prec_gpm_gauss = xr.DataArray(gaussian_filter(prec_gpm, sigma=1), coords=prec_gpm.coords)
prec_mpas = (ds_mpas['rainc'] + ds_mpas['rainnc']).diff('Time').mean('Time') * 8

# Cálculo dos espectros
spec_gpm = radial_mean(np.abs(fftshift(fft2(prec_gpm)))**2)
spec_mov = radial_mean(np.abs(fftshift(fft2(prec_gpm_mediamovel)))**2)
spec_gauss = radial_mean(np.abs(fftshift(fft2(prec_gpm_gauss)))**2)
spec_mpas = radial_mean(np.abs(fftshift(fft2(prec_mpas)))**2)

# Evita divisao por zero
spec_mpas = np.where(spec_mpas == 0, 1e-10, spec_mpas)

# Eficiência espectral
eff_gpm = spec_gpm / spec_mpas
eff_mov = spec_mov / spec_mpas
eff_gauss = spec_gauss / spec_mpas

# Plot
plt.figure(figsize=(10, 5))
plt.plot(eff_gpm, label='GPM (Original)', linewidth=2)
plt.plot(eff_mov, label='GPM (Média Móvel 3x3)', linestyle='--')
plt.plot(eff_gauss, label='GPM (Gaussiana \u03c3=1)', linestyle=':')
plt.xlabel('Número de onda (arbitrário)')
plt.ylabel('Eficiência espectral (GPM / MPAS)')
plt.yscale('log')
plt.xscale('log')
plt.title('Eficiência espectral da precipitação')
plt.grid(True, which="both", linestyle=':')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "eficiencia_espectral.png"), dpi=300)
ds_gpm.close()
ds_mpas.close()
print("[INFO] Figura salva em figs/eficiencia_espectral.png")

