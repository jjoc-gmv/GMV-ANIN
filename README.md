# Drought indices

## Running some openEO code:

```bash
git clone https://git-ext.gmv.com/anin-external/drought-indices.git
cd drought-indices
git checkout openeo
```

Run

```bash
python3 -m pip install -r requirements.txt
cd ..
python3 -m drought-indices.CDI.CDI_openeo
python3 -m drought-indices.FAPAR_Anomaly.FAPAR_Anomaly_openeo
python3 -m drought-indices.SMA.SMA_openeo
python3 -m drought-indices.SPI.SPI_openeo
python3 -m drought-indices.VCI.VCI_openeo
```

## Notes

OpenEO code formatted with 'Black', default settings
Example output files can be found here: https://gmvdrive.gmv.com/index.php/s/oLj4moSZ2Ez5G5P?path=%2F
