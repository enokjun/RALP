#!/bin/bash

# check if Python3 is installed in Mac
type -p python3 >/dev/null 2>& open https://www.python.org/ftp/python/3.10.11/python-3.10.11-macos11.pkg && echo Python 3 is already installed

# check pip is installed in Mac
type -p pip3 --version >/dev/null 

echo Now installing the necessary Python libraries to run SPEC-debris-barrier...

python3 -m pip install pip --upgrade
python3 -m pip install pyyaml==6.0.1
python3 -m pip install numpy==1.26.4
python3 -m pip install pandas==2.2.2
python3 -m pip install scipy==1.13.0
python3 -m pip install plotly==5.22.0
python3 -m pip install laspy==2.5.3
python3 -m pip install pykrige==1.7.1
python3 -m pip install scikit-learn==1.4.2

echo All necessary Python libraries for 3DTS installed!

