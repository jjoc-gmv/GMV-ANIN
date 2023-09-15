from SPI.SPI_openeo import SPI_dc, SPI_previous_month_dc
from SMA.SMA_openeo import SMA_dc
from FAPAR_Anomaly.FAPAR_Anomaly_OpenEO import FAPAR_anomaly_dc
# import SMA.SMA_openeo
# import FAPAR_Anomaly.FAPAR_Anomaly_OpenEO
from openeo_utils.utils import *

from openeo import DataCube
from openeo.api.process import Parameter
from openeo.extra.spectral_indices.spectral_indices import append_indices, compute_indices
from openeo.processes import if_, exp, array_element, log, count, gte, eq, sum, date_shift

SPI_dc = SPI_dc.date_shift(-1, "month")
merged_dc = SPI_dc
merged_dc = merged_dc.merge(SMA_dc)
merged_dc = merged_dc.merge(FAPAR_anomaly_dc)


# Linearly interpolate missing values. To avoid protobuf error.
# CDI_dc = CDI_dc.apply_dimension(
#     dimension="t",
#     process="array_interpolate_linear",
# )


def combined(bands):
    SPI_band = bands.array_element(0)
    SMA_band = bands.array_element(1)
    FAPAR_Anomaly_band = bands.array_element(1)

    # Watch class: when SPI-3 is less than -1 and make no data as 0
    pb = if_(SPI_band < -1, 1, 0)

    # Warning class: where SPI-3 < -1 and SMA < -1
    pb = if_((SMA_band < -1) and (pb == 1), 2, pb)

    # Alert class: where SPI-3 < -1 and FAPAR anomaly < -1
    pb = if_((FAPAR_Anomaly_band < -1) & (pb == 1), 3, pb)

    # Partial recovery:  where FAPAR anomaly < -1 and SPI-3 m-1 < -1 and SPI-3 > -1
    # pb = if_((FAPAR_Anomaly_band<-1) & (SPI_band>-1) & (CDI_stack[i_1][0]<-1),4,pb)

    # Full recovery:  where FAPAR anomaly > -1 and SPI-3 m-1 < -1 and SPI-3 > -1
    # pb = if_((CDI_stack[i][2]>-1) & (CDI_stack[i][0]>-1) & (CDI_stack[i_1][0]<-1),5,CDI)

    return pb


# CDI_dc = merged_dc.apply_dimension(combined, dimension='bands')

udf_code = load_udf(os.path.join(os.path.dirname(__file__), "CDI_UDF.py"))
CDI_dc = merged_dc.apply_dimension(dimension="bands", code=udf_code, runtime="Python")

if __name__ == "__main__":
    year = 2021
    start = f"{year}/01/01"
    end = f"{year + 2}/01/01"  # Big time range
    CDI_dc = CDI_dc.filter_temporal([start, end])

    geojson = load_south_africa_geojson()
    CDI_dc = CDI_dc.filter_spatial(geojson)

    custom_execute_batch(CDI_dc)
