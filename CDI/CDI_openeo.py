from openeo.internal.graph_building import PGNode

from FAPAR_Anomaly.FAPAR_Anomaly_openeo import FAPAR_anomaly_dc
from SMA.SMA_openeo import SMA_dc
from SPI.SPI_openeo import SPI_dc, SPI_previous_month_dc
from openeo_utils.utils import *

temporal_extent = [
    "2020-01-01",  # Only what's needed for CDI
    None,
]

merged_dc = FAPAR_anomaly_dc
merged_dc = merged_dc.merge_cubes(SPI_dc)
merged_dc = merged_dc.merge_cubes(SPI_previous_month_dc)
merged_dc = merged_dc.merge_cubes(SMA_dc)
merged_dc = merged_dc.filter_temporal(temporal_extent)

udf_code = load_udf(os.path.join(os.path.dirname(__file__), "CDI_UDF.py"))
CDI_dc = merged_dc.reduce_dimension(
    dimension="bands",
    reducer=PGNode(
        process_id="run_udf",
        data={"from_parameter": "data"},
        udf=udf_code,
        runtime="Python",
    ),
)

geojson = load_south_africa_geojson()
# geojson = load_johannesburg_geojson()
CDI_dc = CDI_dc.filter_spatial(geojson)


def main(temporal_extent_argument):
    global CDI_dc
    CDI_dc = CDI_dc.filter_temporal(temporal_extent_argument)

    custom_execute_batch(CDI_dc, job_options=heavy_job_options)
    # custom_execute_batch(merged_dc, out_format="netcdf",job_options=heavy_job_options)


if __name__ == "__main__":
    print("WARNING, this script is not finished")
    main(get_temporal_extent_from_argv(["2020-01-01", "2023-09-01"]))
