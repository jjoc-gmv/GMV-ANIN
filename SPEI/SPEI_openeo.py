import glob

import openeo
from openeo_utils.utils import *

connection = get_connection()

# Based on ERA5_monthly.nc
# new Date(new Date(1900, 01, 01).setHours(701256))
# new Date(new Date(1900, 01, 01).setHours(1079616))
temporal_extent = ["1980-01-01", "2023-04-01"]
# temporal_extent = ["2020-01-01", "2023-04-01"]
# new Date(new Date(1990, 01, 01).setHours(24 * -3622))
# new Date(new Date(1980, 01, 31).setHours(24 * -3622))

spatial_extent = {  # South Africa
    "west": 10,
    "south": -40,
    "east": 40,
    "north": -20,
}
# spatial_extent = {  # Johannesburg
#     "west": 27,
#     "south": -27,
#     "east": 30,
#     "north": -26,
# }

band_dictionary = [
    {
        "agera5_name": "dewpoint-temperature",
        "era5land_name": "2_metre_dewpoint_temperature",
        "gmv_name": "d2m",
    },
    {
        "agera5_name": "vapour-pressure",
        "era5land_name": "surface_pressure",
        "gmv_name": "sp",
    },
    {
        "agera5_name": "solar-radiation-flux",
        "era5land_name": "surface_solar_radiation_downwards",
        "gmv_name": "ssrd",  # "Surface short-wave (solar) radiation downwards"
    },
    {
        "agera5_name": "wind-speed",
        # "era5land_name": ['10m_u_component_of_wind', '10m_v_component_of_wind'],  # Johan
        "era5land_name": ['10_metre_u_wind_component', '10_metre_v_wind_component'],  # Emile
        "gmv_name": ['u10', 'v10'],
    },
    {
        "agera5_name": "wind-speed U",
        "era5land_name": '10_metre_u_wind_component',
        "gmv_name": 'u10',
    },
    {
        "agera5_name": "wind-speed V",
        "era5land_name": '10_metre_v_wind_component',
        "gmv_name": 'v10',
    },
    {
        "agera5_name": "precipitation-flux",
        "era5land_name": "total_precipitation",
        "gmv_name": "tp",
    },
    {
        "agera5_name": "temperature-min",
        "era5land_name": "2m_temperature_min",
    },
    {
        "agera5_name": "temperature-mean",
        "era5land_name": "2m_temperature_mean",
    },
    {
        "agera5_name": "temperature-max",
        "era5land_name": "2m_temperature_max",
    },
]


def assert_glob_ok(glob_pattern: str):
    if glob_pattern.startswith("/data/") or glob_pattern.startswith("/dataCOPY/"):
        if os.path.exists("/dataCOPY/"):
            glob_pattern = glob_pattern.replace("/data/", "/dataCOPY/")
            # star_index = glob_pattern.find("*")
            # slash_index = glob_pattern.rfind("/", 0, star_index)
            glob_test = glob.glob(glob_pattern)
            if not glob_test:
                raise Exception("glob_pattern not found: " + glob_pattern)
            return True
    print("Could not verify GLOB pattern: " + glob_pattern)


def get_era5land_band_johan(agera5_name):
    band_tuple = list(filter(lambda x: x["agera5_name"] == agera5_name, band_dictionary))
    assert len(band_tuple) == 1
    era5land_name = band_tuple[0]["era5land_name"]
    if isinstance(era5land_name, list):
        # TODO: Fix this. It will give slightly slower wind speed
        # TODO: Johan wind might have missing data
        era5land_name = era5land_name[0]
        print(f"Warning: multiple era5land names found for {agera5_name}. Only using first one: {era5land_name}")
    assert era5land_name is not None
    glob_pattern = "/data/users/Public/johan.schreurs/ANIN/reanalysis-era5-land_southafrica_float32/*/reanalysis-era5-land_" + era5land_name + "_*.tif"
    assert_glob_ok(glob_pattern)

    # tmp = connection.load_stac("/data/MODIS/STAC/GLASS_FAPAR/tiff_collection_months_mean/v0.1/collection.json",
    #                            spatial_extent=spatial_extent,
    #                            temporal_extent=temporal_extent,
    #                            )
    tmp = connection.load_disk_collection(
        format="GTiff",
        glob_pattern=glob_pattern,
        options=dict(date_regex=r".*_(\d{4})(\d{2})(\d{2}).tif"),
    )
    load_collection = tmp.rename_labels("bands", [agera5_name]) * 1.0
    load_collection._pg.arguments['featureflags'] = {"tilesize": 32}
    return load_collection


