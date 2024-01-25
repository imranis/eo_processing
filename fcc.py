import openeo
import shapely.geometry
from openeo.processes import ProcessBuilder
import LCE
import BCET

connection = openeo.connect(url='openeo.dataspace.copernicus.eu').authenticate_oidc()
minx = 101.52
miny = 3.02
maxx = 101.72
maxy = 3.22
square = [(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)]
polygon = shapely.geometry.Polygon(square)
bbox = polygon.bounds

cube = (
    connection.load_collection(
        "SENTINEL2_L2A",
        temporal_extent=["2023-01-16", "2023-01-19"],
        spatial_extent=dict(zip(["west", "south", "east", "north"], bbox)),
        bands=["B03", "B04", "B08"]))

# red = cube.band('B04')
# green = cube.band('B03')
# nir = cube.band('B08')

# cube_b8 = cube.filter_bands(band=['B08']).reduce_dimension(dimension="t", reducer="mean")
# cube_b3 = cube.filter_bands(band=['B03']).reduce_dimension(dimension="t", reducer="mean")
# cube_b4 = cube.filter_bands(band=['B04']).reduce_dimension(dimension="t", reducer="mean")

cube_b348_reduced = cube.max_time()


def scale_function(x: ProcessBuilder):
    return x.linear_scale_range(0, 6000, 0, 255)


cube_b348_reduced_lin = cube_b348_reduced.apply(scale_function)

res = cube_b348_reduced_lin.save_result(format="PNG", options={
        "red": "B8",
        "green": "B4",
        "blue": "B3"
      })

res.download('fcc_example.png', format='PNG')
BCET.plot_result_bcet('fcc_example.png')

# job = res.create_job(title="temporal_mean_as_PNG_py")
