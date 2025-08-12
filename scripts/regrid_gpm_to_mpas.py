# Reamostragem (remapeamento) dos dados GPM para grade do MPAS
import os
import xarray as xr
import xesmf as xe

path_gpm = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/GPM/3B-HHR.MS.MRG.3IMERG.201010_1hour.nc4"
path_mpas = "/mnt/beegfs/saulo.freitas/runs/tmp/MPAS/runs/mpas.960mpi.4omp.1232.pbs-ha/mpas10km.nc4"

ds_gpm = xr.open_dataset(path_gpm)
ds_mpas = xr.open_dataset(path_mpas)

prec_gpm = ds_gpm["precipitation"]  # mantém tempo para média posterior
dest_grid = xr.Dataset({
    "lat": ds_mpas["latitude"],
    "lon": ds_mpas["longitude"]
})

weight_file = "../data_processed/weights_gpm_to_mpas.nc"

if os.path.exists(weight_file):
    print("[INFO] Usando pesos já existentes")
    regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear", reuse_weights=True, filename=weight_file)
else:
    print("[INFO] Gerando novos pesos")
    regridder = xe.Regridder(prec_gpm, dest_grid, "bilinear", periodic=True, filename=weight_file)

prec_gpm_on_mpas = regridder(prec_gpm)

ds_out = xr.Dataset({"precipitation": prec_gpm_on_mpas})
ds_out.to_netcdf("../data_processed/gpm_remap_to_mpas.nc")
print("[INFO] Arquivo salvo: ../data_processed/gpm_remap_to_mpas.nc")
