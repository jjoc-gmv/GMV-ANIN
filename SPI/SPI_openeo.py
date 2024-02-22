import openeo
from openeo_utils.utils import *

connection = get_connection()
temporal_extent = ["1980-01-01", "2023-03-01"]
spatial_extent = spatial_extent_south_africa

# load_collection_stac = connection.load_stac(  # TODO: Use stac with collection name
#     url="/data/users/Public/victor.verhaert/ANINStac/ERA5-Land-monthly-averaged-data-v2/collection.json",
#     temporal_extent=temporal_extent,
#     spatial_extent=spatial_extent,
#     bands=['total_precipitation'],
# )

glob_pattern = f"/data/users/Public/emile.sonneveld/ERA5-Land-monthly-averaged-data-ANIN/tiff_collection/*/*/*/*_tp.tif"
assert_glob_ok(glob_pattern)
load_collection = connection.load_disk_collection(
    format="GTiff",
    # Based on https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means
    glob_pattern=glob_pattern,
    options=dict(date_regex=r".*(\d{4})-(\d{2})-(\d{2}).*"),
)
load_collection._pg.arguments["featureflags"] = {"tilesize": 16}  # TODO: combine with load_stac
ERA5_dc = load_collection
# resolution = 0.00297619047619  # 300m in degrees LatLon
# ERA5_dc = ERA5_dc.resample_spatial(resolution=resolution, projection=4326)
ERA5_dc *= 1.0

geojson = load_south_africa_geojson()
# geojson = load_johannesburg_geojson()
ERA5_dc = ERA5_dc.filter_spatial(geojson)

UDF_code = load_udf(os.path.join(os.path.dirname(__file__), "SPI_UDF.py"))
SPI_dc = ERA5_dc.apply_dimension(dimension="t", code=UDF_code, runtime="Python")
SPI_dc = SPI_dc.rename_labels("bands", ["SPI"])

previous_month_UDF_code = load_udf(os.path.join(os.path.dirname(__file__), "previous_month_UDF.py"))
SPI_previous_month_dc = SPI_dc.apply_dimension(dimension="t", code=previous_month_UDF_code, runtime="Python")
SPI_previous_month_dc = SPI_previous_month_dc.rename_labels("bands", ["SPI_previous_month"])


def main(temporal_extent_argument):
    global SPI_dc
    SPI_dc = SPI_dc.filter_temporal(temporal_extent_argument)
    custom_execute_batch(SPI_dc)
    # custom_execute_batch(load_collection_stac)
    # custom_execute_batch(ERA5_dc, out_format="netCDF")


if __name__ == "__main__":
    main(get_temporal_extent_from_argv(temporal_extent))
