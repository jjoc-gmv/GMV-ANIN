# Drought indices

## Installation:

```bash
git clone https://git-ext.gmv.com/anin-external/drought-indices.git
cd drought-indices
git checkout openeo
python3 -m pip install -r requirements.txt
```

To install on CONDA: `conda install -c conda-forge openeo`

More instructions here: https://open-eo.github.io/openeo-python-client/installation.html

## Running:

```bash
python3 -m CDI.CDI_openeo
python3 -m FAPAR_Anomaly.FAPAR_Anomaly_openeo
python3 -m SMA.SMA_openeo
python3 -m SPI.SPI_openeo
python3 -m VCI.VCI_openeo
```

## Notes

OpenEO code formatted with 'Black', default settings
Example output files can be found here: https://gmvdrive.gmv.com/index.php/s/oLj4moSZ2Ez5G5P?path=%2F
