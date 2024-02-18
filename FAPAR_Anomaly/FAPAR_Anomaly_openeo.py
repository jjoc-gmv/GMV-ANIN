from openeo_utils.utils import *

connection = get_connection()

spatial_extent = spatial_extent_south_africa

temporal_extent = [
    "2020-01-01",  # Only what's needed for CDI
    "2023-09-01",
]

band = "FAPAR"
CGLS_FAPAR300_V1_GLOBAL_dc = (
        connection.load_collection(
            "CGLS_FAPAR300_V1_GLOBAL",  # 300m resolution, [2014,present]
            temporal_extent=temporal_extent,
            # To avoid "No spatial filter could be derived to load this collection"
            spatial_extent=spatial_extent,
            bands=[band],
        )
        .aggregate_temporal_period("month", reducer="mean")
        # Linearly interpolate missing values. To avoid protobuf error.
        .apply_dimension(
            dimension="t",
            process="array_interpolate_linear",
        )
        * 1.0
)


def load_disk_collection_glass(subfolder):
    return (
            connection.load_stac(f"/data/MTDA/MODIS/GLASS_FAPAR/{subfolder}/STAC_catalogs/v0.1/collection.json",
                                 spatial_extent=spatial_extent,
                                 temporal_extent=temporal_extent,
                                 )
            .aggregate_temporal_period("month", reducer="mean")
            .rename_labels("bands", [subfolder])
            * 1.0
    )


FAPAR_dc = CGLS_FAPAR300_V1_GLOBAL_dc
FAPAR_Mean = load_disk_collection_glass("tiff_collection_months_mean")
FAPAR_Sd = load_disk_collection_glass("tiff_collection_months_sd")

FAPAR_anomaly_dc = (FAPAR_dc - FAPAR_Mean) / FAPAR_Sd

if __name__ == "__main__":
    # geojson = load_south_africa_geojson()
    geojson = load_johannesburg_geojson()  # For faster debugging
    FAPAR_anomaly_dc = FAPAR_anomaly_dc.filter_spatial(geojson)

    # custom_execute_batch(FAPAR_anomaly_dc, job_options=heavy_job_options)
