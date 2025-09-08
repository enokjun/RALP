"""
#####
## 3DPLS version 1.0
## Main code
#####

The 3-Dimensional Probabilistic Landslide Susceptibility (3DPLS) model is a Python code developed for landslide susceptibility assessment.
The 3DPLS model evaluates the landslide susceptibility on a local to a regional scale (i.e. single slope to 10 km2)
and allows for the effects of variability of model parameter on slope stability to be accounted for.
The 3DPLS model couples the hydrological and the slope stability models. The hydrological model calculates the
transient pore pressure changes due to rainfall infiltration using Iverson’s linearized solution of the Richards equation
(Iverson 2000) assuming tension saturation. The slope stability model calculates the factor of safety by utilizing the extension of
Bishop’s simplified method of slope stability analysis (Bishop 1955) to three dimensions, proposed in the study of Hungr (1987).
The 3DPLS model requires topographic data (e.g., DEM, slope, aspect, groundwater depth, depth to bedrock, geological zones),
hydrological parameters (e.g., steady background infiltration rate, permeability coefficient, diffusivity),
geotechnical parameters (e.g., soil unit weight, cohesion, friction angle), and rainfall data.

Developed by: Emir Ahmet Oguz

The code was first developed in 2020 April-December for research purposes (3DPLS version 0.0).
The code has been improved in 2022 through a project supported by NTNU's Innovation Grant (3DPLS version 1.0).

Paper: Oguz, E.A., Depina, I. & Thakur, V. Effects of soil heterogeneity on susceptibility of shallow landslides. Landslides 19, 67–83 (2022). https://doi.org/10.1007/s10346-021-01738-x

"""

## Libraries
import os
import numpy as np
import time
import yaml  ## For reading YAML configuration files

# Configure matplotlib for different environments
import matplotlib
try:
    # Try to use an interactive backend that works with terminal
    matplotlib.use('TkAgg')  # or 'Qt5Agg' if you have Qt
except ImportError:
    # Fall back to a non-interactive backend
    matplotlib.use('Agg')
    print("Warning: Using non-interactive matplotlib backend. Plots will be saved but not displayed.")

import matplotlib.pyplot as plt
# import pickle
# from multiprocessing import Process, Queue, Array, cpu_count  ## For Parallelization
from multiprocessing import cpu_count  ## For Parallelization
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)  ##To remove the warnings (due to FS calculation iterations)

"""
#####################################################################################
## YAML Configuration Loading
#####################################################################################
"""

