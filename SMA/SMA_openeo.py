import os
import json
import openeo
import datetime
from openeo_utils.utils import *

connection = get_connection()

# inspired on https://git.vito.be/users/lippenss/repos/workspace/browse/2023/PEOPLE/udp-reduce_temporal.ipynb
SMA_dc = connection.load_disk_collection(
    format="GTiff",
    # TODO: Data was manually imported. Should be made realtime
    glob_pattern="/data/users/Public/emile.sonneveld/SMA_layer/sma*_m_wld_*_t/sma*_m_wld_*_t.tif",
    options=dict(date_regex=r'.*_(\d{4})(\d{2})(\d{2})_t.tif'),
)
SMA_dc = SMA_dc.aggregate_temporal_period("month", reducer="mean")
SMA_dc = SMA_dc.rename_labels('bands', ['SMA'])

if __name__ == "__main__":
    year = 2021
    start = f"{year}/01/01"
    end = f"{year + 10}/01/01"  # Big time range
    SMA_dc = SMA_dc.filter_temporal([start, end])
    SMA_dc = SMA_dc.filter_bbox(
        west=10,
        south=-40,
        east=40,
        north=-20,
    )
    geojson = load_south_africa_geojson()
    SMA_dc = SMA_dc.filter_spatial(geojson)
    custom_execute_batch(SMA_dc)
