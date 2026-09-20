"""Nodata-safe balanced contrast enhancement for display only."""
import numpy as np


def bcet(Gmin, Gmax, Gmean, x):
    values = np.asarray(np.ma.filled(np.ma.asarray(x, dtype=float), np.nan))
    valid = np.isfinite(values)
    out = np.full(values.shape, np.nan)
    if not valid.any():
        return out
    data = values[valid]
    low, high, mean = data.min(), data.max(), data.mean()
    if high == low:
        out[valid] = Gmean
        return out
    mean_square = np.mean(data ** 2)
    denominator = 2 * (high * (Gmean - Gmin) - mean * (Gmax - Gmin) + low * (Gmax - Gmean))
    if abs(denominator) < 1e-12:
        out[valid] = Gmin + (data - low) / (high - low) * (Gmax - Gmin)
        return out
    b = (high ** 2 * (Gmean - Gmin) - mean_square * (Gmax - Gmin) + low ** 2 * (Gmax - Gmean)) / denominator
    divisor = (high - low) * (high + low - 2 * b)
    if abs(divisor) < 1e-12:
        out[valid] = Gmin + (data - low) / (high - low) * (Gmax - Gmin)
    else:
        a = (Gmax - Gmin) / divisor
        out[valid] = np.clip(a * (data - b) ** 2 + Gmin - a * (low - b) ** 2, Gmin, Gmax)
    return out
