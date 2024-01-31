import openeo
from ipywidgets import Button, DatePicker
import LCE
import BCET
from openeo.processes import ProcessBuilder
import matplotlib.pyplot as plt
import xarray as xr

# Create date picker widgets for the start and end time
start_time_picker = DatePicker(description='Start Time')
end_time_picker = DatePicker(description='End Time')


# Create a button for the user to click when they have picked the dates
button = Button(description='Done')


def tcc(polygon, start_time, end_time):
    # Define a function to execute when the button is clicked
    def on_button_clicked(b):
        connection = openeo.connect(url='openeo.dataspace.copernicus.eu').authenticate_oidc()

        # Get the bounding box of the polygon
        bbox = polygon.bounds

        cube = (connection.load_collection(
            "SENTINEL2_L2A",
            temporal_extent=[start_time, end_time],
            spatial_extent=dict(zip(["west", "south", "east", "north"], bbox)),
            bands=["B02", "B03", "B04"]))

        cube_b234_reduced = cube.mean_time()

        def scale_function(x: ProcessBuilder):
            return x.linear_scale_range(0, 6000, 0, 255)

        cube_b234_reduced_lin = cube_b234_reduced.apply(scale_function)

        res = cube_b234_reduced_lin.save_result(format="GTIFF", options={
            "red": "B4",
            "green": "B3",
            "blue": "B2"
        })

        res.download('tcc_example.tiff', format='GTIFF')
        BCET.plot_result_bcet('tcc_example.tiff')
        LCE.plot_result('tcc_example.tiff', 10)

    button.on_click(on_button_clicked)


def sar(polygon, start_time, end_time):
    # Define a function to execute when the button is clicked
    def on_button_clicked(b):
        connection = openeo.connect(url='openeo.dataspace.copernicus.eu').authenticate_oidc()

        bbox = polygon.bounds

        cube = (connection.load_collection(
            "SENTINEL1_GRD",
            temporal_extent=[start_time, end_time],
            spatial_extent=dict(zip(["west", "south", "east", "north"], bbox)),
            bands=["VV", "VH"]))

        s1bs_linear = cube.sar_backscatter(coefficient="sigma0-ellipsoid")
        s1bs = s1bs_linear.apply(lambda x: 10 * x.log(base=10))
        s1bs.download("sar_example.nc", format="NetCDF")
        s1bs_netcdf = s1bs.save_result(format="NetCDF")

        job_bs = s1bs_netcdf.create_job(title="SAR_backscatter")
        job_id_bs = job_bs.job_id

        if job_id_bs:
            print("Batch job created with id: ", job_id_bs)
            job_bs.start_job()
        else:
            print("Error! Job ID is None")

        job_bs = connection.job(job_id_bs)
        job_description = job_bs.describe_job()
        print("Batch job with id: ", job_id_bs, ' is ', job_description['status'])

        job_bs.get_results()

        S1_ard = xr.open_dataset("sar_example.nc")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 20))
        ax1.imshow(S1_ard.VV[0].values, cmap='Greys_r', vmin=-30, vmax=30)
        ax1.set_title('VV gamma0')
        ax2.imshow(S1_ard.VH[0].values, cmap='Greys_r', vmin=-30, vmax=30)
        ax2.set_title('VH gamma0')
        plt.show()

    button.on_click(on_button_clicked)
