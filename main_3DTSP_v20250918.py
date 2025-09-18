#!/usr/bin/python3

'''
Author:     Enok Cheon 
Date:       Aug 13, 2025
Purpose:    Physically-based Rainfall-Induced Landslide Susceptibility through 3D Translational Slope Probabilistic (3DTSP) Model
Language:   Python3
License:    

Copyright <2025> <Enok Cheon>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

###############
## version description
###############
20250918
- fixed incorrectly placing the initial groundwater table below the bedrock surface for "thickness above bedrock" groundwater model option

20250813
- add probabilistic analysis to soil thickness properties; hence, everything except the DEM are subjected to probabilistic analysis
- fixed issue of when delta_theta = abs(theta_s - theta_initial) = 0 and psi_r = 0. This occurs when the initial suction is zero (i.e. no matric suction means all wetting front situation). therefore, assign a non-zero delta_theta (=1e-6) and psi_r (=1e-4) values based on the selected theta_dp (=6) and press_dp (=4) decimal points.

20250516
- more options for generating soil thickness and initial groundwater table
- generate rainfall history data through nearest neighbor interpolation from rainfall gauge locations
- instead of reading and exporting dip_directions, use aspect instead. Where aspect is Northing coordination based (0 ~ 360, -1 when flat or vertical)
	used to eventually match with the 3DPLS
- add probabilistic analysis to material properties 
- convert DEM to have higher resolution (e.g. 1x1m DEM changed to be 5x5m or 10x10m DEM)
- option to restart simulation (reuse previously used data as long as the same input provided for "filename", "input_folder_path", "output_folder_path")

20250130
- separate the slip surface generating and FS computing functions
- create a function that uses multiprocessing to generate all 3DTS slip surfaces 

20250124
- modify critical_depth_group_3D_FS_HungrJanbu_MP_v7_01 function to incorporate soil cell with 3-sides exposed to exterior

20241029
- root strength computation method modified

20241010
- The input files can be in JSON or YAML format
- input folder and output folder can be distinguished

20240917
- Side resistance also accounts the cohesive strength (Mohr-Coulomb)

20240902
- Input accepted from JSON input files
- Accepts number or GIS (csv, grd*, asc**, las***)
	*grd = Surfer Grid 6 text file format
	**asc = ArcGIS ascii file format
	***las = LiDAR point cloud file format
- Can model soil depth based on empirical relationship between soil thickness and slope angle in Norway [Holm (2011); Edvarson (2013)]
- Generalized Green-Ampt rainfall infiltration method (can accept non-uniform rains)
- Infinite slope stability analysis with unsaturated strength
- 3D limit equilibrium simplified Janbu method with unsaturated strength, side frictional resistance, and root resistance
- Export data into GIS files (csv, grd, asc)
	* with asc file, noData can be accounted and treated within the code
- Plot plotly interactive plots of the results
'''

import sys
import os

if __name__ == '__main__':
	# Parse the command line argument for the input file name(s):
	try:
		input_JSON_YAML_file_name = sys.argv[1]  # sys.argv[1:]
	except:
		print("\nUsage:")
		print("python3(.exe) main_3DTSP_v20250918.py "
			  + "<filepath> [<filepath> ...]\n")
		sys.exit(0)
	
	if len(input_JSON_YAML_file_name) == 0:
		print("\nUsage:")
		print("python3(.exe) main_3DTSP_v20250918.py "
			  + "<filepath> [<filepath> ...]\n")
		sys.exit(0)

	# input_JSON_YAML_file_name = directly assign input file JSON or YAML for debugging
	# input_JSON_YAML_file_name = './test_random_field_3DPLS/3DTSP_v20250516_input_test.yaml'
	# input_JSON_YAML_file_name = './KvamCaseStudy - Input_Parameters - Emir - 3DPLS/Kvam2011_EMIR_3DTS_2to5_Side_Root_INPUT_v20250130_v200.yaml'
	# input_JSON_YAML_file_name = './Kvam2011_EMIR_3DTS_N2_Side_Root_v20250130_v300.yaml'
	# input_JSON_YAML_file_name = './Project_test_2_3DTSP_input_test.yaml'

	# running in linux with nohup and niceness
	# nohup nice -8 python3 main_3DTS_v20250130.py Kvam2011_EMIR_3DTS_2to5_Side_Root_INPUT_v20250130_v201.yaml > v201_out.txt 2>&1 &
	# nohup nice -3 sh run_N1_N12.sh 2>&1 &
	
	print(
'''
#########################################################################
#                                                                       #
#  3D Translational Slope Probabilistic (3DTSP) Model  					#
#  by Dr. Enok Cheon                                                    #
#                                                                       #
#########################################################################

Author:     Enok Cheon 
Date:       Aug 13, 2025
Purpose:    Physically-based Rainfall-Induced Landslide Susceptibility through 3D Translational Slope Probabilistic (3DTSP) Model
Language:   Python3
License:    

Copyright <2025> <Enok Cheon>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

################################################################################

The programming is importing python libraries for analysis ... 

'''
	)

#################################################################################################################
### interpolation_lin_OK_UK
#################################################################################################################
import numpy as np
import decimal
import warnings
import json
import yaml
from copy import deepcopy
from scipy.optimize import fixed_point

## import geoFileConvert
import csv
import laspy
from scipy.stats import mode

# root strength
from scipy.special import gamma as gamma_func 

## interpolation functions
from scipy.interpolate import griddata
from scipy.interpolate import interp1d
from pykrige.ok import OrdinaryKriging
from pykrige.uk import UniversalKriging
from pykrige.ok3d import OrdinaryKriging3D
from pykrige.uk3d import UniversalKriging3D

# dip and aspect
from sklearn.linear_model import LinearRegression

## multiprocessing
import multiprocessing as mp

## UCA
# from scipy.stats import rankdata
from scipy.sparse import csr_matrix, save_npz, load_npz
from scipy.sparse.csgraph import dijkstra
import itertools

## probabilistic analysis
from scipy.linalg import cholesky

## plotly plotting
# import kaleido
# import plotly.io as pio
from plotly.offline import plot
import plotly.graph_objs as go

np.seterr(all='warn', under='ignore')
warnings.filterwarnings('error')

#################################################################################################################
### interpolation_lin_OK_UK
#################################################################################################################
# check if string is float
def is_float(x):
	"""Check if a string can be converted to a float.

	Args:
		x (str): Input string to check.

	Returns:
		bool: True if the string can be converted to a float, False otherwise.
	"""
	try:
		float(x)
		return True
	except ValueError:
		return False
	
# check if string is integer
def is_int(x):
	"""Check if a string can be converted to an integer.

	Args:
		x (str): Input string to check.

	Returns:
		bool: True if the string can be converted to an integer, False otherwise.
	"""
	try:
		int(x)
		return True
	except ValueError:
		return False
	
# import csv file and convert any number (int or float) into number types (int or float)
def csv2list(fileName, starting_row=0):
	"""Convert a CSV file into a numeric nested list.

	Args:
		fileName (str): Path to the CSV file.
		starting_row (int, optional): Row number to start extracting data. Defaults to 0.

	Returns:
		list: Data from the CSV file in list format, with numeric values converted to int or float.
	"""
	with open(fileName, 'r') as f:
		reader = csv.reader(f)
		csvListTxt = list(reader)

	csvList= []
	for idR in range(starting_row, len(csvListTxt)):	
		csvListTxt[idR] = [x for x in csvListTxt[idR] if x != '']
		tempList=[int(i) if is_int(i) else float(i) if is_float(i) else i for i in csvListTxt[idR]]    # only include numbers, skip non-numeric values
		csvList.append(tempList)

	return csvList

def txt2list(fileName, starting_row=0):
	"""Convert a TXT file (tab-delimited) into a numeric nested list.

	Args:
		fileName (str): Path to the TXT file.
		starting_row (int, optional): Row number to start extracting data. Defaults to 0.

	Returns:
		list: Data from the TXT file in list format, with numeric values converted to int or float.
	"""
	with open(fileName, 'r') as myfile:
		data=myfile.read().split('\n')

	txtListNum = []
	for idR in range(starting_row, len(data)):
		tempList1 = data[idR].split('\t') 
		tempList2=[int(i) if is_int(i) else float(i) if is_float(i) else i for i in tempList1]  
		txtListNum.append(tempList2)

	return txtListNum

def exportList2CSV(csv_file,data_list,csv_columns=None):
	"""export list to csv (comma deliminated) file

	Args:
		csv_file (str): filename of csv that will be generated
		data_list (list): data
		csv_columns (str, optional): add column titles to csv. Defaults to None.

	Returns:
		None: _description_
	"""
	with open(csv_file, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile, delimiter=',')
		if csv_columns != None:
			writer.writerow(csv_columns)
		for data in data_list:
			writer.writerow(data)   
	csvfile.close()
	return None

def interpKrig(DEMname, interpType, xRange=None, yRange=None, zRange=None, gridMethodisN=True, Ngrid=50, Lgrid=1, stdMax=30, export=False, outputSingle=True, exportName=None, dp=3):
	"""perform linear interpolation or kriging interpolation (ordinary and universal) for 2D, 3D or 4D

	Args:
		DEMname (list): name of csv file
		interpType (str): type of interpolation (check the Notes for more details)
		xRange (list, optional): range of x grid coordinates as list [min, max]. Defaults to None.
		yRange (list, optional): range of y grid coordinates as list [min, max]. Defaults to None.
		zRange (list, optional): range of z grid coordinates as list [min, max]. Defaults to None.
		gridMethodisN (bool, optional): method to create grid: True = number of grids, or False = length between grids. Defaults to True.
		Ngrid (int, optional): number of grids between limits. Defaults to 50.
		Lgrid (int, optional): length between grids. Defaults to 1.
		stdMax (int, optional): max acceptable error/standard deviation. Defaults to 30.
		export (bool, optional): export the interpolated data and save. Defaults to False.
		outputSingle (bool, optional): if True, export only the interpolated data; if False, export interpolated data and metadatas. Defaults to True.
		exportName (str, optional): export csv file name. If None, export name is 'interpolated_'+DEMname. Defaults to None.
		dp (int, optional): decimal point. Defaults to 3.

	Returns:
		outFile: interpolated data
		*metadata: metadatas for interpolated DEM
			for 2D: gridXCoords, interpolY, stdY
			for 3D: gridXCoords, gridYCoords, interpolZ, stdZ
			for 4D: gridXCoords, gridYCoords, gridZCoords, interpolW, stdW
	
	Notes: 
		Interpolation methods used: (for 1D and 2D)
		1. scipy - linear interpolation (short form = lin)
		2. pykrige - kriging ordinary   (short form = OK)
		3. pykrige - kriging universal  (short form = UK)

		Dimensions available:
		1. 2D - given: x 		calculate: y
		2. 3D - given: x, y 	calculate: z
		3. 4D - given: x, y, z	calculate: w  (kriging only)

		Mathematical model for semi-veriograms (kriging):
		1. linear						
		2. power			
		3. gaussian			
		4. spherical			
		5. exponential		
		6. circular (under-construction... no yet finished)		

		How to write interpolType
		format: [dimension + space + short form interpolation type (+ space + semivariogram model)] in string format
		e.g.) '2 lin' = 2D linear interpolation 
			'3 UK gaussian' = 3D ordinary kriging interpolation with linear semivariogram model
			'4 OK linear' = 4D ordinary kriging interpolation with linear semivariogram model

		Note on xRange, yRange, zRange
			The range of values of x, y, and z for generating square grids can be pre-assigned 
			or used with the max and min values of each x, y, and z

		Note on grid generation
			The grids are squares. Therefore, the grids are generated in the following method:
				
				if Ngrid value is used
					1. find the min and max values of each given points range (x,y,z)
					2. find the spacing between grids for each orthogonal direction given each directions are divided with number N
					3. specified length = minimum value among spacing of each orthogonal direction
					4. specified steps = roundup((max value - min value) / specified length)

				elif Lgrid value is used
					1. find the min and max values of each given points range (x,y,z)
					2. specified length = user defined
					3. specified steps = roundup((max value - min value) / specified length)
				
				# grid generated in the following method
				1. subdivide the values of limits (max and min) of each orthogonal direction into specified steps
	"""

	## set up libraries
	# import modules
	# import numpy as np
	#from numpy import linspace,
	#import making_list_with_floats as makeList  # functions from making_list_with_floats.py 
	# from making_list_with_floats import csv2list, exportList2CSV

	# determine interpType
	# create a list of interpType info [dimensions, interpolation kind, semi-variagram model (OK and UK)]
	typeList = interpType.split(' ')		
	typeList[0] = int(typeList[0])
	if len(typeList) == 2 and typeList[1] in ['OK','UK']:
		typeList.append('linear')
	elif typeList[1] == 'lin':
		pass
	else:
		print('Error: check the interpType input')
		return None

	# sort information of given input file - needs to be in a matrix format
	#print(DEMname)
	'''
	if isinstance(DEMname, str): 
		inputFile = csv2list(DEMname)
	else:
		try:
			DEMname
		except NameError:
			inputFile = DEMname
	'''
	inputFile = DEMname
	inputCol = len(inputFile[0])

	# import csv file of given points and assign to each 
	if inputCol == 2:
		inputX, inputY = np.array(inputFile).T
		#inputZ = np.empty((len(inputX),))
		#inputW = np.empty((len(inputX),))
	elif inputCol == 3:
		inputX, inputY, inputZ = np.array(inputFile).T 
		if typeList[1] == 'lin': 
			inputXY = np.array(inputFile)[:,[0,1]]
	elif inputCol == 4:
		inputX, inputY, inputZ, inputW = np.array(inputFile).T
	else:
		print('Error: check your input file')
		return None

	# sort information depending on the dimension specified
	'''2D'''
	if typeList[0] == 2: 

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN == True:
			# find the minimum spacing
			spacing = abs((maxX-minX)/Ngrid)
			xStepN = round(abs(maxX-minX)/spacing)

		elif gridMethodisN == False:
			xStepN = round(abs(maxX-minX)/Lgrid)

		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)

		# interpolation process
		if typeList[1] == 'lin':
			# import relevent python modules for provided interpolation type and method chosen
			# from scipy.interpolate import interp1d

			# perform interpolation
			tempInterpolated = interp1d(inputX, inputY, bounds_error=False)
			interpolY = tempInterpolated(gridXCoords)
			stdY = None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok import OrdinaryKriging

			# perform interpolation
			tempInterpolated = OrdinaryKriging(inputX, np.zeros(inputX.shape), inputY, variogram_model=typeList[2])
			interpolY, stdY = tempInterpolated.execute('grid', gridXCoords, np.array([0.]))
			interpolY, stdY = interpolY[0], stdY[0]

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk import UniversalKriging

			# perform interpolation
			tempInterpolated = UniversalKriging(inputX, np.zeros(inputX.shape), inputY, variogram_model=typeList[2])
			interpolY, stdY = tempInterpolated.execute('grid', gridXCoords, np.array([0.]))
			interpolY, stdY = interpolY[0], stdY[0]

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:
			for loopYPred in range(len(interpolY)):
				if stdY[loopYPred] > stdMax:
					interpolY[loopYPred] = np.nan			

		# combine into single output file
		if typeList[1] in ['OK', 'UK']:
			outFile = (np.vstack((gridXCoords, interpolY, stdY)).T).tolist()
		else:
			outFile = (np.vstack((gridXCoords, interpolY, np.nan*np.ones((len(gridXCoords),)))).T).tolist()
		
		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)

	'''3D'''
	if typeList[0] == 3:

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]
		
		# for Y
		if yRange == None:
			minY = min(inputY)
			maxY = max(inputY)
		else:
			minY = yRange[0]
			maxY = yRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN:
			# find the minimum spacing
			spacing = min(abs((maxX-minX)/Ngrid), abs((maxY-minY)/Ngrid))
			xStepN = round(abs((maxX-minX)/spacing))
			yStepN = round(abs((maxY-minY)/spacing))
		else:
			xStepN = round(abs((maxX-minX)/Lgrid))
			yStepN = round(abs((maxY-minY)/Lgrid))
			
		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)
		gridYCoords = np.linspace(minY, maxY, yStepN, dtype=float)

		# interpolation process
		if typeList[1] == 'lin':
			# import relevent python modules for provided interpolation type and method chosen
			# from scipy.interpolate import griddata

			meshgridX, meshgridY = np.meshgrid(gridXCoords, gridYCoords)

			# perform interpolation
			interpolZ = griddata(inputXY, inputZ, (meshgridX, meshgridY), method='linear')

			#tempInterpolated = interp2d(inputX, inputY, inputZ, bounds_error=False)
			#interpolZ = tempInterpolated(gridXCoords, gridYCoords)
			
			stdZ = None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok import OrdinaryKriging

			# perform interpolation
			tempInterpolated = OrdinaryKriging(inputX, inputY, inputZ, variogram_model=typeList[2])
			interpolZ, stdZ = tempInterpolated.execute('grid', gridXCoords, gridYCoords)

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk import UniversalKriging

			# perform interpolation
			tempInterpolated = UniversalKriging(inputX, inputY, inputZ, variogram_model=typeList[2])
			interpolZ, stdZ = tempInterpolated.execute('grid', gridXCoords, gridYCoords)

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:
			for loopZPred1 in range(len(interpolZ)):
				for loopZPred2 in range(len(interpolZ[0])):
					if stdZ[loopZPred1][loopZPred2] > stdMax:
						interpolZ[loopZPred1][loopZPred2] = np.nan		

		# combine all coordinates into single output file format
		outFile = []
		for loop31 in range(len(interpolZ)):
			for loop32 in range(len(interpolZ[0])):
				# combine into single output file
				if typeList[1] in ['OK', 'UK']:
					outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], stdZ[loop31][loop32]])
				else:
					outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], np.nan])					
		
		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)
		
	'''4D'''
	if typeList[0] == 4:

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]
		
		# for Y
		if yRange == None:
			minY = min(inputY)
			maxY = max(inputY)
		else:
			minY = yRange[0]
			maxY = yRange[1]
		
		# for Z
		if zRange == None:
			minZ = min(inputZ)
			maxZ = max(inputZ)
		else:
			minZ = zRange[0]
			maxZ = zRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN == True:
			# find the minimum spacing
			spacing = min([abs((maxX-minX)/Ngrid), abs((maxY-minY)/Ngrid), abs((maxZ-minZ)/Ngrid)])
			xStepN = round(abs((maxX-minX)/spacing))
			yStepN = round(abs((maxY-minY)/spacing))
			zStepN = round(abs((maxZ-minZ)/spacing))
		elif gridMethodisN == False:
			xStepN = round(abs((maxX-minX)/Lgrid))
			yStepN = round(abs((maxY-minY)/Lgrid))
			zStepN = round(abs((maxZ-minZ)/Lgrid))

		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)
		gridYCoords = np.linspace(minY, maxY, yStepN, dtype=float)
		gridZCoords = np.linspace(minZ, maxZ, zStepN, dtype=float)	

		# interpolation process
		if typeList[1] == 'lin':
			print('sorry - not completed yet')
			return None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok3d import OrdinaryKriging3D

			# perform interpolation
			tempInterpolated = OrdinaryKriging3D(inputX, inputY, inputZ, inputW, variogram_model=typeList[2])
			interpolW, stdW = tempInterpolated.execute('grid', gridXCoords, gridYCoords, gridZCoords)

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk3d import UniversalKriging3D

			# perform interpolation
			tempInterpolated = UniversalKriging3D(inputX, inputY, inputZ, inputW, variogram_model=typeList[2])
			interpolW, stdW = tempInterpolated.execute('grid', gridXCoords, gridYCoords, gridZCoords)

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:
			for loopWPred1 in range(len(interpolW)):
				for loopWPred2 in range(len(interpolW[0])):
					for loopWPred3 in range(len(interpolW[0][0])):
						if stdW[loopWPred1][loopWPred2][loopWPred3] > stdMax:
							interpolW[loopWPred1][loopWPred2][loopWPred3] = np.nan		

		# combine all coordinates into single output file format
		outFile = []
		for loop31 in range(len(interpolW)):
			for loop32 in range(len(interpolW[0])):
				for loop33 in range(len(interpolW[0][0])):
					# combine into single output file
					if typeList[1] in ['OK', 'UK']:
						outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], stdW[loop31][loop32][loop33]])
					else:
						outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], np.nan])						
		
		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)

	
	'''output files'''
	if outputSingle == False:
		if typeList[0] == 2:
			return outFile, gridXCoords, interpolY, stdY
		elif typeList[0] == 3:
			return outFile, gridXCoords, gridYCoords, interpolZ, stdZ
		elif typeList[0] == 4:
			return outFile, gridXCoords, gridYCoords, gridZCoords, interpolW, stdW
	else:
		return outFile

def interpKrig_v2_0(DEMname, interpType, xRange=None, yRange=None, zRange=None, gridMethodisN=True, Ngrid=50, Lgrid=1, stdMax=30, export=False, outputSingle=True, exportName=None, dp=3):
	"""perform linear interpolation or kriging interpolation (ordinary and universal) for 2D, 3D or 4D

	Args:
		DEMname (list): name of csv file
		interpType (str): type of interpolation (check the Notes for more details)
		xRange (list, optional): range of x grid coordinates as list [min, max]. Defaults to None.
		yRange (list, optional): range of y grid coordinates as list [min, max]. Defaults to None.
		zRange (list, optional): range of z grid coordinates as list [min, max]. Defaults to None.
		gridMethodisN (bool, optional): method to create grid: True = number of grids, or False = length between grids. Defaults to True.
		Ngrid (int, optional): number of grids between limits. Defaults to 50.
		Lgrid (int, optional): length between grids. Defaults to 1.
		stdMax (int, optional): max acceptable error/standard deviation. Defaults to 30.
		export (bool, optional): export the interpolated data and save. Defaults to False.
		outputSingle (bool, optional): if True, export only the interpolated data; if False, export interpolated data and metadatas. Defaults to True.
		exportName (str, optional): export csv file name. If None, export name is 'interpolated_'+DEMname. Defaults to None.
		dp (int, optional): decimal point. Defaults to 3.

	Assumed: 
		cutVal (number) value to assign to interpolated locations exceeding stdMax. Defaults to np.nan

	Returns:
		outFile: interpolated data
		*metadata: metadatas for interpolated DEM
			for 2D: gridXCoords, interpolY, stdY
			for 3D: gridXCoords, gridYCoords, interpolZ, stdZ
			for 4D: gridXCoords, gridYCoords, gridZCoords, interpolW, stdW
	
	Notes:
		Interpolation methods used: (for 1D and 2D)
		1. scipy - linear interpolation (short form = lin)
		2. pykrige - kriging ordinary   (short form = OK)
		3. pykrige - kriging universal  (short form = UK)

		Dimensions available:
		1. 2D - given: x 		calculate: y
		2. 3D - given: x, y 	calculate: z
		3. 4D - given: x, y, z	calculate: w  (kriging only)

		Mathematical model for semi-veriograms (kriging):
		1. linear						
		2. power			
		3. gaussian			
		4. spherical			
		5. exponential		
		6. circular (under-construction... no yet finished)		

		How to write interpolType
		format: [dimension + space + short form interpolation type (+ space + semivariogram model)] in string format
		e.g.) '2 lin' = 2D linear interpolation 
			'3 UK gaussian' = 3D ordinary kriging interpolation with linear semivariogram model
			'4 OK linear' = 4D ordinary kriging interpolation with linear semivariogram model

		Note on xRange, yRange, zRange
			The range of values of x, y, and z for generating square grids can be pre-assigned 
			or used with the max and min values of each x, y, and z

		Note on grid generation
			The grids are squares. Therefore, the grids are generated in the following method:
				
				if Ngrid value is used
					1. find the min and max values of each given points range (x,y,z)
					2. find the spacing between grids for each orthogonal direction given each directions are divided with number N
					3. specified length = minimum value among spacing of each orthogonal direction
					4. specified steps = roundup((max value - min value) / specified length)

				elif Lgrid value is used
					1. find the min and max values of each given points range (x,y,z)
					2. specified length = user defined
					3. specified steps = roundup((max value - min value) / specified length)
				
				# grid generated in the following method
				1. subdivide the values of limits (max and min) of each orthogonal direction into specified steps
	"""

	''' set up '''
	# import modules
	# import numpy as np
	#from numpy import linspace,
	#import making_list_with_floats as makeList  # functions from making_list_with_floats.py 
	# from making_list_with_floats import csv2list, exportList2CSV

	# determine interpType
	# create a list of interpType info [dimensions, interpolation kind, semi-variagram model (OK and UK)]
	typeList = interpType.split(' ')		
	typeList[0] = int(typeList[0])
	if len(typeList) == 2 and typeList[1] in ['OK','UK']:
		typeList.append('linear')
	elif typeList[1] == 'lin':
		pass
	else:
		print('Error: check the interpType input')
		return None

	# sort information of given input file - needs to be in a matrix format
	#print(DEMname)
	'''
	if isinstance(DEMname, str): 
		inputFile = csv2list(DEMname)
	else:
		try:
			DEMname
		except NameError:
			inputFile = DEMname
	'''
	inputFile = DEMname
	inputCol = len(inputFile[0])

	# import csv file of given points and assign to each 
	if inputCol == 2:
		inputX, inputY = np.array(inputFile).T
		#inputZ = np.empty((len(inputX),))
		#inputW = np.empty((len(inputX),))
	elif inputCol == 3:
		inputX, inputY, inputZ = np.array(inputFile).T 
		if typeList[1] == 'lin': 
			inputXY = np.array(inputFile)[:,[0,1]]
	elif inputCol == 4:
		inputX, inputY, inputZ, inputW = np.array(inputFile).T
	else:
		print('Error: check your input file')
		return None

	# sort information depending on the dimension specified
	'''2D'''
	if typeList[0] == 2: 

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN == True:
			# find the minimum spacing
			spacing = abs((maxX-minX)/Ngrid)
			xStepN = round(abs(maxX-minX)/spacing)

		elif gridMethodisN == False:
			xStepN = round(abs(maxX-minX)/Lgrid)

		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)

		# interpolation process
		if typeList[1] == 'lin':
			# import relevent python modules for provided interpolation type and method chosen
			# from scipy.interpolate import interp1d

			# perform interpolation
			tempInterpolated = interp1d(inputX, inputY, bounds_error=False)
			interpolY = tempInterpolated(gridXCoords)
			stdY = None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok import OrdinaryKriging

			# perform interpolation
			tempInterpolated = OrdinaryKriging(inputX, np.zeros(inputX.shape), inputY, variogram_model=typeList[2])
			interpolY, stdY = tempInterpolated.execute('grid', gridXCoords, np.array([0.]))
			interpolY, stdY = interpolY[0], stdY[0]

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk import UniversalKriging

			# perform interpolation
			tempInterpolated = UniversalKriging(inputX, np.zeros(inputX.shape), inputY, variogram_model=typeList[2])
			interpolY, stdY = tempInterpolated.execute('grid', gridXCoords, np.array([0.]))
			interpolY, stdY = interpolY[0], stdY[0]

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:

			interpolY = np.where(stdY > stdMax, np.nan, interpolY)

			# for loopYPred in range(len(interpolY)):
			# 	if stdY[loopYPred] > stdMax:
			# 		interpolY[loopYPred] = np.nan			

		# combine into single output file
		if typeList[1] in ['OK', 'UK']:
			outFile = (np.vstack((gridXCoords, interpolY, stdY)).T).tolist()
		else:
			outFile = (np.vstack((gridXCoords, interpolY, np.nan*np.ones((len(gridXCoords),)))).T).tolist()
		
		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)

	'''3D'''
	if typeList[0] == 3:

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]
		
		# for Y
		if yRange == None:
			minY = min(inputY)
			maxY = max(inputY)
		else:
			minY = yRange[0]
			maxY = yRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN:
			# find the minimum spacing
			spacing = min(abs((maxX-minX)/Ngrid), abs((maxY-minY)/Ngrid))
			xStepN = round(abs((maxX-minX)/spacing))
			yStepN = round(abs((maxY-minY)/spacing))
		else:
			xStepN = round(abs((maxX-minX)/Lgrid))
			yStepN = round(abs((maxY-minY)/Lgrid))
			
		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)
		gridYCoords = np.linspace(minY, maxY, yStepN, dtype=float)

		# interpolation process
		if typeList[1] == 'lin':
			# import relevent python modules for provided interpolation type and method chosen
			# from scipy.interpolate import griddata

			meshgridX, meshgridY = np.meshgrid(gridXCoords, gridYCoords)

			# perform interpolation
			interpolZ = griddata(inputXY, inputZ, (meshgridX, meshgridY), method='linear')

			#tempInterpolated = interp2d(inputX, inputY, inputZ, bounds_error=False)
			#interpolZ = tempInterpolated(gridXCoords, gridYCoords)
			
			stdZ = None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok import OrdinaryKriging

			# perform interpolation
			tempInterpolated = OrdinaryKriging(inputX, inputY, inputZ, variogram_model=typeList[2])
			interpolZ, stdZ = tempInterpolated.execute('grid', gridXCoords, gridYCoords)

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk import UniversalKriging

			# perform interpolation
			tempInterpolated = UniversalKriging(inputX, inputY, inputZ, variogram_model=typeList[2])
			interpolZ, stdZ = tempInterpolated.execute('grid', gridXCoords, gridYCoords)

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:

			interpolZ = np.where(stdZ > stdMax, np.nan, interpolZ)

			# for loopZPred1 in range(len(interpolZ)):
			# 	for loopZPred2 in range(len(interpolZ[0])):
			# 		if stdZ[loopZPred1][loopZPred2] > stdMax:
			# 			interpolZ[loopZPred1][loopZPred2] = np.nan		

		# combine all coordinates into single output file format
		# outFile = []
		# for loop31 in range(len(interpolZ)):
		# 	for loop32 in range(len(interpolZ[0])):
		# 		# combine into single output file
		# 		if typeList[1] in ['OK', 'UK']:
		# 			outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], stdZ[loop31][loop32]])
		# 		else:
		# 			outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], np.nan])					

		## itertools version
		outFile = []
		for loop31, loop32 in itertools.product(range(len(interpolZ)), range(len(interpolZ[0]))):
			# combine into single output file
			if typeList[1] in ['OK', 'UK']:
				outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], stdZ[loop31][loop32]])
			else:
				outFile.append([gridXCoords[loop32], gridYCoords[loop31], interpolZ[loop31][loop32], np.nan])	

		## taichi version		
		# outFile_taichi = ti.field(dtype=ti.f32, shape=(int(np.product(interpolZ.shape)), 4))

		# interpolZ_taichi = ti.field(dtype=ti.f32, shape=interpolZ.shape)
		# interpolZ_taichi.from_numpy(interpolZ)

		# gridXCoords_taichi = ti.field(dtype=ti.f32, shape=len(gridXCoords))
		# gridYCoords_taichi = ti.field(dtype=ti.f32, shape=len(gridYCoords))
		# gridXCoords_taichi.from_numpy(gridXCoords)
		# gridYCoords_taichi.from_numpy(gridYCoords) 

		# if typeList[1] in ['OK', 'UK']: 
		# 	stdZ_taichi = ti.field(dtype=ti.f32, shape=stdZ.shape)
		# 	stdZ_taichi.from_numpy(stdZ) 

		# @ti.kernel
		# def assign_3d_data():
		# 	for loopY, loopX in ti.ndrange(interpolZ.shape):

		# 		table_row_idx = loopY + loopX*len(gridYCoords)

		# 		outFile_taichi[table_row_idx,0] = gridXCoords_taichi[loopX]
		# 		outFile_taichi[table_row_idx,1] = gridYCoords_taichi[loopY]
		# 		outFile_taichi[table_row_idx,2] = interpolZ_taichi[loopY, loopX]

		# 		if typeList[1] in ['OK', 'UK']:
		# 			outFile_taichi[table_row_idx,3] = stdZ_taichi[loopY, loopX] 
		# 		else: 
		# 			outFile_taichi[table_row_idx,3] = ti.log(ti.Vector([-1]))  # nan

		# assign_3d_data()

		# outFile = outFile_taichi.to_numpy()
		# outFile = outFile.tolist()

		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)
		
	'''4D'''
	if typeList[0] == 4:

		# check if user provided given range
		# for X
		if xRange == None:
			minX = min(inputX)
			maxX = max(inputX)
		else:
			minX = xRange[0]
			maxX = xRange[1]
		
		# for Y
		if yRange == None:
			minY = min(inputY)
			maxY = max(inputY)
		else:
			minY = yRange[0]
			maxY = yRange[1]
		
		# for Z
		if zRange == None:
			minZ = min(inputZ)
			maxZ = max(inputZ)
		else:
			minZ = zRange[0]
			maxZ = zRange[1]

		# number of grid points along each orthogonal direction
		if gridMethodisN == True:
			# find the minimum spacing
			spacing = min([abs((maxX-minX)/Ngrid), abs((maxY-minY)/Ngrid), abs((maxZ-minZ)/Ngrid)])
			xStepN = round(abs((maxX-minX)/spacing))
			yStepN = round(abs((maxY-minY)/spacing))
			zStepN = round(abs((maxZ-minZ)/spacing))
		elif gridMethodisN == False:
			xStepN = round(abs((maxX-minX)/Lgrid))
			yStepN = round(abs((maxY-minY)/Lgrid))
			zStepN = round(abs((maxZ-minZ)/Lgrid))

		# coordinates of each grids in orthogonal directions
		gridXCoords = np.linspace(minX, maxX, xStepN, dtype=float)
		gridYCoords = np.linspace(minY, maxY, yStepN, dtype=float)
		gridZCoords = np.linspace(minZ, maxZ, zStepN, dtype=float)	

		# interpolation process
		if typeList[1] == 'lin':
			print('sorry - not completed yet')
			return None

		elif typeList[1] == 'OK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.ok3d import OrdinaryKriging3D

			# perform interpolation
			tempInterpolated = OrdinaryKriging3D(inputX, inputY, inputZ, inputW, variogram_model=typeList[2])
			interpolW, stdW = tempInterpolated.execute('grid', gridXCoords, gridYCoords, gridZCoords)

		elif typeList[1] == 'UK':
			# import relevent python modules for provided interpolation type and method chosen
			# from pykrige.uk3d import UniversalKriging3D

			# perform interpolation
			tempInterpolated = UniversalKriging3D(inputX, inputY, inputZ, inputW, variogram_model=typeList[2])
			interpolW, stdW = tempInterpolated.execute('grid', gridXCoords, gridYCoords, gridZCoords)

		# for pykrige, eliminate points that has a large standard deviation
		if typeList[1] in ['OK', 'UK']:
			# for loopWPred1 in range(len(interpolW)):
			# 	for loopWPred2 in range(len(interpolW[0])):
			# 		for loopWPred3 in range(len(interpolW[0][0])):
			# 			if stdW[loopWPred1][loopWPred2][loopWPred3] > stdMax:
			# 				interpolW[loopWPred1][loopWPred2][loopWPred3] = np.nan	

			interpolW = np.where(stdW > stdMax, np.nan, interpolW)

		# combine all coordinates into single output file format
		# outFile = []
		# for loop31 in range(len(interpolW)):
		# 	for loop32 in range(len(interpolW[0])):
		# 		for loop33 in range(len(interpolW[0][0])):
		# 			# combine into single output file
		# 			if typeList[1] in ['OK', 'UK']:
		# 				outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], stdW[loop31][loop32][loop33]])
		# 			else:
		# 				outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], np.nan])						

		## itertools version
		outFile = []
		for loop31, loop32, loop33 in itertools.product(range(len(interpolW)), range(len(interpolW[0])), range(len(interpolW[0][0]))):
			# combine into single output file
			if typeList[1] in ['OK', 'UK']:
				outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], stdW[loop31][loop32][loop33]])
			else:
				outFile.append([gridXCoords[loop33], gridYCoords[loop32], gridZCoords[loop31], interpolW[loop31][loop32][loop33], np.nan])		

		## taichi version
		# outFile_taichi = ti.field(dtype=ti.f32, shape=(int(np.product(interpolW.shape)), 5))

		# interpolW_taichi = ti.field(dtype=ti.f32, shape=interpolW.shape)
		# interpolW_taichi.from_numpy(interpolW)

		# gridXCoords_taichi = ti.field(dtype=ti.f32, shape=len(gridXCoords))
		# gridYCoords_taichi = ti.field(dtype=ti.f32, shape=len(gridYCoords))
		# gridZCoords_taichi = ti.field(dtype=ti.f32, shape=len(gridZCoords))
		# gridXCoords_taichi.from_numpy(gridXCoords)
		# gridYCoords_taichi.from_numpy(gridYCoords) 
		# gridZCoords_taichi.from_numpy(gridZCoords) 

		# if typeList[1] in ['OK', 'UK']: 
		# 	stdW_taichi = ti.field(dtype=ti.f32, shape=stdZ.shape)
		# 	stdW_taichi.from_numpy(stdZ) 

		# @ti.kernel
		# def assign_4d_data():
		# 	for loopZ, loopY, loopX in ti.ndrange(interpolW.shape):

		# 		table_row_idx = loopZ + loopY*len(gridZCoords) + loopX*len(gridYCoords)*len(gridZCoords)

		# 		outFile_taichi[table_row_idx,0] = gridXCoords_taichi[loopX]
		# 		outFile_taichi[table_row_idx,1] = gridYCoords_taichi[loopY]
		# 		outFile_taichi[table_row_idx,2] = gridZCoords_taichi[loopZ]
		# 		outFile_taichi[table_row_idx,3] = interpolW_taichi[loopZ, loopY, loopX]

		# 		if typeList[1] in ['OK', 'UK']:
		# 			outFile_taichi[table_row_idx,4] = stdW_taichi[loopZ, loopY, loopX] 
		# 		else: 
		# 			outFile_taichi[table_row_idx,4] = ti.log(ti.Vector([-1]))  # nan

		# assign_4d_data()

		# outFile = outFile_taichi.to_numpy()
		# outFile = outFile.tolist()

		# export the interpolated data into csv file
		if export == True:
			if exportName == None:
				exportList2CSV('interpolated_'+interpType.replace(' ','_')+'_'+DEMname, outFile)
			else: 
				exportList2CSV(exportName+'.csv', outFile)

	
	'''output files'''
	if outputSingle == False:
		if typeList[0] == 2:
			return outFile, gridXCoords, interpolY, stdY
		elif typeList[0] == 3:
			return outFile, gridXCoords, gridYCoords, interpolZ, stdZ
		elif typeList[0] == 4:
			return outFile, gridXCoords, gridYCoords, gridZCoords, interpolW, stdW
	else:
		return outFile

#################################################################################################################
### geoFileConvert_20240902
#################################################################################################################
###########################################################################
## conversion from xyz (csv) file format into mesh grid
###########################################################################
# convert xyz to mesh grid matrix
def xyz2mesh(inFileName, exportAll=False, dtype_opt=float):
	"""take 3 columns based XYZ in CSV file format and convert to mesh grid

	Args:
		inFileName (str, array-like): input csv file name (.csv file) or array-like 3 columns XYZ dataset
		exportAll (bool, optional): export all metadatas with mesh grid. Defaults to False.
		dtype_opt (python type, optional): mesh data type. Defaults to float.

	Returns:
		outputZ: _description_
		*metadata: metadatas from XYZ
			gridUniqueX (numpy array): cell x-coordinates
			gridUniqueY (numpy array): cell y-coordinates
			deltaX (float): cell distance in x-direction
			deltaY (float): cell distance in y-direction
	"""

	# check inFileName is a variable or a csv file to be imported
	if isinstance(inFileName, str):  
		try: 
			dataset = np.array(csv2list(inFileName))
		except:
			dataset = np.array(csv2list(inFileName+'.csv'))
	else:
		try:
			inFileName	
		except NameError:
			pass
		else:
			if isinstance(inFileName, list):
				dataset = np.array(inFileName)
			elif isinstance(inFileName, np.ndarray):
				dataset = inFileName

	# create a unique list of x and y coordinates
	gridUniqueX = np.unique(dataset[:,0])
	gridUniqueY = np.unique(dataset[:,1])
	
	# place each unique grid into dictionary for easy search
	gridUniqueX_dict = {}
	for idx,loopx in enumerate(gridUniqueX):
		gridUniqueX_dict[loopx] = idx

	gridUniqueY_dict = {}
	for idy,loopy in enumerate(gridUniqueY):
		gridUniqueY_dict[loopy] = idy

	# go through each line of csv file and place them into a grid format
	# row number = y-coordinates
	# col number = x-coordinates
	outputZ = np.zeros((len(gridUniqueY),len(gridUniqueX)),dtype=dtype_opt)
	for xi,yi,zi in zip(dataset[:,0],dataset[:,1],dataset[:,2]):
		outputZ[gridUniqueY_dict[yi], gridUniqueX_dict[xi]] = zi

	if exportAll:
		deltaX = abs(gridUniqueX[0]-gridUniqueX[1])		# spacing between x grids
		deltaY = abs(gridUniqueY[0]-gridUniqueY[1])		# spacing between y grids
		return outputZ, gridUniqueX, gridUniqueY, deltaX, deltaY
	else:
		return outputZ

# convert mesh to xyz format to be exported as csv
def mesh2xyz(mesh_file, gridUniqueX, gridUniqueY, dtype_opt=float, row_or_col_increase_first="col"):
	"""takes mesh grid and convert to 3 columns based XYZ

	Args:
		mesh_file (numpy array): mesh of the 3rd axis
		gridUniqueX (numpy array): cell x-coordinates
		gridUniqueY (numpy array): cell y-coordinates
		dtype_opt (type, optional): mesh data type. Defaults to float.
		row_or_col_increase_first (str, optional): select whether row (Y) or col (X) increases first in XYZ format. Defaults to "col".	

	Returns:
		output_xyz (numpy array): 3 columns based XYZ of the mesh data 
	"""

	if row_or_col_increase_first == "row":
		xx = np.tile(gridUniqueX, len(gridUniqueY))
		yy = np.repeat(gridUniqueY, len(gridUniqueX))
		zz = np.ravel(mesh_file, order='C')  # equivalent to joining each rows

	elif row_or_col_increase_first == "col":
		xx = np.repeat(gridUniqueX, len(gridUniqueY))
		yy = np.tile(gridUniqueY, len(gridUniqueX))
		zz = np.ravel(mesh_file, order='F')  # equivalent to joining each rows

	output_xyz = np.vstack((xx, yy, zz), dtype=dtype_opt).transpose()
	
	return output_xyz
	
###########################################################################
## conversion between xyz/csv and lidar (las) file
###########################################################################
# convert las to xyz
def las2xyz(inFileName, outFileName=None, outFileFormat='csv', saveOutputFile=False):
	"""take LiDAR .las files and convert to 3 columns based XYZ file

	Args:
		inFileName (str): file path and name of the LiDAR las file
		outFileName (str, optional): output xyz file name. if None, automatically generated. Defaults to None.
		outFileFormat (str, optional): output xyz file format. Options are "csv" and "txt". Defaults to 'csv'.
		saveOutputFile (bool, optional): if True, save the convert file. Defaults to False.

	Returns:
		dataset (numpy array): 3 columns based XYZ of the LiDAR las data 
	"""

	# convert las to csv i.e. xyz
	inFile = laspy.file.File(inFileName+'.las', mode="r")

	# inFileX = np.array((inFile.X - inFile.header.offset[0])*inFile.header.scale[0])
	# inFileY = np.array((inFile.Y - inFile.header.offset[1])*inFile.header.scale[1])
	# inFileZ = np.array((inFile.Z - inFile.header.offset[2])*inFile.header.scale[2])

	inFileX = np.array(inFile.x)
	inFileY = np.array(inFile.y)
	inFileZ = np.array(inFile.z)

	dataset = np.vstack([inFileX, inFileY, inFileZ]).transpose()

	if saveOutputFile:
		# import csv

		if outFileName == None:
			outFileNameF = inFileName+'_XYZ'
		else:
			outFileNameF = outFileName

		if outFileFormat == 'csv':
			with open(outFileNameF+'.csv', 'w', newline='') as csvfile:
				writer = csv.writer(csvfile, delimiter=',')
				for data in dataset:
					writer.writerow(data) 
		elif outFileFormat == 'txt':
			with open(outFileNameF+'.txt', 'w', newline='') as csvfile:
				writer = csv.writer(csvfile, delimiter='\t')
				for data in dataset:
					writer.writerow(data) 

	inFile.close()

	return dataset

def nonzero_int(value):
	# import decimal 

	if abs(decimal.Decimal(value).as_tuple().exponent):
		return 0

	intVal_list = list(str(int(value)))
	intVal_list.reverse()

	countZero = 0
	for idx in range(len(intVal_list)):
		if int(intVal_list[idx]) == 0:
			countZero += 1
		elif int(intVal_list[idx]) != 0:
			break

	return countZero

# convert csv to las
def xyz2las(inFileName, inFileFormat='csv', outFileName=None, offsets=[None,None,None], scales=[None,None,None], maxDP=3):

	'''
	# input
		inFileName			:	input csv/xyz file name 

			Note: there is bug in the laspy module
				if there are more than 5 digits on the left side of the decimal point (i.e. value >= million),
				then there is error occuring - currently fixed by changing the scaling factor

		inFileFormat 		:	type of file input (default = 'csv')
									if 'csv' = input csv file (comma delimiter)
									if 'txt' = input txt file (tab delimiter)

		outFileName			:	output xyz file name 
	
		Note: actual_value = (las_value - offset_value)*scale_value

		offset				:	offset value [xmin,ymin,zmin]	(default = [None,None,None])
									if None -> no offset; therefore, offset = 0
									if 'min' -> value minimum as offset 
									if userdefined [offset in x, offset in y, offset in z] -> just assign offset user requests

								example if offset=[None,'min',0.01], then offset = [0 (no offset), minimum Y value, 0.01 (user specified)]
						
		scale				:	precision scale factor	(default = [None,None,None])
									if None -> compute the lowest decimal points of inputs 
									if userdefined [scale in x, scale in y, scale in z] -> just assign precision user requests 

								example if offset=[None,0.01,0.01], then offset = [based on X value with lowest decimal, 0.01 (user specified), 0.01 (user specified)]

		maxDP				:	maximum decimal place for automatically computing the precision scale factor: int number (default = 3)

	# output
		outFileName			:	output xyz file name 
	'''
	
	# import python modules
	# import laspy
	#import csv
	#from making_list_with_floats import csv2list, txt2list
	# import numpy as np

	# check inFileName is a variable or a csv file to be imported
	'''
	try:
		inFileName
	except NameError:
		dataset = np.array(csv.reader(inFileName+'.csv'))
	else:
		if isinstance(inFileName, list):
			dataset = np.array(inFileName)
		elif isinstance(inFileName, np.ndarray):
			dataset = inFileName
	'''
	# import csv or txt file
	if inFileFormat == 'csv':
		dataset = np.array(csv2list(inFileName+'.csv'))
	elif inFileFormat == 'txt':
		dataset = np.array(txt2list(inFileName+'.txt'))

	# create blank las file to be filled 
	hdr = laspy.header.Header()		# generate las file header

	# assign name to the output las file
	if outFileName == None:
		outFileNameF = 'output_xyz2las'
	else:
		outFileNameF = outFileName

	# create output las file to be written
	outfile = laspy.file.File(outFileNameF+'.las', mode="w", header=hdr)

	# sort each XYZ values into individual numpy 1-D array
	allx = dataset.transpose()[0]			
	ally = dataset.transpose()[1]
	allz = dataset.transpose()[2]

	## offset 

	# compute minimum XYZ values if there is 'min' option in the offset input
	if 'min' in offsets:
		xmin = np.floor(allx.min())
		ymin = np.floor(ally.min())
		zmin = np.floor(allz.min())
		minXYZ = [xmin, ymin, zmin] 

	offsetList_f = [0,0,0]
	for loopOffset in range(3):

		if offsets[loopOffset] == None:	# no offset
			offsetList_f[loopOffset] = 0

		elif offsets[loopOffset] == 'min':	# use minimum value as offset
			offsetList_f[loopOffset] = minXYZ[loopOffset] 

		else:
			offsetList_f[loopOffset] = offsets[loopOffset]

	outfile.header.offset = offsetList_f

	## scale

	# compute max decimal point of XYZ values if there is None option in the scale input
	sampleSize = 20
	if None in scales:

		# take a random value along the XYZ datapoints
		randomX = allx[np.random.randint(0, high=len(allx), size=sampleSize)]
		randomY = ally[np.random.randint(0, high=len(ally), size=sampleSize)]
		randomZ = allz[np.random.randint(0, high=len(allz), size=sampleSize)]
		randomXYZ = [randomX, randomY, randomZ]

		# find the decimal place of each random XYZ value, but set maximum decimal point as 3 
		# import decimal 
		# from scipy.stats import mode

		dpN = [[],[],[]]
		for loopDP in range(sampleSize):	
			dpN[0].append(abs(decimal.Decimal(randomX[loopDP]).as_tuple().exponent))
			dpN[1].append(abs(decimal.Decimal(randomY[loopDP]).as_tuple().exponent))
			dpN[2].append(abs(decimal.Decimal(randomZ[loopDP]).as_tuple().exponent))
		
		#dpList = [min(mode(dpN[0],axis=None)[0][0] - 2, maxDP), min(mode(dpN[1],axis=None)[0][0] - 2, maxDP), min(mode(dpN[2],axis=None)[0][0] - 2, maxDP)]
		dpList = [min(int(np.floor(0.5*(max(dpN[0])+min(dpN[0])))), maxDP),
					min(int(np.floor(0.5*(max(dpN[1])+min(dpN[1])))), maxDP), 
					min(int(np.floor(0.5*(max(dpN[2])+min(dpN[2])))), maxDP)]
		#print(dpList)

		# find the number of interger points on the left side of the decimal point
		ipN = [[],[],[]]
		for loopIP in range(sampleSize):	
			ipN[0].append(len(str(int(randomX[loopIP]))))
			ipN[1].append(len(str(int(randomY[loopIP]))))
			ipN[2].append(len(str(int(randomZ[loopIP]))))
		ipList = [mode(ipN[0],axis=None)[0][0], mode(ipN[1],axis=None)[0][0], mode(ipN[2],axis=None)[0][0]]

		# find the number of significant points data (nonzero value) in the integer value
		sfN = [[],[],[]]
		for loopSF in range(sampleSize):	
			sfN[0].append(nonzero_int(randomX[loopSF]))
			sfN[1].append(nonzero_int(randomY[loopSF]))
			sfN[2].append(nonzero_int(randomZ[loopSF]))
		sfList = [min(sfN[0]), min(sfN[1]), min(sfN[2])]

		# find maximum decimal place from XYZ value and place as scale 
		scale_None = round(0.1**max(dpList), max(dpList))
	
	scaleList_f = [0,0,0]
	for loopScale in range(3):

		if scales[loopScale] == None:	
			
			if dpList[loopScale] == 0:	# if there is no decimal point
				scaleList_f[loopScale] = 10**sfList[loopScale]
			
			else:	# if there is decimla point
				scaleList_f[loopScale] = round(0.1**dpList[loopScale], dpList[loopScale])
		
		else:	# user defined scale
			scaleList_f[loopScale] = scales[loopScale]
			
	outfile.header.scale = scaleList_f

	# input 
	outfile.x = allx
	outfile.y = ally
	outfile.z = allz

	outfile.close()

	return None

###########################################################################
## conversion between xyz to asc (ESRI ASCII grid) file format 
###########################################################################
# convert asc to xyz
def asc2xyz_v2(inFileName, outFileName=None, saveOutputFile=False, user_nodata_z=None, output_meta=False):
	'''
	# input
		inFileName			:	input ESRI ascii file name (.asc file)
		outFileName			:	output xyz file name (default = None)
		saveOutputFile		:	save the convert file (default = False)
	# output
		outFileName			:	output xyz file name
	'''

	# import python modules
	# import numpy as np

	with open(inFileName+'.asc', 'r') as myfile:
		data=myfile.read().replace('\n', ',').split(',')

	mesh_row = list(data[6])
	if (' ' in mesh_row) and ('\t' not in mesh_row):
		delimGrd = ' '
	elif (' ' not in mesh_row) and ('\t' in mesh_row):
		delimGrd = '\t'
	else:
		print('something wrong with grd file on tab and space deliminator')
		assert(1!=1)

	# sort list of files
	ncols = int(data[0].split(delimGrd)[-1])		# for x axis
	nrows = int(data[1].split(delimGrd)[-1])		# for y axis
	xllcorner = float(data[2].split(delimGrd)[-1])
	yllcorner = float(data[3].split(delimGrd)[-1])
	cellsize = float(data[4].split(delimGrd)[-1])
	nodata_value = float(data[5].split(delimGrd)[-1])

	tempZgrid = []
	for zRow in data[6:len(data)]:
		tempZrow = zRow.split(delimGrd)
		tempZgrid_data = [ float(x) for x in tempZrow if len(x) > 0 ]
		if len(tempZgrid_data) > 0:
			tempZgrid.append(tempZgrid_data[:])
	zMesh = np.array(tempZgrid)

	# create grid
	xGrids = np.linspace(xllcorner, xllcorner+cellsize*(ncols-1), ncols)
	# yGrids = np.linspace(yllcorner, yllcorner+cellsize*(nrows-1), nrows)
	yGrids = np.linspace(yllcorner+cellsize*(nrows-1), yllcorner, nrows)

	if isinstance(user_nodata_z, str) and user_nodata_z == "neighbor":
		withData_i, withData_j = np.where(zMesh != nodata_value)
		noData_i, noData_j = np.where(zMesh == nodata_value)

		zMesh_data = np.ravel(zMesh[withData_i, withData_j])
		x_Data = xGrids[withData_j]
		y_Data = yGrids[withData_i]
		xy_Data = np.vstack((x_Data, y_Data)).transpose()
  
		x_noData = xGrids[noData_j]
		y_noData = yGrids[noData_i]

		z_noData = griddata(xy_Data, zMesh_data, (x_noData, y_noData), method='nearest')
  
		zMesh[noData_i, noData_j] = z_noData
  
	elif isinstance(user_nodata_z, (int, float)):
		noData_i, noData_j = np.where(zMesh == nodata_value)
		zMesh[noData_i, noData_j] = user_nodata_z

	# file
	outfile = []
	for i in range(nrows):  		# Y - row
		for j in range(ncols): 		# X - col
			outfile.append([xGrids[j], yGrids[i], zMesh[i,j]])
	# each row on ArcGIS ascii files have same Y coordinates
	# the 1st row corresponds to top of the raster horizontal layer

	if saveOutputFile:
		# import csv

		if outFileName == None:
			outFileNameF = inFileName+'_XYZ'
		else:
			outFileNameF = outFileName

		with open(outFileNameF+'.csv', 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=',')
			for data1 in outfile:
				writer.writerow(data1) 

	if output_meta:
		return outfile, ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value
	else:
		return outfile

# convert xyz to asc and export asc file
def xyz2asc(inFileName, outFileName=None, interpType='3 lin', cellSize=1.0, user_nodata_value=-9999, fmt="%.6f"):

	'''
	# input
		inFileName			:	input xyz file name
		outFileName			:	output ESRI ascii file name 
		interpType			:	type of interpolation to perform to create grid (default = '3 lin')
		cellSize			:	size of cells (default = 1.0)
	# output
		outFileName			:	output asc file name
	'''

	# import python modules
	# import numpy as np
	# from interpolation_lin_OK_UK import interpKrig_v2_0

	# import csv/xyz file and interpolate to create a grid 
	outFile, gridXCoords, gridYCoords, interpolZ, stdZ = interpKrig_v2_0(inFileName, interpType, gridMethodisN=False, Lgrid=cellSize, stdMax=10000, outputSingle=False) 

	# create header 
	header = "ncols %s\n" % len(gridXCoords)	# number of grids along x axis
	header += "nrows %s\n" % len(gridYCoords)	# number of grids along y axis
	header += "xllcorner %s\n" % min(gridXCoords)	# X-coordinate of the origin (by center or lower left corner of the cell)
	header += "yllcorner %s\n" % min(gridYCoords)	# Y-coordinate of the origin (by center or lower left corner of the cell)
	header += "cellsize %s\n" % cellSize 			# distance between each grids
	header += "nodata_value %s" % user_nodata_value

	if outFileName == None:
		outFileNameF = 'output_xyz2'+'enri_ascii_'+interpType
	else:
		outFileNameF = outFileName

	interpolZ_flipped = interpolZ[::-1]   
	# the 1st row corresponds to top of the raster horizontal layer
	# the mesh from xyz2mesh is flipped where 1st row is the bottom of the raster -> need to be flipped

	np.savetxt(outFileNameF+'.asc', interpolZ_flipped, header=header, fmt=fmt, comments='')

	return None

# convert xyz to asc and export asc file
def data_xyz2asc(varNameXYZ, outFileName=None, user_nodata_value=-9999, fmt="%.6f"):

	'''
	# input
		inFileName			:	input xyz file name
		outFileName			:	output ESRI ascii file name 
		interpType			:	type of interpolation to perform to create grid (default = '3 lin')
		cellSize			:	size of cells (default = 1.0)
	# output
		outFileName			:	output asc file name
	'''

	outputZ, gridUniqueX, gridUniqueY, deltaX, deltaY = xyz2mesh(varNameXYZ, exportAll=True, dtype_opt=float)
	cellSize = 0.5*(deltaX + deltaY)

	# create header 
	header = "ncols %s\n" % len(gridUniqueX)	# number of grids along x axis
	header += "nrows %s\n" % len(gridUniqueY)	# number of grids along y axis
	header += "xllcorner %s\n" % min(gridUniqueX)	# X-coordinate of the origin (by center or lower left corner of the cell)
	header += "yllcorner %s\n" % min(gridUniqueY)	# Y-coordinate of the origin (by center or lower left corner of the cell)
	header += "cellsize %s\n" % cellSize 			# distance between each grids
	header += "nodata_value %s" % user_nodata_value

	if outFileName == None:
		outFileNameF = 'output_XYZ_to_enri_ascii'
	else:
		outFileNameF = outFileName

	outputZ_flipped = outputZ[::-1]   
	# the 1st row corresponds to top of the raster horizontal layer
	# the mesh from xyz2mesh is flipped where 1st row is the bottom of the raster -> need to be flipped

	np.savetxt(outFileNameF+'.asc', outputZ_flipped, header=header, fmt=fmt, comments='')

	return None

# convert xyz to asc and export asc file
def data_mesh2asc(varNameMesh, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=None, user_nodata_value=-9999, fmt="%.6f"):

	'''
	# input
		inFileName			:	input xyz file name
		outFileName			:	output ESRI ascii file name 
		interpType			:	type of interpolation to perform to create grid (default = '3 lin')
		cellSize			:	size of cells (default = 1.0)
	# output
		outFileName			:	output asc file name
	'''

	cellSize = 0.5*(deltaX + deltaY)

	# create header 
	header = "ncols %s\n" % len(gridUniqueX)	# number of grids along x axis
	header += "nrows %s\n" % len(gridUniqueY)	# number of grids along y axis
	header += "xllcorner %s\n" % min(gridUniqueX)	# X-coordinate of the origin (by center or lower left corner of the cell)
	header += "yllcorner %s\n" % min(gridUniqueY)	# Y-coordinate of the origin (by center or lower left corner of the cell)
	header += "cellsize %s\n" % cellSize 			# distance between each grids
	header += "nodata_value %s" % user_nodata_value

	if outFileName == None:
		outFileNameF = 'output_mesh_to_enri_ascii'
	else:
		outFileNameF = outFileName

	varNameMesh_flipped = varNameMesh[::-1]
	# the 1st row corresponds to top of the raster horizontal layer
	# the mesh from xyz2mesh is flipped where 1st row is the bottom of the raster -> need to be flipped

	np.savetxt(outFileNameF+'.asc', varNameMesh_flipped, header=header, fmt=fmt, comments='')

	return None

###########################################################################
## conversion between xyz to grd (Surfer grid) file format 
###########################################################################
# convert grd to xyz
def grd2xyz_v2(inFileName, headDataOutput=False, outFileName=None, saveOutputFile=False):
	'''
	# input
		inFileName			:	input surfer grd file name (.grd file)
		headDataOutput			:	extract grd gead data (default = False)
		outFileName			:	output xyz file name 
		saveOutputFile		:	save the convert file (default = False)
	# output
		outFileName			:	output xyz file name
	'''

	# import python modules
	# import numpy as np

	# if isinstance(inFileName, str): 
	# 	inFileNameFormat = inFileName.split('.')

	# 	if len(inFileNameFormat) == 1:
	# 		with open(inFileName+'.grd', 'r') as myfile:
	# 			data=myfile.read().split('\n')
	# 	else:
	# 		with open(inFileName, 'r') as myfile:
	# 			data=myfile.read().split('\n')

	with open(inFileName+'.grd', 'r') as myfile:
		data=myfile.read().split('\n')

	#print(data)
	# sort list of files

	## step 1: find the deliminator of the grd file
	allItems = list(data[1])

	if (' ' in allItems) and ('\t' not in allItems):
		delimGrd = ' '
	elif (' ' not in allItems) and ('\t' in allItems):
		delimGrd = '\t'
	else:
		print('something wrong with grd file on tab and space deliminator')
		assert(1!=1)

	Nx = int(data[1].split(delimGrd)[0])
	Ny = int(data[1].split(delimGrd)[-1])
	xMin = float(data[2].split(delimGrd)[0])
	xMax = float(data[2].split(delimGrd)[-1])
	yMin = float(data[3].split(delimGrd)[0])
	yMax = float(data[3].split(delimGrd)[-1])
	zMin = float(data[4].split(delimGrd)[0])
	zMax = float(data[4].split(delimGrd)[-1])

	#print(inFileName)

	# create grid for z axis (elevation)
	if delimGrd == ' ':
		# find all indices where there should change in row
		indices = [i for i, x in enumerate(data) if x == '']  
		#print(len(indices))
		tempZgrid = []

		for loopN in range(len(indices)):
			#print(indices[loopN])
			tempZrow = ''
			# starting iteration list index
			if loopN == 0:
				startID = 5
			else:
				startID = indices[loopN-1]+1

			# join all the string
			for loopNN in range(startID, indices[loopN]):
				tempZrow += str(data[loopNN])

			tempZrowList = (tempZrow.split(' '))
			tempZrowList.pop()
			tempZgrid.append([ float(x) for x in tempZrowList ])

		tempZgrid.pop()

	elif delimGrd == '\t':
		tempZgrid = []

		for loopN in range(5,len(data)):
			rowData = data[loopN].split(delimGrd)
			rowData.pop()

			tempZgrid.append([ float(x) for x in rowData ])

	zMesh = np.array(tempZgrid)
	#print(tempZgrid)

	# create grid
	xGrids = np.linspace(xMin, xMax, Nx)
	yGrids = np.linspace(yMin, yMax, Ny)

	# file
	outfile = []
	for i in range(len(yGrids)):  # row
		for j in range(len(xGrids)):  # col
			outfile.append([xGrids[j], yGrids[i], zMesh[i,j]])
	# each row on surfer 6 txt grd files have same Y coordinates

	# output csv file
	if saveOutputFile:
		# import csv

		if outFileName == None:
			outFileNameF = inFileName+'_XYZ'
		else:
			outFileNameF = outFileName

		with open(outFileNameF+'.csv', 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=',')
			for data1 in outfile:
				writer.writerow(data1) 
	
	if headDataOutput:
		return outfile, [Nx, Ny, xMin, xMax, yMin, yMax, zMin, zMax]
	else:
		return outfile

# convert grd to numpy array and find Zcoordinate value from given XY coordinates 
def grd2pointXY(inFileName, XYcoord, interpType='lin', data_diff=2, single_output=True):
	'''
	# input
		inFileName		:	input surfer grd file name (.grd file)
		
		XYcoord 		:	list of x and y coordinates (in list form) -> [X, Y]
			e.g. XYcoord = [[0,1],[1,2]]   find all z value at points [0,1] and [1,2]
		
		interpType		:	3D interpolation method to use if not exact (default = 'lin')
			'lin' -> scipy.interpolate.griddata function with linear method
			'cubic' -> scipy.interpolate.griddata function with cubic method
			'OK xxx'  -> Ordinary Kriging with semi-variance model of xxx (pykrige)
				e.g. 'OK linear' -> Ordinate Kriging with linear semi-variance model
			'UK xxx'  -> Universal Kriging with semi-variance model of xxx (pykrige)
				e.g. 'UK gaussian' -> Universal Kriging with gaussian semi-variance model
	
			Mathematical model for semi-veriograms (kriging):
			1. linear						
			2. power			
			3. gaussian			
			4. spherical			
			5. exponential	

		data_diff		:	interval at which the sample is selected from the whole data 
			e.g. data_diff = 2 -> points at index above and below 2 of the selected XY point will be taken as consideration for interpolations

	# output
		
		output 			:	list of XYZ output value from grd file (exact or interpolated) [X, Y, Z]
			e.g. output = [[0,1,0],[1,2,1]]
		dim_value		:	list of Z output value from grd file (exact or interpolated) [Z]
	'''

	# import python modules
	# import numpy as np

	if isinstance(inFileName, str): 
		inFileNameFormat = inFileName.split('.')

		if len(inFileNameFormat) == 1:
			with open(inFileName+'.grd', 'r') as myfile:
				data=myfile.read().split('\n')
		else:
			with open(inFileName, 'r') as myfile:
				data=myfile.read().split('\n')

	#print(data)
	# sort list of files

	## step 1: find the deliminator of the grd file
	allItems = list(data[1])

	if (' ' in allItems) and ('\t' not in allItems):
		delimGrd = ' '
	elif (' ' not in allItems) and ('\t' in allItems):
		delimGrd = '\t'
	else:
		print('something wrong with grd file on tab and space deliminator')
		assert(1!=1)

	# sort grid information
	Nx = int(data[1].split(delimGrd)[0])
	Ny = int(data[1].split(delimGrd)[1])
	xMin = float(data[2].split(delimGrd)[0])
	xMax = float(data[2].split(delimGrd)[1])
	yMin = float(data[3].split(delimGrd)[0])
	yMax = float(data[3].split(delimGrd)[1])
	# zMin = float(data[4].split(delimGrd)[0])
	# zMax = float(data[4].split(delimGrd)[1])

	#print(inFileName)

	# create grid for z axis (elevation)
	if delimGrd == ' ':
		# find all indices where there should change in row
		indices = [i for i, x in enumerate(data) if x == '']  
		#print(len(indices))
		tempZgrid = []

		for loopN in range(len(indices)):
			#print(indices[loopN])
			tempZrow = ''
			# starting iteration list index
			if loopN == 0:
				startID = 5
			else:
				startID = indices[loopN-1]+1

			# join all the string
			for loopNN in range(startID, indices[loopN]):
				tempZrow += str(data[loopNN])

			tempZrowList = (tempZrow.split(' '))
			tempZrowList.pop()
			tempZgrid.append([ float(x) for x in tempZrowList ])

		tempZgrid.pop()

	elif delimGrd == '\t':
		tempZgrid = []

		for loopN in range(5,len(data)):
			rowData = data[loopN].split(delimGrd)
			rowData.pop()

			tempZgrid.append([ float(x) for x in rowData ])

	zMesh = np.array(tempZgrid)
	# row = y coordinates, col = x coordinates
	dim_value = []

	## loop through given XY corodinates to find Z value
	for loopXY in range(len(XYcoord)):	

		# compute index location of XY coordinates in the mesh
		# compute the step of interval along the x and y grids
		xIDX = (XYcoord[loopXY][0] - xMin)/((xMax-xMin)/(Nx-1))
		yIDX = (XYcoord[loopXY][1] - yMin)/((yMax-yMin)/(Ny-1))

		# check whether xIDX or yIDX is integer
		checkX = (abs(xIDX-int(xIDX)) == 0)		# check xIDX is int
		checkY = (abs(yIDX-int(yIDX)) == 0)		# check yIDX is int

		# if both are integer, take the z value directly from zMesh
		if checkX and checkY:
			XYcoord[loopXY].append(zMesh[int(yIDX)][int(xIDX)])
			dim_value.append(zMesh[int(yIDX)][int(xIDX)])

		# else if not use interpolation
		else:
			# x and y grid coordinates
			gridXCoords = np.linspace(xMin, xMax, Nx, dtype=float)
			gridYCoords = np.linspace(yMin, yMax, Ny, dtype=float)

			# compute index for 
			if checkX:
				section_gridXCoords_idx = np.linspace((np.floor(xIDX)-data_diff),(np.ceil(xIDX)+data_diff),(2*data_diff+1),dtype=int)
			else:
				section_gridXCoords_idx = np.linspace((np.floor(xIDX)-data_diff),(np.ceil(xIDX)+data_diff),(2*data_diff+2),dtype=int)

			if checkY:
				section_gridYCoords_idx = np.linspace((np.floor(yIDX)-data_diff),(np.ceil(yIDX)+data_diff),(2*data_diff+1),dtype=int)
			else:
				section_gridYCoords_idx = np.linspace((np.floor(yIDX)-data_diff),(np.ceil(yIDX)+data_diff),(2*data_diff+2),dtype=int)

			#print(section_gridXCoords_idx)
			#print(section_gridYCoords_idx)

			# determine the interpolation method
			# create a list of interpType info [interpolation kind, semi-variagram model (OK and UK)]
			typeList = interpType.split(' ')		
			if len(typeList) == 1 and typeList[0] in ['OK','UK']:
				typeList.append('linear')

			## create input file
			# XYZ format	
			inputFile = []		
			for j in section_gridYCoords_idx:
				for i in section_gridXCoords_idx:
					inputFile.append([gridXCoords[i], gridYCoords[j], zMesh[j][i]])

			#print(inputFile)

			# column of inptues in XYZ coordiantes
			inputX, inputY, inputZ = np.array(inputFile).T 
			#print(inputX, inputY, inputZ)

			# for 'lin' or 'cubic' method combine X and Y column
			if typeList[0] in ['lin','cubic']: 
				inputXY = np.array(inputFile)[:,[0,1]]

			# interpolation process
			if typeList[0] == 'lin':

				# import relevent python modules for provided interpolation type and method chosen
				# from scipy.interpolate import griddata

				# perform interpolation
				interpolZ = griddata(inputXY, inputZ, (XYcoord[loopXY][0], XYcoord[loopXY][1]), method='linear')

				# add Z value 
				interpolZ = interpolZ.tolist()
				#XYcoord[loopXY].append(interpolZ)
				dim_value.append(interpolZ)

			
			elif typeList[0] == 'cubic':
				# import relevent python modules for provided interpolation type and method chosen
				# from scipy.interpolate import griddata

				# perform interpolation
				interpolZ = griddata(inputXY, inputZ, (XYcoord[loopXY][0], XYcoord[loopXY][1]), method='cubic')
				
				# add Z value 
				interpolZ = interpolZ.tolist()
				XYcoord[loopXY].append(interpolZ)
				dim_value.append(interpolZ)

			elif typeList[0] == 'OK':
				# import relevent python modules for provided interpolation type and method chosen
				# from pykrige.ok import OrdinaryKriging

				# perform interpolation
				try:
					tempInterpolated = OrdinaryKriging(inputX, inputY, inputZ, variogram_model=typeList[1])
					#interpolZ, stdZ = tempInterpolated.execute('grid', section_gridXCoords, section_gridYCoords)
					interpolZ, stdZ = tempInterpolated.execute('points', XYcoord[loopXY][0], XYcoord[loopXY][1])
				except:
					if abs(inputZ.max() - inputZ.min()) < 0.0001:
						interpolZ=np.array([0.0])
					else:
						interpolZ=np.array([None])
		
				# add Z value 
				interpolZ = interpolZ.tolist()
				XYcoord[loopXY].append(interpolZ[0])
				dim_value.append(interpolZ[0])

			elif typeList[0] == 'UK':
				# import relevent python modules for provided interpolation type and method chosen
				# from pykrige.uk import UniversalKriging

				# perform interpolation
				try:
					tempInterpolated = UniversalKriging(inputX, inputY, inputZ, variogram_model=typeList[1])
					interpolZ, stdZ = tempInterpolated.execute('points', XYcoord[loopXY][0], XYcoord[loopXY][1])
				except:
					if abs(inputZ.max() - inputZ.min()) < 0.0001:
						interpolZ=np.array([0.0])
					else:
						interpolZ=np.array([None])

				# add Z value 
				interpolZ = interpolZ.tolist()
				XYcoord[loopXY].append(interpolZ[0])
				dim_value.append(interpolZ[0])
	
	# output
	if single_output == True:
		return dim_value
	else:
		return XYcoord, dim_value

# convert xyz to grd and export grd file
def xyz2grd(inFileName, offset=None, outFileName=None, interp=True, interpType='3 lin', userNx=None, userNy=None, fmt="%.6f"):
	'''
	# input
		inFileName			:	input xyz file name
		offset				:	offset of x and y coordinates to make origin (i.e. leftmost x and bottom y) into (0,0) coordinates (default=None)
			for user requires to input of offset:	offset=(distance to move x, distance to move y)
			if offset is None, then the computer will automatically assest whether the origin is at (0,0) and automatically offset the x and y coordinates 
		outFileName			:	output surfer grd file name 
		interp 				:	data requires interpolation. If True, then interpolation is conducted (default=True)
		interpType			:	type of interpolation to perform to create grid (default = '3 lin')
		userNx				:	number of spacing in x axis (default = None)
		userNy				:	number of spacing in y axis (default = None)
	
	if userNx or userNy is assigned, the number of spacing is equivalent to the unit distance between the max and min value
	for example,	xMin=0,  xMax=100   ->  userNx = round(xMax-xMin)
		
	# output
		outFileName			:	output asc file name
	'''

	# check inFileName is a variable or a csv file to be imported
	dataset = np.array(csv2list(inFileName))

	allx = dataset.transpose()[0]
	ally = dataset.transpose()[1]
	allz = dataset.transpose()[2]

	# calculate offset value
	if offset == None:
		offsetX = 0
		offsetY = 0
	elif offset == "grid data":
		offsetX = allx.min()
		offsetY = ally.min()
	else:
		offsetX = offset[0]
		offsetY = offset[1]

	if interp:
		# number of spacings in x and y direction
		if userNx == None:
			Nx = abs(round(allx.max()) - round(allx.min()))+1
			Ny = abs(round(ally.max()) - round(ally.min()))+1
		elif userNx != None and isinstance(userNx, int) and isinstance(userNy, int):
			Nx = userNx
			Ny = userNy

		# find minimum spacing distance
		userLgrid = max([abs((allx.max() - allx.min())/(Nx)), abs((ally.max() - ally.min())/(Ny))])

		# import csv/xyz file and interpolate to create a grid 
		outFile, gridXCoords, gridYCoords, interpolZ, stdZ = interpKrig_v2_0(dataset, interpType, gridMethodisN=False, Lgrid=userLgrid, stdMax=10000, outputSingle=False)
		
	else:
		interpolZ, gridXCoords, gridYCoords, deltaX, deltaY = xyz2mesh(dataset, exportAll=True)

	# create header 
	header = 'DSAA\n'
	header += "%s %s\n" % (len(gridXCoords), len(gridYCoords))			# Nx and Ny
	header += "%s %s\n" % (np.min(gridXCoords)-offsetX, np.max(gridXCoords)-offsetX)	# (xMin-offsetX) (xMax-offsetX)
	header += "%s %s\n" % (np.min(gridYCoords)-offsetY, np.max(gridYCoords)-offsetY)	# (yMin-offsetY) (yMax-offsetY)
	header += "%s %s" % (interpolZ.min(), interpolZ.max())	# zmin zMax		(allz.min(), allz.max())	# zmin zMax	

	if outFileName == None:
		if interp:
			outFileNameF = 'output_xyz2surfer_grd_'+interpType
		else:
			outFileNameF = 'output_xyz2surfer_grd_noInterpolation'
	else:
		outFileNameF = outFileName

	# sort z grid mesh so that each row only contains 10 numbers
	# output file
	np.savetxt(outFileNameF+'.grd', interpolZ, header=header, fmt=fmt, comments='')

	return None

# convert xyz to grd and export grd file
def data_xyz2grd(varNameXYZ, offset=None, outFileName=None, fmt="%.6f"):
	'''
	# input
		varNameXYZ			:	input xyz file name
		offset				:	offset of x and y coordinates to make origin (i.e. leftmost x and bottom y) into (0,0) coordinates (default=None)
			for user requires to input of offset:	offset=(distance to move x, distance to move y)
			if offset is None, then the computer will automatically assest whether the origin is at (0,0) and automatically offset the x and y coordinates 
		outFileName			:	output surfer grd file name 
	
	if userNx or userNy is assigned, the number of spacing is equivalent to the unit distance between the max and min value
	for example,	xMin=0,  xMax=100   ->  userNx = round(xMax-xMin)
		
	# output
		outFileName			:	output asc file name
	'''

	interpolZ, gridXCoords, gridYCoords, deltaX, deltaY = xyz2mesh(varNameXYZ, exportAll=True)

	# calculate offset value
	if offset == None:
		offsetX = 0
		offsetY = 0
	elif offset == "grid data":
		offsetX = np.amin(gridXCoords)
		offsetY = np.amin(gridYCoords)
	else:
		offsetX = offset[0]
		offsetY = offset[1]

	# create header 
	header = 'DSAA\n'
	header += "%s %s\n" % (len(gridXCoords), len(gridYCoords))			# Nx and Ny
	header += "%s %s\n" % (np.amin(gridXCoords)-offsetX, np.amax(gridXCoords)-offsetX)	# (xMin-offsetX) (xMax-offsetX)
	header += "%s %s\n" % (np.amin(gridYCoords)-offsetY, np.amax(gridYCoords)-offsetY)	# (yMin-offsetY) (yMax-offsetY)
	header += "%s %s" % (interpolZ.min(), interpolZ.max())	# zmin zMax		(allz.min(), allz.max())	# zmin zMax	

	if outFileName == None:
		outFileNameF = 'output_xyz2surfer_grd'
	else:
		outFileNameF = outFileName

	# sort z grid mesh so that each row only contains 10 numbers
	# output file
	np.savetxt(outFileNameF+'.grd', interpolZ, header=header, fmt=fmt, comments='')

	return None

# convert xyz to grd and export grd file
def data_mesh2grd(varNameMesh, gridUniqueX, gridUniqueY, offset=None, outFileName=None, fmt="%.6f"):
	'''
	# input
		varNameMesh			:	input mesh file name
		offset				:	offset of x and y coordinates to make origin (i.e. leftmost x and bottom y) into (0,0) coordinates (default=None)
			for user requires to input of offset:	offset=(distance to move x, distance to move y)
			if offset is None, then the computer will automatically assest whether the origin is at (0,0) and automatically offset the x and y coordinates 
		outFileName			:	output surfer grd file name 
	
	if userNx or userNy is assigned, the number of spacing is equivalent to the unit distance between the max and min value
	for example,	xMin=0,  xMax=100   ->  userNx = round(xMax-xMin)
		
	# output
		outFileName			:	output asc file name
	'''

	# calculate offset value
	if offset == None:
		offsetX = 0
		offsetY = 0
	elif offset == "grid data":
		offsetX = np.amin(gridUniqueX)
		offsetY = np.amin(gridUniqueY)
	else:
		offsetX = offset[0]
		offsetY = offset[1]

	# create header 
	header = 'DSAA\n'
	header += "%s %s\n" % (len(gridUniqueX), len(gridUniqueY))			# Nx and Ny
	header += "%s %s\n" % (np.amin(gridUniqueX)-offsetX, np.amax(gridUniqueX)-offsetX)	# (xMin-offsetX) (xMax-offsetX)
	header += "%s %s\n" % (np.amin(gridUniqueY)-offsetY, np.amax(gridUniqueY)-offsetY)	# (yMin-offsetY) (yMax-offsetY)
	header += "%s %s" % (np.amin(varNameMesh), np.amax(varNameMesh))	# zmin zMax		(allz.min(), allz.max())	# zmin zMax	

	if outFileName == None:
		outFileNameF = 'output_mesh2surfer_grd'
	else:
		outFileNameF = outFileName

	# sort z grid mesh so that each row only contains 10 numbers
	# output file
	np.savetxt(outFileNameF+'.grd', varNameMesh, header=header, fmt=fmt, comments='')

	return None

###########################################################################
## compute data from DEM grid data
###########################################################################
# isolate local cells to compute elevation and path-finding
def local_cell_single_cell_v3_2(nearest_X, nearest_Y, DEM, gridUniqueX, gridUniqueY):

	local_xy = []
	local_z = []

	# four corners x,y coordinates
	# x
	Cx_min = max(gridUniqueX[0], nearest_X)
	Cx_max = min(gridUniqueX[-1], nearest_X)

	# y
	Cy_min = max(gridUniqueY[0], nearest_Y)
	Cy_max = min(gridUniqueY[-1], nearest_Y)

	## reference points
	# exactly at grid points or at the csv file corner 
	if Cx_min == Cx_max and Cy_min == Cy_max:
		row_C1 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C1 = np.where(gridUniqueX == Cx_min)[0][0]
		zt1 = DEM[row_C1][col_C1]
		local_xy.append([Cx_min, Cy_min])
		local_z.append(zt1)

		# add XY points along the axes
		if Cx_min == gridUniqueX[0] and Cy_min == gridUniqueY[0]:  # corner (Xmin, Ymin)
			
			# xmin + deltaX
			local_xy.append([gridUniqueX[1], gridUniqueY[0]])
			local_z.append(DEM[0][1])  # i,j = y,x

			# ymin + deltaY
			local_xy.append([gridUniqueX[0], gridUniqueY[1]])
			local_z.append(DEM[1][0])  # i,j = y,x

		elif Cx_min == gridUniqueX[0] and Cy_min == gridUniqueY[-1]:  # corner (Xmin, Ymax)
			
			# xmin + deltaX
			local_xy.append([gridUniqueX[1], gridUniqueY[-1]])
			local_z.append(DEM[-1][1])  # i,j = y,x

			# ymax - deltaY
			local_xy.append([gridUniqueX[0], gridUniqueY[-2]])
			local_z.append(DEM[-2][0])  # i,j = y,x

		elif Cx_min == gridUniqueX[-1] and Cy_min == gridUniqueY[-1]:  # corner (Xmax, Ymax)
			
			# xmax - deltaX
			local_xy.append([gridUniqueX[-2], gridUniqueY[-1]])
			local_z.append(DEM[-1][-2])  # i,j = y,x

			# ymax - deltaY
			local_xy.append([gridUniqueX[-1], gridUniqueY[-2]])
			local_z.append(DEM[-2][-1])  # i,j = y,x

		elif Cx_min == gridUniqueX[-1] and Cy_min == gridUniqueY[0]:  # corner (Xmax, Ymin)
			
			# xmin + deltaX
			local_xy.append([gridUniqueX[-2], gridUniqueY[0]])
			local_z.append(DEM[0][-2])  # i,j = y,x

			# ymin + deltaY
			local_xy.append([gridUniqueX[-1], gridUniqueY[1]])
			local_z.append(DEM[1][-1])  # i,j = y,x

	# x-coordinate exactly at grid points or at the x_coordinate edge 
	elif Cx_min == Cx_max and Cy_min != Cy_max:

		# Cy_min
		row_C1 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C1 = np.where(gridUniqueX == Cx_min)[0][0]
		zt1 = DEM[row_C1][col_C1]
		local_xy.append([Cx_min, Cy_min])
		local_z.append(zt1)

		# Cy_max
		row_C2 = np.where(gridUniqueY == Cy_max)[0][0]
		col_C2 = np.where(gridUniqueX == Cx_min)[0][0]
		zt2 = DEM[row_C2][col_C2]
		local_xy.append([Cx_min, Cy_max])
		local_z.append(zt2)

		# add XY points along the axes
		if Cx_min == gridUniqueX[0]:  # boundary Xmin
			
			# xmin + deltaX
			local_xy.append([gridUniqueX[1], Cy_min])
			local_z.append(DEM[row_C1][1])  # i,j = y,x

			# xmin + deltaX
			local_xy.append([gridUniqueX[1], Cy_max])
			local_z.append(DEM[row_C2][1])  # i,j = y,x

		elif Cx_min == gridUniqueX[-1]:  # boundary Xmax
			
			# xmax - deltaX
			local_xy.append([gridUniqueX[-2], Cy_min])
			local_z.append(DEM[row_C1][-2])  # i,j = y,x

			# xmax - deltaX
			local_xy.append([gridUniqueX[-2], Cy_max])
			local_z.append(DEM[row_C2][-2])  # i,j = y,x

	# y-coordinate exactly at grid points or at the y_coordinate edge 
	elif Cx_min != Cx_max and Cy_min == Cy_max:

		# Cx_min
		row_C1 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C1 = np.where(gridUniqueX == Cx_min)[0][0]
		zt1 = DEM[row_C1][col_C1]
		local_xy.append([Cx_min, Cy_min])
		local_z.append(zt1)

		# Cx_max
		row_C2 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C2 = np.where(gridUniqueX == Cx_max)[0][0]
		zt2 = DEM[row_C2][col_C2]
		local_xy.append([Cx_max, Cy_min])
		local_z.append(zt2)

		# add XY points along the axes
		if Cy_min == gridUniqueY[0]:  # boundary Ymin
			
			# ymin + deltaY
			local_xy.append([Cx_min, gridUniqueY[1]])
			local_z.append(DEM[1][col_C1])  # i,j = y,x

			# ymax - deltaY
			local_xy.append([Cx_max, gridUniqueY[1]])
			local_z.append(DEM[1][col_C2])  # i,j = y,x

		elif Cy_min == gridUniqueY[-1]:  # boundary Ymax
			
			# ymin + deltaY
			local_xy.append([Cx_min, gridUniqueY[-2]])
			local_z.append(DEM[-2][col_C1])  # i,j = y,x

			# ymax - deltaY
			local_xy.append([Cx_max, gridUniqueY[-2]])
			local_z.append(DEM[-2][col_C2])  # i,j = y,x

	else:

		## C1 - x_min, y_min
		# get nearest DEM grid - y - row
		row_C1 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C1 = np.where(gridUniqueX == Cx_min)[0][0]

		xt1 = gridUniqueX[col_C1]
		yt1 = gridUniqueY[row_C1]
		local_xy.append([xt1, yt1])

		zt1 = DEM[row_C1][col_C1]
		local_z.append(zt1)

		## C2 - x_min, y_max
		# get nearest DEM grid - y - row
		row_C2 = np.where(gridUniqueY == Cy_max)[0][0]
		col_C2 = np.where(gridUniqueX == Cx_min)[0][0]

		xt2 = gridUniqueX[col_C2]
		yt2 = gridUniqueY[row_C2]
		local_xy.append([xt2, yt2])

		zt2 = DEM[row_C2][col_C2]
		local_z.append(zt2)

		## C3 - x_max, y_min
		# get nearest DEM grid - y - row
		row_C3 = np.where(gridUniqueY == Cy_min)[0][0]
		col_C3 = np.where(gridUniqueX == Cx_max)[0][0]

		xt3 = gridUniqueX[col_C3]
		yt3 = gridUniqueY[row_C3]
		local_xy.append([xt3, yt3])

		zt3 = DEM[row_C3][col_C3]
		local_z.append(zt3)

		## C4 - x_max, y_max
		# get nearest DEM grid - y - row
		row_C4 = np.where(gridUniqueY == Cy_max)[0][0]
		col_C4 = np.where(gridUniqueX == Cx_max)[0][0]

		xt4 = gridUniqueX[col_C4]
		yt4 = gridUniqueY[row_C4]
		local_xy.append([xt4, yt4])

		zt4 = DEM[row_C4][col_C4]
		local_z.append(zt4)

	return local_xy, local_z

def local_cell_v3_2(cell_size, x0, y0, DEM, gridUniqueX, gridUniqueY, z_pre):

	# DEM dimension
	dims = [len(gridUniqueY), len(gridUniqueX)]

	# max and min X and Y value
	minX = min(gridUniqueX)
	maxX = max(gridUniqueX)
	minY = min(gridUniqueY)
	maxY = max(gridUniqueY)

	# nearest grid location to the x0 and y0 coordinates
	nearest_Y = min(gridUniqueY, key=lambda x:abs(x-y0))
	nearest_X = min(gridUniqueX, key=lambda x:abs(x-x0))

	# point is inside the DEM
	# if (x0 >= minX) and (x0 <= maxX) and (y0 >= minY) and (y0 <= maxY): 
	if (nearest_X >= minX) and (nearest_X <= maxX) and (nearest_Y >= minY) and (nearest_Y <= maxY): 

		try:
			# isolate cell size [n x n] as the local region
			if cell_size > 1:

				local_xy = []
				local_z = []

				# get nearest DEM grid - y - row
				row0 = np.where(gridUniqueY == nearest_Y)[0][0]

				# get nearest DEM grid - x - col
				col0 = np.where(gridUniqueX == nearest_X)[0][0]

				# cell size [n x n]
				cell_list = [ii for ii in range(int((-np.floor(cell_size/2))), int(np.floor(cell_size/2)+1))]

				# find (n x n cell) grids
				for i in cell_list:  
					for j in cell_list:  
						if row0+i<(dims[0]) and row0+i>-1 and col0+j<(dims[1]) and col0+j>-1:
							xt = gridUniqueX[col0+j]
							yt = gridUniqueY[row0+i]
							local_xy.append([xt, yt])

							zt = DEM[row0+i][col0+j]
							local_z.append(zt)

			# take only the elevation from surrounding grid
			elif cell_size == 1:
				local_xy, local_z = local_cell_single_cell_v3_2(nearest_X, nearest_Y, DEM, gridUniqueX, gridUniqueY)
	 
		# particle has reached outside the DEM boundary
		# local cell size too big - near the edge
		except Exception as e: 
			local_xy, local_z = local_cell_single_cell_v3_2(nearest_X, nearest_Y, DEM, gridUniqueX, gridUniqueY)

	# point outside the DEM
	else:	

		try:
			local_xy, local_z = local_cell_single_cell_v3_2(nearest_X, nearest_Y, DEM, gridUniqueX, gridUniqueY)

		except Exception as e: 
			# return itself with same Z-axis value
			local_xy = [[nearest_X, nearest_Y]]

			if z_pre is None:

				# get nearest DEM grid - y - row
				row0 = np.where(gridUniqueY == nearest_Y)[0][0]
				# get nearest DEM grid - x - col
				col0 = np.where(gridUniqueX == nearest_X)[0][0]

				zt = DEM[row0][col0]
				local_z = [float(zt)]

			else:
				local_z = [z_pre]

	return local_xy, local_z

# compute elevation Z value based on local DEM grid cells
def compute_Z_v3_0(part_xy, local_xy, local_z, interp_method):
	'''
	import relevent python modules for provided interpolation type and method chosen
	
	interp_method 
	when len(local_xy) == 1:
		cornor point

	when len(local_xy) == 2:
		linear interpolation between two points

	when len(local_xy) > 2: 
		3D interpolation method (default = 'lin')
	
		'lin' -> scipy.interpolate.griddata function with linear method

		'cubic' -> scipy.interpolate.griddata function with cubic method
	
		'OK xxx'  -> Ordinary Kriging with semi-variance model of xxx (pykrige)
			e.g. 'OK linear' -> Ordinate Kriging with linear semi-variance model

		'UK xxx'  -> Universal Kriging with semi-variance model of xxx (pykrige)
			e.g. 'UK gaussian' -> Universal Kriging with gaussian semi-variance model
	
			Mathematical model for semi-veriograms (kriging):
			1. linear						
			2. power			
			3. gaussian			
			4. spherical			
			5. exponential
	'''

	# both coordinates exactly at grid points or at the csv file corner 
	if len(local_xy) == 1:
		return float(local_z[0])

	# one of coordinate is exactly at grid points or at the coordinate edge
	elif len(local_xy) == 2:

		dx = abs(local_xy[0][0] - local_xy[1][0])
		dy = abs(local_xy[0][1] - local_xy[1][1])

		# linear interpolation along y-axis
		if dx == 0:
			interpolZ = local_z[0] + ((local_z[1] - local_z[0])/(local_xy[1][1] - local_xy[0][1]))*(part_xy[1] - local_xy[0][1])

		# linear interpolation along x-axis
		elif dy == 0:
			interpolZ = local_z[0] + ((local_z[1] - local_z[0])/(local_xy[1][0] - local_xy[0][0]))*(part_xy[0] - local_xy[0][0])

		return float(interpolZ)

	# other cases - cell_size > 1 or one with all the edges
	else:
		try:
			if interp_method == 'linear': # scipy linear interpolation
				interpolZ = griddata(np.array(local_xy), np.array(local_z), (part_xy[0], part_xy[1]), method='linear')

			elif interp_method == 'cubic': # scipy 2D cubic interpolation
				if len(local_xy) < 16:	# when number of point less than 16 - minimum points required to perform bicubic interpolation
					interpolZ = griddata(np.array(local_xy), np.array(local_z), (part_xy[0], part_xy[1]), method='linear')
				else:		
					interpolZ = griddata(np.array(local_xy), np.array(local_z), (part_xy[0], part_xy[1]), method='cubic')

			elif interp_method[:2] == 'OK':  # ordinary Kriging interpolation

				# check that there DEM is not flat
				if abs(max(local_z) - min(local_z)) < 0.01:
					if np.unique(local_z) == 1: # if only one value, then use the single unique value
						interpolZ = float(np.unique(local_z))
					
					else: # use scipy bilinear interpolation
						interpolZ = griddata(np.array(local_xy), np.array(local_z), (part_xy[0], part_xy[1]), method='linear')

				else:
					interp_method_list = interp_method.split(' ')		
					variogram_model = interp_method_list[1]
					
					inputX, inputY = np.transpose(np.array(local_xy))

					tempInterpolated = OrdinaryKriging(inputX, inputY, np.array(local_z), variogram_model=variogram_model)
					interpolZ, stdZ = tempInterpolated.execute('points', part_xy[0], part_xy[1])
					interpolZ = float(interpolZ)
				
			elif interp_method[:2] == 'UK':  # universal Kriging interpolation

				# check that there DEM is not flat
				if abs(max(local_z) - min(local_z)) < 0.01:
					if np.unique(local_z) == 1: # if only one value, then use the single unique value
						interpolZ = float(np.unique(local_z))
					
					else: # use scipy bilinear interpolation
						interpolZ = griddata(np.array(local_xy), np.array(local_z), (part_xy[0], part_xy[1]), method='linear')

				else:

					interp_method_list = interp_method.split(' ')		
					variogram_model = interp_method_list[1]

					inputX, inputY = np.transpose(np.array(local_xy))

					tempInterpolated = UniversalKriging(inputX, inputY, np.array(local_z), variogram_model=variogram_model)
					interpolZ, stdZ = tempInterpolated.execute('points', part_xy[0], part_xy[1])
					interpolZ = float(interpolZ)

			return float(interpolZ)

		except:
			# print('Error: interpolation method is incorrect or unrecognized - check interp_method input')
			return None

# get row and col id (ij coordinate) from x,y-coordinates
def compute_ij_v1_1(x0, y0, gridUniqueX, gridUniqueY, deltaX, deltaY):

	import decimal
	import numpy as np

	# min_dx_dp = abs(decimal.Decimal(str(deltaX)).as_tuple().exponent)
	# min_dy_dp = abs(decimal.Decimal(str(deltaY)).as_tuple().exponent)

	# get nearest DEM grid - y - row
	# nearest_Y = round( round(y0/deltaY)*deltaY , min_dy_dp)
	nearest_Y = min(gridUniqueY, key=lambda x:abs(x-y0))

	if nearest_Y not in gridUniqueY:
		row0 = None
	else:
		row0 = np.where(gridUniqueY == nearest_Y)[0][0]

	# get nearest DEM grid - x - col
	# nearest_X = round( round(x0/deltaX)*deltaX , min_dx_dp)
	nearest_X = min(gridUniqueX, key=lambda x:abs(x-x0))

	if nearest_X not in gridUniqueX:
		col0 = None
	else:
		col0 = np.where(gridUniqueX == nearest_X)[0][0]

	return (row0, col0)

###########################################################################
## read specific GIS data from files
###########################################################################
## read GIS data and convert file format
def read_GIS_data(GIS_file_name, input_folder_path, full_output=False):
	"""read GIS data and convert file format

	Args:
		GIS_file_name (string): file name of the GIS file in csv, asc, grd, or las file format.
		input_folder_path (string): directory to the folder containing the GIS_file_name.
		full_output (bool, optional): if set to True, every generated data are returned. if False, only the GIS data in returned. Defaults to False.

	Returns:
		GIS_surface (2D numpy array): GIS data arranged into DEM-like structure in 2D array.
		nodata_value (int or float): values used to identify the noData in ascii files.
		GIS_noData (2D numpy array): GIS data indicating which regions has noData in ascii file format (0 = noData, 1 = data provided).
		gridUniqueX (1D numpy array): [only returned when full_output == True] range of grids in x-directions.
		gridUniqueY (1D numpy array): [only returned when full_output == True] range of grids in y-directions.
		deltaX (int or float): [only returned when full_output == True] spacing between the grids in x-directions.
		deltaY (int or float): [only returned when full_output == True] spacing between the grids in y-directions.
		dx_dp (int or float): [only returned when full_output == True] decimal points (precision) of the spacing in x-directions.
		dy_dp (int or float): [only returned when full_output == True] decimal points (precision) of the spacing in y-directions.
		XYZ_row_or_col_increase_first (string): [only returned when full_output == True] required information when exporting GIS data into files. if "col", the column ("x") data cycles first in XYZ table format. if "row", the row ("y") data cycles first in XYZ table format.
	"""

	# find file type [csv, las, grd, asc]
	GIS_file_name_list = GIS_file_name.split('.')
	GIS_file_name_type = GIS_file_name_list[-1]

	# find the file name only
	GIS_file_name_only_list = GIS_file_name.split("."+GIS_file_name_type)
	GIS_file_name_only_list2 = [txt if n==0 or n==len(GIS_file_name_only_list)-1 else GIS_file_name_only_list2[n-1]+"."+GIS_file_name_type+txt for n,txt in enumerate(GIS_file_name_only_list)]
	GIS_file_name_only = GIS_file_name_only_list2[-2]

	if GIS_file_name_type == 'csv':
		GIS_surface_xyz = np.array(csv2list(input_folder_path+GIS_file_name))
		GIS_surface, gridUniqueX, gridUniqueY, deltaX, deltaY = xyz2mesh(input_folder_path+GIS_file_name, exportAll=True) 

	elif GIS_file_name_type in ['las', 'grd', 'asc']:
		# create xyz data and convert to csv data
		if GIS_file_name_type == 'las':
			GIS_surface_xyz = las2xyz(input_folder_path+GIS_file_name_only, outFileName=input_folder_path+GIS_file_name_only, outFileFormat='csv', saveOutputFile=False)

		elif GIS_file_name_type == 'grd':
			GIS_surface_xyz = grd2xyz_v2(input_folder_path+GIS_file_name_only, headDataOutput=False, outFileName=input_folder_path+GIS_file_name_only, saveOutputFile=False)

		elif GIS_file_name_type == 'asc':
			GIS_surface_xyz = asc2xyz_v2(input_folder_path+GIS_file_name_only, outFileName=input_folder_path+GIS_file_name_only, saveOutputFile=False, user_nodata_z='neighbor')

		GIS_surface, gridUniqueX, gridUniqueY, deltaX, deltaY = xyz2mesh(GIS_surface_xyz, exportAll=True) 

	# if ascii files are used, noData may be present. For efficiency these regions are categorized as noData and subsequently ignored through the analysis
	# for default, assume they are all cell is filled. 0 = noData, 1 = yesData
	if GIS_file_name_type == 'asc':
		GIS_surf_raw_asc_xyz, ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value = asc2xyz_v2(input_folder_path+GIS_file_name_only, outFileName=None, saveOutputFile=False, user_nodata_z=None, output_meta=True)
		GIS_surf_raw_asc_mesh = xyz2mesh(GIS_surf_raw_asc_xyz, exportAll=False) 
		GIS_noData = np.where(GIS_surf_raw_asc_mesh == nodata_value, 0, 1)
	else:
		nodata_value = -9999
		GIS_noData = np.ones((GIS_surface.shape))

	# check if row increases first or column first in csv file
	if abs(GIS_surface_xyz[0][0] - GIS_surface_xyz[1][0]) == 0 and abs(GIS_surface_xyz[0][1] - GIS_surface_xyz[1][1]) > 0:  # col increases first
		XYZ_row_or_col_increase_first = "col"
	elif abs(GIS_surface_xyz[0][0] - GIS_surface_xyz[1][0]) > 0 and abs(GIS_surface_xyz[0][1] - GIS_surface_xyz[1][1]) == 0:  # row increases first
		XYZ_row_or_col_increase_first = "row"
	else:
		print("if the csv XYZ file format seems to be wrong? Please check the csv file")
		sys.exit(3)	
	
	# decimal places of grid X and Y values
	dx_dp = -decimal.Decimal(str(deltaX)).as_tuple().exponent
	dy_dp = -decimal.Decimal(str(deltaY)).as_tuple().exponent

	if full_output:
		return (GIS_surface, nodata_value, GIS_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, dx_dp, dy_dp, XYZ_row_or_col_increase_first)
	else:
		return (GIS_surface, nodata_value, GIS_noData)


## sort out soil thickness GIS data
def generate_soil_thickness_GIS_data(input_folder_path, soil_depth_model, soil_depth_data, dip_surf_filename, DEM_surface, DEM_noData, gridUniqueX, gridUniqueY, local_cell_sizes_slope, cpu_num):
	"""function to account different methods used to generate soil thickness and bedrock surface GIS data

	Parameters
	----------
	input_folder_path : str
		directory to the folder containing the GIS_file_names
	soil_depth_model : int
		option for generating soil depth
	soil_depth_data : (int | float) | str | list
		file name containing depth of soil layer relative to the ground surface or soil thickness 
	dip_surf_filename : str
		file name containing dip of ground surface. either "dip_surf_filename" will import or will be computed from DEM when performing 
	DEM_surface : 2D numpy array
		DEM data showing topography surface elevation
	DEM_noData : 2D numpy array
		DEM-like data showing regions with no data for ASCII GIS formats
	gridUniqueX : 1D numpy array
		grid x-coordinates
	gridUniqueY : 1D numpy array
		grid y-coordinates
	local_cell_sizes_slope : int
		locall grid size used to compute slope
	cpu_num : int
		number of multiprocessing (logical CPU processors)

	Returns
	-------
	DEM_soil_thickness: 2D numpy array
		DEM-like GIS data showing soil thickness
	DEM_base: 2D numpy array
		DEM-like GIS data showing bedrock surface elevation.
	"""	

	# error
	if (soil_depth_data is None) and (soil_depth_model is None):
		print("if soil thickness data is not provided, please specify some non-zero soil depth")
		sys.exit(3)

	# generate uniform soil depth profile from DEM
	elif (soil_depth_model == 0) and isinstance(soil_depth_data[0], (int, float)):
		DEM_base = DEM_surface - float(soil_depth_data[0])
		DEM_soil_thickness = np.ones((DEM_surface.shape))*float(soil_depth_data[0])

	# generate uniform soil depth profile from DEM - probabilistic
	elif (soil_depth_model == 10) and isinstance(soil_depth_data[0], (int, float)):
		DEM_soil_thickness_mean = np.ones((DEM_surface.shape))*float(soil_depth_data[0])
		DEM_soil_thickness_mean_dev = DEM_soil_thickness_mean * ( np.ones((DEM_surface.shape)) + np.random.normal(0, float(soil_depth_data[1]), (DEM_soil_thickness_mean.shape) ) )  # add random deviation to the mean
		DEM_soil_thickness = np.clip(DEM_soil_thickness_mean_dev, soil_depth_data[2], soil_depth_data[3])   # model clipped between min and max
		DEM_base = DEM_surface - DEM_soil_thickness
		
	# generate soil depth profile from files
	elif (soil_depth_model == 1) and isinstance(soil_depth_data[0], str):    
		DEM_soil_thickness, _, _ = read_GIS_data(soil_depth_data[0], input_folder_path, full_output=False)  
		DEM_base = DEM_surface - DEM_soil_thickness 

	# generate soil depth profile from files - probabilistic
	elif (soil_depth_model == 11) and isinstance(soil_depth_data[0], str):    
		DEM_soil_thickness_mean, _, _ = read_GIS_data(soil_depth_data[0], input_folder_path, full_output=False)  
		DEM_soil_thickness_mean_dev = DEM_soil_thickness_mean * ( np.ones((DEM_surface.shape)) + np.random.normal(0, float(soil_depth_data[1]), (DEM_soil_thickness_mean.shape) ) )  # add random deviation to the mean
		DEM_soil_thickness = np.clip(DEM_soil_thickness_mean_dev, soil_depth_data[2], soil_depth_data[3])   # model clipped between min and max
		DEM_base = DEM_surface - DEM_soil_thickness 

	# generate soil depth profile from surface dip from Holm and Edvarson
	elif (soil_depth_model == 2) and isinstance(soil_depth_data, list) and len(soil_depth_data) == 2 and isinstance(soil_depth_data[0], (int, float)) and soil_depth_data[0] >= 0 and isinstance(soil_depth_data[1], (int, float)) and soil_depth_data[1] > soil_depth_data[0]: 
	
		if isinstance(dip_surf_filename, str):
			DEM_dip_mesh_temp, _, _ = read_GIS_data(dip_surf_filename, input_folder_path, full_output=False)
		else:
			DEM_surf_slope_MP_inputs = []
			for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):	
				xx = gridUniqueX[j]
				yy = gridUniqueY[i]

				# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
				if DEM_noData[i,j] == 0:
					continue

				# i, j, x, y, DEM, gridUniqueX, gridUniqueY, local_cell_sizes_slope = DEM_slope_MP_inputs
				DEM_surf_slope_MP_inputs.append( (i, j, xx, yy, DEM_surface, gridUniqueX, gridUniqueY, local_cell_sizes_slope) )

			pool_DEM_slope = mp.Pool(cpu_num)

			DEM_surf_slope_output_data = pool_DEM_slope.map(DEM_slope_aspect_MP_v3, DEM_surf_slope_MP_inputs)
			# i, j, dip_surf, aspect_surf

			pool_DEM_slope.close()
			pool_DEM_slope.join()

			# get surface dip
			DEM_dip_mesh_temp = np.zeros(DEM_surface.shape)
			for (i,j,dip_s,_) in DEM_surf_slope_output_data:
				DEM_dip_mesh_temp[i,j] = dip_s

		DEM_soil_thickness = np.clip(-2.578*np.tan(np.radians(DEM_dip_mesh_temp)) + 2.612, soil_depth_data[0], soil_depth_data[1])   # model clipped between min and max
		del DEM_dip_mesh_temp
		DEM_base = DEM_surface - DEM_soil_thickness	

	# generate soil depth profile from surface dip from Holm and Edvarson - probabilistic
	elif (soil_depth_model == 12) and (isinstance(soil_depth_data, list) and len(soil_depth_data) == 3) and (isinstance(soil_depth_data[0], (int, float)) and soil_depth_data[0] >= 0) and (isinstance(soil_depth_data[1], (int, float)) and soil_depth_data[1] >= 0) and (isinstance(soil_depth_data[2], (int, float)) and soil_depth_data[2] > soil_depth_data[1]): 
	
		if isinstance(dip_surf_filename, str):
			DEM_dip_mesh_temp, _, _ = read_GIS_data(dip_surf_filename, input_folder_path, full_output=False)
		else:
			DEM_surf_slope_MP_inputs = []
			for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):	
				xx = gridUniqueX[j]
				yy = gridUniqueY[i]

				# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
				if DEM_noData[i,j] == 0:
					continue

				# i, j, x, y, DEM, gridUniqueX, gridUniqueY, local_cell_sizes_slope = DEM_slope_MP_inputs
				DEM_surf_slope_MP_inputs.append( (i, j, xx, yy, DEM_surface, gridUniqueX, gridUniqueY, local_cell_sizes_slope) )

			pool_DEM_slope = mp.Pool(cpu_num)

			DEM_surf_slope_output_data = pool_DEM_slope.map(DEM_slope_aspect_MP_v3, DEM_surf_slope_MP_inputs)
			# i, j, dip_surf, aspect_surf

			pool_DEM_slope.close()
			pool_DEM_slope.join()

			# get surface dip
			DEM_dip_mesh_temp = np.zeros(DEM_surface.shape)
			for (i,j,dip_s,_) in DEM_surf_slope_output_data:
				DEM_dip_mesh_temp[i,j] = dip_s

		DEM_soil_thickness_mean = -2.578*np.tan(np.radians(DEM_dip_mesh_temp)) + 2.612   # mean
		del DEM_dip_mesh_temp

		DEM_soil_thickness_mean_dev = DEM_soil_thickness_mean * ( np.ones((DEM_surface.shape)) + np.random.normal(0, float(soil_depth_data[0]), (DEM_soil_thickness_mean.shape) ) )  # add random deviation to the mean
		DEM_soil_thickness = np.clip(DEM_soil_thickness_mean_dev, soil_depth_data[1], soil_depth_data[2])   # model clipped between min and max
		DEM_base = DEM_surface - DEM_soil_thickness	

	# generate soil depth profile from surface dip from multi-regression model
	elif (soil_depth_model == 3) and isinstance(soil_depth_data, list) and len(soil_depth_data) >= 4:
		DEM_soil_thickness = np.ones((DEM_surface.shape)) * soil_depth_data[3]   
		if len(soil_depth_data) > 4:
			for (gis_filename, beta) in soil_depth_data[4:]:
				gis_data_temp, _, _ = read_GIS_data(gis_filename, input_folder_path, full_output=False)
				if soil_depth_data[0] == "linear":
					DEM_soil_thickness = DEM_soil_thickness + beta*gis_data_temp
				elif soil_depth_data[0] == "power":
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, beta)
				del gis_data_temp
		DEM_soil_thickness = np.clip(DEM_soil_thickness, soil_depth_data[1], soil_depth_data[2])   # model clipped between min and max
		DEM_base = DEM_surface - DEM_soil_thickness	
	
	# generate soil depth profile from surface dip from multi-regression model
	elif (soil_depth_model == 13) and (isinstance(soil_depth_data, list) and len(soil_depth_data) >= 5):
		DEM_soil_thickness_mean = np.ones((DEM_surface.shape)) * soil_depth_data[4]   
		if len(soil_depth_data) > 5:
			for (gis_filename, beta) in soil_depth_data[5:]:
				gis_data_temp, _, _ = read_GIS_data(gis_filename, input_folder_path, full_output=False)
				if soil_depth_data[0] == "linear":
					DEM_soil_thickness_mean = DEM_soil_thickness_mean + beta*gis_data_temp
				elif soil_depth_data[0] == "power":
					DEM_soil_thickness_mean = DEM_soil_thickness_mean * np.power(gis_data_temp, beta)
				del gis_data_temp
		DEM_soil_thickness_mean_dev = DEM_soil_thickness_mean * ( np.ones((DEM_surface.shape)) + np.random.normal(0, float(soil_depth_data[1]), (DEM_soil_thickness_mean.shape) ) )  # add random deviation to the mean
		DEM_soil_thickness = np.clip(DEM_soil_thickness_mean_dev, soil_depth_data[2], soil_depth_data[3])   # model clipped between min and max
		DEM_base = DEM_surface - DEM_soil_thickness	

	return DEM_soil_thickness, DEM_base


## sort out initial groundwater table GIS data
def generate_groundwater_GIS_data(input_folder_path, ground_water_model, ground_water_data, DEM_surface, DEM_base, DEM_soil_thickness):
	"""function to account different methods used to generate initial groundwater table GIS data

	Parameters
	----------
	input_folder_path : str
		directory to the folder containing the GIS_file_name
	ground_water_model : int
		file name containing depth from surface at which groundwater table is found
	ground_water_data : str | list
		parameters for assigning groundwater table is found
	DEM_surface : 2D numpy array
		DEM data showing topography surface elevation
	DEM_base : 2D numpy array
		DEM data showing bedrock surface elevation
	DEM_soil_thickness : 2D numpy array
		DEM data showing soil thickness

	Returns
	-------
	DEM_gwt_z: 2D numpy array
		DEM-like GIS data showing elevation of groundwater table (gwt)
	gwt_depth_from_surf: 2D numpy array
		DEM-like GIS data showing depth of groundwater table relative to the ground surface
	"""	

	if ground_water_model is None and ground_water_data is None:  # if no information at all, assume at bedrock
		DEM_gwt_z = np.copy(DEM_base)
		gwt_depth_from_surf = np.copy(DEM_soil_thickness)

	# thickness above bedrock
	elif ground_water_model == 0:
		if isinstance(ground_water_data, (int, float)) and ground_water_data >= 0:  
			# gwt must be on or lower than the ground surface. max_gwt_depth = min(ground_water_data, soil thickness)
			gwt_depth_from_bedrock = np.where(DEM_soil_thickness <= ground_water_data, DEM_soil_thickness, ground_water_data)
		elif isinstance(ground_water_data, str):
			gwt_depth_from_bedrock, _, _ = read_GIS_data(ground_water_data, input_folder_path, full_output=False)  
		gwt_depth_from_surf = np.copy(DEM_soil_thickness) - gwt_depth_from_bedrock
		DEM_gwt_z = np.copy(DEM_base) + gwt_depth_from_bedrock

	# depth from surface
	elif ground_water_model == 1:
		if isinstance(ground_water_data, (int, float)) and ground_water_data >= 0:  # at below certain depth from DEM surface
			# find maximum gwt depth. gwt must be on or higher than the bedrock surface. max_gwt_depth = min(ground_water_value, soil thickness)
			gwt_depth_from_surf = np.where(DEM_soil_thickness >= ground_water_data, ground_water_data, DEM_soil_thickness)
		elif isinstance(ground_water_data, str):
			gwt_depth_from_surf, _, _ = read_GIS_data(ground_water_data, input_folder_path, full_output=False)  
		DEM_gwt_z = np.copy(DEM_surface) - gwt_depth_from_surf 	

	# percentage of the soil thickness above bedrock
	elif ground_water_model == 2:
		if isinstance(ground_water_data, (int, float)) and ground_water_data >= 0 and ground_water_data <= 100:  
			# gwt must be on or lower than the ground surface. max_gwt_depth = min(ground_water_data, soil thickness)
			gwt_depth_from_bedrock = 0.01*ground_water_data*DEM_soil_thickness
			gwt_depth_from_surf = (1.0-0.01*ground_water_data)*DEM_soil_thickness
		elif isinstance(ground_water_data, str):
			gwt_depth_from_bedrock_ratio, _, _ = read_GIS_data(ground_water_data, input_folder_path, full_output=False)
			gwt_depth_from_bedrock = gwt_depth_from_bedrock_ratio*DEM_soil_thickness
			gwt_depth_from_surf = np.copy(DEM_soil_thickness) - gwt_depth_from_bedrock
		DEM_gwt_z = np.copy(DEM_base) + gwt_depth_from_bedrock

	# percentage of the soil thickness from surface
	elif ground_water_model == 3:
		if isinstance(ground_water_data, (int, float)) and ground_water_data >= 0 and ground_water_data <= 100:  
			# gwt must be on or lower than the ground surface. max_gwt_depth = min(ground_water_data, soil thickness)
			gwt_depth_from_surf = 0.01*ground_water_data*DEM_soil_thickness
		elif isinstance(ground_water_data, str):
			gwt_depth_from_surf_ratio, _, _ = read_GIS_data(ground_water_data, input_folder_path, full_output=False)  
			gwt_depth_from_surf = gwt_depth_from_surf_ratio*DEM_soil_thickness
		DEM_gwt_z = np.copy(DEM_surface) - gwt_depth_from_surf 	

	# groundwater table elevation directly given
	elif ground_water_model == 4:
		if isinstance(ground_water_data, str):
			DEM_gwt_z, _, _ = read_GIS_data(ground_water_data, input_folder_path, full_output=False)  
			gwt_depth_from_surf = np.copy(DEM_surface) - DEM_gwt_z

	else:
		print("ground_water_data depth is not correctly specified, please specify uniform non-zero ground_water_data")
		sys.exit(5)

	return DEM_gwt_z, gwt_depth_from_surf


###########################################################################
## DEM resolution change 
###########################################################################
def generate_t0_GA_pond_parameters(monte_carlo_iteration_max, monte_carlo_iter_filename_dict, output_folder_path, filename, DEM_soil_thickness, dip_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, DEM_surf_dip_infiltraion_apply, plot_option, cpu_num, dz, dx_dp, dy_dp, theta_dp, press_dp, cumul_dp, dz_dp, t_dp):
	"""generate parameters for Green-Ampt model for ponding at time step = 0

	Parameters
	----------
	monte_carlo_iteration_max : int
		max number of iterations for Monte Carlo simulation
	monte_carlo_iter_filename_dict : dict
		dictionary containing the filenames of the input data
	output_folder_path : str
		directory to the folder to save the output data
	filename : str
		project name for the simulation
	DEM_soil_thickness : 2D np.ndarray
		grid of soil thickness
	dip_surf : 2D np.ndarray
		grid of surface dip angles 
	DEM_noData : 2D np.ndarray
		grid of no data values
	nodata_value : float
		value representing no data
	gridUniqueX : 1D np.ndarray
		grid of unique X coordinates
	gridUniqueY : 1D np.ndarray
		grid of unique Y coordinates
	deltaX : float
		distance between grid points in the X direction
	deltaY : float
		distance between grid points in the Y direction
	XYZ_row_or_col_increase_first : str
		string indicating whether the XYZ data is in row or column order
	DEM_surf_dip_infiltraion_apply : bool
		True if surface dip angles should be applied to infiltration calculations
	plot_option : bool
		True if plotting options should be applied
	cpu_num : int
		number of CPU cores to use for parallel processing
	dz : float
		vertical grid spacing	
	dx_dp : int
		decimal points (precision) of the spacing in x-directions
	dy_dp : int
		decimal points (precision) of the spacing in y-directions
	theta_dp : int
		decimal points (precision) of the soil moisture content
	press_dp : int
		decimal points (precision) of the pressure head
	cumul_dp : int
		decimal points (precision) of the cumulative infiltration
	dz_dp : int
		decimal points (precision) of the vertical grid spacing
	t_dp : int
		decimal points (precision) of the time step

	Returns
	-------
	monte_carlo_iter_filename_dict : dict
		updated dictionary of monte_carlo_iter_filename_dict containing the filenames of the input data
	"""


	for iter_num in range(1,monte_carlo_iteration_max+1):
		
		# read data from filenames
		DEM_SWCC_model, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_model"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_model"][0], full_output=False)
		DEM_initial_suction, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["initial_suction"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["initial_suction"][0], full_output=False)
		DEM_SWCC_a, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_a"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_a"][0], full_output=False)
		DEM_SWCC_n, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_n"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_n"][0], full_output=False)
		DEM_SWCC_m, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_m"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["SWCC_m"][0], full_output=False)
		DEM_theta_sat, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["theta_sat"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["theta_sat"][0], full_output=False)
		DEM_theta_residual, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["theta_residual"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["theta_residual"][0], full_output=False)
		DEM_soil_m_v, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["soil_m_v"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["soil_m_v"][0], full_output=False)
		DEM_k_sat, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["k_sat"][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]["k_sat"][0], full_output=False)
		DEM_rain_I, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["intensity"]['0'][1], monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["intensity"]['0'][0], full_output=False)

		compute_initial_hydraulic_input = []
		for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):	
			# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
			if DEM_soil_thickness[i,j] <= dz or DEM_noData[i,j] == 0:
				continue

			if DEM_surf_dip_infiltraion_apply:
				surf_dip_i = dip_surf[i,j]
			else:
				surf_dip_i = 0 
    
			compute_initial_hydraulic_input.append( (i, j, DEM_SWCC_model[i,j], DEM_initial_suction[i,j], DEM_SWCC_a[i,j], DEM_SWCC_n[i,j], DEM_SWCC_m[i,j], DEM_theta_sat[i,j], DEM_theta_residual[i,j], DEM_soil_m_v[i,j], DEM_k_sat[i,j], DEM_rain_I[i,j], surf_dip_i ) )

		pool_hydro_initial = mp.Pool(cpu_num)

		initial_hydro_output = pool_hydro_initial.map(compute_initial_hydro_DEM_mp_v2, compute_initial_hydraulic_input)
		# i, j, theta_initial, psi_r, delta_theta, F_p, z_p, T_p, T_pp

		pool_hydro_initial.close()
		pool_hydro_initial.join()

		theta_initial = np.zeros(DEM_base.shape)
		psi_r = np.zeros(DEM_base.shape)
		delta_theta = np.zeros(DEM_base.shape)
		F_p = np.zeros(DEM_base.shape)
		z_p = np.zeros(DEM_base.shape)
		T_p = np.zeros(DEM_base.shape)
		T_pp = np.zeros(DEM_base.shape)
		for (i, j, theta_initial_0, psi_r_0, delta_theta_0, F_p_0, z_p_0, T_p_0, T_pp_0) in initial_hydro_output:
			theta_initial[i,j] = theta_initial_0
			psi_r[i,j] = psi_r_0
			delta_theta[i,j] = delta_theta_0
			F_p[i,j] = F_p_0
			z_p[i,j] = z_p_0
			T_p[i,j] = T_p_0
			T_pp[i,j] = T_pp_0

		# plot
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - theta_initial - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - theta_initial - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, theta_initial, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - psi_r - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - psi_r - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, psi_r, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - delta_theta - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - delta_theta - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, delta_theta, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - F_p - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - F_p - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, F_p, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - z_p - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - z_p - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, z_p, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - T_p - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - T_p - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, T_p, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - T_pp - i{iter_num}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - T_pp - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, T_pp, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
	
		# export data
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "theta_initial", theta_initial, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, theta_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "psi_r", psi_r, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, press_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "delta_theta", delta_theta, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, theta_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "F_p", F_p, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "z_p", z_p, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "T_p", T_p, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, t_dp, time=None, iteration=iter_num)
		generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "T_pp", T_pp, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, t_dp, time=None, iteration=iter_num)

		# export data filename into dictionary
		temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"]
		temp_dict["theta_initial"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - theta_initial - i{iter_num}.{output_txt_format}"]
		temp_dict["psi_r"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - psi_r - i{iter_num}.{output_txt_format}"]
		temp_dict["delta_theta"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - delta_theta - i{iter_num}.{output_txt_format}"]
		temp_dict["F_p"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - F_p - i{iter_num}.{output_txt_format}"]
		temp_dict["z_p"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - z_p - i{iter_num}.{output_txt_format}"]
		temp_dict["T_p"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - T_p - i{iter_num}.{output_txt_format}"]
		temp_dict["T_pp"] = [f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - T_pp - i{iter_num}.{output_txt_format}"]
		monte_carlo_iter_filename_dict["iterations"][str(iter_num)]["material"]["hydraulic"] = deepcopy(temp_dict)
		del temp_dict
	
	return monte_carlo_iter_filename_dict

###########################################################################
## DEM resolution change
###########################################################################
## resample DEM into larger resolution
def compute_larger_DEM_interpolation(inc_DEM_res_input):
	i, j, x, y, DEM, DEM_noData, gridUniqueX, gridUniqueY, increase_DEM_resolution = inc_DEM_res_input
	
	# get local regions and get average of the local regions in larger resolution
	_, local_z = local_cell_v3_2(increase_DEM_resolution, x, y, DEM, gridUniqueX, gridUniqueY, None)
	_, local_noData = local_cell_v3_2(increase_DEM_resolution, x, y, DEM_noData, gridUniqueX, gridUniqueY, None)
	
	if len(local_z) == 0 or np.sum(local_noData) == 0:   # all local regions have noData with ascii files 
		new_z = 0.0
		noData = 0
	else:  # 
		new_z = np.mean(local_z)
		noData = 1
	 
	return (i, j, new_z, noData)

def increase_DEM_resolution_compute(increase_DEM_resolution, DEM, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, cpu_num, full_output=False):
	deltaX_new = deltaX * increase_DEM_resolution
	deltaY_new = deltaY * increase_DEM_resolution
	gridUniqueX_new = np.arange(gridUniqueX[0], gridUniqueX[-1]+0.05*deltaX_new, deltaX_new)  # x-grid, columns
	gridUniqueY_new = np.arange(gridUniqueY[0], gridUniqueY[-1]+0.05*deltaY_new, deltaY_new)  # y-grid, rows

	DEM_surf_MP_inputs = []
	for (i,j) in itertools.product(range(len(gridUniqueY_new)), range(len(gridUniqueX_new))):	
		DEM_surf_MP_inputs.append( (i, j, gridUniqueX_new[j], gridUniqueY_new[i], DEM, DEM_noData, gridUniqueX_new, gridUniqueY_new, increase_DEM_resolution) )

	pool_DEM_new_res = mp.Pool(cpu_num)

	DEM_new_z_data = pool_DEM_new_res.map(compute_larger_DEM_interpolation, DEM_surf_MP_inputs)
	# i, j, new_z, nodata_num

	pool_DEM_new_res.close()
	pool_DEM_new_res.join()

	DEM_new = np.zeros((len(gridUniqueY_new), len(gridUniqueX_new)), dtype=float)
	DEM_noData_new = np.zeros((len(gridUniqueY_new), len(gridUniqueX_new)), dtype=int)
	for (i,j,new_z,noData_num) in DEM_new_z_data:
		DEM_new[i,j] = new_z
		DEM_noData_new[i,j] = noData_num

	if full_output:
		return DEM_new, DEM_noData_new, gridUniqueX_new, gridUniqueY_new, deltaX_new, deltaY_new
	else:
		return DEM_new

###########################################################################
## computation related to dip and aspect
###########################################################################
# dem cell dip and dip_direction
def DEM_slope_aspect_MP_v3(DEM_slope_MP_inputs):
	"""compute dip and aspect in locally selected DEM cell regions
	
	Using the local x,y,z-coordinates, a planar surface is computed using linear function:
		z = beta_constant + beta_x*x + beta_y*y
	The beta_x and beta_y provides the gradient of the planar surface in x- and y-directions, respectively

	Utilized in a multiprocessing function to speed-up the computation
		
	Args:
		DEM_slope_MP_inputs (tuple): a tuple including the following information
			i (int): DEM row index number corresponding to the assigned y-coordinate
			j (int): DEM column index number corresponding to the assigned x-coordinate
			x (float): x-coordinate  
			y (float): y-coordinate  
			DEM (2D numpy array): topography GIS data (elevation data)
			gridUniqueX (1D numpy array): range of grids in x-directions 
			gridUniqueY (1D numpy array): range of grids in y-directions
			local_cell_sizes_slope (int): the size number assigning the local cell region (N x N size)

	Returns:
		i (int): DEM row index number corresponding to the assigned y-coordinate
		j (int): DEM column index number corresponding to the assigned x-coordinate
		dip_deg (float): steepest planar slope in degrees
		aspect_deg (float): azimuth (bearing) angle direction aligned to downward dip inclination in degrees
	"""
	
	i, j, x, y, DEM, gridUniqueX, gridUniqueY, local_cell_sizes_slope = DEM_slope_MP_inputs
	local_xy, local_z = local_cell_v3_2(local_cell_sizes_slope, x, y, DEM, gridUniqueX, gridUniqueY, None)

	# not enought to compute dip or aspect - incrase the local cell size to get approximate dip and aspects
	if len(local_xy) < 4:
		local_xy, local_z = local_cell_v3_2(local_cell_sizes_slope+2, x, y, DEM, gridUniqueX, gridUniqueY, None)

	reg_local = LinearRegression().fit(np.array(local_xy), np.array(local_z))
	DEM_gradients = reg_local.coef_
	# down-slope -> (+); up-slope -> (-)
	dip_deg = np.degrees(np.abs(np.arccos( 1 / np.sqrt(1 + np.power(DEM_gradients[0],2) + np.power(DEM_gradients[1],2) ))))
	# dip_direction_rad = np.arctan2(-DEM_gradients[1], -DEM_gradients[0]) 
	if DEM_gradients[0] == 0.0 and DEM_gradients[1] == 0.0:
		aspect_deg = -1
	else:
		aspect_deg = np.remainder(450-np.degrees(np.arctan2(-DEM_gradients[1], -DEM_gradients[0])), 360)
	return (i, j, dip_deg, aspect_deg)

# overall function to compute the dip and aspects for ground surface and bedrock surface
def compute_dip_aspect(DEM_surface, DEM_base, DEM_soil_thickness, DEM_noData, gridUniqueX, gridUniqueY, local_cell_sizes_slope, dz, cpu_num):
	"""overall function to compute the dip and aspects for ground surface and bedrock surface

	Parameters
	----------
	DEM_surface : 2D numpy array
		GIS data of surface elevation topography
	DEM_base : 2D numpy array
		GIS data of bedrock surface in elevation
	DEM_soil_thickness : 2D numpy array
		GIS data of soil thickness
	DEM_noData : 2D numpy array
		GIS data indicating which regions has noData in ascii file format (0 = noData, 1 = data provided)
	gridUniqueX : 1D numpy array
		range of grids in x-directions 
	gridUniqueY : 1D numpy array
		range of grids in y-directions
	local_cell_sizes_slope : int
		the size number assigning the local cell region (N x N size)
	dz : float
		minimum spacing of wetting front change and slip surface depth to consider 
	cpu_num : int
		CPU multiprocessing number

	Returns
	-------
	dip_surf : 2D numpy array 
		GIS data of ground surface dip
	aspect_surf : 2D numpy array 
		GIS data of ground surface aspect
	dip_base : 2D numpy array 
		GIS data of bedrock surface dip
	aspect_base : 2D numpy array 
		GIS data of bedrock surface aspect
	"""	
	
	dip_surf = np.zeros(DEM_surface.shape)
	aspect_surf = np.zeros(DEM_surface.shape)
	DEM_surf_slope_MP_inputs = []

	uniform_soil_thickness_check = len(np.unique(DEM_soil_thickness))  
	# if uniform soil thickness value, only a single unique soil thickness value is found

	if uniform_soil_thickness_check != 1: 
		dip_base = np.copy(dip_surf)
		aspect_base = np.copy(aspect_surf)
		DEM_base_slope_MP_inputs = []

	for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):	
		xx = gridUniqueX[j]
		yy = gridUniqueY[i]

		# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
		if DEM_soil_thickness[i,j] < dz or DEM_noData[i,j] == 0:
			continue

		# i, j, x, y, DEM, gridUniqueX, gridUniqueY, local_cell_sizes_slope = DEM_slope_MP_inputs
		DEM_surf_slope_MP_inputs.append( (i, j, xx, yy, DEM_surface, gridUniqueX, gridUniqueY, local_cell_sizes_slope) )

		if uniform_soil_thickness_check != 1: 
			DEM_base_slope_MP_inputs.append( (i, j, xx, yy, DEM_base, gridUniqueX, gridUniqueY, local_cell_sizes_slope) )

	pool_DEM_slope = mp.Pool(cpu_num)

	DEM_surf_slope_output_data = pool_DEM_slope.map(DEM_slope_aspect_MP_v3, DEM_surf_slope_MP_inputs)
	# i, j, dip_surf, aspect_surf

	if uniform_soil_thickness_check != 1: 
		DEM_base_slope_output_data = pool_DEM_slope.map(DEM_slope_aspect_MP_v3, DEM_base_slope_MP_inputs)

	pool_DEM_slope.close()
	pool_DEM_slope.join()

	if uniform_soil_thickness_check != 1: 
		for (i,j,dip_s,asp_s),(_,_,dip_b,asp_b) in zip(DEM_surf_slope_output_data, DEM_base_slope_output_data):
			dip_surf[i,j] = dip_s
			aspect_surf[i,j] = asp_s
			dip_base[i,j] = dip_b
			aspect_base[i,j] = asp_b

	else:
		for (i,j,dip_s,asp_s) in DEM_surf_slope_output_data:
			dip_surf[i,j] = dip_s
			aspect_surf[i,j] = asp_s
		dip_base = np.copy(dip_surf)
		aspect_base = np.copy(aspect_surf)

	return dip_surf, aspect_surf, dip_base, aspect_base

def aspect_to_dip_direction(aspect_angle, input_degree=False, output_degree=False):
	if input_degree: 
		filter_to_range = np.remainder(aspect_angle, 360)
		polar_angle = np.where(np.logical_and(filter_to_range >= 0, filter_to_range < 270), 90-filter_to_range, 450-filter_to_range)
		polar_angle = np.where(aspect_angle < 0, np.nan, polar_angle)
	else:
		filter_to_range = np.remainder(np.degrees(aspect_angle), 360)
		polar_angle = np.where(np.logical_and(filter_to_range >= 0, filter_to_range < 270), 90-filter_to_range, 450-filter_to_range)
		polar_angle = np.where(np.degrees(aspect_angle) < 0, np.nan, polar_angle)
		
	if output_degree:
		return polar_angle 
	else:
		return np.radians(polar_angle)

def dip_direction_to_aspect(dip_dir_angle, input_degree=False, output_degree=False):
	if input_degree and output_degree:
		return np.remainder(450-dip_dir_angle, 360)
	elif input_degree == False and output_degree:
		return np.remainder(450-np.degrees(dip_dir_angle), 360)
	elif input_degree and output_degree == False:
		return np.radians(np.remainder(450-dip_dir_angle, 360))
	else:
		return np.radians(np.remainder(450-np.degrees(dip_dir_angle), 360))

######################################################
## SWCC functions
######################################################
####################
## van Genutchen (1980)
####################
# compute volumetric water content (theta) from suction pressure
def SWCC_vG_theta(psi, a, m, theta_s, theta_r, n=None):
	if n is None:
		n = 1/(1-m)
	theta_normal = np.power(1 + np.power(psi/a, n), -m)
	theta = theta_r + theta_normal*(theta_s - theta_r)
	return theta

# compute volumetric water content (theta) from suction pressure
def SWCC_vG_slope(psi, a, m, n=None):
	if n is None:
		n = 1/(1-m)
	dtheta_dpsi = -((m*n)/psi)*np.power(psi/a, n)*np.power(1 + np.power(psi/a, n), -m-1)
	return dtheta_dpsi

# compute vertical hydraulic conductivity (k_z) from suction pressure
def SWCC_vG_k(k_sat, psi, a, m, n=None):
	if n is None:
		n = 1/(1-m)
	return k_sat*(np.power(1 - np.power(a*psi, n-1)*np.power(1 + np.power(a*psi, n), -m), 2)/np.sqrt(1 + np.power(a*psi, n)))

# compute vertical hydraulic conductivity ratio (k_r) from suction pressure
def SWCC_vG_kr(psi, a, m, n=None):
	if n is None:
		n = 1/(1-m)
	return (np.power(1 - np.power(a*psi, n-1)*np.power(1 + np.power(a*psi, n), -m), 2)/np.sqrt(1 + np.power(a*psi, n)))

# compute wetting front suction head (psi_r) - Mein and Farrel (1974); Swartzendruber (1987)
def SWCC_vG_psi_r(psi_i, a, m, int_num=200, n=None):
	if n is None:
		n = 1/(1-m)
	psi_values = np.linspace(0, psi_i, int_num)
	k_r_values = SWCC_vG_kr(psi_values, a, m, n=n)
	psi_f = abs(float(np.trapz(k_r_values, x=psi_values)))
	return psi_f

####################
## Fredlund and Xing (1994)
####################
# compute volumetric water content (theta) from suction pressure
def SWCC_FX_theta(psi, a, n, m, theta_s, C_r=1500, m_v=0):

	C_psi_AEV = 1 - (np.log(1 + (a/C_r))/np.log(1 + (1_000_000/C_r)))
	theta_AEV = (C_psi_AEV*theta_s)/np.power(np.log(np.e + np.power(1, n)), m)
		
	try:	
		C_psi = 1 - (np.log(1 + (psi/C_r))/np.log(1 + (1_000_000/C_r)))
		theta = (C_psi*theta_s)/np.power(np.log(np.e + np.power(psi/a, n)), m)

	except: #  Warning:
		psi_mod = np.where(psi <= a, np.nan, psi)
		C_psi = 1 - (np.log(1 + (psi_mod/C_r))/np.log(1 + (1_000_000/C_r)))
		theta = (C_psi*theta_s)/np.power(np.log(np.e + np.power(psi_mod/a, n)), m)

	# if u_w >= a (above u_w@AEV), then use m_w to increase Vol. water content (theta) until saturated theta (theta_s)
	theta_limit = theta_AEV + m_v*(-psi + a)
	theta_limit = np.where(theta_limit >= theta_s, theta_s, theta_limit)

	theta = np.where(psi <= a, theta_limit, theta)
	return theta

# compute gradient of SWCC curve at psi
def SWCC_FX_slope(psi, a, n, m, theta_s, C_r=1500, m_v=0):

	try:	
		C_psi = 1 - (np.log(1 + (psi/C_r))/np.log(1 + (1_000_000/C_r)))
		dtheta_dpsi = (C_psi*m*n*theta_s*np.power(psi/a, n-1))/(a * (np.e + np.power(psi/a, n)) * np.power(np.log(np.e + np.power(psi/a, n)), m+1))

	except:
		psi_mod = np.where(psi <= a, np.nan, psi)
		C_psi = 1 - (np.log(1 + (psi_mod/C_r))/np.log(1 + (1_000_000/C_r)))
		dtheta_dpsi = (C_psi*m*n*theta_s*np.power(psi_mod/a, n-1))/(a * (np.e + np.power(psi_mod/a, n)) * np.power(np.log(np.e + np.power(psi_mod/a, n)), m+1))


	# compute gradient of SWCC curve at psi AEV
	# gradient is zero when saturated vol. water content (theta_s) is reached
	if m_v > 0:
		dtheta_dpsi = np.where(psi <= a, m_v, dtheta_dpsi)

		theta_comp = SWCC_FX_theta(psi, a, n, m, theta_s, C_r=C_r, m_v=m_v)
		dtheta_dpsi = np.where(theta_comp >= theta_s, 0, dtheta_dpsi)

	elif m_v == 0:
		dtheta_dpsi = np.where(psi <= a, 0, dtheta_dpsi)

	return dtheta_dpsi

# compute vertical hydraulic conductivity (k_z) from suction pressure
def SWCC_FX_k(k_sat, psi, a, n, m, theta_s, C_r=1500, m_v=0, int_num=200):
	
	top_y_values = np.linspace(np.log(max(np.max(psi), a)), np.log(1_000_000), int_num)
	top_values = ((SWCC_FX_theta(np.exp(top_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v) - SWCC_FX_theta(psi, a, n, m, theta_s, C_r=C_r, m_v=m_v))/np.exp(top_y_values))*SWCC_FX_slope(np.exp(top_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v)
	top_trapz_int = np.abs(np.trapz(top_values, top_y_values)).reshape((len(psi),1))

	bottom_y_values = np.linspace(np.log(a), np.log(1_000_000), int_num)
	bottom_values = ((SWCC_FX_theta(np.exp(bottom_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v) - theta_s)/np.exp(bottom_y_values))*SWCC_FX_slope(np.exp(bottom_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v)
	bottom_trapz_int = np.abs(np.trapz(bottom_values, bottom_y_values))

	kr = top_trapz_int/bottom_trapz_int
	kr = np.where(psi <= a, 1, kr)   # saturated beyond AEV

	return k_sat*kr

# compute vertical hydraulic conductivity ratio (k_r) from suction pressure
def SWCC_FX_kr(psi, a, n, m, theta_s, C_r=1500, m_v=0, int_num=200):
	
	top_y_values = np.linspace(np.log(max(np.max(psi), a)), np.log(1_000_000), int_num)
	top_values = ((SWCC_FX_theta(np.exp(top_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v) - SWCC_FX_theta(psi, a, n, m, theta_s, C_r=C_r, m_v=m_v))/np.exp(top_y_values))*SWCC_FX_slope(np.exp(top_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v)
	# top_trapz_int = np.abs(np.trapz(top_values, top_y_values)).reshape((len(psi),1))
	top_trapz_int = np.abs(np.trapz(top_values, top_y_values))

	bottom_y_values = np.linspace(np.log(a), np.log(1_000_000), int_num)
	bottom_values = ((SWCC_FX_theta(np.exp(bottom_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v) - theta_s)/np.exp(bottom_y_values))*SWCC_FX_slope(np.exp(bottom_y_values), a, n, m, theta_s, C_r=C_r, m_v=m_v)
	bottom_trapz_int = np.abs(np.trapz(bottom_values, bottom_y_values))

	kr = top_trapz_int/bottom_trapz_int
	kr = np.where(psi <= a, 1, kr)   # saturated beyond AEV

	return kr

# compute wetting front suction head (psi_r) - Mein and Farrel (1974); Swartzendruber (1987)
def SWCC_FX_psi_r(psi_i, a, n, m, theta_s, C_r=1500, m_v=0, int_num=200):
	psi_values = np.linspace(0, psi_i, int_num)
	k_r_values = SWCC_FX_kr(psi_values, a, n, m, theta_s, C_r=C_r, m_v=m_v, int_num=int_num)
	psi_f = abs(float(np.trapz(k_r_values, x=psi_values)))
	return psi_f

####################
## initial hydro parameter 
####################
# compute initial hydraulic settings
def compute_initial_hydro_DEM_mp_v2(compute_initial_hydraulic_input):
	
	i, j, SWCC_model, psi_initial, SWCC_a, SWCC_n, SWCC_m, theta_s, theta_r, soil_m_v, k_sat_z, rain_i_t0, surf_dip = compute_initial_hydraulic_input

	# SWCC model: "FX" = Fredlund and Xing (1994) - value = 1
	if SWCC_model == 1:
		# initial vol. water content 
		theta_initial = float(SWCC_FX_theta(psi_initial, SWCC_a, SWCC_n, SWCC_m, theta_s, m_v=soil_m_v, C_r=1500))
		# wetting front section head
		psi_r = float(SWCC_FX_psi_r(psi_initial, SWCC_a, SWCC_n, SWCC_m, theta_s, m_v=soil_m_v, C_r=1500, int_num=200))

	# SWCC model: "vG" = van Genutchen (1980) - value = 0
	elif SWCC_model == 0:
		# initial vol. water content 
		theta_initial = float(SWCC_vG_theta(psi_initial, SWCC_a, SWCC_m, theta_s, theta_r, n=SWCC_n))
		# wetting front section head
		psi_r = float(SWCC_vG_psi_r(psi_initial, SWCC_a, SWCC_m, int_num=200, n=SWCC_n))

	# vol. water content deficient
	delta_theta = abs(theta_s - theta_initial)

	## NOTE: ensure we dont get delta_theta = 0 and psi_r = 0, so give a very small value
	delta_theta = np.where(delta_theta <= 1e-6, 1e-6, delta_theta)
	psi_r = np.where(psi_r <= 1e-4, 1e-4, psi_r)

	# when 90 > surf_dip >= 0
	if round(abs(rain_i_t0 - k_sat_z*np.cos(np.radians(surf_dip))), 8) == 0:
		F_p = 0
	else:
		F_p = (psi_r*k_sat_z*delta_theta)/(rain_i_t0 - k_sat_z*np.cos(np.radians(surf_dip)))
	
	if delta_theta == 0:
		z_p = 0
	else:
		z_p = F_p/delta_theta

	if rain_i_t0 == 0:
		T_p = 0
	else:
		T_p = max(F_p/rain_i_t0, 0)
	
	if delta_theta == 0 or psi_r == 0 or 1.0 + (F_p/(psi_r*delta_theta)) <= 0:
		T_pp = 0
	else:
		T_pp = (F_p - psi_r*delta_theta*np.log(1.0 + (F_p/(psi_r*delta_theta))))/k_sat_z

	return (i, j, theta_initial, psi_r, delta_theta, F_p, z_p, T_p, T_pp)

####################
## pore-water pressure 
####################
# this version considers conditions where groundwater level is not at soil_bottom and introduced rounding to avoid floating point issues
# based on elevation Z as array
def u_w_array_round(z_array, gw_z, front_z, z_b, z_t, psi_i, psi_r, gamma_w=9.81, slope_base=None, dz_dp=5, press_dp=4):

	# round to ensure matching of values and not have floating point error issues
	z_array = np.round(z_array, decimals=dz_dp)
	gw_z = round(gw_z, dz_dp)
	front_z = round(front_z, dz_dp)
	z_b = round(z_b, dz_dp)
	z_t = round(z_t, dz_dp)
	psi_i = round(psi_i, press_dp)
	psi_r = round(psi_r, press_dp)


	# infiltration into soil_c and groundwater table at bedrock
	# two layars : (top) saturated by rain, (low) unsaturated
	if front_z > max(z_b, gw_z) and (gw_z <= z_b):
		u_w = np.where(z_array >= front_z, -psi_r, -psi_i)  

	# infiltration into soil_c and groundwater table above bedrock
	# three layars : (top) saturated by rain, (mid) unsaturated, (low) saturated by groundwater table
	elif front_z > max(z_b, gw_z) and (gw_z > z_b):

		# above wetting front elevation 
		u_w = np.where(z_array >= front_z, -psi_r, -psi_i)

		# below the groundwater level
		if isinstance(slope_base, (int, float)):
			fully_sat_u_w = gamma_w*(gw_z-z_array)*(np.cos(np.radians(slope_base))**2)
		else:
			fully_sat_u_w = gamma_w*(gw_z-z_array)
		u_w = np.where(z_array <= gw_z, fully_sat_u_w, u_w)

	# wetting front reached impermeable layer and groundwater level is rising
	# two layars : (top) saturated by rain, (low) saturated by groundwater table
	elif front_z <= max(z_b, gw_z) and (gw_z < z_t):
		if isinstance(slope_base, (int, float)):
			fully_sat_u_w = gamma_w*(gw_z-z_array)*(np.cos(np.radians(slope_base))**2)
		else:
			fully_sat_u_w = gamma_w*(gw_z-z_array)
		fully_sat_u_w_pos = np.where(fully_sat_u_w < 0, 0, fully_sat_u_w)
		u_w = np.where(z_array > gw_z, -psi_r, fully_sat_u_w_pos)  

	# groundwater level increases beyond the ground surface - ponding
	# two layars : (top) ponding by rain, (low) saturated by groundwater table
	elif gw_z >= z_t: 
		if isinstance(slope_base, (int, float)):
			fully_sat_u_w = gamma_w*(gw_z-z_array)*(np.cos(np.radians(slope_base))**2)
		else:
			fully_sat_u_w = gamma_w*(gw_z-z_array)
		u_w = np.where(fully_sat_u_w < 0, 0, fully_sat_u_w)


	return u_w

# this version considers conditions where groundwater level is not at soil_bottom and introduced rounding to avoid floating point issues
# based on elevation Z single value only
def u_w_ind_round(z, gw_z, front_z, z_b, z_t, psi_i, psi_r, gamma_w=9.81, slope_base=None, dz_dp=5, press_dp=4):

	# round to ensure matching of values and not have floating point error issues
	z = round(z, dz_dp)
	gw_z = round(gw_z, dz_dp)
	front_z = round(front_z, dz_dp)
	z_b = round(z_b, dz_dp)
	z_t = round(z_t, dz_dp)
	psi_i = round(psi_i, press_dp)
	psi_r = round(psi_r, press_dp)

	# infiltration into soil_c and groundwater table at bedrock
	# two layars : (top) saturated by rain, (low) unsaturated
	if front_z > max(z_b, gw_z) and (gw_z <= z_b):  # groundwater level close to bedrock level 
		if z >= front_z:
			u_w = -psi_r
		else:
			u_w = -psi_i

	# infiltration into soil_c and groundwater table above bedrock
	# three layars : (top) saturated by rain, (mid) unsaturated, (low) saturated by groundwater table
	elif front_z > max(z_b, gw_z) and (gw_z > z_b):

		# above wetting front elevation 
		if z >= front_z:
			u_w = -psi_r
		
		# below the groundwater level
		elif z <= gw_z:
			if isinstance(slope_base, (int, float)):
				u_w = gamma_w*(gw_z-z)*(np.cos(np.radians(slope_base))**2)
			else:
				u_w = gamma_w*(gw_z-z)

		# between wetting front and groundwater level
		elif z < front_z and z > gw_z:
			u_w = -psi_i

	# wetting front reached impermeable layer and groundwater level is rising
	# two layars : (top) saturated by rain, (low) saturated by groundwater table
	elif front_z <= max(z_b, gw_z) and (gw_z < z_t):

		# above groundwater table -> residual suction
		if z > gw_z:
			u_w = -psi_r

		# below groundwater table -> positive pore-water pressure
		else:
			if isinstance(slope_base, (int, float)):
				u_w = max(gamma_w*(gw_z-z)*(np.cos(np.radians(slope_base))**2), 0)  # lateral groundwater flow
			else:
				u_w = max(gamma_w*(gw_z-z), 0)

	# groundwater level increases beyond the ground surface - ponding
	# two layars : (top) ponding by rain, (low) saturated by groundwater table
	elif gw_z >= z_t: 
		if isinstance(slope_base, (int, float)):
			u_w = max(gamma_w*(gw_z-z)*(np.cos(np.radians(slope_base))**2), 0)   # lateral groundwater flow
		else:
			u_w = max(gamma_w*(gw_z-z), 0)

	return u_w

######################################################
## Green-ampt infiltration functions
######################################################
## the definite version that works for both uniform and non-uniform rainfall intensities
def GA_F_slanted_iter_noF0comp(Ft, F0, k_sat, delta_time, psi_ff, delta_thetas, dip_beta_deg):
	if dip_beta_deg >= 90:
		return F0
	else:
		return k_sat*np.cos(np.radians(dip_beta_deg))*delta_time + ((psi_ff*delta_thetas)/np.cos(np.radians(dip_beta_deg)))*np.log(1.0 + ((Ft*np.cos(np.radians(dip_beta_deg)))/(psi_ff*delta_thetas)))

def GA_F_slanted_iter_noF0comp_timePondingDuring(t_all, F0, S0, t0, tp, tpp, rain_I, k_sat, psi_ff, delta_thetas, dip_beta_deg):
	if dip_beta_deg >= 90 or rain_I == 0:
		return -1
	else:
		return (k_sat*np.cos(np.radians(dip_beta_deg))*(t_all - tp + tpp) - (F0 + S0 - t0*rain_I)*np.cos(np.radians(dip_beta_deg)) + ((psi_ff*delta_thetas)/np.cos(np.radians(dip_beta_deg)))*np.log(1.0 + (((F0 + S0 + (t_all - t0)*rain_I)*np.cos(np.radians(dip_beta_deg)))/(psi_ff*delta_thetas))))/rain_I

def compute_GA_nonUniRain_slanted_MP(compute_GA_slanted_nonUniRain_input):
	
	i, j, z_top, z_bottom, z_length, infil_zw_pre, wetting_front_z_pre, gwt_z_pre, rain_I, k_sat_z, cur_t, dt, T_p, T_pp, delta_theta, psi_r, infil_cumul_F_pre, slope_beta_deg, P_pre, S_pre, RO_pre, infil_rate_f_pre, S_max, cumul_dp, t_dp, rate_dp, dz_dp = compute_GA_slanted_nonUniRain_input
	'''
	rate_dp 	# rate - f, I
	t_dp    	# time
	cumul_dp    # F, S, RO, P 
	dz_dp 		# vertical size 
	'''

	## check whether the infiltration situation is ponding or not at the cur_t
	if infil_cumul_F_pre > 0 and (cur_t - T_p + T_pp) > 0:
		try:
			# during-ponding check
			time_all_infil = round(float(fixed_point(GA_F_slanted_iter_noF0comp_timePondingDuring, cur_t, args=(infil_cumul_F_pre, S_pre, cur_t-dt, T_p, T_pp, rain_I, k_sat_z, psi_r, delta_theta, slope_beta_deg), xtol=0.05)), t_dp)
			if time_all_infil == -1 or time_all_infil < (cur_t-dt):
				time_all_infil = 1e9
		except: # when it does not converge
			time_all_infil = 1e9
	else:
		time_all_infil = 1e9

	#############################
	## infiltration
	#############################
	# wetting front did not reach the bedrock layer
	if wetting_front_z_pre > max(z_bottom, gwt_z_pre):

		#############################
		## infiltration based on rainfall intensity (i) vs saturated hydraulic conductivity (k_sat_z)
		#############################
		# no ponding should be occurring at initial (all infiltrates into ground) or ponding will occur but time < T_p-T_pp or time > (time required to infiltrate until surface pond is 0)
		if (S_pre == 0 and rain_I*np.cos(np.radians(slope_beta_deg)) <= max(k_sat_z,infil_rate_f_pre)) or ((S_pre > 0 or rain_I*np.cos(np.radians(slope_beta_deg)) > max(k_sat_z,infil_rate_f_pre)) and (((cur_t - T_p + T_pp) <= 0) or (time_all_infil <= cur_t))):

			# infiltration 
			infil_rate_f_new = rain_I*np.cos(np.radians(slope_beta_deg))
			infil_cumul_F_new = infil_cumul_F_pre + rain_I*np.cos(np.radians(slope_beta_deg))*dt
			infil_zw_new = infil_zw_pre + ((rain_I*np.cos(np.radians(slope_beta_deg))*dt)/delta_theta)
			wetting_front_z_new = z_top - infil_zw_new

			# if reached the groundwater level between dt
			if wetting_front_z_new <= gwt_z_pre:					
				# change of groundwater table level = infiltration rate (m/s) * s = change in infil_cumul_F
				gwt_z_new = gwt_z_pre + abs(wetting_front_z_new - gwt_z_pre)
				infil_zw_new = z_length
				wetting_front_z_new = z_bottom
			else:
				gwt_z_new = gwt_z_pre

			# water balance
			if infil_cumul_F_pre > 0:
				P_change = rain_I*dt
			else:
				if dt <= T_p:
					P_change = rain_I*dt
				else:
					P_change = rain_I*(dt - T_p)
			P_new = P_pre + P_change

			F_change = infil_cumul_F_new - infil_cumul_F_pre
			
			excess_water = P_change - F_change
			if excess_water == 0:  # no excess
				S_new = S_pre
				RO_new = RO_pre
			elif (excess_water > 0):  # excess water on surface
				if (excess_water+S_pre <= S_max): # first fill up the surface storage
					S_new = excess_water + S_pre
					RO_new = RO_pre
				else:  # excess water exceeds the capability of the surface storage
					S_new = S_max
					RO_new = RO_pre + max(excess_water - S_max, 0)
			elif (excess_water < 0):  	# more infiltration into the soil - decreasing ponding
				S_new = max(S_pre + excess_water, 0)
				RO_new = RO_pre

		# ponding needs to be considered for the rainfall infiltration
		elif ((S_pre > 0 or rain_I*np.cos(np.radians(slope_beta_deg)) > max(k_sat_z,infil_rate_f_pre)) and (((cur_t - T_p + T_pp) > 0) or (time_all_infil > cur_t))):

			# compute cumulative rainfall amount
			infil_cumul_F_new = float(fixed_point(GA_F_slanted_iter_noF0comp, infil_cumul_F_pre, args=(infil_cumul_F_pre, k_sat_z, cur_t - T_p + T_pp, psi_r, delta_theta, slope_beta_deg), xtol=1e-4))

			# compute rainfall infiltration rate
			infil_rate_f_new = k_sat_z*(1 + (psi_r*delta_theta)/infil_cumul_F_new)

			# compute new wetting front depth
			infil_zw_new = infil_zw_pre + ((infil_cumul_F_new - infil_cumul_F_pre)/delta_theta)

			wetting_front_z_new = z_top - infil_zw_new

			# if reached the groundwater level between dt
			if wetting_front_z_new <= gwt_z_pre:					
				# change of groundwater table level = infiltration rate (m/s) * s = change in infil_cumul_F
				gwt_z_new = gwt_z_pre + abs(wetting_front_z_new - gwt_z_pre)
				infil_zw_new = z_length
				wetting_front_z_new = z_bottom
			else:
				gwt_z_new = gwt_z_pre
			
			# water balance
			if infil_cumul_F_pre > 0:
				P_change = rain_I*dt
			else:
				if dt <= T_p:
					P_change = rain_I*dt
				else:
					P_change = rain_I*(dt - T_p)
			P_new = P_pre + P_change

			F_change = infil_cumul_F_new - infil_cumul_F_pre
			
			excess_water = P_change - F_change
			if excess_water == 0:  # no excess
				S_new = S_pre
				RO_new = RO_pre
			elif (excess_water > 0):  # excess water on surface
				if (excess_water+S_pre <= S_max): # first fill up the surface storage
					S_new = excess_water + S_pre
					RO_new = RO_pre
				else:  # excess water exceeds the capability of the surface storage
					S_new = S_max
					RO_new = RO_pre + max(excess_water + S_pre - S_max, 0)
			elif (excess_water < 0):  	# more infiltration into the soil - decreasing ponding
				S_new = max(S_pre + excess_water, 0)
				RO_new = RO_pre

	# infiltration reached the impermeable bedrock layer
	# and groundwater table layer did not reach the ground surface
	elif wetting_front_z_pre <= max(z_bottom, gwt_z_pre) and gwt_z_pre < z_top:
		
		infil_zw_new = z_length
		wetting_front_z_new = z_bottom

		# if ponding is present when the wetting front has reached the groundwater table (all are saturated), the infiltration rate will be k_sat
		if S_pre > 0:
			infil_rate_f_new = k_sat_z
		# if no ponding present, then the infilatrion rate will be smaller of rainfall intensity and saturated pearmeability
		else:
			infil_rate_f_new = min(rain_I*np.cos(np.radians(slope_beta_deg)), k_sat_z)

		infil_cumul_F_new = infil_cumul_F_pre + infil_rate_f_new*dt

		# change of groundwater table level = infiltration rate (m/s) * s = change in infil_cumul_F
		gwt_z_new = gwt_z_pre + infil_rate_f_new*dt			

		# water balance
		P_change = rain_I*dt
		P_new = P_pre + P_change

		F_change = infil_cumul_F_new - infil_cumul_F_pre

		excess_water = P_change - F_change
		if excess_water == 0:  # no excess
			S_new = S_pre
			RO_new = RO_pre
		elif (excess_water > 0):  # excess water on surface
			if (excess_water+S_pre <= S_max): # first fill up the surface storage
				S_new = excess_water + S_pre
				RO_new = RO_pre
			else:  # excess water exceeds the capability of the surface storage
				S_new = S_max
				RO_new = RO_pre + (excess_water - S_max)
		elif (excess_water < 0):  	# more infiltration into the soil - decreasing ponding
			S_new = max(S_pre + excess_water, 0)
			RO_new = RO_pre

	# groundwater table layer reached the ground surface - no longer infiltration but ponding
	elif gwt_z_pre >= z_top:
		
		infil_zw_new = z_length
		wetting_front_z_new = z_bottom
		infil_rate_f_new = rain_I
		infil_cumul_F_new = infil_cumul_F_pre
		# no more infiltration into soil F_change = 0

		# change of groundwater table level = infiltration rate (m/s) * s = change in infil_cumul_F
		# groundwater level = ponding depth + ground_surface
		# limit the groundwater level on top as S_max -> rest all becomes runoff
		gwt_z_new = min(gwt_z_pre + rain_I*dt, z_top + S_max)

		# water balance
		P_change = rain_I*dt
		P_new = P_pre + P_change

		# limit the groundwater level on top as S_max -> rest all becomes runoff
		S_new = min(gwt_z_new - z_top, S_max)
		S_change = S_new - S_pre

		# Runoff 
		# RO_change = P_change - F_change(=0) - S_change
		RO_new = RO_pre + max(P_change - S_change, 0)

	# rounding to nearest tolerance number - avoid floating point error
	P_new = round(P_new, cumul_dp)
	S_new = round(S_new, cumul_dp)
	RO_new = round(RO_new, cumul_dp)
	infil_cumul_F_new = round(infil_cumul_F_new, cumul_dp)
	infil_rate_f_new = round(infil_rate_f_new, rate_dp)
	gwt_z_new = round(gwt_z_new, dz_dp)
	infil_zw_new = round(infil_zw_new, dz_dp)
	wetting_front_z_new = round(wetting_front_z_new, dz_dp)

	return (i, j, P_new, S_new, RO_new, infil_cumul_F_new, infil_rate_f_new, gwt_z_new, infil_zw_new, wetting_front_z_new)

######################################################
## infinite slope stability function
######################################################
## The definite version for inifinite slope stability analysis
# find critical depth (depth of shallow landslide failure) for given critical FS
# use phi_b for unsaturated shear strength, distinguish between phi from MC
def critical_depth_inf_FS_MP(critical_depth_inf_FS_MP_input):

	# open up inputs
	i, j, z_b, z_t, phi, phi_b, c, gamma_s, alpha, gw_z, front_z, psi_i, psi_r, FS_crit, gamma_w, dz, check_only, dz_dp, press_dp = critical_depth_inf_FS_MP_input

	# output - i, j, failure_soil_thickness_t0, min_comp_FS_t0

	# too thin soil layer or no soil thickness data
	if abs(z_b-z_t) <= dz:
		if check_only:
			return False
		else:
			# return i, j, crit_FS_z_min, float(min_crit_FS), FS_values, u_w_values
			return i, j, 0.0, 10.0   # , FS_values, u_w_values

	# get incremental soil depths
	z_values = np.arange(z_b, z_t, dz)
	z_values = z_values[z_values < z_t]  # ensure the last value is z_t

	# compute pore-water pressure
	u_w_values = u_w_array_round(z_values, gw_z, front_z, z_b, z_t, psi_i, psi_r, gamma_w=gamma_w, slope_base=alpha, dz_dp=dz_dp, press_dp=press_dp)

	# soil tickness for each depths
	soil_thickness = z_t*np.ones(len(z_values),) - z_values

	# convert degree to radians
	phi_rad = np.radians(phi) 	
	phi_b_val_rad = np.where(u_w_values < 0, np.radians(phi_b), np.radians(phi))  	## unsaturated soil friction angle

	alpha_rad = np.radians(alpha)
	alpha_rad_non_zero = np.where(alpha_rad == 0, np.radians(0.1), alpha_rad)   # give very small slope (0.1 deg) instead of zero

	# total unit weight
	total_weight_stress = gamma_s*soil_thickness

	# add water weight when ponding occurs
	if gw_z > z_t:
		total_weight_stress += (gw_z - z_t)*gamma_w

	comp_FS_values = (c + total_weight_stress*np.power(np.cos(alpha_rad_non_zero),2)*np.tan(phi_rad) -  u_w_values*np.tan(phi_b_val_rad) )/(total_weight_stress*np.sin(alpha_rad_non_zero)*np.cos(alpha_rad_non_zero))
	FS_values = np.where(comp_FS_values <= 0, 0, comp_FS_values)
	
	crit_FS = np.where(FS_values <= FS_crit, 1, 0)

	if np.sum(crit_FS) == 0:
		# no FS failure
		if check_only:
			return False
		else:
			min_FS = np.amin(FS_values)
			# return i, j, np.nan, float(min_FS), FS_values, u_w_values
			# return i, j, np.nan, float(min_FS)  #, FS_values, u_w_values
			return i, j, 0.0, max(float(min_FS), 0.0)  # assume no failure when all FS > FS_crit, so no failure depth

	elif np.sum(crit_FS) > 0:
		min_crit_FS = np.amin(FS_values)

		# crit_FS_idx = [idx for idx, FSi in enumerate(FS_values) if FSi == min_crit_FS]
		crit_FS_idx = [idx for idx, FSi in enumerate(FS_values) if FSi <= FS_crit]
		crit_FS_z = [z_values[idx] for idx in crit_FS_idx]

		# assume failure occurs at the deepest layer if multiple failure occurs at depths
		crit_FS_z_min = min(crit_FS_z)  

		failure_soil_thickness = z_t - crit_FS_z_min

		if check_only:
			return True
		else:
			# return i, j, crit_FS_z_min, float(min_crit_FS), FS_values, u_w_values
			return i, j, failure_soil_thickness, max(float(min_crit_FS), 0.0)    # , FS_values, u_w_values

######################################################
## 3D slope stability function
######################################################
## generate all 3DTS slip surfaces in seperate functions
## generate local slip surfaces (plan-view) using superellipse shape
def generate_local_superellipse_grouping_v1_00(group_side_N_min, group_side_N_max, n_param, x_a_y_b_ratio):

	###########################################################
	## generate local slip surfaces
	###########################################################

	## compute all groupings of local slip surfaces
	group_side_slip_surf_grouping = {}   # key = N size, value = [ [[local_row_y], [local_col_x]], ...]

	for group_side_N in range(group_side_N_min, group_side_N_max+1):

		###########################################################
		## local DEM
		###########################################################
		# local grouping size
		# group_side_N = 3

		# DEM local NxN grid
		local_grid_num = np.arange(int(group_side_N**2)).reshape((group_side_N, group_side_N))
		local_x_grid = np.arange(group_side_N)
		local_y_grid = np.arange(group_side_N)

		# centroid
		c_x = np.median(local_x_grid)
		c_y = np.median(local_y_grid)

		# centralized - centroid to equal to index (0,0)
		local_x_grid = local_x_grid - c_x
		local_y_grid = local_y_grid - c_y
		local_xv, local_yv = np.meshgrid(local_x_grid, local_y_grid)

		# max radius
		max_radius = 0.5*group_side_N

		x_a_y_b_pair = [(max_radius, max_radius)]
		x_a_y_b_pair.extend([(max_radius, max_radius*round(1/rr,5)) for rr in x_a_y_b_ratio])
		x_a_y_b_pair.extend([(round(1/rr,5)*max_radius, max_radius) for rr in x_a_y_b_ratio])

		###########################################################
		## slip surface grouping
		###########################################################
		## super-ellipse equations
		# https://en.wikipedia.org/wiki/Superellipse

		# abs(x/x_a)**n + abs(y/y_b)**n = 1
		# if abs(x/x_a)**n + abs(y/y_b)**n < 1, the (x,y) is inside the boundary
		# if abs(x/x_a)**n + abs(y/y_b)**n > 1, the (x,y) is outside the boundary

		# given theta (polar angle), the radius to the boundary edge is computed as:
		# r = ((abs(np.cos(theta)/x_a)**n) + (abs(np.sin(theta)/y_b)**n))**(-1/n)
			
		all_super_ellipse_data = []  # [ [[local_row_y], [local_col_x]], ...]
		inside_cell_num_track = []   # used to prevent repeating local slip surface groupings 

		for nn, (xa, yb) in itertools.product(n_param, x_a_y_b_pair):

			## check which grid cell is included for each super-ellipse
			"""
			it is included if the area is at least half inside the polygon
			this can be checked by computing the distance of the cell centroid to the polygon centroid 
			if abs(x/x_a)**n + abs(y/y_b)**n <= 1, the (x,y) is inside (<1) or touching (=1) the boundary edges
			"""
			sup_ell_cell_r = np.abs((local_xv)/xa)**nn + np.abs((local_yv)/yb)**nn  # centroid is at (0,0)

			inside_row_y_idx, inside_col_x_idx = np.where(sup_ell_cell_r <= 1)  
			# index in x,y that are inside the boundary

			inside_cell_num = sorted([local_grid_num[rowy,colx] for rowy,colx in zip(inside_row_y_idx, inside_col_x_idx)])

			# only add if non-repeating (tabu search)
			# only include if at least single cell is selected
			# only if either row or column has length equal to the local grid size N
			if ((len(all_super_ellipse_data) == 0) or ((len(all_super_ellipse_data) > 0) and (inside_cell_num not in inside_cell_num_track))) and len(inside_cell_num) > 0 and (len(np.unique(inside_row_y_idx))>=group_side_N or len(np.unique(inside_col_x_idx))>=group_side_N):

				inside_row_y_val = local_y_grid[inside_row_y_idx]
				inside_col_x_val = local_x_grid[inside_col_x_idx]

				all_super_ellipse_data.append([inside_row_y_val.tolist()[:], inside_col_x_val.tolist()[:]])
				inside_cell_num_track.append(inside_cell_num)

		group_side_slip_surf_grouping[group_side_N] = all_super_ellipse_data

	return group_side_slip_surf_grouping

# add rotation to superellipse groupings
def generate_local_superellipse_grouping_v1_10(group_side_N_min, group_side_N_max, n_param, x_a_y_b_ratio):

	###########################################################
	## generate local slip surfaces
	###########################################################

	## compute all groupings of local slip surfaces
	group_side_slip_surf_grouping = {}   # key = N size, value = [ [[local_row_y], [local_col_x]], ...]

	for group_side_N in range(group_side_N_min, group_side_N_max+1):

		###########################################################
		## local DEM
		###########################################################
		# local grouping size
		# group_side_N = 3

		# DEM local NxN grid
		local_grid_num = np.arange(int(group_side_N**2)).reshape((group_side_N, group_side_N))
		local_x_grid = np.arange(group_side_N)
		local_y_grid = np.arange(group_side_N)

		# centroid
		c_x = np.median(local_x_grid)
		c_y = np.median(local_y_grid)

		# centralized - centroid to equal to index (0,0)
		local_x_grid = local_x_grid - c_x
		local_y_grid = local_y_grid - c_y
		local_xv, local_yv = np.meshgrid(local_x_grid, local_y_grid)

		# max radius
		max_radius = 0.5*group_side_N

		x_a_y_b_pair = [(max_radius, max_radius)]
		x_a_y_b_pair.extend([(max_radius, max_radius*round(1/rr,5)) for rr in x_a_y_b_ratio])
		x_a_y_b_pair.extend([(round(1/rr,5)*max_radius, max_radius) for rr in x_a_y_b_ratio])

		# rotation angle - every 30 degree, but include 45 degree
		rotation_rad_angle = [-0.5*np.pi, -0.3333*np.pi, -0.25*np.pi, -0.1667*np.pi, 0.0, 0.1667*np.pi, 0.25*np.pi, 0.3333*np.pi]

		###########################################################
		## slip surface grouping
		###########################################################
		## super-ellipse equations
		# https://en.wikipedia.org/wiki/Superellipse

		# abs(x/x_a)**n + abs(y/y_b)**n = 1
		# if abs(x/x_a)**n + abs(y/y_b)**n < 1, the (x,y) is inside the boundary
		# if abs(x/x_a)**n + abs(y/y_b)**n > 1, the (x,y) is outside the boundary

		# given theta (polar angle), the radius to the boundary edge is computed as:
		# r = ((abs(np.cos(theta)/x_a)**n) + (abs(np.sin(theta)/y_b)**n))**(-1/n)
			
		all_super_ellipse_data = []  # [ [[local_row_y], [local_col_x]], ...]
		inside_cell_num_track = []   # used to prevent repeating local slip surface groupings 

		for (nn, (xa, yb), rot_rad) in itertools.product(n_param, x_a_y_b_pair, rotation_rad_angle):

			## check which grid cell is included for each super-ellipse
			"""
			it is included if the area is at least half inside the polygon
			this can be checked by computing the distance of the cell centroid to the polygon centroid 
			if abs(x/x_a)**n + abs(y/y_b)**n <= 1, the (x,y) is inside (<1) or touching (=1) the boundary edges
			instead of rotating the superellipse, rotate the XY-coordinates in the opposite direction
			"""
			local_rot_xv = local_xv*np.cos(-rot_rad) - local_yv*np.sin(-rot_rad)
			local_rot_yv = local_xv*np.sin(-rot_rad) + local_yv*np.cos(-rot_rad)

			# sup_ell_cell_r = np.abs((local_xv)/xa)**nn + np.abs((local_yv)/yb)**nn  # centroid is at (0,0)

			# threshold = 2e-300 * (10**nn)
			# local_rot_xv[np.abs(local_rot_xv) < threshold] = 0
			# local_rot_yv[np.abs(local_rot_yv) < threshold] = 0

			sup_ell_cell_r = np.abs((local_rot_xv)/xa)**nn + np.abs((local_rot_yv)/yb)**nn  # centroid is at (0,0)

			inside_row_y_idx, inside_col_x_idx = np.where(sup_ell_cell_r <= 1) 
			# index in x,y that are inside the boundary

			inside_cell_num = sorted([local_grid_num[rowy,colx] for rowy,colx in zip(inside_row_y_idx, inside_col_x_idx)])

			# find longest length - diagonal length
			longest_length = np.ceil(np.sqrt(len(np.unique(inside_col_x_idx))**2 + len(np.unique(inside_row_y_idx))**2))

			# only add if non-repeating (tabu search)
			# only include if at least single cell is selected
			# only if either row or column has length equal to the local grid size N or (diagonal length bigger than grid size N - relevent when 1 <= power_n < 2)
			if ((len(all_super_ellipse_data) == 0) or ((len(all_super_ellipse_data) > 0) and (inside_cell_num not in inside_cell_num_track))) and len(inside_cell_num) > 0 and (len(np.unique(inside_row_y_idx))>=group_side_N or len(np.unique(inside_col_x_idx))>=group_side_N or longest_length>=group_side_N):

				inside_row_y_val = local_y_grid[inside_row_y_idx]
				inside_col_x_val = local_x_grid[inside_col_x_idx]

				all_super_ellipse_data.append([inside_row_y_val.tolist()[:], inside_col_x_val.tolist()[:]])
				inside_cell_num_track.append(inside_cell_num)

		group_side_slip_surf_grouping[group_side_N] = all_super_ellipse_data

	return group_side_slip_surf_grouping

## simply generate DEM cell groupings in global coordinates 
def generate_global_superellipse_grouping_MP_v1_00(generate_global_superellipse_slip_surface_input):

	# expand inputs
	g_row_y, g_col_x, group_side_N_min, group_side_N_max, group_side_slip_surf_grouping, len_DEM_y_grid, len_DEM_x_grid, DEM_grid_num = generate_global_superellipse_slip_surface_input

	# all_slip_surf_data_temp = []
	slip_surf_track_temp = []

	for group_side_N in range(group_side_N_min, group_side_N_max+1):

		# single cell - automatically add 
		if group_side_N == 1: 
			# all_slip_surf_data_temp.append([(g_row_y, g_col_x)])
			slip_surf_track_temp.append(int(DEM_grid_num[g_row_y, g_col_x]))		# for grouping uniqueness

		# odd number size local cells
		# the centroid cell is the centroid of the slip surface grouping
		elif (group_side_N%2) == 1:
			local_slip_grouping = group_side_slip_surf_grouping[group_side_N][:]

			for local_loop in range(len(local_slip_grouping)):
				# get slip surface grouping in global index
				inside_row_y_global_idx = g_row_y + np.array(local_slip_grouping[local_loop][0])
				inside_col_x_global_idx = g_col_x + np.array(local_slip_grouping[local_loop][1])

				inside_col_x_global_idx = inside_col_x_global_idx.astype(int)
				inside_row_y_global_idx = inside_row_y_global_idx.astype(int)

				# truncate cell that goes outside the DEM boundary
				# truncated_inside_row_y_col_x_global_idx = []
				slip_surf_track_temp2 = []   	# generate involved cell numbers
				for rowy,colx in zip(inside_row_y_global_idx, inside_col_x_global_idx):
					if (rowy >= 0 and rowy < len_DEM_y_grid) and (colx >= 0 and colx < len_DEM_x_grid):
						# truncated_inside_row_y_col_x_global_idx.append((rowy, colx))
						slip_surf_track_temp2.append(DEM_grid_num[rowy, colx])

				# all_slip_surf_data_temp.append(truncated_inside_row_y_col_x_global_idx[:])
				slip_surf_track_temp.append(tuple(sorted(slip_surf_track_temp2)))
				# slip_surf_track_temp.append(list(sorted(slip_surf_track_temp2)))

		# even number size local cells
		elif (group_side_N%2) == 0:
			local_slip_grouping = group_side_slip_surf_grouping[group_side_N][:]

			# use the midway between gridline as centroids -> left-bottom, left-top, right-top, right-bottom
			centroid_cell_corners_add = [(-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (0.5, -0.5)]

			for corner_g_x_add, corner_g_y_add in centroid_cell_corners_add:
				for local_loop in range(len(local_slip_grouping)):
					# get slip surface grouping in global index
					inside_row_y_global_idx = g_row_y + corner_g_y_add + np.array(local_slip_grouping[local_loop][0])
					inside_col_x_global_idx = g_col_x + corner_g_x_add + np.array(local_slip_grouping[local_loop][1])

					inside_col_x_global_idx = inside_col_x_global_idx.astype(int)
					inside_row_y_global_idx = inside_row_y_global_idx.astype(int)

					# truncate cell that goes outside the DEM boundary
					# truncated_inside_row_y_col_x_global_idx = []
					slip_surf_track_temp2 = []   	# generate involved cell numbers
					for rowy,colx in zip(inside_row_y_global_idx, inside_col_x_global_idx):
						if (rowy >= 0 and rowy < len_DEM_y_grid) and (colx >= 0 and colx < len_DEM_x_grid):
							# truncated_inside_row_y_col_x_global_idx.append((rowy, colx))
							slip_surf_track_temp2.append(DEM_grid_num[rowy, colx])

					# all_slip_surf_data_temp.append(truncated_inside_row_y_col_x_global_idx[:])
					slip_surf_track_temp.append(tuple(sorted(slip_surf_track_temp2)))
					# slip_surf_track_temp.append(list(sorted(slip_surf_track_temp2)))

	# return g_row_y, g_col_x, all_slip_surf_data_temp, slip_surf_track_temp
	return slip_surf_track_temp


## taking the superellipse shapes, generate slip surface soil cell data
def generate_3DTS_slip_groupings_mp_v3_00(generate_slip_surface_cell_input):

	unique_slip_surface_i, DEM_grid_num, DEM_surface, DEM_soil_thickness, dip_base_deg, aspect_base_deg, DEM_gwt_z, DEM_wetting_front_z, DEM_psi_r, DEM_initial_suction, DEM_soil_unit_weight, DEM_soil_phi, DEM_soil_phi_b, DEM_soil_c, DEM_root_unit_weight, DEM_root_c_base, DEM_root_c_side, DEM_root_depth, DEM_root_alpha2, DEM_root_beta2, DEM_root_RR_max = generate_slip_surface_cell_input
	
	################################################################
	### get non-repeating superellipse groupings DEM cells
	################################################################
	## sort results into files
	truncated_inside_row_y_col_x_global_idx = []
	if isinstance(unique_slip_surface_i, (tuple, list)):
		for cell_num in unique_slip_surface_i:
			rowy,colx = np.where(DEM_grid_num == cell_num)
			truncated_inside_row_y_col_x_global_idx.append((int(rowy[0]),int(colx[0])))
	elif isinstance(unique_slip_surface_i, (int, float)):
		rowy,colx = np.where(DEM_grid_num == unique_slip_surface_i)
		truncated_inside_row_y_col_x_global_idx.append((int(rowy[0]),int(colx[0])))

	# list to store data
	local_ext_id = []    # external column determined based on neighboring cells 
	
	local_z_b = []		# bottom elevation
	local_z_t = [] 		# top elevation

	local_gw_z = []		# groundwater elevation 
	local_front_z = []	# wetting front elevation
	local_psi_r = []	# residual suction
	local_psi_i = []	# initial suction (from material)

	local_base_dip_rad = []			 # dip (radians)
	local_base_aspect_rad = []  	 # aspect (polar coords) in radians

	local_gamma_s = []			# soil unit weight
	local_phi_eff_rad = []		# effective friction angle
	local_phi_b_rad = []		# unsaturated friction angle
	local_c = []				# effective cohesion

	local_root_gamma_s = []		# root unit weight
	local_root_c_base = []		# root base cohesion
	local_root_c_side = []		# root side cohesion
	local_root_depth = []		# root depth (from surface)

	local_root_alpha2 = []		# root strength alpha2 parameter
	local_root_beta2 = []		# root strength beta2 parameter
	local_root_RR_max = []		# root strength max

	for (t_y_row, t_x_col) in truncated_inside_row_y_col_x_global_idx:

		########################################################################
		## local_ext_id 
		########################################################################
		## existing labeling system
		# 1 = interior,
		# 20 = one-side exterior with x-axis side, (closer to x_min) = no neighboring cell at left
		# 21 = one-side exterior with x-axis side, (closer to x_max) = no neighboring cell at right
		# 30 = one-side exterior with y-axis side, (closer to y_min) = no neighboring cell at bottom
		# 31 = one-side exterior with y-axis side, (closer to y_max) = no neighboring cell at top
		# 400 = two-sides exterior (corner) one x-axis and one y-axis sides (closer to x_min and y_min) = no neighboring cell at left and bottom
		# 401 = two-sides exterior (corner) one x-axis and one y-axis sides (closer to x_min and y_max) = no neighboring cell at left and top
		# 410 = two-sides exterior (corner) one x-axis and one y-axis sides (closer to x_max and y_min) = no neighboring cell at right and bottom
		# 411 = two-sides exterior (corner) one x-axis and one y-axis sides (closer to x_max and y_max) = no neighboring cell at right and top
  		# 420 = no neighboring cell at left and right
		# 402 = no neighboring cell at bottom and top
		# 502 = three-sides exterior = no neighboring cell at left, top, bottom
		# 512 = three-sides exterior = no neighboring cell at right, top, bottom
		# 520 = three-sides exterior = no neighboring cell at left, right, bottom
		# 521 = three-sides exterior = no neighboring cell at left, right, top
		# 6 = four-sides exterior two x-axis and two y-axis sides = single cell 

		## ext soil column id
		grid_type_factor = 1  # centroid thing does not matter anymore

		## check what types of neighboring cells exist (von Neumann neighborhood)
		bottom_top_left_right = [0, 0, 0, 0]  	# 1 = neighbor exist, 0 = nothing there
		if (int(t_y_row-1), t_x_col) in truncated_inside_row_y_col_x_global_idx:  # bottom
			bottom_top_left_right[0] = 1
		if (int(t_y_row+1), t_x_col) in truncated_inside_row_y_col_x_global_idx:  # top
			bottom_top_left_right[1] = 1
		if (t_y_row, int(t_x_col-1)) in truncated_inside_row_y_col_x_global_idx:  # left
			bottom_top_left_right[2] = 1
		if (t_y_row, int(t_x_col+1)) in truncated_inside_row_y_col_x_global_idx:  # right
			bottom_top_left_right[3] = 1

		## 4-sides exterior 
		if sum(bottom_top_left_right) == 0: 
			local_ext_id.append(grid_type_factor*6)

		## 3-sides exterior
		# 502 = no neighboring cell at left, top, bottom
		# 512 = no neighboring cell at right, top, bottom
		# 520 = no neighboring cell at left, right, bottom
		# 521 = no neighboring cell at left, right, top
		elif sum(bottom_top_left_right) == 1:
			if bottom_top_left_right == [0,0,0,1]:
				local_ext_id.append(grid_type_factor*502)

			elif bottom_top_left_right == [0,0,1,0]:
				local_ext_id.append(grid_type_factor*512)

			elif bottom_top_left_right == [0,1,0,0]:
				local_ext_id.append(grid_type_factor*520)

			elif bottom_top_left_right == [1,0,0,0]:
				local_ext_id.append(grid_type_factor*521)

		# 2-sides exterior
		elif sum(bottom_top_left_right) == 2:
			## corners (2-sides)
			# 400 = no neighboring cell at left and bottom
			# 401 = no neighboring cell at left and top
			# 410 = no neighboring cell at right and bottom
			# 411 = no neighboring cell at right and top
			if bottom_top_left_right == [0,1,0,1]:
				local_ext_id.append(grid_type_factor*400)

			elif bottom_top_left_right == [1,0,0,1]:
				local_ext_id.append(grid_type_factor*401)

			elif bottom_top_left_right == [0,1,1,0]:
				local_ext_id.append(grid_type_factor*410)

			elif bottom_top_left_right == [1,0,1,0]:
				local_ext_id.append(grid_type_factor*411)

			## two parallel edges (2-sides)
			# 420 = no neighboring cell at left and right
			# 402 = no neighboring cell at bottom and top
			elif bottom_top_left_right == [1,1,0,0]:
				local_ext_id.append(grid_type_factor*420)

			elif bottom_top_left_right == [0,0,1,1]:
				local_ext_id.append(grid_type_factor*402)

		## one edge (1-side)
		# 20 = one-side exterior with x-axis side, (closer to x_min) = no neighboring cell at left
		# 21 = one-side exterior with x-axis side, (closer to x_max) = no neighboring cell at right
		# 30 = one-side exterior with y-axis side, (closer to y_min) = no neighboring cell at bottom
		# 31 = one-side exterior with y-axis side, (closer to y_max) = no neighboring cell at top
		elif sum(bottom_top_left_right) == 3:
			if bottom_top_left_right == [1,1,0,1]:
				local_ext_id.append(grid_type_factor*20)

			elif bottom_top_left_right == [1,1,1,0]:
				local_ext_id.append(grid_type_factor*21)

			elif bottom_top_left_right == [0,1,1,1]:
				local_ext_id.append(grid_type_factor*30)

			elif bottom_top_left_right == [1,0,1,1]:
				local_ext_id.append(grid_type_factor*31)

		## interior
		elif sum(bottom_top_left_right) == 4:
			local_ext_id.append(grid_type_factor*1) 

		########################################################################
		## elevation of top and bottom soil layers
		########################################################################
		z_top_temp = DEM_surface[t_y_row, t_x_col]
		soil_dz = DEM_soil_thickness[t_y_row, t_x_col]
		z_bottom_temp = z_top_temp - soil_dz
		local_z_t.append(z_top_temp)
		local_z_b.append(z_bottom_temp)

		########################################################################
		## water related
		########################################################################
		local_gw_z.append(DEM_gwt_z[t_y_row, t_x_col])
		local_front_z.append(DEM_wetting_front_z[t_y_row, t_x_col])
		local_psi_r.append(DEM_psi_r[t_y_row, t_x_col])
		local_psi_i.append(DEM_initial_suction[t_y_row, t_x_col])

		########################################################################
		## dip and aspect on base
		########################################################################
		local_base_dip_rad.append(np.radians(dip_base_deg[t_y_row, t_x_col]))
		local_base_aspect_rad.append(np.radians(aspect_base_deg[t_y_row, t_x_col]))

		########################################################################
		## shear strength parameters
		########################################################################
		local_gamma_s.append(DEM_soil_unit_weight[t_y_row, t_x_col])
		local_phi_eff_rad.append(np.radians(DEM_soil_phi[t_y_row, t_x_col]))
		local_phi_b_rad.append(np.radians(DEM_soil_phi_b[t_y_row, t_x_col]))
		local_c.append(DEM_soil_c[t_y_row, t_x_col])

		########################################################################
		## root strength
		########################################################################
		# root strength model 0 -> constant with depth
		local_root_gamma_s.append(DEM_root_unit_weight[t_y_row, t_x_col])
		local_root_c_base.append(DEM_root_c_base[t_y_row, t_x_col])
		local_root_c_side.append(DEM_root_c_side[t_y_row, t_x_col])
		local_root_depth.append(DEM_root_depth[t_y_row, t_x_col])

		# root strength model 1 -> van Zadelhoff et al. (2021) 
		local_root_alpha2.append(DEM_root_alpha2[t_y_row, t_x_col])
		local_root_beta2.append(DEM_root_beta2[t_y_row, t_x_col])
		local_root_RR_max.append(DEM_root_RR_max[t_y_row, t_x_col])

	########################################################################
	# all_slip_surf_data
	########################################################################
 	# index = slip surface ID, data = [0truncated_inside_row_y_col_x_global_idx, 1local_ext_id, 2local_z_t, 3local_z_b, 4local_gw_z, 5local_front_z, 6local_psi_r, 7local_psi_i, 8local_base_dip_rad, 9local_base_aspect_rad, 10local_gamma_s, 11local_phi_eff_rad, 12local_phi_b_rad, 13local_c, 14local_root_gamma_s, 15local_root_c_base, 16local_root_c_side, 17local_root_depth, 18local_root_alpha2, 19local_root_beta2, 20local_root_RR_max ] 
	return [truncated_inside_row_y_col_x_global_idx[:], local_ext_id[:], local_z_t[:], local_z_b[:], local_gw_z[:], local_front_z[:], local_psi_r[:], local_psi_i[:], local_base_dip_rad[:], local_base_aspect_rad[:], local_gamma_s[:], local_phi_eff_rad[:], local_phi_b_rad[:], local_c[:], local_root_gamma_s[:], local_root_c_base[:], local_root_c_side[:], local_root_depth[:], local_root_alpha2[:], local_root_beta2[:], local_root_RR_max[:]]


## computes 3D Janbu slope stability analysis from generated slip surface soil column datas
# Hungr (1989) - 3D Janbu + side resistance + grouping + root resistance
# min surrounding FS sorted outside the function
# side resistance assumed tension strength = 0 (only shear) for both c and phi
# root resistance assumed compressive root strength = 0 (only shear and tensile root cohesion)
# different root resistance model - constant, van Zadelhoff et al. (2021) 
# use aspect instead of dip direction
def critical_depth_group_3D_FS_HungrJanbu_MP_v9_00(critical_depth_3D_FS_MP_input):

	# output - failure_soil_thickness, min_comp_FS_over_depth

	# open up inputs	
	# 0truncated_inside_row_y_col_x_global_idx, 1local_ext_id, 2local_z_t, 3local_z_b, 4local_gw_z, 5local_front_z, 6local_psi_r, 7local_psi_i, 8local_base_dip_rad, 9local_base_aspect_rad, 10local_gamma_s, 11local_phi_eff_rad, 12local_phi_b_rad, 13local_c, 14local_root_gamma_s, 15local_root_c_base, 16local_root_c_side, 17local_root_depth, 18local_root_alpha2, 19local_root_beta2, 20local_root_RR_max, 21iteration_max, 22min_FS_diff, 23deltaX, 24deltaY, 25dz, 26gamma_w, 27FS_crit, 28correctFS_bool, 29FS_3D_apply_side, 30FS_3D_apply_root, 31DEM_root_model, 32dz_dp, 33press_dp
	truncated_inside_row_y_col_x_global_idx, local_ext_id, local_z_t, local_z_b, local_gw_z, local_front_z, local_psi_r, local_psi_i, local_base_dip_rad, local_base_aspect_rad, local_gamma_s, local_phi_eff_rad, local_phi_b_rad, local_c, local_root_gamma_s, local_root_c_base, local_root_c_side, local_root_depth, local_root_alpha2, local_root_beta2, local_root_RR_max, iteration_max, min_FS_diff, deltaX, deltaY, dz, gamma_w, FS_crit, correctFS_bool, FS_3D_apply_side, FS_3D_apply_root, DEM_root_model, dz_dp, press_dp = critical_depth_3D_FS_MP_input

	# local soil thickness
	DEM_soil_thickness_local = np.array(local_z_t) - np.array(local_z_b)

	# sliding direction - average of aspect direction
	col_local = []
	row_local = []
	for (row_y_loop,col_x_loop) in truncated_inside_row_y_col_x_global_idx:
		col_local.append(col_x_loop)
		row_local.append(row_y_loop)

	slide_aspect_rad_sum = 0.0
	slide_aspect_rad_count = 0
	for local_base_aspect_rad_i in local_base_aspect_rad:
		if local_base_aspect_rad_i >= 0:
			slide_aspect_rad_sum += local_base_aspect_rad_i
			slide_aspect_rad_count += 1
	
	if slide_aspect_rad_count == 0:			# if no valid aspect direction - all flat
		slide_aspect_rad = -9999
	elif slide_aspect_rad_count > 0:		# if valid aspect direction - average
		slide_aspect_rad = slide_aspect_rad_sum/slide_aspect_rad_count  # average aspect direction in radians

	# convert aspect to dip_direction
	slide_dir_rad = aspect_to_dip_direction(slide_aspect_rad, input_degree=False, output_degree=False)		# average dip direction in radians
	local_base_dip_dir_rad = aspect_to_dip_direction(local_base_aspect_rad, input_degree=False, output_degree=False)  # aspect -> dip direction in radians

	# too thin soil layer or no soil thickness data for all grids / all columns base dips are zero (less than 1 degree)
	if np.all(DEM_soil_thickness_local <= dz) or np.all(np.degrees(np.abs(local_base_dip_rad)) <= 1) or slide_aspect_rad == -9999:
		# no FS failure - soil failure thickness = 0 and arbitary high FS = 10.0
		return np.zeros(len(local_z_t)).tolist(), 10.0  

	################################################################
	### compute FS 
	################################################################
	
	thickness_per_test = []		# 'centroid' thickness tracker
	local_soil_thickness = []	# local failed soil thickness
	FS_3D_per_thickness = []	# computed FS per 'centroid' thickness

	cent_soil_thickness_list = np.arange(dz, max(DEM_soil_thickness_local), dz).tolist()   	# soil depths increments to check 
	if max(DEM_soil_thickness_local) > cent_soil_thickness_list[-1]:
		cent_soil_thickness_list.append(max(DEM_soil_thickness_local))

	for cent_soil_dZ in cent_soil_thickness_list:

		# soil depth all grids (account for non-uniform soil thickness between)
		local_soil_z_bottom_i = [max(local_z_t[local_idx] - cent_soil_dZ, local_z_b[local_idx]) for local_idx in range(len(local_z_b))]		# soil bottom layer elevation
		local_soil_thickness_i = [min(cent_soil_dZ, abs(local_z_t[local_idx] - local_z_b[local_idx])) for local_idx in range(len(local_z_b))]		# soil layer thickness
		
		thickness_per_test.append(cent_soil_dZ)
		local_soil_thickness.append(local_soil_thickness_i[:])

		#####################################
		## correction factor for simplified 3D Janbu method 
		#####################################
		correctionFactor = 1.0
		if correctFS_bool:

			# factor b1 - based on material properties
			sumPhiList = round(sum(local_phi_eff_rad),2)
			sumCList = round(sum(local_c),2)
			if sumPhiList > 0 and sumCList > 0:
				b1 = 0.50
			elif sumPhiList > 0 and sumCList == 0:
				b1 = 0.31
			elif sumPhiList == 0 and sumCList > 0:
				b1 = 0.69

			# L factor
			if len(local_ext_id) == 1:
				L = 2*(deltaX*deltaY)/np.sqrt((deltaX*np.sin(slide_dir_rad))**2 + (deltaY*np.cos(slide_dir_rad))**2 )
			else:
				Lx = ((abs(max(col_local) - min(col_local))/2) + 0.5)*deltaX
				Ly = ((abs(max(row_local) - min(row_local))/2) + 0.5)*deltaY
				L = 2*(Lx*Ly)/np.sqrt((Lx*np.sin(slide_dir_rad))**2 + (Ly*np.cos(slide_dir_rad))**2 )			

			# d factor
			dZList = []
			for (dip_rad_i, dip_dir_rad_i) in zip(local_base_dip_rad, local_base_dip_dir_rad):
				if np.isnan(dip_rad_i) or np.isnan(dip_dir_rad_i):
					apparantDip = 0.0
				else:
					apparantDip = abs(np.arctan(np.tan(dip_rad_i)*np.cos(abs(slide_dir_rad - dip_dir_rad_i))))
				dZList.append(cent_soil_dZ*np.cos(apparantDip))
			d = max(dZList)

			correctionFactor = 1 + b1*((d/L) - 1.4*((d/L)**2))
			if correctionFactor < 1:
				correctionFactor = 1

		#####################################
		## find FS_3D using fixed point iteration
		#####################################
		guess_FS_3D = 1.5

		for iter_n in range(iteration_max):

			comp_FS_shear = 0
			comp_FS_N_bot = 0
			comp_FS_Qs = 0

			# iterate through each soil columns to compute FS
			for cell_i in range(len(local_z_b)):
	
				if local_soil_thickness_i[cell_i] <= 0: 
					continue

				## base area
				g1 = np.where(np.isnan(local_base_dip_dir_rad[cell_i]), 0, np.sin(local_base_dip_rad[cell_i])*np.sin(local_base_dip_dir_rad[cell_i]))
				g2 = np.where(np.isnan(local_base_dip_dir_rad[cell_i]), 0, np.sin(local_base_dip_rad[cell_i])*np.cos(local_base_dip_dir_rad[cell_i]))
				g3 = np.cos(local_base_dip_rad[cell_i])	
				base_area = deltaX*deltaY*np.sqrt(1 + (g1/g3)**2 + (g2/g3)**2)

				## apparent dip in sliding direction
				apparantDip_rad = np.where(np.isnan(local_base_dip_dir_rad[cell_i]), 0, abs(np.arctan(np.tan(local_base_dip_rad[cell_i])*np.cos(abs(slide_dir_rad - local_base_dip_dir_rad[cell_i])))) )

				# ## base area
				# g1 = np.sin(local_base_dip_rad[cell_i])*np.sin(local_base_dip_dir_rad[cell_i])
				# g2 = np.sin(local_base_dip_rad[cell_i])*np.cos(local_base_dip_dir_rad[cell_i])
				# g3 = np.cos(local_base_dip_rad[cell_i])	
				# base_area = deltaX*deltaY*np.sqrt(1 + (g1/g3)**2 + (g2/g3)**2)

				# ## apparent dip in sliding direction
				# apparantDip_rad = abs(np.arctan(np.tan(local_base_dip_rad[cell_i])*np.cos(abs(slide_dir_rad - local_base_dip_dir_rad[cell_i]))))

				## pore-water pressure6
				U_w_force = base_area*u_w_ind_round(local_soil_z_bottom_i[cell_i], local_gw_z[cell_i], local_front_z[cell_i], local_z_b[cell_i], local_z_t[cell_i], local_psi_i[cell_i], local_psi_r[cell_i], gamma_w=gamma_w, slope_base=np.degrees(apparantDip_rad), dz_dp=dz_dp, press_dp=press_dp)

				## compute soil weight force
				# total unit weight
				total_weight_force = local_gamma_s[cell_i]*local_soil_thickness_i[cell_i]*base_area

				# add water weight when ponding occurs
				if local_gw_z[cell_i] > local_z_t[cell_i]:
					total_weight_force += (local_gw_z[cell_i] - local_z_t[cell_i])*gamma_w*base_area
				
				# add tree root weight if considered
				if FS_3D_apply_root:
					# limited at vertical by root presence depth
					total_weight_force += local_root_gamma_s[cell_i]*base_area*min(local_soil_thickness_i[cell_i], local_root_depth[cell_i])

				## side resistance
				# skip computing if interior
				if abs(local_ext_id[cell_i]) != 1 and FS_3D_apply_side: 

					# average effective stress
					if U_w_force >= 0:
						av_eff_stress = (0.5/base_area)*(total_weight_force - U_w_force)
					else:
						av_eff_stress = (0.5/base_area)*total_weight_force       

					# side area
					if abs(local_ext_id[cell_i]) in [20, 21, 402]: 		# one-side exterior with x-axis side & two-sides exterior x-axis sides - no neighbor on left and right
						side_area = local_soil_thickness_i[cell_i]*deltaX
					elif abs(local_ext_id[cell_i]) in [30, 31, 420]:	 # one-side exterior with y-axis side & two-sides exterior y-axis sides - no neighbor on top and bottom
						side_area = local_soil_thickness_i[cell_i]*deltaY
					elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411, 502, 512, 520, 521, 6]: 	# two-sides exterior (corner) one x-axis and one y-axis sides  or  single cell only
						side_area = local_soil_thickness_i[cell_i]*0.5*(deltaX + deltaY)

					# K_tau = 0.5*(K0 + Ka) = 0.5*( (1-sin(phi)) + (1-sin(phi))/(1+sin(phi)) ) = 0.5*( (1-sin(phi)) + (1-sin(phi))/(1+sin(phi)) )
					K0 = (1 - np.sin(local_phi_eff_rad[cell_i]))
					Ka = (1 - np.sin(local_phi_eff_rad[cell_i]))/(1 + np.sin(local_phi_eff_rad[cell_i]))
					K_tau = 0.5*(K0 + Ka)
					Qs_phi_force_mag = av_eff_stress*K_tau*np.tan(local_phi_eff_rad[cell_i])*side_area # Mohr-Coulomb frictional component
					Qs_c_force_mag = local_c[cell_i]*side_area  # Mohr-Coulomb cohesive component
					Qs_side_mag = Qs_phi_force_mag + Qs_c_force_mag

					## sum of side resistance for single grid cell
					if abs(local_ext_id[cell_i]) in [20, 21]: 		# one-side exterior with x-axis side
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) in [30, 31]:	 # one-side exterior with y-axis side
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411]: 	# two-sides exterior (corner) one x-axis and one y-axis sides
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) == 420: 	# two-sides exterior x-axis sides - no neighbor on left and right
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*2*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*2*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) == 402: 	# two-sides exterior y-axis sides - no neighbor on top and bottom
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*2*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*2*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)

					## 3-sides exterior
					# 502 = three-sides exterior = no neighboring cell at left, top, bottom
					# 512 = three-sides exterior = no neighboring cell at right, top, bottom
					# 2 sides aligned with y-axis and 1 side aligned with x-axis
					elif abs(local_ext_id[cell_i]) in [502, 512]: 
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*(abs(np.cos(slide_dir_rad)) + 2*abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*(abs(np.cos(slide_dir_rad)) + 2*abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)

					# 520 = three-sides exterior = no neighboring cell at left, right, bottom
					# 521 = three-sides exterior = no neighboring cell at left, right, top
					# 2 sides aligned with x-axis and 1 side aligned with y-axis
					elif abs(local_ext_id[cell_i]) in [520, 521]: 
						# friction and cohesion (only shear)
						Qs_force_hor = Qs_side_mag*(2*abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_force_ver = Qs_side_mag*(2*abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) == 6: 	# single cell only
						# friction and cohesion (only shear)
						Qs_force_hor = 2*Qs_side_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_force_ver = 2*Qs_side_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)

				else:
					Qs_force_hor = 0
					Qs_force_ver = 0
				
				## root base resistance
				if FS_3D_apply_root:

					# constant root strength with depth
					if DEM_root_model == 0:
						if local_soil_thickness_i[cell_i] > local_root_depth[cell_i]:
							Qbase_root_force_hor = 0
							Qbase_root_force_ver = 0
						else:
							Qbase_root_force_hor = local_root_c_base[cell_i]*base_area*np.cos(apparantDip_rad)
							Qbase_root_force_ver = local_root_c_base[cell_i]*base_area*np.sin(apparantDip_rad)

					# root strength - van Zadelhoff et al. (2021)
					elif DEM_root_model == 1:
						base_root_gamma_PDF = (local_soil_thickness_i[cell_i]**(local_root_alpha2[cell_i]-1))*np.exp(-local_soil_thickness_i[cell_i]/local_root_beta2[cell_i])/((local_root_beta2[cell_i]**local_root_alpha2[cell_i])*gamma_func(local_root_alpha2[cell_i]))
						Qbase_root_force_hor = local_root_RR_max[cell_i]*base_root_gamma_PDF*base_area*np.cos(apparantDip_rad)
						Qbase_root_force_ver = local_root_RR_max[cell_i]*base_root_gamma_PDF*base_area*np.sin(apparantDip_rad)

				else:
					Qbase_root_force_hor = 0
					Qbase_root_force_ver = 0

				## root side resistance
				if abs(local_ext_id[cell_i]) != 1 and FS_3D_apply_root:

					# constant root strength with depth
					if DEM_root_model == 0:

						# side area
						if abs(local_ext_id[cell_i]) in [20, 21, 402]: 		# one-side exterior with x-axis side & two-sides exterior x-axis sides - no neighbor on left and right
							root_side_area = min(local_soil_thickness_i[cell_i], local_root_depth[cell_i])*deltaX
						elif abs(local_ext_id[cell_i]) in [30, 31, 420]:	# one-side exterior with y-axis side & two-sides exterior y-axis sides - no neighbor on top and bottom
							root_side_area = min(local_soil_thickness_i[cell_i], local_root_depth[cell_i])*deltaY
						elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411, 502, 512, 520, 521, 6]: 
							# two-sides exterior (corner) one x-axis and one y-axis sides or 3-sides or single cell only
							root_side_area = min(local_soil_thickness_i[cell_i], local_root_depth[cell_i])*0.5*(deltaX + deltaY)

						# side root resistance
						Qs_root_force_mag = local_root_c_side[cell_i]*root_side_area

					# root strength - van Zadelhoff et al. (2021)
					elif DEM_root_model == 1:
						# integrate root strength PDF with depth -> root_adhesion over depth
						num_division = max(int((local_soil_thickness_i[cell_i] - 0.001)/(dz*0.05)), 300)
						lateral_root_depth_division = np.linspace(0.001, local_soil_thickness_i[cell_i], num_division)
						lateral_root_gamma_PDF = (lateral_root_depth_division**(local_root_alpha2[cell_i]-1))*np.exp(-lateral_root_depth_division/local_root_beta2[cell_i])/((local_root_beta2[cell_i]**local_root_alpha2[cell_i])*gamma_func(local_root_alpha2[cell_i]))

						## side length
						# if abs(local_ext_id[cell_i]) in [20, 21]: 		# one-side exterior with x-axis side & two-sides exterior x-axis sides - no neighbor on left and right
						# 	root_side_length = deltaX
						# elif abs(local_ext_id[cell_i]) in [30, 31]:	# one-side exterior with y-axis side & two-sides exterior y-axis sides - no neighbor on top and bottom
						# 	root_side_length = deltaY
						# elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411, 402, 420]: # two-sides exterior (corner) one x-axis and one y-axis sides 
						# 	root_side_length = (deltaX + deltaY)
						# elif abs(local_ext_id[cell_i]) in [502, 512, 520, 521]:  # 3-sided exterior
						# 	root_side_length = 1.5*(deltaX + deltaY)
						# elif abs(local_ext_id[cell_i]) == 6:  # 4-sided exterior or single cell only
						# 	root_side_length = 2.0*(deltaX + deltaY)

						if abs(local_ext_id[cell_i]) in [20, 21, 402]: 		# one-side exterior with x-axis side & two-sides exterior x-axis sides - no neighbor on left and right
							root_side_length = deltaX
						elif abs(local_ext_id[cell_i]) in [30, 31, 420]:	# one-side exterior with y-axis side & two-sides exterior y-axis sides - no neighbor on top and bottom
							root_side_length = deltaY
						elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411, 502, 512, 520, 521, 6]: 
							# two-sides exterior (corner) one x-axis and one y-axis sides or 3-sides or single cell only
							root_side_length = 0.5*(deltaX + deltaY)
	   
						Qs_root_force_mag = local_root_RR_max[cell_i]*np.trapz(lateral_root_gamma_PDF, x=lateral_root_depth_division)*root_side_length

					## this assumes root can act in tension and shear
					# sum of side resistance for single grid cell

					## x-axis aligned
					if abs(local_ext_id[cell_i]) == 20: 		# one-side exterior with x-axis side (closer to x_min)
						# shear
						Qs_root_force_hor = Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)
						# tensile
						Qs_root_force_hor += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
	  
					elif abs(local_ext_id[cell_i]) == 21: 		# one-side exterior with x-axis side (closer to x_max)
						# friction and cohesion (only shear)
						Qs_root_force_hor = Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)
						# tensile
						Qs_root_force_hor += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
	  
					## y-axis aligned
					elif abs(local_ext_id[cell_i]) == 30:	 # one-side exterior with y-axis side (closer to y_min)
						# shear
						Qs_root_force_hor = Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)
						# tensile
						Qs_root_force_hor += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)

					elif abs(local_ext_id[cell_i]) == 31:	 # one-side exterior with y-axis side (closer to y_max)
						# shear
						Qs_root_force_hor = Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)
						# tensile
						Qs_root_force_hor += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)

					## corner
					elif abs(local_ext_id[cell_i]) in [400, 401, 410, 411]: 	# two-sides exterior (corner) one x-axis and one y-axis sides
						# shear
						Qs_root_force_hor = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	  
						# (closer to x_min)
						if str(local_ext_id[cell_i])[1] == "0":
							# tensile
							Qs_root_force_hor += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# (closer to x_max)
						elif str(local_ext_id[cell_i])[1] == "1":
							# tensile
							Qs_root_force_hor += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# (closer to y_min)
						if str(local_ext_id[cell_i])[2] == "0":
							# tensile
							Qs_root_force_hor += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# (closer to y_max)
						elif str(local_ext_id[cell_i])[2] == "1":
							# tensile
							Qs_root_force_hor += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)
	   
					## two sides parallel - two-sides exterior x-axis sides - no neighbor on left and right
					elif abs(local_ext_id[cell_i]) == 420: 
						# shear
						Qs_root_force_hor = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	  
						# tensile (closer to x_min)
						Qs_root_force_hor += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# tensile (closer to x_max)
						Qs_root_force_hor += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)


					## two sides parallel - two-sides exterior y-axis sides - no neighbor on top and bottom
					elif abs(local_ext_id[cell_i]) == 402: 	
						# shear
						Qs_root_force_hor = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_root_force_ver = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	  
						# tensile (closer to y_min)
						Qs_root_force_hor += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# tensile (closer to y_max)
						Qs_root_force_hor += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)

					## 3-sided 
					elif abs(local_ext_id[cell_i]) in [502, 512, 520, 521]: 	# 3-sides

						#########################
						### Shear root resistance
						#########################
						# 502 = three-sides exterior = no neighboring cell at left, top, bottom
						# 512 = three-sides exterior = no neighboring cell at right, top, bottom
						# 2 sides aligned with y-axis and 1 side aligned with x-axis
						if abs(local_ext_id[cell_i]) in [502, 512]: 
							# friction and cohesion (only shear)
							Qs_root_force_hor = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + 2*abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
							Qs_root_force_ver = Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + 2*abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	
						# 520 = three-sides exterior = no neighboring cell at left, right, bottom
						# 521 = three-sides exterior = no neighboring cell at left, right, top
						# 2 sides aligned with x-axis and 1 side aligned with y-axis
						elif abs(local_ext_id[cell_i]) in [520, 521]: 
							# friction and cohesion (only shear)
							Qs_root_force_hor = Qs_root_force_mag*(2*abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
							Qs_root_force_ver = Qs_root_force_mag*(2*abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	  
	  					#########################
	  					### tensile root resistance
						#########################
						# 502 = three-sides exterior = no neighboring cell at left, top, bottom
						if local_ext_id[cell_i] == 502:
							# tensile - two y-axis sides
							Qs_root_force_hor += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)

							# tensile - single x-axis side at left
							Qs_root_force_hor += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# 512 = three-sides exterior = no neighboring cell at right, top, bottom
						elif local_ext_id[cell_i] == 512:
							# tensile - two y-axis sides
							Qs_root_force_hor += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)

							# tensile - single x-axis side at right
							Qs_root_force_hor += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(-np.cos(slide_dir_rad), 0)*np.sin(apparantDip_rad)
		  
						# 520 = three-sides exterior = no neighboring cell at left, right, bottom
						if local_ext_id[cell_i] == 520:
							# tensile - single y-axis side side at top
							Qs_root_force_hor += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)

							# tensile - two x-axis sides
							Qs_root_force_hor += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)
							
						# 521 = three-sides exterior = no neighboring cell at left, right, top
						elif local_ext_id[cell_i] == 521:
							# tensile - single y-axis side at bottom
							Qs_root_force_hor += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*max(-np.sin(slide_dir_rad), 0)*np.sin(apparantDip_rad)

							# tensile - two x-axis sides
							Qs_root_force_hor += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
							Qs_root_force_ver += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)

					## single cell
					elif abs(local_ext_id[cell_i]) == 6: 	
						# shear
						Qs_root_force_hor = 2*Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.cos(apparantDip_rad)
						Qs_root_force_ver = 2*Qs_root_force_mag*(abs(np.cos(slide_dir_rad)) + abs(np.sin(slide_dir_rad)))*np.sin(apparantDip_rad)
	  
						# tensile - x-axis
						Qs_root_force_hor += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*abs(np.cos(slide_dir_rad))*np.sin(apparantDip_rad)

						# tensile - y-axis
						Qs_root_force_hor += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.cos(apparantDip_rad)
						Qs_root_force_ver += Qs_root_force_mag*abs(np.sin(slide_dir_rad))*np.sin(apparantDip_rad)
					
				else:
					Qs_root_force_hor = 0
					Qs_root_force_ver = 0

				## unsaturated soil friction angle
				if U_w_force < 0:
					phi_b_val = local_phi_b_rad[cell_i]
				else:
					phi_b_val = local_phi_eff_rad[cell_i]

				## normal force N
				m_alpha = g3 + (np.sin(apparantDip_rad)*np.tan(local_phi_eff_rad[cell_i])/guess_FS_3D)
				Q_resist_ver_sum = Qs_force_ver + Qbase_root_force_ver + Qs_root_force_ver
				Q_resist_hor_sum = Qs_force_hor + Qbase_root_force_hor + Qs_root_force_hor
				N_top = total_weight_force - Q_resist_ver_sum - (base_area*local_c[cell_i]*np.sin(apparantDip_rad)/guess_FS_3D) + (U_w_force*np.tan(phi_b_val)*np.sin(apparantDip_rad)/guess_FS_3D)
				N_factor = N_top/m_alpha
				if N_factor <= 0: 
					N_factor = 0

				## sum factors for computing FS_3D
				comp_FS_shear += (base_area*local_c[cell_i]*np.cos(apparantDip_rad)) + (N_factor*np.tan(local_phi_eff_rad[cell_i])*np.cos(apparantDip_rad)) - (U_w_force*np.tan(phi_b_val)*np.cos(apparantDip_rad))
				comp_FS_N_bot += N_factor*g3*np.tan(apparantDip_rad)
				comp_FS_Qs += Q_resist_hor_sum

			if comp_FS_N_bot <= 0:
				comp_FS_3D = 9999
			else:
				comp_FS_3D = (comp_FS_shear + comp_FS_Qs)/comp_FS_N_bot

			## check iteration
			if (abs(comp_FS_3D - guess_FS_3D) <= min_FS_diff):
				FS_3D_per_thickness.append(correctionFactor*comp_FS_3D)
				break
			elif (comp_FS_3D == 9999):
				FS_3D_per_thickness.append(9999)
				break
			elif (iter_n == iteration_max-1):
				if (abs(comp_FS_3D - guess_FS_3D) > 2*min_FS_diff):
					FS_3D_per_thickness.append(9999)
				else:
					FS_3D_per_thickness.append(0.5*(comp_FS_3D + guess_FS_3D))
				break
			else:
				if comp_FS_3D == 0:
					guess_FS_3D = 1.0		
				else:
					guess_FS_3D = comp_FS_3D

	## find minimum 3D FS and potential critical failure depth for each groupings
	FS_3D_per_thickness_array = np.array(FS_3D_per_thickness)
	FS_3D_per_thickness_array = np.where(FS_3D_per_thickness_array <= 0, 0, FS_3D_per_thickness_array)
	# FS_3D_per_thickness_array = np.where(FS_3D_per_thickness_array >= 10, 10, FS_3D_per_thickness_array)
	crit_FS_3D = np.where(FS_3D_per_thickness_array <= FS_crit, 1, 0)

	if np.sum(crit_FS_3D) == 0:
		# no FS failure - soil failure thickness = 0 and min computed FS
		return np.zeros(len(local_z_t)).tolist(), max(float(np.amin(FS_3D_per_thickness_array)),0)    # assume no failure when all FS > FS_crit, so no failure depth

	elif np.sum(crit_FS_3D) > 0:

		# index of thickness that gives FS < FS_crit
		crit_FS_idx = [idx for idx, FSi in enumerate(FS_3D_per_thickness_array) if FSi <= FS_crit]

		# assume failure occurs at the deepest layer if multiple failure occurs at depths
		failure_soil_thickness = max([thickness_per_test[idx] for idx in crit_FS_idx])  

		# among the slope failures with highest thickness, get minimum FS value
		max_thickness_min_critFS_list = [float(FS_3D_per_thickness_array[idx]) for idx, tt in enumerate(thickness_per_test) if ((idx in crit_FS_idx) and (abs(round(tt - failure_soil_thickness,3))<=0.001))]
		max_thickness_min_critFS = min(max_thickness_min_critFS_list)
		max_thickness_min_critFS_index = max_thickness_min_critFS_list.index(max_thickness_min_critFS)

		# determine failure thickness for each DEM cell
		failure_soil_thickness_per_DEM_cell = local_soil_thickness[max_thickness_min_critFS_index][:]

		# soil failure thickness per DEM cell and min computed FS
		return failure_soil_thickness_per_DEM_cell, max(max_thickness_min_critFS, 0)


######################################################
## DEM functions for UCA and networks
######################################################
# form directed graph for DEM with elevation (Z) and neighboring points
# flow can happen between two equal elevation
def DEM_Z_diff_MP_equal_flow(DEM_neighbor_Zdiff_MP_input):
	point_idx, i, j, x, y, DEM, i_flatten, j_flatten, gridUniqueX, gridUniqueY, local_cell_sizes = DEM_neighbor_Zdiff_MP_input
	
	# get local neighbors D8 + itself
	local_xy, local_z = local_cell_v3_2(local_cell_sizes, x, y, DEM, gridUniqueX, gridUniqueY, None)

	# find i,j (global) and point_idx (1D) of local neighboring cells
	network_graph_ij = []   	# index location to give (1) to graph matrix [directed: flow only from i -> j]

	for (xx,yy),zz in zip(local_xy, local_z):
		ii, jj = compute_ij_v1_1(xx, yy, gridUniqueX, gridUniqueY, deltaX, deltaY)

		# remove itself
		if (ii != i) or (jj != j):
			# point_other_idx = int(np.where((i_flatten == ii) & (j_flatten == jj))[0])
			point_other_idx = int(np.where((i_flatten == ii) & (j_flatten == jj))[0][0])

			# lower elevation than current cell	(cur cell flow into other cells)
			if zz < DEM[i,j]:  
				network_graph_ij.append((point_other_idx, point_idx))

			# higher elevation than current cell (other cell flow into current cell)
			elif zz > DEM[i,j]:  	
				network_graph_ij.append((point_idx, point_other_idx))

			# if equal level of elevation, then flows into each other
			elif zz == DEM[i,j]:
				network_graph_ij.append((point_idx, point_other_idx))
				network_graph_ij.append((point_other_idx, point_idx))

	return network_graph_ij

# form directed graph for DEM with elevation (Z) and neighboring points
# only elevation higher is considered as upslope
def DEM_Z_diff_MP_strictly_hierarchy(DEM_neighbor_Zdiff_MP_input): 
	point_idx, i, j, x, y, DEM, i_flatten, j_flatten, gridUniqueX, gridUniqueY, local_cell_sizes = DEM_neighbor_Zdiff_MP_input
	
	# get local neighbors D8 + itself
	local_xy, local_z = local_cell_v3_2(local_cell_sizes, x, y, DEM, gridUniqueX, gridUniqueY, None)

	# find i,j (global) and point_idx (1D) of local neighboring cells
	network_graph_ij = []   	# index location to give (1) to graph matrix [directed: flow only from i -> j]

	for (xx,yy),zz in zip(local_xy, local_z):
		ii, jj = compute_ij_v1_1(xx, yy, gridUniqueX, gridUniqueY, deltaX, deltaY)

		# remove itself
		if (ii != i) or (jj != j):
			# point_other_idx = int(np.where((i_flatten == ii) & (j_flatten == jj))[0])
			point_other_idx = int(np.where((i_flatten == ii) & (j_flatten == jj))[0][0])
			
			# lower elevation than current cell	(cur cell flow into other cells)
			if zz < DEM[i,j]:  
				network_graph_ij.append((point_other_idx, point_idx))

			# higher elevation than current cell (other cell flow into current cell)
			elif zz > DEM[i,j]:  	
				network_graph_ij.append((point_idx, point_other_idx))

	return network_graph_ij

# count the number of cells that flows into the selected cell
def count_UCA_cells_MP_v2(count_UCA_cells_inputs): 
	"""multiprocessing number for computing UCA 

	Args:
		count_UCA_cells_inputs (tuple): (row, col, point index, DEM_neighbor_directed_graph)

	Returns:
		tuple: (row, col, point index, number of connections)
	"""
	i, j, point_idx, DEM_neighbor_directed_graph = count_UCA_cells_inputs

	# if precessor != -9999 or dist_matrix != inf, then there is a path that flows into selected point_idx
	_, predecessors = dijkstra(csgraph=DEM_neighbor_directed_graph, directed=True, indices=point_idx, return_predecessors=True)
	connection_found_check = np.where(predecessors != -9999, 1, 0)

	# count how many upslope cell will flow into the selected cell	
	# +1 is to account for itself
	connection_found_check_count = int(np.sum(connection_found_check))+1	  

	return (i, j, point_idx, connection_found_check_count)

######################################################
## rounding to significant figures
######################################################
# rounding functions to significant figures
# https://www.delftstack.com/howto/python/round-to-significant-digits-python/
def round_to_sigfig(number, sigfig):
	"""rounding number of particular significant figures

	Args:
		number (int, float or numpy array): number
		sigfig (int, float): the significant figure number to which the number is rounded

	Returns:
		(int, float or numpy array): number adjusted to significant figures
	"""

	if isinstance(number, (int, float)) and number == 0:
		return 0.0

	elif isinstance(number, (int, float)) and number > 0:
		return round(number, int(sigfig) - int(np.floor(np.log10(abs(number)))) - 1)
	
	elif type(number) == np.ndarray:
		nonzero_number = np.where(number == 0, np.nan, number)
		rounding_number_sigfig = int(sigfig) - np.floor(np.log10(np.absolute(nonzero_number))) - 1
		rounding_number_sigfig = np.where(number == 0, 0, rounding_number_sigfig).astype(int)
		return np.array([round(num_i, sfi) for num_i,sfi in zip(number, rounding_number_sigfig)])

###########################################################################
## input data files
###########################################################################
def check_prob_input(prob_param_list):
	"""check material input properties that constructs probabilistic distribution

	Args:
		prob_param_list (list): material input parameter provided by user

	Returns:
		Prints the error message, if exists. Return False when error found.
	"""

	if (len(prob_param_list) != 7):
		print("if probabilistic parameter is considered, seven values must be provided")
		return False
	
	if isinstance(prob_param_list[0], (int, float)) == False:
		print("if probabilistic parameter is considered, the mean values must be a number")
		return False	

	if isinstance(prob_param_list[1], (int, float)) == False:
		print("if probabilistic parameter is considered, the coefficient of variation (CoV) values must be a number")
		return False	

	if (prob_param_list[2] not in ["N", "LN"]):
		print("if probabilistic parameter is considered, the statistical distribution must be one of the recognized distribution (N or LN)")
		return False	
	
	if isinstance(prob_param_list[3], (int, float, str)) == False or (isinstance(prob_param_list[3], (int, float)) and prob_param_list[3] < 0.0) or (isinstance(prob_param_list[3], str) and prob_param_list[3] != "inf"):
		print("if probabilistic parameter is considered, the correlation length must be positive or zero value. Otherwise, the infinite correlation length must be expressed as \"inf\"")
		return False

	if isinstance(prob_param_list[4], (int, float, str)) == False or (isinstance(prob_param_list[4], (int, float)) and prob_param_list[4] < 0.0) or (isinstance(prob_param_list[4], str) and prob_param_list[4] != "inf"):
		print("if probabilistic parameter is considered, the correlation length must be positive or zero value. Otherwise, the infinite correlation length must be expressed as \"inf\"")
		return False

	if isinstance(prob_param_list[5], (int, float)) == False or isinstance(prob_param_list[6], (int, float)) == False or ((isinstance(prob_param_list[5], (int, float)) and isinstance(prob_param_list[6], (int, float))) and prob_param_list[5] > prob_param_list[6]):
		print("if probabilistic parameter is considered, the min and max range should be number and min value must be equal to smaller than the max")
		return False

	return True

def read_RISD_json_yaml_input_v20250711(input_file_name):
	"""Read input parameters from a JSON or YAML file for RISD analysis.

	Args:
		input_file_name (str): Path to the input JSON or YAML file.

	Returns:
		tuple: Various input parameters for RISD analysis.
	"""

	##################################################################################################################
	## input json or yaml file
	##################################################################################################################

	if isinstance(input_file_name, str):
		# check whether it is yaml or json file format
		input_file_name_list = input_file_name.split('.')
		input_file_name_format = input_file_name_list[-1]

		if input_file_name_format.lower()  == "json":
			with open(input_file_name, 'r') as json_file:
				json_yaml_input_data = json.load(json_file)

		elif input_file_name_format.lower() in ["yaml", "yml"]:
			with open(input_file_name, 'r') as yaml_file:
				json_yaml_input_data = yaml.safe_load(yaml_file)
	
	elif isinstance(input_file_name, dict):
		json_yaml_input_data = deepcopy(input_file_name)


	##################################################################################################################
	## to restart 3DTSP simulations
	##################################################################################################################
	if "original_input" in json_yaml_input_data.keys() and "iterations" in json_yaml_input_data.keys():
		filename = json_yaml_input_data["original_input"]["filename"]
		input_folder_path = json_yaml_input_data["original_input"]["input_folder_path"]
		output_folder_path = json_yaml_input_data["original_input"]["output_folder_path"]

		dz = json_yaml_input_data["original_input"]["vertical_spacing"]
		dt = min([abs(e-s) for (s,e,_) in json_yaml_input_data["original_input"]["rainfall_history"]])/json_yaml_input_data["original_input"]["dt_iteration"]

		# return info
		return filename, input_folder_path, output_folder_path, json_yaml_input_data, None, None, None, None, None, dz, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, dt, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None



	##################################################################################################################
	## read json or yaml file and extract input file data - also check whether input values have no issues
	##################################################################################################################

	try: # exception for json input file error

		###########################################################
		## Name and folder information
		###########################################################
		# project name / export name
		filename = json_yaml_input_data["filename"] 

		# project folder path
		input_folder_path = json_yaml_input_data["input_folder_path"]
		if input_folder_path[-1] != "/":
			input_folder_path += '/'

		output_folder_path = json_yaml_input_data["output_folder_path"]
		if output_folder_path[-1] != "/":
			output_folder_path += '/'

		# create full path to not have issues
		# cur_file_path_abs = os.getcwd() # always relative to the function file
		# input_folder_path = os.path.normpath(os.path.join(cur_file_path_abs, input_folder_path)) + '/'
		# output_folder_path = os.path.normpath(os.path.join(cur_file_path_abs, output_folder_path)) + '/'

		# format of output
		output_txt_format = json_yaml_input_data["results_format"]
		
		# generate plot or not
		plot_option = json_yaml_input_data["generate_plot"]

		# restarting of the analysis
		if isinstance(json_yaml_input_data["restarting_simulation_JSON"], str) and (("json" in json_yaml_input_data["restarting_simulation_JSON"]) or ("JSON" in json_yaml_input_data["restarting_simulation_JSON"])):
			if "\\" in json_yaml_input_data["restarting_simulation_JSON"] or "/" in json_yaml_input_data["restarting_simulation_JSON"]:
				with open(json_yaml_input_data["restarting_simulation_JSON"], 'r') as json_file:
					restarting_simulation_dict = json.load(json_file)
			else:
				with open(input_folder_path+json_yaml_input_data["restarting_simulation_JSON"], 'r') as json_file:
					restarting_simulation_dict = json.load(json_file)

			filename = restarting_simulation_dict["original_input"]["filename"]
			input_folder_path = restarting_simulation_dict["original_input"]["input_folder_path"]
			output_folder_path = restarting_simulation_dict["original_input"]["output_folder_path"]

			dz = restarting_simulation_dict["original_input"]["vertical_spacing"]
			dt = min([abs(e-s) for (s,e,_) in restarting_simulation_dict["original_input"]["rainfall_history"]])/restarting_simulation_dict["original_input"]["dt_iteration"]

			# return info
			return filename, input_folder_path, output_folder_path, restarting_simulation_dict, None, None, None, None, None, dz, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, dt, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None


		elif isinstance(json_yaml_input_data["restarting_simulation_JSON"], str) and (("yaml" in json_yaml_input_data["restarting_simulation_JSON"]) or ("YAML" in json_yaml_input_data["restarting_simulation_JSON"]) or ("yml" in json_yaml_input_data["restarting_simulation_JSON"]) or ("YML" in json_yaml_input_data["restarting_simulation_JSON"])):
			if "\\" in json_yaml_input_data["restarting_simulation_JSON"] or "/" in json_yaml_input_data["restarting_simulation_JSON"]:
				with open(json_yaml_input_data["restarting_simulation_JSON"], 'r') as yaml_file:
					restarting_simulation_dict = yaml.safe_load(yaml_file)
			else:
				with open(input_folder_path+json_yaml_input_data["restarting_simulation_JSON"], 'r') as yaml_file:
					restarting_simulation_dict = yaml.safe_load(yaml_file)

			filename = restarting_simulation_dict["original_input"]["filename"]
			input_folder_path = restarting_simulation_dict["original_input"]["input_folder_path"]
			output_folder_path = restarting_simulation_dict["original_input"]["output_folder_path"]

			dz = restarting_simulation_dict["original_input"]["vertical_spacing"]
			dt = min([abs(e-s) for (s,e,_) in restarting_simulation_dict["original_input"]["rainfall_history"]])/restarting_simulation_dict["original_input"]["dt_iteration"]

			# return info
			return filename, input_folder_path, output_folder_path, restarting_simulation_dict, None, None, None, None, None, dz, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, dt, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None


		elif json_yaml_input_data["restarting_simulation_JSON"] is None:
			restarting_simulation_dict = None


			# with open(input_folder_path+json_yaml_input_data["restarting_simulation_JSON"], 'r') as json_file:
			# 	restarting_simulation_dict_temp = json.load(json_file)

			# restarting_simulation_dict = {} 
			# for key, value in restarting_simulation_dict_temp.items():
			# 	key_val = int(key) if is_int(key) else float(key) if is_float(key) else key

			# 	if (isinstance(value, list) and len(value) == 2) or isinstance(value, (str,int,float)) or (value is None):
			# 		restarting_simulation_dict[key_val] = deepcopy(value)

			# 	elif isinstance(value, dict):
			# 		restarting_simulation_dict[key_val] = {}
			# 		for sub_key, sub_value in value.items():
			# 			sub_key_val = int(sub_key) if is_int(sub_key) else float(sub_key) if is_float(sub_key) else sub_key
			# 			if (isinstance(sub_value, list) and len(sub_value) == 2) or isinstance(sub_value, (str,int,float)) or (sub_value is None):
			# 				restarting_simulation_dict[key_val][sub_key_val] = deepcopy(sub_value)

			# 			elif isinstance(sub_value, dict):
			# 				restarting_simulation_dict[key_val][sub_key_val] = {}
			# 				for sub_sub_key, sub_sub_value in sub_value.items():
			# 					sub_sub_key_val = int(sub_sub_key) if is_int(sub_sub_key) else float(sub_sub_key) if is_float(sub_sub_key) else sub_sub_key
			# 					restarting_simulation_dict[key_val][sub_key_val][sub_sub_key_val] = deepcopy(sub_sub_value)	

			###########################################################
			## default numbers
			###########################################################
			gamma_w = json_yaml_input_data["unit_weight_of_water"]
			FS_crit = json_yaml_input_data["FS_crit"]
			dz = json_yaml_input_data["vertical_spacing"]

			## multiprocessing CPU count
			max_cpu_num = json_yaml_input_data["max_cpu_num"]
			if mp.cpu_count() >= max_cpu_num:
				cpu_num = int(max_cpu_num)
			else:
				cpu_num = int(mp.cpu_count())

			###########################################################
			## analysis options
			###########################################################
			termination_apply = json_yaml_input_data["termination_apply"]
			after_termination_new_times_apply = json_yaml_input_data["after_termination_new_times_apply"]
			DEM_surf_dip_infiltraion_apply = json_yaml_input_data["DEM_surf_dip_infiltraion_apply"]
			DEM_debris_flow_criteria_apply = json_yaml_input_data["DEM_debris_flow_criteria_apply"]
			
			FS_3D_analysis_opt = json_yaml_input_data["FS_analysis_method"]
			if FS_3D_analysis_opt == "infinite":
				FS_3D_analysis = False
				cell_size_3DFS_min = 1
				cell_size_3DFS_max = 1
				superellipse_n_parameter = 100
				superellipse_eccen_ratio = 1
				FS_3D_iter_limit = 1
				FS_3D_tol = 0.001
				FS_3D_apply_side = False
				FS_3D_apply_root = False

			elif FS_3D_analysis_opt == "3D Janbu":
				FS_3D_analysis = True
				cell_size_3DFS_min = json_yaml_input_data["cell_size_3DFS_min"]
				cell_size_3DFS_max = json_yaml_input_data["cell_size_3DFS_max"]
				superellipse_n_parameter = json_yaml_input_data["superellipse_power"]
				superellipse_eccen_ratio = json_yaml_input_data["superellipse_eccentricity_ratio"]
				FS_3D_iter_limit = json_yaml_input_data["3D_FS_iteration_limit"]
				FS_3D_tol = json_yaml_input_data["3D_FS_convergence_tolerance"]
				FS_3D_apply_side = json_yaml_input_data["apply_side_resistance_3D"]
				FS_3D_apply_root = json_yaml_input_data["apply_root_resistance_3D"]

			elif FS_3D_analysis_opt is None:
				FS_3D_analysis = None
				cell_size_3DFS_min = None
				cell_size_3DFS_max = None
				superellipse_n_parameter = None
				superellipse_eccen_ratio = None
				FS_3D_iter_limit = None
				FS_3D_tol = None
				FS_3D_apply_side = None
				FS_3D_apply_root = None
			
			DEM_UCA_compute_all = True # json_yaml_input_data["DEM_UCA_compute_all"]

			######################################################
			## probabilistic analysis options
			######################################################
			monte_carlo_iteration_max = int(json_yaml_input_data["monte_carlo_iteration_max"])

			######################################################
			## inputs - infiltration 
			######################################################
			## time units
			length_unit, time_unit = json_yaml_input_data["rain_unit"].split("/")

			# convert all length to m, time to s and pressure to kPa

			convert_time = 1
			convert_intensity = 1
			if length_unit == "mm":
				convert_intensity *= 1/1000
			elif length_unit == "cm":
				convert_intensity *= 1/100
			
			if time_unit == "hr":
				convert_time *= 3600
				convert_intensity *= 1/3600
			elif time_unit == "min":
				convert_time *= 60
				convert_intensity *= 1/60

			## rainfall time history
			dt_iter_num = json_yaml_input_data["dt_iteration"]					# subdivide between start time and end time to get more data between the start and end
			rainfall_history_given = json_yaml_input_data["rainfall_history"]	# [start_time, end_time, rainfall intensity]

			# check for interval
			dt = min([abs(e-s) for (s,e,_) in rainfall_history_given])/dt_iter_num

			rain_time_I = []
			for (startT, endT, rainI) in rainfall_history_given:
				Time_interval = endT - startT
				time_num_steps = int(np.floor(Time_interval/dt))
				if time_num_steps > 1:
					for t_idx in range(time_num_steps):
						if isinstance(rainI, (int, float)):  # uniformly apply
							rain_time_I.append([(startT + t_idx*dt)*convert_time, (startT + (t_idx+1)*dt)*convert_time, rainI*convert_intensity])
						elif isinstance(rainI, str):  # from GIS file
							rain_time_I.append([(startT + t_idx*dt)*convert_time, (startT + (t_idx+1)*dt)*convert_time, rainI])
						elif isinstance(rainI, list) and len(rainI) > 0 and len(rainI[0]) == 3:  # from nearest rain gauge data
							rain_gauge_I = [[x,y,It*convert_intensity] for (x,y,It) in rainI]
							rain_time_I.append([(startT + t_idx*dt)*convert_time, (startT + (t_idx+1)*dt)*convert_time, rain_gauge_I[:]])
							del rain_gauge_I
						elif isinstance(rainI, list) and len(rainI) > 0 and len(rainI[0]) == 9:  # from nearest rain gauge data - probabilistic
							# format = [[X, Y, Mean, CoV, Prob. Dist., Corr. Length X, Corr. Length Y, Min, Max], ...]
							rain_gauge_I = [[x,y,mu_I*convert_intensity,cov,dist,corLx,corLy,min_I*convert_intensity,max_I*convert_intensity] for (x,y,mu_I,cov,dist,corLx,corLy,min_I,max_I) in rainI]
							rain_time_I.append([(startT + t_idx*dt)*convert_time, (startT + (t_idx+1)*dt)*convert_time, rain_gauge_I[:]])
							del rain_gauge_I
				else:
					if isinstance(rainI, (int, float)):  # uniformly apply
						rain_time_I.append([startT*convert_time, endT*convert_time, rainI*convert_intensity])
					elif isinstance(rainI, str):  # from GIS file
						rain_time_I.append([startT*convert_time, endT*convert_time, rainI])
					elif isinstance(rainI, list) and len(rainI) > 0 and len(rainI[0]) == 3:  # from nearest rain gauge data
						rain_gauge_I = [[x,y,It*convert_intensity] for (x,y,It) in rainI]
						rain_time_I.append([startT*convert_time, endT*convert_time, rain_gauge_I[:]])
						del rain_gauge_I
					elif isinstance(rainI, list) and len(rainI) > 0 and len(rainI[0]) == 9:  # from nearest rain gauge data - probabilistic
						# format = [[X, Y, Mean, CoV, Prob. Dist., Corr. Length X, Corr. Length Y, Min, Max], ...]
						rain_gauge_I = [[x,y,mu_I*convert_intensity,cov,dist,corLx,corLy,min_I*convert_intensity,max_I*convert_intensity] for (x,y,mu_I,cov,dist,corLx,corLy,min_I,max_I) in rainI]
						rain_time_I.append([startT*convert_time, endT*convert_time, rain_gauge_I[:]])
						del rain_gauge_I

			dt = dt*convert_time

			## time step after landslide failure occurs
			debris_t_max = json_yaml_input_data["debris_t_max"]  	 # s
			debris_dt = json_yaml_input_data["debris_dt"]			 # s

			######################################################
			## field data
			######################################################
			## DEM file name
			DEM_file_name = json_yaml_input_data["DEM_file_name"]
			increase_DEM_resolution = 1 # json_yaml_input_data["increase_DEM_resolution"]

			## soil material file name
			material_file_name = json_yaml_input_data["material_file_name"]
			
			## soil depth
			if isinstance(json_yaml_input_data["soil_depth_data"], list) and (len(json_yaml_input_data["soil_depth_data"]) >= 2):
				# model
				if json_yaml_input_data["soil_depth_data"][0] == "uniform":
					soil_depth_model = 0  # compute from bedrock surface
				elif json_yaml_input_data["soil_depth_data"][0] == "GIS":
					soil_depth_model = 1  # compute from ground surface
				elif json_yaml_input_data["soil_depth_data"][0] == "Holm and Edvarson - Norway":
					soil_depth_model = 2  # compute with ground surface and ratio of soil thickness  
				elif json_yaml_input_data["soil_depth_data"][0] == "general multiregression":
					if json_yaml_input_data["soil_depth_data"][1] not in ["linear", "power"]:
						print("soil thicknes model not correctly provided")
						sys.exit(2)
					soil_depth_model = 3  # compute with bedrock surface and ratio of soil thickness  
				elif json_yaml_input_data["soil_depth_data"][0] == "prob - uniform":
					soil_depth_model = 10  # compute from bedrock surface
				elif json_yaml_input_data["soil_depth_data"][0] == "prob - GIS":
					soil_depth_model = 11  # compute from ground surface
				elif json_yaml_input_data["soil_depth_data"][0] == "prob - Holm and Edvarson - Norway":
					soil_depth_model = 12  # compute with ground surface and ratio of soil thickness  
				elif json_yaml_input_data["soil_depth_data"][0] == "prob - general multiregression":
					if json_yaml_input_data["soil_depth_data"][1] not in ["linear", "power"]:
						print("soil thicknes model not correctly provided")
						sys.exit(2)
					soil_depth_model = 13  # compute with bedrock surface and ratio of soil thickness  
				else:
					print("soil thicknes model not correctly provided")
					sys.exit(2)

				# information
				soil_depth_data = json_yaml_input_data["soil_depth_data"][1:]

			else:
				raise RuntimeError

			## groundwater table 
			if isinstance(json_yaml_input_data["ground_water_data"], list) and (len(json_yaml_input_data["ground_water_data"]) == 2):
				# model
				if json_yaml_input_data["ground_water_data"][0] == "thickness above bedrock":
					ground_water_model = 0  # compute from bedrock surface
				elif json_yaml_input_data["ground_water_data"][0] == "depth from surface":
					ground_water_model = 1  # compute from ground surface
				elif json_yaml_input_data["ground_water_data"][0] == "percentage of the soil thickness above bedrock":
					ground_water_model = 2  # compute with ground surface and ratio of soil thickness  
				elif json_yaml_input_data["ground_water_data"][0] == "percentage of the soil thickness from surface":
					ground_water_model = 3  # compute with bedrock surface and ratio of soil thickness  
				elif json_yaml_input_data["ground_water_data"][0] == "GWT elevation GIS":
					ground_water_model = 4  # elevation of groundwater table
				else:
					print("ground water model not correctly provided")
					sys.exit(2)

				# information
				ground_water_data = json_yaml_input_data["ground_water_data"][1]
				if isinstance(ground_water_data, (int, float, str)) == False:
					print("ground water data not correctly provided")
					sys.exit(2)
			else:
				raise RuntimeError

			## dip and aspect of surface and bedrock
			if isinstance(json_yaml_input_data["dip_surf_filename"], str) and isinstance(json_yaml_input_data["aspect_surf_filename"], str) and isinstance(json_yaml_input_data["dip_base_filename"], str) and isinstance(json_yaml_input_data["aspect_base_filename"], str):
				dip_surf_filename = json_yaml_input_data["dip_surf_filename"]
				aspect_surf_filename = json_yaml_input_data["aspect_surf_filename"]
				dip_base_filename = json_yaml_input_data["dip_base_filename"]
				aspect_base_filename = json_yaml_input_data["aspect_base_filename"]
			else:
				dip_surf_filename = None
				aspect_surf_filename = None
				dip_base_filename = None
				aspect_base_filename = None

			######################################################
			## debris-flow initiation criteria
			######################################################
			# necessary for UCA and works well for linear interpolation for gradient
			local_cell_sizes_slope = json_yaml_input_data["local_cell_sizes_slope"] 
			# interpolation_method = json_yaml_input_data["interpolation_method"]

			# if any file names is None, the following is computed
			DEM_debris_flow_initiation_filename = json_yaml_input_data["DEM_debris_flow_initiation_filename"]
			DEM_neighbor_directed_graph_filename = json_yaml_input_data["DEM_neighbor_directed_graph_filename"]
			DEM_UCA_filename = json_yaml_input_data["DEM_UCA_filename"]

			######################################################
			## material data
			######################################################
			if material_file_name is None or (isinstance(material_file_name, str) and material_file_name != "GIS"):
				material_strKey = json_yaml_input_data["material"]
				material = {}
				material_GIS = None
				for strKey, matData in material_strKey.items():
					material[int(strKey)] = matData

					if isinstance(matData["hydraulic"]["SWCC_model"], str) == False or (isinstance(matData["hydraulic"]["SWCC_model"], str) and (matData["hydraulic"]["SWCC_model"] not in ["vG","FX"])):
						print("correct SWCC model needs to be specified")
						sys.exit(2)

					# check format for hydraulic parameters
					for hydro_key in ["k_sat", "initial_suction", "SWCC_a", "SWCC_n", "SWCC_m", "theta_sat", "theta_residual", "soil_m_v", "max_surface_storage"]:
						if isinstance(matData["hydraulic"][hydro_key], (int,float)) and (matData["hydraulic"][hydro_key]<0):
							print("hydraulic parameters should be the zero or positive soil strength values")
							sys.exit(2)

						elif isinstance(matData["hydraulic"][hydro_key], list):
							check_prob_bool = check_prob_input(matData["hydraulic"][hydro_key])
							# does not check numerical value - left to user to double-check
							if not check_prob_bool:
								sys.exit(2)

					# check format for slope stability
					if isinstance(FS_3D_analysis, bool):
						for soil_key in ["unit_weight", "phi", "phi_b", "c"]:
							if isinstance(matData["soil"][soil_key], (int,float)):
								if (soil_key == "unit_weight") and (matData["soil"][soil_key]<=0):
									print("if slope stability is used, should specify the non-zero soil unit weight value")
									sys.exit(2)
								elif (soil_key != "unit_weight") and (matData["soil"][soil_key]<0):
									print("if slope stability is used, should specify the zero or positive soil strength values")
									sys.exit(2)

							elif isinstance(matData["soil"][soil_key], list):
								check_prob_bool = check_prob_input(matData["soil"][soil_key])
								# does not check numerical value - left to user to double-check
								if not check_prob_bool:
									sys.exit(2)

					# check format for root reinforcement
					if FS_3D_apply_root and (isinstance(matData["root"]["unit_weight"], (int,float,list)) and isinstance(matData["root"]["model"], str)) and (matData["root"]["model"] in ["constant", "van Zadelhoff et al. (2021)"]) and (isinstance(matData["root"]["parameters"], list) and len(matData["root"]["parameters"]) == 3):
						for idx in range(3):
							# deterministic
							if isinstance(matData["root"]["parameters"][idx], (int,float)) and matData["root"]["parameters"][idx] < 0.0:
								print("if root strength is considered, the input file should specify non-negative values")
								sys.exit(2)

							# probabilistic
							elif isinstance(matData["root"]["parameters"][idx], list):
								check_prob_bool = check_prob_input(matData["root"]["parameters"][idx])
								# does not check numerical value - left to user to double-check
								if not check_prob_bool:
									sys.exit(2)
					
					elif FS_3D_apply_root == False:
						pass
							
					else:
						print("if constant root strength is considered, the JSON file should specify [c_base (kPa), c_side (kPa), root_depth] or correctly")
						print("if \"van Zadelhoff et al. (2021)\" root strength is considered, the JSON file should specify [alpha2, beta2, RR_max (kN/m)] correctly")
						sys.exit(2)
		
			elif (isinstance(material_file_name, str) and material_file_name == "GIS"):     
				material = {}
				material[1] = json_yaml_input_data["material"]["1"]
				material_GIS = json_yaml_input_data["material_GIS"]
				# if FS_3D_apply_root == False:
				# 	pass
				# elif FS_3D_apply_root and (isinstance(material_GIS["root"]["unit_weight"], str) and isinstance(material_GIS["root"]["model"], str)):
				# 	if (material_GIS["root"]["model"] == "constant") and ((isinstance(material_GIS["root"]["parameters"], list) and len(material_GIS["root"]["parameters"]) == 3 and isinstance(material_GIS["root"]["parameters"][0], str) and isinstance(material_GIS["root"]["parameters"][1], str) and isinstance(material_GIS["root"]["parameters"][2], str)) == False or (isinstance(material[1]["root"]["parameters"], list) and len(material[1]["root"]["parameters"]) == 3 and isinstance(material[1]["root"]["parameters"][0], (int,float)) and isinstance(material[1]["root"]["parameters"][1], (int,float)) and isinstance(material[1]["root"]["parameters"][2], (int,float))) == False):
				# 		print("if constant root strength is considered, the JSON file should specify [c_base (kPa), c_side (kPa), root_depth] correctly")
				# 		sys.exit(2)
				# 	elif (material_GIS["root"]["model"] == "van Zadelhoff et al. (2021)") and ((isinstance(material_GIS["root"]["parameters"], list) and len(material_GIS["root"]["parameters"]) == 3 and isinstance(material_GIS["root"]["parameters"][0], str) and isinstance(material_GIS["root"]["parameters"][1], str) and isinstance(material_GIS["root"]["parameters"][2], str)) == False or (isinstance(material[1]["root"]["parameters"], list) and len(material[1]["root"]["parameters"]) == 3 and isinstance(material[1]["root"]["parameters"][0], (int,float)) and isinstance(material[1]["root"]["parameters"][1], (int,float)) and isinstance(material[1]["root"]["parameters"][2], (int,float))) == False):
				# 		print("if \"van Zadelhoff et al. (2021)\" root strength is considered, the JSON file should specify [alpha2, beta2, RR_max (kN/m)] correctly")
				# 		sys.exit(2)
				# else:
				# 	print("if root strength is considered, the JSON file should specify the root values")
				# 	sys.exit(2)


			# return info
			return filename, input_folder_path, output_folder_path, restarting_simulation_dict, monte_carlo_iteration_max, output_txt_format, plot_option, gamma_w, FS_crit, dz, termination_apply, after_termination_new_times_apply, DEM_surf_dip_infiltraion_apply, DEM_debris_flow_criteria_apply, FS_3D_analysis, FS_3D_iter_limit, FS_3D_tol, cell_size_3DFS_min, cell_size_3DFS_max, superellipse_n_parameter, superellipse_eccen_ratio, FS_3D_apply_side, FS_3D_apply_root, DEM_UCA_compute_all, cpu_num, dt, rain_time_I, debris_t_max, debris_dt, DEM_file_name, increase_DEM_resolution, material_file_name, soil_depth_model, soil_depth_data, ground_water_model, ground_water_data, dip_surf_filename, aspect_surf_filename, dip_base_filename, aspect_base_filename, local_cell_sizes_slope, DEM_debris_flow_initiation_filename, DEM_neighbor_directed_graph_filename, DEM_UCA_filename, material, material_GIS

	except (KeyError, NameError):
		# input file variable error
		print("the keywords or assigned name is misspelled or incorrect in the JSON file. Please double check the inputs and formats of JSON file")		# python script version error 
		sys.exit(1)
	
	except RuntimeError:
		# input file variable error
		print("format not correctly followed")		# python script version error 
		sys.exit(1)	

#############################################################################################################################################################################################
## modified for RALP - stepwise - separate Correlation matrix for each X and Y directions
#############################################################################################################################################################################################
###########################################################################
## generate correlation matrix and random field
###########################################################################
## compute the correlation matrix for each parameters
def compute_correlation_matrix_step_mp(corr_mat_inputs):
	"""
	## Compute the correlation matrix with multiprocessing.

	Parameters
	----------
	uniqueGrid : array
		Grid coordinates.
	CorrLength : int/float
		Correlation length range in X or Y direction.

	Returns
	-------
	CorrMat: 2D Array
		The correlation matrix.
	"""

	# inputs
	uniqueGrid, CorrLength = corr_mat_inputs
	number_of_cells = len(uniqueGrid) * len(uniqueGrid)

	## Allocate correlation matrix.
	if isinstance(CorrLength, (int, float)) and (CorrLength == 0):
		## If the correlation length in either X or Y is zero, then random field with zero correlation length in both direction is created.
		## It check the Matrix folder for the corr. matrix. If there is no, it creates.
		CorrMat = np.identity(number_of_cells)  # identity matrix

	elif isinstance(CorrLength, (int, float)) and (CorrLength > 0):
		xmm,_ = np.meshgrid(uniqueGrid, uniqueGrid)
		xm_t = np.transpose(xmm)
		exponent_t = -2.0 * np.sqrt(np.power(xmm - xm_t, 2)/(CorrLength**2))
		exponent_t = np.where(exponent_t < -100, -np.inf, exponent_t)
		CorrMat = np.exp(exponent_t)

	# if infinite correlation length used (i.e. deterministic):
	elif (isinstance(CorrLength, str) or isinstance(CorrLength, str)) and (CorrLength == "inf"):
		CorrMat = np.ones(number_of_cells)  # identity matrix

	return CorrMat

## when random distribution is used
def generate_random_field_step(n_row, n_col, CorrMatX, CorrMatY, ParMean, ParCoV, DistType, ParMin, ParMax):
	"""
	## Generate random field with given correlation matrix and parameter statistical distributions.

	Args:
		n_row (int): number of rows in DEM domain
		n_col (int): number of columns in DEM domain
		CorrMatX (2D array): correlation matrix for X-direction
		CorrMatY (2D array): correlation matrix for X-direction
		ParMean (float): mean of the parameter
		ParCoV (float): coefficient of variation (CoV) of the parameter
		DistType (str): distribution type {normal 'N' or lognormal 'LN'}
		ParMin (float): minimum value of the parameter
		ParMax (float): maximum value of the parameter

	Returns:
		ParInp (2D array): generated random field of the parameter clipped between ParMin and ParMax
	"""

	## Cholesky decomposition
	Ax = cholesky(CorrMatX, lower=True)
	Ay = cholesky(CorrMatY, lower=True)

	## uniform random number between 0 and 1
	U = np.transpose(np.random.normal(0, 1, (n_row, n_col))) 

	# For normal distribution
	if DistType == "N":
		ParInp = ParMean + (ParCoV * ParMean) * np.transpose(np.matmul(np.matmul(Ax, U), np.transpose(Ay)))
	# For lognormal distribution
	elif DistType == "LN": 
		SigLnPar = np.sqrt(np.log(1 + ParCoV**2))
		MuLnPar = np.log(ParMean) - 0.5 * SigLnPar**2
		ParInp = np.exp(MuLnPar + SigLnPar * np.transpose(np.matmul(np.matmul(Ax, U), np.transpose(Ay))))

	# clip the values to be within the min and max range
	ParInp = np.clip(ParInp, ParMin, ParMax)  

	return ParInp

###########################################################################
## generate material parameters
###########################################################################
## multiprocessing function to generate random field for each iteration of Monte-Carlo simulation
def generate_random_field_step_monte_carlo_iter_mp_filenameOnly(random_field_inputs):

	monte_carlo_iter, DEM_material_id, matID_list, mat_dict, corr_X_mats_dict, corr_Y_mats_dict, dx_dp, dy_dp, dz_dp, rate_dp, theta_dp, press_dp, cumul_dp, n_row, n_col, gridUniqueX, gridUniqueY, deltaX, deltaY, folder_dir, save_file_name, output_txt_format, XYZ_row_or_col_increase_first, DEM_noData, nodata_value, plot_option = random_field_inputs
	
	###############################################################
	## basic information computed
	###############################################################
	# dictionary keys used for the mat_dict
	hydraulic_keys = ["k_sat", "initial_suction", "SWCC_a", "SWCC_n", "SWCC_m", "theta_sat", "theta_residual", "soil_m_v", "max_surface_storage"]
	hydraulic_out_name = ["k_sat", "initial_suction", "SWCC_a", "SWCC_n", "SWCC_m", "theta_sat", "theta_residual", "soil_m_v", "S_max"]
	hydraulic_dp = [rate_dp, theta_dp, press_dp, press_dp, press_dp, theta_dp, theta_dp, theta_dp, cumul_dp]
	soil_keys = ["unit_weight", "phi", "phi_b", "c"]
	soil_dp = [2, 2, 2, press_dp]
	# soil_out_name = soil_keys
	# root_keys = ["unit_weight", "parameters"]
	# root_out_name = ["unit_weight", "c_base", "c_side", "depth", "alpha2", "beta2", "RR_max"]
	# root_dp = [2, press_dp, press_dp, dz_dp, cumul_dp, cumul_dp, press_dp]  
	
	###############################################################
	## templates to store GIS data
	###############################################################
	out_folder_dir = f"{folder_dir}iteration_{monte_carlo_iter}/material/"

	DEM_SWCC_model = np.zeros((DEM_material_id.shape), dtype=int)
	DEM_root_model = np.zeros((DEM_material_id.shape), dtype=int)

	monte_carlo_iter_filename_dict_t = {
		"hydraulic": {
			"SWCC_model": None,
			"SWCC_a": None,
			"SWCC_n": None,
			"SWCC_m": None,
			"k_sat": None,
			"initial_suction": None,
			"theta_sat": None,
			"theta_residual": None,
			"soil_m_v": None,
			"max_surface_storage": None
		},
		"soil": {
			"unit_weight": None,
			"phi": None,
			"phi_b": None,
			"c": None
		},
		"root": {
			"unit_weight": None,
			"model": None,
			"parameters_constant": None,
			"parameters_van_Zadelhoff": None
		}
	}

	###############################################################
	## hydraulic
	###############################################################
	##########################
	# SWCC_model
	##########################
	for matID in matID_list:
		# find all row and column indices of DEM where matching the assigned material ID (mID)
		DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == matID)

		if mat_dict[matID]["hydraulic"]["SWCC_model"] == "vG":
			DEM_SWCC_model[DEM_material_id_row_I, DEM_material_id_col_J] = 0
		elif mat_dict[matID]["hydraulic"]["SWCC_model"] == "FX":
			DEM_SWCC_model[DEM_material_id_row_I, DEM_material_id_col_J] = 1

	# assign the field parameters to the Monte-Carlo iteration dictionary
	monte_carlo_iter_filename_dict_t["hydraulic"]["SWCC_model"] = [f"{out_folder_dir}", f"{save_file_name} - SWCC_model - i{monte_carlo_iter}.{output_txt_format}"]

	# generate output file 
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "SWCC_model", DEM_SWCC_model, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=monte_carlo_iter)

	# generate the plot
	if os.path.exists(f"{out_folder_dir}{save_file_name} - SWCC_model - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - SWCC_model - i{monte_carlo_iter}", 'SWCC_model', gridUniqueX, gridUniqueY, None, DEM_SWCC_model, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	##########################
	# other hydraulic parameters
	##########################
	for DP, hydraulic_str, hydraulic_key in zip(hydraulic_dp, hydraulic_out_name, hydraulic_keys):

		# template
		DEM_temp = np.zeros((DEM_material_id.shape), dtype=float)
		
		for matID in matID_list:
			# assign the random field parameters to the grid cells (zero or positive correlation length)					
			if isinstance(mat_dict[matID]["hydraulic"][hydraulic_key], list) and (isinstance(mat_dict[matID]["hydraulic"][hydraulic_key][3], (int, float)) and isinstance(mat_dict[matID]["hydraulic"][hydraulic_key][4], (int, float))) and ((mat_dict[matID]["hydraulic"][hydraulic_key][3] >= 0) and (mat_dict[matID]["hydraulic"][hydraulic_key][4] >= 0)):
				ParInp = generate_random_field_step(n_row, n_col,  
								corr_X_mats_dict[mat_dict[matID]["hydraulic"][hydraulic_key][3]], # CorrMatX = CorrMatX_dict[CorrLengthX]
								corr_Y_mats_dict[mat_dict[matID]["hydraulic"][hydraulic_key][4]], # CorrMatY = CorrMatY_dict[CorrLengthY]
								mat_dict[matID]["hydraulic"][hydraulic_key][0], # ParMean
								mat_dict[matID]["hydraulic"][hydraulic_key][1], # ParCoV
								mat_dict[matID]["hydraulic"][hydraulic_key][2], # DistType
								mat_dict[matID]["hydraulic"][hydraulic_key][5], # ParMin
								mat_dict[matID]["hydraulic"][hydraulic_key][6]) # ParMax

			# assign the deterministic - infinite correlation length (CorrLengthX, CorrLengthY) or zero coefficient of variation (CoV)
			elif isinstance(mat_dict[matID]["hydraulic"][hydraulic_key], list) and (isinstance(mat_dict[matID]["hydraulic"][hydraulic_key][3], str) and isinstance(mat_dict[matID]["hydraulic"][hydraulic_key][4], str)) and ((mat_dict[matID]["hydraulic"][hydraulic_key][3] == "inf") or (mat_dict[matID]["hydraulic"][hydraulic_key][4] == "inf") or (mat_dict[matID]["hydraulic"][hydraulic_key][1] == 0)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["hydraulic"][hydraulic_key][0])  # use the mean value

			# assign the deterministic - only single numeric value
			elif isinstance(mat_dict[matID]["hydraulic"][hydraulic_key], (int, float)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["hydraulic"][hydraulic_key])

			# find all row and column indices of DEM where matching the assigned material ID (mID)
			DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == int(matID))

			# assign the values to 
			DEM_temp[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

		# assign the field parameters to the Monte-Carlo iteration dictionary
		monte_carlo_iter_filename_dict_t["hydraulic"][hydraulic_key] = [f"{out_folder_dir}", f"{save_file_name} - {hydraulic_str} - i{monte_carlo_iter}.{output_txt_format}"]

		# generate output file 
		generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, hydraulic_str, DEM_temp, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, DP, time=None, iteration=monte_carlo_iter)

		# generate the plot
		if os.path.exists(f"{out_folder_dir}{save_file_name} - {hydraulic_str} - i{monte_carlo_iter}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - {hydraulic_str} - i{monte_carlo_iter}", hydraulic_str, gridUniqueX, gridUniqueY, None, DEM_temp, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	###############################################################
	## soil
	###############################################################
	for DP, soil_key in zip(soil_dp, soil_keys):

		# template
		DEM_temp = np.zeros((DEM_material_id.shape), dtype=float)
		
		for matID in matID_list:	
			# assign the random field parameters to the grid cells (zero or positive correlation length)					
			if isinstance(mat_dict[matID]["soil"][soil_key], list) and (isinstance(mat_dict[matID]["soil"][soil_key][3], (int, float)) and isinstance(mat_dict[matID]["soil"][soil_key][4], (int, float))) and ((mat_dict[matID]["soil"][soil_key][3] >= 0) and (mat_dict[matID]["soil"][soil_key][4] >= 0)):
				ParInp = generate_random_field_step(n_row, n_col,  
								corr_X_mats_dict[mat_dict[matID]["soil"][soil_key][3]], # CorrMatX = CorrMatX_dict[CorrLengthX]
								corr_Y_mats_dict[mat_dict[matID]["soil"][soil_key][4]], # CorrMatY = CorrMatY_dict[CorrLengthY]
								mat_dict[matID]["soil"][soil_key][0], # ParMean
								mat_dict[matID]["soil"][soil_key][1], # ParCoV
								mat_dict[matID]["soil"][soil_key][2], # DistType
								mat_dict[matID]["soil"][soil_key][5], # ParMin
								mat_dict[matID]["soil"][soil_key][6]) # ParMax

			# assign the deterministic - infinite correlation length (CorrLengthX, CorrLengthY) or zero coefficient of variation (CoV)
			elif isinstance(mat_dict[matID]["soil"][soil_key], list) and (isinstance(mat_dict[matID]["soil"][soil_key][3], str) and isinstance(mat_dict[matID]["soil"][soil_key][4], str)) and ((mat_dict[matID]["soil"][soil_key][3] == "inf") or (mat_dict[matID]["soil"][soil_key][4] == "inf") or (mat_dict[matID]["soil"][soil_key][1] == 0)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["soil"][soil_key][0])  # use the mean value

			# assign the deterministic - only single numeric value
			elif isinstance(mat_dict[matID]["soil"][soil_key], (int, float)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["soil"][soil_key])

			# find all row and column indices of DEM where matching the assigned material ID (mID)
			DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == int(matID))

			# assign the values to 
			DEM_temp[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

		# assign the field parameters to the Monte-Carlo iteration dictionary
		monte_carlo_iter_filename_dict_t["soil"][soil_key] = [f"{out_folder_dir}", f"{save_file_name} - soil_{soil_key} - i{monte_carlo_iter}.{output_txt_format}"]

		# generate output file 
		generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, f"soil_{soil_key}", DEM_temp, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, DP, time=None, iteration=monte_carlo_iter)

		# generate the plot
		if os.path.exists(f"{out_folder_dir}{save_file_name} - soil_{soil_key} - i{monte_carlo_iter}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - soil_{soil_key} - i{monte_carlo_iter}", soil_key, gridUniqueX, gridUniqueY, None, DEM_temp, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	###############################################################
	## root
	###############################################################
	##########################
	## model used for root reinforcement
	##########################
	for matID in matID_list:
		# find all row and column indices of DEM where matching the assigned material ID (mID)
		DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == matID)

		if mat_dict[matID]["root"]["model"] == "constant":
			DEM_root_model[DEM_material_id_row_I, DEM_material_id_col_J] = 0
		elif mat_dict[matID]["root"]["model"] == "van Zadelhoff et al. (2021)":
			DEM_root_model[DEM_material_id_row_I, DEM_material_id_col_J] = 1

	# assign the field parameters to the Monte-Carlo iteration dictionary
	monte_carlo_iter_filename_dict_t["root"]["model"] = [f"{out_folder_dir}", f"{save_file_name} - root_model - i{monte_carlo_iter}.{output_txt_format}"]

	# generate output file 
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_model", DEM_root_model, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=monte_carlo_iter)

	# generate the plot
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_model - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_model - i{monte_carlo_iter}", 'root_model', gridUniqueX, gridUniqueY, None, DEM_root_model, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	##########################
	## root unit weight
	##########################
	DEM_root_unit_weight = np.zeros((DEM_material_id.shape), dtype=float)   # DEM vegetation unit weight
		
	for matID in matID_list:	
		# assign the random field parameters to the grid cells (zero or positive correlation length)					
		if isinstance(mat_dict[matID]["root"]["unit_weight"], list) and (isinstance(mat_dict[matID]["root"]["unit_weight"][3], (int, float)) and isinstance(mat_dict[matID]["root"]["unit_weight"][4], (int, float))) and ((mat_dict[matID]["root"]["unit_weight"][3] >= 0) and (mat_dict[matID]["root"]["unit_weight"][4] >= 0)):
			ParInp = generate_random_field_step(n_row, n_col,  
							corr_X_mats_dict[mat_dict[matID]["root"]["unit_weight"][3]], # CorrMatX = CorrMatX_dict[CorrLengthX]
							corr_Y_mats_dict[mat_dict[matID]["root"]["unit_weight"][4]], # CorrMatY = CorrMatY_dict[CorrLengthY]
							mat_dict[matID]["root"]["unit_weight"][0], # ParMean
							mat_dict[matID]["root"]["unit_weight"][1], # ParCoV
							mat_dict[matID]["root"]["unit_weight"][2], # DistType
							mat_dict[matID]["root"]["unit_weight"][5], # ParMin
							mat_dict[matID]["root"]["unit_weight"][6]) # ParMax

		# assign the deterministic - infinite correlation length (CorrLengthX, CorrLengthY) or zero coefficient of variation (CoV)
		elif isinstance(mat_dict[matID]["root"]["unit_weight"], list) and (isinstance(mat_dict[matID]["root"]["unit_weight"][3], str) and isinstance(mat_dict[matID]["root"]["unit_weight"][4], str)) and ((mat_dict[matID]["root"]["unit_weight"][3] == "inf") or (mat_dict[matID]["root"]["unit_weight"][4] == "inf") or (mat_dict[matID]["root"]["unit_weight"][1] == 0)):
			ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["root"]["unit_weight"][0])  # use the mean value

		# assign the deterministic - only single numeric value
		elif isinstance(mat_dict[matID]["root"]["unit_weight"], (int, float)):
			ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["root"]["unit_weight"])

		# find all row and column indices of DEM where matching the assigned material ID (mID)
		DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == int(matID))

		# assign the values to 
		DEM_root_unit_weight[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

	# assign the field parameters to the Monte-Carlo iteration dictionary
	monte_carlo_iter_filename_dict_t["root"]["unit_weight"] = [f"{out_folder_dir}", f"{save_file_name} - root_unit_weight - i{monte_carlo_iter}.{output_txt_format}"]

	# generate output file 
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_unit_weight", DEM_root_unit_weight, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 2, time=None, iteration=monte_carlo_iter)

	# generate the plot
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_unit_weight - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_unit_weight - i{monte_carlo_iter}", 'root_unit_weight', gridUniqueX, gridUniqueY, None, DEM_root_unit_weight, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	##########################
	## root model parameter
	##########################
	DEM_param_c_base = np.zeros((DEM_material_id.shape), dtype=float)   # DEM root model parameter root_c_base
	DEM_param_c_side = np.zeros((DEM_material_id.shape), dtype=float)   # DEM root model parameter root_c_side	
	DEM_param_root_depth = np.zeros((DEM_material_id.shape), dtype=float)    # DEM root model parameter root_depth

	DEM_param_vZ_alpha2 = np.zeros((DEM_material_id.shape), dtype=float)   # DEM root model parameter root_alpha2
	DEM_param_vZ_beta2 = np.zeros((DEM_material_id.shape), dtype=float)    # DEM root model parameter root_beta2	
	DEM_param_vZ_RR_max = np.zeros((DEM_material_id.shape), dtype=float)   # DEM root model parameter root_RR_max

	for param_idx in range(3):
		for matID in matID_list:	
			# assign the random field parameters to the grid cells (zero or positive correlation length)					
			if isinstance(mat_dict[matID]["root"]["parameters"][param_idx], list) and (isinstance(mat_dict[matID]["root"]["parameters"][param_idx][3], (int, float)) and isinstance(mat_dict[matID]["root"]["parameters"][param_idx][4], (int, float))) and ((mat_dict[matID]["root"]["parameters"][param_idx][3] >= 0) and (mat_dict[matID]["root"]["parameters"][param_idx][4] >= 0)):
				ParInp = generate_random_field_step(n_row, n_col,  
								corr_X_mats_dict[mat_dict[matID]["root"]["parameters"][param_idx][3]], # CorrMatX = CorrMatX_dict[CorrLengthX]
								corr_Y_mats_dict[mat_dict[matID]["root"]["parameters"][param_idx][4]], # CorrMatY = CorrMatY_dict[CorrLengthY]
								mat_dict[matID]["root"]["parameters"][param_idx][0], # ParMean
								mat_dict[matID]["root"]["parameters"][param_idx][1], # ParCoV
								mat_dict[matID]["root"]["parameters"][param_idx][2], # DistType
								mat_dict[matID]["root"]["parameters"][param_idx][5], # ParMin
								mat_dict[matID]["root"]["parameters"][param_idx][6]) # ParMax

			# assign the deterministic - infinite correlation length (CorrLengthX, CorrLengthY) or zero coefficient of variation (CoV)
			elif isinstance(mat_dict[matID]["root"]["parameters"][param_idx], list) and (isinstance(mat_dict[matID]["root"]["parameters"][param_idx][3], str) and isinstance(mat_dict[matID]["root"]["parameters"][param_idx][4], str)) and ((mat_dict[matID]["root"]["parameters"][param_idx][3] == "inf") or (mat_dict[matID]["root"]["parameters"][param_idx][4] == "inf") or (mat_dict[matID]["root"]["parameters"][param_idx][1] == 0)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["root"]["parameters"][param_idx][0])  # use the mean value

			# assign the deterministic - only single numeric value
			elif isinstance(mat_dict[matID]["root"]["parameters"][param_idx], (int, float)):
				ParInp = np.ones((n_row, n_col))*float(mat_dict[matID]["root"]["parameters"][param_idx])

			# find all row and column indices of DEM where matching the assigned material ID (mID)
			DEM_material_id_row_I, DEM_material_id_col_J = np.where(DEM_material_id == int(matID))

			# assign the values to 
			if mat_dict[matID]["root"]["model"] == "constant":
				if param_idx == 0:
					DEM_param_c_base[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]
				elif param_idx == 1:
					DEM_param_c_side[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]
				elif param_idx == 2:
					DEM_param_root_depth[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

			elif mat_dict[matID]["root"]["model"] == "van Zadelhoff et al. (2021)":
				if param_idx == 0:
					DEM_param_vZ_alpha2[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]
				elif param_idx == 1:
					DEM_param_vZ_beta2[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]
				elif param_idx == 2:
					DEM_param_vZ_RR_max[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

	# assign the field parameters to the Monte-Carlo iteration dictionary
	monte_carlo_iter_filename_dict_t["root"]["parameters_constant"] = [
		[f"{out_folder_dir}", f"{save_file_name} - root_c_base - i{monte_carlo_iter}.{output_txt_format}"],
		[f"{out_folder_dir}", f"{save_file_name} - root_c_side - i{monte_carlo_iter}.{output_txt_format}"],
		[f"{out_folder_dir}", f"{save_file_name} - root_depth - i{monte_carlo_iter}.{output_txt_format}"]
	]
	monte_carlo_iter_filename_dict_t["root"]["parameters_van_Zadelhoff"] = [
		[f"{out_folder_dir}", f"{save_file_name} - root_alpha2 - i{monte_carlo_iter}.{output_txt_format}"],
		[f"{out_folder_dir}", f"{save_file_name} - root_beta2 - i{monte_carlo_iter}.{output_txt_format}"],
		[f"{out_folder_dir}", f"{save_file_name} - root_RR_max - i{monte_carlo_iter}.{output_txt_format}"]
	]

	# generate output file 
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_c_base", DEM_param_c_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, press_dp, time=None, iteration=monte_carlo_iter)
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_c_side", DEM_param_c_side, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, press_dp, time=None, iteration=monte_carlo_iter)
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_depth", DEM_param_root_depth, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=monte_carlo_iter)

	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_alpha2", DEM_param_vZ_alpha2, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=None, iteration=monte_carlo_iter)
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_beta2", DEM_param_vZ_beta2, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=None, iteration=monte_carlo_iter)
	generate_output_GIS(output_txt_format, out_folder_dir, save_file_name, "root_RR_max", DEM_param_vZ_RR_max, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, press_dp, time=None, iteration=monte_carlo_iter)

	# generate the plot
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_c_base - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_c_base - i{monte_carlo_iter}", 'root_c_base', gridUniqueX, gridUniqueY, None, DEM_param_c_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_c_side - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_c_side - i{monte_carlo_iter}", 'root_c_side', gridUniqueX, gridUniqueY, None, DEM_param_c_side, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_depth - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_depth - i{monte_carlo_iter}", 'root_depth', gridUniqueX, gridUniqueY, None, DEM_param_root_depth, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_alpha2 - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_alpha2 - i{monte_carlo_iter}", 'root_alpha2', gridUniqueX, gridUniqueY, None, DEM_param_vZ_alpha2, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_beta2 - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_beta2 - i{monte_carlo_iter}", 'root_beta2', gridUniqueX, gridUniqueY, None, DEM_param_vZ_beta2, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
	if os.path.exists(f"{out_folder_dir}{save_file_name} - root_RR_max - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{save_file_name} - root_RR_max - i{monte_carlo_iter}", 'root_RR_max', gridUniqueX, gridUniqueY, None, DEM_param_vZ_RR_max, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

	return monte_carlo_iter_filename_dict_t

## Define random material parameter step Monte Carlo
def define_random_field_step_monte_carlo_filenameOnly(DEM_material_id, uniqueGridX, uniqueGridY, deltaX, deltaY, mat_dict, max_cpu_num, iterations=500, output_folder_dir="./", save_file_name="", output_txt_format="csv", XYZ_row_or_col_increase_first="row", DEM_noData=None, nodata_value=-9999, dz_incre=0.1, plot=False):
	"""
	## Random fields are created.

	Parameters
	----------
	DEM_material_id : 2D array (int)
		Material ID for each grid cell.
	uniqueGridX : array
		Grid X coordinates.
	uniqueGridY : array
		Grid Y coordinates.
	deltaX : int/float
		Cell size in X direction.
	deltaY : int/float
		Cell size in Y direction.
	mat_dict : dictionary
		contains the material properties for each zone (e.g. matID):
		[0Mean properties, 1coefficient of variation (CoV), 2Statistical Distribution, 3Correlation Length in X-direction, 4Correlation Length in Y-direction, 5Minimum value, 6Maximum value]
			Statistical Distribution: 'LN' (log-normal) or 'N' (normal) 
	max_cpu_num : int
		maximum number of CPU cores to use for parallel processing.
	iterations : int (defailt=500)
		number of Monte-Carlo (MC) iterations (i.e. N) to generate random field data.
	output_folder_dir : str
		the output folder directory to save the generated Nth Monte-Carlo GIS files. (default="./")
	save_file_name : str
		the project name to save the generated Nth Monte-Carlo GIS files. (default="")
	output_txt_format : str
		the output file format for the generated Nth Monte-Carlo GIS files. (default="csv")
	XYZ_row_or_col_increase_first : str
		specifies whether the XYZ coordinates increase first by row or column. (default="row")
	DEM_noData : 2D numpy array
		the no-data value for the DEM data. (default=None)
	nodata_value : float
		the value to use for no-data cells. (default=-9999)
	dz_incre : float
		the increment value for the Z-axis. (default=0.1)
	plot : bool 
		whether to plot the generated random field data. If True, the generated random field data will be plotted. (default=False)

	Returns
	-------
	monte_carlo_iter_filename_dict: dict
		Generate N Random field data of the parameters
	"""

	###############################################################
	## compute frequently used values
	###############################################################
	## Create a coordinate mesh
	# number_of_cells = len(uniqueGridX) * len(uniqueGridY)
	n_row, n_col = DEM_material_id.shape

	## identify max number of material zones
	matID_list = np.unique(DEM_material_id).tolist()

	## decimal precision for the GIS files
	dx_dp = -decimal.Decimal(str(deltaX)).as_tuple().exponent
	dy_dp = -decimal.Decimal(str(deltaY)).as_tuple().exponent
	
	# decimal places to round - avoid floating point errors
	dz_dp = -decimal.Decimal(str(dz_incre)).as_tuple().exponent
	rate_dp = -decimal.Decimal(str(1e-12)).as_tuple().exponent  	# rate - f, I
	theta_dp = 6    # theta_i, theta_s, theta_r, delta_theta
	press_dp = 4	# psi, u_w
	cumul_dp = 6    # F, S, RO, P 

	###############################################################
	## compute unique correlation matrix for each parameters
	###############################################################
	"""assume that at least one of the parameters will be considered for statistical analysis"""
	
	corLX_unique = []
	corLY_unique = []
	corL_X_set_unique_input = []
	corL_Y_set_unique_input = []

	for matID in matID_list:
		for key_level1 in mat_dict[matID]:

			if key_level1 == "soil" or key_level1 == "hydraulic":
				for key_level2 in mat_dict[matID][key_level1]:
					if isinstance(mat_dict[matID][key_level1][key_level2], list) and (mat_dict[matID][key_level1][key_level2][3] not in corLX_unique):
						corLX_unique.append( mat_dict[matID][key_level1][key_level2][3] ) 
						corL_X_set_unique_input.append( (uniqueGridX, mat_dict[matID][key_level1][key_level2][3]) )			
						
					if isinstance(mat_dict[matID][key_level1][key_level2], list) and (mat_dict[matID][key_level1][key_level2][4] not in corLY_unique):
						corLY_unique.append( mat_dict[matID][key_level1][key_level2][4] )
						corL_Y_set_unique_input.append( (uniqueGridY, mat_dict[matID][key_level1][key_level2][4]) )

			elif key_level1 == "root":   # nest list exists in the material dictionary related to root
				for key_level2 in mat_dict[matID][key_level1]:
					if key_level2 != "parameters" and isinstance(mat_dict[matID][key_level1][key_level2], list) and (mat_dict[matID][key_level1][key_level2][3] not in corLX_unique):
						corLX_unique.append( mat_dict[matID][key_level1][key_level2][3] )
						corL_X_set_unique_input.append( (uniqueGridX, mat_dict[matID][key_level1][key_level2][3]) )
					if key_level2 != "parameters" and isinstance(mat_dict[matID][key_level1][key_level2], list) and (mat_dict[matID][key_level1][key_level2][4] not in corLY_unique):
						corLY_unique.append( mat_dict[matID][key_level1][key_level2][4] )
						corL_Y_set_unique_input.append( (uniqueGridY, mat_dict[matID][key_level1][key_level2][4]) )

					if key_level2 == "parameters":
						for idx in range(3):
							if isinstance(mat_dict[matID][key_level1][key_level2][idx], list) and (mat_dict[matID][key_level1][key_level2][idx][3] not in corLX_unique):
								corLX_unique.append( mat_dict[matID][key_level1][key_level2][idx][3])
								corL_X_set_unique_input.append( (uniqueGridX, mat_dict[matID][key_level1][key_level2][idx][3]) )

							if isinstance(mat_dict[matID][key_level1][key_level2][idx], list) and (mat_dict[matID][key_level1][key_level2][idx][4] not in corLY_unique):
								corLY_unique.append( mat_dict[matID][key_level1][key_level2][idx][4] )
								corL_Y_set_unique_input.append( (uniqueGridY, mat_dict[matID][key_level1][key_level2][idx][4]) )

	if len(corLX_unique) != 0 and len(corLY_unique) != 0:

		with mp.Pool(processes=max_cpu_num) as pool: 
			## compute correlation matrix for each parameters in each material ID zone
			corr_mats_X = pool.map(compute_correlation_matrix_step_mp, corL_X_set_unique_input)
			## close the pool
			pool.close()	
			pool.join()

		with mp.Pool(processes=max_cpu_num) as pool: 
			## compute correlation matrix for each parameters in each material ID zone
			corr_mats_Y = pool.map(compute_correlation_matrix_step_mp, corL_Y_set_unique_input)
			## close the pool
			pool.close()	
			pool.join()

		## create a dictionary for each parameters	
		corr_mats_X_dict = {}
		corr_mats_Y_dict = {}
		for idx,key in enumerate(corLX_unique):
			corr_mats_X_dict[key] = corr_mats_X[idx]
		for idx,key in enumerate(corLY_unique):
			corr_mats_Y_dict[key] = corr_mats_Y[idx]
	
	else:
		corr_mats_X_dict = {}
		corr_mats_Y_dict = {}

	###############################################################
	## generating random fields for Monte-Carlo iterations through multiprocessing
	###############################################################
	# multiprocessing input
	random_field_inputs = [(monte_carlo_iter+1, DEM_material_id, matID_list, mat_dict, corr_mats_X_dict, corr_mats_Y_dict, dx_dp, dy_dp, dz_dp, rate_dp, theta_dp, press_dp, cumul_dp, n_row, n_col, uniqueGridX, uniqueGridY, deltaX, deltaY, output_folder_dir, save_file_name, output_txt_format, XYZ_row_or_col_increase_first, DEM_noData, nodata_value, plot) for monte_carlo_iter in range(iterations)]

	# multiprocessing output
	with mp.Pool(processes=max_cpu_num) as pool: 
		## compute correlation matrix for each parameters in each material ID zone
		monte_carlo_dict_mp_t = pool.map(generate_random_field_step_monte_carlo_iter_mp_filenameOnly, random_field_inputs)
		## close the pool
		pool.close()	
		pool.join()

	# Monte-Carlo iterations database 
	monte_carlo_iter_filename_dict = {}  # key: iteration ID integer (N), contains the random field data values GIS file directory and name

	for idx,gis_dict_t in enumerate(monte_carlo_dict_mp_t):
		monte_carlo_iter_filename_dict[idx+1] = deepcopy(gis_dict_t)

	return monte_carlo_iter_filename_dict

###########################################################################
## generate rainfall intensity
###########################################################################
## multiprocessing function to generate random field for each iteration of Monte-Carlo simulation
def generate_rainfall_GIS_each_time_step(rainfall_GIS_each_time_step_input):
	"""Generate rainfall GIS data for each time step.

	Parameters
	-------
	time : int
		Time step.
	monte_carlo_iter : int
		Monte Carlo iteration number.	
	start_t : float
		Start time for the rainfall data.
	end_t : float	
		End time for the rainfall data.
	r_data : str, list, int, float
		Rainfall data. If str, it is the path to a GIS file. If list, it is a list of rain gauge data.
		If int or float, it is a constant rainfall intensity.
	n_row : int
		Number of rows in the grid.
	n_col : int	
		Number of columns in the grid.
	uniqueGridX : 1D numpy array
		X-coordinates of the grid.
	uniqueGridY : 1D numpy array
		Y-coordinates of the grid.
	deltaX : float
		Grid spacing in the X direction.
	deltaY : float	
		Grid spacing in the Y direction.
	corr_mats_X_dict : dict	
		Dictionary of correlation matrices in the X direction.
	corr_mats_Y_dict : dict	
		Dictionary of correlation matrices in the Y direction.
	input_folder_path : str
		Path to the input folder.
	output_folder_path : str	
		Path to the output folder.
	output_txt_format : str
		Output file format. options {"csv", "grd", "asc"}
	filename : str
		Filename for the output files.
	DEM_noData : float
		Value representing location of no data in the DEM.
	nodata_value : float
		Value representing no data in the output files.
	XYZ_row_or_col_increase_first : str
		Indicates whether the first column or row of the grid increases first. options {"row", "col"}
	dx_dp : float
		decimal points for X-coordinate.
	dy_dp : float
		decimal points for Y-coordinate.
	I_dp : float
		decimal points for rainfall intensity.
	plot_option : bool	
		If True, generate plots for the output data.

	Returns
	-------
	rain_I_filename : str
		Rainfall intensity GIS data filename
	"""	
	
	# unpack the input
	time, monte_carlo_iter, start_t, end_t, r_data, n_row, n_col, uniqueGridX, uniqueGridY, deltaX, deltaY, corr_mats_X_dict, corr_mats_Y_dict, input_folder_path, output_folder_path, output_txt_format, filename, DEM_noData, nodata_value, XYZ_row_or_col_increase_first, dx_dp, dy_dp, I_dp, plot_option = rainfall_GIS_each_time_step_input

	out_folder_dir = f"{output_folder_path}iteration_{monte_carlo_iter}/intensity/"

	# uniformly apply
	if isinstance(r_data, (int, float)):  
		rain_I_GIS = np.ones((n_row, n_col))*r_data 

	# from GIS file
	elif isinstance(r_data, str): 
		rain_I_GIS, _, _ = read_GIS_data(r_data, input_folder_path, full_output=False)

	# from nearest rain gauge data
	elif isinstance(r_data, list) and len(r_data[0]) == 3: 
		# format: [[X, Y, intensity], ...]
		xx, yy = np.meshgrid(uniqueGridX, uniqueGridY)
		xGrids = np.ravel(xx)
		yGrids = np.ravel(yy)

		xy_Data = np.array([[x,y] for (x,y,_) in r_data])
		I_Data = np.array([[I] for (_,_,I) in r_data])

		interp_nearest_I_data = griddata(xy_Data, I_Data, (xGrids, yGrids), method='nearest')
		rain_I_GIS = np.reshape(interp_nearest_I_data, (n_row, n_col))

	# from nearest rain gauge data with probabilistic
	elif isinstance(r_data, list) and len(r_data[0]) == 9:  
		# format: [[0X, 1Y, 2Mean, 3CoV, 4Prob_Dist., 5Corr_Length_X, 6Corr_Length_Y, 7Min, 8Max], ...]

		# material ID assigned - ID based on the closest rain gauge point
		xx, yy = np.meshgrid(uniqueGridX, uniqueGridY)
		xGrids = np.ravel(xx)
		yGrids = np.ravel(yy)

		xy_Data = np.array([[x,y] for (x,y,_,_,_,_,_,_,_) in r_data])
		id_Data = np.arange(len(r_data))

		interp_nearest_id_data = griddata(xy_Data, id_Data, (xGrids, yGrids), method='nearest')
		rain_ID = np.reshape(interp_nearest_id_data, (n_row, n_col))

		# template
		rain_I_GIS = np.zeros((n_row, n_col), dtype=float)

		# go through each rain gauge points to assign the probabilistic rainfall intensity
		for rD in range(len(r_data)):

			# assign the random field parameters to the grid cells (zero or positive correlation length)		
			if (isinstance(r_data[rD][5], (int, float)) and isinstance(r_data[rD][6], (int, float))) and ((r_data[rD][5] >= 0) and (r_data[rD][6] >= 0)):
				ParInp = generate_random_field_step(n_row, n_col,  
									corr_mats_X_dict[r_data[rD][5]], # CorrMatX = CorrMatX_dict[CorrLengthX]
									corr_mats_Y_dict[r_data[rD][6]], # CorrMatY = CorrMatY_dict[CorrLengthY]
									r_data[rD][2], # ParMean
									r_data[rD][3], # ParCoV
									r_data[rD][4], # DistType
									r_data[rD][7], # ParMin
									r_data[rD][8]) # ParMax

			# assign the deterministic - infinite correlation length (CorrLengthX, CorrLengthY) or zero coefficient of variation (CoV)
			elif ((isinstance(r_data[rD][5], str) and (r_data[rD][5] == "inf"))) or ((isinstance(r_data[rD][6], str) and (r_data[rD][6] == "inf"))) or ((isinstance(r_data[rD][3], (int, float)) and (r_data[rD][3] == 0))):
				ParInp = np.ones((n_row, n_col))*float(r_data[rD][2])  # use the mean value

			# find all row and column indices of DEM where matching the assigned material ID (mID)
			DEM_material_id_row_I, DEM_material_id_col_J = np.where(rain_ID == rD)

			# assign the values to rain_I_GIS
			rain_I_GIS[DEM_material_id_row_I, DEM_material_id_col_J] = ParInp[DEM_material_id_row_I, DEM_material_id_col_J]

	# generate output file 
	generate_output_GIS(output_txt_format, out_folder_dir, filename, "rain_I", rain_I_GIS, DEM_noData, nodata_value, uniqueGridX, uniqueGridY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, I_dp, time=time, iteration=monte_carlo_iter)

	# generate the plot
	if os.path.exists(f"{out_folder_dir}{filename} - rain_I - t{time} - i{monte_carlo_iter}.html") == False and plot_option:
		plot_DEM_mat_map_v7_0(f"{out_folder_dir}", f"{filename} - rain_I - t{time} - i{monte_carlo_iter}", 'rain_I', uniqueGridX, uniqueGridY, None, rain_I_GIS, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)

	return (start_t, end_t, f"{out_folder_dir}", f"{filename} - rain_I - t{time} - i{monte_carlo_iter}.{output_txt_format}")

## Define random rainfall step Monte Carlo 
def define_random_rainfall_step_monte_carlo(rain_time_I, uniqueGridX, uniqueGridY, deltaX, deltaY, max_cpu_num, input_folder_path, output_folder_path, filename, iterations=500, output_txt_format="csv", XYZ_row_or_col_increase_first="row", DEM_noData=None, nodata_value=-9999, I_dp=9, plot=False):	
	"""Random fields are created for rainfall

	Parameters
	----------
	rain_time_I: list
		List of time steps for the rainfall data. format = [start_time, end_time, rainfall_data]
			rainfall_data can be:
			(1) value uniformly applied everywhere. format = int or float
			(2) filename of GIS that provide spatially varying rainfall intensity. format = string (must contain the file extension)
			(3) series of rain gauge points for nearest neighbor interpolation (or Voronoi diagram). format = [[X, Y, recorded rainfall intensity value in int or float], ...]
			(4) probabilistic of rain gauge points for nearest neighbor interpolation (or Voronoi diagram). format = [[X, Y, Mean, CoV, Prob. Dist., Corr. Length X, Corr. Length Y, Min, Max], ...]
	uniqueGridX : array
		Grid X coordinates.
	uniqueGridY : array
		Grid Y coordinates.
	deltaX : int/float
		Cell size in X direction.
	deltaY : int/float
		Cell size in Y direction.
	max_cpu_num : int
		maximum number of CPU cores to use for parallel processing.
	input_folder_path : str
		Path to the input folder.
	output_folder_path : str
		Path to the output folder.
	filename : str
		Filename for the output files.
	iterations : int (defailt=500)
		number of Monte-Carlo (MC) iterations (i.e. N) to generate random field data.
	output_txt_format : str
		the output file format for the generated Nth Monte-Carlo GIS files. (default="csv")
	XYZ_row_or_col_increase_first : str
		specifies whether the XYZ coordinates increase first by row or column. (default="row")
	DEM_noData : 2D numpy array
		the no-data value for the DEM data. (default=None)
	nodata_value : float
		the value to use for no-data cells. (default=-9999)
	I_dp : int
		decimal points for rainfall intensity. (default=9)
	plot : bool 
		whether to plot the generated random field data. If True, the generated random field data will be plotted. (default=False)
	"""

	###############################################################
	## compute frequently used values
	###############################################################
	## Create a coordinate mesh
	# number_of_cells = len(uniqueGridX) * len(uniqueGridY)
	n_row, n_col = len(uniqueGridY), len(uniqueGridX)

	## decimal precision for the GIS files
	dx_dp = -decimal.Decimal(str(deltaX)).as_tuple().exponent
	dy_dp = -decimal.Decimal(str(deltaY)).as_tuple().exponent

	###############################################################
	## compute unique correlation matrix for each parameters
	###############################################################
	"""assume that at least one of the parameters will be considered for statistical analysis"""
	
	corLX_unique = []
	corLY_unique = []
	corL_X_set_unique_input = []
	corL_Y_set_unique_input = []

	for (_,_,r_data) in rain_time_I:
		if isinstance(r_data, list) and len(r_data) > 0 and len(r_data[0]) == 9:  # probabilistic of rain gauge points for nearest neighbor interpolation (or Voronoi diagram)
			for idx in range(len(r_data)):
				# format = [[0X, 1Y, 2Mean, 3CoV, 4Prob. Dist., 5Corr. Length X, 6Corr. Length Y, 7Min, 8Max], ...]
				corLX_unique.append(r_data[idx][5])
				corLY_unique.append(r_data[idx][6])
				corL_X_set_unique_input.append((uniqueGridX, r_data[idx][5]))
				corL_Y_set_unique_input.append((uniqueGridY, r_data[idx][6]))

	if len(corLX_unique) != 0 and len(corLY_unique) != 0:

		with mp.Pool(processes=max_cpu_num) as pool: 
			## compute correlation matrix for each parameters in each material ID zone
			corr_mats_X = pool.map(compute_correlation_matrix_step_mp, corL_X_set_unique_input)
			## close the pool
			pool.close()	
			pool.join()

		with mp.Pool(processes=max_cpu_num) as pool: 
			## compute correlation matrix for each parameters in each material ID zone
			corr_mats_Y = pool.map(compute_correlation_matrix_step_mp, corL_Y_set_unique_input)
			## close the pool
			pool.close()	
			pool.join()

		## create a dictionary for each parameters	
		corr_mats_X_dict = {}
		corr_mats_Y_dict = {}
		for idx,key in enumerate(corLX_unique):
			corr_mats_X_dict[key] = corr_mats_X[idx]
		for idx,key in enumerate(corLY_unique):
			corr_mats_Y_dict[key] = corr_mats_Y[idx]
	
	else:
		corr_mats_X_dict = {}
		corr_mats_Y_dict = {}

	###############################################################
	## generating rfainfall intensity GIS for each time step and Monte-Carlo iteration
	###############################################################
	rainfall_GIS_each_time_step_input = []
	for monte_carlo_iter in range(1,iterations+1):
		for time,(start_t,end_t,r_data) in enumerate(rain_time_I):
			rainfall_GIS_each_time_step_input.append((time, monte_carlo_iter, start_t, end_t, r_data, n_row, n_col, uniqueGridX, uniqueGridY, deltaX, deltaY, corr_mats_X_dict, corr_mats_Y_dict, input_folder_path, output_folder_path, output_txt_format, filename, DEM_noData, nodata_value, XYZ_row_or_col_increase_first, dx_dp, dy_dp, I_dp, plot))

	# multiprocessing output
	with mp.Pool(processes=max_cpu_num) as pool: 
		## compute correlation matrix for each parameters in each material ID zone
		rainfall_GIS_name_t = pool.map(generate_rainfall_GIS_each_time_step, rainfall_GIS_each_time_step_input)
		## close the pool
		pool.close()	
		pool.join()

	# dict of rainfall GIS data filenames
	rainfall_GIS_dict = {}  # key: iteration ID integer (N), rainfall GIS data filenames
	for idx, (gis_t, (start_t, end_t, gis_dir_t, gis_name_t)) in enumerate(zip(rainfall_GIS_each_time_step_input, rainfall_GIS_name_t)):
		if gis_t[1] not in rainfall_GIS_dict.keys():
			rainfall_GIS_dict[gis_t[1]] = {str(gis_t[0]): [gis_dir_t, gis_name_t, start_t, end_t]}  # time, rainfall data
		else:
			temp_dict = rainfall_GIS_dict[gis_t[1]]
			temp_dict[str(gis_t[0])] = [gis_dir_t, gis_name_t, start_t, end_t]
			rainfall_GIS_dict[gis_t[1]] = deepcopy(temp_dict)
			del temp_dict
	
	return rainfall_GIS_dict


###########################################################################
## 2D and 3D plotly interactive map - HTML
###########################################################################
# plot infiltration and infinite slope stability computed values
def plot_DEM_mat_map_v7_0(folder_path, plot_naming, z_label, gridUniqueX, gridUniqueY, DEM, DEM_data, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000):
	"""Generate a 2D contour plot of DEM data and save it as an HTML file.

	Args:
		folder_path (str): Directory to save the plot.
		plot_naming (str): Name of the plot.
		z_label (str): Label for the z-axis.
		gridUniqueX (list or np.ndarray): Unique x-coordinates of the grid.
		gridUniqueY (list or np.ndarray): Unique y-coordinates of the grid.
		DEM (np.ndarray): 2D array of DEM elevation data.
		DEM_data (np.ndarray): 2D array of data to plot.
		contour_limit (list, optional): Contour limits [min, max, interval]. Defaults to None.
		open_html (bool, optional): Whether to open the plot in a browser. Defaults to False.
		layout_width (int, optional): Width of the plot layout. Defaults to 1000.
		layout_height (int, optional): Height of the plot layout. Defaults to 1000.

	Generates:
		html files: 2D contour plot map of DEM_data
	"""

	##############################################################
	## prefined features
	##############################################################

	if plot_naming == None:
		plot_naming = 'RIS'

	# black, green, blue, magenta, red, yellow, cyan
	# color_list = ['rgba(0, 0, 0, 1)', 'rgba(0, 255, 0, 1)', 'rgba(0, 0, 255, 1)', 'rgba(255, 0, 255, 1)', 'rgba(255, 0, 0, 1)', 'rgba(255, 255, 0, 1)', 'rgba(0, 255, 255, 1)']
	# color_list_ref = ['rgba(0, 0, 0, 0.75)', 'rgba(0, 255, 0, 0.75)', 'rgba(0, 0, 255, 0.75)', 'rgba(255, 0, 255, 0.75)', 'rgba(255, 0, 0, 1)', 'rgba(255, 255, 0, 0.75)', 'rgba(0, 255, 255, 0.75)']

	## preset of color scales for contours
	countour_scale_elevation = [[0.0, 'rgba(255,255,255,0.0)'], [0.1, 'rgba(255,255,255,0.0)'], [0.2, 'rgba(255,255,255,0.0)'], [0.3, 'rgba(255,255,255,0.0)'], [0.4, 'rgba(255,255,255,0.0)'], [0.5, 'rgba(255,255,255,0.0)'], [0.6, 'rgba(255,255,255,0.0)'], [0.7, 'rgba(255,255,255,0.0)'], [0.8, 'rgba(255,255,255,0.0)'], [0.9, 'rgba(255,255,255,0.0)'], [1.0, 'rgba(255,255,255,0.0)']]

	colorscale_data= [[0.0, 'rgba(0,0,0,1)'], [0.1, 'rgba(155,0,155,1)'], [0.2, 'rgba(255,0,255,1)'], [0.3, 'rgba(146,0,255,1)'], [0.4, 'rgba(0,0,255,1)'], [0.5, 'rgba(0,104,255,1)'], [0.6, 'rgba(0,255,220,1)'], [0.7, 'rgba(0,255,0,1)'], [0.8, 'rgba(255,255,0,1)'], [0.9, 'rgba(255,130,0,1)'], [1.0, 'rgba(255,0,0,1)']]

	# colorscale_FS_data= [(0.00, 'rgba(255,0,0,1)'), (0.40, 'rgba(255,0,0,1)'),  	# red (FS<1)
	# 					 (0.40, 'rgba(255,165,0,1)'), (0.52, 'rgba(255,165,0,1)'),  # orange(1<=FS<1.3)
	# 					 (0.52, 'rgba(0,0,255,1)'), (0.60, 'rgba(0,0,255,1)'), 		# blue(1.3<=FS<1.5)
	# 					 (0.60, 'rgba(0,255,0,1)'), (0.80, 'rgba(0,255,0,1)'),		# green(1.5<=FS<2.0)
	# 					 (0.80, 'rgba(128,128,128,1)'), (1.00, 'rgba(128,128,128,1)')]  # grey(3>=FS>=2.0)

	# colorscale_heat_data == colorscale_data, but at 0, colorscale_data->black and colorscale_heat_data->transparent empty
	# colorscale_heat_data= [[0.0, 'rgba(255,255,255,0)'], [0.1, 'rgba(155,0,155,1)'], [0.2, 'rgba(255,0,255,1)'], [0.3, 'rgba(146,0,255,1)'], [0.4, 'rgba(0,0,255,1)'], [0.5, 'rgba(0,104,255,1)'], [0.6, 'rgba(0,255,220,1)'], [0.7, 'rgba(0,255,0,1)'], [0.8, 'rgba(255,255,0,1)'], [0.9, 'rgba(255,130,0,1)'], [1.0, 'rgba(255,0,0,1)']]

	# countour_scale = [[0.0, 'rgba(255,255,255,1)'], [0.1, 'rgba(255,255,255,1)'], [0.2, 'rgba(255,255,255,1)'], [0.3, 'rgba(255,255,255,1)'], [0.4, 'rgba(255,255,255,1)'], [0.5, 'rgba(255,255,255,1)'], [0.6, 'rgba(255,255,255,1)'], [0.7, 'rgba(255,255,255,1)'], [0.8, 'rgba(255,255,255,1)'], [0.9, 'rgba(255,255,255,1)'], [1.0, 'rgba(255,255,255,1)']]

  
	##############################################################
	## elevation contour map - 2D
	##############################################################
	if DEM is None:
		data_DEM_comp = []

	else:

		topoContour = go.Contour(
			x=gridUniqueX,
			y=gridUniqueY,
			z=DEM,
			line=dict(smoothing=0.85),
			autocontour=False, 
			colorscale=countour_scale_elevation,
			showscale=False,
			contours=dict(
				showlabels = True,
				labelfont = dict(
					family = 'Raleway',
					size = 12,
					color = 'black'
				)
				#cmax=np.ceil(max(flowpath.transpose()[loop])),
				#cmin=np.floor(min(flowpath.transpose()[loop]))
			)
		)
		data_DEM_comp = [topoContour]

	# plot_zmax = float(np.ceil(np.max(DEM) + max(max_limits[1], max_limits[6])))

	##############################################################
	## flowpath cluster map
	##############################################################

	###############################
	## dataframe of all cluster data
	###############################
	if isinstance(contour_limit, list) and all([isinstance(item, (int, float)) for item in contour_limit]):
		map_plot_DEM_comp = go.Contour(
			x=gridUniqueX,
			y=gridUniqueY,
			z=DEM_data,
			name=plot_naming, 
			hovertemplate='X: %{x}<br>'+
							'Y: %{y}<br>'+
							z_label+': %{z}',
			colorscale=colorscale_data,
			contours_start=contour_limit[0],
			contours_end=contour_limit[1],
			contours_size=contour_limit[2],
			line=dict(smoothing=0.85),
			contours_showlabels=True,
			contours_labelfont_size=10,
			contours_labelfont_color='rgba(255, 255, 255, 1)'  # white
		)	

	elif contour_limit is None:
		map_plot_DEM_comp = go.Contour(
			x=gridUniqueX,
			y=gridUniqueY,
			z=DEM_data,
			name=plot_naming, 
			hovertemplate='X: %{x}<br>'+
							'Y: %{y}<br>'+
							z_label+': %{z}',
			colorscale=colorscale_data,
			line=dict(smoothing=0.85),
			contours_showlabels=True,
			contours_labelfont_size=10,
			contours_labelfont_color='rgba(255, 255, 255, 1)'  # white
		)

	data_DEM_comp.append(map_plot_DEM_comp)

	##############################################################
	## plotly layout
	##############################################################
	layout_map_DEM_comp = go.Layout(
		title=plot_naming,
		paper_bgcolor='rgba(255,255,255,1)',
		plot_bgcolor='rgba(255,255,255,1)',
		autosize=True,
		width=layout_width, #Nx, #800,
		height=layout_height, #Ny, #1000,
		xaxis=dict(
			# scaleanchor="y",
			# scaleratio=1,
			showline=True,
			linewidth=1, 
			linecolor='black',
			mirror=True,
			autorange=False,
			title='x [m]',
			constrain="domain",
			range=[min(gridUniqueX), max(gridUniqueX)]
		),
		yaxis=dict(
			scaleanchor="x",
			scaleratio=1,
			showline=True,
			linewidth=1, 
			linecolor='black',
			mirror=True,
			autorange=False,
			title='y [m]',
			# constrain="domain",
			range=[min(gridUniqueY), max(gridUniqueY)] 
		),
		showlegend=True,
		legend=dict(orientation="h"),
		margin=dict(
			l=65,
			r=50,
			b=65,
			t=90
		)
	)

	###############################
	## plot 
	###############################
	# figure
	fig_map_DEM_comp = go.Figure(data=data_DEM_comp, layout=layout_map_DEM_comp)

	# plot
	# try:
	# 	fig_map_DEM_comp.write_image(folder_path+plot_naming+'.png')
	# except:
	# 	pass

	# try:
	# 	fig_map_DEM_comp.write_image(folder_path+plot_naming+'.svg')
	# except:
	# 	pass

	# fig_map_DEM_comp.write_image(folder_path+plot_naming+'.png')
	# fig_map_DEM_comp.write_image(folder_path+plot_naming+'.svg')

	plot(fig_map_DEM_comp, filename=folder_path+plot_naming+'.html', auto_open=open_html)

	return None


###########################################################################
## generate output GIS file 
###########################################################################
def generate_output_GIS(output_txt_format, output_dir, filename, suffix, mesh_GIS_data, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, third_dp, time=None, iteration=None):
	"""generate output files of GIS data

	Parameters
	----------
	output_txt_format : str
		generated file format. the options {"csv", "grd", "asc"} correspond to {comma-separated-value text, Surfer text grd file, ESRI ascii file}
	output_dir : str
		directory of the outputs
	filename : str
		project name
	suffix : str
		type of GIS data
	mesh_GIS_data : 2D numpy array
		GIS information that will be saved into output
	DEM_noData : 2D numpy array
		labels cells with NoData in original DEM ascii file 
	nodata_value : float | int
		value used to denote "NoData" in ascii file format
	gridUniqueX : 1D numpy array
		x-grid coordinates
	gridUniqueY : 1D numpy array
		y-grid coordinates
	deltaX : float
		spacing of grids in x-directions
	deltaY : float
		spacing of grids in y-directions
	XYZ_row_or_col_increase_first : str
		the ascending order in CSV file format. options {"row", "col"} means first increase in "y", "x" directions, respectively.
	dx_dp : int
		decimal point for increments in x-directions
	dy_dp : int
		decimal point for increments in y-directions
	third_dp : int
		decimal point for increments in the third axis 
	time : None | int, optional
		temporal data, by default None. If None, generated GIS file is not temporal component. If integer, labels temporal-dependent data 
	iteration : None | int, optional
		monte-carlo iteration data, by default None.
	"""

	end_tag = f" - {suffix}"
	if isinstance(time, (int, float, str)):
		end_tag += f" - t{int(time)}"
	if isinstance(iteration, (int, float, str)):
		end_tag += f" - i{int(iteration)}"

	if output_txt_format == "csv":
		mesh_GIS_data_xyz = mesh2xyz(mesh_GIS_data, gridUniqueX, gridUniqueY, dtype_opt=float, row_or_col_increase_first=XYZ_row_or_col_increase_first)
		np.savetxt(output_dir+filename+f"{end_tag}.csv", mesh_GIS_data_xyz, delimiter=",", comments='', fmt=['%.'+str(dx_dp)+'f','%.'+str(dy_dp)+'f','%.'+str(third_dp)+'f'])
		del mesh_GIS_data_xyz

	elif output_txt_format == "grd":
		data_mesh2grd(mesh_GIS_data, gridUniqueX, gridUniqueY, offset=None, outFileName=output_dir+filename+end_tag, fmt='%.'+str(third_dp)+'f')

	elif output_txt_format == "asc":
		mesh_GIS_data_noDataChecked = np.where(DEM_noData==0, nodata_value, mesh_GIS_data)
		data_mesh2asc(mesh_GIS_data_noDataChecked, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_dir+filename+end_tag, user_nodata_value=nodata_value, fmt='%.'+str(third_dp)+'f')
		del mesh_GIS_data_noDataChecked

# Create a JSON Encoder class
class json_serialize(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.integer):
			return int(obj)
		if isinstance(obj, np.floating):
			return float(obj)
		if isinstance(obj, tuple):
			return list(obj)
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		return json.JSONEncoder.default(self, obj)

###########################################################################
## run rainfall infiltration and slope stability analysis from input JSON file 
###########################################################################
def perform_3DTSP_v1(monte_carlo_iter_filename_dict):
	"""Run the combined infiltration and slope stability analysis for each Monte Carlo iteration.

	Parameters
	----------
	monte_carlo_iter_filename_dict : dict
		Dictionary containing the filenames for each Monte Carlo iteration.
	"""

	#####################################
	## import input files from original input
	#####################################
	# filename, input_folder_path, output_folder_path, restarting_simulation_dict, monte_carlo_iteration_max, output_txt_format, plot_option, gamma_w, FS_crit, dz, termination_apply, after_termination_new_times_apply, DEM_surf_dip_infiltraion_apply, DEM_debris_flow_criteria_apply, FS_3D_analysis, FS_3D_iter_limit, FS_3D_tol, cell_size_3DFS_min, cell_size_3DFS_max, superellipse_n_parameter, superellipse_eccen_ratio, FS_3D_apply_side, FS_3D_apply_root, DEM_UCA_compute_all, cpu_num, dt, rain_time_I, debris_t_max, debris_dt, DEM_file_name, increase_DEM_resolution, material_file_name, soil_depth_model, soil_depth_data, ground_water_model, ground_water_data, dip_surf_filename, aspect_surf_filename, dip_base_filename, aspect_base_filename, local_cell_sizes_slope, DEM_debris_flow_initiation_filename, DEM_neighbor_directed_graph_filename, DEM_UCA_filename, material, material_GIS = read_RISD_json_yaml_input_v20250711(input_JSON_YAML_file_name)

	copy_input = deepcopy(monte_carlo_iter_filename_dict["original_input"])
	copy_input["restarting_simulation_JSON"] = None

	filename, input_folder_path, output_folder_path, _, monte_carlo_iteration_max, output_txt_format, plot_option, gamma_w, FS_crit, dz, _, _, DEM_surf_dip_infiltraion_apply, DEM_debris_flow_criteria_apply, FS_3D_analysis, FS_3D_iter_limit, FS_3D_tol, cell_size_3DFS_min, cell_size_3DFS_max, superellipse_n_parameter, superellipse_eccen_ratio, FS_3D_apply_side, FS_3D_apply_root, _, cpu_num, dt, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = read_RISD_json_yaml_input_v20250711(copy_input) 
	# = read_RISD_json_yaml_input_v20250711(monte_carlo_iter_filename_dict["original_input"])
	
	#####################################
	# store new dictionary
	#####################################
	monte_carlo_iter_result_filename_dict = deepcopy(monte_carlo_iter_filename_dict)

	# slope analysis results for each monte-carlo simulation if not existing
	output_folder_path_iter_temp = f"{output_folder_path}iteration_"
	for iter_num in range(1,monte_carlo_iteration_max+1):
     
		# create output folder for each Monte Carlo iteration slope stability analysis
		if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/slope/"):
			os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/slope/", exist_ok=True)			

		# create template for slope stability analysis results
		if "min_FS" not in monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)].keys():
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["min_FS"] = {}
		if "crit_FS_z" not in monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)].keys():
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["crit_FS_z"] = {}
		if "debris_flow_source" not in monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)].keys():
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["debris_flow_source"] = {}
		if "landslide_source" not in monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)].keys():
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["landslide_source"] = {}

	#####################################
	# check if all Monte Carlo iterations are completed
	#####################################
	check_all_monte_carlo_iterations_completed = 0
	for iter_num, filename_dict in monte_carlo_iter_filename_dict["iterations"].items(): 
		# check if simulation is completed
		if ("min_FS" in filename_dict.keys()) and ((len(filename_dict["intensity"]) == len(filename_dict["min_FS"]) == len(filename_dict["gwt_z"])) or ((len(filename_dict["intensity"]) <= len(filename_dict["min_FS"])) and (len(filename_dict["intensity"]) <= len(filename_dict["gwt_z"])) and (len(filename_dict["min_FS"]) == len(filename_dict["gwt_z"])))):
			check_all_monte_carlo_iterations_completed += 1 

	if check_all_monte_carlo_iterations_completed == monte_carlo_iteration_max:
		print(f"		All Monte Carlo iterations Completed.\n")
		return monte_carlo_iter_result_filename_dict
 
	#####################################
	## import input files from Monte Carlo iteration dictionary
	#####################################
	## constant with time - DEM and grid data
	DEM_surface, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_surface"][1], monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_surface"][0], full_output=False)
	DEM_noData, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_noData"][1], monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_noData"][0], full_output=False)

	## grid information
	nodata_value = monte_carlo_iter_filename_dict["iterations"]["1"]["nodata_value"]
	XYZ_row_or_col_increase_first = monte_carlo_iter_filename_dict["iterations"]["1"]["XYZ_row_or_col_increase_first"]
	deltaX = monte_carlo_iter_filename_dict["iterations"]["1"]["deltaX"]
	deltaY = monte_carlo_iter_filename_dict["iterations"]["1"]["deltaY"]
	gridUniqueX = np.arange(monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueX_min"], monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueX_max"]+0.1*deltaX, deltaX)
	gridUniqueY = np.arange(monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueY_min"], monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueY_max"]+0.1*deltaY, deltaY)

	## decimal point information
	dx_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["dx_dp"]
	dy_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["dy_dp"]
	dz_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["dz_dp"]
	rate_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["rate_dp"]
	t_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["t_dp"]
	theta_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["theta_dp"]
	press_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["press_dp"]
	cumul_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["cumul_dp"]
	FS_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["FS_dp"]

	######################################################
	## generate all possible combinations of DEM cell groupings for 3D slope stability analysis
	######################################################	
	# this is same for all Monte Carlo iterations so run this outside the loop once
	if isinstance(FS_3D_analysis, bool) and FS_3D_analysis:

		print('The programming is generating the slip surface data for 3D slope stability analysis ... \n')
		
		###################
		## generate local slip surfaces (plan-view) using superellipse shape
		###################
		group_side_slip_surf_grouping = generate_local_superellipse_grouping_v1_10(cell_size_3DFS_min, cell_size_3DFS_max, superellipse_n_parameter, superellipse_eccen_ratio)
		# group_side_N_min, group_side_N_max, n_param, x_a_y_b_ratio

		###################
		## simply generate DEM cell groupings in global coordinates 
		###################
		# assign unique number to each DEM cell 
		# use to identify unique cell groupings
		DEM_grid_num = np.arange(int(len(gridUniqueY)*len(gridUniqueX))).reshape((len(gridUniqueY), len(gridUniqueX))).astype(int)

		# multiprocess input file			
		generate_global_superellipse_slip_surface_input = []
		for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))): 
			generate_global_superellipse_slip_surface_input.append((i, j, cell_size_3DFS_min, cell_size_3DFS_max, group_side_slip_surf_grouping, len(gridUniqueY), len(gridUniqueX), DEM_grid_num))
			# g_row_y, g_col_x, group_side_N_min, group_side_N_max, group_side_slip_surf_grouping, len_DEM_y_grid, len_DEM_x_grid, DEM_grid_num

		# generate all possible combinations of DEM cell groupings
		pool_generate_3DTS_slip_stage1 = mp.Pool(cpu_num)

		slip_surface_data_stage1 = pool_generate_3DTS_slip_stage1.map(generate_global_superellipse_grouping_MP_v1_00, generate_global_superellipse_slip_surface_input)   
		# all_slip_surf_data_temp - current

		pool_generate_3DTS_slip_stage1.close()
		pool_generate_3DTS_slip_stage1.join()

		# only take in unique DEM cell groupings
		unique_slip_surf_grouping_DEM_grid_num = list(set(list(itertools.chain.from_iterable(slip_surface_data_stage1))))
		# unique_slip_surf_grouping_DEM_grid_num_list = [list(item) if isinstance(item, tuple) else int(item) for item in unique_slip_surf_grouping_DEM_grid_num]  


	######################################
	# run the Monte Carlo iterations
	######################################
	for iter_num, filename_dict in monte_carlo_iter_filename_dict["iterations"].items(): 
     
		#####################################
		## import input files from Monte Carlo iteration dictionary - subjected to change over time
		#####################################
		bedrock_surface, _, _ = read_GIS_data(filename_dict["bedrock_surface"][1], filename_dict["bedrock_surface"][0], full_output=False)
		soil_thickness, _, _ = read_GIS_data(filename_dict["soil_thickness"][1], filename_dict["soil_thickness"][0], full_output=False)
		
		dip_surf_deg, _, _ = read_GIS_data(filename_dict["dip_surf_deg"][1], filename_dict["dip_surf_deg"][0], full_output=False)
		# aspect_surf_deg, _, _ = read_GIS_data(filename_dict["aspect_surf_deg"][1], filename_dict["aspect_surf_deg"][0], full_output=False)	
		dip_base_deg, _, _ = read_GIS_data(filename_dict["dip_base_deg"][1], filename_dict["dip_base_deg"][0], full_output=False)
		aspect_base_deg, _, _ = read_GIS_data(filename_dict["aspect_base_deg"][1], filename_dict["aspect_base_deg"][0], full_output=False)

		DEM_debris_flow_criteria, _, _ = read_GIS_data(filename_dict["DEM_debris_flow_criteria"][1], filename_dict["DEM_debris_flow_criteria"][0], full_output=False) 

		#####################################
		# check if simulation is completed
		#####################################
		if ("min_FS" in filename_dict.keys()) and ((len(filename_dict["intensity"]) == len(filename_dict["min_FS"]) == len(filename_dict["gwt_z"])) or ((len(filename_dict["intensity"]) <= len(filename_dict["min_FS"])) and (len(filename_dict["intensity"]) <= len(filename_dict["gwt_z"])) and (len(filename_dict["min_FS"]) == len(filename_dict["gwt_z"])))):
			print(f"Monte Carlo iteration {iter_num} completed.")
			continue 
	
		#####################################
		# run the simulation
		#####################################
		print(f"Running Monte Carlo iteration {iter_num} ...")

		#####################################
		# extract inputs specific to the iterations
		#####################################
		max_time_step = len(filename_dict["intensity"])
		if ("min_FS" in filename_dict.keys()) and (len(filename_dict["min_FS"]) >= 1):
			start_time_step = len(filename_dict["min_FS"])-1
		else:
			start_time_step = 0
		
		## material - hydraulic properties
		# SWCC_model, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["SWCC_model"][1], filename_dict["material"]["hydraulic"]["SWCC_model"][0], full_output=False)
		# SWCC_a, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["SWCC_a"][1], filename_dict["material"]["hydraulic"]["SWCC_a"][0], full_output=False)
		# SWCC_n, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["SWCC_n"][1], filename_dict["material"]["hydraulic"]["SWCC_n"][0], full_output=False)
		# SWCC_m, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["SWCC_m"][1], filename_dict["material"]["hydraulic"]["SWCC_m"][0], full_output=False)
		k_sat, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["k_sat"][1], filename_dict["material"]["hydraulic"]["k_sat"][0], full_output=False)
		initial_suction, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["initial_suction"][1], filename_dict["material"]["hydraulic"]["initial_suction"][0], full_output=False)
		# theta_sat, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["theta_sat"][1], filename_dict["material"]["hydraulic"]["theta_sat"][0], full_output=False)
		# theta_residual, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["theta_residual"][1], filename_dict["material"]["hydraulic"]["theta_residual"][0], full_output=False)
		# soil_m_v, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["soil_m_v"][1], filename_dict["material"]["hydraulic"]["soil_m_v"][0], full_output=False)
		S_max, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["max_surface_storage"][1], filename_dict["material"]["hydraulic"]["max_surface_storage"][0], full_output=False)
		# theta_initial, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["theta_initial"][1], filename_dict["material"]["hydraulic"]["theta_initial"][0], full_output=False)
		psi_r, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["psi_r"][1], filename_dict["material"]["hydraulic"]["psi_r"][0], full_output=False)
		delta_theta, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["delta_theta"][1], filename_dict["material"]["hydraulic"]["delta_theta"][0], full_output=False)
		# F_p, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["F_p"][1], filename_dict["material"]["hydraulic"]["F_p"][0], full_output=False)
		# z_p, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["z_p"][1], filename_dict["material"]["hydraulic"]["z_p"][0], full_output=False)
		T_p, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["T_p"][1], filename_dict["material"]["hydraulic"]["T_p"][0], full_output=False)
		T_pp, _, _ = read_GIS_data(filename_dict["material"]["hydraulic"]["T_pp"][1], filename_dict["material"]["hydraulic"]["T_pp"][0], full_output=False)

		## material - soil strength properties
		soil_unit_weight, _, _ = read_GIS_data(filename_dict["material"]["soil"]["unit_weight"][1], filename_dict["material"]["soil"]["unit_weight"][0], full_output=False)
		soil_phi, _, _ = read_GIS_data(filename_dict["material"]["soil"]["phi"][1], filename_dict["material"]["soil"]["phi"][0], full_output=False)
		soil_phi_b, _, _ = read_GIS_data(filename_dict["material"]["soil"]["phi_b"][1], filename_dict["material"]["soil"]["phi_b"][0], full_output=False)
		soil_c, _, _ = read_GIS_data(filename_dict["material"]["soil"]["c"][1], filename_dict["material"]["soil"]["c"][0], full_output=False)

		## material - root reinforcement properties 
		root_unit_weight, _, _ = read_GIS_data(filename_dict["material"]["root"]["unit_weight"][1], filename_dict["material"]["root"]["unit_weight"][0], full_output=False)
		root_model, _, _ = read_GIS_data(filename_dict["material"]["root"]["model"][1], filename_dict["material"]["root"]["model"][0], full_output=False)
		root_c_base, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_constant"][0][1], filename_dict["material"]["root"]["parameters_constant"][0][0], full_output=False)
		root_c_side, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_constant"][1][1], filename_dict["material"]["root"]["parameters_constant"][1][0], full_output=False)
		root_depth, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_constant"][2][1], filename_dict["material"]["root"]["parameters_constant"][2][0], full_output=False)
		root_alpha2, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_van_Zadelhoff"][0][1], filename_dict["material"]["root"]["parameters_van_Zadelhoff"][0][0], full_output=False)
		root_beta2, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_van_Zadelhoff"][1][1], filename_dict["material"]["root"]["parameters_van_Zadelhoff"][1][0], full_output=False)
		root_RR_max, _, _ = read_GIS_data(filename_dict["material"]["root"]["parameters_van_Zadelhoff"][2][1], filename_dict["material"]["root"]["parameters_van_Zadelhoff"][2][0], full_output=False)

		##################
		# taking the superellipse shapes, generate slip surface soil cell data
		##################
		if isinstance(FS_3D_analysis, bool):

			#####################################
			# read GIS data of hydraulic properties for initial set-up
			#####################################
			# gwt_dz_t, _, _ = read_GIS_data(filename_dict["gwt_dz"][str(start_time_step)][1], filename_dict["gwt_dz"][str(start_time_step)][0], full_output=False)
			gwt_z_t, _, _ = read_GIS_data(filename_dict["gwt_z"][str(start_time_step)][1], filename_dict["gwt_z"][str(start_time_step)][0], full_output=False)
			Surface_Storage_t, _, _ = read_GIS_data(filename_dict["Surface_Storage"][str(start_time_step)][1], filename_dict["Surface_Storage"][str(start_time_step)][0], full_output=False)
			Precipitation_t, _, _ = read_GIS_data(filename_dict["Precipitation"][str(start_time_step)][1], filename_dict["Precipitation"][str(start_time_step)][0], full_output=False)
			Runoff_t, _, _ = read_GIS_data(filename_dict["Runoff"][str(start_time_step)][1], filename_dict["Runoff"][str(start_time_step)][0], full_output=False)
			f_rate_t, _, _ = read_GIS_data(filename_dict["f_rate"][str(start_time_step)][1], filename_dict["f_rate"][str(start_time_step)][0], full_output=False)
			F_cumul_t, _, _ = read_GIS_data(filename_dict["F_cumul"][str(start_time_step)][1], filename_dict["F_cumul"][str(start_time_step)][0], full_output=False)
			z_w_t, _, _ = read_GIS_data(filename_dict["z_w"][str(start_time_step)][1], filename_dict["z_w"][str(start_time_step)][0], full_output=False)
			wet_z_t, _, _ = read_GIS_data(filename_dict["wet_z"][str(start_time_step)][1], filename_dict["wet_z"][str(start_time_step)][0], full_output=False)

		#####################################
		# generate all slip surface soil column data
		#####################################
		if isinstance(FS_3D_analysis, bool) and FS_3D_analysis:

			# all_slip_surf_data - all unique slip surface soil cell data
			# index = slip surface ID, data = [0truncated_inside_row_y_col_x_global_idx, 1local_ext_id, 2local_z_t, 3local_z_b, 4local_gw_z, 5local_front_z, 6local_psi_r, 7local_psi_i, 8local_base_dip_rad, 9local_base_aspect_rad, 10local_gamma_s, 11local_phi_eff_rad, 12local_phi_b_rad, 13local_c, 14local_root_gamma_s, 15local_root_c_base, 16local_root_c_side, 17local_root_depth, 18local_root_alpha2, 19local_root_beta2, 20local_root_RR_max ] 
			# cell_all_affecting_slip - find all slip surface containing given (global_row_y, global_col_x)

			# multiprocess input file
			generate_slip_surface_cell_input = [] 
			for unique_slip_surface_i in unique_slip_surf_grouping_DEM_grid_num: 
				generate_slip_surface_cell_input.append((unique_slip_surface_i, DEM_grid_num, DEM_surface, soil_thickness, dip_base_deg, aspect_base_deg, gwt_z_t, wet_z_t, psi_r, initial_suction, soil_unit_weight, soil_phi, soil_phi_b, soil_c, root_unit_weight, root_c_base, root_c_side, root_depth, root_alpha2, root_beta2, root_RR_max))
				# unique_slip_surface_i, DEM_grid_num, DEM_surface, DEM_soil_thickness, dip_base, aspect_base, DEM_gwt_z, DEM_wetting_front_z, DEM_psi_r, DEM_initial_suction, DEM_soil_unit_weight, DEM_soil_phi, DEM_soil_phi_b, DEM_soil_c, DEM_root_unit_weight, DEM_root_c_base, DEM_root_c_side, DEM_root_depth, DEM_root_alpha2, DEM_root_beta2, DEM_root_RR_max

			# generate all possible combinations of DEM cell groupings
			pool_generate_3DTS_slip_stage2 = mp.Pool(cpu_num)

			all_slip_surf_data = pool_generate_3DTS_slip_stage2.map(generate_3DTS_slip_groupings_mp_v3_00, generate_slip_surface_cell_input)   
			# all_slip_surf_data 

			pool_generate_3DTS_slip_stage2.close()
			pool_generate_3DTS_slip_stage2.join()

			#####################################
			# generate all slip surface soil column data for 3D slope stability analysis
			#####################################
			compute_t_3DFS_input = []
			for slip_data_temp in all_slip_surf_data:

				try:
					slip_data = slip_data_temp[:]

					# critical_depth_3D_FS_MP_input
					# 0truncated_inside_row_y_col_x_global_idx, 1local_ext_id, 2local_z_t, 3local_z_b, 4local_gw_z, 5local_front_z, 6local_psi_r, 7local_psi_i, 8local_base_dip_rad, 9local_base_aspect_rad, 10local_gamma_s, 11local_phi_eff_rad, 12local_phi_b_rad, 13local_c, 14local_root_gamma_s, 15local_root_c_base, 16local_root_c_side, 17local_root_depth, 18local_root_alpha2, 19local_root_beta2, 20local_root_RR_max, 

					# 21iteration_max, 22min_FS_diff, 23deltaX, 24deltaY, 25dz, 26gamma_w, 27FS_crit, 28correctFS_bool, 29FS_3D_apply_side, 30FS_3D_apply_root
					slip_data.extend( [FS_3D_iter_limit, FS_3D_tol, deltaX, deltaY, dz, gamma_w, FS_crit, True, FS_3D_apply_side, FS_3D_apply_root] )
					
					# DEM root model - use the most frequent root strength model
					DEM_root_model_mode = int(mode([ root_model[i, j] for (i, j) in slip_data[0][:] ])[0])

					# 31DEM_root_model, 32dz_dp, 33press_dp
					slip_data.extend( [DEM_root_model_mode, dz_dp, press_dp] )
					
					# store multiprocessing inputs
					compute_t_3DFS_input.append(tuple(slip_data))
					del slip_data

				except:  # skip if something is not correctly generated
					pass 

		#############################
		## Physically-based slope stability at time step = starting time step
		#############################
		if FS_3D_analysis is not None: 

			### cell 3D slope stability
			if FS_3D_analysis:

				###################
				## update water-related information and perform slope stability analysis for each generated slip surface
				###################
				# multiprocessing analysis
				pool_1DGA_3DFS_t = mp.Pool(cpu_num)

				t_output_failSoil_critFS = pool_1DGA_3DFS_t.map(critical_depth_group_3D_FS_HungrJanbu_MP_v9_00, compute_t_3DFS_input)   # Hungr 1989 + side resistance + root resistance
				# index = slip surface ID number
				# failure_soil_thickness_per_DEM_cell, min_comp_FS for each generated slip surface

				pool_1DGA_3DFS_t.close()
				pool_1DGA_3DFS_t.join()

				###################
				## critical FS per each cell 
				###################
				min_comp_FS = np.ones(DEM_surface.shape)*9999 		  # for noData -> 9999
				failure_soil_thickness = np.zeros(DEM_surface.shape)
	
				for ((failure_soil_thickness_per_DEM_cell, min_comp_FS_comp), slip_data) in zip(t_output_failSoil_critFS, compute_t_3DFS_input):
					for idx,(t_y_row, t_x_col) in enumerate(slip_data[0]):
						# save the minimum computed factor of safety and track the corresponding failure soil thickness
						if min_comp_FS[t_y_row, t_x_col] > min_comp_FS_comp:
							min_comp_FS[t_y_row, t_x_col] = min_comp_FS_comp
							failure_soil_thickness[t_y_row, t_x_col] = failure_soil_thickness_per_DEM_cell[idx]

				# revert noData from 9999 to -1
				min_comp_FS = np.where(min_comp_FS == 9999, -1, min_comp_FS)

			### infinite slope stability analysis
			else:

				# multiprocessing input
				compute_t_inf_slope_input = []
				for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))): 
					
					# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
					if DEM_soil_thickness[i,j] <= dz or DEM_noData[i,j] == 0:
						continue

					# i, j, z_b, z_t, phi, phi_b, c, gamma_s, alpha, gw_z, front_z, psi_i, psi_r, FS_crit, gamma_w, dz, check_only, dz_dp, press_dp = critical_depth_inf_FS_MP_input
					compute_t_inf_slope_input.append( (i, j, bedrock_surface[i,j], DEM_surface[i,j], soil_phi[i,j], soil_phi_b[i,j], soil_c[i,j], soil_unit_weight[i,j], dip_base_deg[i,j], gwt_z_t[i,j], wet_z_t[i,j], initial_suction[i,j], psi_r[i,j], FS_crit, gamma_w, dz, False, dz_dp, press_dp) )

				pool_1DGA_infS_t = mp.Pool(cpu_num)

				t_output_FS_data = pool_1DGA_infS_t.map(critical_depth_inf_FS_MP, compute_t_inf_slope_input)
				# i, j, failure_soil_thickness_t, min_comp_FS_t

				pool_1DGA_infS_t.close()
				pool_1DGA_infS_t.join()

				## join and store the FS output
				min_comp_FS = np.ones(bedrock_surface.shape)*-1
				failure_soil_thickness = np.zeros(bedrock_surface.shape)

				for (i,j,crit_zz,min_FSi) in t_output_FS_data:

					if min_FSi == 9999: # all error
						min_FSi = -1
					min_FSi = min(min_FSi, 10) # in case of very large FS value

					min_comp_FS[i,j] = min_FSi
					failure_soil_thickness[i,j] = crit_zz

			################################################################
			## debris-flow initiation
			################################################################
			# landslide source - slope cell with FS < critical FS
			landslide_source = np.where((min_comp_FS < FS_crit) & (soil_thickness > dz), 1, 0)

			# debris-flow initiation condition applied -> check if slope failure become debris-flow
			if DEM_debris_flow_criteria_apply:
				debris_flow_source = np.where((min_comp_FS < FS_crit) & (DEM_debris_flow_criteria == 1) & (soil_thickness > dz), 1, 0)
			# debris-flow initiation condition not applied -> then all slope can become debris-flow
			else:  
				debris_flow_source = np.copy(landslide_source)

			################################################################
			## store and export data 
			################################################################
			# add results to the filename dictionary
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["min_FS"][str(start_time_step)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - min_FS - t{start_time_step} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["crit_FS_z"][str(start_time_step)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - crit_FS_z - t{start_time_step} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["debris_flow_source"][str(start_time_step)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - debris_flow_source - t{start_time_step} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["landslide_source"][str(start_time_step)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - landslide_source - t{start_time_step} - i{iter_num}.{output_txt_format}"]

			# plot data
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - min_FS - t{start_time_step} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - min_FS - t{start_time_step} - i{iter_num}", 'FS', gridUniqueX, gridUniqueY, None, min_comp_FS, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - crit_FS_z - t{start_time_step} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - crit_FS_z - t{start_time_step} - i{iter_num}", 'fail_dz', gridUniqueX, gridUniqueY, None, failure_soil_thickness, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - debris_flow_source - t{start_time_step} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - debris_flow_source - t{start_time_step} - i{iter_num}", 'dfs', gridUniqueX, gridUniqueY, None, debris_flow_source, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - landslide_source - t{start_time_step} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - landslide_source - t{start_time_step} - i{iter_num}", 'dfs', gridUniqueX, gridUniqueY, None, landslide_source, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)

			# export data
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "min_FS", min_comp_FS, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, FS_dp, time=start_time_step, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "crit_FS_z", failure_soil_thickness, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=start_time_step, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "debris_flow_source", debris_flow_source, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=start_time_step, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "landslide_source", landslide_source, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=start_time_step, iteration=iter_num)

			#############################
			## progress track
			############################# 
			start_time = filename_dict["intensity"][str(start_time_step)][2] 
			if start_time >= 3600: 	# time is in hours
				print(f"iteration {iter_num}, completed time-step: {start_time_step}, current time: {start_time/3600:.2f}hr; completion: {100*(start_time_step)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")
			else:  # time is in seconds
				print(f"iteration {iter_num}, completed time-step: {start_time_step}, current time: {start_time:,}s; completion: {100*(start_time_step)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")
    
			# export final all input and results JSON file - save to keep track of the simulations
			with open(f"{output_folder_path}{filename} - all_input_results.json", 'w') as f:
				json.dump(monte_carlo_iter_result_filename_dict, f, indent=4, cls=json_serialize)

		#####################################
		## iterate through time steps
		#####################################
		for time_step in range(start_time_step, max_time_step):
			
			#####################################
			# GIS data at given time step
			#####################################
			rain_t, _, _ = read_GIS_data(filename_dict["intensity"][str(time_step)][1], filename_dict["intensity"][str(time_step)][0], full_output=False)
			cur_time = filename_dict["intensity"][str(time_step)][3] # end of the time in the current time step
   
			if time_step == start_time_step:
				# gwt_dz_t, _, _ = read_GIS_data(filename_dict["gwt_dz"][str(time_step)][1], filename_dict["gwt_dz"][str(time_step)][0], full_output=False)
				gwt_z_t, _, _ = read_GIS_data(filename_dict["gwt_z"][str(time_step)][1], filename_dict["gwt_z"][str(time_step)][0], full_output=False)
				Surface_Storage_t, _, _ = read_GIS_data(filename_dict["Surface_Storage"][str(time_step)][1], filename_dict["Surface_Storage"][str(time_step)][0], full_output=False)
				Precipitation_t, _, _ = read_GIS_data(filename_dict["Precipitation"][str(time_step)][1], filename_dict["Precipitation"][str(time_step)][0], full_output=False)
				Runoff_t, _, _ = read_GIS_data(filename_dict["Runoff"][str(time_step)][1], filename_dict["Runoff"][str(time_step)][0], full_output=False)
				f_rate_t, _, _ = read_GIS_data(filename_dict["f_rate"][str(time_step)][1], filename_dict["f_rate"][str(time_step)][0], full_output=False)
				F_cumul_t, _, _ = read_GIS_data(filename_dict["F_cumul"][str(time_step)][1], filename_dict["F_cumul"][str(time_step)][0], full_output=False)
				z_w_t, _, _ = read_GIS_data(filename_dict["z_w"][str(time_step)][1], filename_dict["z_w"][str(time_step)][0], full_output=False)
				wet_z_t, _, _ = read_GIS_data(filename_dict["wet_z"][str(time_step)][1], filename_dict["wet_z"][str(time_step)][0], full_output=False)
			else:
				# gwt_dz_t = np.copy(gwt_dz_new_f)
				gwt_z_t = np.copy(gwt_z_new_f)
				Surface_Storage_t = np.copy(S_f)
				Precipitation_t = np.copy(P_f)
				Runoff_t = np.copy(RO_f)
				f_rate_t = np.copy(infil_rate_f_f)
				F_cumul_t = np.copy(infil_cumul_F_f)
				z_w_t = np.copy(infil_zw_f)
				wet_z_t = np.copy(wetting_front_z_f)

			#####################################################
			## 1D transient Green-Ampt analysis
			######################################################

			# multiprocessing data setup
			compute_GA_slanted_nonUniRain_input = []
			for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):

				# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
				if soil_thickness[i,j] <= dz or DEM_noData[i,j] == 0:
					continue

				if DEM_surf_dip_infiltraion_apply:
					surf_dip_i = dip_surf_deg[i,j]
				else:
					surf_dip_i = 0 

				# general surface (90 > beta >= 0)
				# i, j, z_top, z_bottom, z_length, infil_zw_pre, wetting_front_z_pre, gwt_z_pre, rain_I, k_sat_z, cur_t, dt, T_p, T_pp, delta_theta, psi_r, infil_cumul_F_pre, slope_beta_deg, dz, P_pre, S_pre, RO_pre, infil_rate_f_pre, S_max, cumul_dp, t_dp, rate_dp, dz_dp = compute_GA_slanted_nonUniRain_input
				compute_GA_slanted_nonUniRain_input.append( (i, j, DEM_surface[i,j], bedrock_surface[i,j], soil_thickness[i,j], z_w_t[i,j], wet_z_t[i,j], gwt_z_t[i,j], rain_t[i,j], k_sat[i,j], cur_time, dt, T_p[i,j], T_pp[i,j], delta_theta[i,j], psi_r[i,j], F_cumul_t[i,j], surf_dip_i, Precipitation_t[i,j], Surface_Storage_t[i,j], Runoff_t[i,j], f_rate_t[i,j], S_max[i,j], cumul_dp, t_dp, rate_dp, dz_dp) )

			# run infilatration analysis
			pool_1DGA_t = mp.Pool(cpu_num)

			comp_1DGS_output = pool_1DGA_t.map(compute_GA_nonUniRain_slanted_MP, compute_GA_slanted_nonUniRain_input)
			# i, j, P_new, S_new, RO_new, infil_cumul_F_new, infil_rate_f_new, gwt_z_new, infil_zw_new, wetting_front_z_new

			pool_1DGA_t.close()
			pool_1DGA_t.join()

			# join and store computed data
			P_f = np.zeros(DEM_surface.shape)
			S_f = np.zeros(DEM_surface.shape)
			RO_f = np.zeros(DEM_surface.shape)
			infil_rate_f_f = np.zeros(DEM_surface.shape)
			infil_cumul_F_f = np.zeros(DEM_surface.shape)
			infil_zw_f = np.zeros(DEM_surface.shape)
			wetting_front_z_f = np.zeros(DEM_surface.shape)
			gwt_z_new_f = np.zeros(DEM_surface.shape)
			gwt_dz_new_f = np.zeros(DEM_surface.shape)
			for (i, j, P_new, S_new, RO_new, infil_cumul_F_new, infil_rate_f_new, gwt_z_new, infil_zw_new, wetting_front_z_new) in comp_1DGS_output:
				P_f[i,j] = P_new
				S_f[i,j] = S_new
				RO_f[i,j] = RO_new
				infil_rate_f_f[i,j] = infil_rate_f_new
				infil_cumul_F_f[i,j] = infil_cumul_F_new
				infil_zw_f[i,j] = infil_zw_new
				wetting_front_z_f[i,j] = wetting_front_z_new
				gwt_z_new_f[i,j] = gwt_z_new
				gwt_dz_new_f[i,j] = DEM_surface[i,j] - gwt_z_new  

			# add results to the filename dictionary
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["gwt_dz"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - gwt_dz - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["gwt_z"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - gwt_z - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["Surface_Storage"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Surface_Storage - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["Precipitation"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Precipitation - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["Runoff"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Runoff - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["f_rate"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - f_rate - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["F_cumul"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - F_cumul - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["z_w"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - z_w - t{time_step+1} - i{iter_num}.{output_txt_format}"]
			monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["wet_z"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - wet_z - t{time_step+1} - i{iter_num}.{output_txt_format}"]

			# generate plots
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - gwt_dz - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - gwt_dz - t{time_step+1} - i{iter_num}", 'gwt_dz', gridUniqueX, gridUniqueY, None, gwt_dz_new_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - gwt_z - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - gwt_z - t{time_step+1} - i{iter_num}", 'gwt_z', gridUniqueX, gridUniqueY, None, gwt_z_new_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - Surface_Storage - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Surface_Storage - t{time_step+1} - i{iter_num}", 'S', gridUniqueX, gridUniqueY, None, S_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - Precipitation - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Precipitation - t{time_step+1} - i{iter_num}", 'P', gridUniqueX, gridUniqueY, None, P_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - Runoff - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - Runoff - t{time_step+1} - i{iter_num}", 'RO', gridUniqueX, gridUniqueY, None, RO_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - f_rate - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - f_rate - t{time_step+1} - i{iter_num}", 'f', gridUniqueX, gridUniqueY, None, infil_rate_f_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - F_cumul - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - F_cumul - t{time_step+1} - i{iter_num}", 'F', gridUniqueX, gridUniqueY, None, infil_cumul_F_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - z_w - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - z_w - t{time_step+1} - i{iter_num}", 'z_w', gridUniqueX, gridUniqueY, None, infil_zw_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/hydraulics/{filename} - wet_z - t{time_step+1} - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/hydraulics/", f"{filename} - wet_z - t{time_step+1} - i{iter_num}", 'wet_z', gridUniqueX, gridUniqueY, None, wetting_front_z_f, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

			# generate output file
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "gwt_dz", gwt_dz_new_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "gwt_z", gwt_z_new_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "Surface_Storage", S_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "Precipitation", P_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "Runoff", RO_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "f_rate", infil_rate_f_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, rate_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "F_cumul", infil_cumul_F_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "z_w", infil_zw_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=time_step+1, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/hydraulics/", filename, "wet_z", wetting_front_z_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=time_step+1, iteration=iter_num)

			#############################
			## Physically-based slope stability
			#############################
			if FS_3D_analysis is not None: 

				### cell 3D slope stability
				if FS_3D_analysis:

					###################
					## update water-related information and perform slope stability analysis for each generated slip surface
					###################
					# multiprocessing input
					compute_t_3DFS_input_temp = compute_t_3DFS_input[:]
					del compute_t_3DFS_input

					compute_t_3DFS_input = []
					for slip_data_temp in compute_t_3DFS_input_temp:
			
						slip_data = list(slip_data_temp)

						# critical_depth_3D_FS_MP_input
						# 0truncated_inside_row_y_col_x_global_idx, 1local_ext_id, 2local_z_t, 3local_z_b, 4local_gw_z, 5local_front_z, 6local_psi_r, 7local_psi_i, 8local_base_dip_rad, 9local_base_aspect_rad, 10local_gamma_s, 11local_phi_eff_rad, 12local_phi_b_rad, 13local_c, 14local_root_gamma_s, 15local_root_c_base, 16local_root_c_side, 17local_root_depth, 18local_root_alpha2, 19local_root_beta2, 20local_root_RR_max, 21iteration_max, 22min_FS_diff, 23deltaX, 24deltaY, 25dz, 26gamma_w, 27FS_crit, 28correctFS_bool, 29FS_3D_apply_side, 30FS_3D_apply_root, 31DEM_root_model, 32dz_dp, 33press_dp

						# only the groundwater condition has changed since pervious simulation
						# only change 4local_gw_z and 5local_front_z
						new_local_gw_z = []
						new_local_front_z = []
						for (t_y_row, t_x_col) in slip_data[0]:
							new_local_gw_z.append(gwt_z_new_f[t_y_row, t_x_col])
							new_local_front_z.append(wetting_front_z_f[t_y_row, t_x_col])

						slip_data[4] = new_local_gw_z[:]
						slip_data[5] = new_local_front_z[:]

						compute_t_3DFS_input.append(slip_data[:])
						del slip_data

					pool_1DGA_3DFS_t = mp.Pool(cpu_num)

					t_output_failSoil_critFS = pool_1DGA_3DFS_t.map(critical_depth_group_3D_FS_HungrJanbu_MP_v9_00, compute_t_3DFS_input)   # Hungr 1989 + side resistance + root resistance
					# index = slip surface ID number
					# failure_soil_thickness_per_DEM_cell, min_comp_FS for each generated slip surface

					pool_1DGA_3DFS_t.close()
					pool_1DGA_3DFS_t.join()

					###################
					## critical FS per each cell 
					###################

					min_comp_FS = np.ones(DEM_surface.shape)*9999 		  # for noData -> 9999
					failure_soil_thickness = np.zeros(DEM_surface.shape)
		
					for ((failure_soil_thickness_per_DEM_cell, min_comp_FS_comp), slip_data) in zip(t_output_failSoil_critFS, compute_t_3DFS_input):
						for idx,(t_y_row, t_x_col) in enumerate(slip_data[0]):
							# save the minimum computed factor of safety and track the corresponding failure soil thickness
							if min_comp_FS[t_y_row, t_x_col] > min_comp_FS_comp:
								min_comp_FS[t_y_row, t_x_col] = min_comp_FS_comp
								failure_soil_thickness[t_y_row, t_x_col] = failure_soil_thickness_per_DEM_cell[idx]

					# revert noData from 9999 to -1
					min_comp_FS = np.where(min_comp_FS == 9999, -1, min_comp_FS)

				### infinite slope stability analysis
				else:

					# multiprocessing input
					compute_t_inf_slope_input = []
					for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))): 
						
						# skip any DEM cell with soil depth less than the minimum depth increment - too small for analysis
						if DEM_soil_thickness[i,j] <= dz or DEM_noData[i,j] == 0:
							continue

						# i, j, z_b, z_t, phi, phi_b, c, gamma_s, alpha, gw_z, front_z, psi_i, psi_r, FS_crit, gamma_w, dz, check_only, dz_dp, press_dp = critical_depth_inf_FS_MP_input
						compute_t_inf_slope_input.append( (i, j, bedrock_surface[i,j], DEM_surface[i,j], soil_phi[i,j], soil_phi_b[i,j], soil_c[i,j], soil_unit_weight[i,j], dip_base_deg[i,j], gwt_z_new_f[i,j], wetting_front_z_f[i,j], initial_suction[i,j], psi_r[i,j], FS_crit, gamma_w, dz, False, dz_dp, press_dp) )

					pool_1DGA_infS_t = mp.Pool(cpu_num)

					t_output_FS_data = pool_1DGA_infS_t.map(critical_depth_inf_FS_MP, compute_t_inf_slope_input)
					# i, j, failure_soil_thickness_t, min_comp_FS_t

					pool_1DGA_infS_t.close()
					pool_1DGA_infS_t.join()

					## join and store the FS output
					min_comp_FS = np.ones(bedrock_surface.shape)*-1
					failure_soil_thickness = np.zeros(bedrock_surface.shape)

					for (i,j,crit_zz,min_FSi) in t_output_FS_data:

						if min_FSi == 9999: # all error
							min_FSi = -1
						min_FSi = min(min_FSi, 10) # in case of very large FS value

						min_comp_FS[i,j] = min_FSi
						failure_soil_thickness[i,j] = crit_zz

				################################################################
				## debris-flow initiation
				################################################################
				# landslide source - slope cell with FS < critical FS
				landslide_source = np.where((min_comp_FS < FS_crit) & (soil_thickness > dz), 1, 0)

				# debris-flow initiation condition applied -> check if slope failure become debris-flow
				if DEM_debris_flow_criteria_apply:
					debris_flow_source = np.where((min_comp_FS < FS_crit) & (DEM_debris_flow_criteria == 1) & (soil_thickness > dz), 1, 0)
				# debris-flow initiation condition not applied -> then all slope can become debris-flow
				else:  
					debris_flow_source = np.copy(landslide_source)

				################################################################
				## store and export data 
				################################################################
				# add results to the filename dictionary
				monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["min_FS"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - min_FS - t{time_step+1} - i{iter_num}.{output_txt_format}"]
				monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["crit_FS_z"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - crit_FS_z - t{time_step+1} - i{iter_num}.{output_txt_format}"]
				monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["debris_flow_source"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - debris_flow_source - t{time_step+1} - i{iter_num}.{output_txt_format}"]
				monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["landslide_source"][str(time_step+1)] = [f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - landslide_source - t{time_step+1} - i{iter_num}.{output_txt_format}"]

				# plot data
				if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - min_FS - t{time_step+1} - i{iter_num}.html") == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - min_FS - t{time_step+1} - i{iter_num}", 'FS', gridUniqueX, gridUniqueY, None, min_comp_FS, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - crit_FS_z - t{time_step+1} - i{iter_num}.html") == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - crit_FS_z - t{time_step+1} - i{iter_num}", 'fail_dz', gridUniqueX, gridUniqueY, None, failure_soil_thickness, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - debris_flow_source - t{time_step+1} - i{iter_num}.html") == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - debris_flow_source - t{time_step+1} - i{iter_num}", 'dfs', gridUniqueX, gridUniqueY, None, debris_flow_source, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path}iteration_{iter_num}/slope/{filename} - landslide_source - t{time_step+1} - i{iter_num}.html") == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/slope/", f"{filename} - landslide_source - t{time_step+1} - i{iter_num}", 'dfs', gridUniqueX, gridUniqueY, None, landslide_source, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)

				# export data
				generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "min_FS", min_comp_FS, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, FS_dp, time=time_step+1, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "crit_FS_z", failure_soil_thickness, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=time_step+1, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "debris_flow_source", debris_flow_source, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=time_step+1, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/slope/", filename, "landslide_source", landslide_source, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=time_step+1, iteration=iter_num)

				#############################
				## termination condition
				############################# 
				# terminate when failure has occurred
				# non_neg_FS = np.where(min_comp_FS < 0, 9999, min_comp_FS)
				# if after_termination_new_times_apply and np.amin(non_neg_FS) < FS_crit:
				# 	failure_occurred = True

				#############################
				## progress track
				############################# 
				# if cur_time >= 3600: 	# time is in hours
				# 	print(f"iteration {iter_num}, completed time-step: {time_step+1}, current time: {cur_time/3600:.2f}hr; completion: {100*(time_step+1)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")
				# else:  # time is in seconds
				# 	print(f"iteration {iter_num}, completed time-step: {time_step+1}, current time: {cur_time:,}s; completion: {100*(time_step+1)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")

				#############################
				## termination condition
				############################# 
				# terminate when failure has occurred
				# if (np.isnan(failure_soil_thickness).any() or np.sum(failure_soil_thickness) > 0) and termination_apply:
				# 	break

			#############################
			## progress track
			############################# 
			if cur_time >= 3600: 	# time is in hours
				print(f"iteration {iter_num}, completed time-step: {time_step+1}, current time: {cur_time/3600:.2f}hr; completion: {100*(time_step+1)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")
			else:  # time is in seconds
				print(f"iteration {iter_num}, completed time-step: {time_step+1}, current time: {cur_time:,}s; completion: {100*(time_step+1)/max_time_step:.2f}%") 	#; debris-flow simuilation time: {debris_cur_t}s")

			# export final all input and results JSON file - save to keep track of the simulations
			with open(f"{output_folder_path}{filename} - all_input_results.json", 'w') as f:
				json.dump(monte_carlo_iter_result_filename_dict, f, indent=4, cls=json_serialize)


		print(f'		 Computation of combined rainfall infiltration and slope stability for iteration {iter_num} is completed!\n')

	print(f'		 Computation of combined rainfall infiltration and slope stability is completed!\n')

	return monte_carlo_iter_result_filename_dict


###########################################################################
## run probabilistic results 
###########################################################################
def run_probabilistic_results(monte_carlo_iter_result_filename_dict):
	"""Run the probabilistic susceptibility analysis based on Monte Carlo iterations.

	Parameters
	----------
	monte_carlo_iter_result_filename_dict : dict
		Dictionary containing the filenames for each input and results of Monte Carlo iterations.
	"""

	## basic information
	filename = monte_carlo_iter_result_filename_dict["original_input"]["filename"]
	output_folder_path = monte_carlo_iter_result_filename_dict["original_input"]["output_folder_path"]
	if output_folder_path[-1] != "/":
		output_folder_path += '/'
	monte_carlo_iteration_max = monte_carlo_iter_result_filename_dict["original_input"]["monte_carlo_iteration_max"]
	output_txt_format = monte_carlo_iter_result_filename_dict["original_input"]["results_format"]
	plot_option = monte_carlo_iter_result_filename_dict["original_input"]["generate_plot"]

	'''NOTE: assuming that the DEM is not changing over all the simulations - use the DEM from the first iteration'''
	## grid information
	DEM_noData, _, _ = read_GIS_data(monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_noData"][1], monte_carlo_iter_filename_dict["iterations"]["1"]["DEM_noData"][0], full_output=False)
	nodata_value = monte_carlo_iter_filename_dict["iterations"]["1"]["nodata_value"]
	XYZ_row_or_col_increase_first = monte_carlo_iter_filename_dict["iterations"]["1"]["XYZ_row_or_col_increase_first"]
	deltaX = monte_carlo_iter_filename_dict["iterations"]["1"]["deltaX"]
	deltaY = monte_carlo_iter_filename_dict["iterations"]["1"]["deltaY"]
	gridUniqueX = np.arange(monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueX_min"], monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueX_max"]+0.1*deltaX, deltaX)
	gridUniqueY = np.arange(monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueY_min"], monte_carlo_iter_filename_dict["iterations"]["1"]["gridUniqueY_max"]+0.1*deltaY, deltaY)

	## decimal point information
	dx_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["dx_dp"]
	dy_dp = monte_carlo_iter_filename_dict["iterations"]["1"]["dy_dp"]

	# set up the filename dictionary for probabilistic results
	monte_carlo_iter_result_prob_filename_dict = deepcopy(monte_carlo_iter_result_filename_dict)
	monte_carlo_iter_result_prob_filename_dict["probabilistic_landslide"] = {}
	monte_carlo_iter_result_prob_filename_dict["probabilistic_debris_flow"] = {}

	## generate probabilistic results folder
	probabilistic_results_folder = f"{output_folder_path}probabilistic_results/"
	if not os.path.exists(probabilistic_results_folder):
		os.makedirs(probabilistic_results_folder, exist_ok=True)

	# time loop and iteration loop information
	time_max = max(len(monte_carlo_iter_result_filename_dict["iterations"]["1"]["intensity"]), len(monte_carlo_iter_result_filename_dict["iterations"]["1"]["min_FS"]))

	for time_step in range(time_max):
		prob_susceptibility_landslide = np.zeros((len(gridUniqueY), len(gridUniqueX)), dtype=float)  # susceptibility map for shallow landslides
		prob_susceptibility_debris_flow = np.zeros((len(gridUniqueY), len(gridUniqueX)), dtype=float)  # susceptibility map for debris flows initiation
		
		for iter_num in range(1, monte_carlo_iteration_max+1):
			landslide_suscept_i, _, _ = read_GIS_data(monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["landslide_source"][str(time_step)][1], monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["landslide_source"][str(time_step)][0], full_output=False) 
			debris_suscept_i, _, _ = read_GIS_data(monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["debris_flow_source"][str(time_step)][1], monte_carlo_iter_result_filename_dict["iterations"][str(iter_num)]["debris_flow_source"][str(time_step)][0], full_output=False) 
			
			prob_susceptibility_landslide = prob_susceptibility_landslide + landslide_suscept_i
			prob_susceptibility_debris_flow = prob_susceptibility_debris_flow + debris_suscept_i 
		
		prob_susceptibility_landslide = prob_susceptibility_landslide / monte_carlo_iteration_max
		prob_susceptibility_debris_flow = prob_susceptibility_debris_flow / monte_carlo_iteration_max

		# add results to the filename dictionary
		monte_carlo_iter_result_prob_filename_dict["probabilistic_landslide"][str(time_step)] = [probabilistic_results_folder, f"{filename} - prob_susceptibility_landslide - t{time_step}.{output_txt_format}"]
		monte_carlo_iter_result_prob_filename_dict["probabilistic_debris_flow"][str(time_step)] = [probabilistic_results_folder, f"{filename} - prob_susceptibility_debris_flow - t{time_step}.{output_txt_format}"]

		# plot data
		if os.path.exists(f"{probabilistic_results_folder}{filename} - prob_susceptibility_landslide - t{time_step}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(probabilistic_results_folder, f"{filename} - prob_susceptibility_landslide - t{time_step}", 'slope_prob', gridUniqueX, gridUniqueY, None, prob_susceptibility_landslide, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
		if os.path.exists(f"{probabilistic_results_folder}{filename} - prob_susceptibility_debris_flow - t{time_step}.html") == False and plot_option:
			plot_DEM_mat_map_v7_0(probabilistic_results_folder, f"{filename} - prob_susceptibility_debris_flow - t{time_step}", 'debris_prob', gridUniqueX, gridUniqueY, None, prob_susceptibility_debris_flow, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)

		# export data
		generate_output_GIS(output_txt_format, probabilistic_results_folder, filename, "prob_susceptibility_landslide", prob_susceptibility_landslide, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 5, time=time_step, iteration=None)
		generate_output_GIS(output_txt_format, probabilistic_results_folder, filename, "prob_susceptibility_debris_flow", prob_susceptibility_debris_flow, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 5, time=time_step, iteration=None)

	return monte_carlo_iter_result_prob_filename_dict


###########################################################################
## run 
###########################################################################
if __name__ == '__main__':

	# check the input JSON files exist in the specified directory
	if os.path.exists(input_JSON_YAML_file_name) == False:
		print("the input JSON file does not exist in the specified directory")
		sys.exit(1)

	######################################################################################################################################################
	## generate input data from JSON files
	######################################################################################################################################################	
	print('The programming is reading the input JSON file for analysis ... \n')

	filename, input_folder_path, output_folder_path, restarting_simulation_dict, monte_carlo_iteration_max, output_txt_format, plot_option, gamma_w, FS_crit, dz, termination_apply, after_termination_new_times_apply, DEM_surf_dip_infiltraion_apply, DEM_debris_flow_criteria_apply, FS_3D_analysis, FS_3D_iter_limit, FS_3D_tol, cell_size_3DFS_min, cell_size_3DFS_max, superellipse_n_parameter, superellipse_eccen_ratio, FS_3D_apply_side, FS_3D_apply_root, DEM_UCA_compute_all, cpu_num, dt, rain_time_I, debris_t_max, debris_dt, DEM_file_name, increase_DEM_resolution, material_file_name, soil_depth_model, soil_depth_data, ground_water_model, ground_water_data, dip_surf_filename, aspect_surf_filename, dip_base_filename, aspect_base_filename, local_cell_sizes_slope, DEM_debris_flow_initiation_filename, DEM_neighbor_directed_graph_filename, DEM_UCA_filename, material, material_GIS = read_RISD_json_yaml_input_v20250711(input_JSON_YAML_file_name)

	# out_filename = output_folder_path + filename   #default typical file path and file name template for saving results and plots
 
	print('		Importing the input JSON file completed!\n')

	#################################################################################################################################
	## rounding
	#################################################################################################################################

	# decimal places to round - avoid floating point errors
	dz_dp = max(-decimal.Decimal(str(dz)).as_tuple().exponent, 5)   # vertical size
	rate_dp = -decimal.Decimal(str(1e-12)).as_tuple().exponent  	# rate - f, I
	t_dp = max(-decimal.Decimal(str(dt)).as_tuple().exponent, 2)   # time
	theta_dp = 6    # theta_i, theta_s, theta_r, delta_theta
	press_dp = 4	# psi, u_w
	cumul_dp = 6    # F, S, RO, P 
	FS_dp = 3 

	######################################################################################################################################################
	## generate JSON files to run the simulations
	######################################################################################################################################################
	## generate from input data
	if restarting_simulation_dict is None:

		######################################################
		## generate folders in output directory based on type of generated data
		######################################################
		print('The programming is creating folders to save output files ... \n')

		# # to store GIS (DEM, dip, aspect, soil thickness, groundwater table, material zone) - now changable
		# if not os.path.exists(output_folder_path_GIS):
		# 	os.makedirs(output_folder_path_GIS, exist_ok=True)

		# to store GIS inputs for each Monte-Carlo simulation
		output_folder_path_iter_temp = f"{output_folder_path}iteration_"
		for iter_num in range(1,monte_carlo_iteration_max+1):
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}"):
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}", exist_ok=True)  
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"):   					
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/GIS/", exist_ok=True)    # GIS (DEM, dip, aspect, soil thickness, groundwater table, material zone) - now changable
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/material/"):
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/material/", exist_ok=True) 		# material parameters for each monte-carlo simulation 
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/intensity/"):
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/intensity/", exist_ok=True) 		# precipitation history (rainfall or snowmelt intensity) 
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/hydraulics/"):
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/hydraulics/", exist_ok=True)		# hydraulic infiltration analysis results for each monte-carlo simulation
			if not os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/slope/"):
				os.makedirs(f"{output_folder_path_iter_temp}{iter_num}/slope/", exist_ok=True)			# slope analysis results for each monte-carlo simulation

		print('		Creating folders completed!\n')

		##################################################################################################################
		## input json or yaml file
		##################################################################################################################
		print('The programming is creating template to store simulation inputs ... \n')

		# material parameters and analysis results - for each monte-carlo simulation
		monte_carlo_iter_filename_dict = {"iterations": {}}
		for iter_num in range(1,monte_carlo_iteration_max+1):
			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = {}

		# check whether it is yaml or json file format
		input_file_name_list = input_JSON_YAML_file_name.split('.')
		input_file_name_format = input_file_name_list[-1]

		if input_file_name_format.lower()  == "json":
			with open(input_JSON_YAML_file_name, 'r') as json_file:
				json_yaml_input_data = json.load(json_file)

		elif input_file_name_format.lower() in ["yaml", "yml"]:
			with open(input_JSON_YAML_file_name, 'r') as yaml_file:
				json_yaml_input_data = yaml.safe_load(yaml_file)
		
		monte_carlo_iter_filename_dict["original_input"] = deepcopy(json_yaml_input_data)

		print('		Creating template input dictionary completed!\n')

		######################################################
		## generate geometry that is fixed over time
		######################################################
		print('The programming is reading the importing DEM file for analysis ... \n')

		###########################
		## DEM surface - z_top - unchange
		###########################
		DEM_surface, nodata_value, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, dx_dp, dy_dp, XYZ_row_or_col_increase_first = read_GIS_data(DEM_file_name, input_folder_path, full_output=True)

		## future implementation to increase the resolution of DEM and other provided GIS files
		# if isinstance(increase_DEM_resolution, int) and (increase_DEM_resolution > 1):  # make DEM larger by grouping
		# 	DEM_surface, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY = increase_DEM_resolution_compute(increase_DEM_resolution, DEM_surface, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, cpu_num, full_output=True)

		DEM_surface_xyz = mesh2xyz(DEM_surface, gridUniqueX, gridUniqueY, dtype_opt=float, row_or_col_increase_first=XYZ_row_or_col_increase_first)			

		# assign the 
		for iter_num in range(1,monte_carlo_iteration_max+1):
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]

			if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM - i{iter_num}', 'Z', gridUniqueX, gridUniqueY, None, DEM_surface, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

			# generate output file
			generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM", DEM_surface, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "NoData", DEM_noData, np.ones((DEM_noData.shape)), nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=iter_num)

			# store file name
			temp_dict["DEM_surface"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM - i{iter_num}.{output_txt_format}"]
			temp_dict["DEM_noData"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - NoData - i{iter_num}.{output_txt_format}"]
			temp_dict["nodata_value"] = nodata_value
			temp_dict["gridUniqueX_min"] = float(np.min(gridUniqueX))
			temp_dict["gridUniqueX_max"] = float(np.max(gridUniqueX))
			temp_dict["gridUniqueY_min"] = float(np.min(gridUniqueY))
			temp_dict["gridUniqueY_max"] = float(np.max(gridUniqueY))
			temp_dict["deltaX"] = deltaX
			temp_dict["deltaY"] = deltaY
			temp_dict["n_row_y"] = len(gridUniqueY)
			temp_dict["n_col_x"] = len(gridUniqueX)
			temp_dict["dx_dp"] = dx_dp
			temp_dict["dy_dp"] = dy_dp
			temp_dict["dz_dp"] = dz_dp
			temp_dict["rate_dp"] = rate_dp
			temp_dict["t_dp"] = t_dp
			temp_dict["theta_dp"] = theta_dp
			temp_dict["press_dp"] = press_dp
			temp_dict["cumul_dp"] = cumul_dp
			temp_dict["FS_dp"] = FS_dp
			temp_dict["XYZ_row_or_col_increase_first"] = XYZ_row_or_col_increase_first

			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict

		print('		Importing the DEM file completed!\n')

		###########################
		## DEM base - z_bottom and soil depth - varying
		###########################
		print('The programming is reading the importing soil depth file for analysis ... \n')

		# soil depth are all subjected to probabilistic analysis
		for iter_num in range(1,monte_carlo_iteration_max+1):
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]

			DEM_soil_thickness, DEM_base = generate_soil_thickness_GIS_data(input_folder_path, soil_depth_model, soil_depth_data, dip_surf_filename, DEM_surface, DEM_noData, gridUniqueX, gridUniqueY, local_cell_sizes_slope, cpu_num)

			# plot
			if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - bedrock_surface - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - bedrock_surface - i{iter_num}', 'Z', gridUniqueX, gridUniqueY, None, DEM_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - soil_thickness - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - soil_thickness - i{iter_num}', 'dZ', gridUniqueX, gridUniqueY, None, DEM_soil_thickness, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

			# generate output file
			generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "bedrock_surface", DEM_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
			generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "soil_thickness", DEM_soil_thickness, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)

			# store file name
			temp_dict["bedrock_surface"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - bedrock_surface - i{iter_num}.{output_txt_format}"]
			temp_dict["soil_thickness"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - soil_thickness - i{iter_num}.{output_txt_format}"]

			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict

		print('		Generating the soil thickness and bedrock surface files completed!\n')

		###########################
		## soil surface slope - beta and base slope - alpha
		###########################
		print('The programming is reading the dip and aspect data for analysis ... \n')

		if soil_depth_model < 10:  # deterministic soil thickness (does not change over iteration)

			# multiprocessing input
			if (dip_surf_filename is None) or (aspect_surf_filename is None) or (dip_base_filename is None) or (aspect_base_filename is None):
				dip_surf, aspect_surf, dip_base, aspect_base = compute_dip_aspect(DEM_surface, DEM_base, DEM_soil_thickness, DEM_noData, gridUniqueX, gridUniqueY, local_cell_sizes_slope, dz, cpu_num)

			## instead of recomputing, recall computed data
			elif isinstance(dip_surf_filename, str) and isinstance(aspect_surf_filename, str) and isinstance(dip_base_filename, str) and isinstance(aspect_base_filename, str):
				dip_surf, _, _ = read_GIS_data(dip_surf_filename, input_folder_path, full_output=False)
				aspect_surf, _, _ = read_GIS_data(aspect_surf_filename, input_folder_path, full_output=False)
				dip_base, _, _ = read_GIS_data(dip_base_filename, input_folder_path, full_output=False)
				aspect_base, _, _ = read_GIS_data(aspect_base_filename, input_folder_path, full_output=False)

			else:
				print("specify either/both dip and aspect files correctly")
				sys.exit(6)

			# assign slope and aspect to each iterations
			for iter_num in range(1,monte_carlo_iteration_max+1):
				temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]

				# plot data
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - dip_surf_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - dip_surf_deg - i{iter_num}', 'dip_deg', gridUniqueX, gridUniqueY, None, dip_surf, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - aspect_surf_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - aspect_surf_deg - i{iter_num}', 'aspect_deg', gridUniqueX, gridUniqueY, None, aspect_surf, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - dip_base_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - dip_base_deg - i{iter_num}', 'dip_deg', gridUniqueX, gridUniqueY, None, dip_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - aspect_base_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - aspect_base_deg - i{iter_num}', 'aspect_deg', gridUniqueX, gridUniqueY, None, aspect_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

				# export data
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "dip_surf_deg", dip_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "aspect_surf_deg", aspect_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "dip_base_deg", dip_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "aspect_base_deg", aspect_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)

				# store file name
				temp_dict["dip_surf_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - dip_surf_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["aspect_surf_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - aspect_surf_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["dip_base_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - dip_base_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["aspect_base_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - aspect_base_deg - i{iter_num}.{output_txt_format}"]

				monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
				del temp_dict

		elif soil_depth_model >= 10:  # probabilistic soil thickness

			# assign slope and aspect to each iterations
			for iter_num in range(1,monte_carlo_iteration_max+1):
				temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]

				# read from generated files
				DEM_base, _, _ = read_GIS_data(temp_dict["bedrock_surface"][1], temp_dict["bedrock_surface"][0], full_output=False)
				DEM_soil_thickness, _, _ = read_GIS_data(temp_dict["soil_thickness"][1], temp_dict["soil_thickness"][0], full_output=False)

				# multiprocessing input
				if (dip_surf_filename is None) or (aspect_surf_filename is None) or (dip_base_filename is None) or (aspect_base_filename is None):
					dip_surf, aspect_surf, dip_base, aspect_base = compute_dip_aspect(DEM_surface, DEM_base, DEM_soil_thickness, DEM_noData, gridUniqueX, gridUniqueY, local_cell_sizes_slope, dz, cpu_num)
				## instead of recomputing, recall computed data - only for deterministic soil thickness 

				# plot data
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - dip_surf_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - dip_surf_deg - i{iter_num}', 'dip_deg', gridUniqueX, gridUniqueY, None, dip_surf, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - aspect_surf_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - aspect_surf_deg - i{iter_num}', 'aspect_deg', gridUniqueX, gridUniqueY, None, aspect_surf, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - dip_base_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - dip_base_deg - i{iter_num}', 'dip_deg', gridUniqueX, gridUniqueY, None, dip_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
				if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - aspect_base_deg - i{iter_num}.html') == False and plot_option:
					plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - aspect_base_deg - i{iter_num}', 'aspect_deg', gridUniqueX, gridUniqueY, None, aspect_base, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

				# export data
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "dip_surf_deg", dip_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "aspect_surf_deg", aspect_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "dip_base_deg", dip_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)
				generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "aspect_base_deg", aspect_base, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)

				# store file name
				temp_dict["dip_surf_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - dip_surf_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["aspect_surf_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - aspect_surf_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["dip_base_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - dip_base_deg - i{iter_num}.{output_txt_format}"]
				temp_dict["aspect_base_deg"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - aspect_base_deg - i{iter_num}.{output_txt_format}"]

				monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
				del temp_dict

		print('		Generating the dip and aspect files completed!\n')

		###########################
		## debris-flow initiation criteria (Kang et al., 2017) 
		###########################
		if FS_3D_analysis is not None: 

			print('The programming is reading the debris-flow initiation criteria data for analysis ... \n')

			# debris-flow initiation criteria is applied; hence, only cell passing the criteria can potentially be debris-flow source
			if DEM_debris_flow_criteria_apply:

				# compute upslope contributing area (UCA) - debris flow initiation criteria for regions with 
				if DEM_debris_flow_initiation_filename is None and DEM_UCA_filename is None:

					cell_area = deltaX*deltaY

					DEM_i, DEM_j = np.mgrid[0:len(gridUniqueY), 0:len(gridUniqueX)]
					i_flatten = np.ravel(DEM_i)   # flatten row based 
					j_flatten = np.ravel(DEM_j)   # flatten row based 

					DEM_grid_x, DEM_grid_y = np.meshgrid(gridUniqueX, gridUniqueY)
					x_flatten = np.ravel(DEM_grid_x)   # flatten row based 
					y_flatten = np.ravel(DEM_grid_y)   # flatten row based 

					#############
					## create network graph of DEM
					#############
					if DEM_neighbor_directed_graph_filename is None:

						# flatten elevation values
						DEM_surf_z_flatten = np.ravel(DEM_surface)
					
						DEM_neighbor_Zdiff_MP_input = []
						for loop2 in range(len(DEM_surf_z_flatten)):
							DEM_neighbor_Zdiff_MP_input.append( (loop2, i_flatten[loop2], j_flatten[loop2], gridUniqueX[j_flatten[loop2]], gridUniqueY[i_flatten[loop2]], DEM_surface, i_flatten, j_flatten, gridUniqueX, gridUniqueY, 3) )
							# point_idx, i, j, x, y, DEM, i_flatten, j_flatten, gridUniqueX, gridUniqueY, local_cell_sizes = DEM_neighbor_Zdiff_MP_input

						pool_DEM_surf_z_diff = mp.Pool(cpu_num)

						'''
						DEM_Z_diff_MP_strictly_hierarchy -> seems to good at upstream region, but caanot show flow happening between equal elevation - slight underestimate the upstream contributing area
						DEM_neighbor_Zdiff_data -> seems to add more regions than typical upstream region	
						'''	
						# DEM_neighbor_Zdiff_data = pool_DEM_surf_z_diff.map(DEM_Z_diff_MP_equal_flow, DEM_neighbor_Zdiff_MP_input)				
						DEM_neighbor_Zdiff_data = pool_DEM_surf_z_diff.map(DEM_Z_diff_MP_strictly_hierarchy, DEM_neighbor_Zdiff_MP_input)  
						# network_graph_ij (i,j) to place graph weight of 1

						pool_DEM_surf_z_diff.close()
						pool_DEM_surf_z_diff.join()

						# combine each index into single unique set of (i,j)
						DEM_neighbor_directed_graph_ij = list(set(list(itertools.chain.from_iterable(DEM_neighbor_Zdiff_data))))
						
						DEM_neighbor_directed_graph_ij_array = np.array(DEM_neighbor_directed_graph_ij)
						DEM_neighbor_directed_graph_i, DEM_neighbor_directed_graph_j = DEM_neighbor_directed_graph_ij_array[:,0], DEM_neighbor_directed_graph_ij_array[:,1]
						DEM_neighbor_directed_graph_val = np.ones(DEM_neighbor_directed_graph_i.shape)
						DEM_neighbor_directed_graph = csr_matrix( (DEM_neighbor_directed_graph_val, (DEM_neighbor_directed_graph_i, DEM_neighbor_directed_graph_j)), shape=(len(DEM_surf_z_flatten), len(DEM_surf_z_flatten)) )
						
						save_npz(input_folder_path+filename+"_neighboring_cell_directed_matrix.npz", DEM_neighbor_directed_graph)

					elif isinstance(DEM_neighbor_directed_graph_filename, str):
						DEM_neighbor_directed_graph = load_npz(input_folder_path+DEM_neighbor_directed_graph_filename)

					############
					## compute UCA for every cells or just for those that will potentially fail into debris-flow
					############
					# DEM_UCA_MP_input: i, j, point_idx, DEM_neighbor_directed_graph
					DEM_UCA_MP_input = []
					for (i,j) in itertools.product(range(len(gridUniqueY)), range(len(gridUniqueX))):
						if DEM_UCA_compute_all:
							point_idx = int(np.where((DEM_surface_xyz[:,0] == x_flatten[j]) & (DEM_surface_xyz[:,1] == y_flatten[i]))[0][0])
							DEM_UCA_MP_input.append((i, j, point_idx, DEM_neighbor_directed_graph))
						elif DEM_UCA_compute_all == False and dip_base[i,j] >= 14.32:
							point_idx = int(np.where((DEM_surface_xyz[:,0] == x_flatten[j]) & (DEM_surface_xyz[:,1] == y_flatten[i]))[0][0])
							DEM_UCA_MP_input.append((i, j, point_idx, DEM_neighbor_directed_graph))

					pool_DEM_UCA = mp.Pool(cpu_num)

					DEM_UCA_data_output = pool_DEM_UCA.map(count_UCA_cells_MP_v2, DEM_UCA_MP_input)
					# i, j, point_idx, connection_found_check_count

					pool_DEM_UCA.close()
					pool_DEM_UCA.join()

					DEM_UCA = np.zeros((DEM_surface.shape))
					for (i,j,p_idx,UCA_count) in DEM_UCA_data_output:
						DEM_UCA[i,j] = UCA_count*cell_area

					############
					## compute debris-flow initiation criteria for each cell
					############
					# Based on (Kang et al., 2017), where UCA >= 500 m^2 and base_dip >= max(34*np.exp(-0.003*UCA)+14.32, 14.32)
					# min dip required to transition into debris-flow
					DEM_UCA_filtered = np.where(DEM_UCA >= 3500, 3500, DEM_UCA)
					debris_flow_initiation_min_base_dip = np.where(DEM_UCA_filtered == 3500, 14.32, 34*np.exp(-0.003*DEM_UCA_filtered)+14.32)

					# compare the min dip needed for debris-flow when when UCA >= 500 m^2 
					DEM_debris_flow_criteria = np.where((DEM_UCA >= 500) & (dip_base >= debris_flow_initiation_min_base_dip), 1, 0)

					############
					## export data
					############
					for iter_num in range(1,monte_carlo_iteration_max+1):
						temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]   

						generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_UCA", DEM_UCA, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, int(dx_dp*dy_dp)+1, time=None, iteration=iter_num)
						generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_debris_flow_criteria", DEM_debris_flow_criteria, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=iter_num)

						############
						## plot
						############
						if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_UCA - i{iter_num}.html') == False and plot_option:
							plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_UCA - i{iter_num}', 'UCA', gridUniqueX, gridUniqueY, None, DEM_UCA, contour_limit=[0, 4000, 500], open_html=False, layout_width=1000, layout_height=1000)
						if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_debris_flow_criteria - i{iter_num}.html') == False and plot_option:
							plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_debris_flow_criteria - i{iter_num}', 'dfc', gridUniqueX, gridUniqueY, None, DEM_debris_flow_criteria, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

						# store file name
						temp_dict["DEM_UCA"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_UCA - i{iter_num}.{output_txt_format}"]
						temp_dict["DEM_debris_flow_criteria"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_debris_flow_criteria - i{iter_num}.{output_txt_format}"]

						monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
						del temp_dict

					del DEM_UCA

				# already computed all regions with debris-flow initiation check complete
				elif isinstance(DEM_debris_flow_initiation_filename, str):
					## read the GIS file
					DEM_debris_flow_criteria, _, _ = read_GIS_data(DEM_debris_flow_initiation_filename, input_folder_path, full_output=False)
     
					for iter_num in range(1,monte_carlo_iteration_max+1):
						temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]  

						## export data
						generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_debris_flow_criteria", DEM_debris_flow_criteria, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=iter_num)

						## plot
						if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_debris_flow_criteria - i{iter_num}.html') == False and plot_option:
							plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_debris_flow_criteria - i{iter_num}', 'dfc', gridUniqueX, gridUniqueY, None, DEM_debris_flow_criteria, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

						# store file name
						temp_dict["DEM_UCA"] = None
						temp_dict["DEM_debris_flow_criteria"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_debris_flow_criteria - i{iter_num}.{output_txt_format}"]

						monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
						del temp_dict

				# already computed UCA but no with debris-flow initiation check
				elif isinstance(DEM_UCA_filename, str) and DEM_debris_flow_initiation_filename is None:
					############
					## DEM_UCA
					############			
					DEM_UCA, _, _ = read_GIS_data(DEM_UCA_filename, input_folder_path, full_output=False)

					############
					## debris flow criteria
					############
					# Based on (Kang et al., 2017), where UCA >= 500 m^2 and min_base_dip >= 14.32 and base_dip >= 34*np.exp(-0.003*UCA)+14.32
					DEM_UCA_filtered = np.where(DEM_UCA >= 3500, 3500, DEM_UCA)
					debris_flow_initiation_min_base_dip = np.where(DEM_UCA_filtered == 3500, 14.32, 34*np.exp(-0.003*DEM_UCA_filtered)+14.32)
					DEM_debris_flow_criteria = np.where((DEM_UCA >= 500) & (dip_base >= debris_flow_initiation_min_base_dip), 1, 0)

					for iter_num in range(1,monte_carlo_iteration_max+1):
						temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]  

						############
						## export data
						############
						generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_UCA", DEM_UCA, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, int(dx_dp*dy_dp)+1, time=None, iteration=iter_num)
						generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_debris_flow_criteria", DEM_debris_flow_criteria, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=iter_num)

						############
						## plot
						############
						if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_UCA - i{iter_num}.html') == False and plot_option:
							plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_UCA - i{iter_num}', 'UCA', gridUniqueX, gridUniqueY, None, DEM_UCA, contour_limit=[0, 4000, 500], open_html=False, layout_width=1000, layout_height=1000)
						if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_debris_flow_criteria - i{iter_num}.html') == False and plot_option:
							plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_debris_flow_criteria - i{iter_num}', 'dfc', gridUniqueX, gridUniqueY, None, DEM_debris_flow_criteria, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

						############
						## store file name
						############
						temp_dict["DEM_UCA"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_UCA - i{iter_num}.{output_txt_format}"]
						temp_dict["DEM_debris_flow_criteria"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_debris_flow_criteria - i{iter_num}.{output_txt_format}"]

						monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
						del temp_dict

					del DEM_UCA

			# no debris-flow initiation criteria is applied; hence, any cell can potentially be debris-flow source
			else:
				DEM_debris_flow_criteria = np.ones((DEM_surface.shape))  # all regions are subjected to debris flow failures
       
				for iter_num in range(1,monte_carlo_iteration_max+1):
					temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]       

					## export data		
					generate_output_GIS(output_txt_format, f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename, "DEM_debris_flow_criteria", DEM_debris_flow_criteria, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, 0, time=None, iteration=iter_num)

					if os.path.exists(f"{output_folder_path_iter_temp}{iter_num}/GIS/"+filename+f' - DEM_debris_flow_criteria - i{iter_num}.html') == False and plot_option:
						plot_DEM_mat_map_v7_0(f"{output_folder_path_iter_temp}{iter_num}/GIS/", filename+f' - DEM_debris_flow_criteria - i{iter_num}', 'dfc', gridUniqueX, gridUniqueY, None, DEM_debris_flow_criteria, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

					# store file name
					temp_dict["DEM_UCA"] = None
					temp_dict["DEM_debris_flow_criteria"] = [f"{output_folder_path_iter_temp}{iter_num}/GIS/", f"{filename} - DEM_debris_flow_criteria - i{iter_num}.{output_txt_format}"]
     
					monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
					del temp_dict

			print('		Generating the debris-flow initiation criteria file completed!\n')

		######################################################
		## generate geometry for time step = 0
		######################################################
		###########################
		## groundwater table 
		###########################
		print('The programming is reading the initial groundwater table data for analysis ... \n')

		DEM_gwt_z, gwt_depth_from_surf = generate_groundwater_GIS_data(input_folder_path, ground_water_model, ground_water_data, DEM_surface, DEM_base, DEM_soil_thickness)

		# add initial groundwater table to each monte carlo simulations 
		for iter_num in range(1,monte_carlo_iteration_max+1):
			output_folder_path_iter_temp_hydraulics = f"{output_folder_path}iteration_{iter_num}/hydraulics/"

			# plot
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - gwt_dz - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - gwt_dz - t0 - i{iter_num}', 'gwt_dz', gridUniqueX, gridUniqueY, None, gwt_depth_from_surf, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - gwt_z - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - gwt_z - t0 - i{iter_num}', 'gwt_z', gridUniqueX, gridUniqueY, None, DEM_gwt_z, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)

			# export data
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "gwt_dz", gwt_depth_from_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "gwt_z", DEM_gwt_z, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=0, iteration=iter_num)

			# store file name
			gwt_dz_temp_dict = {"0": [output_folder_path_iter_temp_hydraulics, f"{filename} - gwt_dz - t0 - i{iter_num}.{output_txt_format}"]}
			gwt_z_temp_dict = {"0": [output_folder_path_iter_temp_hydraulics, f"{filename} - gwt_z - t0 - i{iter_num}.{output_txt_format}"]}

			# store file name
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]
			temp_dict["gwt_dz"] = deepcopy(gwt_dz_temp_dict)
			temp_dict["gwt_z"] = deepcopy(gwt_z_temp_dict)
			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict, gwt_dz_temp_dict, gwt_z_temp_dict

		print('		Generating the initial groundwater table files completed!\n')

		###########################
		## material properties - DEM
		###########################
		print('The programming is assigning material properties and initial state for analysis ... \n')

		# SWCC model: "vG" = van Genutchen (1980) - value = 0
		# SWCC model: "FX" = Fredlund and Xing (1994) - value = 1

		# material ID 
		if material_file_name is None or (isinstance(material_file_name, str) and material_file_name != "GIS"):  # uniform or no-zone-based material properties 
			DEM_material_id = np.ones((DEM_surface.shape), dtype=int)
			DEM_material_id_list = [1]
		elif isinstance(material_file_name, str) and material_file_name != "GIS":  # zone-based material properties 
			DEM_material_id, _, _ = read_GIS_data(material_file_name, input_folder_path, full_output=False)
			DEM_material_id_list = np.unique(DEM_material_id).tolist()

		# material properties
		for iter_num in range(1,monte_carlo_iteration_max+1):
			# plot
			if os.path.exists(f"{output_folder_path}iteration_{iter_num}/material/{filename} - DEM_material_id - i{iter_num}.html") == False and plot_option:
				plot_DEM_mat_map_v7_0(f"{output_folder_path}iteration_{iter_num}/material/", f"{filename} - DEM_material_id - i{iter_num}", 'mID', gridUniqueX, gridUniqueY, None, DEM_material_id, contour_limit=None, open_html=False, layout_width=1000, layout_height=1000)
			# export data
			generate_output_GIS(output_txt_format, f"{output_folder_path}iteration_{iter_num}/material/", filename, "DEM_material_id", DEM_material_id, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=None, iteration=iter_num)

		# generate GIS files and plots for each monte carlo iteration
		# (1) GIS data for each material properties for each iteration (iteration = 1 when deterministic)
		# (2) dictionary storing all material properties for each iteration 
		monte_carlo_iter_material_filename_dict = define_random_field_step_monte_carlo_filenameOnly(DEM_material_id, gridUniqueX, gridUniqueY, deltaX, deltaY, material, cpu_num, iterations=monte_carlo_iteration_max, output_folder_dir=output_folder_path, save_file_name=filename, output_txt_format=output_txt_format, XYZ_row_or_col_increase_first=XYZ_row_or_col_increase_first, DEM_noData=DEM_noData, nodata_value=nodata_value, dz_incre=dz, plot=plot_option)
		'''
		monte_carlo_iter_material_filename_dict[iteration number] = {
			"hydraulic": {
				"SWCC_model", "SWCC_a", "SWCC_n", "SWCC_m", "k_sat", "initial_suction", "theta_sat", "theta_residual", "soil_m_v", "max_surface_storage"
			},
			"soil": {
				"unit_weight", "phi", "phi_b", "c"
			},
			"root": {
				"unit_weight", "model",
				"parameters_constant": [root_c_base, root_c_side, root_depth],
				"parameters_van_Zadelhoff": [root_alpha2, root_beta2, root_RR_max]
			}
		}
		'''

		# store file name
		for iter_num in range(1,monte_carlo_iteration_max+1):
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]
			temp_dict["material"] = deepcopy(monte_carlo_iter_material_filename_dict[iter_num])
			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict

		print('		Generating the material properties completed!\n')

		###########################
		## rainfall GIS - DEM
		########################### 
		print('The programming is generating precipitation for analysis ... \n')

		# generate random rainfall time series for each grid cell
		monte_carlo_iter_I_filename_dict = define_random_rainfall_step_monte_carlo(rain_time_I, gridUniqueX, gridUniqueY, deltaX, deltaY, cpu_num, input_folder_path, output_folder_path, filename, iterations=monte_carlo_iteration_max, output_txt_format=output_txt_format, XYZ_row_or_col_increase_first=XYZ_row_or_col_increase_first, DEM_noData=DEM_noData, nodata_value=nodata_value, I_dp=rate_dp, plot=plot_option)
		'''
		monte_carlo_iter_I_filename_dict[iteration number] = {
			time: rain_I_GIS filename
			...
			}
		}
		'''

		# store file name
		for iter_num in range(1,monte_carlo_iteration_max+1):
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]
			temp_dict["intensity"] = deepcopy(monte_carlo_iter_I_filename_dict[iter_num])
			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict  

		# surface storage (S), cumulative runoff (RO), cumulative rainfall (P) 
		DEM_S = np.zeros((DEM_surface.shape), dtype=float)
		DEM_RO = np.zeros((DEM_surface.shape), dtype=float)
		DEM_P = np.zeros((DEM_surface.shape), dtype=float)

		# rainfall infiltration rate (f), cumulative rainfall infiltration (F), wetting front Z (wetting_front_z), infiltrated depth from surface (zw)
		DEM_infil_rate_f = np.zeros(DEM_surface.shape)
		DEM_infil_cumul_F = np.zeros(DEM_surface.shape)

		# if groundwater table is at surface, then all saturated -> infiltrated depth (infil_zw) and wetting front elevation (wetting_front_z) is at the base
		# if not assume top surface are dry and anything at and below the groundwater table is saturated
		DEM_infil_zw = np.where(np.logical_or(gwt_depth_from_surf == 0, DEM_gwt_z >= DEM_surface), DEM_soil_thickness, 0)
		DEM_wetting_front_z = np.where(np.logical_or(gwt_depth_from_surf == 0, DEM_gwt_z >= DEM_surface), DEM_base, DEM_surface)

		# add precipitation to each monte carlo simulations
		Surface_Storage_dict = {}
		Precipitation_dict = {}
		Runoff_dict = {}
		f_rate_dict = {}
		F_cumul_dict = {}
		z_w_dict = {}
		wet_z_dict = {}
		for iter_num in range(1,monte_carlo_iteration_max+1):
			output_folder_path_iter_temp_hydraulics = f"{output_folder_path}iteration_{iter_num}/hydraulics/"

			# plot
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - Surface_Storage - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - Surface_Storage - t0 - i{iter_num}', 'S', gridUniqueX, gridUniqueY, None, DEM_S, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - Precipitation - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - Precipitation - t0 - i{iter_num}', 'P', gridUniqueX, gridUniqueY, None, DEM_P, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - Runoff - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - Runoff - t0 - i{iter_num}', 'RO', gridUniqueX, gridUniqueY, None, DEM_RO, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - f_rate - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - f_rate - t0 - i{iter_num}', 'f', gridUniqueX, gridUniqueY, None, DEM_infil_rate_f, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - F_cumul - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - F_cumul - t0 - i{iter_num}', 'F', gridUniqueX, gridUniqueY, None, DEM_infil_cumul_F, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - z_w - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - z_w - t0 - i{iter_num}', 'z_w', gridUniqueX, gridUniqueY, None, DEM_infil_zw, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)
			if os.path.exists(output_folder_path_iter_temp_hydraulics+filename+f' - wet_z - t0 - i{iter_num}.html') == False and plot_option:
				plot_DEM_mat_map_v7_0(output_folder_path_iter_temp_hydraulics, filename+f' - wet_z - t0 - i{iter_num}', 'wet_z', gridUniqueX, gridUniqueY, None, DEM_wetting_front_z, contour_limit=[0, 1.0, 0.1], open_html=False, layout_width=1000, layout_height=1000)

			# export data
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "Surface_Storage", DEM_S, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "Precipitation", DEM_P, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "Runoff", DEM_RO, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "f_rate", DEM_infil_rate_f, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, rate_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "F_cumul", DEM_infil_cumul_F, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, cumul_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "z_w", DEM_infil_zw, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=0, iteration=iter_num)
			generate_output_GIS(output_txt_format, output_folder_path_iter_temp_hydraulics, filename, "wet_z", DEM_wetting_front_z, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, dx_dp, dy_dp, dz_dp, time=0, iteration=iter_num)

			# store file name
			Surface_Storage_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - Surface_Storage - t0 - i{iter_num}.{output_txt_format}"]
			Precipitation_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - Precipitation - t0 - i{iter_num}.{output_txt_format}"]
			Runoff_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - Runoff - t0 - i{iter_num}.{output_txt_format}"]
			f_rate_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - f_rate - t0 - i{iter_num}.{output_txt_format}"]
			F_cumul_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - F_cumul - t0 - i{iter_num}.{output_txt_format}"]
			z_w_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - z_w - t0 - i{iter_num}.{output_txt_format}"]
			wet_z_dict["0"] = [output_folder_path_iter_temp_hydraulics, filename+f" - wet_z - t0 - i{iter_num}.{output_txt_format}"]

			# store file name
			temp_dict = monte_carlo_iter_filename_dict["iterations"][str(iter_num)]
			temp_dict["Surface_Storage"] = deepcopy(Surface_Storage_dict)
			temp_dict["Precipitation"] = deepcopy(Precipitation_dict)
			temp_dict["Runoff"] = deepcopy(Runoff_dict)
			temp_dict["f_rate"] = deepcopy(f_rate_dict)
			temp_dict["F_cumul"] = deepcopy(F_cumul_dict)
			temp_dict["z_w"] = deepcopy(z_w_dict)
			temp_dict["wet_z"] = deepcopy(wet_z_dict)
			monte_carlo_iter_filename_dict["iterations"][str(iter_num)] = deepcopy(temp_dict)
			del temp_dict

		print('		Generating the precipitation completed!\n')

		######################################################
		## hydraulic properties at time_step = 0 at each DEM cell
		######################################################	
		monte_carlo_iter_filename_dict = generate_t0_GA_pond_parameters(monte_carlo_iteration_max, monte_carlo_iter_filename_dict, output_folder_path, filename, DEM_soil_thickness, dip_surf, DEM_noData, nodata_value, gridUniqueX, gridUniqueY, deltaX, deltaY, XYZ_row_or_col_increase_first, DEM_surf_dip_infiltraion_apply, plot_option, cpu_num, dz, dx_dp, dy_dp, theta_dp, press_dp, cumul_dp, dz_dp, t_dp)

		print('		Generating the material properties and initial state data completed!\n')
		
		######################################################
		## export the monte_carlo_iter_filename_dict into json files 
		######################################################	
		# export
		with open(f"{output_folder_path}{filename} - all_input.json", 'w') as f:
			json.dump(monte_carlo_iter_filename_dict, f, indent=4, cls=json_serialize)

		print('		Prepared to start the simulations!\n')


	## use JSON files to run the simulations
	elif isinstance(restarting_simulation_dict, dict):
		monte_carlo_iter_filename_dict = deepcopy(restarting_simulation_dict)

		print('		Imported the monte carlo simulation files to restart simulation!\n')


	######################################################################################################################################################
	## perform simulations from monte carlo simulation JSON files 
	######################################################################################################################################################
	monte_carlo_iter_result_filename_dict = perform_3DTSP_v1(monte_carlo_iter_filename_dict)

	######################################################################################################################################################
	## analyze probabilistic analysis based on the overall simulation results
	######################################################################################################################################################
	print('The programming is computing probabilistic analysis results ... \n')

	monte_carlo_iter_result_prob_filename_dict = run_probabilistic_results(monte_carlo_iter_result_filename_dict)

	# export final all input and results JSON file
	with open(f"{output_folder_path}{filename} - all_input_results.json", 'w') as f:
		json.dump(monte_carlo_iter_result_prob_filename_dict, f, indent=4, cls=json_serialize)

	print('		 Computation of probabilistic physically-based shallow landslide susceptibility is completed!\n')
