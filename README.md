# Robust Areal Landslide Prediction (RALP) software 

The RALP software provides a graphical user interface (GUI) enabling users to select parameters and generate necessary files 
for performing physically based landslide susceptibility analysis for 3DTSP and 3DPLS.

The repository provides the necessary Python scripts to run the RALP software on Windows, Linux, and Mac OS. 
However, it requires users to install Python and the necessary libraries.

For Windows users, it is recommended to download the **"RALP_v1_03_window_setup.exe"** and install it on a local Windows PC. 
It already includes Python and the libraries required to run 3DTSP and 3DPLS. 
Therefore, it does not require users to install or set up a Python environment.
If, for any reason, the software exe file is considered to be dangerous (virus or company system),
please enable the anti-virus software or identify the software as safe.
Otherwise, please use the **start_GUI_windows.bat** file to start the Windows version of the RALP software.

**Update on the RALP windows version might be slower, so please check the version**

More details on the installation, RALP manual, and examples are described in the **"Robust Areal Landslide Prediction (RALP) - GUI v1.03 - User Manual.pdf"**.

# References
- [3DPLS]	Oguz, EA, Depina I, Thakur V (2022) Effects of soil heterogeneity on susceptibility of shallow landslides. Landslides, 19(1):67-83. https://doi.org/10.1007/s10346-021-01738-x
- [3DTS] Cheon, E., Ahmet Oguz, E., DiBiagio, A., Piciullo, L., Kwon, T. H., and Lee, S. R. (2025a): A Physically-based 3D Landslide Susceptibility Model for Shallow Translational Landslides using DEM, EGU General Assembly 2025, Vienna, Austria, 27 Apr–2 May 2025, EGU25-17059, https://doi.org/10.5194/egusphere-egu25-17059
- [3DTS] Cheon E, Oguz EA, DiBiagio A, Piciullo L (2025) A 3D Shallow Translational Landslide Susceptibility Model with DEM Cells Accounting for Side Resistance and Vegetation Effects. The 9th International Symposium for Geotechnical Safety and Risk (ISGSR) at Oslo, Norway. https://doi.org/10.3850/GRF-25280825_isgsr-007-P354-cd
- [3DTS] Cheon E, Oguz EA, DiBiagio A, Piciullo L (2025) A 3D Shallow Translational Landslide Susceptibility Model Accounting for Side Resistance and Vegetation Effects (under revision)

# Acknowledgement
- The slope stability models were developed through contributions and comments by **Dr. Emir A. Oguz**, **Amanda DiBiagio**, and **Lica Piciullo**
- The preparation of the user manual was funded by the basic support and the HUT project provided to Norwegian Geotechnical Institute (NGI) by the Research Council of Norway

# Contact
- Please email **enok.cheon@ngi.no** if you need to. However, to inform us of any found bugs, software issues, or general feedback, please use the GitHub Issues

# Version
**ver 1.03**
- fixed issues regarding vegetation weight
- fixed incorrect plotting of 2D plots
- added feature to generate 2D animation of results over time

**ver 1.02**
- fixed issues regarding unit not converted when rainfall intensity is defined from GIS files
  
**ver 1.01**
- fixed issues when assigning the initial groundwater table using the "thickness above bedrock" option
- fixed the symbol of initial suction pressure to correctly show $\psi_i$ instead of $\theta_i$, as $\theta_i$ would refer to initial volumetric water content
  
**ver 1.00**
- performs combined hydrological infiltration analysis and slope stability analysis with either a deterministic or probabilistic approach for determining landslide geohazard risk with **3DPLS** and **3DTS** models
