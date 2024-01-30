import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
from rasterio.plot import show, show_hist
import numpy as np


def plot_result(file_path, percent):
    with open(file_path, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()

    # Original image
    original = data_array.copy()

    min_val = np.percentile(data_array, percent)
    max_val = np.percentile(data_array, 100 - percent)
    data_array = np.clip(data_array, min_val, max_val)
    data_array = ((data_array - min_val) / (max_val - min_val)) * 255

    # Enhanced image
    enhanced = data_array

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    # Plot original and enhanced images
    axs[0, 0].set_title('Input Image')
    show(original, ax=axs[0, 0])
    axs[0, 1].set_title('Image after LCE')
    show(enhanced, ax=axs[0, 1])

    # Plot histograms
    axs[1, 0].set_title('Histogram of the Input Image')
    show_hist(original, ax=axs[1, 0])
    axs[1, 1].set_title('Histogram of the Image after LCE')
    show_hist(enhanced, ax=axs[1, 1])

    plt.show()
