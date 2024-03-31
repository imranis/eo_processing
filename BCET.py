import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import netCDF4 as nc


def bcet(Gmin, Gmax, Gmean, x):
    x = x.astype(float)
    mask = (x != 0)  # Create a mask for non-black pixels
    x_masked = x[mask]

    Lmin = np.min(x_masked)
    Lmax = np.max(x_masked)
    Lmean = np.mean(x_masked)
    LMssum = np.mean(x_masked**2)

    bnum = Lmax**2 * (Gmean - Gmin) - LMssum * (Gmax - Gmin) + Lmin**2 * (Gmax - Gmean)
    bden = 2 * (Lmax * (Gmean - Gmin) - Lmean * (Gmax - Gmin) + Lmin * (Gmax - Gmean))

    b = bnum / bden

    a = (Gmax - Gmin) / ((Lmax - Lmin) * (Lmax + Lmin - 2 * b))

    c = Gmin - a * (Lmin - b)**2

    y = a * (x - b)**2 + c
    return np.uint8(y)


def plot_bcet(nc_file_path):
    # Load the NetCDF file
    nc_data = nc.Dataset(nc_file_path)

    # for var_name in nc_data.variables:
    #     print(var_name)

    variable_names = list(nc_data.variables.keys())

    # Read the RGB bands data
    blue = nc_data.variables[variable_names[3]][:]
    green = nc_data.variables[variable_names[4]][:]
    red = nc_data.variables[variable_names[5]][:]

    # Define BCET parameters
    Gmin = 0
    Gmax = 255
    Gmean = 110

    # Apply BCET to each RGB band
    bcet_blue = bcet(Gmin, Gmax, Gmean, blue)
    bcet_green = bcet(Gmin, Gmax, Gmean, green)
    bcet_red = bcet(Gmin, Gmax, Gmean, red)

    # Combine the three bands into one RGB image
    rgb_image = np.dstack((bcet_red, bcet_green, bcet_blue))

    # Plot the RGB image and its histogram
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

    axes[0].imshow(rgb_image)
    axes[0].set_title("Masked Image after BCET")
    axes[0].axis('off')

    sns.histplot(rgb_image[..., 0].ravel(), bins=50, color='r', label='Red', ax=axes[1], alpha=0.7)
    sns.histplot(rgb_image[..., 1].ravel(), bins=50, color='g', label='Green', ax=axes[1], alpha=0.7)
    sns.histplot(rgb_image[..., 2].ravel(), bins=50, color='b', label='Blue', ax=axes[1], alpha=0.7)
    axes[1].set_title("Image Histogram")
    axes[1].legend()

    plt.tight_layout()
    plt.show()


def plot_input(nc_file_path):
    # Load the NetCDF file
    nc_data = nc.Dataset(nc_file_path)

    variable_names = list(nc_data.variables.keys())

    # Read the RGB bands data
    blue = nc_data.variables[variable_names[3]][:]
    green = nc_data.variables[variable_names[4]][:]
    red = nc_data.variables[variable_names[5]][:]

    # Combine the three bands into one RGB image
    rgb_image = np.dstack((red, green, blue))

    # Plot the RGB image and its histogram
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

    axes[0].imshow(rgb_image)
    axes[0].set_title("Unmasked Image")

    sns.histplot(rgb_image[..., 0].ravel(), bins=50, color='r', label='Red', ax=axes[1], alpha=0.7)
    sns.histplot(rgb_image[..., 1].ravel(), bins=50, color='g', label='Green', ax=axes[1], alpha=0.7)
    sns.histplot(rgb_image[..., 2].ravel(), bins=50, color='b', label='Blue', ax=axes[1], alpha=0.7)
    axes[1].set_title("Image Histogram")
    axes[1].legend()

    plt.tight_layout()
    plt.show()