def load_yaml_config(yaml_path):
    """Load and parse YAML configuration file"""
    with open(yaml_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def parse_soil_parameters(config, analysis_type):
    """Parse soil parameters from YAML configuration"""
    soil_config = config['soil_parameters']
    zones = [key for key in soil_config.keys() if key.startswith('zone_')]
    num_zones = len(zones)

    if analysis_type == "Drained":
        # Initialize arrays for drained analysis
        Mean_cInp = np.zeros(num_zones)
        Mean_phiInp = np.zeros(num_zones)
        Mean_uwsInp = np.zeros(num_zones)
        Mean_kSatInp = np.zeros(num_zones)
        Mean_diffusInp = np.zeros(num_zones)

        CoV_cInp = np.zeros(num_zones)
        CoV_phiInp = np.zeros(num_zones)
        CoV_uwsInp = np.zeros(num_zones)
        CoV_kSatInp = np.zeros(num_zones)
        CoV_diffusInp = np.zeros(num_zones)

        Dist_cInp = np.array(['N'] * num_zones, dtype=object)
        Dist_phiInp = np.array(['N'] * num_zones, dtype=object)
        Dist_uwsInp = np.array(['N'] * num_zones, dtype=object)
        Dist_kSatInp = np.array(['N'] * num_zones, dtype=object)
        Dist_diffusInp = np.array(['N'] * num_zones, dtype=object)

        CorrLenX_cInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_cInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenX_phiInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_phiInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenX_uwsInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_uwsInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenX_kSatInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_kSatInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenX_diffusInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_diffusInp = np.array(['inf'] * num_zones, dtype=object)

        # Parse each zone
        for i, zone in enumerate(zones):
            zone_data = soil_config[zone]

            # Cohesion
            Mean_cInp[i] = zone_data['cohesion']['mean_cInp']
            CoV_cInp[i] = zone_data['cohesion']['cov_cInp']
            Dist_cInp[i] = "LN" if zone_data['cohesion']['dist_cInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['cohesion']['corrLenX_cInp']
            CorrLenX_cInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['cohesion']['corrLenY_cInp']
            CorrLenY_cInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

            # Friction angle
            Mean_phiInp[i] = zone_data['friction_angle']['mean_phiInp']
            CoV_phiInp[i] = zone_data['friction_angle']['cov_phiInp']
            Dist_phiInp[i] = "LN" if zone_data['friction_angle']['dist_phiInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['friction_angle']['corrLenX_phiInp']
            CorrLenX_phiInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['friction_angle']['corrLenY_phiInp']
            CorrLenY_phiInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

            # Unit weight
            Mean_uwsInp[i] = zone_data['unit_weight']['mean_uwsInp']
            CoV_uwsInp[i] = zone_data['unit_weight']['cov_uwsInp']
            Dist_uwsInp[i] = "LN" if zone_data['unit_weight']['dist_uwsInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['unit_weight']['corrLenX_uwsInp']
            CorrLenX_uwsInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['unit_weight']['corrLenY_uwsInp']
            CorrLenY_uwsInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

            # Saturated permeability
            Mean_kSatInp[i] = zone_data['saturated_permeability']['mean_kSatInp']
            CoV_kSatInp[i] = zone_data['saturated_permeability']['cov_kSatInp']
            Dist_kSatInp[i] = "LN" if zone_data['saturated_permeability']['dist_kSatInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['saturated_permeability']['corrLenX_kSatInp']
            CorrLenX_kSatInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['saturated_permeability']['corrLenY_kSatInp']
            CorrLenY_kSatInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

            # Diffusivity
            Mean_diffusInp[i] = zone_data['diffusivity']['mean_diffusInp']
            CoV_diffusInp[i] = zone_data['diffusivity']['cov_diffusInp']
            Dist_diffusInp[i] = "LN" if zone_data['diffusivity']['dist_diffusInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['diffusivity']['corrLenX_diffusInp']
            CorrLenX_diffusInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['diffusivity']['corrLenY_diffusInp']
            CorrLenY_diffusInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

        # Create parameter arrays as expected by the original code
        Parameter_Means = np.array([[Mean_cInp], [Mean_phiInp], [Mean_uwsInp], [Mean_kSatInp], [Mean_diffusInp]], dtype=float)
        Parameter_CoVs = np.array([[CoV_cInp], [CoV_phiInp], [CoV_uwsInp], [CoV_kSatInp], [CoV_diffusInp]], dtype=float)
        Parameter_Dist = np.array([[Dist_cInp], [Dist_phiInp], [Dist_uwsInp], [Dist_kSatInp], [Dist_diffusInp]], dtype=object)
        Parameter_CorrLenX = np.array([[CorrLenX_cInp], [CorrLenX_phiInp], [CorrLenX_uwsInp], [CorrLenX_kSatInp], [CorrLenX_diffusInp]], dtype=object)
        Parameter_CorrLenY = np.array([[CorrLenY_cInp], [CorrLenY_phiInp], [CorrLenY_uwsInp], [CorrLenY_kSatInp], [CorrLenY_diffusInp]], dtype=object)

    elif analysis_type == "Undrained":
        # Initialize arrays for undrained analysis
        Mean_SuInp = np.zeros(num_zones)
        Mean_uwsInp = np.zeros(num_zones)

        CoV_SuInp = np.zeros(num_zones)
        CoV_uwsInp = np.zeros(num_zones)

        Dist_SuInp = np.array(['N'] * num_zones, dtype=object)
        Dist_uwsInp = np.array(['N'] * num_zones, dtype=object)

        CorrLenX_SuInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_SuInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenX_uwsInp = np.array(['inf'] * num_zones, dtype=object)
        CorrLenY_uwsInp = np.array(['inf'] * num_zones, dtype=object)

        # Parse each zone
        for i, zone in enumerate(zones):
            zone_data = soil_config[zone]

            # Undrained shear strength
            Mean_SuInp[i] = zone_data['undrained_shear_strength']['mean_SuInp']
            CoV_SuInp[i] = zone_data['undrained_shear_strength']['cov_SuInp']
            Dist_SuInp[i] = "LN" if zone_data['undrained_shear_strength']['dist_SuInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['undrained_shear_strength']['corrLenX_SuInp']
            CorrLenX_SuInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['undrained_shear_strength']['corrLenY_SuInp']
            CorrLenY_SuInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

            # Unit weight (also available in undrained)
            Mean_uwsInp[i] = zone_data['unit_weight']['mean_uwsInp']
            CoV_uwsInp[i] = zone_data['unit_weight']['cov_uwsInp']
            Dist_uwsInp[i] = "LN" if zone_data['unit_weight']['dist_uwsInp'] == "Lognormal" else "N"
            # Handle correlation length: keep 'inf' as string, convert numbers to float
            corrx_val = zone_data['unit_weight']['corrLenX_uwsInp']
            CorrLenX_uwsInp[i] = corrx_val if corrx_val == 'inf' else float(corrx_val)
            corry_val = zone_data['unit_weight']['corrLenY_uwsInp']
            CorrLenY_uwsInp[i] = corry_val if corry_val == 'inf' else float(corry_val)

        # Create parameter arrays as expected by the original code
        Parameter_Means = np.array([[Mean_SuInp], [Mean_uwsInp]], dtype=float)
        Parameter_CoVs = np.array([[CoV_SuInp], [CoV_uwsInp]], dtype=float)
        Parameter_Dist = np.array([[Dist_SuInp], [Dist_uwsInp]], dtype=object)
        Parameter_CorrLenX = np.array([[CorrLenX_SuInp], [CorrLenX_uwsInp]], dtype=object)
        Parameter_CorrLenY = np.array([[CorrLenY_SuInp], [CorrLenY_uwsInp]], dtype=object)

    return Parameter_Means, Parameter_CoVs, Parameter_Dist, Parameter_CorrLenX, Parameter_CorrLenY

## Directories
# Get the directory where this script is located
Script_Directory = os.path.dirname(os.path.abspath(__file__))
print(f"Script_Directory: {Script_Directory}")
# Go up two levels: Codes -> 3DPLS -> Workspace_Root
# Workspace_Root = os.path.dirname(os.path.dirname(Script_Directory))  ## The main workspace folder
# ECo: only go up level once
Workspace_Root = os.path.dirname(Script_Directory)  ## The main workspace folder
print(f"Workspace_Root: {Workspace_Root}")

## Load configuration
Config_Directory = os.path.join(Workspace_Root, "03-Input")
yaml_config_path = os.path.join(Config_Directory, "input_3DPLS.yaml")
config = load_yaml_config(yaml_config_path)

print(f"Loading configuration from: {yaml_config_path}")

Main_Directory = os.path.join(Workspace_Root) #, "3DPLS")  ## The 3DPLS folder
print(f"Main_Directory: {Main_Directory}")
# Main_Directory = r"C:\\3DPLS\\git\\3DPLS"  ## The main folder
Code_Directory = Main_Directory + "\\Codes"  ## The folder including the code
Maxrix_Directory = os.path.join(Main_Directory, "Matrix")

## Get GIS data directory from YAML config
GIS_Data_Directory = os.path.join(Workspace_Root, config['directories']['gis_data_folder'].replace("./", "").replace("/", "\\"))
print(f"GIS_Data_Directory: {GIS_Data_Directory}")

## Get results directory from YAML config
Results_Directory = os.path.join(Workspace_Root, "3DPLS", config['directories']['output_folder'].replace("./", "").replace("/", "\\"))
print(f"Results_Directory: {Results_Directory}")

## Create directories if they do not exist.
if os.path.exists(Maxrix_Directory) == False:
    os.makedirs(Maxrix_Directory)
if os.path.exists(Results_Directory) == False:
    os.makedirs(Results_Directory)
if os.path.exists(Main_Directory + "\\InputData") == False:
    os.makedirs(Main_Directory + "\\InputData")

os.chdir(Main_Directory)  ## Change directory

"""
#####################################################################################
## Part - 1
## Get the data from GIS_Data_Directory (ASCII grid format files)
## Arrange the data if needed
#####################################################################################
"""

## Import the function to read the ASCII grid format files
os.chdir(Code_Directory)  ## Change directory
from Functions_3DPLS_v1_1 import ReadData, DataArrange

## Dimensions of the problem domain
## The user can define the dimensions or it can be read from the dem file.
## Manual entry
# nrows, ncols         =
# xllcorner, yllcorner =
# cellsize             =
# nel                  = nrows*ncols
## Entry from dem file (or any other file with ASCII format)
os.chdir(GIS_Data_Directory)  ## Change directory
dem_filename = config['gis_files']['dem']
with open(dem_filename) as f:  ## read information from dem file
    Temp = f.readlines()[0:7]
    ncols = int(Temp[0].split()[1])  ## Number of columns
    nrows = int(Temp[1].split()[1])  ## Number of rows
    xllcorner = int(float(Temp[2].split()[1]))  ## Corner coodinate
    yllcorner = int(float(Temp[3].split()[1]))  ## Corner coodinate
    cellsize = float(Temp[4].split()[1])  ## Cell size
    if config['gis_config']['read_nodata_from_file']:
        NoData = int(float(Temp[5].split()[1]))  ## No Data value from file
    else:
        NoData = config['gis_config']['nodata_value']  ## No Data value from config
    nel = nrows * ncols  ## Number of cells
f.close()

## Get GIS file names from YAML config
gis_files_config = config['gis_files']
DataFiles = [gis_files_config[key] for key in gis_files_config.keys()]
NumberData = ReadData(DataFiles)  ## Read files
NumberDataAndNames = []  ## Allocate. File names and data together
for i in range(np.size(DataFiles)):
    NumberDataAndNames.append([DataFiles[i]] + [NumberData[i]])

## Input data assignment using YAML configuration
for i in range(np.size(DataFiles)):
    if DataFiles[i] == gis_files_config['dem']:
        DEMInput = NumberDataAndNames[i][1]  ## Digital elevation map data
    elif DataFiles[i] == gis_files_config.get('dir', 'dir.asc'):
        DirectionInput = NumberDataAndNames[i][1]  ## Direction of steepest slope (From TopoIndex or QGIS) (if needed)
    elif DataFiles[i] == gis_files_config['rizero']:
        rizeroInput = NumberDataAndNames[i][1]  ## Steady, background infiltration
    elif DataFiles[i] == gis_files_config['slope']:
        SlopeInput = NumberDataAndNames[i][1]  ## Slope angle
    elif DataFiles[i] == gis_files_config['zones']:
        ZoneInput = NumberDataAndNames[i][1].astype(int)  ## Zones, converted to int
    elif DataFiles[i] == gis_files_config['aspect']:
        AspectInput = NumberDataAndNames[i][1]  ## Aspect (if needed)
    elif DataFiles[i] == gis_files_config['zmax']:
        ZmaxInput = NumberDataAndNames[i][1]  ## Depth to bedrock (can be obtained later)
    elif DataFiles[i] == gis_files_config.get('source', 'source.asc'):
        SourceInput = NumberDataAndNames[i][1]  ## Initiation cells, source (if needed)
    elif DataFiles[i] == gis_files_config['depthwt']:
        HwInput = NumberDataAndNames[i][1]  ## Depth to ground water table (can be obtained later)

# Import the function to arrange the data (Note: Currently the function is for the case study in Oguz et al. (2022): Kvam Lansdlides)
# Depending on the problem and needs, the function can be modified.
os.chdir(Code_Directory)
ZoneInput, SlopeInput, DirectionInput, DEMInput, AspectInput, rizeroInput, ZmaxInput, HwInput = DataArrange(
    ZoneInput, SlopeInput, DirectionInput, DEMInput, AspectInput, rizeroInput, NoData
)

## Rainfall input data from YAML configuration (m/sec).
riInp = np.array(([config['rainfall']['riInp']], [config['rainfall']['riInp_duration']]))
print(f"Rainfall input: {riInp[0][0]} m/s for {riInp[1][0]} seconds")

"""
#####################################################################################
## Part - 2
## Defining the parameters from YAML configuration
#####################################################################################
"""

## Monte Carlo number from YAML
MCnumber = config['monte_carlo']['mcnumber']
print(f"Monte Carlo number: {MCnumber}")

## Analysis type and soil parameters from YAML
AnalysisType = config['analysis']['analysis_type']  ## 'Drained'-'Undrained'
FSCalType = config['analysis']['fs_calculation_type']  ## 'Normal3D' - 'Bishop3D' - 'Janbu3D'

## Random field method from YAML
RanFieldMethod = config['analysis']['random_field_method']  ## 'CMD' - 'SCMD'
SaveMat = config['analysis']['save_mat']  ## 'YES' - 'NO'
print(f"Analysis: {AnalysisType}, FS Calculation: {FSCalType}, Random Field: {RanFieldMethod}")

## Variability of Zmax from YAML
ZmaxVar = config['zmax_parameters']['zmax_var']
if ZmaxVar == "YES":
    CoV_Zmax = config['zmax_parameters']['cov_zmax']
    MinZmax = config['zmax_parameters']['min_zmax']
else:
    CoV_Zmax = 0
    MinZmax = 0
ZmaxArg = (ZmaxVar, CoV_Zmax, MinZmax)
print(f"Zmax variability: {ZmaxVar}, CoV: {CoV_Zmax}, Min: {MinZmax}")

## Load soil parameters from YAML configuration
Parameter_Means, Parameter_CoVs, Parameter_Dist, Parameter_CorrLenX, Parameter_CorrLenY = parse_soil_parameters(config, AnalysisType)
print(f"Loaded soil parameters for {AnalysisType} analysis with {Parameter_Means.shape[1]} zones")

## Ellipsoidal parameters from YAML configuration
ellipsoid_config = config['ellipsoid']
Ella = ellipsoid_config['ella']
Ellb = ellipsoid_config['ellb']
Ellc = ellipsoid_config['ellc']
EllAlpha = ellipsoid_config['ellalpha']
Ellz = ellipsoid_config['ellz']
EllAlpha_Calc = ellipsoid_config['ellalpha_calc']
EllParam = [Ella, Ellb, Ellc, EllAlpha, Ellz, EllAlpha_Calc]
print(f"Ellipsoid parameters: a={Ella}, b={Ellb}, c={Ellc}, alpha={EllAlpha}, z={Ellz}, calc_alpha={EllAlpha_Calc}")

## Investigation zone from YAML configuration
investigation_config = config['investigation']
InZone = np.array(investigation_config['inzone'])
from Functions_3DPLS_v1_1 import InZone_Rec_to_List  ## Otherwise, lists of cells (row, column) can be also defined.

InZone = InZone_Rec_to_List(InZone)

## Time analysis from YAML configuration
TimeToAnalyse = np.array(investigation_config['time_to_analyse'])

## Minimum number of cells inside the ellipsoidal sliding surface (Sub-discretize)
## If this number is not satisfied, the code halves the cells and increase the number of cells.
## Either “numpy.kron” or "scipy.interpolate.griddata" can be used, but manual change is required in the functions.
## Default method is “numpy.kron”.
SubDisNum = investigation_config['sub_dis_num']  ## (Suggested: 100,200)

"""
#####################################################################################
## Part - 3
## Run the analysis
#####################################################################################
"""
## !!!  For reproducibility purposes, the example problems are provided.
## For the validation problems and simplified case problem, small changes are required.
## There are some small modifications to the code when the name assigned as one of the
## {'Pr1', 'Pr2','Pr3S1Dry','Pr3S2Dry','Pr3S2Wet' 'SimpCase'}
ProblemName = config['analysis']['problem_name']
## !!!

#########
#########
## Multiprocessing in both MC phase and generation of the ellipsoidal sliding surfaces with FS calculations
## There are multiple run options
## When zmax is variant, "C-MP-MP" is recommended.
## When zmax is invatiant, "S-MP-MP" is recommended.
#########
#########

## Import functions
from Functions_3DPLS_v1_1 import FSCalcEllipsoid_v1_0_SingleRrocess, FSCalcEllipsoid_v1_0_MutiProcess
from operator import itemgetter
from Functions_3DPLS_v1_1 import Ellipsoid_Generate_Main, Ellipsoid_Generate_Main_Multi, IndMC_Main, IndMC_Main_Multi

# Allocate processes for Monte Carlo simulations and calculations for ellipsoidal sliding surfaces individually
print("Total number of processors: %d" % (cpu_count()))
## Select the run option
## "C-XX-XX" is for Monte Carlo simulations conbined with generation of ellipsoidal sliding surfaces such that ellipsoids are generated for each simulations.This is suggested when zmax is variant.
## "S-XX-XX" is for separate monte carlo simulations and ellipsoidal sliding surface generation such that ellipsoids are generated first and simulations are performed afterward.This is suggested when zmax is invariant.
## "C": combined, "S": separated, "SP": singe process, "MP": multi processes, "MT": multi threads
## "C-XX-YY": XX for Monte Carlo simulations, YY for generation of ellipsoidal sliding surfaces in each simulation.
## "S-XX-YY": XX for generation of ellipsoidal sliding surfaces, YY for Monte Carlo simulations.
Multiprocessing_Option_List = ["C-SP-SP", "C-MP-SP", "C-MP-MP", "C-MP-MT", "S-SP-SP", "S-SP-MP", "S-MP-SP", "S-MP-MP"]
Multiprocessing_Option = config['multiprocessing']['multiprocessing_option']  ## Select 0-7

## Arrange the numbers of processors / threads for calculations
## For options "C-XX-XX"
TOTAL_PROCESSES_MC = config['multiprocessing']['total_processes_mc']  ## Will be utilized if either "C-MP-SP" or "C-MP-MP" run option is selected
TOTAL_PROCESSES_ELL = config['multiprocessing']['total_processes_ell']  ## Will be utilized if "C-MP-MP" run option is selected
TOTAL_THREADS_ELL = config['multiprocessing']['total_threads_ell']  ## Will be utilized if "C-MP-MT" run option is selected
## For options "S-XX-XX"
TOTAL_PROCESSES_IndMC = config['multiprocessing']['total_processes_indmc']  ## Will be utilized if either "S-SP-MP" or "S-MP-MP" run option is selected
TOTAL_PROCESSES_EllGen = config['multiprocessing']['total_processes_ellgen']  ## Will be utilized if either "S-MP-SP" or "S-MP-MP" run option is selected

# "FSCalcEllipsoid_v1_0_SingleRrocess" is normal procedure with single process unit.
# "FSCalcEllipsoid_v1_0_MutiProcess" is developed to utilize multiple processors.
# Parallelization was implemented at two level: Monte carlo simulations and generation of ellipsoidal sliding surfaces.
# Select "MCRun_v1_0_SingleProcess", "MCRun_v1_0_MultiProcess", "MCRun_v1_0_MultiThread" in "FSCalcEllipsoid_v1_0_MutiProcess" function.
if __name__ == "__main__":

    ## Time before the main calculation part of the code
    t1 = time.time()

    #####
    ## Combined Monte Carlo simulations and generation of ellipdoidal sliding surfaces.
    #####

    ## Check Multiprocessing_option and run
    if Multiprocessing_Option == "C-SP-SP":
        print("Run option: (SP)", Multiprocessing_Option)

        FSCalcEllipsoid_v1_0_SingleRrocess(
            AnalysisType,
            FSCalType,
            RanFieldMethod,
            InZone,
            SubDisNum,
            Results_Directory,
            Code_Directory,
            Maxrix_Directory,
            nrows,
            ncols,
            nel,
            cellsize,
            EllParam,
            MCnumber,
            Parameter_Means,
            Parameter_CoVs,
            Parameter_Dist,
            Parameter_CorrLenX,
            Parameter_CorrLenY,
            SaveMat,
            ZoneInput,
            SlopeInput,
            ZmaxArg,
            ZmaxInput,
            DEMInput,
            HwInput,
            rizeroInput,
            riInp,
            AspectInput,
            TimeToAnalyse,
            NoData,
            ProblemName,
        )

        ## Time after the main calculation part of the code
        t2 = time.time()
        print("Time elapsed: ", t2 - t1)

    ## Check Multiprocessing_option and run
    if Multiprocessing_Option in ["C-MP-SP", "C-MP-MP", "C-MP-MT"]:
        print("Run option: (MP)", Multiprocessing_Option)

        FSCalcEllipsoid_v1_0_MutiProcess(
            Multiprocessing_Option,
            TOTAL_PROCESSES_MC,
            TOTAL_PROCESSES_ELL,
            TOTAL_THREADS_ELL,
            AnalysisType,
            FSCalType,
            RanFieldMethod,
            InZone,
            SubDisNum,
            Results_Directory,
            Code_Directory,
            Maxrix_Directory,
            nrows,
            ncols,
            nel,
            cellsize,
            EllParam,
            MCnumber,
            Parameter_Means,
            Parameter_CoVs,
            Parameter_Dist,
            Parameter_CorrLenX,
            Parameter_CorrLenY,
            SaveMat,
            ZoneInput,
            SlopeInput,
            ZmaxArg,
            ZmaxInput,
            DEMInput,
            HwInput,
            rizeroInput,
            riInp,
            AspectInput,
            TimeToAnalyse,
            NoData,
            ProblemName,
        )
        ## Time after the main calculation part of the code
        t2 = time.time()
        print("Time elapsed: ", t2 - t1)

    #####
    ## Separated Monte Carlo simulations and generation of ellipdoidal sliding surfaces.
    #####

    ## Check Multiprocessing_option and generate sliding surfaces
    if Multiprocessing_Option in ["S-SP-SP", "S-SP-MP"]:
        print("Run option: (Sliding surfaces: SP)", Multiprocessing_Option)

        ## Singleprocessing generation of ellipsoidal sliding surfaces
        AllInf = Ellipsoid_Generate_Main(
            InZone, SubDisNum, nrows, ncols, nel, cellsize, EllParam, SlopeInput, ZmaxInput, DEMInput, AspectInput, NoData, ProblemName
        )

        ## Save sliding surfaces' information
        AllInf = AllInf[:]
        AllInf_sorted = sorted(AllInf, key=itemgetter(0))
        AllInf_sorted = np.asarray(AllInf_sorted, dtype=object)
        # from sys import getsizeof
        # round(getsizeof(AllInf_sorted) / 1024 / 1024,2) ## to get size in MB round to 2 digit
        os.chdir(Results_Directory)
        np.save("Elipsoidal_Sliding_Surfaces", AllInf_sorted)

        ## Time elapsed for generation of ellipsoidal sliding surfaces
        t2 = time.time()
        print("Time elapsed for generation of ellipsoidal sliding surfaces: ", t2 - t1)

    ## Check Multiprocessing_option and generate sliding surfaces
    if Multiprocessing_Option in ["S-MP-SP", "S-MP-MP"]:
        print("Run option: (Sliding surfaces: MP)", Multiprocessing_Option)

        ## Multiprocessing generation of ellipsoidal sliding surfaces
        AllInf = Ellipsoid_Generate_Main_Multi(
            TOTAL_PROCESSES_EllGen,
            InZone,
            SubDisNum,
            nrows,
            ncols,
            nel,
            cellsize,
            EllParam,
            SlopeInput,
            ZmaxInput,
            DEMInput,
            AspectInput,
            NoData,
            ProblemName,
        )

        ## Save sliding surfaces' information
        AllInf = AllInf[:]
        AllInf_sorted = sorted(AllInf, key=itemgetter(0))
        AllInf_sorted = np.asarray(AllInf_sorted, dtype=object)
        # from sys import getsizeof
        # round(getsizeof(AllInf_sorted) / 1024 / 1024,2) ## to get size in MB round to 2 digit
        os.chdir(Results_Directory)
        np.save("Elipsoidal_Sliding_Surfaces", AllInf_sorted)

        ## Time elapsed for generation of ellipsoidal sliding surfaces
        t2 = time.time()
        print("Time elapsed for generation of ellipsoidal sliding surfaces: ", t2 - t1)

    ## If sliding surfaces have already been generated and saved, load the information directly and commented out th above two function.
    # os.chdir(Results_Directory)
    # AllInf_sorted = np.load("Elipsoidal_Sliding_Surfaces.npy",allow_pickle=True)

    ## Check Multiprocessing_option and perfom Monte Carlo simulations
    if Multiprocessing_Option in ["S-SP-SP", "S-MP-SP"]:
        print("Run option: (MC simulations: SP)", Multiprocessing_Option)

        IndMC_Main(
            AllInf_sorted,
            AnalysisType,
            FSCalType,
            RanFieldMethod,
            InZone,
            Results_Directory,
            Maxrix_Directory,
            nrows,
            ncols,
            cellsize,
            MCnumber,
            Parameter_Means,
            Parameter_CoVs,
            Parameter_Dist,
            Parameter_CorrLenX,
            Parameter_CorrLenY,
            SaveMat,
            SlopeInput,
            ZoneInput,
            HwInput,
            rizeroInput,
            riInp,
            TimeToAnalyse,
            NoData,
            ProblemName,
        )

        ## Time elapsed for Monte Carlo simulations
        t3 = time.time()
        print("Time elapsed for Monte Carlo simulations: ", t3 - t2)

    ## Check Multiprocessing_option and perfom Monte Carlo simulations
    if Multiprocessing_Option in ["S-SP-MP", "S-MP-MP"]:
        print("Run option: (MC simulations: MP)", Multiprocessing_Option)

        IndMC_Main_Multi(
            TOTAL_PROCESSES_IndMC,
            AllInf_sorted,
            AnalysisType,
            FSCalType,
            RanFieldMethod,
            InZone,
            Results_Directory,
            Maxrix_Directory,
            nrows,
            ncols,
            cellsize,
            MCnumber,
            Parameter_Means,
            Parameter_CoVs,
            Parameter_Dist,
            Parameter_CorrLenX,
            Parameter_CorrLenY,
            SaveMat,
            SlopeInput,
            ZoneInput,
            HwInput,
            rizeroInput,
            riInp,
            TimeToAnalyse,
            NoData,
            ProblemName,
        )

        ## Time elapsed for Monte Carlo simulations
        t3 = time.time()
        print("Time elapsed for Monte Carlo simulations: ", t3 - t2)

    """
    #####################################################################################
    ## Part - 4
    ## Plot the resuts
    #####################################################################################
    """

    ## Read the results
    os.chdir(Results_Directory)
    DataFiles = os.listdir()
    DataFiles = [i for i in DataFiles if i.endswith("FS_Values.npy")]
    Result_Files = []
    for i in range(np.size(DataFiles)):
        print(DataFiles[i])
        Temp = np.load(DataFiles[i])
        Temp2 = [Temp[m].flatten() for m in range(np.shape(Temp)[0])]
        Result_Files.append(Temp2)

    ## Rearrange a list for each time instances
    Results_Time = []
    for i in range(np.shape(Result_Files[0])[0]):  ## over time
        Temp = [res[i] for res in Result_Files]
        Temp = np.asarray(Temp)
        Results_Time.append(Temp)

    # print(np.unique(Results_Time))

    # ## The plots should be drawn by the user.
    # ## All results are stored in the result folder.
    # ## Both statistical results and the results of each MC simulation can be calculated and corresponding plots can be drawn.

    # ## There are 2 example plots below.

    # ###########################
    # ## Example 1
    # ## Mean factor of safety map of the study area
    # ###########################

    # os.chdir(Results_Directory)

    ## Calculate the mean
    MeanFSData = []
    for i in range(np.shape(Results_Time)[0]):
        Temp = np.mean(Results_Time[i], axis=0)  ## Take the average over Monte Carlo simulations
        Temp = np.reshape(Temp, (nrows, ncols))
        MeanFSData.append(Temp)

    ## Select a time instance
    MeanFSData = MeanFSData[0]
    MeanFSData[MeanFSData == 0] = np.nan
    print(np.unique(MeanFSData[~np.isnan(MeanFSData)]))

    # Check if display is available
    backend = matplotlib.get_backend()
    can_display = backend != 'Agg'
    print(f"Matplotlib backend: {backend}")
    if not can_display:
        print("Note: Plots will be saved to files but cannot be displayed in terminal.")

    # ## Draw mean FS map

    # ## Color map can be modified and newcmp can be used.
    # ## import lib for drawings
    # # from matplotlib import cm
    # # from matplotlib.colors import ListedColormap  #, LinearSegmentedColormap
    # # viridis = cm.get_cmap('viridis', 256)
    # # newcolors = viridis(np.linspace(0, 1, 256))
    # # RedColor1 = np.array([255/256, 0, 0, 1])
    # # RedColor2 = np.array([241/256, 169/256, 160/256, 1])
    # # newcolors[int(256/10):int(256/5), :] = RedColor2
    # # newcolors[:int(256/10), :] = RedColor1
    # # newcmp = ListedColormap(newcolors)

    font = {'family': 'Times New Roman', 'size': '14'}  #        'weight' : 'bold',
    # font = {'family' : 'Times New Roman'}
    plt.rc('font', **font)

    ## Min and max values can be defiend
    # minFS = 0
    # maxFS = 5

    ## Plot figure
    fig, (ax1, cax) = plt.subplots(ncols=2, figsize=(4, 6), gridspec_kw={"width_ratios": [1, 0.1]})
    fig.subplots_adjust(wspace=0.2)
    im = ax1.imshow(MeanFSData)
    ## Axes label
    # ax1.set_title('')
    ax1.set_ylabel("i")
    ax1.set_xlabel("j")

    ## Color bar
    # fig.colorbar(im, cax=cax, ticks=np.array((1.0,1.1,1.2,1.4,1.6,1.8,2.0)))
    fig.colorbar(im, cax=cax)

    # Save the figure to the results folder
    fig_path = os.path.join(Results_Directory, "MeanFSMap.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"Mean FS map saved to: {fig_path}")
    plt.close(fig)  # Close the figure to free memory

    ###########################
    ###########################

    ###########################
    ## Example 2
    ## Probability of failure map of the study area
    ###########################

    os.chdir(Results_Directory)

    ## Calculate the mean
    PfData = []
    for i in range(np.shape(Results_Time)[0]):
        Temp = Results_Time[i]        ## FS data at one time instance
        Temp_MC = np.shape(Temp)[0]   ## MC number
        Index_zero = np.where(Temp[0] == 0)

        Temp = np.where(Temp<1.0,1,0) ## FS<1.0
        Temp = np.sum(Temp, axis=0)   ## Number of failure
        Temp = Temp / Temp_MC * 100  ## Probability of failure calculation

        Temp[Index_zero] = np.nan
        Temp = np.reshape(Temp, (nrows,ncols))
        PfData.append(Temp)

    ## Select a time instance
    PfData = PfData[0]

    font = {'family' : 'Times New Roman',
            'size'   : '14'}   #        'weight' : 'bold',
    # font = {'family' : 'Times New Roman'}
    plt.rc('font', **font)

    ## Min and max values can be defiend
    minPf = 0
    maxPf = 40

    ## Plot figure
    fig, (ax1, cax) = plt.subplots(ncols=2,figsize=(4,6), gridspec_kw={"width_ratios":[1, 0.1]})

    fig.subplots_adjust(wspace=0.2)
    im  = ax1.imshow(PfData,vmin=minPf, vmax=maxPf)
    ## Axes label
    # ax1.set_title('')
    ax1.set_ylabel("i")
    ax1.set_xlabel("j")

    ## Color bar
    # fig.colorbar(im, cax=cax, ticks=np.array((1.0,1.1,1.2,1.4,1.6,1.8,2.0)))
    # fig.colorbar(im, cax=cax)
    fig.colorbar(im, cax=cax, label='$P_{f}$ (L) (%)')

    # Save the figure to the results folder
    fig_path = os.path.join(Results_Directory, "PfMap.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"Probability of failure map saved to: {fig_path}")
    plt.close(fig)  # Close the figure to free memory


    ###########################
    ###########################