def get_era5land_band_ANIN(agera5_name):
    band_tuple = list(filter(lambda x: x["agera5_name"] == agera5_name, band_dictionary))
    assert len(band_tuple) == 1
    gmv_name = band_tuple[0]["gmv_name"]
    era5land_name = band_tuple[0]["era5land_name"]
    assert gmv_name is not None
    assert era5land_name is not None

    glob_pattern = "/data/users/Public/emile.sonneveld/ERA5-Land-monthly-averaged-data-ANIN/tiff_collection/*/*/*/*_" + gmv_name + ".tif"
    assert_glob_ok(glob_pattern)

    # * 1.0 to avoid: "class geotrellis.raster.FloatCellType$ cannot be cast to class geotrellis.raster.HasNoData"
    load_collection = connection.load_disk_collection(
        format="GTiff",
        # Based on https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means
        glob_pattern=glob_pattern,
        options=dict(date_regex=r".*(\d{4})-(\d{2})-(\d{2}).*"),
        # options=dict(date_regex=r".*tiff_collection/(\d{4})/(\d{2})/(\d{2})/.*"),
    ).rename_labels("bands", [era5land_name]) * 1.0
    load_collection._pg.arguments['featureflags'] = {"tilesize": 16}
    return load_collection


def get_era5land_band(agera5_name):
    band_tuple = list(filter(lambda x: x["agera5_name"] == agera5_name, band_dictionary))
    assert len(band_tuple) == 1
    era5land_name = band_tuple[0]["era5land_name"]
    if isinstance(era5land_name, list):
        # TODO: Fix this. It will give slightly slower wind speed
        era5land_name = era5land_name[0]
        print(f"Warning: multiple era5land names found for {agera5_name}. Only using first one: {era5land_name}")
        band_name = agera5_name
    else:
        band_name = era5land_name

    assert era5land_name is not None
    glob_pattern = "/data/users/Public/emile.sonneveld/ERA5-Land-monthly-averaged-data-v3/tiff_collection/*/*/*/*_" + era5land_name + ".tiff"
    assert_glob_ok(glob_pattern)

    # * 1.0 to avoid: "class geotrellis.raster.FloatCellType$ cannot be cast to class geotrellis.raster.HasNoData"
    load_collection = connection.load_disk_collection(
        format="GTiff",
        # Based on https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means
        glob_pattern=glob_pattern,
        options=dict(date_regex=r".*tiff_collection/(\d{4})/(\d{2})/(\d{2})/.*"),
    ).rename_labels("bands", [band_name])  # * 1.0
    load_collection._pg.arguments['featureflags'] = {"tilesize": 16}
    return load_collection


def get_agera5_band(band):
    return connection.load_collection(
        "AGERA5",
        temporal_extent=temporal_extent,
        spatial_extent=spatial_extent,
        bands=[band],
    ) * 1.0


kelvin_to_celsius_offset = -273.15

bands = [
    get_era5land_band_ANIN("dewpoint-temperature").aggregate_temporal_period("month", reducer="mean"),
    get_era5land_band_ANIN("vapour-pressure").aggregate_temporal_period("month", reducer="mean"),
    get_era5land_band_ANIN("solar-radiation-flux").aggregate_temporal_period("month", reducer="mean"),
    get_era5land_band_ANIN("wind-speed U").aggregate_temporal_period("month", reducer="mean"),  # U + V speed?
    get_era5land_band_ANIN("wind-speed V").aggregate_temporal_period("month", reducer="mean"),  # U + V speed?
    get_era5land_band_ANIN("precipitation-flux").aggregate_temporal_period("month", reducer="sum"),
    get_era5land_band_johan("temperature-min").aggregate_temporal_period("month", reducer="mean"),  # TODO: OK?
    get_era5land_band_johan("temperature-mean").aggregate_temporal_period("month", reducer="mean"),  # TODO: OK?
    get_era5land_band_johan("temperature-max").aggregate_temporal_period("month", reducer="mean"),
]
ERA5_dc = bands[0]
for b in bands[1:]:
    ERA5_dc = ERA5_dc.merge_cubes(b)

# Linearly interpolate missing values. To avoid protobuf error.
# AGERA5 = AGERA5.apply_dimension(
#     dimension="t",
#     process="array_interpolate_linear",
# )

# SPEI_dc = AGERA5
UDF_code = load_udf(os.path.join(os.path.dirname(__file__), "SPEI_UDF.py"))
ERA5_dc = ERA5_dc.filter_temporal(temporal_extent)
geojson = load_south_africa_geojson()
# geojson = load_johannesburg_geojson()
ERA5_dc = ERA5_dc.filter_spatial(geojson)
SPEI_dc = ERA5_dc.apply_dimension(dimension="t", code=UDF_code, runtime="Python")
SPEI_dc = SPEI_dc.rename_labels("bands", ["SPEI"])

if __name__ == "__main__":
    # Sometimes got errors like this:
    # Trying to construct a datacube with a bounds Extent(16.448304, -46.981234, 38.002543, -22.12718) that is not entirely inside the global bounds: Extent(9.949999999999989, -40.05, 40.05000000000001, -19.94999999999999)

    # SPEI_dc = SPEI_dc.filter_temporal("1970-01-01", "2023-01-01")
    custom_execute_batch(SPEI_dc, heavy_job_options, out_format="netcdf") # , run_locally=True)

    # execute locally:

    # ERA5_dc = ERA5_dc.filter_spatial(geojson)
    # ERA5_dc = ERA5_dc.filter_temporal("2020-01-01", "2022-12-01")
    # custom_execute_batch(ERA5_dc, out_format="netcdf") #, run_locally=True)
    pass
