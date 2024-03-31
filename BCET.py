import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
import numpy as np


def BCET(Gmin, Gmax, Gmean, img):
    # Mask out zero values
    img_nonzero = img[img != 0]

    Lmin = np.min(img_nonzero)
    Lmax = np.max(img_nonzero)
    Lmean = np.mean(img_nonzero)
    LMssum = np.mean(np.square(img_nonzero))

    bnum = Lmax**2 * (Gmean - Gmin) - LMssum * (Gmax - Gmin) + Lmin**2 * (Gmax - Gmean)
    bden = 2 * (Lmax * (Gmean - Gmin) - Lmean * (Gmax - Gmin) + Lmin * (Gmax - Gmean))

    b = bnum / bden
    a = (Gmax - Gmin) / ((Lmax - Lmin) * (Lmax + Lmin - 2 * b))
    c = Gmin - a * (Lmin - b)**2

    # Apply BCET only to non-zero values
    y = np.zeros_like(img)
    y[img != 0] = a * (img[img != 0] - b)**2 + c
    return y.astype(np.uint8)


def read_this(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()
# if image is RGB, data_array has form (band, height, width)
# if image is grayscale, data_array has form (height, width)
    # Check if the image is grayscale or RGB
    if data_array.shape[0] == 1:  # Grayscale image
        data_array = data_array[0]
        img_type = 'grayscale'
    else:  # RGB image
        data_array = data_array.transpose((1, 2, 0))
        img_type = 'rgb'

    return data_array, img_type


def plot_result_bcet(file_path):
    img, img_type = read_this(file_path)
    Gmin = 0
    Gmax = 255
    Gmean = 120

    # Process the image based on its type
    if img_type == 'grayscale':  # Grayscale image
        Output = BCET(Gmin, Gmax, Gmean, img)
    else:  # RGB image
        R = BCET(Gmin, Gmax, Gmean, img[:, :, 0])
        G = BCET(Gmin, Gmax, Gmean, img[:, :, 1])
        B = BCET(Gmin, Gmax, Gmean, img[:, :, 2])
        Output = np.stack([R, G, B], axis=2)

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    axs[0, 0].imshow(img, cmap='gray' if img_type == 'grayscale' else None)
    axs[0, 0].set_title('Input Image')
    axs[0, 1].imshow(Output, cmap='gray' if img_type == 'grayscale' else None)
    axs[0, 1].set_title('Image after BCET')

    colors = ['r', 'g', 'b']
    for i, color in enumerate(colors):
        axs[1, 0].hist(img.flatten(), bins=256, color=color, alpha=0.5)
        axs[1, 1].hist(Output.flatten(), bins=256, color=color, alpha=0.5)

    plt.show()
