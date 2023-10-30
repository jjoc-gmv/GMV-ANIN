import datetime
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import cdsapi
import osgeo.gdal
import osgeo.ogr
import osgeo.osr

# Configure cdsapi access: https://cds.climate.copernicus.eu/api-how-to#install-the-cds-api-key

# Avoid "Warning 1: Unable to save auxiliary information in ..."
os.environ["GDAL_PAM_ENABLED"] = "NO"

c = cdsapi.Client()
download_path = Path("/data/users/Public/emile.sonneveld/ERA5-Land-monthly-averaged-data/")
if not download_path.exists():
    raise Exception("download_path not found: " + str(download_path))
(download_path / "tiff_collection").mkdir(exist_ok=True)

tempdir = Path(tempfile.mkdtemp())

today = datetime.date.today()


def netcdf_zip_to_gtiff(netcdf_input_path):
    if netcdf_input_path.name.lower().endswith(".zip"):
        unzip_folder = tempdir / ("unzip_" + netcdf_input_path.name)
        shutil.rmtree(unzip_folder, ignore_errors=True)
        unzip_folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(netcdf_input_path, "r") as zip_ref:
            zip_ref.extractall(unzip_folder)
        results = list(unzip_folder.rglob("*.nc"))
        assert len(results) == 1
        net_cdf_file = results[0]
    else:
        unzip_folder = None
        net_cdf_file = netcdf_input_path

    src_ds = osgeo.gdal.Open(str(net_cdf_file))
    if src_ds is None:
        return None
    # assert src_ds.RasterCount == 12  # one per month, but current year has less months
    # 'time#units': 'hours since 1900-01-01 00:00:00.0'
    src_mtdata = src_ds.GetMetadata()
    z = re.match(r"(\w+) since (\d{4})-(\d{2})-(\d{2})", src_mtdata["time#units"])
    time_delta = z.group(1)
    base_date = datetime.date(int(z.group(2)), int(z.group(3)), int(z.group(4)))
    for band_nr in range(src_ds.RasterCount):
        band_nr += 1
        band = src_ds.GetRasterBand(band_nr)

        stats = band.GetStatistics(True, True)
        print("Band %s Min=%.3f, Max=%.3f, Mean=%.3f, StdDev=%.3f"
              % (band_nr, stats[0], stats[1], stats[2], stats[3]))

        mtdata_band = band.GetMetadata()
        NETCDF_DIM_time = int(mtdata_band["NETCDF_DIM_time"])
        name = mtdata_band["long_name"].lower().replace(" ", "_")

        if time_delta == "hours":
            date = base_date + datetime.timedelta(hours=NETCDF_DIM_time)
        elif time_delta == "days":
            date = base_date + datetime.timedelta(days=NETCDF_DIM_time)
        else:
            raise Exception("Unknown time_delta: " + str(time_delta))

        print("date: " + str(date))
        download_path / "tiff_collection"
        yyy = "{:04d}".format(date.year)
        mm = "{:02d}".format(date.month)
        dd = "{:02d}".format(date.day)
        # output_file = Path(
        #     "/home/emile/Desktop/ToShareWithVito/SPI/outputs/nc_to_tiffs/") / f"{yyy}-{mm}-{dd}_{name}.tiff"
        output_file = download_path / "tiff_collection" / yyy / mm / dd / f"{yyy}-{mm}-{dd}_{name}.tiff"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        arr = band.ReadAsArray()
        [rows, cols] = arr.shape
        driver = osgeo.gdal.GetDriverByName("GTiff")

        # Write single band as GeoTIFF:
        out_ds = driver.Create(str(output_file), cols, rows, 1, band.DataType, options=["COMPRESS=DEFLATE"])
        out_ds.SetGeoTransform(src_ds.GetGeoTransform())
        out_ds.SetProjection(src_ds.GetProjection())
        out_ds.SetMetadata(src_ds.GetMetadata())

        out_srs = osgeo.osr.SpatialReference()
        out_srs.ImportFromEPSG(4326)
        # Error on older versions: https://github.com/OSGeo/gdal/issues/1677
        out_ds.SetSpatialRef(out_srs)  # Make explicit to be sure

        out_ds.GetRasterBand(1).WriteArray(arr)
        out_ds.GetRasterBand(1).SetNoDataValue(band.GetNoDataValue())
        out_ds.FlushCache()  # Saves to disk
    if unzip_folder:
        shutil.rmtree(unzip_folder, ignore_errors=True)
    # os.rmdir(unzip_folder) # Can't always do due to '.nfs' file


# netcdf_zip_to_gtiff(Path("/home/emile/Desktop/ToShareWithVito/SPI/outputs/SPI.nc"))
# exit()

# Requests years separately to allow to re-run this script after an interruption
for year in range(1970, 2023):
    target_tiff_folder = download_path / "tiff_collection" / str(year)
    if target_tiff_folder.exists():
        if today.year == year:
            shutil.rmtree(target_tiff_folder, ignore_errors=True)
            print("Will re-process: " + str(target_tiff_folder))
        else:
            print("Already exists: " + str(target_tiff_folder))
            continue

    # Requesting multiple bands at once gives confusing results
    for band_name in ["2m_temperature", "total_precipitation"]:
        target_file = download_path / f"download_{year}_{band_name}.netcdf.zip"
        months = list(range(1, 13))
        if today.year == year and target_file.exists():
            os.remove(target_file)  # trigger re-download
            # Requesting months that do not exist yet gives bad data
            months = list(range(1, today.month - 3))  # Dataset rus a few months behind
        if not target_file.exists():
            tmp_file_path = target_file.parent / (target_file.name + ".tmp")
            if tmp_file_path.exists():
                os.remove(tmp_file_path)
            c.retrieve(
                "reanalysis-era5-land-monthly-means",
                {
                    "product_type": "monthly_averaged_reanalysis",
                    "variable": band_name,
                    "year": [year],
                    "month": months,
                    "time": "00:00",
                    "area": [
                        # South Africa
                        -20, 10, -40, 40,
                    ],
                    "format": "netcdf.zip",
                },
                tmp_file_path,
            )
            os.rename(tmp_file_path, target_file)  # atomic, to avoid corrupt files
        netcdf_zip_to_gtiff(target_file)

print("Done")
