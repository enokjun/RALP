#!/bin/bash

# check if Python3 is installed in Linux
type -p python3 >/dev/null 2>& sudo apt install python3.10 && echo Python 3 is already installed

# check pip is installed in linux
type -p pip3 --version >/dev/null 

echo Now installing the necessary Python libraries to run SPEC-debris-barrier...

python3 -m pip3 install pip3 --upgrade
python3 -m pip3 install pyyaml==6.0.1
python3 -m pip3 install numpy==1.26.4
python3 -m pip3 install pandas==2.2.2
python3 -m pip3 install scipy==1.13.0
python3 -m pip3 install plotly==5.22.0
python3 -m pip3 install laspy==2.5.3
python3 -m pip3 install pykrige==1.7.1
python3 -m pip3 install scikit-learn==1.4.2

echo All necessary Python libraries for 3DTS installed!

