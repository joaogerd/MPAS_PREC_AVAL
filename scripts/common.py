from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import numpy as np
import xarray as xr
from scipy.fft import fft2, fftshift

__all__ = [
    "Paths",
    "resolve_paths",
    "pick_latlon",
    "setup_logging",
    "print_field_stats",
    "compute_spectrum",
    "radial_mean",
    "trim_edges",
]

# -----------------------------
# Paths & Logging
# -----------------------------
@dataclass(frozen=True)
class Paths:
    """Container for common project paths."""
    root: Path
    data_dir: Path
    figs_dir: Path


def resolve_paths(root: str | None = None) -> Paths:
    """
    Resolve project paths consistently.

    Parameters
    ----------
    root : str or None, optional
        Optional path to the project root. If None, assumes this file is
        under <root>/scripts/common.py and climbs two levels.

    Returns
    -------
    Paths
        Dataclass with resolved root, data_dir, figs_dir.
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


def pick_latlon(ds: xr.Dataset) -> tuple[str, str]:
    """
    Identify latitude and longitude variable names in an xarray Dataset.

    Searches for common variants used in MPAS, GPM, and postprocessed outputs,
    returning the first match for each coordinate.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset containing latitude and longitude variables or coordinates.

    Returns
    -------
    tuple of str
        (lat_name, lon_name)

    Raises
    ------
    KeyError
        If no matching latitude/longitude names are found.
    """
    lat_candidates = ("lat", "latitude", "XLAT", "XLAT_M", "y")
    lon_candidates = ("lon", "longitude", "XLONG", "XLONG_M", "x")

    lat_name = next((n for n in lat_candidates if n in ds), None)
    lon_name = next((n for n in lon_candidates if n in ds), None)
    if lat_name and lon_name:
        return lat_name, lon_name

    # Some files expose lat/lon as coords (not data variables)
    lat_name = next((n for n in lat_candidates if n in ds.coords), lat_name)
    lon_name = next((n for n in lon_candidates if n in ds.coords), lon_name)
    if lat_name and lon_name:
        return lat_name, lon_name

    raise KeyError("Could not find latitude/longitude in dataset "
                   f"(tried {lat_candidates} / {lon_candidates}).")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure global logging format and level."""
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=level)

# -----------------------------
# Data helpers
# -----------------------------
def print_field_stats(field, label: str = "") -> None:
    """
    Print basic statistics for a field (precipitation or generic numeric array).

    Parameters
    ----------
    field : xarray.DataArray or numpy.ndarray
        Field to analyze.
    label : str, optional
        Optional label to include in the printed output header.

    Raises
    ------
    TypeError
        If `field` is not a DataArray or ndarray.
    """
    if isinstance(field, xr.DataArray):
        values = field.values
    elif isinstance(field, np.ndarray):
        values = field
    else:
        raise TypeError(f"Unsupported field type: {type(field)}")

    print(f"[STATS] {label}")
    print(f"  Shape: {values.shape}")
    print(f"  Min:   {np.nanmin(values):.4f}")
    print(f"  Max:   {np.nanmax(values):.4f}")
    print(f"  Mean:  {np.nanmean(values):.4f}")
    print(f"  Std:   {np.nanstd(values):.4f}")
    print(f"  NaNs:  {np.isnan(values).sum()}")


# -----------------------------
# Spectral helpers
# -----------------------------
def compute_spectrum(field: np.ndarray) -> np.ndarray:
    """
    Compute the 2D power spectrum of a field.

    If the field is 3D (time, y, x), the mean is taken over the time dimension
    before computing the spectrum.

    Parameters
    ----------
    field : np.ndarray
        2D or 3D array. For 3D, the first dimension is assumed to be time.

    Returns
    -------
    np.ndarray
        2D power spectrum (fftshifted).

    Raises
    ------
    ValueError
        If the input is not 2D or 3D.
    """
    if field.ndim == 3:
        field = field.mean(axis=0)
    elif field.ndim != 2:
        raise ValueError(f"Expected a 2D or 3D array, got {field.ndim}D with shape {field.shape}")

    field = np.asarray(field)
    fft = np.fft.fft2(field)
    fft_shifted = np.fft.fftshift(fft)
    power_spectrum = np.abs(fft_shifted) ** 2
    return power_spectrum


def radial_mean(power_spectrum: np.ndarray) -> np.ndarray:
    """
    Compute the azimuthal (radial) mean of a 2D power spectrum.

    Parameters
    ----------
    power_spectrum : np.ndarray
        2D power spectrum.

    Returns
    -------
    np.ndarray
        1D radial profile.

    Raises
    ------
    ValueError
        If the input is not 2D.
    """
    if power_spectrum.ndim != 2:
        raise ValueError(f"Expected a 2D array, got {power_spectrum.ndim}D with shape {power_spectrum.shape}")

    ny, nx = power_spectrum.shape
    y, x = np.indices((ny, nx))
    center_y, center_x = ny // 2, nx // 2
    r = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2).astype(int)

    tbin = np.bincount(r.ravel(), power_spectrum.ravel())
    nr = np.bincount(r.ravel())
    return tbin / np.maximum(nr, 1)

def trim_edges(a: np.ndarray, n: int = 10) -> np.ndarray:
    """
    Trim n pixels from each border of a 2D array.

    Parameters
    ----------
    a : np.ndarray
        2D array.
    n : int, optional
        Number of pixels to trim from each edge. Default is 10.

    Returns
    -------
    np.ndarray
        Trimmed 2D array.
    """
    if n <= 0:
        return a
    return a[n:-n, n:-n]

