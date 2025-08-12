import xarray as xr
import numpy as np
import scipy.ndimage
import os

# Caminhos de entrada/saída
data_dir = "../data_processed"
input_file = os.path.join(data_dir, "gpm_remap_to_mpas.nc")
output_file = os.path.join(data_dir, "gpm_smoothed.nc")

# Carrega os dados
print("[INFO] Lendo dados de entrada:", input_file)
ds = xr.open_dataset(input_file)
prec = ds["precipitation"]

# Aplica média móvel 3x3
print("[INFO] Aplicando média móvel 3x3...")
mov_avg = prec.copy(deep=True)
mov_avg.data = scipy.ndimage.uniform_filter(prec.data, size=3, mode='nearest')

# Aplica filtro gaussiano 3x3
print("[INFO] Aplicando filtro Gaussiano 3x3...")
gauss = prec.copy(deep=True)
gauss.data = scipy.ndimage.gaussian_filter(prec.data, sigma=1.0, mode='nearest')

# Salva resultados em novo NetCDF
print("[INFO] Salvando resultados em:", output_file)
ds_out = xr.Dataset({
    "precipitation_original": prec,
    "precipitation_movavg3x3": mov_avg,
    "precipitation_gauss3x3": gauss,
})
ds_out.to_netcdf(output_file)
ds.close()

print("[INFO] Suavizações salvas com sucesso!")

