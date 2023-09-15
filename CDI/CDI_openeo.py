import SPI.SPI_openeo
import SMA.SMA_openeo
import FAPAR_Anomaly.FAPAR_Anomaly_OpenEO
from openeo_utils.utils import *

CDI_dc = SPI.SPI_openeo.SPI_dc
CDI_dc = CDI_dc.merge(SMA.SMA_openeo.SMA_dc)
CDI_dc = CDI_dc.merge(FAPAR_Anomaly.FAPAR_Anomaly_OpenEO.FAPAR_anomaly_dc)

# Linearly interpolate missing values. To avoid protobuf error.
CDI_dc = CDI_dc.apply_dimension(
    dimension="t",
    process="array_interpolate_linear",
)

if __name__ == "__main__":
    year = 2021
    start = f"{year}/01/01"
    end = f"{year + 2}/01/01"  # Big time range
    CDI_dc = CDI_dc.filter_temporal([start, end])

    geojson = load_south_africa_geojson()
    CDI_dc = CDI_dc.filter_spatial(geojson)

    custom_execute_batch(CDI_dc)
