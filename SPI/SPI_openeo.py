import openeo
from openeo_utils.utils import *

connection = get_connection()

# ERA5_dc = connection.load_collection(
#     "AGERA5",
#     temporal_extent=["2015-01-01", "2023-07-01"],
#     spatial_extent={  # South Africa
#         "west": 10,
#         "south": -40,
#         "east": 40,
#         "north": -20,
#     },
#     bands=["precipitation-flux"],
# )

# ERA5_dc = connection.load_disk_collection(
#     format="GTiff",
#     glob_pattern="/data/users/Public/johan.schreurs/ANIN/reanalysis-era5-land_southafrica_float32/*/reanalysis-era5-land_total_precipitation_*.tif",
#     options=dict(date_regex=r".*reanalysis-era5-land_.*_(\d{4})(\d{2})(\d{2}).tif"),
# )  # reanalysis-era5-land_10m_u_component_of_wind_20220101.tif

ERA5_dc = connection.load_disk_collection(
    format="GTiff",
    # Based on https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means
    glob_pattern="/data/users/Public/emile.sonneveld/ERA5-Land-monthly-averaged-data/tiff_collection/*/*/*/*_total_precipitation.tiff",
    options=dict(date_regex=r".*tiff_collection/(\d{4})/(\d{2})/(\d{2})/.*"),
).filter_temporal(
    "1970-01-01", "2023-01-01"
)  # Latest: 2023-05-01

ERA5_dc = ERA5_dc.aggregate_temporal_period("month", reducer="sum")

# SPI_dc = ERA5_dc
UDF_code = load_udf(os.path.join(os.path.dirname(__file__), "SPI_UDF.py"))
SPI_dc = ERA5_dc.apply_dimension(dimension="t", code=UDF_code, runtime="Python")
SPI_dc = SPI_dc.rename_labels("bands", ["SPI"])

previous_month_UDF_code = load_udf(
    os.path.join(os.path.dirname(__file__), "previous_month_UDF.py")
)
SPI_previous_month_dc = SPI_dc.apply_dimension(
    dimension="t", code=previous_month_UDF_code, runtime="Python"
)
SPI_previous_month_dc = SPI_previous_month_dc.rename_labels(
    "bands", ["SPI_previous_month"]
)

if __name__ == "__main__":
    geojson = load_south_africa_geojson()
    # geojson = load_johannesburg_geojson()
    SPI_dc = SPI_dc.filter_spatial(geojson)

    # SPI_dc = SPI_dc.filter_temporal("2020-01-01", "2023-01-01")

    custom_execute_batch(SPI_dc)
