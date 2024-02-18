import logging
import scipy
import numpy as np
import xarray as xr
from openeo.udf import XarrayDataCube

_log = logging.getLogger("FAPAR_Anomaly_UDF")

def anomaly_calculator(input_array: np.ndarray):
    # second_axis_length = 12
    # values = np.pad(values,
    #                 pad_width=(0, pads),
    #                 mode="constant",
    #                 constant_values=np.NaN)
    # first_axis_length = int(input_array.shape[0] / second_axis_length)
    # reshaped = np.reshape(input_array, newshape=(first_axis_length, second_axis_length))

    values_per_month = [[], [], [], [], [], [], [], [], [], [], [], []]  # Made with repr([[]] * 12)
    # values_per_month = list(map(lambda x: np.full(12, np.nan), range(0, 12)))
    for i in range(input_array.size):
        month = i % 12
        val = input_array.data[i]
        if np.isnan(val):
            raise Exception("nok!")
            # Will aggregate ove a big time period, so some missing values should be ok
        values_per_month[month].append(val)
    # np.nanmean(month_values, axis=)
    # np.nanstd(month_values)
    values_per_month = list(map(lambda x: np.array(x), values_per_month))
    average_per_month = list(map(lambda month_values: month_values.mean(), values_per_month))
    sd_per_month = list(map(lambda month_values: month_values.std(), values_per_month))

    average_per_month = list(map(lambda month_values: scipy.stats.zscore(month_values), values_per_month))

    array_z_score = np.full(input_array.size, np.nan)
    for i in range(input_array.size):
        month = i % 12
        val = input_array.data[i]
        array_z_score[i] = (val - average_per_month[month]) / sd_per_month[month]

    # No need to specify crs here
    return xr.DataArray(
        data=array_z_score,
        dims=["t"],
    )


def apply_datacube(cube: XarrayDataCube, context: dict) -> XarrayDataCube:
    input_array_with_bands = cube.get_array()
    # _log.warn("input_array_with_bands.shape: " + str(input_array_with_bands.shape))
    # ('t', 'band', 'y', 'x')
    blah = scipy.stats.zscore(input_array_with_bands.values, axis=0, nan_policy="omit")
    # blah = blah.rename({'x': 'longitude', 'y': 'latitude'})
    output_array_with_bands = xr.DataArray(
        data=blah,
        dims=input_array_with_bands.dims,
    )

    # output_array_with_bands = xr.apply_ufunc(anomaly_calculator,
    #                                          input_array_with_bands,
    #                                          input_core_dims=[["t"]],
    #                                          output_core_dims=[["t"]],
    #                                          dask="parallelized",
    #                                          output_dtypes=['float32'],
    #                                          vectorize=True,
    #                                          )
    # _log.warning("spi_wrapped(...) ret.shape: " + str(
    #     ret.shape) + " input_array.shape: " + str(ret.shape))
    return XarrayDataCube(output_array_with_bands)


if __name__ == "__main__":
    # Test code:
    import rioxarray as rxr
    from pathlib import Path

    file_path_tiffs = list(Path("/dataCOPY/users/Public/emile.sonneveld/GLASS_FAPAR_Layer/tiff_collection/2000")
                           .rglob("*.h20v11.*.hdf.tiff"))
    # file_path_tiffs = file_path_tiffs[0:4]
    tiles = list(map(lambda x: rxr.open_rasterio(x, masked=True), file_path_tiffs))
    array = xr.concat(tiles, "t")

    # array = xr.DataArray(
    #     data=[1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
    #           13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    #           np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,
    #           ],
    #     dims=["t"],
    # )
    # array = array.expand_dims(dim='bands', axis=1).assign_coords(bands=["band_name"])
    # array = array.expand_dims(dim='x', axis=1)
    # array = array.expand_dims(dim='y', axis=1)
    # 1000*1000
    array = array.isel(x=range(0, 100), y=range(0, 100))  # Sub-region for performance
    ret = apply_datacube(XarrayDataCube(array), dict())
    ret.array.sel(band=0).transpose('t', 'y', 'x').rio.to_raster("out.tmp.nc", compress='DEFLATE')
    print(ret)
