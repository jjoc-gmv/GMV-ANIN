import json
import os
import datetime
import openeo
import geopandas as gpd

# Possible backends: "openeo.cloud" "openeo.vito.be"
connection = openeo.connect("openeo.cloud").authenticate_oidc()
now = datetime.datetime.now()
print(connection.root_url + " time: " + str(now))

precipitation_dc = connection.load_collection(
    "AGERA5",
    temporal_extent=["2015-01-01", "2023-01-01"],  # Small sample date
    spatial_extent={
        "west": 10,
        "south": -40,
        "east": 40,
        "north": -20,
    },
    bands=["precipitation-flux"],
)
precipitation_dc = precipitation_dc.aggregate_temporal_period("month", reducer="sum")


# precipitation_dc = (precipitation_dc * 0.01)


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


# Load de shp
# Once we decide the layer for each index it has to be fixed
shpfile = load_shape_file('shape/CNTR_RG_01M_2020_4326.shp')

# Create the mask layer
mask_layer = select_shape(shpfile)


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


geojson = json.loads(mask_layer.to_json())
geojson = split_geojson_in_features(geojson)

with open("south_africa_mask.json", "w") as f:
    json.dump(geojson, f, indent=2)

precipitation_dc = precipitation_dc.filter_spatial(geojson)


def load_udf(udf):
    """
    UDF: User Defined Function
    """
    with open(udf, 'r+', encoding="utf8") as f:
        return f.read()


udf_code = load_udf("SPI_UDF.py")
precipitation_dc = precipitation_dc.apply_dimension(code=udf_code, runtime="Python")

from pathlib import Path

output_dir = Path("out-" + str(now).replace(":", "_"))
output_dir.mkdir(parents=True, exist_ok=True)
precipitation_dc.print_json(file=output_dir / "process_graph.json", indent=2)

precipitation_dc.download("SPI_monthly.nc")

# job = precipitation_dc.execute_batch(
#     title=os.path.basename(__file__),
#     # filename_prefix="SPI",
#     format="GTiff",
# )
# job.get_results().download_files(output_dir)

print("End time: " + str(datetime.datetime.now()))
