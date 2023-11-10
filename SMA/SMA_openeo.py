import openeo
from openeo_utils.utils import *

connection = get_connection()

SMA_dc = connection.load_disk_collection(
    format="GTiff",
    # TODO: Should fetch realtime data
    # Data was manually imported from https://edo.jrc.ec.europa.eu/gdo/php/index.php?id=2112
    # By making a free account on Terrascope, you can edit this folder too: https://terrascope.be/en/form/vm
    glob_pattern="/data/users/Public/emile.sonneveld/SMA_layer/sma*_m_wld_*_t/sma*_m_wld_*_t.tif",
    options=dict(date_regex=r".*_(\d{4})(\d{2})(\d{2})_t.tif"),
)
SMA_dc = SMA_dc.aggregate_temporal_period("month", reducer="mean")
SMA_dc = SMA_dc.rename_labels("bands", ["SMA"])

if __name__ == "__main__":
    start = f"2020-01-01"
    end = f"2023-09-01"
    SMA_dc = SMA_dc.filter_temporal([start, end])

    geojson = load_south_africa_geojson()
    # geojson = load_johannesburg_geojson()
    SMA_dc = SMA_dc.filter_spatial(geojson)
    custom_execute_batch(SMA_dc)
