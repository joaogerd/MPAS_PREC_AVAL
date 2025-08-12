import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
import os

# === Script original para comparação direta entre GPM e MPAS ===
# Gera uma figura com dois painéis comparando campos médios de precipitação

# Caminhos
path_gpm = "../data_processed/gpm_remap_to_mpas.nc"
path_mpas = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4"
output_fig = "../figs/comparacao_gpm_mpas_blackstyle.png"

# Carrega os dados
ds_gpm = xr.open_dataset(path_gpm)
ds_mpas = xr.open_dataset(path_mpas)

# Precipitação diária
prec_gpm = ds_gpm['precipitation'].mean(dim='time') * 24
prec_mpas = (ds_mpas['rainc'] + ds_mpas['rainnc']).diff('Time').mean(dim='Time') * 8

lat = ds_mpas['latitude']
lon = ds_mpas['longitude']

# Escala de cores discreta
bounds = [0.0, 1.0, 1.5, 2, 2.5, 3, 4, 6, 8, 10, 14, 18, 22, 26, 30, 40, 50]
colors_gpm = [
    "#000000", "#e6e6ff", "#b3b3ff", "#6666ff", "#000066",
    "#004000", "#008000", "#00cc00", "#66ff66", "#ffff00",
    "#ffcc00", "#ff9900", "#ff3300", "#cc0000", "#990000",
    "#660000", "#bfbfbf"
]
cmap_gpm = ListedColormap(colors_gpm)
norm = BoundaryNorm(boundaries=bounds, ncolors=len(colors_gpm))

fig = plt.figure(figsize=(12, 5), facecolor='black')

# Painel GPM
ax1 = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
ax1.set_facecolor('black')
lon2d_gpm, lat2d_gpm = np.meshgrid(ds_gpm['lon'], ds_gpm['lat'])
cf1 = ax1.pcolormesh(lon2d_gpm, lat2d_gpm, prec_gpm.T, cmap=cmap_gpm, norm=norm)
ax1.add_feature(cfeature.COASTLINE.with_scale('110m'), edgecolor='white')
ax1.set_title('GPM – IMERG (0.1°)', color='white')
cb1 = plt.colorbar(cf1, ax=ax1, orientation='horizontal', pad=0.05, ticks=bounds)
cb1.set_label('mm/dia', color='white')
cb1.ax.xaxis.set_tick_params(color='white')
plt.setp(cb1.ax.get_xticklabels(), color='white')

# Painel MPAS
ax2 = plt.subplot(1, 2, 2, projection=ccrs.PlateCarree())
ax2.set_facecolor('black')
cf2 = ax2.pcolormesh(lon, lat, prec_mpas, cmap=cmap_gpm, norm=norm)
ax2.add_feature(cfeature.COASTLINE.with_scale('110m'), edgecolor='white')
ax2.set_title('MONAN/MPAS (10km)', color='white')
cb2 = plt.colorbar(cf2, ax=ax2, orientation='horizontal', pad=0.05, ticks=bounds)
cb2.set_label('mm/dia', color='white')
cb2.ax.xaxis.set_tick_params(color='white')
plt.setp(cb2.ax.get_xticklabels(), color='white')

plt.tight_layout()
plt.savefig(output_fig, dpi=300, facecolor=fig.get_facecolor())
ds_gpm.close()
ds_mpas.close()
