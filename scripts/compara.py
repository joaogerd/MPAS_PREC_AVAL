import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

# ==============================================================
# Script de comparação visual entre dados de precipitação do GPM
# (IMERG) e simulação do modelo MONAN/MPAS com grade lat-lon.
# Os campos representados são médias diárias (mm/dia).
# ==============================================================

# --- Caminhos dos arquivos (ajuste conforme necessário) ---
path_gpm = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/GPM/3B-HHR.MS.MRG.3IMERG.201010_1hour.nc4"
path_mpas = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4"

# --- Carrega os arquivos NetCDF ---
ds_gpm = xr.open_dataset(path_gpm)  # Dataset GPM com precipitação horária
ds_mpas = xr.open_dataset(path_mpas)  # Dataset MPAS com acumulados 3h

# --- Calcula média de precipitação para o período (em mm/dia) ---
# GPM: média horária ao longo do tempo e multiplicado por 24 para obter mm/dia
prec_gpm = ds_gpm['precipitation'].mean(dim='time') * 24

# MPAS: média diária a partir do acumulado de 3h (rainc + rainnc)
# A diferença entre tempos consecutivos remove acúmulo contínuo, e multiplica-se por 8 para obter mm/dia
prec_mpas = (ds_mpas['rainc'] + ds_mpas['rainnc']).diff('Time').mean(dim='Time') * 8

# --- Coordenadas geográficas do MPAS (grade regular lat-lon) ---
lat = ds_mpas['latitude']
lon = ds_mpas['longitude']

# --- Escala de cores discreta compatível com visualização usada por Saulo ---
# Limites (bounds) definem os intervalos para a colormap. Valores abaixo de 1.0 mm/dia recebem cor preta.
bounds = [0.0, 1.0, 1.5, 2, 2.5, 3, 4, 6, 8, 10, 14, 18, 22, 26, 30, 40, 50]
colors_gpm = [
    "#000000",  # < 1.0 mm/dia (preto)
    "#e6e6ff", "#b3b3ff", "#6666ff", "#000066",
    "#004000", "#008000", "#00cc00", "#66ff66",
    "#ffff00", "#ffcc00", "#ff9900", "#ff3300",
    "#cc0000", "#990000", "#660000", "#bfbfbf"
]
cmap_gpm = ListedColormap(colors_gpm)
norm = BoundaryNorm(boundaries=bounds, ncolors=len(colors_gpm))

# --- Cria figura com dois painéis lado a lado (GPM e MPAS) ---
fig = plt.figure(figsize=(12, 5), facecolor='black')

# =============================
# Painel 1 – Precipitação GPM
# =============================
ax1 = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
ax1.set_facecolor('black')
lon2d_gpm, lat2d_gpm = np.meshgrid(ds_gpm['lon'], ds_gpm['lat'])
cf1 = ax1.pcolormesh(lon2d_gpm, lat2d_gpm, prec_gpm.T, cmap=cmap_gpm, norm=norm)
ax1.add_feature(cfeature.COASTLINE.with_scale('110m'), edgecolor='white')
ax1.set_title('GPM – IMERG (0.1dg)', color='white', fontsize=12)
cb1 = plt.colorbar(cf1, ax=ax1, orientation='horizontal', pad=0.05, ticks=bounds[1:])
cb1.set_label('mm/dia', color='white')
cb1.ax.xaxis.set_tick_params(color='white')
plt.setp(plt.getp(cb1.ax.axes, 'xticklabels'), color='white')

# ==============================
# Painel 2 – Precipitação MPAS
# ==============================
ax2 = plt.subplot(1, 2, 2, projection=ccrs.PlateCarree())
ax2.set_facecolor('black')
cf2 = ax2.pcolormesh(lon, lat, prec_mpas, cmap=cmap_gpm, norm=norm)
ax2.add_feature(cfeature.COASTLINE.with_scale('110m'), edgecolor='white')
ax2.set_title('MONAN/MPAS (10km)', color='white', fontsize=12)
cb2 = plt.colorbar(cf2, ax=ax2, orientation='horizontal', pad=0.05, ticks=bounds[1:])
cb2.set_label('mm/dia', color='white')
cb2.ax.xaxis.set_tick_params(color='white')
plt.setp(plt.getp(cb2.ax.axes, 'xticklabels'), color='white')

# --- Finaliza layout e salva figura ---
plt.tight_layout()
plt.savefig("comparacao_gpm_mpas_blackstyle.png", dpi=300, facecolor=fig.get_facecolor())

# --- Fecha arquivos NetCDF para evitar mensagens de erro ---
ds_gpm.close()
ds_mpas.close()

#plt.show()  # Descomente para exibir na tela (modo interativo)
