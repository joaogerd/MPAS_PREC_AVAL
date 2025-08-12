# smooth_field.py
# ------------------------------------------------
# Suaviza campos de precipitação usando convolução 2D
# Entrada: NetCDF com campo de precipitação (lat/lon)
# Saída: NetCDF com campo suavizado
# ------------------------------------------------

import xarray as xr
import numpy as np
from scipy.ndimage import gaussian_filter

# --- Parâmetros ---
input_path = "data_processed/gpm_remap_to_mpas.nc"
output_path = "data_processed/gpm_smoothed.nc"
sigma = 1.0  # desvio padrão da suavização

# --- Carrega dado ---
ds = xr.open_dataset(input_path)
field = ds['precipitation']

# --- Aplica suavização ---
field_smooth = xr.apply_ufunc(
    gaussian_filter, field,
    input_core_dims=[["latitude", "longitude"]],
    kwargs={"sigma": sigma},
    dask="allowed",
    output_dtypes=[field.dtype]
)

# --- Salva resultado ---
ds_out = xr.Dataset({"precipitation": field_smooth})
ds_out.to_netcdf(output_path)
print(f"[INFO] Campo suavizado salvo em: {output_path}")

