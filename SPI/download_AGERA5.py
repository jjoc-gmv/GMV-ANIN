import datetime
import os
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
download_path = Path("/data/users/Public/emile.sonneveld/ERA5-Land-monthly/")
if not download_path.exists():
    raise Exception("download_path not found: " + str(download_path))


def netcdf_zip_to_gtiff(netcdf_zip_path):
    # unzip_folder = download_path / ("unzip_" + netcdf_zip_path.name)
    unzip_folder = Path(tempfile.gettempdir()) / ("unzip_" + netcdf_zip_path.name)
    shutil.rmtree(unzip_folder, ignore_errors=True)
    unzip_folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(netcdf_zip_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_folder)
    results = list(unzip_folder.rglob('*.nc'))
    assert len(results) == 1
    net_cdf_file = results[0]

    src_ds = osgeo.gdal.Open(str(net_cdf_file))
    if src_ds is None:
        return None
    assert src_ds.RasterCount == 12  # one per month
    for band_nr in range(src_ds.RasterCount):
        band_nr += 1
        band = src_ds.GetRasterBand(band_nr)

        stats = band.GetStatistics(True, True)
        print("Band %s Min=%.3f, Max=%.3f, Mean=%.3f, StdDev=%.3f" %
              (band_nr, stats[0], stats[1], stats[2], stats[3]))

        mtdata = band.GetMetadata()
        NETCDF_DIM_time = int(mtdata["NETCDF_DIM_time"])
        name = mtdata["long_name"].lower().replace(" ", "_")
        # Hardcoded start date:
        date = datetime.date(1900, 1, 1) + datetime.timedelta(hours=NETCDF_DIM_time)
        print("date: " + str(date))
        download_path / "tiff_collection"
        yyy = "{:04d}".format(date.year)
        mm = "{:02d}".format(date.month)
        dd = "{:02d}".format(date.day)
        output_file = (download_path / "tiff_collection" / yyy / mm / dd / f"{yyy}-{mm}-{dd}_{name}.tiff")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        arr = band.ReadAsArray()
        [rows, cols] = arr.shape
        driver = osgeo.gdal.GetDriverByName("GTiff")

        # Write single band as GeoTIFF:
        out_ds = driver.Create(str(output_file), cols, rows, 1, band.DataType)
        out_ds.SetGeoTransform(src_ds.GetGeoTransform())
        out_ds.SetProjection(src_ds.GetProjection())
        out_ds.SetMetadata(src_ds.GetMetadata())

        out_srs = osgeo.osr.SpatialReference()
        out_srs.ImportFromEPSG(4326)
        # https://github.com/OSGeo/gdal/issues/1677
        # out_ds.SetSpatialRef(out_srs)  # Make explicit to be sure

        out_ds.GetRasterBand(1).WriteArray(arr)
        out_ds.GetRasterBand(1).SetNoDataValue(band.GetNoDataValue())
        out_ds.FlushCache()  # Saves to disk
    shutil.rmtree(unzip_folder, ignore_errors=True)
    # os.rmdir(unzip_folder) # Can't always do due to '.nfs' file


# Requests years separately to allow to re-run this script after an interruption
for year in range(1980, 2015):
    print("year: " + str(year))
    (download_path / "tiff_collection").mkdir(exist_ok=True)
    target_tiff_folder = download_path / "tiff_collection" / str(year)
    if target_tiff_folder.exists():
        print("Already exists: " + str(target_tiff_folder))
        continue

    # Requesting multiple bands at once gives confusing results
    for band_name in ['2m_temperature', 'total_precipitation']:

        target_file = download_path / f'download_{year}_{band_name}.netcdf.zip'
        if not target_file.exists():
            c.retrieve(
                'reanalysis-era5-land-monthly-means',
                {
                    'product_type': 'monthly_averaged_reanalysis',
                    'variable': band_name,
                    'year': [
                        year
                    ],
                    'month': [
                        '01', '02', '03',
                        '04', '05', '06',
                        '07', '08', '09',
                        '10', '11', '12',
                    ],
                    'time': '00:00',
                    'area': [
                        # South Africa
                        -20, 10, -40, 40,
                    ],
                    'format': 'netcdf.zip',
                },
                target_file)
        # target_tiff_folder.parent.mkdir(parents=True, exist_ok=True)
        netcdf_zip_to_gtiff(target_file)

    exit(0)  # remove once testing is done
