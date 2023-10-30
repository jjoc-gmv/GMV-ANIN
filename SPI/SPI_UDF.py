import numpy as np
import os
import sys
import xarray as xr
from openeo.udf import XarrayDataCube

wheel_path = '/data/users/Public/emile.sonneveld/python/climate_indices-1.0.13-py2.py3-none-any.whl'
if not os.path.exists(wheel_path):
    raise Exception("Path not found: " + wheel_path)
sys.path.append(wheel_path)
import climate_indices
from climate_indices import indices

############################## SETTING PARAMETERS  for the SPI ##############################

scale = 3
distribution = climate_indices.indices.Distribution.gamma  # Fixed
data_start_year = 1980
calibration_year_initial = 1980
calibration_year_final = 2023
periodicity = climate_indices.compute.Periodicity.monthly  # Fixed

if calibration_year_final - calibration_year_initial <= 2:
    print("Gamma correction in SPI on only 2 years will give bad looking results")


def spi_wrapped(values: np.ndarray):
    return indices.spi(
        values=values,
        scale=scale,
        distribution=distribution,
        data_start_year=data_start_year,
        calibration_year_initial=calibration_year_initial,
        calibration_year_final=calibration_year_final,
        periodicity=periodicity,
    )[np.newaxis].T


def proccessingNETCDF(data: xr.DataArray):
    """Process the data to serve as input to de SPI function
    Args:
        data: netcdf file

        Returns
        DataArrayGroupBy grouped over point (y and x coordinates)
    """
    num_days_month = data.t.dt.days_in_month
    # num_days_month = 30

    tp_scale_factor = 2.180728636941368e-07
    tp_add_offset = 0.007146202370012436
    data_precip = (data * tp_scale_factor) + tp_add_offset  # Rescaling the values
    # data_precip = (data * 2.908522800670776e-07) + 0.009530702520736942  # Rescaling the values
    # data_precip = data_precip * 1000  # The original units are meters, we change them to millimeters, and multiply by the days of the month
    data_precip = data_precip.squeeze()

    # Giving the appropriate shape to da data
    data_grouped = data_precip.stack(point=('y', 'x')).groupby('point')
    print("""Data is prepared to serve as input for the SPI index.""")

    return data_grouped


def apply_datacube(cube: XarrayDataCube, context: dict) -> XarrayDataCube:
    array = cube.get_array()

    data_grouped = proccessingNETCDF(array)
    spi_results = xr.apply_ufunc(spi_wrapped,
                                 data_grouped,
                                 # input_core_dims=[["t"]],
                                 # output_core_dims=[["t"]],
                                 )

    BAND_NAME = 'SPI'
    spi_results = spi_results.expand_dims(dim='bands', axis=0).assign_coords(bands=[BAND_NAME])
    spi_results = spi_results.unstack('point')
    spi_results = spi_results.rename({'y': 'lat', 'x': 'lon'})  # Necessary step
    spi_results = spi_results.reindex(lat=list(reversed(spi_results['lat'])))
    spi_results = spi_results.rename({'lat': 'y', 'lon': 'x'})
    # No need to specify crs here
    return XarrayDataCube(spi_results)


if __name__ == "__main__":
    print("Running test code!")
    import pandas as pd

    d = [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
         13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
         25, 26, 27, 28, 29, 30]
    dates = pd.to_datetime(d)
    array = xr.DataArray(
        data=d,
        coords=dates,
        dims=["t"],
    )

    array = array.expand_dims(dim='bands').assign_coords(bands=["band_name"])
    array = array.expand_dims(dim='x')
    array = array.expand_dims(dim='y')

    ret = apply_datacube(XarrayDataCube(array), dict())
    print(ret)
