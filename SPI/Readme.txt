Calculate the SPI as follows:

python3.11 -m venv --without-pip ./venv
. venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python3.11
python3.11 -m pip install -r requirements.txt 


The results have a lookalike distribution as the SPI originally calculated by GMV, but still has some slight differences. Probably because the openeo version only starts calculating from 2015, and the GMV version from 1980.

There is also an artifact line visible. This could be due to a polygon glitch.

The output result does not weight mush and is committed in this repository.
