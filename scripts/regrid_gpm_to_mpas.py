import os
import xarray as xr
import xesmf as xe

# =====================================================
# Script para reamostrar o campo de precipitação GPM
# (originalmente em grade lat-lon 0.1°) para a grade
# do modelo MPAS (lat/lon regular ou Voronoi).
# Gera um novo arquivo NetCDF com GPM reamostrado,
# preservando a dimensão temporal.
# =====================================================

# --- Caminhos dos arquivos de entrada ---
path_gpm = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/GPM/3B-HHR.MS.MRG.3IMERG.201010_1hour.nc4"
path_mpas = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4"

# --- Carrega os dados ---
ds_gpm = xr.open_dataset(path_gpm)
ds_mpas = xr.open_dataset(path_mpas)

# --- Mantém o campo de precipitação com a dimensão temporal ---
prec_gpm = ds_gpm['precipitation']

# --- Coordenadas da grade de destino (MPAS) ---
dest_grid = xr.Dataset({
    "lat": ds_mpas["latitude"],
    "lon": ds_mpas["longitude"]
})

# --- Define nome do arquivo de pesos ---
weight_file = "weights_gpm_to_mpas.nc"

# --- Cria ou reutiliza os pesos para o regrid ---
if os.path.exists(weight_file):
    print("[INFO] Usando pesos de regrid já existentes.")
    regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear", reuse_weights=True, filename=weight_file)
else:
    print("[INFO] Criando novos pesos de regrid.")
    regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear", periodic=True, filename=weight_file)

# --- Aplica regrid ponto-a-ponto no tempo ---
prec_gpm_on_mpas = regridder(prec_gpm)

# --- Salva o resultado remapeado com tempo preservado ---
ds_out = xr.Dataset({
    "precipitation": prec_gpm_on_mpas
})
ds_out.to_netcdf("gpm_remap_to_mpas.nc")

print("[INFO] Arquivo salvo: gpm_remap_to_mpas.nc")

