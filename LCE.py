"""Notebook-compatible plotting helper for scientific index rasters."""
from functions2 import render_raster, stretch


def plot_result(file_path, percent=5):
    # Return ownership of the figure to the caller instead of displaying globally.
    return render_raster(file_path, 'ndvi', percent=percent)
