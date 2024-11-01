## General Overview
The tools developed in this project can be deployed and executed using Jupyter Notebooks. This section of the Handbook follows the previous section and presents a simple workflow for computing the drought indices. For a more detailed explanation of each index, it's use and application, see the [Specifications](theoretical_basis.md).

!!! Warning "Before your proceed"
    1. Make sure have created and activated the [Conda Virtual Environment](Installation.md#create-a-virtual-environment-with-conda).
    2. Unzip the CNTR_RG_01M_2020_4325.zip file. It is a shapefile what will enable you to run the tool and follow along if you wish to do so. You can do so by *right-clicking on the file in your File Explorer*>*Extract All...*>*Extract*.

## Example 1: Standardised Precipitation Index (SPI)
The SPI tool provides monthly time-series information based on precipitation data. It is computed at a national scale at a resolution of 1° x 1° and requires no temporal extent as an input.

1. To run SPI, start by open the SPI.ipynb file in the SPI folder.
2. Click on the first cell in the notebook and run it. This should prompt a box near the top of your VSCode to appear:
    ![alt text](<assets/python_environments.png>)

3. Click on "*Python Environments...*", and select "*anin*".
4. In the second cell under the `ERA5_input_path` parameter, input the path to the ERA_monthly.nc file.
5. For the `shapefile_path` parameter, input the path to the CNTR_RG_01M_2020_4326.shp file.
6. Create a folder in GMV-ANIN to store the tool's outputs. I named mine 'outputs'. Input that folder path to the `path_out` parameter.
7. Choose an output filename for the SPI product you plan on producing, for example "SPI_test.nc". Input it under the `SPI_output_file` parameter.
8. Once you are done the second cell should look something like this:
   ![alt text](<assets/cell_example.png>)
9. Run the remainder of cells from the second one onwards.
10. Once all cells have run you should see the output file in your 'outputs' folder.

!!! tip "Filepaths in Windows"
    Python on occasion has difficulties with Windows filepaths due to their use of backslashes. To avoid any complications ensure your filepaths have double backslashes in them.
!!! tip "Running a Cell in Jupyter Notebooks"
    You can run any cell you have selected in Jupyter notebooks by pressing (Ctrl + Enter). (Shift + Enter) will run the cell and select the following one.

The script will create the output netCDF file in the folder you input as your `path_out` parameter. This output can be visualized using QGIS.
!!! note "Example SPI output over South Africa, Leshoto, and Eswatini"
    <figcaption>![alt text](<assets/SPI_results_clipped.png>){width="600"}<figcaption>

## Vizualizing Outputs
A section detailing how best to visualize the outputs will be added to the documentation shortly.