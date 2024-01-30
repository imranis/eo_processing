import openeo
import shapely.geometry
import LCE
import BCET


def ndvi():
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
            temporal_extent=["2020-01-01", "2020-01-10"],
            spatial_extent=dict(zip(["west", "south", "east", "north"], bbox)),
            bands=["B02", "B03", "B04", "B08"]))

    nir = cube.band('B08')
    red = cube.band('B04')

    ndvi = (nir - red)/(nir + red)
    ndvi = ndvi.max_time()

    ndvi.download('ndvi_example.tiff', format='GTIFF')
    LCE.plot_result_5_pct('ndvi_example.tiff')
    BCET.plot_result_bcet('ndvi_example.tiff')
