@echo off
rem Install the Python 3.10 version to the computer
if exist "./bin/python-3.10.11-amd64.exe" (
    rem file exists so run the installation file
    echo 64-bit version of Python 3.10 is already installed.
	call "./bin/python-3.10.11-amd64.exe"
) else (
    rem file doesn't exist - download from the internet and setup
    echo 64-bit version of Python 3.10 not found on the computer.
    echo Downloading the installer from python.org and running it...
    start "" https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
)

echo Python 3.10.11 installed on the computer.
pause
echo Now installing the necessary Python libraries to run SPEC-debris-barrier...

python -m pip install pip --upgrade
python -m pip install pyyaml==6.0.1
python -m pip install numpy==1.26.4
python -m pip install pandas==2.2.2
python -m pip install scipy==1.13.0
python -m pip install plotly==5.22.0
python -m pip install laspy==2.5.3
python -m pip install pykrige==1.7.1
python -m pip install scikit-learn==1.4.2

echo All necessary Python libraries for 3DTS installed!
pause
