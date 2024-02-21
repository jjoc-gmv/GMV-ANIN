import openeo
from openeo_utils.utils import *

connection = get_connection()

band = "NDVI"
temporal_extent = ["2020-07-01", "2023-05-01"]
spatial_extent = spatial_extent_south_africa

CGLS_NDVI300_V2_GLOBAL_dc = connection.load_collection(
    "CGLS_NDVI300_V2_GLOBAL",  # 300m resolution, [2020, present]
    temporal_extent=temporal_extent,
    # To avoid "No spatial filter could be derived to load this collection"
    spatial_extent=spatial_extent,
    bands=[band],
)
CGLS_NDVI300_V2_GLOBAL_dc = CGLS_NDVI300_V2_GLOBAL_dc.aggregate_temporal_period("month", reducer="mean")
scale_factor = 0.004
add_offset = -0.08
CGLS_NDVI300_V2_GLOBAL_dc = (CGLS_NDVI300_V2_GLOBAL_dc * scale_factor) + add_offset

# glob_pattern = f"/data/users/Public/emile.sonneveld/ANIN/CROP_MASK/*.tif"
# assert_glob_ok(glob_pattern)
# mask = connection.load_disk_collection(
#     format="GTiff",
#     glob_pattern=glob_pattern,
#     options=dict(date_regex=r".*(\d{4})-(\d{2})-(\d{2}).*"),
# ).filter_bbox(spatial_extent).filter_temporal(temporal_extent)

phenology_mask = connection.load_stac(
    "/data/users/Public/emile.sonneveld/ANIN/CROP_MASK/CROP_MASK_STAC/collection.json",
    spatial_extent=spatial_extent,
    temporal_extent=temporal_extent,
)

MODIS_dc = connection.load_stac(
    "/data/users/Public/emile.sonneveld/ANIN/VCI/MODIS_NDVI/MODIS_NDVI_DERIVATIONS_STAC/collection.json",
    spatial_extent=spatial_extent,
    temporal_extent=temporal_extent,
)

MODIS_MIN_dc = MODIS_dc.band("NDVI_MIN")
MODIS_MAX_dc = MODIS_dc.band("NDVI_MAX")

VCI_dc = (CGLS_NDVI300_V2_GLOBAL_dc - MODIS_MIN_dc) / (MODIS_MAX_dc - MODIS_MIN_dc)
VCI_dc = VCI_dc.mask(phenology_mask)

geojson = load_south_africa_geojson()
# geojson = load_johannesburg_geojson()
VCI_dc = VCI_dc.filter_spatial(geojson)

if __name__ == "__main__":
    VCI_dc = VCI_dc.filter_temporal(temporal_extent)
    # VCI_dc = VCI_dc.filter_temporal("2020-07-01", "2020-07-30")
    custom_execute_batch(VCI_dc, job_options=heavy_job_options)
    # custom_execute_batch(CGLS_NDVI300_V2_GLOBAL_dc, out_format="netcdf", job_options=heavy_job_options, run_type="sync")  # OK
    # custom_execute_batch(MODIS_MAX_dc, out_format="netcdf", job_options=heavy_job_options, run_type="batch_job")  # okish
    # custom_execute_batch(MODIS_MIN_dc, out_format="netcdf", job_options=heavy_job_options, run_type="sync")  # okish
