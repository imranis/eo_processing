"""Satellite processing shared by the notebook and web UI.

Authentication belongs to the caller. Every operation uses the supplied connection.
"""
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from shapely.geometry import mapping

# Matplotlib's global state is not thread-safe across Streamlit sessions.
_PLOT_LOCK = RLock()

PRODUCTS = {
    'tcc': ('True colour', ['B04', 'B03', 'B02']),
    'tcc_masked': ('True colour · cloud masked', ['B04', 'B03', 'B02']),
    'fcc': ('False colour', ['B08', 'B04', 'B03']),
    'fcc_masked': ('False colour · cloud masked', ['B08', 'B04', 'B03']),
    'nbr': ('Normalised Burn Ratio', ['B08', 'B12']),
    'ndvi': ('Vegetation Index', ['B08', 'B04']),
    'sar': ('SAR backscatter', ['VV', 'VH']),
}

@dataclass
class ProcessingResult:
    product: str
    rasters: list[Path]
    preview: Path
    figure: object


def build_cube(connection, product, polygon, start_time, end_time):
    """Build a scientific-value cube; RGB order is explicit, never positional metadata."""
    bands = PRODUCTS[product][1]
    masked = product.endswith('_masked')
    cube = connection.load_collection(
        'SENTINEL1_GRD' if product == 'sar' else 'SENTINEL2_L2A',
        temporal_extent=[str(start_time), str(end_time)],
        spatial_extent=dict(zip(['west', 'south', 'east', 'north'], polygon.bounds)),
        bands=bands + (['SCL'] if masked else []),
    )
    if masked:
        scl = cube.band('SCL')
        mask = (scl == 3) | (scl == 8) | (scl == 9) | (scl == 10)
        cube = cube.filter_bands(bands).mask(mask.resample_cube_spatial(cube))
    if product == 'sar':
        cube = cube.sar_backscatter(coefficient='sigma0-ellipsoid').mean_time()
        cube = cube.apply(lambda x: 10 * x.log(base=10))
    else:
        cube = cube.mean_time()
        if product in ('nbr', 'ndvi'):
            cube = cube.band(bands[0]).normalized_difference(cube.band(bands[1]))
    return cube.mask_polygon(mapping(polygon))


def submit_product(connection, product, polygon, start_time, end_time):
    cube = build_cube(connection, product, polygon, start_time, end_time)
    job = cube.save_result(format='GTiff').create_job(title=f'EO Explorer · {product}')
    # Caller records the job before starting it, so a failed start never loses its ID.
    return job


def stretch(data, percent=5):
    values = np.asarray(np.ma.filled(data, np.nan), dtype=float)
    valid = np.isfinite(values)
    out = np.full(values.shape, np.nan)
    if valid.any():
        low, high = np.percentile(values[valid], [percent, 100 - percent])
        out[valid] = np.clip((values[valid] - low) / (high - low), 0, 1) if high > low else 0.5
    return out


def render_raster(path, product, percent=5):
    with _PLOT_LOCK:
        return _render_raster(path, product, percent)


def _render_raster(path, product, percent=5):
    from BCET import bcet
    with rasterio.open(path) as dataset:
        data = dataset.read(masked=True).astype(float).filled(np.nan)
    if not np.isfinite(data).any():
        raise ValueError('No valid pixels were found. Try another date range or area.')
    rgb = product.startswith(('tcc', 'fcc'))
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    if rgb:
        if data.shape[0] != 3:
            plt.close(fig)
            raise ValueError('Expected three ordered colour bands.')
        original = np.moveaxis(np.clip(data / 6000, 0, 1), 0, -1)
        enhanced = np.moveaxis(np.stack([bcet(0, 255, 110, band) / 255 for band in data]), 0, -1)
        alpha = np.all(np.isfinite(original), axis=-1).astype(float)
        axes[0, 0].imshow(np.dstack((np.nan_to_num(original), alpha)))
        axes[0, 1].imshow(np.dstack((np.nan_to_num(enhanced), alpha)))
        for channel, color in enumerate('rgb'):
            for ax, values in [(axes[1, 0], original[..., channel]), (axes[1, 1], enhanced[..., channel])]:
                ax.hist(values[np.isfinite(values)], bins=64, color=color, alpha=.45)
        axes[0, 1].set_title('BCET enhancement')
    elif product == 'sar':
        for i, band in enumerate(['VV', 'VH']):
            axes[0, i].imshow(data[i], cmap='gray', vmin=-30, vmax=0)
            axes[0, i].set_title(f'{band} sigma0 (dB)')
            axes[1, i].hist(data[i][np.isfinite(data[i])], bins=64)
    else:
        original, enhanced = data[0], stretch(data[0], percent)
        im = axes[0, 0].imshow(original, cmap='RdYlGn', vmin=-1, vmax=1)
        fig.colorbar(im, ax=axes[0, 0], shrink=.7)
        axes[0, 1].imshow(enhanced, cmap='RdYlGn', vmin=0, vmax=1)
        axes[0, 1].set_title('Linear contrast enhancement')
        for ax, values in [(axes[1, 0], original), (axes[1, 1], enhanced)]:
            ax.hist(values[np.isfinite(values)], bins=64)
    if product != 'sar':
        axes[0, 0].set_title(PRODUCTS[product][0])
    for ax in axes[0]:
        ax.axis('off')
    for ax in axes[1]:
        ax.set_title('Pixel histogram')
    fig.tight_layout()
    return fig


def collect_product(job, product, output_dir):
    target = Path(output_dir) / product
    target.mkdir(parents=True, exist_ok=True)
    files = job.get_results().download_files(target)
    rasters = [Path(p) for p in files if Path(p).suffix.lower() in ('.tif', '.tiff')]
    if not rasters:
        raise ValueError('The processing service returned no GeoTIFF result.')
    with _PLOT_LOCK:
        figure = render_raster(rasters[0], product)
        preview = target / f'{product}.png'
        try:
            figure.savefig(preview, dpi=120)
        except Exception:
            plt.close(figure)
            raise
    return ProcessingResult(product, rasters, preview, figure)


def process(connection, product, polygon, start_time, end_time, output_dir):
    """Blocking convenience API for notebooks; web UI polls jobs independently."""
    job = submit_product(connection, product, polygon, start_time, end_time)
    job.start_job()
    deadline = time.monotonic() + 3600
    while time.monotonic() < deadline:
        status = job.status()
        if status == 'finished':
            return collect_product(job, product, output_dir)
        if status in ('error', 'canceled'):
            raise RuntimeError(f'{product}: job {job.job_id} {status}')
        time.sleep(5)
    job.stop_job()
    raise TimeoutError(f'{product}: processing exceeded one hour and was stopped.')


def tcc(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'tcc', polygon, start_time, end_time, output_dir)


def fcc(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'fcc', polygon, start_time, end_time, output_dir)


def tcc_masked(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'tcc_masked', polygon, start_time, end_time, output_dir)


def fcc_masked(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'fcc_masked', polygon, start_time, end_time, output_dir)


def nbr(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'nbr', polygon, start_time, end_time, output_dir)


def ndvi(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'ndvi', polygon, start_time, end_time, output_dir)


def sar(connection, polygon, start_time, end_time, output_dir):
    return process(connection, 'sar', polygon, start_time, end_time, output_dir)
