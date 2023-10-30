import datetime
import os
import re
import typing
from pathlib import Path

import geopandas as gpd
import osgeo.gdal
import osgeo.ogr
import pyproj
import shapely.geometry
import shapely.ops
import shapely.ops

# Run this to get the latest data:
# cd /dataCOPY/users/Public/emile.sonneveld/GLASS_FAPAR_Layer
# wget --mirror --domains www.glass.umd.edu --no-parent http://www.glass.umd.edu/FAPAR/MODIS/250m/ --accept "*.h19v1[123].*.hdf" --accept "*.h20v1[123].*.hdf" --accept "index.html"

# http://www.glass.umd.edu/Overview.html
input_path = Path('/dataCOPY/users/Public/emile.sonneveld/GLASS_FAPAR_Layer/www.glass.umd.edu/FAPAR/MODIS/250m/')
if not input_path.exists():
    raise Exception("Path not found: " + str(input_path))

output_path = Path("/dataCOPY/users/Public/emile.sonneveld/GLASS_FAPAR_Layer/tiff_collection/")
if not output_path.exists():
    raise Exception("Path not found: " + str(output_path))

os.chdir(input_path)

file_list = list(input_path.rglob('*.hdf'))


def read_hdf_extent_polygon(hdf_file_path) -> typing.Optional[gpd.GeoDataFrame]:
    hdf_data = osgeo.gdal.Open(str(hdf_file_path))
    if hdf_data is None:
        return None
    geo_transform = hdf_data.GetGeoTransform()
    minx = geo_transform[0]
    maxy = geo_transform[3]
    maxx = minx + geo_transform[1] * hdf_data.RasterXSize
    miny = maxy + geo_transform[5] * hdf_data.RasterYSize

    hdf_crs = pyproj.CRS.from_user_input(hdf_data.GetProjection())
    return gpd.GeoDataFrame(geometry=[shapely.geometry.box(minx, miny, maxx, maxy)], crs=hdf_crs)


if __name__ == "__main__":
    from openeo_utils.utils import *

    geodata_polygon = load_south_africa_shape()
    south_africa_polygon = shapely.ops.unary_union(geodata_polygon.geometry)
    south_africa_polygon = south_africa_polygon.convex_hull
    # geodata_polygon = None

    for file_path in file_list:
        try:
            z = re.match(r".*/(\d{4})[_-]\d/(\d{3}).*", str(file_path))
            year = int(z.group(1))
            day = int(z.group(2))
            date = datetime.date(year, 1, 1) + datetime.timedelta(days=day)
            output_file = (output_path / "{:04d}".format(date.year) / "{:02d}".format(date.month) /
                           "{:02d}".format(date.day) / (file_path.name + ".tiff"))
            output_file.parent.mkdir(parents=True, exist_ok=True)
            if output_file.exists():
                print("output already exists: " + str(output_file))
                continue

            hdf_df = read_hdf_extent_polygon(file_path)
            if hdf_df is None:
                print("Could not read file: " + str(file_path))
                continue

            if geodata_polygon is not None:
                hdf_df = hdf_df.to_crs(geodata_polygon.crs)
                hdf_polygon = shapely.ops.unary_union(hdf_df.geometry)
                overlaps = south_africa_polygon.overlaps(hdf_polygon)
                if not overlaps:
                    continue

            cmd = f"""gdal_translate -co COMPRESS=DEFLATE -of GTiff "{file_path}" "{output_file}.tmp" """
            print(cmd)
            os.system(cmd)
            os.rename(f"{output_file}.tmp", output_file)  # atomic, to avoid corrupt files
            # exit()
        except KeyboardInterrupt:
            # To be a ble to stop the program
            raise
        except Exception as e:
            print("Problem with: " + str(file_path))
            print(e)
    print("Done")
