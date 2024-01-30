import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
import numpy as np
import cv2


def BCET(Gmin, Gmax, Gmean, img):
    Lmin = np.min(img)
    Lmax = np.max(img)
    Lmean = np.mean(img)
    LMssum = np.mean(np.square(img))

    bnum = Lmax**2 * (Gmean - Gmin) - LMssum * (Gmax - Gmin) + Lmin**2 * (Gmax - Gmean)
    bden = 2 * (Lmax * (Gmean - Gmin) - Lmean * (Gmax - Gmin) + Lmin * (Gmax - Gmean))

    b = bnum / bden
    a = (Gmax - Gmin) / ((Lmax - Lmin) * (Lmax + Lmin - 2 * b))
    c = Gmin - a * (Lmin - b)**2

    y = a * (img - b)**2 + c
    return y.astype(np.uint8)


def read_this(file_path, gray_scale=False):
    with open(file_path, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()

    if gray_scale:
        data_array = cv2.cvtColor(data_array.transpose((1, 2, 0)), cv2.COLOR_RGB2GRAY)
    else:
        data_array = data_array.transpose((1, 2, 0))
    return data_array


def plot_result_bcet(file_path):
    img = read_this(file_path)
    Gmin = 0
    Gmax = 255
    Gmean = 120

# RGB image
    R = BCET(Gmin, Gmax, Gmean, img[:, :, 0])
    G = BCET(Gmin, Gmax, Gmean, img[:, :, 1])
    B = BCET(Gmin, Gmax, Gmean, img[:, :, 2])

    Output = np.stack([R, G, B], axis=2)

    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    axs[0, 0].imshow(img)
    axs[0, 0].set_title('Input Image')
    axs[0, 1].imshow(Output)
    axs[0, 1].set_title('Image after BCET')

    colors = ['r', 'g', 'b']
    for i, color in enumerate(colors):
        axs[1, 0].hist(img[:, :, i].flatten(), bins=256, color=color, alpha=0.5)
        axs[1, 1].hist(Output[:, :, i].flatten(), bins=256, color=color, alpha=0.5)

    axs[1, 0].set_title('Histogram of the Input Image')
    axs[1, 1].set_title('Histogram of the Image after BCET')
    plt.show()
