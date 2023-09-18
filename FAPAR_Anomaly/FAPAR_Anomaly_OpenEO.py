import os
import json
import openeo
import datetime
from openeo_utils.utils import *

connection = get_connection()
# TODO: Calculate averages on monthly basis.

# Z-score stays the same when scaling all data points
# import numpy as np
# import scipy.stats as stats
# data = np.array([6, 7, 7, 12, 13, 13, 15, 16, 19, 22])
# print(stats.zscore(data))
# print(stats.zscore(data * 10))


band = "FAPAR"
FAPAR_dc = connection.load_collection(
    "CGLS_FAPAR300_V1_GLOBAL",
    temporal_extent=["1990-01-01", "2100-01-01"],
    # To avoid "No spatial filter could be derived to load this collection"
    # spatial_extent={  # South Africa. (filter_spatial() is good enough)
    #     "west": 10,
    #     "south": -40,
    #     "east": 40,
    #     "north": -20,
    # },
    # spatial_extent={  # Johannes burg
    #     "west": 27,
    #     "south": -27,
    #     "east": 30,
    #     "north": -26,
    # },
    bands=[band],
)

# FAPAR_dc = FAPAR_dc.resample_spatial(resolution=50.0, projection=4326)
FAPAR_dc = FAPAR_dc.resample_spatial(projection=4326,
                                     resolution=0.0089285714285 / 1000 * 400)  # based on 1km resolution
FAPAR_dc = FAPAR_dc.aggregate_temporal_period("month", reducer="mean")
FAPAR_dc = (FAPAR_dc * 0.01)

# Formula:  = (current - median ) / SD
current_band = FAPAR_dc.band(band)
mean_band = FAPAR_dc.reduce_temporal("mean").band(band)  # TODO: mean needs to be calculated per month
difference_band = current_band.merge_cubes(mean_band, overlap_resolver="subtract")
sd_band = FAPAR_dc.reduce_temporal("sd").band(band)
FAPAR_anomaly_dc = difference_band.merge_cubes(sd_band, overlap_resolver="divide")

FAPAR_anomaly_dc = FAPAR_anomaly_dc.add_dimension("bands", "FAPAR_anomaly", type="bands")

# Test in between values:
# FAPAR_dc.reduce_temporal("mean").download("mean.nc")
# FAPAR_dc.reduce_temporal("min").download("min.nc")
# FAPAR_dc.reduce_temporal("max").download("max.nc")
# FAPAR_dc.reduce_temporal("sd").download("sd.nc")

if __name__ == "__main__":
    # Select smaller period for performance. (Mean still needs to be calculated on larger period)
    FAPAR_anomaly_dc = FAPAR_anomaly_dc.filter_temporal("2021-01-01", "2025-01-01")

    FAPAR_anomaly_dc = FAPAR_anomaly_dc.filter_bbox({  # Johannes burg
        "west": 27,
        "south": -27,
        "east": 30,
        "north": -26,
    })

    custom_execute_batch(FAPAR_anomaly_dc)
