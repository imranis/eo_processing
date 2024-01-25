import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
from rasterio.plot import show, show_hist
import numpy as np
import cv2


def plot_result_5_pct(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()

    min_val = np.percentile(data_array, 5)
    max_val = np.percentile(data_array, 95)
    data_array = np.clip(data_array, min_val, max_val)
    data_array = ((data_array - min_val) / (max_val - min_val)) * 255
    fig, (l, r) = plt.subplots(1, 2, figsize=(12, 5))
    show(data_array, cmap='gray', ax=l)
    show_hist(data_array, ax=r)
    plt.show()


def plot_result_10_pct(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()

    min_val = np.percentile(data_array, 10)
    max_val = np.percentile(data_array, 90)
    data_array = np.clip(data_array, min_val, max_val)
    data_array = ((data_array - min_val) / (max_val - min_val)) * 255
    fig, (l, r) = plt.subplots(1, 2, figsize=(12, 5))
    show(data_array, cmap='gray', ax=l)
    show_hist(data_array, ax=r)
    plt.show()
