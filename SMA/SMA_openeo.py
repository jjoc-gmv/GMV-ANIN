import os
import json
import openeo
import datetime

now = datetime.datetime.now()

url = "https://openeo-dev.vito.be"
print("now: " + str(now) + " url: " + url)
connection = openeo.connect(url).authenticate_oidc()

out_path = "out-" + str(now).replace(":", "_")
os.mkdir(out_path)

with open(__file__, 'r') as file:
    job_description = "now: " + str(now) + " url: " + url + "\n\n"
    job_description += "python code: \n\n\n```python\n" + file.read() + "\n```"

year = 2021
start = f"{year}/01/01"
end = f"{year + 10}/01/01"  # Big time range

# inspired on https://git.vito.be/users/lippenss/repos/workspace/browse/2023/PEOPLE/udp-reduce_temporal.ipynb
cube = connection.load_disk_collection(
    format="GTiff",
    glob_pattern="/data/users/Public/emile.sonneveld/SMA_layer/smant_m_wld_*_t/smant_m_wld_*_t.tif",
    options=dict(date_regex=r'.*_(\d{4})(\d{2})(\d{2})_t.tif'),
)
cube = cube.filter_bbox(
    west=10,
    south=-40,
    east=40,
    north=-20,
)
cube = cube.filter_temporal([start, end])
cube = cube.aggregate_temporal_period("month", reducer="sum")

# graph.print_json(file=os.path.join(out_path, "datacube_print_json.json"))
job = connection.create_job(
    process_graph=cube.flat_graph(),
    title=os.path.basename(__file__),
    description=job_description,
)

print("job_id: " + job.job_id)
job.start_and_wait()
job.get_results().download_files(out_path)
print("job.status() " + job.status())
