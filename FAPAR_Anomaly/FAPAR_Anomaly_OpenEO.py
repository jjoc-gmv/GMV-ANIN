import json
import os
import datetime
import openeo

# Work in Progress Code...

# Z-score stays the same when scaling all data points
# import numpy as np
# import scipy.stats as stats
# data = np.array([6, 7, 7, 12, 13, 13, 15, 16, 19, 22])
# print(stats.zscore(data))
# print(stats.zscore(data * 10))


# openeo.cloud openeo-dev.vito.be
connection = openeo.connect("openeo-dev.vito.be").authenticate_oidc()
now = datetime.datetime.now()
print(connection.root_url + " time: " + str(now))

band = "FAPAR"
fapar_dc = connection.load_collection(
    "CGLS_FAPAR300_V1_GLOBAL",
    temporal_extent=["2020-03-01", "2025-05-30"],
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

# fapar_dc = fapar_dc.resample_spatial(resolution=50.0, projection=4326)
fapar_dc = fapar_dc.resample_spatial(projection=4326,
                                     resolution=0.0089285714285 / 1000 * 400)  # based on 1km resolution
fapar_dc = fapar_dc.aggregate_temporal_period("month", reducer="mean")
fapar_dc = (fapar_dc * 0.01)

with open("../SPI/south_africa_mask.json") as f:
    input_json = json.load(f)
    fapar_dc = fapar_dc.filter_spatial(geometries=input_json)

# Formula:  = (current - median ) / SD
current_band = fapar_dc.band(band)
mean_band = fapar_dc.reduce_temporal("mean").band(band)  # TODO: mean needs to be calculated per month
difference_band = current_band.merge_cubes(mean_band, overlap_resolver="subtract")
sd_band = fapar_dc.reduce_temporal("sd").band(band)
anomaly_band = difference_band.merge_cubes(sd_band, overlap_resolver="divide")

# Select smaller period for performance. (Mean still needs to be calculated on larger period)
anomaly_band = anomaly_band.filter_temporal("2021-01-01", "2025-01-01")

# Test in between values:
fapar_dc.reduce_temporal("mean").download("mean.nc")
fapar_dc.reduce_temporal("min").download("min.nc")
fapar_dc.reduce_temporal("max").download("max.nc")
fapar_dc.reduce_temporal("sd").download("sd.nc")

# anomaly_band.download("ANIN_SPI.nc")
out_path = "out-" + band + "-" + str(now).replace(":", "_")
os.mkdir(out_path)
anomaly_band.print_json(file=os.path.join(out_path, "process_graph.json"))
job = anomaly_band.create_job(
    title=os.path.basename(__file__),
    # format="netCDF",
    format="GTiff",
)
with open(os.path.join(out_path, "job_id.txt"), mode="w") as f:
    f.write(job.job_id)

# Starts the job and waits until it finished to download the result.
job.start_and_wait()
with open(os.path.join(out_path, "logs.json"), "w") as f:
    json.dump(job.logs(), f, indent=2)
job.get_results().download_files(out_path)
