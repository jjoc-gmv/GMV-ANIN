
import numpy as np
import pandas as pd
import spei as si
import scipy.stats as scs
from shapely.geometry import Point
import geopandas as gpd



def sum_to_scale(
        values: np.ndarray,
        scale: int,
) -> np.ndarray:
    """
    Compute a sliding sums array using 1-D convolution. The initial
    (scale - 1) elements of the result array will be padded with np.NaN values.
    Missing values are not ignored, i.e. if a np.NaN
    (missing) value is part of the group of values to be summed then the sum
    will be np.NaN
    For example if the first array is [3, 4, 6, 2, 1, 3, 5, 8, 5] and
    the number of values to sum is 3 then the resulting array
    will be [np.NaN, np.NaN, 13, 12, 9, 6, 9, 16, 18].
    More generally:
    Y = f(X, n)
    Y[i] == np.NaN, where i < n
    Y[i] == sum(X[i - n + 1:i + 1]), where i >= n - 1 and X[i - n + 1:i + 1]
        contains no NaN values
    Y[i] == np.NaN, where i >= n - 1 and X[i - n + 1:i + 1] contains
        one or more NaN values
    :param values: the array of values over which we'll compute sliding sums
    :param scale: the number of values for which each sliding summation will
        encompass, for example if this value is 3 then the first two elements of
        the output array will contain the pad value and the third element of the
        output array will contain the sum of the first three elements, and so on
    :return: an array of sliding sums, equal in length to the input values
        array, left padded with NaN values
    """

    # don't bother if the number of values to sum is 1
    if scale == 1:
        return values

    # get the valid sliding summations with 1D convolution
    sliding_sums = np.convolve(values, np.ones(scale), mode="valid")

    # pad the first (n - 1) elements of the array with NaN values
    return np.hstack(([np.NaN] * (scale - 1), sliding_sums))

    # BELOW FOR dask/xarray DataArray integration
    # # pad the values array with (scale - 1) NaNs
    # values = pad(values, pad_width=(scale - 1, 0), mode='constant', constant_values=np.NaN)
    #
    # start = 1
    # end = -(scale - 2)
    # return convolve(values, np.ones(scale), mode='reflect', cval=0.0, origin=0)[start: end]


def compute_sgi(
    timeseries:pd.Series,
    scale: int,
) -> pd.Series:
    """bla"""

    if scale == 1:
        scaled_sgi = si.sgi(timeseries)
    else:
        dates = timeseries.index.to_pydatetime()
        scaled_np = sum_to_scale(timeseries,scale)
        scaled_np_unstacked = np.hsplit(scaled_np,1)
        scaled_gwl = np.vstack(scaled_np_unstacked).T
        scaled_gwl_ts = pd.Series(data = scaled_gwl.flatten(), index=dates)
        scaled_sgi = si.sgi(scaled_gwl_ts)

    return scaled_sgi

def compute_ssfi(
    timeseries:pd.Series,
    scale: int,
) -> pd.Series:
    """bla"""
    dates = timeseries.index.to_pydatetime()

    if scale == 1:
        z = scs.mstats.plotting_positions(timeseries,0,0)
        ssi = (z - np.mean(z)) / np.std(z)
        scaled_ssfi = pd.Series(data = ssi, index=dates)
    else:
        scaled_np = sum_to_scale(timeseries,scale)
        scaled_np_unstacked = np.hsplit(scaled_np,1)
        scaled_ts = np.vstack(scaled_np_unstacked).T
        scaled_ts = pd.Series(data = scaled_ts.flatten(), index=dates)
        z = scs.mstats.plotting_positions(scaled_ts,0,0)
        ssi = (z - np.mean(z)) / np.std(z)
        scaled_ssfi = pd.Series(data = ssi, index=dates)

    return scaled_ssfi


def average_index(df_latlon,shapefile,averaging_field):

    # Convert the stations dataframe into a GeoDataFrame by specifying the geometry column with the coordinates:

    geometry = [Point(xy) for xy in zip(df_latlon['Longitude'], df_latlon['Latitude'])]
    stations_gdf = gpd.GeoDataFrame(df_latlon, geometry=geometry)

    # Perform a spatial join between the polygons and the stations to determine which stations fall within each polygon:
    stations_by_polygon = gpd.sjoin(shapefile, stations_gdf, how='inner', op='contains')

    # Select the columns based on their numeric names
    time_step_columns = [col for col in stations_by_polygon.columns if str(col).isdigit()]

    # Group the stations by polygon and time step, and calculate the average for each group:
    averaged_index = stations_by_polygon.groupby([averaging_field])[time_step_columns].mean()

    return averaged_index
