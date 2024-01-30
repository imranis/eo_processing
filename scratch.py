import openeo
import shapely.geometry
from openeo.processes import ProcessBuilder

connection = openeo.connect(url='openeo.dataspace.copernicus.eu').authenticate_oidc()
minx = 100.85
miny = 4.25
maxx = 101.05
maxy = 4.45
square = [(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)]
polygon = shapely.geometry.Polygon(square)
bbox = polygon.bounds

cube = (
    connection.load_collection(
        "SENTINEL2_L2A",
        temporal_extent=["2023-10-01", "2024-01-01"],
        spatial_extent=dict(zip(["west", "south", "east", "north"], bbox)),
        bands=["B03", "B04", "B08"]))

# red = cube.band('B04')
# green = cube.band('B03')
# nir = cube.band('B08')

# cube_b8 = cube.filter_bands(band=['B08']).reduce_dimension(dimension="t", reducer="mean")
# cube_b3 = cube.filter_bands(band=['B03']).reduce_dimension(dimension="t", reducer="mean")
# cube_b4 = cube.filter_bands(band=['B04']).reduce_dimension(dimension="t", reducer="mean")

cube_b348_reduced = cube.mean_time()


def scale_function(x: ProcessBuilder):
    return x.linear_scale_range(0, 6000, 0, 255)


cube_b348_reduced_lin = cube_b348_reduced.apply(scale_function)

res = cube_b348_reduced_lin.save_result(format="PNG", options={
        "red": "B8",
        "green": "B4",
        "blue": "B3"
      })

job = res.create_job(title="temporal_mean_as_PNG_py")
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

    # Check if the image is grayscale or RGB
    if len(img.shape) == 2:  # Grayscale image
        Output = BCET(Gmin, Gmax, Gmean, img)
        plt.imshow(Output, cmap='gray')
        plt.title('Image after BCET')
        plt.show()

    elif img.shape[2] == 1:  # Single-channel image
        Output = BCET(Gmin, Gmax, Gmean, img[:, :, 0])
        plt.imshow(Output, cmap='gray')
        plt.title('Image after BCET')
        plt.show()

    else:  # RGB image
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
