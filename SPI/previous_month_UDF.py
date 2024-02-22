from openeo.udf import XarrayDataCube


def apply_datacube(cube: XarrayDataCube, context: dict) -> XarrayDataCube:
    array = cube.get_array()
    # Not sure if shifting one month or one day.
    array.shift(t=1)  # Probably uses NaN as filler value

    # num_days_month = array.t.dt.days_in_month
    # num_days_month = 30

    # No need to specify crs here
    return XarrayDataCube(array)
