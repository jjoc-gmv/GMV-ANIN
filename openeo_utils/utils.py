import datetime
import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import openeo

connection = None

now = datetime.datetime.now()


def get_connection():
    global connection
    if connection is None:
        # Possible backends: "openeo.cloud" "openeo.vito.be"
        url = "https://openeo-dev.vito.be"
        connection = openeo.connect(url).authenticate_oidc()
        print(connection.root_url + " time: " + str(now))
    return connection


def load_shape_file(filepath):
    """Loads the shape file desired to mask a grid.
    Args:
        filepath: Path to *.shp file
    """
    shpfile = gpd.read_file(filepath)
    print("""Shapefile loaded. To prepare for masking, run the function
        `select_shape`.""")
    return shpfile


# Create the mask
def select_shape(shpfile):
    """Select the submask of interest from the shapefile.
    Args:
        shpfile: (*.shp) loaded through `load_shape_file`
        category: (str) header of shape file from which to filter shape.
            (Run print(shpfile) to see options)
        name: (str) name of shape relative to category.
           Returns:
        shapely polygon
    """

    col_code = 'ISO3_CODE'
    country_codes = ['ZAF', 'LSO', 'SWZ']

    # Extract the rows that have 'ZAF', 'LSO', or 'SWZ' in the 'SOV_A3' column
    selected_rows = shpfile[shpfile[col_code].isin(country_codes)]

    # Combine the selected polygons into a single polygon
    unioned_polygon = selected_rows.geometry.unary_union

    # Convert the unioned polygon to a geopandas dataframe with a single row
    mask_polygon = gpd.GeoDataFrame(geometry=[unioned_polygon])

    print("""Mask created.""")

    return mask_polygon


def split_geojson_in_features(geojson):
    features = geojson["features"]
    assert len(features) == 1
    coordinates = features[0]["geometry"]["coordinates"]

    ret_json = """
    {
  "type": "FeatureCollection",
  "features": [
        """
    features = []
    for c in coordinates:
        feature_str = """
        {
      "id": "0",
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
        """
        feature_str += repr(c)
        feature_str += """
        ]
      }
    }
        """
        features.append(feature_str)
    ret_json += ",\n".join(features)
    ret_json += """
  ]
}"""
    return json.loads(ret_json)


def load_south_africa_geojson():
    # Load de shp
    # Once we decide the layer for each index it has to be fixed
    shpfile = load_shape_file('../SPI/shape/CNTR_RG_01M_2020_4326.shp')

    # Create the mask layer
    mask_layer = select_shape(shpfile)

    geojson = json.loads(mask_layer.to_json())
    geojson = split_geojson_in_features(geojson)

    with open("south_africa_mask.json", "w") as f:
        json.dump(geojson, f, indent=2)

    return geojson


def load_udf(udf):
    """
    UDF: User Defined Function
    """
    with open(udf, 'r+', encoding="utf8") as fs:
        return fs.read()


def custom_execute_batch(datacube):
    try:
        import inspect
        parent_filename = inspect.stack()[1].filename

        with open(parent_filename, 'r') as file:
            job_description = "now: " + str(now) + " url: " + connection.root_url + "\n\n"
            job_description += "python code: \n\n\n```python\n" + file.read() + "\n```"

        output_dir = Path("out-" + str(now).replace(":", "_").replace(" ", "_"))
        output_dir.mkdir(parents=True, exist_ok=True)
        datacube.print_json(file=output_dir / "process_graph.json", indent=2)
        print(str(output_dir.absolute()) + "/")
        # datacube.download("SPI_monthly.nc")
        job = datacube.create_job(
            title=os.path.basename(parent_filename),
            format="GTiff",
            # format="NetCDF",
            description=job_description,
            job_options={"executor-memory": "10g"},
        )
        with open(output_dir / "job_id.txt", mode="w") as f:
            f.write(job.job_id)
        job.start_and_wait()
        job.get_results().download_files(output_dir)

        with open(output_dir / "logs.json", "w") as f:
            json.dump(job.logs(), f, indent=2)

        os.system('spd-say "Program terminated"')  # vocal feedback
    except KeyboardInterrupt:
        # No audio when user manually stops program
        pass
    except:
        os.system('spd-say "Program failed"')  # vocal feedback
        raise
    finally:
        print("custom_execute_batch end time: " + str(datetime.datetime.now()))
