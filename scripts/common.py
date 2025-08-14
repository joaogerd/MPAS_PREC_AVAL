from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import os
import numpy as np
import xarray as xr
from scipy.fft import fft2, fftshift

# -----------------------------
# Paths & Logging
# -----------------------------
@dataclass(frozen=True)
class Paths:
    root: Path
    data_dir: Path
    figs_dir: Path

def resolve_paths(root: str | None = None) -> Paths:
    """
    Resolve project paths consistently.

    Args:
        root: Optional string path to the project root. If None, assumes
              this file is under <root>/scripts/common.py and climbs two levels.

    Returns:
        Paths: dataclass with resolved root, data_dir, figs_dir.
    """
    if root is None:
        # scripts/common.py -> scripts -> project root
        root_path = Path(__file__).resolve().parents[1]
    else:
        root_path = Path(root).resolve()

    data_dir = root_path / "data_processed"
    figs_dir = root_path / "figs"
    data_dir.mkdir(exist_ok=True, parents=True)
    figs_dir.mkdir(exist_ok=True, parents=True)
    return Paths(root=root_path, data_dir=data_dir, figs_dir=figs_dir)

def get_spatial_dims(da: xr.DataArray) -> tuple[str, str]:
    lat_names = {"lat", "latitude", "y"}
    lon_names = {"lon", "longitude", "x"}
    dims = da.dims
    lat_dim = next((d for d in dims if d.lower() in lat_names), None)
    lon_dim = next((d for d in dims if d.lower() in lon_names), None)
    if lat_dim is None or lon_dim is None:
        raise ValueError(f"Não foi possível detectar dimensões espaciais em: {dims}")
    return lat_dim, lon_dim


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        format="[%(levelname)s] %(message)s", level=level
    )

# -----------------------------
# Data helpers
# -----------------------------
def load_gpm(path: str | os.PathLike) -> xr.DataArray:
    ds = xr.open_dataset(path)
    try:
        return ds["precipitation"]
    except KeyError as exc:
        raise KeyError("Expected variable 'precipitation' in GPM file") from exc

def load_mpas_precip_daily(path: str | os.PathLike) -> xr.DataArray:
    """
    Load MPAS accumulated precipitation and convert to daily rate.

    It expects variables 'rainc' and 'rainnc' accumulated in time and a time
    dimension named either 'Time' or 'time'. We compute diff along time and
    then take the mean over time.

    Returns:
        xr.DataArray with precip [mm/day] on MPAS grid.
    """
    ds = xr.open_dataset(path)
    if "Time" in ds.dims:
        tname = "Time"
    elif "time" in ds.dims:
        tname = "time"
    else:
        raise KeyError("No time dimension named 'Time' or 'time' in MPAS dataset")

    rain = ds["rainc"] + ds["rainnc"]
    # diff along time -> mean over time -> scale factor (8 * 3h = 24h) if 3-hourly;
    # If cadence differs, user should pre-aggregate or adapt scale.
    d = rain.diff(tname).mean(tname)
    # Heurística: se step ~3h, multiplicar por 8 para mm/dia
    d = d * 8
    return d

# -----------------------------
# Spectral helpers
# -----------------------------
def compute_spectrum(field: np.ndarray) -> np.ndarray:
    ft = fft2(field)
    spec = np.abs(ft) ** 2
    return fftshift(spec)

def radial_mean(power_spectrum: np.ndarray) -> np.ndarray:
    ny, nx = power_spectrum.shape
    y, x = np.indices((ny, nx))
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)
    tbin = np.bincount(r.ravel(), power_spectrum.ravel())
    nr = np.bincount(r.ravel())
    return tbin / np.maximum(nr, 1)

def trim_edges(a: np.ndarray, n: int = 10) -> np.ndarray:
    if n <= 0:
        return a
    return a[n:-n, n:-n]

