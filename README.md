# Robust Areal Landslide Prediction (RALP) software 

The RALP software provides a graphical user interface (GUI) enabling users to select parameters and generate necessary files 
for performing physically based landslide susceptibility analysis for 3DTSP and 3DPLS.

The repository provides the necessary Python scripts to run the RALP software on Windows, Linux, and MacOS. 
However, it requires users to install Python and the necessary libraries.

For Windows users, it is recommended to download the **"RALP_v1_00_window_setup.exe"** and install it on a local Windows PC. 
It already contains Python and the libraries required for running 3DTSP and 3DPLS. 
Therefore, it does not require the users to install and set up the Python environment.
If for any reason, the software exe file is considered to be dangerous (virus or company system),
please enable the software or identify the software as safe.
Otherwise, please use the **start_GUI_windows.bat** file to start the windows-version RALP software.

**Update on the RALP windows version might be slower, so please check the version**

More details on the installation, RALP manual, and examples are described in the **"Robust Areal Landslide Prediction (RALP) - GUI v1.00 - User Manual.pdf"**.

# References
- [3DPLS]	Oguz, EA, Depina I, Thakur V (2022) Effects of soil heterogeneity on susceptibility of shallow landslides. Landslides, 19(1):67-83. https://doi.org/10.1007/s10346-021-01738-x
- [3DTS] Cheon E, Oguz EA, DiBiagio A, Piciullo L (2025) A 3D Shallow Translational Landslide Susceptibility Model with DEM Cells Accounting for Side Resistance and Vegetation Effects. The 9th International Symposium for Geotechnical Safety and Risk (ISGSR) at Oslo, Norway. https://doi.org/10.3850/GRF-25280825_isgsr-007-P354-cd

# Contact
- Please email **enok.cheon@ngi.no** if you need to. However, to inform us of any found bugs, software issues, or general feedback, please use the GitHub Issues

# ver 1.01
- fixed issues when assign initial groundwater table using the "thickness above bedrock" option
- fixed the symbol of initial suction pressure to correctly show $\psi_i$ instead of $\theta_i$, as $\theta_i$ would refer to initial volumetric water content
