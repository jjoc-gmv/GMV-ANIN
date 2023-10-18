import openeo
from openeo_utils.utils import *

connection = get_connection()

band = "NDVI"
CGLS_NDVI_V3_GLOBAL_dc = connection.load_collection(
    "CGLS_NDVI_V3_GLOBAL",  # 1km resolution, [1999, 2020]
    # This temporal_extent ends up in the UDF, so keep small when testing.
    temporal_extent=["1999-01-01", "2014-01-01"],
    # To avoid "No spatial filter could be derived to load this collection"
    spatial_extent={  # South Africa
        "west": 10,
        "south": -40,
        "east": 40,
        "north": -20,
    },
    bands=[band],
)

CGLS_NDVI300_V1_GLOBAL_dc = connection.load_collection(
    "CGLS_NDVI300_V1_GLOBAL",  # 300m resolutions [2014, 2021]
    # This temporal_extent ends up in the UDF, so keep small when testing.
    temporal_extent=["2014-01-01", "2020-01-01"],
    # To avoid "No spatial filter could be derived to load this collection"
    spatial_extent={  # South Africa
        "west": 10,
        "south": -40,
        "east": 40,
        "north": -20,
    },
    bands=[band],
)

CGLS_NDVI300_V2_GLOBAL_dc = connection.load_collection(
    "CGLS_NDVI300_V2_GLOBAL",  # 300m resolution, [2020, present]
    temporal_extent=["2020-01-01", "2023-09-01"],
    # To avoid "No spatial filter could be derived to load this collection"
    spatial_extent={  # South Africa
        "west": 10,
        "south": -40,
        "east": 40,
        "north": -20,
    },
    bands=[band],
)

# TODO: Use precalculated MODIS min max. Or use MODIS long term.
# This might be easier to implement after some STAC developments have been made.
# load_disk_collection is not fully supported.
# dc = connection.load_disk_collection(
#     format="GTiff",
#     glob_pattern="/data/users/Public/emile.sonneveld/ToShareWithVito/VCI/MAX",  # VCI/MIN
#     options=dict(date_regex=r".*_(\d{4})(\d{2})(\d{2})_t.tif"),
# )

# MODIS_dc = connection.load_collection(
#     collection_id="MODIS",  # Goes through SentinelHub, so slow
#     temporal_extent=["2000-02-24T00:00:00Z", "2023-02-10T00:00:00Z"],
#     spatial_extent={  # South Africa
#         "west": 10,
#         "south": -40,
#         "east": 40,
#         "north": -20,
#     },
#     bands=None
# )

# This whole datacube ends up in the UDF to calculate reference data.
# Combine low quality history, and high quality current time:
NDVI_dc = (CGLS_NDVI300_V2_GLOBAL_dc
           .merge_cubes(CGLS_NDVI300_V1_GLOBAL_dc, overlap_resolver="or"))
#           .merge_cubes(CGLS_NDVI_V3_GLOBAL_dc.resample_cube_spatial(CGLS_NDVI300_V1_GLOBAL_dc), overlap_resolver="or"))
# NDVI_dc = NDVI_dc.filter_temporal("2015-01-01", "2023-07-01")

# NDVI_dc = NDVI_dc.resample_spatial(resolution=50.0, projection=4326)
# NDVI_dc = NDVI_dc.resample_spatial(projection=4326,
#                                      resolution=0.0089285714285 / 1000 * 400)  # based on 1km resolution

# Linearly interpolate missing values. To avoid protobuf error.
NDVI_dc = NDVI_dc.apply_dimension(
    dimension="t",
    process="array_interpolate_linear",
)

# Can error on months without data: "Band count must be greater than 0"
NDVI_dc = NDVI_dc.aggregate_temporal_period("month", reducer="mean")

UDF_code = load_udf(os.path.join(os.path.dirname(__file__), "VCI_UDF.py"))
VCI_dc = NDVI_dc.apply_dimension(dimension="t", code=UDF_code, runtime="Python")
VCI_dc = VCI_dc.rename_labels("bands", ["VCI"])

if __name__ == "__main__":
    # Select smaller period for performance. (Min/Max still needs to be calculated on larger period)
    # VCI_dc = NDVI_dc
    VCI_dc = VCI_dc.filter_temporal("2021-01-01", "2022-01-01")
    # OpenEO batch job failed: KeyError('minKey')
    # IndexError: list index out of range

    # pixel_size = 0.002976190476
    # pixel_size = 0.1
    # VCI_dc = VCI_dc.resample_spatial(resolution=pixel_size, projection=4326)

    geojson = load_south_africa_geojson()
    # geojson = load_johannesburg_geojson()
    VCI_dc = VCI_dc.filter_spatial(geojson)

    custom_execute_batch(VCI_dc, job_options=heavy_job_options)
