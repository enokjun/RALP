#!/usr/bin/python3

'''
Authors:		Dr. Enok Cheon (3DTSP and GUI), Dr. Emir A. Oguz (3DPLS)
Association:	Dept. of Natural Hazards, NGI, Sandakerveien 140, 0484 Oslo
Date:			Sep 05, 2025
Purpose:		Robust Areal Landslide Prediction (RALP) - 3DTSP and 3DPLS
Language:		Python3
License:		MIT
   
Copyright (c) <2025> <Enok Cheon>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

###########################################################################
## import libraries for GUI
###########################################################################
if __name__ == '__main__':
	print(
'''
###########################################################################
Authors:       Dr. Enok Cheon (3DTS and GUI), Dr. Emir A. Oguz (3DPLS)
Association:   Dept. of Natural Hazards, NGI, Sandakerveien 140, 0484 Oslo
Date:          Sep 05, 2025
Purpose:       Robust Areal Landslide Prediction (RALP) - 3DTSP and 3DPLS
Language:      Python3
License:       MIT
   
Copyright (c) <2025> <Enok Cheon>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###########################################################################

'''
	)
	print("The programming is importing python libraries for analysis ... ")

# GUI
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import filedialog
# from tkinter import font

# additional computational library imported for 3DTSP and 3DPLS computing
import numpy as np
from scipy.interpolate import griddata
import pandas as pd 
from copy import deepcopy 

# basic libraries
import yaml

# run terminal or cmd/powershell
import subprocess

# os related 
import shutil
import csv
import os
import sys
from platform import system

# main functions
import main_3DTSP_v20250813 as m3DTSP

if __name__ == '__main__':
	print("Importing modules (this may take a while) ... ")

###########################################################################
## Read data stored in CSV files
###########################################################################
# check if string is float
def is_float(x):
	try:
		float(x)
		return True
	except ValueError:
		return False
	
# check if string is integer
def is_int(x):
	try:
		int(x)
		return True
	except ValueError:
		return False
	
# import csv file and convert any number (int or float) into number types (int or float)
def csv2list_numbercheck(fileName, starting_row=0, end_row=None):
	"""convert csv (comma deliminated) file into numeric nested list

	Args:
		fileName (str): csv file
		starting_row (int, optional): row number to which start extracting. Defaults to 0.

	Returns:
		list: data from csv file in list format
	"""
	with open(fileName, 'r') as f:
		reader = csv.reader(f)
		csvListTxt = list(reader)

	if end_row is None:
		end_row = len(csvListTxt)
	elif isinstance(end_row, int):
		end_row = min(end_row, len(csvListTxt))

	csvList= []
	for idR in range(starting_row, end_row):	
		csvListTxt[idR] = [x for x in csvListTxt[idR] if x != '']
		tempList=[int(i) if is_int(i) else float(i) if is_float(i) else i for i in csvListTxt[idR]]    # only include numbers, skip non-numeric values
		csvList.append(tempList)

	return csvList


###########################################################################
## GUI main body
###########################################################################
def RALP_GUI():

	###########################################################################
	## what system are we running on, which text editor is available?
	###########################################################################
	
	opsys = system()
	if not opsys in ["Windows", "Linux", "Darwin"]:
		print("Operating system {:s} not supported.\n".format(opsys))
		sys.exit(1)

	if opsys == "Darwin":
		editor = "TextEdit"				# default editor on macOS
		pdf_viewer = "preview"			# default PDF viewer on macOS

	elif opsys == "Linux":

		flag = 0

		if os.path.isfile("/usr/bin/xdg-open") == True:
			fileman = "xdg-open"
		elif os.path.isfile("/usr/bin/konqueror"):			# KDE
			fileman = "konqueror"
		elif os.path.isfile("/usr/bin/dolphin"):			# KDE
			fileman = "dolphin"
		elif os.path.isfile("/usr/bin/nautilus"):			# Gnome
			fileman = "nautilus"
		elif os.path.isfile("/usr/bin/pcmanfm"):			# e.g. LXDE
			fileman = "pcmanfm"
		elif os.path.isfile("/usr/bin/pcmanfm-qt"):			# e.g. LXqt
			fileman = "pcmanfm-qt"
		else:
			print("\nNo graphical file manager found. Install one among:")
			print("    gedit, kate, sublime_text, geany, leafpad")
			print("or edit the top of main_3DTS_v20250130.py")
			print("to reflect your system's set-up.")
			flag += 1

		if os.path.isfile("/usr/bin/xdg-open"):
			editor = "xdg-open"
		elif os.path.isfile("/usr/bin/gedit") == True:		# Debian & Co.
			editor = "gedit"
		elif os.path.isfile("/usr/bin/kate") == True:		# KDE
			editor = "kate"
		elif os.path.isfile("/usr/bin/sublime_text") == True:
			editor = "sublime_text"
		elif os.path.isfile("/snap/bin/sublime_text") == True:
			editor = "snap run sublime_text"
		elif os.path.isfile("/usr/bin/geany") == True:		# GTK-based distros
			editor = "geany"
		elif os.path.isfile("/snap/bin/geany") == True:		# GTK-based distros
			editor = "snap run geany"
		elif os.path.isfile("/usr/bin/leafpad") == True:	# GTK-based distros
			editor = "leafpad"		
		elif os.path.isfile("/snap/bin/leafpad") == True:	# GTK-based distros
			editor = "snap run leafpad"
		else:
			print("\nNo graphical text editor found. Install one among:")
			print("    gedit, kate, sublime_text, geany, leafpad")
			print("or edit the top of main_3DTS_v20250130.py.")
			flag += 1
		
		if os.path.isfile("/usr/bin/xdg-open") == True:
			pdf_viewer = "xdg-open"
		elif os.path.isfile("/usr/bin/qpdfview") == True:
			pdf_viewer = "qpdfview"
		elif os.path.isfile("/usr/bin/evince") == True:
			pdf_viewer = "evince"
		elif os.path.isfile("/snap/bin/evince") == True:
			pdf_viewer = "snap run evince"
		elif os.path.isfile("/usr/bin/okular") == True:
			pdf_viewer = "okular"
		elif os.path.isfile("/snap/bin/okular") == True:
			pdf_viewer = "snap run okular"
		elif os.path.isfile("/usr/bin/acroread") == True:
			pdf_viewer = "acroread"
		else:
			print("\nNo PDF viewer found. Install one among:")
			print("    qpdfview, okular, evince, acroread")
			print("or edit the top of main_3DTS_v20250130.py.")
			flag += 1

		if flag > 0:
			sys.exit(2)
			
	###########################################################################
	## folder path of where the GUI file is installed
	###########################################################################
	if getattr(sys, 'frozen', False):
		application_path = os.path.dirname(sys.executable)
	else:
		try:
			app_full_path = os.path.realpath(__file__)
			application_path = os.path.dirname(app_full_path)
		except NameError:
			application_path = os.getcwd()

	app_path = os.path.join(application_path)

	###########################################################################
	## set up GUI root
	###########################################################################
	root = tk.Tk()

	root.title("Robust Areal Landslide Prediction (RALP) v1.00")    # S/W title
	root.call('wm', 'iconphoto', root._w, tk.PhotoImage(file='NGI_logo_cropped.png'))     # icon
	root.geometry("1995x935")            # window size - when need to fix 

	###########################################################################
	## mainframe, canvas and scrollbar
	###########################################################################
	## reference: https://www.youtube.com/watch?v=0WafQCaok6g

	#################################
	## main frame - overall contain the canvas and the scrollbars
	#################################
	main_frame = tk.Frame(root)
	main_frame.pack(fill='both', expand=True)

	main_canvas = tk.Canvas(main_frame)
	# main_canvas = tk.Canvas(main_frame, width=main_frame.winfo_screenwidth(), height=main_frame.winfo_screenheight())
	# main_canvas = tk.Canvas(main_frame, width=1900, height=900)
	# main_canvas.pack(side='top', fill='both', expand=True)
	# main_canvas.pack(side='left', fill='x', expand=True)
	# main_canvas.grid(row=0, rowspan=1, column=0, columnspan=1, padx=0, pady=0, sticky="news")

	###########################################################################
	## GUI operation
	###########################################################################
	root.resizable(width=True, height=True)
	# root.resizable(width=True, height=False)  # window resize is disabled in vertical direction
	# root.resizable(width=False, height=False)

	# set maxium and minimum size GUI can become
	root.maxsize(2000, 1000)
	root.minsize(650, 500)

	#################################
	## horizontal scroll bar
	#################################
	hor_scroll_bar = tk.Scrollbar(main_frame, orient='horizontal', command=main_canvas.xview)
	hor_scroll_bar.pack(side='bottom', fill='x')
	main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
	main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

	#################################
	## vertical scroll bar
	#################################
	ver_scroll_bar = tk.Scrollbar(main_frame, orient='vertical', command=main_canvas.yview)
	ver_scroll_bar.pack(side='right', fill='y')
	main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
	main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

	#################################
	## main GUI frame
	#################################
	# add canvas pack after packing the scroll bars to fit
	main_canvas.pack(side='left', fill='both', expand=True)

	GUI_frame = tk.Frame(main_canvas)
	main_canvas.create_window((0,0), window=GUI_frame, anchor="nw")

	###########################################################################
	## commands to operate when button is clicked or action is taken
	###########################################################################
	#################################
	# stop or when closing entire window
	#################################
	def quit_command():

		if status.cget("text") == "simulation running ":
		
			quit_response = messagebox.askyesno("Quit Simulation", "Are you sure you want to quit the simulation and close?")

			# pop up message based on simulation results
			if quit_response:       # cancel simulation
				root.quit()
				root.destroy()		
		
		else:
			root.quit()
			root.destroy()		

		return None

	#################################
	# basic project name, directories and overall input JSON file
	#################################
	# import overall input JSON (3DTSP) or YAML (3DPLS) file to rerun simulation 
	def open_overall_input_JSON_YAML_file_command():

		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_input_JSON_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select overall input JSON or YAML file",
								filetypes=(
									("input YAML file", "*.yaml"),
									("input YAML file", "*.yml"),
									("input YAML file", "*.YAML"),
									("input YAML file", "*.YML"),
									("input JSON file", "*.json"),
									("input JSON file", "*.JSON")
								)   
							)
		
		# display output folder location in the output text
		try:
			if len(selected_input_JSON_file) > 0 and os.path.isfile(selected_input_JSON_file):
				# delete whatever is written in the file name text output box - so new one can be added
				overall_input_folder_entry.delete(0, tk.END)
				overall_input_folder_entry.insert(0, selected_input_JSON_file)

				# update status to show similuation is running 
				status.config(text = "overall input JSON/YAML file loaded ")

		except:
			pass

		return None

	# select folder directory for input data
	def open_input_folder_command():

		# if file loading was done previously once and is valid, then reopen the current folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_filepath = filedialog.askdirectory(initialdir=file_path, title="Select input directory")

		# display input folder location in the input text
		try:
			if len(selected_filepath) > 0 and os.path.isdir(selected_filepath):

				# delete whatever is written in the file name text input box - so new one can be added
				input_folder_entry.delete(0, tk.END)
				input_folder_entry.insert(0, selected_filepath)

				# update status to show similuation is running 
				status.config(text = "input directory loaded ")

		except:
			pass

		return None

	# select folder directory for output data
	def open_output_folder_command():

		# if file loading was done previously once and is valid, then reopen the current folder 
		try:
			if len(output_folder_entry.get()) > 0 and os.path.isdir(output_folder_entry.get()):
				status.config(text="selecting new output folder path ")
				file_path = output_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_filepath = filedialog.askdirectory(initialdir=file_path, title="Select output directory")
		
		# display output folder location in the output text
		try:
			if len(selected_filepath) > 0 and os.path.isdir(selected_filepath):

				# delete whatever is written in the file name text output box - so new one can be added
				output_folder_entry.delete(0, tk.END)
				output_folder_entry.insert(0, selected_filepath)

				# update status to show similuation is running 
				status.config(text = "output directory loaded ")

		except:
			pass

		return None

	#################################
	# open DEM file
	#################################
	def open_DEM_file_command():

		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_DEM_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select DEM file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_DEM_file) > 0 and os.path.isfile(selected_DEM_file):

				# only need the filename
				file_path_name = selected_DEM_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				DEM_filename_entry.delete(0, tk.END)
				DEM_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "DEM file loaded ")

		except:
			pass

		return None


	#################################
	# soil depth
	#################################
	# sub window layout change based on soil depth option selected
	def soil_input_func():
		selected_soil_depth_assign_option = soil_depth_opt_combo.get()
		if selected_soil_depth_assign_option == "Uniform Depth":
			open_new_window_soil_uniform_depth()
		elif selected_soil_depth_assign_option == "GIS file":
			open_soil_GIS_file_command()
		elif selected_soil_depth_assign_option == "Holm (2012) & Edvarson (2013)":
			open_new_window_soil_HnE()
		elif selected_soil_depth_assign_option in ["Linear Multiregression", "Power Multiregression"]:
			open_new_window_soil_general()

	# function to prevent multiple windows to open while assigning soil depth data
	def close_soil_window_toplevel(sub_window):
		soil_depth_opt_combo.config(state="normal")  # Enable the combo
		soil_depth_data_assign_button.config(state="normal")  # Enable the assign button
		sub_window.destroy()		# close the sub window completely

	# Function to open a new window to assign uniform soil depth
	def open_new_window_soil_uniform_depth():
		# disable the combo and assign button to prevent multiple clicks
		soil_depth_opt_combo.config(state="disable")
		soil_depth_data_assign_button.config(state="disable")

		# Create a new window to get soil depth data
		new_window = tk.Toplevel(root)  
		new_window.title("Uniform Soil Depth")
		new_window.geometry("270x230") 
		new_window.resizable(width=True, height=True)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		###########
		## layout
		###########
		# title
		uniform_soil_assign_label = tk.Label(new_window, text="Uniform Soil Depth", font=("Arial", 12, "bold"), anchor="w", justify="left")
		uniform_soil_assign_label.grid(row=0, column=0, columnspan=6, padx=5, pady=(0,5), sticky="w")

		# get uniform (or mean)
		uniform_soil_assign_label = tk.Label(new_window, text="Mean Soil Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		uniform_soil_assign_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=uniform_soil_depth_double)
		uniform_soil_assign_label.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
		uniform_soil_assign_entry.grid(row=1, column=2, columnspan=4, padx=5, pady=5, sticky="we")
  
		# get min 
		uniform_soil_min_label = tk.Label(new_window, text="Min Soil Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		uniform_soil_min_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=min_soil_depth_double)
		uniform_soil_min_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
		uniform_soil_min_entry.grid(row=2, column=2, columnspan=4, padx=5, pady=5, sticky="we")

		# get max 
		uniform_soil_max_label = tk.Label(new_window, text="Max Soil Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		uniform_soil_max_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=max_soil_depth_double)
		uniform_soil_max_label.grid(row=3, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
		uniform_soil_max_entry.grid(row=3, column=2, columnspan=4, padx=5, pady=5, sticky="we")
  
		# get CoV 
		uniform_soil_cov_label = tk.Label(new_window, text="CoV", font=("Arial", 12), anchor="w", justify="left")
		uniform_soil_cov_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=soil_depth_probabilistic_cov)
		uniform_soil_cov_label.grid(row=4, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
		uniform_soil_cov_entry.grid(row=4, column=2, columnspan=4, padx=5, pady=5, sticky="we")

		# disable or enable parameter   
		if soil_depth_probabilistic_check_int.get() >= 1:
			uniform_soil_cov_entry.config(state="normal")
			uniform_soil_min_entry.config(state="normal")
			uniform_soil_max_entry.config(state="normal")
		else:
			uniform_soil_cov_entry.config(state="disable")
			uniform_soil_min_entry.config(state="disable")
			uniform_soil_max_entry.config(state="disable")

		# assign button
		uniform_soil_assign_button = tk.Button(new_window, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_soil_window_toplevel(new_window)) 
		uniform_soil_assign_button.grid(row=5, column=0, columnspan=6, padx=5, pady=5, sticky="we")

		# Call close_soil_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_soil_window_toplevel(new_window)) 
		new_window.mainloop()

	# open soil GIS file
	def open_soil_GIS_file_command():

		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_soil_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select soil thickness GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_soil_GIS_file) > 0 and os.path.isfile(selected_soil_GIS_file):
				# only need the filename
				file_path_name = selected_soil_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
	   
				GIS_soil_depth_str.set(file_name_only)  # set the GIS soil depth file path to the string variable

				status.config(text = "soil thickness GIS file loaded ")       		# update status to show similuation is running 
		except:
			pass

		return None

	# assign min and max range for dip-based soil depth from Holm (2012) & Edvarson (2013)
	def open_new_window_soil_HnE():
		# disable the combo and assign button to prevent multiple clicks
		soil_depth_opt_combo.config(state="disable")
		soil_depth_data_assign_button.config(state="disable")

		# Create a new window to get soil depth data
		new_window = tk.Toplevel(root)  
		new_window.title("Holm (2012) & Edvarson (2013)")
		new_window.geometry("255x190") 
		new_window.resizable(width=True, height=True)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		###########
		## layout
		###########
		# other values
		HnE_soil_assign_label = tk.Label(new_window, text="Dip-Based Soil Depth Range", font=("Arial", 12, "bold"), anchor="w", justify="left")
		HnE_min_soil_assign_label = tk.Label(new_window, text="Min Soil Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		HnE_max_soil_assign_label = tk.Label(new_window, text="Max Soil Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		HnE_cov_soil_assign_label = tk.Label(new_window, text="CoV", font=("Arial", 12), anchor="w", justify="left")
		HnE_min_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=min_soil_depth_double)
		HnE_max_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=max_soil_depth_double)
		HnE_cov_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=soil_depth_probabilistic_cov)
		HnE_soil_assign_button = tk.Button(new_window, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_soil_window_toplevel(new_window)) 

		HnE_soil_assign_label.grid(row=0, column=0, columnspan=6, padx=5, pady=(0,5), sticky="w")
		HnE_min_soil_assign_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_min_soil_depth_entry.grid(row=2, column=3, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_max_soil_assign_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_max_soil_depth_entry.grid(row=3, column=3, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_cov_soil_assign_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_cov_soil_depth_entry.grid(row=4, column=3, columnspan=3, padx=5, pady=5, sticky="we")
		HnE_soil_assign_button.grid(row=5, column=0, columnspan=6, padx=5, pady=5, sticky="we")

		# disable or enable parameter   
		if soil_depth_probabilistic_check_int.get() >= 1:
			HnE_cov_soil_depth_entry.config(state="normal")
		else:
			HnE_cov_soil_depth_entry.config(state="disable")

		# Call close_soil_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_soil_window_toplevel(new_window)) 
		new_window.mainloop()

	# open file for soil depth based on linear or power multiregression
	def open_soil_multiregression_GIS_file_command(GIS_data_file_str):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_soil_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select soil thickness GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_soil_GIS_file) > 0 and os.path.isfile(selected_soil_GIS_file):
				# only need the filename
				file_path_name = selected_soil_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				GIS_data_file_str.set(file_name_only)  # set the GIS soil depth file path to the string variable
		except:
			pass

		return None

	# open new window for soil depth based on linear or power multiregression
	def open_new_window_soil_general():
		# disable the combo and assign button to prevent multiple clicks
		soil_depth_opt_combo.config(state="disable")
		soil_depth_data_assign_button.config(state="disable")

		# Create a new window to get soil depth data
		new_window = tk.Toplevel(root)  
		new_window.title("Soil Depth Multiregression")
		new_window.geometry("575x800") 
		new_window.resizable(width=True, height=True)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		####################################
		# layout
		####################################
		# meta
		gen_reg_soil_assign_label = tk.Label(new_window, text="Regression Soil Depth", font=("Arial", 12, "bold"), anchor="w", justify="left")
  
		num_params_label = tk.Label(new_window, text="Number of Parameters", font=("Arial", 12), anchor="w", justify="left")
		num_params_str = tk.StringVar(value=10)  # default number of parameters is 10
		num_params_combo = ttk.Combobox(
				new_window,
				state="readonly",
				values=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
				textvariable=num_params_str,
				width=10,
				font=("Arial", 12)
			)
		num_params_combo.set("10")  # set default value to 10

		gen_reg_soil_assign_label.grid(row=0, column=0, columnspan=11, padx=5, pady=(0,5), sticky="w")
		num_params_label.grid(row=1, column=0, columnspan=4, padx=5, pady=(0,5), sticky="we")
		num_params_combo.grid(row=1, column=4, columnspan=4, padx=5, pady=(0,5), sticky="we")

		def gen_reg_input_func(*args):
			# disable or enable parameter   
			if int(num_params_str.get()) >= 1:
				gen_reg_param1_entry.config(state="normal")
				gen_reg_param1_filename_entry.config(state="normal")
				gen_reg_param1_filename_button.config(state="normal")
			else:
				gen_reg_param1_entry.config(state="disable")
				gen_reg_param1_filename_entry.config(state="disable")
				gen_reg_param1_filename_button.config(state="disable")
	
			if int(num_params_str.get()) >= 2:
				gen_reg_param2_entry.config(state="normal")
				gen_reg_param2_filename_entry.config(state="normal")
				gen_reg_param2_filename_button.config(state="normal")
			else:
				gen_reg_param2_entry.config(state="disable")
				gen_reg_param2_filename_entry.config(state="disable")
				gen_reg_param2_filename_button.config(state="disable")	
	
			if int(num_params_str.get()) >= 3:
				gen_reg_param3_entry.config(state="normal")
				gen_reg_param3_filename_entry.config(state="normal")
				gen_reg_param3_filename_button.config(state="normal")
			else:
				gen_reg_param3_entry.config(state="disable")
				gen_reg_param3_filename_entry.config(state="disable")
				gen_reg_param3_filename_button.config(state="disable")	
	
			if int(num_params_str.get()) >= 4:
				gen_reg_param4_entry.config(state="normal")
				gen_reg_param4_filename_entry.config(state="normal")
				gen_reg_param4_filename_button.config(state="normal")
			else:
				gen_reg_param4_entry.config(state="disable")
				gen_reg_param4_filename_entry.config(state="disable")
				gen_reg_param4_filename_button.config(state="disable")	
	
			if int(num_params_str.get()) >= 5:
				gen_reg_param5_entry.config(state="normal")
				gen_reg_param5_filename_entry.config(state="normal")
				gen_reg_param5_filename_button.config(state="normal")
			else:
				gen_reg_param5_entry.config(state="disable")
				gen_reg_param5_filename_entry.config(state="disable")
				gen_reg_param5_filename_button.config(state="disable")
	
			if int(num_params_str.get()) >= 6:
				gen_reg_param6_entry.config(state="normal")
				gen_reg_param6_filename_entry.config(state="normal")
				gen_reg_param6_filename_button.config(state="normal")
			else:
				gen_reg_param6_entry.config(state="disable")
				gen_reg_param6_filename_entry.config(state="disable")
				gen_reg_param6_filename_button.config(state="disable")
	
			if int(num_params_str.get()) >= 7:
				gen_reg_param7_entry.config(state="normal")
				gen_reg_param7_filename_entry.config(state="normal")
				gen_reg_param7_filename_button.config(state="normal")
			else:	
				gen_reg_param7_entry.config(state="disable")
				gen_reg_param7_filename_entry.config(state="disable")
				gen_reg_param7_filename_button.config(state="disable")
	
			if int(num_params_str.get()) >= 8:
				gen_reg_param8_entry.config(state="normal")
				gen_reg_param8_filename_entry.config(state="normal")
				gen_reg_param8_filename_button.config(state="normal")
			else:
				gen_reg_param8_entry.config(state="disable")
				gen_reg_param8_filename_entry.config(state="disable")
				gen_reg_param8_filename_button.config(state="disable")	
	
			if int(num_params_str.get()) >= 9:
				gen_reg_param9_entry.config(state="normal")
				gen_reg_param9_filename_entry.config(state="normal")
				gen_reg_param9_filename_button.config(state="normal")
			else:	
				gen_reg_param9_entry.config(state="disable")
				gen_reg_param9_filename_entry.config(state="disable")
				gen_reg_param9_filename_button.config(state="disable")
	
			if int(num_params_str.get()) >= 10:
				gen_reg_param10_entry.config(state="normal")
				gen_reg_param10_filename_entry.config(state="normal")
				gen_reg_param10_filename_button.config(state="normal")
			else:
				gen_reg_param10_entry.config(state="disable")
				gen_reg_param10_filename_entry.config(state="disable")
				gen_reg_param10_filename_button.config(state="disable")	

		##################
		# max and min soil depth range
		##################
		gen_reg_min_soil_assign_label = tk.Label(new_window, text="Min Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		gen_reg_max_soil_assign_label = tk.Label(new_window, text="Max Depth (m)", font=("Arial", 12), anchor="w", justify="left")
		gen_reg_min_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=min_soil_depth_double)
		gen_reg_max_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=max_soil_depth_double)

		gen_reg_min_soil_assign_label.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="we")
		gen_reg_min_soil_depth_entry.grid(row=2, column=4, columnspan=4, padx=5, pady=5, sticky="we")
		gen_reg_max_soil_assign_label.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="we")
		gen_reg_max_soil_depth_entry.grid(row=3, column=4, columnspan=4, padx=5, pady=5, sticky="we")

		##################
		# CoV
		##################
		gen_reg_cov_soil_assign_label = tk.Label(new_window, text="CoV", font=("Arial", 12), anchor="w", justify="left")
		gen_reg_cov_soil_depth_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=soil_depth_probabilistic_cov)

		gen_reg_cov_soil_assign_label.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="we")
		gen_reg_cov_soil_depth_entry.grid(row=4, column=4, columnspan=4, padx=5, pady=5, sticky="we")

		# disable or enable parameter   
		if soil_depth_probabilistic_check_int.get() >= 1:
			gen_reg_cov_soil_depth_entry.config(state="normal")
		else:
			gen_reg_cov_soil_depth_entry.config(state="disable")

		##################
		# max and min soil depth range
		##################		
		separator_hor = ttk.Separator(new_window, orient='horizontal')
		separator_hor.grid(row=5, column=0, columnspan=11, padx=1, pady=5, sticky="we")

		##################
		# paramters table
		##################	
		# table - header layout
		gen_reg_header_coeff_label = tk.Label(new_window, text="Coefficient", font=("Arial", 12, "bold"), anchor="w", justify="center")
		gen_reg_header_filename_label = tk.Label(new_window, text="File Name", font=("Arial", 12, "bold"), anchor="w", justify="center")

		gen_reg_header_coeff_label.grid(row=6, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_header_filename_label.grid(row=6, column=4, columnspan=2, padx=5, pady=5, sticky="we")

		# table - column layout
		tk.Label(new_window, text="Intercept", font=("Arial", 12), anchor="w", justify="left").grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_intercept_label
		tk.Label(new_window, text="Parameter 1", font=("Arial", 12), anchor="w", justify="left").grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param1_label
		tk.Label(new_window, text="Parameter 2", font=("Arial", 12), anchor="w", justify="left").grid(row=9, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param2_label
		tk.Label(new_window, text="Parameter 3", font=("Arial", 12), anchor="w", justify="left").grid(row=10, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param3_label
		tk.Label(new_window, text="Parameter 4", font=("Arial", 12), anchor="w", justify="left").grid(row=11, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param4_label
		tk.Label(new_window, text="Parameter 5", font=("Arial", 12), anchor="w", justify="left").grid(row=12, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param5_label
		tk.Label(new_window, text="Parameter 6", font=("Arial", 12), anchor="w", justify="left").grid(row=13, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param6_label
		tk.Label(new_window, text="Parameter 7", font=("Arial", 12), anchor="w", justify="left").grid(row=14, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param7_label
		tk.Label(new_window, text="Parameter 8", font=("Arial", 12), anchor="w", justify="left").grid(row=15, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param8_label
		tk.Label(new_window, text="Parameter 9", font=("Arial", 12), anchor="w", justify="left").grid(row=16, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param9_label
		tk.Label(new_window, text="Parameter 10", font=("Arial", 12), anchor="w", justify="left").grid(row=17, column=0, columnspan=2, padx=5, pady=5, sticky="we")  # gen_reg_param10_label
 
		# table - first column - coefficient entry
		gen_reg_intercept_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_intercept_double)
		gen_reg_param1_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param1_double)
		gen_reg_param2_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param2_double)
		gen_reg_param3_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param3_double)
		gen_reg_param4_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param4_double)
		gen_reg_param5_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param5_double)
		gen_reg_param6_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param6_double)
		gen_reg_param7_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param7_double)
		gen_reg_param8_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param8_double)
		gen_reg_param9_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param9_double)
		gen_reg_param10_entry = tk.Entry(new_window, width=15, bd=3, font=("Arial", 12), textvariable=gen_reg_param10_double)

		gen_reg_intercept_entry.grid(row=7, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param1_entry.grid(row=8, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param2_entry.grid(row=9, column=2, columnspan=2, padx=5, pady=5, sticky="we")	
		gen_reg_param3_entry.grid(row=10, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param4_entry.grid(row=11, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param5_entry.grid(row=12, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param6_entry.grid(row=13, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param7_entry.grid(row=14, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param8_entry.grid(row=15, column=2, columnspan=2, padx=5, pady=5, sticky="we")		
		gen_reg_param9_entry.grid(row=16, column=2, columnspan=2, padx=5, pady=5, sticky="we")
		gen_reg_param10_entry.grid(row=17, column=2, columnspan=2, padx=5, pady=5, sticky="we")	

		# table - second column - filename entry
		gen_reg_param1_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param1_filename_str)
		gen_reg_param2_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param2_filename_str)
		gen_reg_param3_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param3_filename_str)
		gen_reg_param4_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param4_filename_str)
		gen_reg_param5_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param5_filename_str)
		gen_reg_param6_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param6_filename_str)
		gen_reg_param7_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param7_filename_str)
		gen_reg_param8_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param8_filename_str)
		gen_reg_param9_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param9_filename_str)
		gen_reg_param10_filename_entry = tk.Entry(new_window, width=20, bd=3, font=("Arial", 12), textvariable=gen_reg_param10_filename_str)

		gen_reg_param1_filename_entry.grid(row=8, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param2_filename_entry.grid(row=9, column=4, columnspan=6, padx=5, pady=5, sticky="we")	
		gen_reg_param3_filename_entry.grid(row=10, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param4_filename_entry.grid(row=11, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param5_filename_entry.grid(row=12, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param6_filename_entry.grid(row=13, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param7_filename_entry.grid(row=14, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param8_filename_entry.grid(row=15, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param9_filename_entry.grid(row=16, column=4, columnspan=6, padx=5, pady=5, sticky="we")
		gen_reg_param10_filename_entry.grid(row=17, column=4, columnspan=6, padx=5, pady=5, sticky="we")

		# table - third column - filename select button
		gen_reg_param1_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param1_filename_str))
		gen_reg_param2_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param2_filename_str))
		gen_reg_param3_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param3_filename_str))
		gen_reg_param4_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param4_filename_str))
		gen_reg_param5_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param5_filename_str))
		gen_reg_param6_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param6_filename_str))
		gen_reg_param7_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param7_filename_str))
		gen_reg_param8_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param8_filename_str))
		gen_reg_param9_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param9_filename_str))
		gen_reg_param10_filename_button = tk.Button(new_window, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_soil_multiregression_GIS_file_command(gen_reg_param10_filename_str))

		gen_reg_param1_filename_button.grid(row=8, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param2_filename_button.grid(row=9, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param3_filename_button.grid(row=10, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param4_filename_button.grid(row=11, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param5_filename_button.grid(row=12, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param6_filename_button.grid(row=13, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param7_filename_button.grid(row=14, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param8_filename_button.grid(row=15, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param9_filename_button.grid(row=16, column=10, columnspan=1, padx=5, pady=5, sticky="we")
		gen_reg_param10_filename_button.grid(row=17, column=10, columnspan=1, padx=5, pady=5, sticky="we")

		num_params_str.trace_add("write", gen_reg_input_func)  	# disable and able based combobox option

		##################
		# assign 
		##################	
		gen_reg_soil_assign_button = tk.Button(new_window, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_soil_window_toplevel(new_window)) 
		gen_reg_soil_assign_button.grid(row=18, column=0, columnspan=11, padx=5, pady=5, sticky="we")

		# Call close_soil_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_soil_window_toplevel(new_window)) 
		new_window.mainloop()		

	#################################
	## open precomputed terrain surface dip and aspect GIS files
	#################################
	# open terrain surface dip GIS file
	def open_surf_dip_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_surf_dip_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select surface dip GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_surf_dip_GIS_file) > 0 and os.path.isfile(selected_surf_dip_GIS_file):

				# only need the filename
				file_path_name = selected_surf_dip_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				surf_dip_filename_entry.delete(0, tk.END)
				surf_dip_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "surface dip GIS file loaded ")

		except:
			pass

		return None

	# open terrain surface aspect GIS file
	def open_surf_aspect_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_surf_dip_dir_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select surface dip direction GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_surf_dip_dir_GIS_file) > 0 and os.path.isfile(selected_surf_dip_dir_GIS_file):

				# only need the filename
				file_path_name = selected_surf_dip_dir_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				surf_aspect_filename_entry.delete(0, tk.END)
				surf_aspect_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "surface dip direction GIS file loaded ")

		except:
			pass

		return None

	# open base dip GIS file
	def open_base_dip_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_base_dip_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select base dip GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_base_dip_GIS_file) > 0 and os.path.isfile(selected_base_dip_GIS_file):

				# only need the filename
				file_path_name = selected_base_dip_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				base_dip_filename_entry.delete(0, tk.END)
				base_dip_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "base dip GIS file loaded ")

		except:
			pass

		return None

	# open base aspect GIS file
	def open_base_aspect_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_base_dip_dir_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select base dip direction GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_base_dip_dir_GIS_file) > 0 and os.path.isfile(selected_base_dip_dir_GIS_file):

				# only need the filename
				file_path_name = selected_base_dip_dir_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				base_aspect_filename_entry.delete(0, tk.END)
				base_aspect_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "base dip direction GIS file loaded ")

		except:
			pass

		return None

	#################################
	# groundwater input
	#################################
	# sub window layout change based on groundwater table option selected
	def gwt_input_func():
		selected_gwt_assign_option = groundwater_opt_str.get()			
		if selected_gwt_assign_option in ["GWT elevation GIS"] :
			open_groundwater_data_GIS_file_command()
		elif selected_gwt_assign_option in ["Thickness Above Bedrock", "Depth From Surface", "% of Soil Thickness Above Bedrock", "% of Soil Thickness From Surface"]:
			open_new_window_gwt_data_assign(selected_gwt_assign_option)
   
	# function to prevent multiple windows to open while assigning soil depth data
	def close_gwt_window_toplevel(sub_window):
		groundwater_opt_combo.config(state="normal")  			# Enable the combo
		groundwater_data_assign_button.config(state="normal")  	# Enable the assign button
		sub_window.destroy()		# close the sub window completely

	# Function to open a new window to assign groundwater table data
	def open_new_window_gwt_data_assign(selected_gwt_assign_option):
		# disable the combo and assign button to prevent multiple clicks
		groundwater_opt_combo.config(state="disable")
		groundwater_data_assign_button.config(state="disable")

		# Create a new window to get soil depth data
		new_window = tk.Toplevel(root)  
		new_window.title("Groundwater Table Assignment")
		new_window.geometry("440x190") 
		new_window.resizable(width=True, height=False)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		# layout
		gwt_data_title_label = tk.Label(new_window, text=f"Groundwater: {groundwater_opt_str.get()}", font=("Arial", 12, "bold"), anchor="w", justify="left")

		if selected_gwt_assign_option in ["Thickness Above Bedrock", "Depth From Surface"]:
			gwt_data_val_label = tk.Label(new_window, text=f"Value (m)", font=("Arial", 12), anchor="w", justify="left")
		elif selected_gwt_assign_option in ["% of Soil Thickness Above Bedrock", "% of Soil Thickness From Surface"]:
			gwt_data_val_label = tk.Label(new_window, text=f"Value (%)", font=("Arial", 12), anchor="w", justify="left")

		gwt_data_val_entry = tk.Entry(new_window, width=25, bd=3, font=("Arial", 12), textvariable=gwt_value_double)
		gwt_data_filename_label = tk.Label(new_window, text=f"GIS filename", font=("Arial", 12), anchor="w", justify="left")
		gwt_data_filename_entry = tk.Entry(new_window, width=25, bd=3, font=("Arial", 12), textvariable=gwt_GIS_filename_str)
		gwt_data_filename_button = tk.Button(new_window, text="Select", width=5, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_groundwater_data_GIS_file_command(gwt_data_filename_entry)) 
		gwt_data_assign_button = tk.Button(new_window, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_gwt_window_toplevel(new_window)) 

		gwt_data_val_entry.config(state="normal")
		gwt_data_filename_entry.config(state="disable")
		gwt_data_filename_button.config(state="disable")

		def gwt_data_type_input_func(*args):
			# Enable or disable the entry and button based on the selected data type
			if gwt_data_type_str.get() == "number":
				gwt_data_val_entry.config(state="normal")
				gwt_data_filename_entry.config(state="disable")
				gwt_data_filename_button.config(state="disable")
				gwt_GIS_filename_str.set("")
			elif gwt_data_type_str.get() == "GIS":
				gwt_data_val_entry.config(state="disable")
				gwt_data_filename_entry.config(state="normal")
				gwt_data_filename_button.config(state="normal")
				gwt_value_double.set(0.0)

		gwt_data_type_label = tk.Label(new_window, text="Type of Data", font=("Arial", 12), anchor="w", justify="left")
		gwt_data_type_str = tk.StringVar()  
		gwt_data_type_combo = ttk.Combobox(
				new_window,
				state="readonly",
				values=["number", "GIS"],
				textvariable=gwt_data_type_str,
				width=10,
				font=("Arial", 12)
			)
		gwt_data_type_combo.current(0)  # set default value to "number"
		gwt_data_type_str.trace_add("write", gwt_data_type_input_func)  	# disable and able based combobox option

		gwt_data_title_label.grid(row=0, column=0, columnspan=4, padx=5, pady=(0,5), sticky="we")
		gwt_data_type_label.grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		gwt_data_type_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=(0,5), sticky="we")
		gwt_data_val_label.grid(row=2, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		gwt_data_val_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=(0,5), sticky="we")
		gwt_data_filename_label.grid(row=3, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		gwt_data_filename_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=(0,5), sticky="we")
		gwt_data_filename_button.grid(row=3, column=3, columnspan=1, padx=5, pady=(0,5), sticky="we")
		gwt_data_assign_button.grid(row=4, column=0, columnspan=4, padx=5, pady=(0,5), sticky="we")

		# Call close_soil_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_gwt_window_toplevel(new_window)) 
		new_window.mainloop()

	def open_groundwater_data_GIS_file_command(filename_entry=None):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_groundwater_data_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select initial groundwater GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_groundwater_data_GIS_file) > 0 and os.path.isfile(selected_groundwater_data_GIS_file):

				# only need the filename
				file_path_name = selected_groundwater_data_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				gwt_GIS_filename_str.set(file_name_only)

				if filename_entry is not None:
					# delete whatever is written in the file name text output box - so new one can be added
					filename_entry.delete(0, tk.END)
					filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "initial groundwater table elevation file loaded ")

		except:
			pass

		return None

	#################################
	# RiZero input
	################################# 
	# sub window layout change based on groundwater table option selected
	def rizero_input_func():
		selected_rizero_assign_option = RiZero_opt_str.get()			
		if selected_rizero_assign_option in ["Uniform"] :
			open_new_window_rizero_assign()
		elif selected_rizero_assign_option in ["GIS file"]:
			open_rizero_data_GIS_file_command()

	# function to prevent multiple windows to open while assigning soil depth data
	def close_rizero_window_toplevel(sub_window):
		RiZero_opt_combo.config(state="normal")  			# Enable the combo
		RiZero_assign_button.config(state="normal")  	# Enable the assign button
		sub_window.destroy()		# close the sub window completely

	# Function to open a new window to assign groundwater table data
	def open_new_window_rizero_assign():
		# disable the combo and assign button to prevent multiple clicks
		RiZero_opt_combo.config(state="disable")
		RiZero_assign_button.config(state="disable")

		# Create a new window to get soil depth data
		new_window = tk.Toplevel(root)  
		new_window.title("RiZero Uniform Assignment")
		new_window.geometry("370x110") 
		new_window.resizable(width=True, height=True)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		# layout
		rizero_data_title_label = tk.Label(new_window, text=f"RiZero Uniform", font=("Arial", 12, "bold"), anchor="w", justify="left")
		rizero_data_val_label = tk.Label(new_window, text=f"steady background infiltration (m/s)", font=("Arial", 12), anchor="w", justify="left")
		rizero_data_val_entry = tk.Entry(new_window, width=10, bd=3, font=("Arial", 12), textvariable=rizero_value_double)
		rizero_data_assign_button = tk.Button(new_window, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_rizero_window_toplevel(new_window)) 

		rizero_data_title_label.grid(row=0, column=0, columnspan=4, padx=5, pady=(0,5), sticky="we")
		rizero_data_val_label.grid(row=1, column=0, columnspan=3, padx=5, pady=(0,5), sticky="w")
		rizero_data_val_entry.grid(row=1, column=3, columnspan=1, padx=5, pady=(0,5), sticky="we")
		rizero_data_assign_button.grid(row=2, column=0, columnspan=4, padx=5, pady=(0,5), sticky="we")

		# Call close_soil_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_rizero_window_toplevel(new_window)) 
		new_window.mainloop()

	def open_rizero_data_GIS_file_command(filename_entry=None):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_rizero_data_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select RiZero GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_rizero_data_GIS_file) > 0 and os.path.isfile(selected_rizero_data_GIS_file):

				# only need the filename
				file_path_name = selected_rizero_data_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				rizero_GIS_filename_str.set(file_name_only)

				if filename_entry is not None:
					# delete whatever is written in the file name text output box - so new one can be added
					filename_entry.delete(0, tk.END)
					filename_entry.insert(0, file_name_only)

				# update status 
				status.config(text = "RiZero GIS file loaded ")

		except:
			pass

		return None


	#################################
	# rainfall input
	#################################
	# sub window layout change based on rainfall history option selected
	def rainfall_history_func():
		selected_rainfall_history_option = rainfall_history_opt_str.get()	
		if selected_rainfall_history_option == "Uniform":
			open_new_window_rainfall_uniform()
		elif selected_rainfall_history_option == "GIS file":
			open_new_window_rainfall_GIS()
		elif selected_rainfall_history_option == "Deterministic Rainfall Gauge":
			open_new_window_rainfall_gauge_deter()
		elif selected_rainfall_history_option == "Probabilistic Rainfall Gauge":
			open_new_window_rainfall_gauge_prob()

	# function to prevent multiple windows to open while assigning soil depth data
	def close_rainfall_window_toplevel(sub_window):
		rainfall_history_opt_combo.config(state="normal")  # Enable the combo
		rainfall_history_assign_button.config(state="normal")  # Enable the assign button
		sub_window.destroy()		# close the sub window completely

	# Function to open a new window to assign uniform rainfall data 
	def open_new_window_rainfall_uniform():
		# disable the combo and assign button to prevent multiple clicks
		rainfall_history_opt_combo.config(state="disable")
		rainfall_history_assign_button.config(state="disable")

		# Create a new window to get Rainfall History data
		new_window = tk.Toplevel(root)  
		new_window.title("Rainfall History")
		new_window.geometry("440x700") 
		new_window.resizable(width=False, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		rain_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=rain_data_frame, anchor="nw")

		###############
		# layout
		###############
		# uniform_soil_assign_label
		tk.Label(rain_data_frame, text="Uniform Rainfall", font=("Arial", 12), anchor="w", justify="left").grid(row=0, column=0, columnspan=3, padx=5, pady=(0,5), sticky="w")

		# history row head data
		tk.Label(rain_data_frame, text="Time Step", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="Start Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="End Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="Intensity", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=3, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# time step column head data and entry
		for i in range(1, 101):
			tk.Label(rain_data_frame, text=str(i), font=("Arial", 12), anchor="w", justify="left").grid(row=i+1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][0]).grid(row=i+1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="we")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][1]).grid(row=i+1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="we")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][0]).grid(row=i+1, column=3, columnspan=1, padx=5, pady=(0,5), sticky="we")

		# uniform_rain_assign_button
		tk.Button(rain_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_rainfall_window_toplevel(new_window)).grid(row=0, column=3, columnspan=1, padx=5, pady=5, sticky="we")

		# Call close_rainfall_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_rainfall_window_toplevel(new_window)) 
		new_window.mainloop()


	def open_rainfall_GIS_file_command(time_step, entry_widget):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_rainfall_history_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select rainfall intensity GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd")
		 						)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_rainfall_history_GIS_file) > 0 and os.path.isfile(selected_rainfall_history_GIS_file):

				# only need the filename
				file_path_name = selected_rainfall_history_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				rain_hist_t_dict[time_step][2][1].set(file_name_only)

				# delete whatever is written in the file name text output box - so new one can be added
				entry_widget.delete(0, tk.END)
				entry_widget.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "rainfall GIS file loaded ")

		except:
			pass

		return None


	# Function to open a new window to assign GIS rainfall data 
	def open_new_window_rainfall_GIS():
		# disable the combo and assign button to prevent multiple clicks
		rainfall_history_opt_combo.config(state="disable")
		rainfall_history_assign_button.config(state="disable")

		# Create a new window to get Rainfall History data
		new_window = tk.Toplevel(root)  
		new_window.title("Rainfall History")
		new_window.geometry("640x730") 
		new_window.resizable(width=False, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		rain_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=rain_data_frame, anchor="nw")

		###############
		# layout
		###############
		# uniform_soil_assign_label
		tk.Label(rain_data_frame, text="GIS-based Rainfall", font=("Arial", 12, "bold"), anchor="w", justify="left").grid(row=0, column=0, columnspan=4, padx=5, pady=(0,5), sticky="w")

		# history row head data
		tk.Label(rain_data_frame, text="Time Step", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="Start Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="End Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="GIS", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=3, columnspan=4, padx=5, pady=(0,5), sticky="w")

		# time step column head data and entry
		rain_hist_t_GIS_entry_dict = {}
		for i in range(1, 101):    

			tk.Label(rain_data_frame, text=str(i), font=("Arial", 12), anchor="w", justify="left").grid(row=i+1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][0]).grid(row=i+1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="we")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][1]).grid(row=i+1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="we")
			
			# tk.Entry(rain_data_frame, width=20, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][1]).grid(row=i+1, column=3, columnspan=3, padx=5, pady=(0,5), sticky="we")
			rain_hist_t_GIS_entry_dict[i] = tk.Entry(rain_data_frame, width=20, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][1])
			rain_hist_t_GIS_entry_dict[i].grid(row=i+1, column=3, columnspan=3, padx=5, pady=(0,5), sticky="we")
		
		# add the GIS file selection button
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(1, rain_hist_t_GIS_entry_dict[1])).grid(row=2, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(2, rain_hist_t_GIS_entry_dict[2])).grid(row=3, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(3, rain_hist_t_GIS_entry_dict[3])).grid(row=4, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(4, rain_hist_t_GIS_entry_dict[4])).grid(row=5, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(5, rain_hist_t_GIS_entry_dict[5])).grid(row=6, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(6, rain_hist_t_GIS_entry_dict[6])).grid(row=7, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(7, rain_hist_t_GIS_entry_dict[7])).grid(row=8, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(8, rain_hist_t_GIS_entry_dict[8])).grid(row=9, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(9, rain_hist_t_GIS_entry_dict[9])).grid(row=10, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(10, rain_hist_t_GIS_entry_dict[10])).grid(row=11, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(11, rain_hist_t_GIS_entry_dict[11])).grid(row=12, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(12, rain_hist_t_GIS_entry_dict[12])).grid(row=13, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(13, rain_hist_t_GIS_entry_dict[13])).grid(row=14, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(14, rain_hist_t_GIS_entry_dict[14])).grid(row=15, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(15, rain_hist_t_GIS_entry_dict[15])).grid(row=16, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(16, rain_hist_t_GIS_entry_dict[16])).grid(row=17, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(17, rain_hist_t_GIS_entry_dict[17])).grid(row=18, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(18, rain_hist_t_GIS_entry_dict[18])).grid(row=19, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(19, rain_hist_t_GIS_entry_dict[19])).grid(row=20, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(20, rain_hist_t_GIS_entry_dict[20])).grid(row=21, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(21, rain_hist_t_GIS_entry_dict[21])).grid(row=22, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(22, rain_hist_t_GIS_entry_dict[22])).grid(row=23, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(23, rain_hist_t_GIS_entry_dict[23])).grid(row=24, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(24, rain_hist_t_GIS_entry_dict[24])).grid(row=25, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(25, rain_hist_t_GIS_entry_dict[25])).grid(row=26, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(26, rain_hist_t_GIS_entry_dict[26])).grid(row=27, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(27, rain_hist_t_GIS_entry_dict[27])).grid(row=28, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(28, rain_hist_t_GIS_entry_dict[28])).grid(row=29, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(29, rain_hist_t_GIS_entry_dict[29])).grid(row=30, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(30, rain_hist_t_GIS_entry_dict[30])).grid(row=31, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(31, rain_hist_t_GIS_entry_dict[31])).grid(row=32, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(32, rain_hist_t_GIS_entry_dict[32])).grid(row=33, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(33, rain_hist_t_GIS_entry_dict[33])).grid(row=34, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(34, rain_hist_t_GIS_entry_dict[34])).grid(row=35, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(35, rain_hist_t_GIS_entry_dict[35])).grid(row=36, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(36, rain_hist_t_GIS_entry_dict[36])).grid(row=37, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(37, rain_hist_t_GIS_entry_dict[37])).grid(row=38, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(38, rain_hist_t_GIS_entry_dict[38])).grid(row=39, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(39, rain_hist_t_GIS_entry_dict[39])).grid(row=40, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(40, rain_hist_t_GIS_entry_dict[40])).grid(row=41, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(41, rain_hist_t_GIS_entry_dict[41])).grid(row=42, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(42, rain_hist_t_GIS_entry_dict[42])).grid(row=43, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(43, rain_hist_t_GIS_entry_dict[43])).grid(row=44, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(44, rain_hist_t_GIS_entry_dict[44])).grid(row=45, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(45, rain_hist_t_GIS_entry_dict[45])).grid(row=46, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(46, rain_hist_t_GIS_entry_dict[46])).grid(row=47, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(47, rain_hist_t_GIS_entry_dict[47])).grid(row=48, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(48, rain_hist_t_GIS_entry_dict[48])).grid(row=49, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(49, rain_hist_t_GIS_entry_dict[49])).grid(row=50, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(50, rain_hist_t_GIS_entry_dict[50])).grid(row=51, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(51, rain_hist_t_GIS_entry_dict[51])).grid(row=52, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(52, rain_hist_t_GIS_entry_dict[52])).grid(row=53, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(53, rain_hist_t_GIS_entry_dict[53])).grid(row=54, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(54, rain_hist_t_GIS_entry_dict[54])).grid(row=55, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(55, rain_hist_t_GIS_entry_dict[55])).grid(row=56, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(56, rain_hist_t_GIS_entry_dict[56])).grid(row=57, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(57, rain_hist_t_GIS_entry_dict[57])).grid(row=58, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(58, rain_hist_t_GIS_entry_dict[58])).grid(row=59, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(59, rain_hist_t_GIS_entry_dict[59])).grid(row=60, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(60, rain_hist_t_GIS_entry_dict[60])).grid(row=61, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(61, rain_hist_t_GIS_entry_dict[61])).grid(row=62, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(62, rain_hist_t_GIS_entry_dict[62])).grid(row=63, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(63, rain_hist_t_GIS_entry_dict[63])).grid(row=64, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(64, rain_hist_t_GIS_entry_dict[64])).grid(row=65, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(65, rain_hist_t_GIS_entry_dict[65])).grid(row=66, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(66, rain_hist_t_GIS_entry_dict[66])).grid(row=67, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(67, rain_hist_t_GIS_entry_dict[67])).grid(row=68, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(68, rain_hist_t_GIS_entry_dict[68])).grid(row=69, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(69, rain_hist_t_GIS_entry_dict[69])).grid(row=70, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(70, rain_hist_t_GIS_entry_dict[70])).grid(row=71, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(71, rain_hist_t_GIS_entry_dict[71])).grid(row=72, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(72, rain_hist_t_GIS_entry_dict[72])).grid(row=73, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(73, rain_hist_t_GIS_entry_dict[73])).grid(row=74, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(74, rain_hist_t_GIS_entry_dict[74])).grid(row=75, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(75, rain_hist_t_GIS_entry_dict[75])).grid(row=76, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(76, rain_hist_t_GIS_entry_dict[76])).grid(row=77, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(77, rain_hist_t_GIS_entry_dict[77])).grid(row=78, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(78, rain_hist_t_GIS_entry_dict[78])).grid(row=79, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(79, rain_hist_t_GIS_entry_dict[79])).grid(row=80, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(80, rain_hist_t_GIS_entry_dict[80])).grid(row=81, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(81, rain_hist_t_GIS_entry_dict[81])).grid(row=82, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(82, rain_hist_t_GIS_entry_dict[82])).grid(row=83, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(83, rain_hist_t_GIS_entry_dict[83])).grid(row=84, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(84, rain_hist_t_GIS_entry_dict[84])).grid(row=85, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(85, rain_hist_t_GIS_entry_dict[85])).grid(row=86, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(86, rain_hist_t_GIS_entry_dict[86])).grid(row=87, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(87, rain_hist_t_GIS_entry_dict[87])).grid(row=88, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(88, rain_hist_t_GIS_entry_dict[88])).grid(row=89, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(89, rain_hist_t_GIS_entry_dict[89])).grid(row=90, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(90, rain_hist_t_GIS_entry_dict[90])).grid(row=91, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(91, rain_hist_t_GIS_entry_dict[91])).grid(row=92, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(92, rain_hist_t_GIS_entry_dict[92])).grid(row=93, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(93, rain_hist_t_GIS_entry_dict[93])).grid(row=94, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(94, rain_hist_t_GIS_entry_dict[94])).grid(row=95, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(95, rain_hist_t_GIS_entry_dict[95])).grid(row=96, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(96, rain_hist_t_GIS_entry_dict[96])).grid(row=97, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(97, rain_hist_t_GIS_entry_dict[97])).grid(row=98, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(98, rain_hist_t_GIS_entry_dict[98])).grid(row=99, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(99, rain_hist_t_GIS_entry_dict[99])).grid(row=100, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(100, rain_hist_t_GIS_entry_dict[100])).grid(row=101, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(101, rain_hist_t_GIS_entry_dict[101])).grid(row=102, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(102, rain_hist_t_GIS_entry_dict[102])).grid(row=103, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(103, rain_hist_t_GIS_entry_dict[103])).grid(row=104, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(104, rain_hist_t_GIS_entry_dict[104])).grid(row=105, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(105, rain_hist_t_GIS_entry_dict[105])).grid(row=106, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(106, rain_hist_t_GIS_entry_dict[106])).grid(row=107, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(107, rain_hist_t_GIS_entry_dict[107])).grid(row=108, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(108, rain_hist_t_GIS_entry_dict[108])).grid(row=109, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(109, rain_hist_t_GIS_entry_dict[109])).grid(row=110, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(110, rain_hist_t_GIS_entry_dict[110])).grid(row=111, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(111, rain_hist_t_GIS_entry_dict[111])).grid(row=112, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(112, rain_hist_t_GIS_entry_dict[112])).grid(row=113, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(113, rain_hist_t_GIS_entry_dict[113])).grid(row=114, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(114, rain_hist_t_GIS_entry_dict[114])).grid(row=115, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(115, rain_hist_t_GIS_entry_dict[115])).grid(row=116, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(116, rain_hist_t_GIS_entry_dict[116])).grid(row=117, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(117, rain_hist_t_GIS_entry_dict[117])).grid(row=118, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(118, rain_hist_t_GIS_entry_dict[118])).grid(row=119, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(119, rain_hist_t_GIS_entry_dict[119])).grid(row=120, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(120, rain_hist_t_GIS_entry_dict[120])).grid(row=121, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(121, rain_hist_t_GIS_entry_dict[121])).grid(row=122, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(122, rain_hist_t_GIS_entry_dict[122])).grid(row=123, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(123, rain_hist_t_GIS_entry_dict[123])).grid(row=124, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(124, rain_hist_t_GIS_entry_dict[124])).grid(row=125, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(125, rain_hist_t_GIS_entry_dict[125])).grid(row=126, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(126, rain_hist_t_GIS_entry_dict[126])).grid(row=127, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(127, rain_hist_t_GIS_entry_dict[127])).grid(row=128, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(128, rain_hist_t_GIS_entry_dict[128])).grid(row=129, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(129, rain_hist_t_GIS_entry_dict[129])).grid(row=130, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(130, rain_hist_t_GIS_entry_dict[130])).grid(row=131, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(131, rain_hist_t_GIS_entry_dict[131])).grid(row=132, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(132, rain_hist_t_GIS_entry_dict[132])).grid(row=133, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(133, rain_hist_t_GIS_entry_dict[133])).grid(row=134, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(134, rain_hist_t_GIS_entry_dict[134])).grid(row=135, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(135, rain_hist_t_GIS_entry_dict[135])).grid(row=136, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(136, rain_hist_t_GIS_entry_dict[136])).grid(row=137, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(137, rain_hist_t_GIS_entry_dict[137])).grid(row=138, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(138, rain_hist_t_GIS_entry_dict[138])).grid(row=139, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(139, rain_hist_t_GIS_entry_dict[139])).grid(row=140, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(140, rain_hist_t_GIS_entry_dict[140])).grid(row=141, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(141, rain_hist_t_GIS_entry_dict[141])).grid(row=142, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(142, rain_hist_t_GIS_entry_dict[142])).grid(row=143, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(143, rain_hist_t_GIS_entry_dict[143])).grid(row=144, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(144, rain_hist_t_GIS_entry_dict[144])).grid(row=145, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(145, rain_hist_t_GIS_entry_dict[145])).grid(row=146, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(146, rain_hist_t_GIS_entry_dict[146])).grid(row=147, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(147, rain_hist_t_GIS_entry_dict[147])).grid(row=148, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(148, rain_hist_t_GIS_entry_dict[148])).grid(row=149, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(149, rain_hist_t_GIS_entry_dict[149])).grid(row=150, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(150, rain_hist_t_GIS_entry_dict[150])).grid(row=151, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(151, rain_hist_t_GIS_entry_dict[151])).grid(row=152, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(152, rain_hist_t_GIS_entry_dict[152])).grid(row=153, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(153, rain_hist_t_GIS_entry_dict[153])).grid(row=154, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(154, rain_hist_t_GIS_entry_dict[154])).grid(row=155, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(155, rain_hist_t_GIS_entry_dict[155])).grid(row=156, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(156, rain_hist_t_GIS_entry_dict[156])).grid(row=157, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(157, rain_hist_t_GIS_entry_dict[157])).grid(row=158, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(158, rain_hist_t_GIS_entry_dict[158])).grid(row=159, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(159, rain_hist_t_GIS_entry_dict[159])).grid(row=160, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(160, rain_hist_t_GIS_entry_dict[160])).grid(row=161, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(161, rain_hist_t_GIS_entry_dict[161])).grid(row=162, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(162, rain_hist_t_GIS_entry_dict[162])).grid(row=163, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(163, rain_hist_t_GIS_entry_dict[163])).grid(row=164, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(164, rain_hist_t_GIS_entry_dict[164])).grid(row=165, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(165, rain_hist_t_GIS_entry_dict[165])).grid(row=166, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(166, rain_hist_t_GIS_entry_dict[166])).grid(row=167, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(167, rain_hist_t_GIS_entry_dict[167])).grid(row=168, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(168, rain_hist_t_GIS_entry_dict[168])).grid(row=169, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(169, rain_hist_t_GIS_entry_dict[169])).grid(row=170, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(170, rain_hist_t_GIS_entry_dict[170])).grid(row=171, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(171, rain_hist_t_GIS_entry_dict[171])).grid(row=172, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(172, rain_hist_t_GIS_entry_dict[172])).grid(row=173, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(173, rain_hist_t_GIS_entry_dict[173])).grid(row=174, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(174, rain_hist_t_GIS_entry_dict[174])).grid(row=175, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(175, rain_hist_t_GIS_entry_dict[175])).grid(row=176, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(176, rain_hist_t_GIS_entry_dict[176])).grid(row=177, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(177, rain_hist_t_GIS_entry_dict[177])).grid(row=178, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(178, rain_hist_t_GIS_entry_dict[178])).grid(row=179, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(179, rain_hist_t_GIS_entry_dict[179])).grid(row=180, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(180, rain_hist_t_GIS_entry_dict[180])).grid(row=181, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(181, rain_hist_t_GIS_entry_dict[181])).grid(row=182, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(182, rain_hist_t_GIS_entry_dict[182])).grid(row=183, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(183, rain_hist_t_GIS_entry_dict[183])).grid(row=184, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(184, rain_hist_t_GIS_entry_dict[184])).grid(row=185, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(185, rain_hist_t_GIS_entry_dict[185])).grid(row=186, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(186, rain_hist_t_GIS_entry_dict[186])).grid(row=187, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(187, rain_hist_t_GIS_entry_dict[187])).grid(row=188, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(188, rain_hist_t_GIS_entry_dict[188])).grid(row=189, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(189, rain_hist_t_GIS_entry_dict[189])).grid(row=190, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(190, rain_hist_t_GIS_entry_dict[190])).grid(row=191, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(191, rain_hist_t_GIS_entry_dict[191])).grid(row=192, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(192, rain_hist_t_GIS_entry_dict[192])).grid(row=193, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(193, rain_hist_t_GIS_entry_dict[193])).grid(row=194, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(194, rain_hist_t_GIS_entry_dict[194])).grid(row=195, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(195, rain_hist_t_GIS_entry_dict[195])).grid(row=196, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(196, rain_hist_t_GIS_entry_dict[196])).grid(row=197, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(197, rain_hist_t_GIS_entry_dict[197])).grid(row=198, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(198, rain_hist_t_GIS_entry_dict[198])).grid(row=199, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(199, rain_hist_t_GIS_entry_dict[199])).grid(row=200, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		# tk.Button(rain_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_rainfall_GIS_file_command(200, rain_hist_t_GIS_entry_dict[200])).grid(row=201, column=6, columnspan=1, padx=5, pady=5, sticky="we")
	
		
		# uniform_rain_assign_button
		tk.Button(rain_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_rainfall_window_toplevel(new_window)).grid(row=0, column=6, columnspan=1, padx=5, pady=5, sticky="we")

		# Call close_rainfall_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_rainfall_window_toplevel(new_window)) 
		new_window.mainloop()


	# Function to open a new window to assign deterministic nearest neighbor rainfall gauge data
	def open_new_window_rainfall_gauge_deter():
		# disable the combo and assign button to prevent multiple clicks
		rainfall_history_opt_combo.config(state="disable")
		rainfall_history_assign_button.config(state="disable")

		# Create a new window to get Rainfall History data
		new_window = tk.Toplevel(root)  
		new_window.title("Rainfall History")
		new_window.geometry("640x730") 
		new_window.resizable(width=True, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## horizontal scroll bar
		hor_scroll_bar = tk.Scrollbar(new_window, orient='horizontal', command=main_canvas.xview)
		hor_scroll_bar.pack(side='bottom', fill='x')
		main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		rain_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=rain_data_frame, anchor="nw")

		###############
		# layout
		###############
		# uniform_soil_assign_label
		tk.Label(rain_data_frame, text="Deterministic Rain Gauge", font=("Arial", 12), anchor="w", justify="left").grid(row=0, column=0, columnspan=3, padx=5, pady=(0,5), sticky="w")

		# history row head data
		tk.Label(rain_data_frame, text="Time Step", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="Start Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="End Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# rain gauge (max 5)
		for j in range(5):
			tk.Label(rain_data_frame, text=f"{j+1}: X (m)", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=3+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: Y (m)", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=4+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: I", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=5+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# time step column head data and entry
		for i in range(1, 101):
			tk.Label(rain_data_frame, text=str(i), font=("Arial", 12), anchor="w", justify="left").grid(row=i+1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][0]).grid(row=i+1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="we")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][1]).grid(row=i+1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="we")

			for j in range(5):
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][0]).grid(row=i+1, column=3+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")  # X
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][1]).grid(row=i+1, column=4+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Y
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][2]).grid(row=i+1, column=5+j*3, columnspan=1, padx=5, pady=(0,5), sticky="w")  # I

		# assign_button
		tk.Button(rain_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_rainfall_window_toplevel(new_window)).grid(row=0, column=3, columnspan=1, padx=5, pady=5, sticky="we")

		# Call close_rainfall_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_rainfall_window_toplevel(new_window)) 
		new_window.mainloop()

	# Function to open a new window to assign probabilistic nearest neighbor rainfall gauge data
	def open_new_window_rainfall_gauge_prob():
		# disable the combo and assign button to prevent multiple clicks
		rainfall_history_opt_combo.config(state="disable")
		rainfall_history_assign_button.config(state="disable")

		# Create a new window to get Rainfall History data
		new_window = tk.Toplevel(root)  
		new_window.title("Rainfall History")
		new_window.geometry("640x730") 
		new_window.resizable(width=True, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## horizontal scroll bar
		hor_scroll_bar = tk.Scrollbar(new_window, orient='horizontal', command=main_canvas.xview)
		hor_scroll_bar.pack(side='bottom', fill='x')
		main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		rain_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=rain_data_frame, anchor="nw")

		###############
		# layout
		###############
		# uniform_soil_assign_label
		tk.Label(rain_data_frame, text="Probabilistic Rain Gauge", font=("Arial", 12), anchor="w", justify="left").grid(row=0, column=0, columnspan=3, padx=5, pady=(0,5), sticky="w")

		# history row head data
		tk.Label(rain_data_frame, text="Time Step", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="Start Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="w")
		tk.Label(rain_data_frame, text="End Time", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# rain gauge (max 5)
		for j in range(5):
			tk.Label(rain_data_frame, text=f"{j+1}: X (m)", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=3+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: Y (m)", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=4+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: mean I", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=5+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: CoV", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=6+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: P. Dist.", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=7+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: CorLenX", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=8+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: CorLenY", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=9+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: Min", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=10+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Label(rain_data_frame, text=f"{j+1}: Max", font=("Arial", 12), anchor="w", justify="left").grid(row=1, column=11+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# time step column head data and entry
		for i in range(1, 101):
			tk.Label(rain_data_frame, text=str(i), font=("Arial", 12), anchor="w", justify="left").grid(row=i+1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][0]).grid(row=i+1, column=1, columnspan=1, padx=5, pady=(0,5), sticky="we")
			tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][1]).grid(row=i+1, column=2, columnspan=1, padx=5, pady=(0,5), sticky="we")

			for j in range(5):
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][0]).grid(row=i+1, column=3+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # X
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][1]).grid(row=i+1, column=4+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Y
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][2]).grid(row=i+1, column=5+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # I
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][3]).grid(row=i+1, column=6+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # CoV
	
				# probabilistic distribution		
				prob_dist_combo = ttk.Combobox(
						rain_data_frame,
						state="readonly",
						values=["N", "LN"],
						textvariable=rain_hist_t_dict[i][2][2][j][4],
						width=10,
						font=("Arial", 12)
					)
				prob_dist_combo.current(0)  # set default value to "N"
				prob_dist_combo.grid(row=i+1, column=7+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # prob dist.
	
				# tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][5]).grid(row=i+1, column=8+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Corr. Length X
				# tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][6]).grid(row=i+1, column=9+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Corr. Length Y

				cor_len_x_combo = ttk.Combobox(
						rain_data_frame,
						state="normal",
						values=["inf"],
						textvariable=rain_hist_t_dict[i][2][2][j][5],
						width=10,
						font=("Arial", 12)
					)
				cor_len_x_combo.grid(row=i+1, column=8+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
	
				cor_len_y_combo = ttk.Combobox(
						rain_data_frame,
						state="normal",
						values=["inf"],
						textvariable=rain_hist_t_dict[i][2][2][j][6],
						width=10,
						font=("Arial", 12)
					)
				cor_len_y_combo.grid(row=i+1, column=9+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")
	
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][7]).grid(row=i+1, column=10+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Min
				tk.Entry(rain_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=rain_hist_t_dict[i][2][2][j][8]).grid(row=i+1, column=11+j*9, columnspan=1, padx=5, pady=(0,5), sticky="w")  # Max

		# assign_button
		tk.Button(rain_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_rainfall_window_toplevel(new_window)).grid(row=0, column=3, columnspan=1, padx=5, pady=5, sticky="we")

		# Call close_rainfall_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_rainfall_window_toplevel(new_window)) 
		new_window.mainloop()


	# disable assigning Green-Ampt model if Iverson model is selected
	def infil_model_func(*args): 
		if infil_model_str.get() == "Green-Ampt":
			SWCC_model_combo.config(state="readonly")
			surf_dip_for_GA_checkbutton.config(state="normal")

			unit_weight_water_double.set(9.81) 
			unit_weight_water_entry.config(state="normal")

		elif infil_model_str.get() == "Iverson":
			SWCC_model_combo.config(state="disable")
			surf_dip_for_GA_checkbutton.config(state="disable")

			"""NOTE by ECo: Perhaps add option to allow change of water unit weight in Iverson"""
			unit_weight_water_double.set(10.0)
			unit_weight_water_entry.config(state="disable")


	#################################
	# slope stability
	#################################
	def slope_model_func(*args):
		if slope_model_str.get() == "Skip (only perform infiltration)":
			# disable 3DTS options
			min_cell_3DTS_entry.config(state="disable")
			max_cell_3DTS_entry.config(state="disable")
			superellipse_power_3DTS_entry.config(state="disable")
			superellipse_eccen_ratio_3DTS_entry.config(state="disable")
			side_resistance_3DTS_checkbutton.config(state="disable")
			root_reinforced_model_combo.config(state="disable")

			# disable 3DPLS options
			analysis_opt_3DPLS_combo.config(state="disable")
			ellipsoidal_slip_surface_a_entry.config(state="disable")
			ellipsoidal_slip_surface_b_entry.config(state="disable")
			ellipsoidal_slip_surface_c_entry.config(state="disable")
			ellipsoidal_slip_surface_z_entry.config(state="disable")
			ellipsoidal_slip_surface_alpha_comp_checkbutton.config(state="disable")
			ellipsoidal_slip_surface_alpha_entry.config(state="disable")
			ellipsoidal_slip_surface_min_sub_div_entry.config(state="disable")

			# side and root resistance model
			side_resistance_3DTS_int.set(0)
			root_reinforced_model_str.set("None")

			# multiprocessing 
			max_CPU_pool_entry.config(state="normal")
			# multi_CPU_method_combo.config(state="disable")
			# MP_1st_CPU_pool_entry.config(state="disable")
			# MP_2nd_CPU_pool_entry.config(state="disable")
			# MT_2nd_CPU_pool_entry.config(state="disable")

		elif slope_model_str.get() == "Infinite Slope":
			# disable 3DTS options
			min_cell_3DTS_entry.config(state="disable")
			max_cell_3DTS_entry.config(state="disable")
			superellipse_power_3DTS_entry.config(state="disable")
			superellipse_eccen_ratio_3DTS_entry.config(state="disable")
			side_resistance_3DTS_checkbutton.config(state="disable")
			root_reinforced_model_combo.config(state="disable")

			# disable 3DPLS options
			analysis_opt_3DPLS_combo.config(state="disable")
			ellipsoidal_slip_surface_a_entry.config(state="disable")
			ellipsoidal_slip_surface_b_entry.config(state="disable")
			ellipsoidal_slip_surface_c_entry.config(state="disable")
			ellipsoidal_slip_surface_z_entry.config(state="disable")
			ellipsoidal_slip_surface_alpha_comp_checkbutton.config(state="disable")
			ellipsoidal_slip_surface_alpha_entry.config(state="disable")
			ellipsoidal_slip_surface_min_sub_div_entry.config(state="disable")

			# side and root resistance model
			side_resistance_3DTS_int.set(0)
			root_reinforced_model_str.set("None")

			# multiprocessing 
			multi_CPU_method_opt_int.set(1)
			max_CPU_pool_entry.config(state="normal")

			# multi_CPU_method_str.set("Pool")
			# multi_CPU_method_combo.config(state="disable")
			# max_CPU_pool_entry.config(state="normal")
			# MP_1st_CPU_pool_entry.config(state="disable")
			# MP_2nd_CPU_pool_entry.config(state="disable")
			# MT_2nd_CPU_pool_entry.config(state="disable")

			# rainfall history
			rainfall_history_opt_str.set("Uniform")
			rainfall_history_opt_combo.config(state="normal")

			# hydrological model
			infil_model_str.set("Green-Ampt")
			infil_model_combo.config(state="disable")
			SWCC_model_combo.config(state="normal")
			unit_weight_water_double.set(9.81) 
			unit_weight_water_entry.config(state="normal")

			# probabilistic
			random_field_method_str.set("SCMD")
			random_field_method_combo.config(state="disable") 

		elif slope_model_str.get() == "3D Translational Slide (3DTS)":
			# disable 3DTS options
			min_cell_3DTS_entry.config(state="normal")
			max_cell_3DTS_entry.config(state="normal")
			superellipse_power_3DTS_entry.config(state="normal")
			superellipse_eccen_ratio_3DTS_entry.config(state="normal")
			side_resistance_3DTS_checkbutton.config(state="normal")
			root_reinforced_model_combo.config(state="readonly")

			# disable 3DPLS options
			analysis_opt_3DPLS_combo.config(state="disable")
			ellipsoidal_slip_surface_a_entry.config(state="disable")
			ellipsoidal_slip_surface_b_entry.config(state="disable")
			ellipsoidal_slip_surface_c_entry.config(state="disable")
			ellipsoidal_slip_surface_z_entry.config(state="disable")
			ellipsoidal_slip_surface_alpha_comp_checkbutton.config(state="disable")
			ellipsoidal_slip_surface_alpha_entry.config(state="disable")
			ellipsoidal_slip_surface_min_sub_div_entry.config(state="disable")

			# side and root resistance model
			side_resistance_3DTS_int.set(1)
			root_reinforced_model_str.set("None")

			# multiprocessing 
			multi_CPU_method_opt_int.set(1)
			max_CPU_pool_entry.config(state="normal")

			# multi_CPU_method_str.set("Pool")
			# multi_CPU_method_combo.config(state="disable")
			# max_CPU_pool_entry.config(state="normal")
			# MP_1st_CPU_pool_entry.config(state="disable")
			# MP_2nd_CPU_pool_entry.config(state="disable")
			# MT_2nd_CPU_pool_entry.config(state="disable")

			# rainfall history
			rainfall_history_opt_str.set("Uniform")
			rainfall_history_opt_combo.config(state="normal")

			# hydrological model
			infil_model_str.set("Green-Ampt")
			infil_model_combo.config(state="disable")
			SWCC_model_combo.config(state="normal")
			unit_weight_water_double.set(9.81) 
			unit_weight_water_entry.config(state="normal")

			# probabilistic
			random_field_method_str.set("SCMD")
			random_field_method_combo.config(state="disable") 

		elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]:
			# disable 3DTS options
			min_cell_3DTS_entry.config(state="disable")
			max_cell_3DTS_entry.config(state="disable")
			superellipse_power_3DTS_entry.config(state="disable")
			superellipse_eccen_ratio_3DTS_entry.config(state="disable")
			side_resistance_3DTS_checkbutton.config(state="disable")
			root_reinforced_model_str.set("None")
			root_reinforced_model_combo.config(state="disable")

			# enable 3DPLS options
			analysis_opt_3DPLS_combo.config(state="normal")
			ellipsoidal_slip_surface_a_entry.config(state="normal")
			ellipsoidal_slip_surface_b_entry.config(state="normal")
			ellipsoidal_slip_surface_c_entry.config(state="normal")
			ellipsoidal_slip_surface_z_entry.config(state="normal")
			ellipsoidal_slip_surface_alpha_comp_checkbutton.config(state="normal")
			ellipsoidal_slip_surface_min_sub_div_entry.config(state="normal")
			# ellipsoidal_slip_surface_alpha_entry.config(state="normal")

			# side and root resistance model
			side_resistance_3DTS_int.set(0)
			root_reinforced_model_str.set("None")

			# multiprocessing 
			multi_CPU_method_opt_int.set(1)
			max_CPU_pool_entry.config(state="normal")

			# multi_CPU_method_str.set("S-MP-MP")
			# multi_CPU_method_combo.config(state="normal")
			# max_CPU_pool_entry.config(state="disable")
			# MP_1st_CPU_pool_entry.config(state="normal")
			# MP_2nd_CPU_pool_entry.config(state="normal")
			# MT_2nd_CPU_pool_entry.config(state="normal")

			# rainfall history
			rainfall_history_opt_str.set("Uniform")
			rainfall_history_opt_combo.config(state="disable")

			# hydrological model
			infil_model_str.set("Iverson")
			infil_model_combo.config(state="disable")
			SWCC_model_combo.config(state="disable")
			unit_weight_water_double.set(10.0) 
			unit_weight_water_entry.config(state="disable")

			# probabilistic
			random_field_method_str.set("SCMD")
			random_field_method_combo.config(state="normal") 

	#################################
	# debris flow criteria
	#################################
	def debris_flow_criteria_func(*args):
		if debris_flow_criteria_int.get() == 1:  # selected
			debris_flow_criteria_network_buttom.config(state="normal")
			debris_flow_criteria_UCA_buttom.config(state="normal")
			debris_flow_criteria_Criteria_buttom.config(state="normal")
		elif debris_flow_criteria_int.get() == 0:  # not considered
			debris_flow_criteria_network_buttom.config(state="disable")
			debris_flow_criteria_UCA_buttom.config(state="disable")
			debris_flow_criteria_Criteria_buttom.config(state="disable")

	def open_DFC_network_file_command(): 
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_debris_flow_criteria_network_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select neighbor directed network graph based on DEM",
								filetypes=(
									("numpy zip (npz)", "*.npz"),
								)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_debris_flow_criteria_network_file) > 0 and os.path.isfile(selected_debris_flow_criteria_network_file):

				# only need the filename
				file_path_name = selected_debris_flow_criteria_network_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				debris_flow_criteria_network_str.delete(0, tk.END)
				debris_flow_criteria_network_str.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "DEM-based neighbor directed network graph file loaded ")

		except:
			pass

		return None

	def open_DFC_UCA_file_command(): 
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_UCA_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select UCA GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_UCA_GIS_file) > 0 and os.path.isfile(selected_UCA_GIS_file):

				# only need the filename
				file_path_name = selected_UCA_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				debris_flow_criteria_UCA_str.delete(0, tk.END)
				debris_flow_criteria_UCA_str.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "UCA GIS file loaded ")

		except:
			pass

		return None

	def open_DFC_Criteria_file_command(): 
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_debris_flow_criteria_Criteria_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select Debris Flow Criteria GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_debris_flow_criteria_Criteria_GIS_file) > 0 and os.path.isfile(selected_debris_flow_criteria_Criteria_GIS_file):

				# only need the filename
				file_path_name = selected_debris_flow_criteria_Criteria_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				debris_flow_criteria_Criteria_str.delete(0, tk.END)
				debris_flow_criteria_Criteria_str.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "initial groundwater / RiZero GIS file loaded ")

		except:
			pass

		return None

	#################################
	# material assignment
	#################################
	def open_mat_zone_file_command(entry_widget):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'
		
		# load directory
		selected_mat_zone_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select Material Zone GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_mat_zone_GIS_file) > 0 and os.path.isfile(selected_mat_zone_GIS_file):

				# only need the filename
				file_path_name = selected_mat_zone_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				mat_zone_filename_str.set(file_name_only)

				# delete whatever is written in the file name text output box - so new one can be added
				entry_widget.delete(0, tk.END)
				entry_widget.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "Material Zone ID GIS file loaded ")

		except:
			pass

		return None


	# select which type of new window to open
	def mat_assign_func():
		if mat_assign_opt_str.get() in ["Uniform", "Zone-Based"] and mc_iterations_int.get() == 1:
			mat_assign_deter_new_window()
		elif mat_assign_opt_str.get() in ["Uniform", "Zone-Based"]  and mc_iterations_int.get() > 1:
			mat_assign_prob_new_window()
		elif mat_assign_opt_str.get() == "GIS files" and slope_model_str.get() not in ["3D Normal", "3D Bishop", "3D Janbu"]:
			open_new_window_material_GIS()

	# function to prevent multiple windows to open while assigning soil depth data
	def close_mat_window_toplevel(sub_window):
		mat_assign_opt_combo.config(state="normal")  # Enable the combo
		num_mat_combo.config(state="normal")  # Enable the combo
		root_reinforced_model_combo.config(state="normal")  # Enable the combo
		SWCC_model_combo.config(state="normal")  # Enable the combo
		mat_assign_button.config(state="normal")  # Enable the assign button
		mc_iterations_entry.config(state="normal")  # Enable the assign button
		random_field_method_combo.config(state="normal")  # Enable the combo
		random_field_save_checkbutton.config(state="normal")  # Enable the checkbutton
		sub_window.destroy()		# close the sub window completely

	# Function to open a new window to assign deterministic material assignment
	def mat_assign_deter_new_window():
		# disable the combo and assign button to prevent multiple clicks
		mat_assign_opt_combo.config(state="disable")
		num_mat_combo.config(state="disable")
		root_reinforced_model_combo.config(state="disable")
		SWCC_model_combo.config(state="disable")
		mc_iterations_entry.config(state="disable")
		mat_assign_button.config(state="disable")
		random_field_method_combo.config(state="disable")
		random_field_save_checkbutton.config(state="disable")  

		# Create a new window to get material properties data
		new_window = tk.Toplevel(root)  
		new_window.title("Material")
		new_window.geometry("800x500") 
		new_window.resizable(width=True, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## horizontal scroll bar
		hor_scroll_bar = tk.Scrollbar(new_window, orient='horizontal', command=main_canvas.xview)
		hor_scroll_bar.pack(side='bottom', fill='x')
		main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		mat_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=mat_data_frame, anchor="nw")

		##############################
		# meta layout
		##############################
		if mat_assign_opt_str.get() == "Uniform":
			num_mat_int.set(1)  # set to 1 if uniform assignment is selected
		elif mat_assign_opt_str.get() == "Zone-Based" and num_mat_int.get() < 2:	
			num_mat_int.set(2)  # set to 2 since at least 2 zones are expected

		tk.Label(mat_data_frame, text=f"{mat_assign_opt_str.get()} Deterministic Material Properties: {num_mat_int.get()} soil zones", font=("Arial", 14, "bold"), anchor="w", justify="left").grid(row=0, column=0, columnspan=10, padx=5, pady=(0,5), sticky="w")
   		
		##############################
		# material ID zone file
		##############################
		# surface topography dip direction file name
		mat_zone_filename_label = tk.Label(mat_data_frame, text="Material Zones", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
		mat_zone_filename_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_zone_filename_str)
		mat_zone_filename_button = tk.Button(mat_data_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_zone_file_command(mat_zone_filename_entry)) 

		mat_zone_filename_label.grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		mat_zone_filename_button.grid(row=1, column=1, columnspan=1, padx=5, pady=5)
		mat_zone_filename_entry.grid(row=1, column=2, columnspan=4, padx=5, pady=5, sticky="we")

		if mat_assign_opt_str.get() == "Uniform" or num_mat_int.get() == 1: 
			mat_zone_filename_entry.config(state="disable")
			mat_zone_filename_button.config(state="disable")

		##############################
		# material ID column
		##############################
		tk.Label(mat_data_frame, text="Mat ID", font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# material ID (max 10)
		for j in range(1, 11):
			tk.Label(mat_data_frame, text=f"{j}", font=("Arial", 12), anchor="w", justify="left").grid(row=2+j, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
  
		##############################
		# 1st column heading data
		##############################
		column_headings = [u"K\u209B (m/s)", u'\u03B8\u1D62', 'SWCC_model', 'a (kPa)', 'n', 'm', u'\u03B8\u209B', u'\u03B8\u1D63', u'm\u1D65', 'S_max (m)', u'D (m\u00B2/s)', u'\u0263\u209B (kN/m\u00B3)', u'\u0278\' (\u00B0)', u'\u0278_b (\u00B0)', u'c\' (kPa)', 'root_model', u'\u0263\u1D63 (kN/m\u00B3)', 'c_base (kPa)', 'c_side (kPa)', 'root_depth (m)', u'\u02512', u'\u03B22', 'RR_max (kN/m)']
		mat_data_dict_keys = ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity", "soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c", "root_model", "root_unit_weight",  "root_c_base", "root_c_side", "root_root_depth", "root_alpha2", "root_beta2", "root_RR_max"]

		############
		## deterministic
		############
		for i, heading in enumerate(column_headings):
			tk.Label(mat_data_frame, text=heading, font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=i+1, columnspan=1, padx=5, pady=(0,5), sticky="w")  

		for j in range(1, 11):
			for i,mat_key in enumerate(mat_data_dict_keys):
				if mat_key in ["hydraulic_SWCC_model", "root_model"]:
					model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key])
					if mat_key == "hydraulic_SWCC_model":
						if infil_model_str.get() == "Iverson":
							mat_data_dict[j][mat_key].set("Iverson")
						else:
							mat_data_dict[j][mat_key].set(SWCC_model_str.get())
					elif mat_key == "root_model":
						mat_data_dict[j][mat_key].set(root_reinforced_model_str.get()) 
					model_entry.grid(row=j+2, column=i+1, columnspan=1, padx=5, pady=(0,5), sticky="we") 
					model_entry.config(state="disable")
				
				elif mat_key in ["root_unit_weight", "root_c_base", "root_c_side", "root_root_depth", "root_alpha2", "root_beta2", "root_RR_max"]:
					model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key][0])
					model_entry.grid(row=j+2, column=i+1, columnspan=1, padx=5, pady=(0,5), sticky="we") 

					if root_reinforced_model_str.get() == "None" or slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Normal", "3D Bishop", "3D Janbu"] or j > num_mat_int.get():
						model_entry.config(state="disable")
					elif mat_key in ["root_alpha2", "root_beta2", "root_RR_max"] and (root_reinforced_model_str.get() == "Constant with Depth" or j > num_mat_int.get()):
						model_entry.config(state="disable")
					elif mat_key in ["root_c_base", "root_c_side", "root_root_depth"] and (root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)" or j > num_mat_int.get()):
						model_entry.config(state="disable")
	   
				else:
					model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key][0])
					model_entry.grid(row=j+2, column=i+1, columnspan=1, padx=5, pady=(0,5), sticky="we") 
					if j > num_mat_int.get():
						model_entry.config(state="disable")
					
					# disable and enable Hydraulic 
					elif j <= num_mat_int.get() and mat_key in ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity"]:
						if (infil_model_str.get() == "Iverson" or slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]) and mat_key not in ["hydraulic_k_sat", "hydraulic_diffusivity"]:
							model_entry.config(state="disable")
						elif infil_model_str.get() == "Green-Ampt" and mat_key in ["hydraulic_diffusivity"]:
							model_entry.config(state="disable")
					
					# disable and enable Soil properties
					elif j <= num_mat_int.get() and mat_key in ["soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c"]:
						if slope_model_str.get() == "Skip (only perform infiltration)":
							model_entry.config(state="disable")
						elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"] and mat_key == "soil_phi_b":
							model_entry.config(state="disable")


		# assign_button
		tk.Button(mat_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_mat_window_toplevel(new_window)).grid(row=13, column=0, columnspan=2, padx=5, pady=5, sticky="we")

		# Call close_mat_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_mat_window_toplevel(new_window)) 
		new_window.mainloop()

	# Function to open a new window to assign probabilistic material assignment
	def mat_assign_prob_new_window():
		# disable the combo and assign button to prevent multiple clicks
		mat_assign_opt_combo.config(state="disable")
		num_mat_combo.config(state="disable")
		root_reinforced_model_combo.config(state="disable")
		SWCC_model_combo.config(state="disable")
		mc_iterations_entry.config(state="disable")
		mat_assign_button.config(state="disable")
		random_field_method_combo.config(state="disable")  
		random_field_save_checkbutton.config(state="disable") 

		# Create a new window to get material properties data
		new_window = tk.Toplevel(root)  
		new_window.title("Material")
		new_window.geometry("1000x500") 
		new_window.resizable(width=True, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## horizontal scroll bar
		hor_scroll_bar = tk.Scrollbar(new_window, orient='horizontal', command=main_canvas.xview)
		hor_scroll_bar.pack(side='bottom', fill='x')
		main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		mat_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=mat_data_frame, anchor="nw")

		##############################
		# meta layout
		##############################
		if mat_assign_opt_str.get() == "Uniform":
			num_mat_int.set(1)  # set to 1 if uniform assignment is selected
		elif mat_assign_opt_str.get() == "Zone-Based" and num_mat_int.get() < 2:	
			num_mat_int.set(2)  # set to 2 since at least 2 zones are expected

		tk.Label(mat_data_frame, text=f"{mat_assign_opt_str.get()} Probabilistic Material Properties: {num_mat_int.get()} soil zones", font=("Arial", 14, "bold"), anchor="w", justify="left").grid(row=0, column=0, columnspan=10, padx=5, pady=(0,5), sticky="w")
   		
		##############################
		# material ID column
		##############################
		tk.Label(mat_data_frame, text="Mat ID", font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# material ID (max 10)
		for j in range(1, 11):
			tk.Label(mat_data_frame, text=f"{j}", font=("Arial", 12), anchor="w", justify="left").grid(row=2+j, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
  
		##############################
		# material ID zone file
		##############################
		# surface topography dip direction file name
		mat_zone_filename_label = tk.Label(mat_data_frame, text="Material Zones", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
		mat_zone_filename_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_zone_filename_str)
		mat_zone_filename_button = tk.Button(mat_data_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_zone_file_command(mat_zone_filename_entry)) 

		mat_zone_filename_label.grid(row=1, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
		mat_zone_filename_button.grid(row=1, column=1, columnspan=1, padx=5, pady=5)
		mat_zone_filename_entry.grid(row=1, column=2, columnspan=4, padx=5, pady=5, sticky="we")

		if mat_assign_opt_str.get() == "Uniform" or num_mat_int.get() == 1: 
			mat_zone_filename_entry.config(state="disable")
			mat_zone_filename_button.config(state="disable")
  
		##############################
		# 1st column heading data
		##############################
		prob_headings = [u"\u03BC", "CoV", "Prob. Dist.", "CorL X (m)", "CorL Y (m)", "Min", "Max"]

		column_headings = [u"K\u209B (m/s)", u'\u03B8\u1D62', 'SWCC_model', 'a (kPa)', 'n', 'm', u'\u03B8\u209B', u'\u03B8\u1D63', u'm\u1D65', 'S_max (m)', u'D (m\u00B2/s)', u'\u0263\u209B (kN/m\u00B3)', u'\u0278\' (\u00B0)', u'\u0278_b (\u00B0)', u'c\' (kPa)', 'root_model', u'\u0263\u1D63 (kN/m\u00B3)', 'c_base (kPa)', 'c_side (kPa)', 'root_depth (m)', u'\u02512', u'\u03B22', 'RR_max (kN/m)']

		mat_data_dict_keys = ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity", "soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c", "root_model", "root_unit_weight",  "root_c_base", "root_c_side", "root_root_depth", "root_alpha2", "root_beta2", "root_RR_max"]

		############
		## probabilistic - part 1
		############
		count_head = 1
		for i, heading in enumerate(column_headings):
			if heading == "SWCC_model":
				tk.Label(mat_data_frame, text=f"{heading}", font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="w")  
				count_head += 1
			elif heading == "root_model":
				tk.Label(mat_data_frame, text=f"{heading}", font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="w") 
				count_head += 1
			else:
				for k, p_head in enumerate(prob_headings):
					tk.Label(mat_data_frame, text=f"{heading}: {p_head}", font=("Arial", 12), anchor="w", justify="left").grid(row=2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="w")  
					count_head += 1

		for j in range(1, 11):
			count_head = 1
			for i,mat_key in enumerate(mat_data_dict_keys):
				if mat_key in ["hydraulic_SWCC_model", "root_model"]:
					model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key])
					if mat_key == "hydraulic_SWCC_model":
						if infil_model_str.get() == "Iverson":
							mat_data_dict[j][mat_key].set("Iverson")
						else:
							mat_data_dict[j][mat_key].set(SWCC_model_str.get())
					elif mat_key == "root_model":
						mat_data_dict[j][mat_key].set(root_reinforced_model_str.get()) 
					model_entry.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we") 
					model_entry.config(state="disable")
					count_head += 1
				
				elif mat_key in ["root_unit_weight", "root_c_base", "root_c_side", "root_root_depth", "root_alpha2", "root_beta2", "root_RR_max"]:
					for k, p_head in enumerate(prob_headings):
		
						if p_head == "Prob. Dist.":
							prob_dist_combo = ttk.Combobox(
									mat_data_frame,
									state="readonly",
									values=["Normal", "Lognormal"],
									textvariable=mat_data_dict[j][mat_key][k],
									width=10,
									font=("Arial", 12)
								)
							prob_dist_combo.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we")

							if root_reinforced_model_str.get() == "None" or slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Normal", "3D Bishop", "3D Janbu"] or j > num_mat_int.get():
								prob_dist_combo.config(state="disable")
							elif mat_key in ["root_alpha2", "root_beta2", "root_RR_max"] and (root_reinforced_model_str.get() == "Constant with Depth" or j > num_mat_int.get()):
								prob_dist_combo.config(state="disable")
							elif mat_key in ["root_c_base", "root_c_side", "root_root_depth"] and (root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)" or j > num_mat_int.get()):
								prob_dist_combo.config(state="disable")
							count_head += 1

						elif p_head in ["CorL X (m)", "CorL Y (m)"]:
							cor_len_combo = ttk.Combobox(
									mat_data_frame,
									state="normal",
									values=["inf"],
									textvariable=mat_data_dict[j][mat_key][k],
									width=10,
									font=("Arial", 12)
								)
							cor_len_combo.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we")

							if root_reinforced_model_str.get() == "None" or slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Normal", "3D Bishop", "3D Janbu"] or j > num_mat_int.get():
								cor_len_combo.config(state="disable")
							elif mat_key in ["root_alpha2", "root_beta2", "root_RR_max"] and (root_reinforced_model_str.get() == "Constant with Depth" or j > num_mat_int.get()):
								cor_len_combo.config(state="disable")
							elif mat_key in ["root_c_base", "root_c_side", "root_root_depth"] and (root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)" or j > num_mat_int.get()):
								cor_len_combo.config(state="disable")
							count_head += 1

						else:
							model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key][k])
							model_entry.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we") 

							if root_reinforced_model_str.get() == "None" or slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Normal", "3D Bishop", "3D Janbu"] or j > num_mat_int.get():
								model_entry.config(state="disable")
							elif mat_key in ["root_alpha2", "root_beta2", "root_RR_max"] and (root_reinforced_model_str.get() == "Constant with Depth" or j > num_mat_int.get()):
								model_entry.config(state="disable")
							elif mat_key in ["root_c_base", "root_c_side", "root_root_depth"] and (root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)" or j > num_mat_int.get()):
								model_entry.config(state="disable")
							count_head += 1

				else:
					for k, p_head in enumerate(prob_headings):
						if p_head == "Prob. Dist.":
							prob_dist_combo = ttk.Combobox(
									mat_data_frame,
									state="readonly",
									values=["Normal", "Lognormal"],
									textvariable=mat_data_dict[j][mat_key][k],
									width=10,
									font=("Arial", 12)
								)
							prob_dist_combo.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we")
							if j > num_mat_int.get():
								prob_dist_combo.config(state="disable")
							
							# disable and enable Hydraulic 
							elif j <= num_mat_int.get() and mat_key in ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity"]:
								if (infil_model_str.get() == "Iverson" or slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]) and mat_key not in ["hydraulic_k_sat", "hydraulic_diffusivity"]:
									prob_dist_combo.config(state="disable")
								elif infil_model_str.get() == "Green-Ampt" and mat_key in ["hydraulic_diffusivity"]:
									prob_dist_combo.config(state="disable")
							
							# disable and enable Soil properties
							elif j <= num_mat_int.get() and mat_key in ["soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c"]:
								if slope_model_str.get() == "Skip (only perform infiltration)":
									prob_dist_combo.config(state="disable")
								elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"] and mat_key == "soil_phi_b":
									prob_dist_combo.config(state="disable")

							count_head += 1	

						elif p_head in ["CorL X (m)", "CorL Y (m)"]:
							cor_len_combo = ttk.Combobox(
									mat_data_frame,
									state="normal",
									values=["inf"],
									textvariable=mat_data_dict[j][mat_key][k],
									width=10,
									font=("Arial", 12)
								)
							cor_len_combo.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we")
							if j > num_mat_int.get():
								cor_len_combo.config(state="disable")

							# disable and enable Hydraulic 
							elif j <= num_mat_int.get() and mat_key in ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity"]:
								if (infil_model_str.get() == "Iverson" or slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]) and mat_key not in ["hydraulic_k_sat", "hydraulic_diffusivity"]:
									cor_len_combo.config(state="disable")
								elif infil_model_str.get() == "Green-Ampt" and mat_key in ["hydraulic_diffusivity"]:
									cor_len_combo.config(state="disable")
							
							# disable and enable Soil properties
							elif j <= num_mat_int.get() and mat_key in ["soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c"]:
								if slope_model_str.get() == "Skip (only perform infiltration)":
									cor_len_combo.config(state="disable")
								elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"] and mat_key == "soil_phi_b":
									cor_len_combo.config(state="disable")

							count_head += 1	

						else:
							model_entry = tk.Entry(mat_data_frame, width=10, bd=3, font=("Arial", 12), textvariable=mat_data_dict[j][mat_key][k])
							model_entry.grid(row=j+2, column=count_head, columnspan=1, padx=5, pady=(0,5), sticky="we") 
							if j > num_mat_int.get():
								model_entry.config(state="disable")

							# disable and enable Hydraulic 
							elif j <= num_mat_int.get() and mat_key in ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "hydraulic_diffusivity"]:
								if (infil_model_str.get() == "Iverson" or slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]) and mat_key not in ["hydraulic_k_sat", "hydraulic_diffusivity"]:
									model_entry.config(state="disable")
								elif infil_model_str.get() == "Green-Ampt" and mat_key in ["hydraulic_diffusivity"]:
									model_entry.config(state="disable")
							
							# disable and enable Soil properties
							elif j <= num_mat_int.get() and mat_key in ["soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c"]:
								if slope_model_str.get() == "Skip (only perform infiltration)":
									model_entry.config(state="disable")
								elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"] and mat_key == "soil_phi_b":
									model_entry.config(state="disable")

							count_head += 1		

		# assign_button
		tk.Button(mat_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_mat_window_toplevel(new_window)).grid(row=13, column=0, columnspan=2, padx=5, pady=5, sticky="we")

		# Call close_mat_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_mat_window_toplevel(new_window)) 
		new_window.mainloop()

	# import GIS-based material files
	def open_mat_GIS_file_command(mat_key, entry_widget):
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_mat_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select material properties GIS file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd")
		 						)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_mat_GIS_file) > 0 and os.path.isfile(selected_mat_GIS_file):

				# only need the filename
				file_path_name = selected_mat_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]
				mat_data_GIS_dict[mat_key].set(file_name_only)

				# delete whatever is written in the file name text output box - so new one can be added
				entry_widget.delete(0, tk.END)
				entry_widget.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = f"material {mat_key} GIS file loaded ")

		except:
			pass

		return None

	# Function to open a new window to assign GIS material data 
	def open_new_window_material_GIS():
		# disable the combo and assign button to prevent multiple clicks
		mat_assign_opt_combo.config(state="disable")
		num_mat_combo.config(state="disable")
		root_reinforced_model_combo.config(state="disable")
		SWCC_model_combo.config(state="disable")
		mc_iterations_entry.config(state="disable")
		mat_assign_button.config(state="disable")
		random_field_method_combo.config(state="disable")  
		random_field_save_checkbutton.config(state="disable") 

		# GIS is always deterministic
		mc_iterations_int.set(1)

		# Create a new window to get material properties data
		new_window = tk.Toplevel(root)  
		new_window.title("Material")
		new_window.geometry("550x700") 
		new_window.resizable(width=True, height=True)
		main_canvas = tk.Canvas(new_window)

		# icon
		icon_img = tk.PhotoImage(file='NGI_logo_cropped.png')
		new_window.iconphoto(False, icon_img)
		new_window._icon_img = icon_img

		## horizontal scroll bar
		hor_scroll_bar = tk.Scrollbar(new_window, orient='horizontal', command=main_canvas.xview)
		hor_scroll_bar.pack(side='bottom', fill='x')
		main_canvas.configure(xscrollcommand = hor_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		## vertical scroll bar
		ver_scroll_bar = tk.Scrollbar(new_window, orient='vertical', command=main_canvas.yview)
		ver_scroll_bar.pack(side='right', fill='y')
		main_canvas.configure(yscrollcommand = ver_scroll_bar.set)
		main_canvas.bind('<Configure>', lambda e:main_canvas.configure(scrollregion=main_canvas.bbox("all")))

		# add canvas pack after packing the scroll bars to fit
		main_canvas.pack(side='left', fill='both', expand=True)

		mat_data_frame = tk.Frame(main_canvas)
		main_canvas.create_window((0,0), window=mat_data_frame, anchor="nw")

		##############################
		# main heading
		##############################
		tk.Label(mat_data_frame, text="GIS-based Material Properties", font=("Arial", 14, "bold"), anchor="w", justify="left").grid(row=0, column=0, columnspan=10, padx=5, pady=(0,5), sticky="w")

		##############################
		# material 
		##############################
		tk.Label(mat_data_frame, text="Properties", font=("Arial", 12, "bold"), anchor="w", justify="left").grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
		tk.Label(mat_data_frame, text="File or Value", font=("Arial", 12, "bold"), anchor="w", justify="left").grid(row=1, column=2, columnspan=4, padx=5, pady=(0,5), sticky="w")
		tk.Label(mat_data_frame, text="Select GIS", font=("Arial", 12, "bold"), anchor="w", justify="left").grid(row=1, column=6, columnspan=1, padx=5, pady=(0,5), sticky="w")

		# only need things from 3DTS things
		GIS_input_mat_data_dict_keys = ["hydraulic_k_sat", "hydraulic_initial_suction", "hydraulic_SWCC_model", "hydraulic_SWCC_a", "hydraulic_SWCC_n", "hydraulic_SWCC_m", "hydraulic_theta_sat", "hydraulic_theta_residual", "hydraulic_soil_m_v", "hydraulic_max_surface_storage", "soil_unit_weight", "soil_phi", "soil_phi_b", "soil_c", "root_model", "root_unit_weight",  "root_c_base", "root_c_side", "root_root_depth", "root_alpha2", "root_beta2", "root_RR_max"]
		GIS_input_column_headings = [u"K\u209B (m/s)", u'\u03B8\u1D62', 'SWCC_model', 'a (kPa)', 'n', 'm', u'\u03B8\u209B', u'\u03B8\u1D63', u'm\u1D65', 'S_max (m)', u'\u0263\u209B (kN/m\u00B3)', u'\u0278\' (\u00B0)', u'\u0278_b (\u00B0)', u'c\' (kPa)', 'root_model', u'\u0263\u1D63 (kN/m\u00B3)', 'c_base (kPa)', 'c_side (kPa)', 'root_depth (m)', u'\u02512', u'\u03B22', 'RR_max (kN/m)']

		# material heading
		for i, heading in enumerate(GIS_input_column_headings):
			tk.Label(mat_data_frame, text=heading, font=("Arial", 12), anchor="w", justify="left").grid(row=2+i, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w") 

		# entry
		mat_GIS_entry_dict = {}
		for i,mat_key in enumerate(GIS_input_mat_data_dict_keys):    
			mat_GIS_entry_dict[mat_key] = tk.Entry(mat_data_frame, width=30, bd=3, font=("Arial", 12), textvariable=mat_data_GIS_dict[mat_key])
			mat_GIS_entry_dict[mat_key].grid(row=i+2, column=2, columnspan=4, padx=5, pady=(0,5), sticky="we")
		
		# material GIS file selection button
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_k_sat", mat_GIS_entry_dict["hydraulic_k_sat"])).grid(row=2, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_initial_suction", mat_GIS_entry_dict["hydraulic_initial_suction"])).grid(row=3, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_SWCC_model", mat_GIS_entry_dict["hydraulic_SWCC_model"])).grid(row=4, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_SWCC_a", mat_GIS_entry_dict["hydraulic_SWCC_a"])).grid(row=5, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_SWCC_n", mat_GIS_entry_dict["hydraulic_SWCC_n"])).grid(row=6, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_SWCC_m", mat_GIS_entry_dict["hydraulic_SWCC_m"])).grid(row=7, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_theta_sat", mat_GIS_entry_dict["hydraulic_theta_sat"])).grid(row=8, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_theta_residual", mat_GIS_entry_dict["hydraulic_theta_residual"])).grid(row=9, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_soil_m_v", mat_GIS_entry_dict["hydraulic_soil_m_v"])).grid(row=10, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("hydraulic_max_surface_storage", mat_GIS_entry_dict["hydraulic_max_surface_storage"])).grid(row=11, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("soil_unit_weight", mat_GIS_entry_dict["soil_unit_weight"])).grid(row=12, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("soil_phi", mat_GIS_entry_dict["soil_phi"])).grid(row=13, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("soil_phi_b", mat_GIS_entry_dict["soil_phi_b"])).grid(row=14, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("soil_c", mat_GIS_entry_dict["soil_c"])).grid(row=15, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_model", mat_GIS_entry_dict["root_model"])).grid(row=16, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_unit_weight", mat_GIS_entry_dict["root_unit_weight"])).grid(row=17, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_c_base", mat_GIS_entry_dict["root_c_base"])).grid(row=18, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_c_side", mat_GIS_entry_dict["root_c_side"])).grid(row=19, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_root_depth", mat_GIS_entry_dict["root_root_depth"])).grid(row=20, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_alpha2", mat_GIS_entry_dict["root_alpha2"])).grid(row=21, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_beta2", mat_GIS_entry_dict["root_beta2"])).grid(row=22, column=6, columnspan=1, padx=5, pady=5, sticky="we")
		tk.Button(mat_data_frame, text="Select", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:open_mat_GIS_file_command("root_RR_max", mat_GIS_entry_dict["root_RR_max"])).grid(row=23, column=6, columnspan=1, padx=5, pady=5, sticky="we")

		# assign_button
		tk.Button(mat_data_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=lambda:close_mat_window_toplevel(new_window)).grid(row=0, column=6, columnspan=2, padx=5, pady=5, sticky="we")

		# Call close_mat_window_toplevel when the window is closed
		new_window.protocol("WM_DELETE_WINDOW", lambda:close_mat_window_toplevel(new_window)) 
		new_window.mainloop()


	#################################
	# open landslide source file
	#################################
	def open_source_file_command():

		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(input_folder_entry.get()):
				status.config(text="selecting new input folder path ")
				file_path = input_folder_entry.get()
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_source_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select landslide source file",
								filetypes=(
									("Esri ASCII raster", "*.asc"),
									("comma-separated value", "*.csv"),
									("Surfer 6 Text Grid", "*.grd"),
								)   # only open valid DEM files formats
							)
		
		# display output folder location in the output text
		try:
			if len(selected_source_file) > 0 and os.path.isfile(selected_source_file):

				# only need the filename
				file_path_name = selected_source_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# delete whatever is written in the file name text output box - so new one can be added
				landslide_source_filename_entry.delete(0, tk.END)
				landslide_source_filename_entry.insert(0, file_name_only)

				# update status to show similuation is running 
				status.config(text = "landslide source file loaded ")

		except:
			pass

		return None

	#################################
	# function keys
	#################################
	"""need to update the manual link"""
	def open_manual_file_command():
		# name of help file
		help_file = app_path+"/Robust Areal Landslide Prediction (RALP) - GUI v1.00 - User Manual.pdf"
		if opsys == "Windows":
			os.startfile(help_file)
		elif opsys == "Darwin":
			subprocess.run(["open", help_file])
		else:
			subprocess.run(["xdg-open", help_file])
		# webbrowser.open_new("https://www.google.com")
		return None


	def open_input_result_folder_explorer_command():
		# open the folder path
		if system() == "Windows":
			os.startfile(input_folder_str.get()+'/')
			os.startfile(output_folder_str.get()+'/')
		elif system() == "Linux":
			subprocess.run([fileman, input_folder_str.get()+'/'])
			subprocess.run([fileman, output_folder_str.get()+'/'])
		elif system() == "Darwin":
			subprocess.run(["open", input_folder_str.get()])
			subprocess.run(["open", output_folder_str.get()])
		return None


	def make_yaml_bat_bash_command():

		##########################################
		## for 3DTS
		##########################################
		if (slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Translational Slide (3DTS)"]):

			#####################
			## restart simulations from previously runned files
			#####################
			if overall_input_folder_str.get() != "" and (".json" in overall_input_folder_str.get() or ".JSON" in overall_input_folder_str.get() or ".yaml" in overall_input_folder_str.get() or ".YAML" in overall_input_folder_str.get() or ".yml" in overall_input_folder_str.get() or ".YML" in overall_input_folder_str.get()):

				# only the filename
				file_path_name = overall_input_folder_str.get() 
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				removed_file_ext_list = file_name_only.split(".")
				removed_file_without_ext = ".".join(file_naming_list[:-1])

				######################################
				## generate YAML file and save in input directory
				######################################
				with open(output_folder_str.get()+'/'+project_name_str.get()+'_3DTSP_input.yaml', 'w') as yaml_file:
					yaml.safe_dump(json_yaml_input_data, yaml_file, default_flow_style=None, sort_keys=False)

				######################################
				## generate bat and bash file to run 
				######################################
				run_bash_script = "#!/bin/bash\n\n"
				run_bat_script = "@echo off\n\n"

				run_python_code = '\"' + '.\\main_3DTSP_v20250813.pyc\" \"'+file_name_only+'\"' 

				run_bash_script += f"python3 {run_python_code}\n"
				run_bat_script += f"python {run_python_code} && pause && exit \n"

				run_bash_script += f"\necho rerun of 3DTSP simulation for {file_name_only} completed\n"
				with open(output_folder_str.get()+'/'+f'rerun_3DTSP_{removed_file_without_ext}.sh', 'w') as f:
					f.write(run_bash_script)

				run_bat_script += f"\necho rerun of 3DTSP simulation for {file_name_only} completed\n"
				with open(output_folder_str.get()+'/'+f'rerun_3DTSP_{removed_file_without_ext}.bat', 'w') as f:
					f.write(run_bat_script)

				######################################
				## copy paste the main_3DTS script
				######################################
				shutil.copy(overall_input_folder_str.get(), output_folder_str.get()+f".\\{file_name_only}")
				shutil.copy(r"./main_3DTSP_v20250813.py", output_folder_str.get()+r"./main_3DTSP_v20250813.py")

			#####################
			## generate dictionary hold input file 
			#####################
			else:
				json_yaml_input_data = {}

				json_yaml_input_data["filename"] = project_name_str.get()

				# assign relative path from the bash or batch script
				json_yaml_input_data["input_folder_path"] = "./"
				json_yaml_input_data["output_folder_path"] = f"./{project_name_str.get()}_results/"

				# generate an empty folder in the output directory
				if not os.path.exists(output_folder_str.get()+f"/{project_name_str.get()}_results/"):
					os.makedirs(output_folder_str.get()+f"/{project_name_str.get()}_results/")

				json_yaml_input_data["restarting_simulation_JSON"] = None 
				if overall_input_folder_str.get() != "" and (".json" in overall_input_folder_str.get() or ".JSON" in overall_input_folder_str.get()):
					json_yaml_input_data["restarting_simulation_JSON"] = overall_input_folder_str.get()

				json_yaml_input_data["results_format"] = output_format_opt_str.get()

				if generate_plot_opt_int.get() == 1:
					json_yaml_input_data["generate_plot"] = True
				else:
					json_yaml_input_data["generate_plot"] = False

				json_yaml_input_data["unit_weight_of_water"] = unit_weight_water_double.get()

				json_yaml_input_data["FS_crit"] = critical_FS_double.get()

				json_yaml_input_data["monte_carlo_iteration_max"] = mc_iterations_int.get()

				json_yaml_input_data["vertical_spacing"] = soil_dz_double.get()

				json_yaml_input_data["termination_apply"] = False
				json_yaml_input_data["after_termination_new_times_apply"] = False

				if surf_dip_for_GA_int.get() == 1:
					json_yaml_input_data["DEM_surf_dip_infiltraion_apply"] = True
				else:
					json_yaml_input_data["DEM_surf_dip_infiltraion_apply"] = False

				if debris_flow_criteria_int.get() == 1:
					json_yaml_input_data["DEM_debris_flow_criteria_apply"] = True
				else:		
					json_yaml_input_data["DEM_debris_flow_criteria_apply"] = False
				
				if slope_model_str.get() == "Skip (only perform infiltration)": 
					json_yaml_input_data["FS_analysis_method"] = None 
					json_yaml_input_data["cell_size_3DFS_min"] = None
					json_yaml_input_data["cell_size_3DFS_max"] = None
					json_yaml_input_data["superellipse_power"] = None
					json_yaml_input_data["superellipse_eccentricity_ratio"] = None
					json_yaml_input_data["3D_FS_iteration_limit"] = None
					json_yaml_input_data["3D_FS_convergence_tolerance"] = None
					json_yaml_input_data["apply_side_resistance_3D"] = None
					json_yaml_input_data["apply_root_resistance_3D"] = None

				elif slope_model_str.get() == "Infinite Slope":
					json_yaml_input_data["FS_analysis_method"] = "infinite" 
					json_yaml_input_data["cell_size_3DFS_min"] = 1
					json_yaml_input_data["cell_size_3DFS_max"] = 1
					json_yaml_input_data["superellipse_power"] = 100
					json_yaml_input_data["superellipse_eccentricity_ratio"] = 1
					json_yaml_input_data["3D_FS_iteration_limit"] = 1
					json_yaml_input_data["3D_FS_convergence_tolerance"] = 0.001
					json_yaml_input_data["apply_side_resistance_3D"] = False
					json_yaml_input_data["apply_root_resistance_3D"] = False

				elif slope_model_str.get() == "3D Translational Slide (3DTS)":
					json_yaml_input_data["FS_analysis_method"] = "3D Janbu" 
					json_yaml_input_data["cell_size_3DFS_min"] = min_cell_3DTS_int.get()
					json_yaml_input_data["cell_size_3DFS_max"] = max_cell_3DTS_int.get()

					temp_super_power1 = superellipse_power_3DTS_str.get().split(",")
					temp_super_power2 = [float(p1.strip()) for p1 in temp_super_power1]  # strip all whitespaces

					temp_eccen_ratio1 = superellipse_eccen_ratio_3DTS_str.get().split(",")
					temp_eccen_ratio2 = [float(ec1.strip()) for ec1 in temp_eccen_ratio1]  # strip all whitespaces

					json_yaml_input_data["superellipse_power"] = temp_super_power2[:]
					json_yaml_input_data["superellipse_eccentricity_ratio"] = temp_eccen_ratio2[:]
					json_yaml_input_data["3D_FS_iteration_limit"] = 30
					json_yaml_input_data["3D_FS_convergence_tolerance"] = 0.005

					if side_resistance_3DTS_int.get() == 1:
						json_yaml_input_data["apply_side_resistance_3D"] = True 
					else:
						json_yaml_input_data["apply_side_resistance_3D"] = False

					if root_reinforced_model_str.get() == "None":
						json_yaml_input_data["apply_root_resistance_3D"] = False
					elif root_reinforced_model_str.get() in ["Constant with Depth", "van Zadelhoff et al. (2021)"]: 
						json_yaml_input_data["apply_root_resistance_3D"] = True

				json_yaml_input_data["DEM_UCA_compute_all"] = True

				if multi_CPU_method_opt_int.get() >= 1:
					json_yaml_input_data["max_cpu_num"] = max_CPU_pool_int.get()
				else:
					json_yaml_input_data["max_cpu_num"] = 1

				json_yaml_input_data["rain_unit"] = rainfall_intensity_unit_str.get()

				rainfall_hist_list = []
				for rain_t in range(1, 101):
					# check if empty
					if (rain_hist_t_dict[rain_t][0].get() == 0 and rain_hist_t_dict[rain_t][1].get() == 0) or (rainfall_history_opt_str.get() == "Uniform" and rain_hist_t_dict[rain_t][2][0] == 0) or (rainfall_history_opt_str.get() == "GIS file" and len(rain_hist_t_dict[rain_t][2][1].get()) == 0) or (rainfall_history_opt_str.get() in ["Deterministic Rainfall Gauge", "Probabilistic Rainfall Gauge"] and (rain_hist_t_dict[rain_t][2][2][0][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][1][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][2][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][3][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][4][2].get() == 0)):
						continue    

					if rainfall_history_opt_str.get() == "Uniform":
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), rain_hist_t_dict[rain_t][2][0].get()])
					elif rainfall_history_opt_str.get() == "GIS file":
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), rain_hist_t_dict[rain_t][2][1].get()])
					elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge":
						gauge_list = []
						for gauge in range(5):
							if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0:
								gauge_list.append([
									rain_hist_t_dict[rain_t][2][2][gauge][0].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][1].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][2].get()
								])
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), gauge_list[:]])
					elif rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":
						gauge_list = []
						for gauge in range(5):
							if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0 and (isinstance(rain_hist_t_dict[rain_t][2][2][gauge][5].get(), (int,float)) and rain_hist_t_dict[rain_t][2][2][gauge][5].get() != 0) and (isinstance(rain_hist_t_dict[rain_t][2][2][gauge][6].get(), (int, float)) and rain_hist_t_dict[rain_t][2][2][gauge][6].get() != 0):
								gauge_list.append([
									rain_hist_t_dict[rain_t][2][2][gauge][0].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][1].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][2].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][3].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][4].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][5].get(),	
									rain_hist_t_dict[rain_t][2][2][gauge][6].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][7].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][8].get()
								])
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), gauge_list[:]])
				json_yaml_input_data["rainfall_history"] = rainfall_hist_list[:]

				json_yaml_input_data["dt_iteration"] = rainfall_time_sudiv_int.get()
				
				# not implemented for 3DTS yet
				json_yaml_input_data["debris_t_max"] = 30
				json_yaml_input_data["debris_dt"] = 1
				
				json_yaml_input_data["DEM_file_name"] = DEM_filename_str.get()		

				if soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["uniform", uniform_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["GIS", GIS_soil_depth_str.get()]
				elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["Holm and Edvarson - Norway", min_soil_depth_double.get(), max_soil_depth_double.get()] 
				elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
					gen_soil_d = ["general multiregression", "linear", min_soil_depth_double.get(),
					max_soil_depth_double.get(), gen_reg_intercept_double.get()]
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]
				elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
					gen_soil_d = ["general multiregression", "power", min_soil_depth_double.get(),
					max_soil_depth_double.get(), gen_reg_intercept_double.get()] 
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]

				elif soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - uniform", uniform_soil_depth_double.get(), soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - GIS", GIS_soil_depth_str.get(), soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - Holm and Edvarson - Norway", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 1:
					gen_soil_d = ["prob - general multiregression", "linear", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get(), gen_reg_intercept_double.get()]
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]
				elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 1:
					gen_soil_d = ["prob - general multiregression", "power", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get(), gen_reg_intercept_double.get()] 
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]

				
				if groundwater_opt_str.get() == "Thickness Above Bedrock":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["thickness above bedrock", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:			
						json_yaml_input_data["ground_water_data"] = ["thickness above bedrock", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "Depth From Surface":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["depth from surface", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["depth from surface", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "% of Soil Thickness Above Bedrock":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness above bedrock", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness above bedrock", gwt_GIS_filename_str.get()]    
				elif groundwater_opt_str.get() == "% of Soil Thickness From Surface":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness from surface", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness from surface", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "GWT elevation GIS":
					if len(gwt_GIS_filename_str.get()) > 0:
						json_yaml_input_data["ground_water_data"] = ["GWT elevation GIS", gwt_GIS_filename_str.get()]


				if surf_dip_filename_str.get() == "(optional)" or len(surf_dip_filename_str.get()) == 0:
					json_yaml_input_data["dip_surf_filename"] = None
				else:
					json_yaml_input_data["dip_surf_filename"] = surf_dip_filename_str.get()

				if surf_aspect_filename_str.get() == "(optional)" or len(surf_aspect_filename_str.get()) == 0:
					json_yaml_input_data["aspect_surf_filename"] = None
				else:
					json_yaml_input_data["aspect_surf_filename"] = surf_aspect_filename_str.get()

				if base_dip_filename_str.get() == "(optional)" or len(base_dip_filename_str.get()) == 0:
					json_yaml_input_data["dip_base_filename"] = None
				else:
					json_yaml_input_data["dip_base_filename"] = base_dip_filename_str.get()

				if base_aspect_filename_str.get() == "(optional)" or len(base_aspect_filename_str.get()) == 0:
					json_yaml_input_data["aspect_base_filename"] = None
				else:
					json_yaml_input_data["aspect_base_filename"] = base_aspect_filename_str.get()


				if len(debris_flow_criteria_Criteria_str.get()) == 0:
					json_yaml_input_data["DEM_debris_flow_initiation_filename"] = None
				else:
					json_yaml_input_data["DEM_debris_flow_initiation_filename"] = debris_flow_criteria_Criteria_str.get()

				if len(debris_flow_criteria_network_str.get()) == 0:
					json_yaml_input_data["DEM_neighbor_directed_graph_filename"] = None
				else:
					json_yaml_input_data["DEM_neighbor_directed_graph_filename"] = debris_flow_criteria_network_str.get()

				if len(debris_flow_criteria_UCA_str.get()) == 0:
					json_yaml_input_data["DEM_UCA_filename"] = None
				else:
					json_yaml_input_data["DEM_UCA_filename"] = debris_flow_criteria_UCA_str.get()

				json_yaml_input_data["local_cell_sizes_slope"] = local_cell_DEM2dip_int.get()
				json_yaml_input_data["interpolation_method"] = "linear"

				## material properties
				# SWCC model shortform
				if SWCC_model_str.get() == "van Genuchten (1980)":
					SWCC_model_assign = "vG"
				elif SWCC_model_str.get() == "Fredlund and Xing (1994)":
					SWCC_model_assign = "FX"

				# uniform asignment
				if mat_assign_opt_str.get() == "Uniform":

					json_yaml_input_data["material_file_name"] = None    # material ID on DEM cells

					mID = 1
					# deterministic
					if mc_iterations_int.get() == 1:
						json_yaml_input_data["material"] = {
							str(mID): {
								"hydraulic": {
									"k_sat": mat_data_dict[mID]["hydraulic_k_sat"][0].get(),
									"initial_suction": mat_data_dict[mID]["hydraulic_initial_suction"][0].get(),
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": mat_data_dict[mID]["hydraulic_SWCC_a"][0].get(),
									"SWCC_n": mat_data_dict[mID]["hydraulic_SWCC_n"][0].get(),
									"SWCC_m": mat_data_dict[mID]["hydraulic_SWCC_m"][0].get(),
									"theta_sat": mat_data_dict[mID]["hydraulic_theta_sat"][0].get(),
									"theta_residual": mat_data_dict[mID]["hydraulic_theta_residual"][0].get(),
									"soil_m_v": mat_data_dict[mID]["hydraulic_soil_m_v"][0].get(),
									"max_surface_storage": mat_data_dict[mID]["hydraulic_max_surface_storage"][0].get()
								},
								"soil": {
									"unit_weight": mat_data_dict[mID]["soil_unit_weight"][0].get(),
									"phi": mat_data_dict[mID]["soil_phi"][0].get(),
									"phi_b": mat_data_dict[mID]["soil_phi_b"][0].get(),
									"c": mat_data_dict[mID]["soil_c"][0].get(),
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}
						} 

						if root_reinforced_model_str.get() == "Constant with Depth":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "constant" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"] = [
								mat_data_dict[mID]["root_c_base"][0].get(),
								mat_data_dict[mID]["root_c_side"][0].get(),
								mat_data_dict[mID]["root_root_depth"][0].get()
							]
						elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"] = [
								mat_data_dict[mID]["root_alpha2"][0].get(),
								mat_data_dict[mID]["root_beta2"][0].get(),
								mat_data_dict[mID]["root_RR_max"][0].get()
							]

					# Monte Carlo probabilistic
					elif mc_iterations_int.get() > 1:
						json_yaml_input_data["material"] = {
							str(mID): {
								"hydraulic": {
									"k_sat": [
										mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"initial_suction": [
										mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": [
										mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_n": [
										mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_m": [
										mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"theta_sat": [
										mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"theta_residual": [
										mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"soil_m_v": [
										mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"max_surface_storage": [
										mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else None
					  					for pIDX in range(7)
									]
								},
								"soil": {
									"unit_weight": [
										mat_data_dict[mID]["soil_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"phi": [
										mat_data_dict[mID]["soil_phi"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"phi_b": [
										mat_data_dict[mID]["soil_phi_b"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"c": [
										mat_data_dict[mID]["soil_c"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_c"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_c"][pIDX].get())
										else float(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_c"][pIDX].get())
										else None
					  					for pIDX in range(7)
									]
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}
						} 

						if root_reinforced_model_str.get() == "Constant with Depth":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "constant" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = [
									mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][0] = [
									mat_data_dict[mID]["root_c_base"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_base"][pIDX].get())
									else float(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_base"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][1] = [
									mat_data_dict[mID]["root_c_side"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_side"][pIDX].get())
									else float(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_side"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][2] = [
									mat_data_dict[mID]["root_root_depth"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_root_depth"][pIDX].get())
									else float(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_root_depth"][pIDX].get())
									else None
									for pIDX in range(7)
								]

						elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = [
									mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][0] = [
									mat_data_dict[mID]["root_alpha2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_alpha2"][pIDX].get())
									else float(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_alpha2"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][1] = [
									mat_data_dict[mID]["root_beta2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_beta2"][pIDX].get())
									else float(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_beta2"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][2] = [
									mat_data_dict[mID]["root_RR_max"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_RR_max"][pIDX].get())
									else float(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_RR_max"][pIDX].get())
									else None
									for pIDX in range(7)
								]

					# GIS files 
					json_yaml_input_data["material_GIS"] = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": None 
						}
					}

					if root_reinforced_model_str.get() == "Constant with Depth":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "constant" 
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "van Zadelhoff et al. (2021)" 

				elif mat_assign_opt_str.get() == "Zone-Based":

					# material ID on DEM cells
					json_yaml_input_data["material_file_name"] = mat_zone_filename_str.get()

					temp_mat = {}
					for mID in range(1, 1+int(num_mat_int.get())):
						# deterministic
						if mc_iterations_int.get() == 1:
							temp_mat[str(mID)] = {
								"hydraulic": {
									"k_sat": mat_data_dict[mID]["hydraulic_k_sat"][0].get(),
									"initial_suction": mat_data_dict[mID]["hydraulic_initial_suction"][0].get(),
									"SWCC_model": SWCC_model_assign,
										"SWCC_a": mat_data_dict[mID]["hydraulic_SWCC_a"][0].get(),
										"SWCC_n": mat_data_dict[mID]["hydraulic_SWCC_n"][0].get(),
										"SWCC_m": mat_data_dict[mID]["hydraulic_SWCC_m"][0].get(),
										"theta_sat": mat_data_dict[mID]["hydraulic_theta_sat"][0].get(),
										"theta_residual": mat_data_dict[mID]["hydraulic_theta_residual"][0].get(),
										"soil_m_v": mat_data_dict[mID]["hydraulic_soil_m_v"][0].get(),
										"max_surface_storage": mat_data_dict[mID]["hydraulic_max_surface_storage"][0].get()
									},
									"soil": {
										"unit_weight": mat_data_dict[mID]["soil_unit_weight"][0].get(),
										"phi": mat_data_dict[mID]["soil_phi"][0].get(),
										"phi_b": mat_data_dict[mID]["soil_phi_b"][0].get(),
										"c": mat_data_dict[mID]["soil_c"][0].get(),
									},
									"root": {
										"unit_weight": None,
										"model": None,
										"parameters": [None, None, None]
									}
								}

							if root_reinforced_model_str.get() == "Constant with Depth":
								temp_mat[str(mID)]["root"]["model"] = "constant" 
								temp_mat[str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
								temp_mat[str(mID)]["root"]["parameters"] = [
									mat_data_dict[mID]["root_c_base"][0].get(),
									mat_data_dict[mID]["root_c_side"][0].get(),
									mat_data_dict[mID]["root_root_depth"][0].get()
								]
							elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
								temp_mat[str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
								temp_mat[str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
								temp_mat[str(mID)]["root"]["parameters"] = [
									mat_data_dict[mID]["root_alpha2"][0].get(),
									mat_data_dict[mID]["root_beta2"][0].get(),
									mat_data_dict[mID]["root_RR_max"][0].get()
								]

						# Monte Carlo probabilistic
						elif mc_iterations_int.get() > 1:
							temp_mat[str(mID)] = {
								"hydraulic": {
									"k_sat": [
										mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"initial_suction": [
										mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": [
										mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_n": [
										mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_m": [
										mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"theta_sat": [
										mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"theta_residual": [
										mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"soil_m_v": [
										mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"max_surface_storage": [
										mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								},
								"soil": {
									"unit_weight": [
										mat_data_dict[mID]["soil_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"phi": [
										mat_data_dict[mID]["soil_phi"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"phi_b": [
										mat_data_dict[mID]["soil_phi_b"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"c": [
										mat_data_dict[mID]["soil_c"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_c"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_c"][pIDX].get())
										else float(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_c"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}

							if root_reinforced_model_str.get() == "Constant with Depth":
								temp_mat[str(mID)]["root"]["model"] = "constant" 
								temp_mat[str(mID)]["root"]["unit_weight"] = [
										mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][0] = [
										mat_data_dict[mID]["root_c_base"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_base"][pIDX].get())
										else float(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_base"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][1] = [
										mat_data_dict[mID]["root_c_side"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_side"][pIDX].get())
										else float(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_side"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][2] = [
										mat_data_dict[mID]["root_root_depth"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_root_depth"][pIDX].get())
										else float(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_root_depth"][pIDX].get())
										else None
										for pIDX in range(7)
									]

							elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
								temp_mat[str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
								temp_mat[str(mID)]["root"]["unit_weight"] = [
										mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][0] = [
										mat_data_dict[mID]["root_alpha2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_alpha2"][pIDX].get())
										else float(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_alpha2"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][1] = [
										mat_data_dict[mID]["root_beta2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_beta2"][pIDX].get())
										else float(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_beta2"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][2] = [
										mat_data_dict[mID]["root_RR_max"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_RR_max"][pIDX].get())
										else float(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_RR_max"][pIDX].get())
										else None
										for pIDX in range(7)
									]

					json_yaml_input_data["material"] = temp_mat

					# GIS files 
					json_yaml_input_data["material_GIS"] = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": None 
						}
					}

					if root_reinforced_model_str.get() == "Constant with Depth":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "constant" 
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "van Zadelhoff et al. (2021)" 

				elif mat_assign_opt_str.get() == "GIS files":

					# material ID on DEM cells
					json_yaml_input_data["material_file_name"] = None

					temp_mat = {
						"1": {
							"hydraulic": {
								"k_sat": None,
								"initial_suction": None,
								"SWCC_model": SWCC_model_assign,
								"SWCC_a": None,
								"SWCC_n": None,
								"SWCC_m": None,
								"theta_sat": None,
								"theta_residual": None,
								"soil_m_v": None,
								"max_surface_storage": None
							},
							"soil": {
								"unit_weight": None,
								"phi": None,
								"phi_b": None,
								"c": None,
							},
							"root": {
								"unit_weight": None,
								"model": None,
								"parameters": [None, None, None]
							}
						}
					} 

					temp_mat_GIS = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": [None, None, None] 
						}
					}

					# root
					if root_reinforced_model_str.get() == "Constant with Depth":
						temp_mat["1"]["root"]["model"] = "constant"
						temp_mat_GIS["root"]["model"] = "constant"

						# root - unit_weight
						if len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==False and is_float(mat_data_GIS_dict["root_unit_weight"].get())==False): 
							temp_mat_GIS["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
						elif len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==True or is_float(mat_data_GIS_dict["root_unit_weight"].get())==True):	
							temp_mat["1"]["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
					
						# parameters
						if len(mat_data_GIS_dict["root_c_base"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_base"].get())==False and is_float(mat_data_GIS_dict["root_c_base"].get())==False): 
							temp_mat_GIS["root"]["parameters"][0] = mat_data_GIS_dict["root_c_base"].get()
						elif len(mat_data_GIS_dict["root_c_base"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_base"].get())==True or is_float(mat_data_GIS_dict["root_c_base"].get())==True):	
							temp_mat["1"]["root"]["parameters"][0] = mat_data_GIS_dict["root_c_base"].get()

						if len(mat_data_GIS_dict["root_c_side"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_side"].get())==False and is_float(mat_data_GIS_dict["root_c_side"].get())==False): 
							temp_mat_GIS["root"]["parameters"][1] = mat_data_GIS_dict["root_c_side"].get()
						elif len(mat_data_GIS_dict["root_c_side"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_side"].get())==True or is_float(mat_data_GIS_dict["root_c_side"].get())==True):	
							temp_mat["1"]["root"]["parameters"][1] = mat_data_GIS_dict["root_c_side"].get()
			
						if len(mat_data_GIS_dict["root_root_depth"].get()) > 0 and (is_int(mat_data_GIS_dict["root_root_depth"].get())==False and is_float(mat_data_GIS_dict["root_root_depth"].get())==False): 
							temp_mat_GIS["root"]["parameters"][2] = mat_data_GIS_dict["root_root_depth"].get()
						elif len(mat_data_GIS_dict["root_root_depth"].get()) > 0 and (is_int(mat_data_GIS_dict["root_root_depth"].get())==True or is_float(mat_data_GIS_dict["root_root_depth"].get())==True):	
							temp_mat["1"]["root"]["parameters"][2] = mat_data_GIS_dict["root_root_depth"].get()
					
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						temp_mat["1"]["root"]["model"] = "van Zadelhoff et al. (2021)"
						temp_mat_GIS["root"]["model"] = "van Zadelhoff et al. (2021)"

						# root - unit_weight
						if len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==False and is_float(mat_data_GIS_dict["root_unit_weight"].get())==False): 
							temp_mat_GIS["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
						elif len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==True or is_float(mat_data_GIS_dict["root_unit_weight"].get())==True):	
							temp_mat["1"]["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
			
						# parameters
						if len(mat_data_GIS_dict["root_alpha2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_alpha2"].get())==False and is_float(mat_data_GIS_dict["root_alpha2"].get())==False): 
							temp_mat_GIS["root"]["parameters"][0] = mat_data_GIS_dict["root_alpha2"].get()
						elif len(mat_data_GIS_dict["root_alpha2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_alpha2"].get())==True or is_float(mat_data_GIS_dict["root_alpha2"].get())==True):	
							temp_mat["1"]["root"]["parameters"][0] = mat_data_GIS_dict["root_alpha2"].get()

						if len(mat_data_GIS_dict["root_beta2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_beta2"].get())==False and is_float(mat_data_GIS_dict["root_beta2"].get())==False): 
							temp_mat_GIS["root"]["parameters"][1] = mat_data_GIS_dict["root_beta2"].get()
						elif len(mat_data_GIS_dict["root_beta2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_beta2"].get())==True or is_float(mat_data_GIS_dict["root_beta2"].get())==True):	
							temp_mat["1"]["root"]["parameters"][1] = mat_data_GIS_dict["root_beta2"].get()
			
						if len(mat_data_GIS_dict["root_RR_max"].get()) > 0 and (is_int(mat_data_GIS_dict["root_RR_max"].get())==False and is_float(mat_data_GIS_dict["root_RR_max"].get())==False): 
							temp_mat_GIS["root"]["parameters"][2] = mat_data_GIS_dict["root_RR_max"].get()
						elif len(mat_data_GIS_dict["root_RR_max"].get()) > 0 and (is_int(mat_data_GIS_dict["root_RR_max"].get())==True or is_float(mat_data_GIS_dict["root_RR_max"].get())==True):	
							temp_mat["1"]["root"]["parameters"][2] = mat_data_GIS_dict["root_RR_max"].get()


					# hydraulic - k_sat
					if len(mat_data_GIS_dict["hydraulic_k_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_k_sat"].get())==False and is_float(mat_data_GIS_dict["hydraulic_k_sat"].get())==False): 
						temp_mat_GIS["hydraulic"]["k_sat"] = mat_data_GIS_dict["hydraulic_k_sat"].get()
					elif len(mat_data_GIS_dict["hydraulic_k_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_k_sat"].get())==True or is_float(mat_data_GIS_dict["hydraulic_k_sat"].get())==True):	
						temp_mat["1"]["hydraulic"]["k_sat"] = mat_data_GIS_dict["hydraulic_k_sat"].get()

					# hydraulic - initial_suction
					if len(mat_data_GIS_dict["hydraulic_initial_suction"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_initial_suction"].get())==False and is_float(mat_data_GIS_dict["hydraulic_initial_suction"].get())==False): 
						temp_mat_GIS["hydraulic"]["initial_suction"] = mat_data_GIS_dict["hydraulic_initial_suction"].get()
					elif len(mat_data_GIS_dict["hydraulic_initial_suction"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_initial_suction"].get())==True or is_float(mat_data_GIS_dict["hydraulic_initial_suction"].get())==True):	
						temp_mat["1"]["hydraulic"]["initial_suction"] = mat_data_GIS_dict["hydraulic_initial_suction"].get()

					# hydraulic - SWCC_a
					if len(mat_data_GIS_dict["hydraulic_SWCC_a"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_a"] = mat_data_GIS_dict["hydraulic_SWCC_a"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_a"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_a"] = mat_data_GIS_dict["hydraulic_SWCC_a"].get()

					# hydraulic - SWCC_n
					if len(mat_data_GIS_dict["hydraulic_SWCC_n"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_n"] = mat_data_GIS_dict["hydraulic_SWCC_n"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_n"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_n"] = mat_data_GIS_dict["hydraulic_SWCC_n"].get()

					# hydraulic - SWCC_m
					if len(mat_data_GIS_dict["hydraulic_SWCC_m"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_m"] = mat_data_GIS_dict["hydraulic_SWCC_m"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_m"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_m"] = mat_data_GIS_dict["hydraulic_SWCC_m"].get()

					# hydraulic - theta_sat
					if len(mat_data_GIS_dict["hydraulic_theta_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_sat"].get())==False and is_float(mat_data_GIS_dict["hydraulic_theta_sat"].get())==False): 
						temp_mat_GIS["hydraulic"]["theta_sat"] = mat_data_GIS_dict["hydraulic_theta_sat"].get()
					elif len(mat_data_GIS_dict["hydraulic_theta_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_sat"].get())==True or is_float(mat_data_GIS_dict["hydraulic_theta_sat"].get())==True):	
						temp_mat["1"]["hydraulic"]["theta_sat"] = mat_data_GIS_dict["hydraulic_theta_sat"].get()

					# hydraulic - theta_residual
					if len(mat_data_GIS_dict["hydraulic_theta_residual"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_residual"].get())==False and is_float(mat_data_GIS_dict["hydraulic_theta_residual"].get())==False): 
						temp_mat_GIS["hydraulic"]["theta_residual"] = mat_data_GIS_dict["hydraulic_theta_residual"].get()
					elif len(mat_data_GIS_dict["hydraulic_theta_residual"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_residual"].get())==True or is_float(mat_data_GIS_dict["hydraulic_theta_residual"].get())==True):	
						temp_mat["1"]["hydraulic"]["theta_residual"] = mat_data_GIS_dict["hydraulic_theta_residual"].get()

					# hydraulic - soil_m_v
					if len(mat_data_GIS_dict["hydraulic_soil_m_v"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==False and is_float(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==False): 
						temp_mat_GIS["hydraulic"]["soil_m_v"] = mat_data_GIS_dict["hydraulic_soil_m_v"].get()
					elif len(mat_data_GIS_dict["hydraulic_soil_m_v"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==True or is_float(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==True):	
						temp_mat["1"]["hydraulic"]["soil_m_v"] = mat_data_GIS_dict["hydraulic_soil_m_v"].get()

					# hydraulic - max_surface_storage
					if len(mat_data_GIS_dict["hydraulic_max_surface_storage"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==False and is_float(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==False): 
						temp_mat_GIS["hydraulic"]["max_surface_storage"] = mat_data_GIS_dict["hydraulic_max_surface_storage"].get()
					elif len(mat_data_GIS_dict["hydraulic_max_surface_storage"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==True or is_float(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==True):	
						temp_mat["1"]["hydraulic"]["max_surface_storage"] = mat_data_GIS_dict["hydraulic_max_surface_storage"].get()
			
					# slope_stability - unit_weight
					if len(mat_data_GIS_dict["soil_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_unit_weight"].get())==False and is_float(mat_data_GIS_dict["soil_unit_weight"].get())==False): 
						temp_mat_GIS["soil"]["unit_weight"] = mat_data_GIS_dict["soil_unit_weight"].get()
					elif len(mat_data_GIS_dict["soil_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_unit_weight"].get())==True or is_float(mat_data_GIS_dict["soil_unit_weight"].get())==True):	
						temp_mat["1"]["soil"]["unit_weight"] = mat_data_GIS_dict["soil_unit_weight"].get()
			
					# slope_stability - phi
					if len(mat_data_GIS_dict["soil_phi"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi"].get())==False and is_float(mat_data_GIS_dict["soil_phi"].get())==False): 
						temp_mat_GIS["soil"]["phi"] = mat_data_GIS_dict["soil_phi"].get()
					elif len(mat_data_GIS_dict["soil_phi"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi"].get())==True or is_float(mat_data_GIS_dict["soil_phi"].get())==True):	
						temp_mat["1"]["soil"]["phi"] = mat_data_GIS_dict["soil_phi"].get()
			
					# slope_stability - phi_b
					if len(mat_data_GIS_dict["soil_phi_b"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi_b"].get())==False and is_float(mat_data_GIS_dict["soil_phi_b"].get())==False): 
						temp_mat_GIS["soil"]["phi_b"] = mat_data_GIS_dict["soil_phi_b"].get()
					elif len(mat_data_GIS_dict["soil_phi_b"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi_b"].get())==True or is_float(mat_data_GIS_dict["soil_phi_b"].get())==True):	
						temp_mat["1"]["soil"]["phi_b"] = mat_data_GIS_dict["soil_phi_b"].get()

					# slope_stability - c
					if len(mat_data_GIS_dict["soil_c"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_c"].get())==False and is_float(mat_data_GIS_dict["soil_c"].get())==False): 
						temp_mat_GIS["soil"]["c"] = mat_data_GIS_dict["soil_c"].get()
					elif len(mat_data_GIS_dict["soil_c"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_c"].get())==True or is_float(mat_data_GIS_dict["soil_c"].get())==True):	
						temp_mat["1"]["soil"]["c"] = mat_data_GIS_dict["soil_c"].get()


					json_yaml_input_data["material"] = temp_mat
					json_yaml_input_data["material_GIS"] = temp_mat_GIS

				######################################
				## generate YAML file and save in input directory
				######################################
				with open(output_folder_str.get()+'/'+project_name_str.get()+'_3DTSP_input.yaml', 'w') as yaml_file:
					yaml.safe_dump(json_yaml_input_data, yaml_file, default_flow_style=None, sort_keys=False)

				######################################
				## generate bat and bash file to run 
				######################################
				run_bash_script = "#!/bin/bash\n\n"
				run_bat_script = "@echo off\n\n"

				run_python_code = '\"' + '.\\main_3DTSP_v20250813.py\" \"'+ project_name_str.get()+'_input.yaml'+'\"' 

				run_bash_script += f"python3 {run_python_code}\n"
				run_bat_script += f"python {run_python_code} && pause && exit \n"

				run_bash_script += f"\necho 3DTSP simulation of {project_name_str.get()+'_input.yaml'} completed\n"
				with open(output_folder_str.get()+'/'+f'run_3DTSP_{project_name_str.get()}.sh', 'w') as f:
					f.write(run_bash_script)

				run_bat_script += f"\necho 3DTSP simulation of {project_name_str.get()+'_input.yaml'} completed\n"
				with open(output_folder_str.get()+'/'+f'run_3DTSP_{project_name_str.get()}.bat', 'w') as f:
					f.write(run_bat_script)

				######################################
				## copy paste the main_3DTS script
				######################################
				shutil.copy(r"./main_3DTSP_v20250813.py", output_folder_str.get()+r"./main_3DTSP_v20250813.py")


		##########################################
		## for 3DPLS
		##########################################
		elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]:

			#####################
			## generate dictionary hold input file 
			#####################
			json_yaml_input_data = {
				"directories": {},
				"gis_files" : {},
				"gis_config" : {},
				"rainfall" : {},
				"monte_carlo" : {},
				"analysis" : {},
				"zmax_parameters" : {},
				"multiprocessing" : {},
				"soil_parameters" : {},
				"ellipsoid" : {},
				"investigation" : {},
				"project" : {}
			}

			# assign relative path from the bash or batch script
			json_yaml_input_data['directories']["input_folder"] = output_folder_str.get()+"/3DPLS/03-Input/"
			json_yaml_input_data['directories']["output_folder"] = output_folder_str.get()+"/3DPLS/04-Results/"
			json_yaml_input_data['directories']["matrix_storage"] = output_folder_str.get()+"/3DPLS/04-Results/matrices/"
			json_yaml_input_data['directories']["gis_data_folder"] = output_folder_str.get()+"/3DPLS/GIS/"

			# generate an empty folder in the input directory
			if not os.path.exists(output_folder_str.get()+"/3DPLS/03-Input/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/03-Input/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/04-Results/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/04-Results/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/Matrix/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/Matrix/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/04-Results/matrices/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/04-Results/matrices/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/Codes/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/Codes/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/GIS/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/GIS/")

			# move any ascii GIS data in input_folder_str.get() into output_folder_str.get()+"/3DPLS/GIS/"
			for file in os.listdir(input_folder_str.get()):
				if file.endswith(".asc"):
					shutil.copy(os.path.join(input_folder_str.get(), file), os.path.join(output_folder_str.get()+"/3DPLS/GIS/", file))

			#####################
			## project name 
			#####################
			json_yaml_input_data['project']["filename"] = project_name_str.get()
   
			#####################
			## gis files (gis_files, gis_config, zmax_parameters)
			#####################
   
			########## DEM ##########
			json_yaml_input_data["gis_files"]["dem"] = DEM_filename_str.get()

			########## array information ##########
			DEM_surface, nodata_value, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, dx_dp, dy_dp, _ = m3DTSP.read_GIS_data(DEM_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=True)

			json_yaml_input_data["gis_config"]["nodata_value"] = nodata_value
			json_yaml_input_data["gis_config"]["read_nodata_from_file"] = True

			########## RiZero from file ##########
			if len(rizero_GIS_filename_str.get()) > 0:
				json_yaml_input_data["gis_files"]["rizero"] = rizero_GIS_filename_str.get()

			# RiZero from uniform value
			else: 
				RiZero_2D = np.ones(DEM_surface.shape)*rizero_value_double.get()
				m3DTSP.data_mesh2asc(RiZero_2D, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"rizero", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["rizero"] = "rizero.asc"

			########## slope and aspect ##########
			# from file name
			if (surf_dip_filename_str.get() != "(optional)" and len(surf_dip_filename_str.get()) > 0) and (surf_aspect_filename_str.get() != "(optional)" and len(surf_aspect_filename_str.get()) > 0):
				json_yaml_input_data["gis_files"]["slope"] = surf_dip_filename_str.get()
				json_yaml_input_data["gis_files"]["aspect"] = surf_aspect_filename_str.get()
				json_yaml_input_data["gis_files"]["dir"] = surf_aspect_filename_str.get()

				dip_surf, _, _ = m3DTSP.read_GIS_data(surf_dip_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)

			# slope and aspect computed from DEM
			elif (surf_dip_filename_str.get() == "(optional)" or len(surf_dip_filename_str.get()) == 0) and (surf_aspect_filename_str.get() == "(optional)" or len(surf_aspect_filename_str.get()) == 0):
				DEM_soil_thickness = np.ones(DEM_surface.shape).astype(np.int32)
				DEM_base = DEM_surface - DEM_soil_thickness
    
				dip_surf, aspect_surf, _, _ = m3DTSP.compute_dip_aspect(DEM_surface, DEM_base, DEM_soil_thickness, DEM_noData, gridUniqueX, gridUniqueY, local_cell_DEM2dip_int.get(), 2, max_CPU_pool_int.get())

				m3DTSP.data_mesh2asc(dip_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"slope", user_nodata_value=nodata_value, fmt="%.6f")
				m3DTSP.data_mesh2asc(aspect_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"aspect", user_nodata_value=nodata_value, fmt="%.6f")
				m3DTSP.data_mesh2asc(aspect_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"dir", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["slope"] = "slope.asc"
				json_yaml_input_data["gis_files"]["aspect"] = "aspect.asc"
				json_yaml_input_data["gis_files"]["dir"] = "dir.asc"

			########### zone ##########
			json_yaml_input_data["gis_files"]["zones"] = output_format_opt_str.get()

			if mat_assign_opt_str.get() == "Uniform":
				matID_array = np.ones(DEM_surface.shape).astype(int)
				m3DTSP.data_mesh2asc(matID_array, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zones", user_nodata_value=nodata_value, fmt="%.0f")
				json_yaml_input_data["gis_files"]["zones"] = "zones.asc"    # material ID on DEM cells

			elif mat_assign_opt_str.get() == "Zone-Based":
				json_yaml_input_data["gis_files"]["zones"] = mat_zone_filename_str.get()
   
			########## zmax ##########
			if soil_depth_probabilistic_check_int.get() == 1:  # for any probabilistic

				DEM_soil_thickness = -2.578*np.tan(np.radians(dip_surf)) + 2.612
				DEM_soil_thickness = DEM_soil_thickness * ( np.ones(DEM_soil_thickness.shape) + soil_depth_probabilistic_cov.get() * np.random.normal(0, 1, size=(DEM_soil_thickness.shape)) )
				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"/zmax", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "Yes"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = soil_depth_probabilistic_cov.get()
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = min_soil_depth_double.get()
   
			elif soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 0:
				DEM_soil_thickness = np.ones(DEM_surface.shape)*uniform_soil_depth_double.get()
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc" 
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 0:
				json_yaml_input_data["gis_files"]["zmax"] = GIS_soil_depth_str.get()
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 0:
				DEM_soil_thickness = -2.578*np.tan(np.radians(dip_surf)) + 2.612
				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "Yes"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0
    
			elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 0:

				DEM_soil_thickness = np.ones((DEM_surface.shape)) * gen_reg_intercept_double.get()   

				if len(gen_reg_param1_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param1_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param1_double.get()
				if len(gen_reg_param2_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param2_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param2_double.get()
				if len(gen_reg_param3_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param3_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param3_double.get()
				if len(gen_reg_param4_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param4_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param4_double.get()
				if len(gen_reg_param5_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param5_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param5_double.get()
				if len(gen_reg_param6_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param6_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param6_double.get()
				if len(gen_reg_param7_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param7_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param7_double.get()
				if len(gen_reg_param8_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param8_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param8_double.get()
				if len(gen_reg_param9_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param9_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param9_double.get()
				if len(gen_reg_param10_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param10_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param10_double.get()

				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
       
				DEM_soil_thickness = np.ones((DEM_surface.shape)) * gen_reg_intercept_double.get()

				if len(gen_reg_param1_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param1_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param1_double.get())
				if len(gen_reg_param2_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param2_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param2_double.get())
				if len(gen_reg_param3_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param3_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param3_double.get())
				if len(gen_reg_param4_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param4_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param4_double.get())
				if len(gen_reg_param5_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param5_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param5_double.get())
				if len(gen_reg_param6_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param6_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param6_double.get())
				if len(gen_reg_param7_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param7_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param7_double.get())
				if len(gen_reg_param8_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param8_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param8_double.get())
				if len(gen_reg_param9_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param9_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param9_double.get())
				if len(gen_reg_param10_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param10_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param10_double.get())

				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0   
   
			########## post-processing with 3DPLS ##########
			if landslide_source_filename_str.get() != "(optional)" and len(landslide_source_filename_str.get()) > 0:
				json_yaml_input_data["gis_files"]["source"] = output_format_opt_str.get()

			########## groundwater table ##########
			if groundwater_opt_str.get() == "GWT elevation GIS":
				if len(gwt_GIS_filename_str.get()) > 0:
					json_yaml_input_data["gis_files"]["depthwt"] = gwt_GIS_filename_str.get()
			else:
				if groundwater_opt_str.get() == "Thickness Above Bedrock":
					ground_water_model = 0
				elif groundwater_opt_str.get() == "Depth From Surface":
					ground_water_model = 1
				elif groundwater_opt_str.get() == "% of Soil Thickness Above Bedrock":
					ground_water_model = 2 
				elif groundwater_opt_str.get() == "% of Soil Thickness From Surface":
					ground_water_model = 3
    
				if len(gwt_GIS_filename_str.get()) == 0:			
					ground_water_data = gwt_value_double.get()
				elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:			
					ground_water_data = gwt_GIS_filename_str.get()

				DEM_base = DEM_surface - DEM_soil_thickness

				DEM_gwt_z, gwt_depth_from_surf = m3DTSP.generate_groundwater_GIS_data(output_folder_str.get()+"/3DPLS/GIS/", ground_water_model, ground_water_data, DEM_surface, DEM_base, DEM_soil_thickness)

				m3DTSP.data_mesh2asc(gwt_depth_from_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"depthwt", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["depthwt"] = "depthwt.asc"

			#####################
			## rainfall - uniform
			#####################
			""" NOTE: Iverson can only do uniform deterministic rainfall, so if anything else, compute the average rainfall over time and for given location """
			rainfall_intensity_sum = 0.0  # unit based on rainfall_intensity_unit_str.get()
			rainfall_time_unit_count = 0
			rainfall_time_max = 0   # unit based on rainfall_intensity_unit_str.get()
			
			for rain_t in range(1, 101):
				# check if empty
				if (rain_hist_t_dict[rain_t][0].get() == 0 and rain_hist_t_dict[rain_t][1].get() == 0) or (rainfall_history_opt_str.get() == "Uniform" and rain_hist_t_dict[rain_t][2][0] == 0) or (rainfall_history_opt_str.get() == "GIS file" and len(rain_hist_t_dict[rain_t][2][1].get()) == 0) or (rainfall_history_opt_str.get() in ["Deterministic Rainfall Gauge", "Probabilistic Rainfall Gauge"] and (rain_hist_t_dict[rain_t][2][2][0][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][1][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][2][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][3][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][4][2].get() == 0)):
					continue    

				# uniform rainfall
				if rainfall_history_opt_str.get() == "Uniform":
					rainfall_intensity_sum += rain_hist_t_dict[rain_t][2][0].get()*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += (rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

				# GIS file containing intensity
				elif rainfall_history_opt_str.get() == "GIS file":
					rain_I, nodata_value, rain_noData = m3DTSP.read_GIS_data(rain_hist_t_dict[rain_t][2][1].get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					rain_I_filter = np.where(np.logical_or(rain_noData==0, DEM_noData==0), 0, rain_I)
					rainfall_intensity_sum += np.sum(rain_I_filter)*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += int(np.sum(rain_noData))*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

				# get intensity from the nearest rainfall gauge measurement
				# even when using probabilistic rainfall, assume their cells are large to tend towards mean
				elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge" or rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":

					# format: [[X, Y, intensity], ...]
					xx, yy = np.meshgrid(gridUniqueX, gridUniqueY)
					xGrids = np.ravel(xx)
					yGrids = np.ravel(yy)

					gauge_xy_list = []
					gauge_I_list = []
					for gauge in range(5):
						if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0:
							gauge_xy_list.append([rain_hist_t_dict[rain_t][2][2][gauge][0].get(), rain_hist_t_dict[rain_t][2][2][gauge][1].get()])
							gauge_I_list.append([rain_hist_t_dict[rain_t][2][2][gauge][2].get()])

					interp_nearest_I_data = griddata(np.array(gauge_xy_list), np.array(gauge_I_list), (xGrids, yGrids), method='nearest')
					rain_I = np.reshape(interp_nearest_I_data, (len(gridUniqueY), len(gridUniqueX)))
					rain_I_filter = np.where(DEM_noData==0, 0, rain_I)

					rainfall_intensity_sum += np.sum(rain_I_filter)*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += int(np.sum(DEM_noData))*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

			rainfall_intensity_av = rainfall_intensity_sum/rainfall_time_unit_count

			# convert all length to m, time to s for rainfall history in 3DPLS
			rainfall_intensity_unit = rainfall_intensity_unit_str.get()
			length_unit, time_unit = rainfall_intensity_unit.split("/")

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

			# store
			json_yaml_input_data["rainfall"]["riInp"] = rainfall_intensity_av*convert_intensity
			json_yaml_input_data["rainfall"]["riInp_duration"] = rainfall_time_max*convert_time

			#####################
			## MONTE CARLO AND ANALYSIS CONFIGURATION
			#####################
			# monte carlo
			json_yaml_input_data["monte_carlo"]["mcnumber"] = mc_iterations_int.get()

			# analysis information
			json_yaml_input_data["analysis"]["analysis_type"] = analysis_opt_3DPLS_str.get()

			if slope_model_str.get() == "3D Normal":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Normal3D"
			elif slope_model_str.get() == "3D Bishop":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Bishop3D"
			elif slope_model_str.get() == "3D Janbu":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Janbu3D"

			json_yaml_input_data["analysis"]["random_field_method"] = random_field_method_str.get()
			json_yaml_input_data["analysis"]["save_mat"] = "YES"   # set them as default
			json_yaml_input_data["analysis"]["problem_name"] = ""

			# ellipsoidal slip surface
			json_yaml_input_data["ellipsoid"]["ella"] = ellipsoidal_slip_surface_a_double.get()
			json_yaml_input_data["ellipsoid"]["ellb"] = ellipsoidal_slip_surface_b_double.get()
			json_yaml_input_data["ellipsoid"]["ellc"] = ellipsoidal_slip_surface_c_double.get()
			json_yaml_input_data["ellipsoid"]["ellz"] = ellipsoidal_slip_surface_z_double.get()
			if ellipsoidal_slip_surface_alpha_comp_int.get() == 1:
				json_yaml_input_data["ellipsoid"]["ellalpha_calc"] = "Yes"
				json_yaml_input_data["ellipsoid"]["ellalpha"] = 0.0
			elif ellipsoidal_slip_surface_alpha_comp_int.get() == 0:
				json_yaml_input_data["ellipsoid"]["ellalpha_calc"] = "No"
				json_yaml_input_data["ellipsoid"]["ellalpha"] = ellipsoidal_slip_surface_alpha_double.get()

			# investigation
			if inzone_check_int.get() == 1:  # compute inzone automatically from DEM
				json_yaml_input_data["investigation"]["inzone"] = [[0, len(gridUniqueY)-1], [0, len(gridUniqueX)-1]]
			elif inzone_check_int.get() == 0:  # get from manual data
				json_yaml_input_data["investigation"]["inzone"] = [[inzone_min_i_int.get(), inzone_max_i_int.get()], [inzone_min_j_int.get(), inzone_max_j_int.get()]]

			if intime_check_int.get() == 1 or len(intime_str.get()) == 0:  # compute automatically
				json_yaml_input_data["investigation"]["time_to_analyse"] = [rainfall_time_max*convert_time]
			elif intime_check_int.get() == 0 and len(intime_str.get()) > 0:  # get from manual data
				temp_intime = intime_str.get().split(",")
				temp_intime = [float(p1.strip())*convert_time for p1 in temp_intime]  # strip all whitespaces and convert units
				json_yaml_input_data["investigation"]["time_to_analyse"] = temp_intime[:]

			json_yaml_input_data["investigation"]["sub_dis_num"] = max(int(ellipsoidal_slip_surface_min_sub_div_int.get()), 0)

			#####################
			## multiprocessing
			#####################
			if multi_CPU_method_opt_int.get() >= 1:
				json_yaml_input_data["multiprocessing"]["multiprocessing_option"] = "S-MP-MP" # multi_CPU_method_str.get()
				json_yaml_input_data["multiprocessing"]["total_processes_mc"] = max_CPU_pool_int.get()  # MP_1st_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_ell"] = max_CPU_pool_int.get()  # MP_2nd_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_threads_ell"] = max_CPU_pool_int.get()  # MT_2nd_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_indmc"] = max_CPU_pool_int.get()  # MP_1st_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_ellgen"] = max_CPU_pool_int.get()  # MP_2nd_CPU_pool_int.get()
			else:
				json_yaml_input_data["multiprocessing"]["multiprocessing_option"] = "S-SP-SP"
				json_yaml_input_data["multiprocessing"]["total_processes_mc"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_ell"] = 1
				json_yaml_input_data["multiprocessing"]["total_threads_ell"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_indmc"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_ellgen"] = 1


			#####################
			## material
			#####################
			zone_mat_param_temp = {
				# Cohesion parameters (Pa) - user assigned kPa
				"cohesion": {
					"mean_cInp": 0.0,
					"cov_cInp": 0.0,
					"dist_cInp": "Normal",
					"corrLenX_cInp": 'inf', 
					"corrLenY_cInp": 'inf' 
				},
				# Friction angle parameters (deg)
				"friction_angle": {
					"mean_phiInp": 0.0,
					"cov_phiInp": 0.0,
					"dist_phiInp": "Normal",
					"corrLenX_phiInp": 'inf',
					"corrLenY_phiInp": 'inf'
				},
				# Unit weight parameters (N/m3) - user assigned kN/m3
				"unit_weight": {
					"mean_uwsInp": 0.0, 
					"cov_uwsInp": 0.0, 
					"dist_uwsInp": "Normal",
					"corrLenX_uwsInp": 'inf',
					"corrLenY_uwsInp": 'inf'
				},
				# Saturated permeability parameters (m/s)
				"saturated_permeability": {
					"mean_kSatInp": 0.0,
					"cov_kSatInp": 0.0,
					"dist_kSatInp": "Normal",
					"corrLenX_kSatInp": 'inf',
					"corrLenY_kSatInp": 'inf'
				},
				# Diffusivity parameters (m2/s)
				"diffusivity": {
					"mean_diffusInp": 0.0,
					"cov_diffusInp": 0.0,
					"dist_diffusInp": "Lognormal",
					"corrLenX_diffusInp": 'inf',
					"corrLenY_diffusInp": 'inf'
				},
				# Undrained shear strength (for undrained analysis) (Pa) - user assigned kPa
				"undrained_shear_strength": {
					"mean_SuInp": 0.0,
					"cov_SuInp": 0.0,
					"dist_SuInp": "Normal",
					"corrLenX_SuInp": 'inf',
					"corrLenY_SuInp": 'inf'
				}
			}
		
			# uniform asignment
			if mat_assign_opt_str.get() == "Uniform" or num_mat_int.get() == 1:
				mID_max = 1
			elif mat_assign_opt_str.get() == "Zone-Based" and num_mat_int.get() > 1:
				mID_max = int(num_mat_int.get())

			for mID in range(1, 1+mID_max):

				zone_mat_param_template = deepcopy(zone_mat_param_temp)

				# deterministic
				if mc_iterations_int.get() == 1:
					zone_mat_param_template['cohesion']['mean_cInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['friction_angle']['mean_phiInp'] = mat_data_dict[mID]["soil_phi"][0].get()
					zone_mat_param_template['unit_weight']['mean_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][0].get()*1000.0
					zone_mat_param_template['saturated_permeability']['mean_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][0].get()
					zone_mat_param_template['diffusivity']['mean_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][0].get()
					zone_mat_param_template['undrained_shear_strength']['mean_SuInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0

				# Monte Carlo probabilistic
				elif mc_iterations_int.get() > 1:
					zone_mat_param_template['cohesion']['mean_cInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['cohesion']['cov_cInp'] = mat_data_dict[mID]["soil_c"][1].get()
					zone_mat_param_template['cohesion']['dist_cInp'] = "Normal" if mat_data_dict[mID]["soil_c"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_c"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal" 
					zone_mat_param_template['cohesion']['corrLenX_cInp'] = "inf" if mat_data_dict[mID]["soil_c"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][3].get()) if is_int(mat_data_dict[mID]["soil_c"][3].get()) else float(mat_data_dict[mID]["soil_c"][3].get()) if is_float(mat_data_dict[mID]["soil_c"][3].get()) else mat_data_dict[mID]["soil_c"][3].get()
					zone_mat_param_template['cohesion']['corrLenY_cInp'] = "inf" if mat_data_dict[mID]["soil_c"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][4].get()) if is_int(mat_data_dict[mID]["soil_c"][4].get()) else float(mat_data_dict[mID]["soil_c"][4].get()) if is_float(mat_data_dict[mID]["soil_c"][4].get()) else mat_data_dict[mID]["soil_c"][4].get()

					zone_mat_param_template['friction_angle']['mean_phiInp'] = mat_data_dict[mID]["soil_phi"][0].get()
					zone_mat_param_template['friction_angle']['cov_phiInp'] = mat_data_dict[mID]["soil_phi"][1].get()
					zone_mat_param_template['friction_angle']['dist_phiInp'] = "Normal" if mat_data_dict[mID]["soil_phi"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_phi"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['friction_angle']['corrLenX_phiInp'] = "inf" if mat_data_dict[mID]["soil_phi"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_phi"][3].get()) if is_int(mat_data_dict[mID]["soil_phi"][3].get()) else float(mat_data_dict[mID]["soil_phi"][3].get()) if is_float(mat_data_dict[mID]["soil_phi"][3].get()) else mat_data_dict[mID]["soil_phi"][3].get()
					zone_mat_param_template['friction_angle']['corrLenY_phiInp'] = "inf" if mat_data_dict[mID]["soil_phi"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_phi"][4].get()) if is_int(mat_data_dict[mID]["soil_phi"][4].get()) else float(mat_data_dict[mID]["soil_phi"][4].get()) if is_float(mat_data_dict[mID]["soil_phi"][4].get()) else mat_data_dict[mID]["soil_phi"][4].get()

					zone_mat_param_template['unit_weight']['mean_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][0].get()*1000.0
					zone_mat_param_template['unit_weight']['cov_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][1].get()
					zone_mat_param_template['unit_weight']['dist_uwsInp'] = "Normal" if mat_data_dict[mID]["soil_unit_weight"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_unit_weight"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['unit_weight']['corrLenX_uwsInp'] = "inf" if mat_data_dict[mID]["soil_unit_weight"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_unit_weight"][3].get()) if is_int(mat_data_dict[mID]["soil_unit_weight"][3].get()) else float(mat_data_dict[mID]["soil_unit_weight"][3].get()) if is_float(mat_data_dict[mID]["soil_unit_weight"][3].get()) else mat_data_dict[mID]["soil_unit_weight"][3].get()
					zone_mat_param_template['unit_weight']['corrLenY_uwsInp'] = "inf" if mat_data_dict[mID]["soil_unit_weight"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_unit_weight"][4].get()) if is_int(mat_data_dict[mID]["soil_unit_weight"][4].get()) else float(mat_data_dict[mID]["soil_unit_weight"][4].get()) if is_float(mat_data_dict[mID]["soil_unit_weight"][4].get()) else mat_data_dict[mID]["soil_unit_weight"][4].get()

					zone_mat_param_template['saturated_permeability']['mean_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][0].get()
					zone_mat_param_template['saturated_permeability']['cov_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][1].get()
					zone_mat_param_template['saturated_permeability']['dist_kSatInp'] = "Normal" if mat_data_dict[mID]["hydraulic_k_sat"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["hydraulic_k_sat"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['saturated_permeability']['corrLenX_kSatInp'] = "inf" if mat_data_dict[mID]["hydraulic_k_sat"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) if is_int(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) else float(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) if is_float(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) else mat_data_dict[mID]["hydraulic_k_sat"][3].get()
					zone_mat_param_template['saturated_permeability']['corrLenY_kSatInp'] = "inf" if mat_data_dict[mID]["hydraulic_k_sat"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) if is_int(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) else float(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) if is_float(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) else mat_data_dict[mID]["hydraulic_k_sat"][4].get()

					zone_mat_param_template['diffusivity']['mean_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][0].get()
					zone_mat_param_template['diffusivity']['cov_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][1].get()
					zone_mat_param_template['diffusivity']['dist_diffusInp'] = "Normal" if mat_data_dict[mID]["hydraulic_diffusivity"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["hydraulic_diffusivity"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['diffusivity']['corrLenX_diffusInp'] = "inf" if mat_data_dict[mID]["hydraulic_diffusivity"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) if is_int(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) else float(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) if is_float(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) else mat_data_dict[mID]["hydraulic_diffusivity"][3].get()
					zone_mat_param_template['diffusivity']['corrLenY_diffusInp'] = "inf" if mat_data_dict[mID]["hydraulic_diffusivity"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) if is_int(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) else float(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) if is_float(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) else mat_data_dict[mID]["hydraulic_diffusivity"][4].get()

					zone_mat_param_template['undrained_shear_strength']['mean_SuInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['undrained_shear_strength']['cov_SuInp'] = mat_data_dict[mID]["soil_c"][1].get()
					zone_mat_param_template['undrained_shear_strength']['dist_SuInp'] = "Normal" if mat_data_dict[mID]["soil_c"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_c"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal" 
					zone_mat_param_template['undrained_shear_strength']['corrLenX_SuInp'] = "inf" if mat_data_dict[mID]["soil_c"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][3].get()) if is_int(mat_data_dict[mID]["soil_c"][3].get()) else float(mat_data_dict[mID]["soil_c"][3].get()) if is_float(mat_data_dict[mID]["soil_c"][3].get()) else mat_data_dict[mID]["soil_c"][3].get()
					zone_mat_param_template['undrained_shear_strength']['corrLenY_SuInp'] = "inf" if mat_data_dict[mID]["soil_c"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][4].get()) if is_int(mat_data_dict[mID]["soil_c"][4].get()) else float(mat_data_dict[mID]["soil_c"][4].get()) if is_float(mat_data_dict[mID]["soil_c"][4].get()) else mat_data_dict[mID]["soil_c"][4].get()

				# add data
				json_yaml_input_data["soil_parameters"][f"zone_{mID}"] = deepcopy(zone_mat_param_template)

			######################################
			## generate YAML file and save in input directory
			######################################
			with open(output_folder_str.get()+'/3DPLS/03-Input/'+'input_3DPLS.yaml', 'w') as yaml_file:
				yaml.safe_dump(json_yaml_input_data, yaml_file, default_flow_style=None, sort_keys=False)

			######################################
			## generate bat and bash file to run 
			######################################
			run_bash_script = "#!/bin/bash\n\n"
			run_bat_script = "@echo off\n\n"

			run_python_code = '\"' + '.\\Codes\\Main_3DPLS_v1_1_yaml.py\" \"'

			run_bash_script += f"python3 {run_python_code}\n"
			run_bat_script += f"python {run_python_code} && pause && exit \n"

			run_bash_script += f"\necho 3DPLS simulation of {project_name_str.get()} completed\n"
			with open(output_folder_str.get()+'/3DPLS/'+f'run_3DPLS_{project_name_str.get()}.sh', 'w') as f:
				f.write(run_bash_script)

			run_bat_script += f"\necho 3DPLS simulation of {project_name_str.get()} completed\n"
			with open(output_folder_str.get()+'/3DPLS/'+f'run_3DPLS_{project_name_str.get()}.bat', 'w') as f:
				f.write(run_bat_script)

			######################################
			## copy paste the 3DPLS scripts
			######################################
			shutil.copy(r"./Main_3DPLS_v1_1_yaml.py", output_folder_str.get()+"/3DPLS/Codes/"+r"./Main_3DPLS_v1_1_yaml.py")
			shutil.copy(r"./Functions_3DPLS_v1_1.py", output_folder_str.get()+"/3DPLS/Codes/"+r"./Functions_3DPLS_v1_1.py")

		######################################
		## status
		######################################
		status.config(text = "generated input YAML, bash, and bat scripts for running ")


	def start_simulation_command():

		##########################################
		## for 3DTS
		##########################################
		if (slope_model_str.get() in ["Skip (only perform infiltration)", "Infinite Slope", "3D Translational Slide (3DTS)"]):

			#####################
			## restart simulations from previously runned files
			#####################
			if overall_input_folder_str.get() != "" and (".json" in overall_input_folder_str.get() or ".JSON" in overall_input_folder_str.get() or ".yaml" in overall_input_folder_str.get() or ".YAML" in overall_input_folder_str.get() or ".yml" in overall_input_folder_str.get() or ".YML" in overall_input_folder_str.get()):

				# only the filename
				file_path_name = overall_input_folder_str.get() 
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				######################################
				## open subprocess and start simulation
				######################################
				## check the operative system
				opsys = system()
				if not opsys in ["Windows", "Linux", "Darwin"]:
					print("Operating system {:s} not supported.\n".format(opsys))
					sys.exit(1)
					
				## write the cmd or terminal command line to run the 3DTS simulation
				run_python_code = '\".\\main_3DTSP_v20250813.py\" \"'+overall_input_folder_str.get()+'\"' 

				status.config(text = "simulation running ")

				## open new terminal or cmd to run 3DTS simulation
				if opsys == "Windows":  # cmd in windows
					popen_cmd_code = "python "+run_python_code+" && pause && exit"
					proc = subprocess.Popen(popen_cmd_code, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')

				elif system() == "Linux": # Linux use #!/usr/bin/python3	
					popen_terminal_code = "python3 "+run_python_code
					proc = subprocess.Popen(popen_terminal_code, shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')
				
				elif system() == "Darwin":  # MacOS
					popen_terminal_code = "python3 "+run_python_code
					proc = subprocess.Popen(popen_terminal_code, shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')
				
				while proc.poll() is None:
					pass

				proc.kill()     # close terminal to finish
				errX = proc.communicate()[1]  # export error message - for potential debugging

				# Compare the metadata of all files
				if errX == '':     # no error
					print("All 3DTSP simulation is complete! Check the results or simulation state")
				else:     # some sort of error occurred
					print("3DTSP simulation had error and terminated.\nError message:"+errX)

				status.config(text = "simulation finished ")

				return None

			#####################
			## generate dictionary hold input file 
			#####################
			else:
				json_yaml_input_data = {}

				json_yaml_input_data["filename"] = project_name_str.get()

				# assign relative path from the bash or batch script
				json_yaml_input_data["input_folder_path"] = f"{input_folder_str.get()}"
				json_yaml_input_data["output_folder_path"] = f"{output_folder_str.get()}/{project_name_str.get()}_results/"

				# generate an empty folder in the output directory
				if not os.path.exists(output_folder_str.get()+f"/{project_name_str.get()}_results/"):
					os.makedirs(output_folder_str.get()+f"/{project_name_str.get()}_results/")

				json_yaml_input_data["restarting_simulation_JSON"] = None 
				if overall_input_folder_str.get() != "" and (".json" in overall_input_folder_str.get() or ".JSON" in overall_input_folder_str.get()):
					json_yaml_input_data["restarting_simulation_JSON"] = overall_input_folder_str.get()

				json_yaml_input_data["results_format"] = output_format_opt_str.get()

				if generate_plot_opt_int.get() == 1:
					json_yaml_input_data["generate_plot"] = True
				else:
					json_yaml_input_data["generate_plot"] = False

				json_yaml_input_data["unit_weight_of_water"] = unit_weight_water_double.get()

				json_yaml_input_data["FS_crit"] = critical_FS_double.get()

				json_yaml_input_data["monte_carlo_iteration_max"] = mc_iterations_int.get()

				json_yaml_input_data["vertical_spacing"] = soil_dz_double.get()

				json_yaml_input_data["termination_apply"] = False
				json_yaml_input_data["after_termination_new_times_apply"] = False

				if surf_dip_for_GA_int.get() == 1:
					json_yaml_input_data["DEM_surf_dip_infiltraion_apply"] = True
				else:
					json_yaml_input_data["DEM_surf_dip_infiltraion_apply"] = False

				if debris_flow_criteria_int.get() == 1:
					json_yaml_input_data["DEM_debris_flow_criteria_apply"] = True
				else:		
					json_yaml_input_data["DEM_debris_flow_criteria_apply"] = False
				
				if slope_model_str.get() == "Skip (only perform infiltration)": 
					json_yaml_input_data["FS_analysis_method"] = None 
					json_yaml_input_data["cell_size_3DFS_min"] = None
					json_yaml_input_data["cell_size_3DFS_max"] = None
					json_yaml_input_data["superellipse_power"] = None
					json_yaml_input_data["superellipse_eccentricity_ratio"] = None
					json_yaml_input_data["3D_FS_iteration_limit"] = None
					json_yaml_input_data["3D_FS_convergence_tolerance"] = None
					json_yaml_input_data["apply_side_resistance_3D"] = None
					json_yaml_input_data["apply_root_resistance_3D"] = None

				elif slope_model_str.get() == "Infinite Slope":
					json_yaml_input_data["FS_analysis_method"] = "infinite" 
					json_yaml_input_data["cell_size_3DFS_min"] = 1
					json_yaml_input_data["cell_size_3DFS_max"] = 1
					json_yaml_input_data["superellipse_power"] = 100
					json_yaml_input_data["superellipse_eccentricity_ratio"] = 1
					json_yaml_input_data["3D_FS_iteration_limit"] = 1
					json_yaml_input_data["3D_FS_convergence_tolerance"] = 0.001
					json_yaml_input_data["apply_side_resistance_3D"] = False
					json_yaml_input_data["apply_root_resistance_3D"] = False

				elif slope_model_str.get() == "3D Translational Slide (3DTS)":
					json_yaml_input_data["FS_analysis_method"] = "3D Janbu" 
					json_yaml_input_data["cell_size_3DFS_min"] = min_cell_3DTS_int.get()
					json_yaml_input_data["cell_size_3DFS_max"] = max_cell_3DTS_int.get()

					temp_super_power1 = superellipse_power_3DTS_str.get().split(",")
					temp_super_power2 = [float(p1.strip()) for p1 in temp_super_power1]  # strip all whitespaces

					temp_eccen_ratio1 = superellipse_eccen_ratio_3DTS_str.get().split(",")
					temp_eccen_ratio2 = [float(ec1.strip()) for ec1 in temp_eccen_ratio1]  # strip all whitespaces

					json_yaml_input_data["superellipse_power"] = temp_super_power2[:]
					json_yaml_input_data["superellipse_eccentricity_ratio"] = temp_eccen_ratio2[:]
					json_yaml_input_data["3D_FS_iteration_limit"] = 30
					json_yaml_input_data["3D_FS_convergence_tolerance"] = 0.005

					if side_resistance_3DTS_int.get() == 1:
						json_yaml_input_data["apply_side_resistance_3D"] = True 
					else:
						json_yaml_input_data["apply_side_resistance_3D"] = False

					if root_reinforced_model_str.get() == "None":
						json_yaml_input_data["apply_root_resistance_3D"] = False
					elif root_reinforced_model_str.get() in ["Constant with Depth", "van Zadelhoff et al. (2021)"]: 
						json_yaml_input_data["apply_root_resistance_3D"] = True

				json_yaml_input_data["DEM_UCA_compute_all"] = True

				json_yaml_input_data["max_cpu_num"] = max_CPU_pool_int.get()

				json_yaml_input_data["rain_unit"] = rainfall_intensity_unit_str.get()

				rainfall_hist_list = []
				for rain_t in range(1, 101):
					# check if empty
					if (rain_hist_t_dict[rain_t][0].get() == 0 and rain_hist_t_dict[rain_t][1].get() == 0) or (rainfall_history_opt_str.get() == "Uniform" and rain_hist_t_dict[rain_t][2][0] == 0) or (rainfall_history_opt_str.get() == "GIS file" and len(rain_hist_t_dict[rain_t][2][1].get()) == 0) or (rainfall_history_opt_str.get() in ["Deterministic Rainfall Gauge", "Probabilistic Rainfall Gauge"] and (rain_hist_t_dict[rain_t][2][2][0][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][1][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][2][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][3][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][4][2].get() == 0)):
						continue    

					if rainfall_history_opt_str.get() == "Uniform":
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), rain_hist_t_dict[rain_t][2][0].get()])
					elif rainfall_history_opt_str.get() == "GIS file":
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), rain_hist_t_dict[rain_t][2][1].get()])
					elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge":
						gauge_list = []
						for gauge in range(5):
							if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0:
								gauge_list.append([
									rain_hist_t_dict[rain_t][2][2][gauge][0].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][1].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][2].get()
								])
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), gauge_list[:]])
					elif rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":
						gauge_list = []
						for gauge in range(5):
							if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0 and (isinstance(rain_hist_t_dict[rain_t][2][2][gauge][5].get(), (int,float)) and rain_hist_t_dict[rain_t][2][2][gauge][5].get() != 0) and (isinstance(rain_hist_t_dict[rain_t][2][2][gauge][6].get(), (int, float)) and rain_hist_t_dict[rain_t][2][2][gauge][6].get() != 0):
								gauge_list.append([
									rain_hist_t_dict[rain_t][2][2][gauge][0].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][1].get(), 
									rain_hist_t_dict[rain_t][2][2][gauge][2].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][3].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][4].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][5].get(),	
									rain_hist_t_dict[rain_t][2][2][gauge][6].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][7].get(),
									rain_hist_t_dict[rain_t][2][2][gauge][8].get()
								])
						rainfall_hist_list.append([rain_hist_t_dict[rain_t][0].get(), rain_hist_t_dict[rain_t][1].get(), gauge_list[:]])
				json_yaml_input_data["rainfall_history"] = rainfall_hist_list[:]

				json_yaml_input_data["dt_iteration"] = rainfall_time_sudiv_int.get()
				
				# not implemented for 3DTS yet
				json_yaml_input_data["debris_t_max"] = 30
				json_yaml_input_data["debris_dt"] = 1
				
				json_yaml_input_data["DEM_file_name"] = DEM_filename_str.get()		

				if soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["uniform", uniform_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["GIS", GIS_soil_depth_str.get()]
				elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 0:
					json_yaml_input_data["soil_depth_data"] = ["Holm and Edvarson - Norway", min_soil_depth_double.get(), max_soil_depth_double.get()] 
				elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
					gen_soil_d = ["general multiregression", "linear", min_soil_depth_double.get(),
					max_soil_depth_double.get(), gen_reg_intercept_double.get()]
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]
				elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
					gen_soil_d = ["general multiregression", "power", min_soil_depth_double.get(),
					max_soil_depth_double.get(), gen_reg_intercept_double.get()] 
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]

				elif soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - uniform", uniform_soil_depth_double.get(), soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - GIS", GIS_soil_depth_str.get(), soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 1:
					json_yaml_input_data["soil_depth_data"] = ["prob - Holm and Edvarson - Norway", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get()]
				elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 1:
					gen_soil_d = ["prob - general multiregression", "linear", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get(), gen_reg_intercept_double.get()]
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]
				elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 1:
					gen_soil_d = ["prob - general multiregression", "power", soil_depth_probabilistic_cov.get(), min_soil_depth_double.get(), max_soil_depth_double.get(), gen_reg_intercept_double.get()] 
					if len(gen_reg_param1_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param1_filename_str.get(), gen_reg_param1_double.get()])
					if len(gen_reg_param2_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param2_filename_str.get(), gen_reg_param2_double.get()])
					if len(gen_reg_param3_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param3_filename_str.get(), gen_reg_param3_double.get()])
					if len(gen_reg_param4_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param4_filename_str.get(), gen_reg_param4_double.get()])
					if len(gen_reg_param5_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param5_filename_str.get(), gen_reg_param5_double.get()])	
					if len(gen_reg_param6_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param6_filename_str.get(), gen_reg_param6_double.get()])	
					if len(gen_reg_param7_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param7_filename_str.get(), gen_reg_param7_double.get()])		
					if len(gen_reg_param8_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param8_filename_str.get(), gen_reg_param8_double.get()])	
					if len(gen_reg_param9_filename_str.get()) > 0:	
						gen_soil_d.append([gen_reg_param9_filename_str.get(), gen_reg_param9_double.get()])
					if len(gen_reg_param10_filename_str.get()) > 0:
						gen_soil_d.append([gen_reg_param10_filename_str.get(), gen_reg_param10_double.get()])
					json_yaml_input_data["soil_depth_data"] = gen_soil_d[:]

				
				if groundwater_opt_str.get() == "Thickness Above Bedrock":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["thickness above bedrock", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:			
						json_yaml_input_data["ground_water_data"] = ["thickness above bedrock", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "Depth From Surface":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["depth from surface", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["depth from surface", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "% of Soil Thickness Above Bedrock":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness above bedrock", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness above bedrock", gwt_GIS_filename_str.get()]    
				elif groundwater_opt_str.get() == "% of Soil Thickness From Surface":
					if len(gwt_GIS_filename_str.get()) == 0:			
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness from surface", gwt_value_double.get()]
					elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:		
						json_yaml_input_data["ground_water_data"] = ["percentage of the soil thickness from surface", gwt_GIS_filename_str.get()]
				elif groundwater_opt_str.get() == "GWT elevation GIS":
					if len(gwt_GIS_filename_str.get()) > 0:
						json_yaml_input_data["ground_water_data"] = ["GWT elevation GIS", gwt_GIS_filename_str.get()]


				if surf_dip_filename_str.get() == "(optional)" or len(surf_dip_filename_str.get()) == 0:
					json_yaml_input_data["dip_surf_filename"] = None
				else:
					json_yaml_input_data["dip_surf_filename"] = surf_dip_filename_str.get()

				if surf_aspect_filename_str.get() == "(optional)" or len(surf_aspect_filename_str.get()) == 0:
					json_yaml_input_data["aspect_surf_filename"] = None
				else:
					json_yaml_input_data["aspect_surf_filename"] = surf_aspect_filename_str.get()

				if base_dip_filename_str.get() == "(optional)" or len(base_dip_filename_str.get()) == 0:
					json_yaml_input_data["dip_base_filename"] = None
				else:
					json_yaml_input_data["dip_base_filename"] = base_dip_filename_str.get()

				if base_aspect_filename_str.get() == "(optional)" or len(base_aspect_filename_str.get()) == 0:
					json_yaml_input_data["aspect_base_filename"] = None
				else:
					json_yaml_input_data["aspect_base_filename"] = base_aspect_filename_str.get()


				if len(debris_flow_criteria_Criteria_str.get()) == 0:
					json_yaml_input_data["DEM_debris_flow_initiation_filename"] = None
				else:
					json_yaml_input_data["DEM_debris_flow_initiation_filename"] = debris_flow_criteria_Criteria_str.get()

				if len(debris_flow_criteria_network_str.get()) == 0:
					json_yaml_input_data["DEM_neighbor_directed_graph_filename"] = None
				else:
					json_yaml_input_data["DEM_neighbor_directed_graph_filename"] = debris_flow_criteria_network_str.get()

				if len(debris_flow_criteria_UCA_str.get()) == 0:
					json_yaml_input_data["DEM_UCA_filename"] = None
				else:
					json_yaml_input_data["DEM_UCA_filename"] = debris_flow_criteria_UCA_str.get()

				json_yaml_input_data["local_cell_sizes_slope"] = local_cell_DEM2dip_int.get()
				json_yaml_input_data["interpolation_method"] = "linear"

				## material properties
				# SWCC model shortform
				if SWCC_model_str.get() == "van Genuchten (1980)":
					SWCC_model_assign = "vG"
				elif SWCC_model_str.get() == "Fredlund and Xing (1994)":
					SWCC_model_assign = "FX"

				# uniform asignment
				if mat_assign_opt_str.get() == "Uniform":

					json_yaml_input_data["material_file_name"] = None    # material ID on DEM cells

					mID = 1
					# deterministic
					if mc_iterations_int.get() == 1:
						json_yaml_input_data["material"] = {
							str(mID): {
								"hydraulic": {
									"k_sat": mat_data_dict[mID]["hydraulic_k_sat"][0].get(),
									"initial_suction": mat_data_dict[mID]["hydraulic_initial_suction"][0].get(),
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": mat_data_dict[mID]["hydraulic_SWCC_a"][0].get(),
									"SWCC_n": mat_data_dict[mID]["hydraulic_SWCC_n"][0].get(),
									"SWCC_m": mat_data_dict[mID]["hydraulic_SWCC_m"][0].get(),
									"theta_sat": mat_data_dict[mID]["hydraulic_theta_sat"][0].get(),
									"theta_residual": mat_data_dict[mID]["hydraulic_theta_residual"][0].get(),
									"soil_m_v": mat_data_dict[mID]["hydraulic_soil_m_v"][0].get(),
									"max_surface_storage": mat_data_dict[mID]["hydraulic_max_surface_storage"][0].get()
								},
								"soil": {
									"unit_weight": mat_data_dict[mID]["soil_unit_weight"][0].get(),
									"phi": mat_data_dict[mID]["soil_phi"][0].get(),
									"phi_b": mat_data_dict[mID]["soil_phi_b"][0].get(),
									"c": mat_data_dict[mID]["soil_c"][0].get(),
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}
						} 

						if root_reinforced_model_str.get() == "Constant with Depth":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "constant" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"] = [
								mat_data_dict[mID]["root_c_base"][0].get(),
								mat_data_dict[mID]["root_c_side"][0].get(),
								mat_data_dict[mID]["root_root_depth"][0].get()
							]
						elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"] = [
								mat_data_dict[mID]["root_alpha2"][0].get(),
								mat_data_dict[mID]["root_beta2"][0].get(),
								mat_data_dict[mID]["root_RR_max"][0].get()
							]

					# Monte Carlo probabilistic
					elif mc_iterations_int.get() > 1:
						json_yaml_input_data["material"] = {
							str(mID): {
								"hydraulic": {
									"k_sat": [
										mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"initial_suction": [
										mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": [
										mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_n": [
										mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"SWCC_m": [
										mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"theta_sat": [
										mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"theta_residual": [
										mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"soil_m_v": [
										mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"max_surface_storage": [
										mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else None
					  					for pIDX in range(7)
									]
								},
								"soil": {
									"unit_weight": [
										mat_data_dict[mID]["soil_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"phi": [
										mat_data_dict[mID]["soil_phi"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"phi_b": [
										mat_data_dict[mID]["soil_phi_b"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else None
					  					for pIDX in range(7)
									],
									"c": [
										mat_data_dict[mID]["soil_c"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_c"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_c"][pIDX].get())
										else float(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_c"][pIDX].get())
										else None
					  					for pIDX in range(7)
									]
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}
						} 

						if root_reinforced_model_str.get() == "Constant with Depth":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "constant" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = [
									mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][0] = [
									mat_data_dict[mID]["root_c_base"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_base"][pIDX].get())
									else float(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_base"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][1] = [
									mat_data_dict[mID]["root_c_side"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_side"][pIDX].get())
									else float(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_side"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][2] = [
									mat_data_dict[mID]["root_root_depth"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_root_depth"][pIDX].get())
									else float(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_root_depth"][pIDX].get())
									else None
									for pIDX in range(7)
								]

						elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
							json_yaml_input_data["material"][str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
							json_yaml_input_data["material"][str(mID)]["root"]["unit_weight"] = [
									mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][0] = [
									mat_data_dict[mID]["root_alpha2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_alpha2"][pIDX].get())
									else float(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_alpha2"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][1] = [
									mat_data_dict[mID]["root_beta2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_beta2"][pIDX].get())
									else float(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_beta2"][pIDX].get())
									else None
									for pIDX in range(7)
								]
							json_yaml_input_data["material"][str(mID)]["root"]["parameters"][2] = [
									mat_data_dict[mID]["root_RR_max"][pIDX].get() if pIDX in [0, 1, 5, 6]  
									else "N" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Normal", "normal", "NORMAL"]
									else "LN" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
									else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["inf", "Inf", "INF"]
									else int(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_RR_max"][pIDX].get())
									else float(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_RR_max"][pIDX].get())
									else None
									for pIDX in range(7)
								]

					# GIS files 
					json_yaml_input_data["material_GIS"] = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": None 
						}
					}

					if root_reinforced_model_str.get() == "Constant with Depth":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "constant" 
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "van Zadelhoff et al. (2021)" 

				elif mat_assign_opt_str.get() == "Zone-Based":

					# material ID on DEM cells
					json_yaml_input_data["material_file_name"] = mat_zone_filename_str.get()

					temp_mat = {}
					for mID in range(1, 1+int(num_mat_int.get())):
						# deterministic
						if mc_iterations_int.get() == 1:
							temp_mat[str(mID)] = {
								"hydraulic": {
									"k_sat": mat_data_dict[mID]["hydraulic_k_sat"][0].get(),
									"initial_suction": mat_data_dict[mID]["hydraulic_initial_suction"][0].get(),
									"SWCC_model": SWCC_model_assign,
										"SWCC_a": mat_data_dict[mID]["hydraulic_SWCC_a"][0].get(),
										"SWCC_n": mat_data_dict[mID]["hydraulic_SWCC_n"][0].get(),
										"SWCC_m": mat_data_dict[mID]["hydraulic_SWCC_m"][0].get(),
										"theta_sat": mat_data_dict[mID]["hydraulic_theta_sat"][0].get(),
										"theta_residual": mat_data_dict[mID]["hydraulic_theta_residual"][0].get(),
										"soil_m_v": mat_data_dict[mID]["hydraulic_soil_m_v"][0].get(),
										"max_surface_storage": mat_data_dict[mID]["hydraulic_max_surface_storage"][0].get()
									},
									"soil": {
										"unit_weight": mat_data_dict[mID]["soil_unit_weight"][0].get(),
										"phi": mat_data_dict[mID]["soil_phi"][0].get(),
										"phi_b": mat_data_dict[mID]["soil_phi_b"][0].get(),
										"c": mat_data_dict[mID]["soil_c"][0].get(),
									},
									"root": {
										"unit_weight": None,
										"model": None,
										"parameters": [None, None, None]
									}
								}

							if root_reinforced_model_str.get() == "Constant with Depth":
								temp_mat[str(mID)]["root"]["model"] = "constant" 
								temp_mat[str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
								temp_mat[str(mID)]["root"]["parameters"] = [
									mat_data_dict[mID]["root_c_base"][0].get(),
									mat_data_dict[mID]["root_c_side"][0].get(),
									mat_data_dict[mID]["root_root_depth"][0].get()
								]
							elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
								temp_mat[str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
								temp_mat[str(mID)]["root"]["unit_weight"] = mat_data_dict[mID]["root_unit_weight"][0].get()
								temp_mat[str(mID)]["root"]["parameters"] = [
									mat_data_dict[mID]["root_alpha2"][0].get(),
									mat_data_dict[mID]["root_beta2"][0].get(),
									mat_data_dict[mID]["root_RR_max"][0].get()
								]

						# Monte Carlo probabilistic
						elif mc_iterations_int.get() > 1:
							temp_mat[str(mID)] = {
								"hydraulic": {
									"k_sat": [
										mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_k_sat"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"initial_suction": [
										mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_initial_suction"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_model": SWCC_model_assign,
									"SWCC_a": [
										mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_a"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_n": [
										mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_n"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"SWCC_m": [
										mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_SWCC_m"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"theta_sat": [
										mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_sat"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"theta_residual": [
										mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_theta_residual"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"soil_m_v": [
										mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_soil_m_v"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"max_surface_storage": [
										mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["hydraulic_max_surface_storage"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								},
								"soil": {
									"unit_weight": [
										mat_data_dict[mID]["soil_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"phi": [
										mat_data_dict[mID]["soil_phi"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"phi_b": [
										mat_data_dict[mID]["soil_phi_b"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_phi_b"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else float(mat_data_dict[mID]["soil_phi_b"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_phi_b"][pIDX].get())
										else None
										for pIDX in range(7)
									],
									"c": [
										mat_data_dict[mID]["soil_c"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["soil_c"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["soil_c"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["soil_c"][pIDX].get())
										else float(mat_data_dict[mID]["soil_c"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["soil_c"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								},
								"root": {
									"unit_weight": None,
									"model": None,
									"parameters": [None, None, None]
								}
							}

							if root_reinforced_model_str.get() == "Constant with Depth":
								temp_mat[str(mID)]["root"]["model"] = "constant" 
								temp_mat[str(mID)]["root"]["unit_weight"] = [
										mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][0] = [
										mat_data_dict[mID]["root_c_base"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_base"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_base"][pIDX].get())
										else float(mat_data_dict[mID]["root_c_base"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_base"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][1] = [
										mat_data_dict[mID]["root_c_side"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_c_side"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_c_side"][pIDX].get())
										else float(mat_data_dict[mID]["root_c_side"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_c_side"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][2] = [
										mat_data_dict[mID]["root_root_depth"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_root_depth"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_root_depth"][pIDX].get())
										else float(mat_data_dict[mID]["root_root_depth"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_root_depth"][pIDX].get())
										else None
										for pIDX in range(7)
									]

							elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
								temp_mat[str(mID)]["root"]["model"] = "van Zadelhoff et al. (2021)" 
								temp_mat[str(mID)]["root"]["unit_weight"] = [
										mat_data_dict[mID]["root_unit_weight"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_unit_weight"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else float(mat_data_dict[mID]["root_unit_weight"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_unit_weight"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][0] = [
										mat_data_dict[mID]["root_alpha2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_alpha2"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_alpha2"][pIDX].get())
										else float(mat_data_dict[mID]["root_alpha2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_alpha2"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][1] = [
										mat_data_dict[mID]["root_beta2"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_beta2"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_beta2"][pIDX].get())
										else float(mat_data_dict[mID]["root_beta2"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_beta2"][pIDX].get())
										else None
										for pIDX in range(7)
									]
								temp_mat[str(mID)]["root"]["parameters"][2] = [
										mat_data_dict[mID]["root_RR_max"][pIDX].get() if pIDX in [0, 1, 5, 6]  
										else "N" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Normal", "normal", "NORMAL"]
										else "LN" if pIDX == 2 and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]
										else "inf" if pIDX in [3,4] and mat_data_dict[mID]["root_RR_max"][pIDX].get() in ["inf", "Inf", "INF"]
										else int(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_int(mat_data_dict[mID]["root_RR_max"][pIDX].get())
										else float(mat_data_dict[mID]["root_RR_max"][pIDX].get()) if pIDX in [3,4] and is_float(mat_data_dict[mID]["root_RR_max"][pIDX].get())
										else None
										for pIDX in range(7)
									]

					json_yaml_input_data["material"] = temp_mat

					# GIS files 
					json_yaml_input_data["material_GIS"] = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": None 
						}
					}

					if root_reinforced_model_str.get() == "Constant with Depth":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "constant" 
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						json_yaml_input_data["material_GIS"]["root"]["model"] = "van Zadelhoff et al. (2021)" 

				elif mat_assign_opt_str.get() == "GIS files":

					# material ID on DEM cells
					json_yaml_input_data["material_file_name"] = None

					temp_mat = {
						"1": {
							"hydraulic": {
								"k_sat": None,
								"initial_suction": None,
								"SWCC_model": SWCC_model_assign,
								"SWCC_a": None,
								"SWCC_n": None,
								"SWCC_m": None,
								"theta_sat": None,
								"theta_residual": None,
								"soil_m_v": None,
								"max_surface_storage": None
							},
							"soil": {
								"unit_weight": None,
								"phi": None,
								"phi_b": None,
								"c": None,
							},
							"root": {
								"unit_weight": None,
								"model": None,
								"parameters": [None, None, None]
							}
						}
					} 

					temp_mat_GIS = {
						"hydraulic": {
							"SWCC_model": SWCC_model_assign,
							"k_sat": None,
							"initial_suction": None,
							"SWCC_a": None,
							"SWCC_n": None,
							"SWCC_m": None,
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
							"parameters": [None, None, None] 
						}
					}

					# root
					if root_reinforced_model_str.get() == "Constant with Depth":
						temp_mat["1"]["root"]["model"] = "constant"
						temp_mat_GIS["root"]["model"] = "constant"

						# root - unit_weight
						if len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==False and is_float(mat_data_GIS_dict["root_unit_weight"].get())==False): 
							temp_mat_GIS["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
						elif len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==True or is_float(mat_data_GIS_dict["root_unit_weight"].get())==True):	
							temp_mat["1"]["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
					
						# parameters
						if len(mat_data_GIS_dict["root_c_base"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_base"].get())==False and is_float(mat_data_GIS_dict["root_c_base"].get())==False): 
							temp_mat_GIS["root"]["parameters"][0] = mat_data_GIS_dict["root_c_base"].get()
						elif len(mat_data_GIS_dict["root_c_base"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_base"].get())==True or is_float(mat_data_GIS_dict["root_c_base"].get())==True):	
							temp_mat["1"]["root"]["parameters"][0] = mat_data_GIS_dict["root_c_base"].get()

						if len(mat_data_GIS_dict["root_c_side"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_side"].get())==False and is_float(mat_data_GIS_dict["root_c_side"].get())==False): 
							temp_mat_GIS["root"]["parameters"][1] = mat_data_GIS_dict["root_c_side"].get()
						elif len(mat_data_GIS_dict["root_c_side"].get()) > 0 and (is_int(mat_data_GIS_dict["root_c_side"].get())==True or is_float(mat_data_GIS_dict["root_c_side"].get())==True):	
							temp_mat["1"]["root"]["parameters"][1] = mat_data_GIS_dict["root_c_side"].get()
			
						if len(mat_data_GIS_dict["root_root_depth"].get()) > 0 and (is_int(mat_data_GIS_dict["root_root_depth"].get())==False and is_float(mat_data_GIS_dict["root_root_depth"].get())==False): 
							temp_mat_GIS["root"]["parameters"][2] = mat_data_GIS_dict["root_root_depth"].get()
						elif len(mat_data_GIS_dict["root_root_depth"].get()) > 0 and (is_int(mat_data_GIS_dict["root_root_depth"].get())==True or is_float(mat_data_GIS_dict["root_root_depth"].get())==True):	
							temp_mat["1"]["root"]["parameters"][2] = mat_data_GIS_dict["root_root_depth"].get()
					
					elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
						temp_mat["1"]["root"]["model"] = "van Zadelhoff et al. (2021)"
						temp_mat_GIS["root"]["model"] = "van Zadelhoff et al. (2021)"

						# root - unit_weight
						if len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==False and is_float(mat_data_GIS_dict["root_unit_weight"].get())==False): 
							temp_mat_GIS["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
						elif len(mat_data_GIS_dict["root_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["root_unit_weight"].get())==True or is_float(mat_data_GIS_dict["root_unit_weight"].get())==True):	
							temp_mat["1"]["root"]["unit_weight"] = mat_data_GIS_dict["root_unit_weight"].get()
			
						# parameters
						if len(mat_data_GIS_dict["root_alpha2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_alpha2"].get())==False and is_float(mat_data_GIS_dict["root_alpha2"].get())==False): 
							temp_mat_GIS["root"]["parameters"][0] = mat_data_GIS_dict["root_alpha2"].get()
						elif len(mat_data_GIS_dict["root_alpha2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_alpha2"].get())==True or is_float(mat_data_GIS_dict["root_alpha2"].get())==True):	
							temp_mat["1"]["root"]["parameters"][0] = mat_data_GIS_dict["root_alpha2"].get()

						if len(mat_data_GIS_dict["root_beta2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_beta2"].get())==False and is_float(mat_data_GIS_dict["root_beta2"].get())==False): 
							temp_mat_GIS["root"]["parameters"][1] = mat_data_GIS_dict["root_beta2"].get()
						elif len(mat_data_GIS_dict["root_beta2"].get()) > 0 and (is_int(mat_data_GIS_dict["root_beta2"].get())==True or is_float(mat_data_GIS_dict["root_beta2"].get())==True):	
							temp_mat["1"]["root"]["parameters"][1] = mat_data_GIS_dict["root_beta2"].get()
			
						if len(mat_data_GIS_dict["root_RR_max"].get()) > 0 and (is_int(mat_data_GIS_dict["root_RR_max"].get())==False and is_float(mat_data_GIS_dict["root_RR_max"].get())==False): 
							temp_mat_GIS["root"]["parameters"][2] = mat_data_GIS_dict["root_RR_max"].get()
						elif len(mat_data_GIS_dict["root_RR_max"].get()) > 0 and (is_int(mat_data_GIS_dict["root_RR_max"].get())==True or is_float(mat_data_GIS_dict["root_RR_max"].get())==True):	
							temp_mat["1"]["root"]["parameters"][2] = mat_data_GIS_dict["root_RR_max"].get()


					# hydraulic - k_sat
					if len(mat_data_GIS_dict["hydraulic_k_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_k_sat"].get())==False and is_float(mat_data_GIS_dict["hydraulic_k_sat"].get())==False): 
						temp_mat_GIS["hydraulic"]["k_sat"] = mat_data_GIS_dict["hydraulic_k_sat"].get()
					elif len(mat_data_GIS_dict["hydraulic_k_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_k_sat"].get())==True or is_float(mat_data_GIS_dict["hydraulic_k_sat"].get())==True):	
						temp_mat["1"]["hydraulic"]["k_sat"] = mat_data_GIS_dict["hydraulic_k_sat"].get()

					# hydraulic - initial_suction
					if len(mat_data_GIS_dict["hydraulic_initial_suction"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_initial_suction"].get())==False and is_float(mat_data_GIS_dict["hydraulic_initial_suction"].get())==False): 
						temp_mat_GIS["hydraulic"]["initial_suction"] = mat_data_GIS_dict["hydraulic_initial_suction"].get()
					elif len(mat_data_GIS_dict["hydraulic_initial_suction"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_initial_suction"].get())==True or is_float(mat_data_GIS_dict["hydraulic_initial_suction"].get())==True):	
						temp_mat["1"]["hydraulic"]["initial_suction"] = mat_data_GIS_dict["hydraulic_initial_suction"].get()

					# hydraulic - SWCC_a
					if len(mat_data_GIS_dict["hydraulic_SWCC_a"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_a"] = mat_data_GIS_dict["hydraulic_SWCC_a"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_a"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_a"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_a"] = mat_data_GIS_dict["hydraulic_SWCC_a"].get()

					# hydraulic - SWCC_n
					if len(mat_data_GIS_dict["hydraulic_SWCC_n"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_n"] = mat_data_GIS_dict["hydraulic_SWCC_n"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_n"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_n"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_n"] = mat_data_GIS_dict["hydraulic_SWCC_n"].get()

					# hydraulic - SWCC_m
					if len(mat_data_GIS_dict["hydraulic_SWCC_m"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==False and is_float(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==False): 
						temp_mat_GIS["hydraulic"]["SWCC_m"] = mat_data_GIS_dict["hydraulic_SWCC_m"].get()
					elif len(mat_data_GIS_dict["hydraulic_SWCC_m"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==True or is_float(mat_data_GIS_dict["hydraulic_SWCC_m"].get())==True):	
						temp_mat["1"]["hydraulic"]["SWCC_m"] = mat_data_GIS_dict["hydraulic_SWCC_m"].get()

					# hydraulic - theta_sat
					if len(mat_data_GIS_dict["hydraulic_theta_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_sat"].get())==False and is_float(mat_data_GIS_dict["hydraulic_theta_sat"].get())==False): 
						temp_mat_GIS["hydraulic"]["theta_sat"] = mat_data_GIS_dict["hydraulic_theta_sat"].get()
					elif len(mat_data_GIS_dict["hydraulic_theta_sat"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_sat"].get())==True or is_float(mat_data_GIS_dict["hydraulic_theta_sat"].get())==True):	
						temp_mat["1"]["hydraulic"]["theta_sat"] = mat_data_GIS_dict["hydraulic_theta_sat"].get()

					# hydraulic - theta_residual
					if len(mat_data_GIS_dict["hydraulic_theta_residual"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_residual"].get())==False and is_float(mat_data_GIS_dict["hydraulic_theta_residual"].get())==False): 
						temp_mat_GIS["hydraulic"]["theta_residual"] = mat_data_GIS_dict["hydraulic_theta_residual"].get()
					elif len(mat_data_GIS_dict["hydraulic_theta_residual"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_theta_residual"].get())==True or is_float(mat_data_GIS_dict["hydraulic_theta_residual"].get())==True):	
						temp_mat["1"]["hydraulic"]["theta_residual"] = mat_data_GIS_dict["hydraulic_theta_residual"].get()

					# hydraulic - soil_m_v
					if len(mat_data_GIS_dict["hydraulic_soil_m_v"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==False and is_float(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==False): 
						temp_mat_GIS["hydraulic"]["soil_m_v"] = mat_data_GIS_dict["hydraulic_soil_m_v"].get()
					elif len(mat_data_GIS_dict["hydraulic_soil_m_v"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==True or is_float(mat_data_GIS_dict["hydraulic_soil_m_v"].get())==True):	
						temp_mat["1"]["hydraulic"]["soil_m_v"] = mat_data_GIS_dict["hydraulic_soil_m_v"].get()

					# hydraulic - max_surface_storage
					if len(mat_data_GIS_dict["hydraulic_max_surface_storage"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==False and is_float(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==False): 
						temp_mat_GIS["hydraulic"]["max_surface_storage"] = mat_data_GIS_dict["hydraulic_max_surface_storage"].get()
					elif len(mat_data_GIS_dict["hydraulic_max_surface_storage"].get()) > 0 and (is_int(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==True or is_float(mat_data_GIS_dict["hydraulic_max_surface_storage"].get())==True):	
						temp_mat["1"]["hydraulic"]["max_surface_storage"] = mat_data_GIS_dict["hydraulic_max_surface_storage"].get()
			
					# slope_stability - unit_weight
					if len(mat_data_GIS_dict["soil_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_unit_weight"].get())==False and is_float(mat_data_GIS_dict["soil_unit_weight"].get())==False): 
						temp_mat_GIS["soil"]["unit_weight"] = mat_data_GIS_dict["soil_unit_weight"].get()
					elif len(mat_data_GIS_dict["soil_unit_weight"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_unit_weight"].get())==True or is_float(mat_data_GIS_dict["soil_unit_weight"].get())==True):	
						temp_mat["1"]["soil"]["unit_weight"] = mat_data_GIS_dict["soil_unit_weight"].get()
			
					# slope_stability - phi
					if len(mat_data_GIS_dict["soil_phi"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi"].get())==False and is_float(mat_data_GIS_dict["soil_phi"].get())==False): 
						temp_mat_GIS["soil"]["phi"] = mat_data_GIS_dict["soil_phi"].get()
					elif len(mat_data_GIS_dict["soil_phi"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi"].get())==True or is_float(mat_data_GIS_dict["soil_phi"].get())==True):	
						temp_mat["1"]["soil"]["phi"] = mat_data_GIS_dict["soil_phi"].get()
			
					# slope_stability - phi_b
					if len(mat_data_GIS_dict["soil_phi_b"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi_b"].get())==False and is_float(mat_data_GIS_dict["soil_phi_b"].get())==False): 
						temp_mat_GIS["soil"]["phi_b"] = mat_data_GIS_dict["soil_phi_b"].get()
					elif len(mat_data_GIS_dict["soil_phi_b"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_phi_b"].get())==True or is_float(mat_data_GIS_dict["soil_phi_b"].get())==True):	
						temp_mat["1"]["soil"]["phi_b"] = mat_data_GIS_dict["soil_phi_b"].get()

					# slope_stability - c
					if len(mat_data_GIS_dict["soil_c"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_c"].get())==False and is_float(mat_data_GIS_dict["soil_c"].get())==False): 
						temp_mat_GIS["soil"]["c"] = mat_data_GIS_dict["soil_c"].get()
					elif len(mat_data_GIS_dict["soil_c"].get()) > 0 and (is_int(mat_data_GIS_dict["soil_c"].get())==True or is_float(mat_data_GIS_dict["soil_c"].get())==True):	
						temp_mat["1"]["soil"]["c"] = mat_data_GIS_dict["soil_c"].get()


					json_yaml_input_data["material"] = temp_mat
					json_yaml_input_data["material_GIS"] = temp_mat_GIS

				######################################
				## generate YAML file and save in output directory
				######################################
				with open(output_folder_str.get()+'/'+project_name_str.get()+'_3DTSP_input.yaml', 'w') as yaml_file:
					yaml.safe_dump(json_yaml_input_data, yaml_file, default_flow_style=None, sort_keys=False)

				status.config(text = "simulation running ")

				######################################
				## open subprocess and start simulation
				######################################
				## check the operative system
				opsys = system()
				if not opsys in ["Windows", "Linux", "Darwin"]:
					print("Operating system {:s} not supported.\n".format(opsys))
					sys.exit(1)
					
				## write the cmd or terminal command line to run the 3DTS simulation
				run_python_code = '\"' + '.\\main_3DTSP_v20250813.py\" \"'+output_folder_str.get() + '\\' + project_name_str.get()+'_3DTSP_input.yaml'+'\"' 

				## open new terminal or cmd to run 3DTS simulation
				if opsys == "Windows":  # cmd in windows
					popen_cmd_code = "python "+run_python_code+" && pause && exit"
					proc = subprocess.Popen(popen_cmd_code, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')

				elif system() == "Linux": # Linux use #!/usr/bin/python3	
					popen_terminal_code = "python3 "+run_python_code
					proc = subprocess.Popen(popen_terminal_code, shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')
				
				elif system() == "Darwin":  # MacOS
					popen_terminal_code = "python3 "+run_python_code
					proc = subprocess.Popen(popen_terminal_code, shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')
				
				while proc.poll() is None:
					pass

				proc.kill()     # close terminal to finish
				errX = proc.communicate()[1]  # export error message - for potential debugging

				# Compare the metadata of all files
				if errX == '':     # no error
					print("All 3DTSP simulation is complete! Check the results or simulation state")
				else:     # some sort of error occurred
					print("3DTSP simulation had error and terminated.\nError message:"+errX)

				status.config(text = "simulation finished ")

				return None

		##########################################
		## for 3DPLS
		##########################################
		elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]:

			#####################
			## generate dictionary hold input file 
			#####################
			json_yaml_input_data = {
				"directories": {},
				"gis_files" : {},
				"gis_config" : {},
				"rainfall" : {},
				"monte_carlo" : {},
				"analysis" : {},
				"zmax_parameters" : {},
				"multiprocessing" : {},
				"soil_parameters" : {},
				"ellipsoid" : {},
				"investigation" : {},
				"project" : {}
			}

			# assign relative path from the bash or batch script
			json_yaml_input_data['directories']["input_folder"] = output_folder_str.get()+"/3DPLS/03-Input/"
			json_yaml_input_data['directories']["output_folder"] = output_folder_str.get()+"/3DPLS/04-Results/"
			json_yaml_input_data['directories']["matrix_storage"] = output_folder_str.get()+"/3DPLS/04-Results/matrices/"
			json_yaml_input_data['directories']["gis_data_folder"] = output_folder_str.get()+"/3DPLS/GIS/"

			# generate an empty folder in the input directory
			if not os.path.exists(output_folder_str.get()+"/3DPLS/03-Input/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/03-Input/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/04-Results/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/04-Results/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/Matrix/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/Matrix/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/04-Results/matrices/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/04-Results/matrices/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/Codes/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/Codes/")
			if not os.path.exists(output_folder_str.get()+"/3DPLS/GIS/"):
				os.makedirs(output_folder_str.get()+"/3DPLS/GIS/")

			# move any ascii GIS data in input_folder_str.get() into output_folder_str.get()+"/3DPLS/GIS/"
			for file in os.listdir(input_folder_str.get()):
				if file.endswith(".asc"):
					shutil.copy(os.path.join(input_folder_str.get(), file), os.path.join(output_folder_str.get()+"/3DPLS/GIS/", file))

			#####################
			## project name 
			#####################
			json_yaml_input_data['project']["filename"] = project_name_str.get()
   
			#####################
			## gis files (gis_files, gis_config, zmax_parameters)
			#####################
   
			########## DEM ##########
			json_yaml_input_data["gis_files"]["dem"] = DEM_filename_str.get()

			########## array information ##########
			DEM_surface, nodata_value, DEM_noData, gridUniqueX, gridUniqueY, deltaX, deltaY, dx_dp, dy_dp, _ = m3DTSP.read_GIS_data(DEM_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=True)

			json_yaml_input_data["gis_config"]["nodata_value"] = nodata_value
			json_yaml_input_data["gis_config"]["read_nodata_from_file"] = True

			########## RiZero from file ##########
			if len(rizero_GIS_filename_str.get()) > 0:
				json_yaml_input_data["gis_files"]["rizero"] = rizero_GIS_filename_str.get()

			# RiZero from uniform value
			else: 
				RiZero_2D = np.ones(DEM_surface.shape)*rizero_value_double.get()
				m3DTSP.data_mesh2asc(RiZero_2D, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"rizero", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["rizero"] = "rizero.asc"

			########## slope and aspect ##########
			# from file name
			if (surf_dip_filename_str.get() != "(optional)" and len(surf_dip_filename_str.get()) > 0) and (surf_aspect_filename_str.get() != "(optional)" and len(surf_aspect_filename_str.get()) > 0):
				json_yaml_input_data["gis_files"]["slope"] = surf_dip_filename_str.get()
				json_yaml_input_data["gis_files"]["aspect"] = surf_aspect_filename_str.get()
				json_yaml_input_data["gis_files"]["dir"] = surf_aspect_filename_str.get()

				dip_surf, _, _ = m3DTSP.read_GIS_data(surf_dip_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)

			# slope and aspect computed from DEM
			elif (surf_dip_filename_str.get() == "(optional)" or len(surf_dip_filename_str.get()) == 0) and (surf_aspect_filename_str.get() == "(optional)" or len(surf_aspect_filename_str.get()) == 0):
				DEM_soil_thickness = np.ones(DEM_surface.shape).astype(np.int32)
				DEM_base = DEM_surface - DEM_soil_thickness
    
				dip_surf, aspect_surf, _, _ = m3DTSP.compute_dip_aspect(DEM_surface, DEM_base, DEM_soil_thickness, DEM_noData, gridUniqueX, gridUniqueY, local_cell_DEM2dip_int.get(), 2, max_CPU_pool_int.get())

				m3DTSP.data_mesh2asc(dip_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"slope", user_nodata_value=nodata_value, fmt="%.6f")
				m3DTSP.data_mesh2asc(aspect_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"aspect", user_nodata_value=nodata_value, fmt="%.6f")
				m3DTSP.data_mesh2asc(aspect_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"dir", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["slope"] = "slope.asc"
				json_yaml_input_data["gis_files"]["aspect"] = "aspect.asc"
				json_yaml_input_data["gis_files"]["dir"] = "dir.asc"

			########### zone ##########
			json_yaml_input_data["gis_files"]["zones"] = output_format_opt_str.get()

			if mat_assign_opt_str.get() == "Uniform":
				matID_array = np.ones(DEM_surface.shape).astype(int)
				m3DTSP.data_mesh2asc(matID_array, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zones", user_nodata_value=nodata_value, fmt="%.0f")
				json_yaml_input_data["gis_files"]["zones"] = "zones.asc"    # material ID on DEM cells

			elif mat_assign_opt_str.get() == "Zone-Based":
				json_yaml_input_data["gis_files"]["zones"] = mat_zone_filename_str.get()
   
			########## zmax ##########
			if soil_depth_probabilistic_check_int.get() == 1:  # for any probabilistic

				DEM_soil_thickness = -2.578*np.tan(np.radians(dip_surf)) + 2.612
				DEM_soil_thickness = DEM_soil_thickness * ( np.ones(DEM_soil_thickness.shape) + soil_depth_probabilistic_cov.get() * np.random.normal(0, 1, size=(DEM_soil_thickness.shape)) )
				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"/zmax", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "Yes"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = soil_depth_probabilistic_cov.get()
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = min_soil_depth_double.get()
   
			elif soil_depth_opt_str.get() == "Uniform Depth" and soil_depth_probabilistic_check_int.get() == 0:
				DEM_soil_thickness = np.ones(DEM_surface.shape)*uniform_soil_depth_double.get()
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc" 
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "GIS file" and soil_depth_probabilistic_check_int.get() == 0:
				json_yaml_input_data["gis_files"]["zmax"] = GIS_soil_depth_str.get()
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "Holm (2012) & Edvarson (2013)" and soil_depth_probabilistic_check_int.get() == 0:
				DEM_soil_thickness = -2.578*np.tan(np.radians(dip_surf)) + 2.612
				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "Yes"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0
    
			elif soil_depth_opt_str.get() == "Linear Multiregression" and soil_depth_probabilistic_check_int.get() == 0:

				DEM_soil_thickness = np.ones((DEM_surface.shape)) * gen_reg_intercept_double.get()   

				if len(gen_reg_param1_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param1_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param1_double.get()
				if len(gen_reg_param2_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param2_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param2_double.get()
				if len(gen_reg_param3_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param3_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param3_double.get()
				if len(gen_reg_param4_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param4_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param4_double.get()
				if len(gen_reg_param5_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param5_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param5_double.get()
				if len(gen_reg_param6_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param6_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param6_double.get()
				if len(gen_reg_param7_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param7_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param7_double.get()
				if len(gen_reg_param8_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param8_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param8_double.get()
				if len(gen_reg_param9_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param9_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param9_double.get()
				if len(gen_reg_param10_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param10_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness + gis_data_temp*gen_reg_param10_double.get()

				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0

			elif soil_depth_opt_str.get() == "Power Multiregression" and soil_depth_probabilistic_check_int.get() == 0:
       
				DEM_soil_thickness = np.ones((DEM_surface.shape)) * gen_reg_intercept_double.get()

				if len(gen_reg_param1_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param1_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param1_double.get())
				if len(gen_reg_param2_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param2_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param2_double.get())
				if len(gen_reg_param3_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param3_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param3_double.get())
				if len(gen_reg_param4_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param4_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param4_double.get())
				if len(gen_reg_param5_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param5_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param5_double.get())
				if len(gen_reg_param6_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param6_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param6_double.get())
				if len(gen_reg_param7_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param7_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param7_double.get())
				if len(gen_reg_param8_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param8_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param8_double.get())
				if len(gen_reg_param9_filename_str.get()) > 0:	
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param9_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param9_double.get())
				if len(gen_reg_param10_filename_str.get()) > 0:
					gis_data_temp, _, _ = m3DTSP.read_GIS_data(gen_reg_param10_filename_str.get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					DEM_soil_thickness = DEM_soil_thickness * np.power(gis_data_temp, gen_reg_param10_double.get())

				DEM_soil_thickness = np.clip(DEM_soil_thickness, min_soil_depth_double.get(), max_soil_depth_double.get())   # model clipped between min and max    
    
				m3DTSP.data_mesh2asc(DEM_soil_thickness, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"zmax", user_nodata_value=nodata_value, fmt="%.6f")
				json_yaml_input_data["gis_files"]["zmax"] = "zmax.asc"
				json_yaml_input_data["zmax_parameters"]["zmax_var"] = "No"
				json_yaml_input_data["zmax_parameters"]["cov_zmax"] = 0.0
				json_yaml_input_data["zmax_parameters"]["min_zmax"] = 0.0   
   
			########## post-processing with 3DPLS ##########
			if landslide_source_filename_str.get() != "(optional)" and len(landslide_source_filename_str.get()) > 0:
				json_yaml_input_data["gis_files"]["source"] = output_format_opt_str.get()

			########## groundwater table ##########
			if groundwater_opt_str.get() == "GWT elevation GIS":
				if len(gwt_GIS_filename_str.get()) > 0:
					json_yaml_input_data["gis_files"]["depthwt"] = gwt_GIS_filename_str.get()
			else:
				if groundwater_opt_str.get() == "Thickness Above Bedrock":
					ground_water_model = 0
				elif groundwater_opt_str.get() == "Depth From Surface":
					ground_water_model = 1
				elif groundwater_opt_str.get() == "% of Soil Thickness Above Bedrock":
					ground_water_model = 2 
				elif groundwater_opt_str.get() == "% of Soil Thickness From Surface":
					ground_water_model = 3
    
				if len(gwt_GIS_filename_str.get()) == 0:			
					ground_water_data = gwt_value_double.get()
				elif len(gwt_GIS_filename_str.get()) > 0 and gwt_value_double.get() == 0.0:			
					ground_water_data = gwt_GIS_filename_str.get()

				DEM_base = DEM_surface - DEM_soil_thickness

				DEM_gwt_z, gwt_depth_from_surf = m3DTSP.generate_groundwater_GIS_data(output_folder_str.get()+"/3DPLS/GIS/", ground_water_model, ground_water_data, DEM_surface, DEM_base, DEM_soil_thickness)

				m3DTSP.data_mesh2asc(gwt_depth_from_surf, gridUniqueX, gridUniqueY, deltaX, deltaY, outFileName=output_folder_str.get()+"/3DPLS/GIS/"+"depthwt", user_nodata_value=nodata_value, fmt="%.6f")

				json_yaml_input_data["gis_files"]["depthwt"] = "depthwt.asc"

			#####################
			## rainfall - uniform
			#####################
			""" NOTE: Iverson can only do uniform deterministic rainfall, so if anything else, compute the average rainfall over time and for given location """
			rainfall_intensity_sum = 0.0  # unit based on rainfall_intensity_unit_str.get()
			rainfall_time_unit_count = 0
			rainfall_time_max = 0   # unit based on rainfall_intensity_unit_str.get()
			
			for rain_t in range(1, 101):
				# check if empty
				if (rain_hist_t_dict[rain_t][0].get() == 0 and rain_hist_t_dict[rain_t][1].get() == 0) or (rainfall_history_opt_str.get() == "Uniform" and rain_hist_t_dict[rain_t][2][0] == 0) or (rainfall_history_opt_str.get() == "GIS file" and len(rain_hist_t_dict[rain_t][2][1].get()) == 0) or (rainfall_history_opt_str.get() in ["Deterministic Rainfall Gauge", "Probabilistic Rainfall Gauge"] and (rain_hist_t_dict[rain_t][2][2][0][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][1][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][2][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][3][2].get() == 0 and rain_hist_t_dict[rain_t][2][2][4][2].get() == 0)):
					continue    

				# uniform rainfall
				if rainfall_history_opt_str.get() == "Uniform":
					rainfall_intensity_sum += rain_hist_t_dict[rain_t][2][0].get()*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += (rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

				# GIS file containing intensity
				elif rainfall_history_opt_str.get() == "GIS file":
					rain_I, nodata_value, rain_noData = m3DTSP.read_GIS_data(rain_hist_t_dict[rain_t][2][1].get(), output_folder_str.get()+"/3DPLS/GIS/", full_output=False)
					rain_I_filter = np.where(np.logical_or(rain_noData==0, DEM_noData==0), 0, rain_I)
					rainfall_intensity_sum += np.sum(rain_I_filter)*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += int(np.sum(rain_noData))*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

				# get intensity from the nearest rainfall gauge measurement
				# even when using probabilistic rainfall, assume their cells are large to tend towards mean
				elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge" or rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":

					# format: [[X, Y, intensity], ...]
					xx, yy = np.meshgrid(gridUniqueX, gridUniqueY)
					xGrids = np.ravel(xx)
					yGrids = np.ravel(yy)

					gauge_xy_list = []
					gauge_I_list = []
					for gauge in range(5):
						if rain_hist_t_dict[rain_t][2][2][gauge][0].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][1].get() != 0 and rain_hist_t_dict[rain_t][2][2][gauge][2].get() != 0:
							gauge_xy_list.append([rain_hist_t_dict[rain_t][2][2][gauge][0].get(), rain_hist_t_dict[rain_t][2][2][gauge][1].get()])
							gauge_I_list.append([rain_hist_t_dict[rain_t][2][2][gauge][2].get()])

					interp_nearest_I_data = griddata(np.array(gauge_xy_list), np.array(gauge_I_list), (xGrids, yGrids), method='nearest')
					rain_I = np.reshape(interp_nearest_I_data, (len(gridUniqueY), len(gridUniqueX)))
					rain_I_filter = np.where(DEM_noData==0, 0, rain_I)

					rainfall_intensity_sum += np.sum(rain_I_filter)*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_unit_count += int(np.sum(DEM_noData))*(rain_hist_t_dict[rain_t][1].get() - rain_hist_t_dict[rain_t][0].get())
					rainfall_time_max = max(rainfall_time_max, rain_hist_t_dict[rain_t][1].get())

			rainfall_intensity_av = rainfall_intensity_sum/rainfall_time_unit_count

			# convert all length to m, time to s for rainfall history in 3DPLS
			rainfall_intensity_unit = rainfall_intensity_unit_str.get()
			length_unit, time_unit = rainfall_intensity_unit.split("/")

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

			# store
			json_yaml_input_data["rainfall"]["riInp"] = rainfall_intensity_av*convert_intensity
			json_yaml_input_data["rainfall"]["riInp_duration"] = rainfall_time_max*convert_time

			#####################
			## MONTE CARLO AND ANALYSIS CONFIGURATION
			#####################
			# monte carlo
			json_yaml_input_data["monte_carlo"]["mcnumber"] = mc_iterations_int.get()

			# analysis information
			json_yaml_input_data["analysis"]["analysis_type"] = analysis_opt_3DPLS_str.get()

			if slope_model_str.get() == "3D Normal":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Normal3D"
			elif slope_model_str.get() == "3D Bishop":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Bishop3D"
			elif slope_model_str.get() == "3D Janbu":
				json_yaml_input_data["analysis"]["fs_calculation_type"] = "Janbu3D"

			json_yaml_input_data["analysis"]["random_field_method"] = random_field_method_str.get()
			json_yaml_input_data["analysis"]["save_mat"] = "YES"   # set them as default
			json_yaml_input_data["analysis"]["problem_name"] = ""

			# ellipsoidal slip surface
			json_yaml_input_data["ellipsoid"]["ella"] = ellipsoidal_slip_surface_a_double.get()
			json_yaml_input_data["ellipsoid"]["ellb"] = ellipsoidal_slip_surface_b_double.get()
			json_yaml_input_data["ellipsoid"]["ellc"] = ellipsoidal_slip_surface_c_double.get()
			json_yaml_input_data["ellipsoid"]["ellz"] = ellipsoidal_slip_surface_z_double.get()
			if ellipsoidal_slip_surface_alpha_comp_int.get() == 1:
				json_yaml_input_data["ellipsoid"]["ellalpha_calc"] = "Yes"
				json_yaml_input_data["ellipsoid"]["ellalpha"] = 0.0
			elif ellipsoidal_slip_surface_alpha_comp_int.get() == 0:
				json_yaml_input_data["ellipsoid"]["ellalpha_calc"] = "No"
				json_yaml_input_data["ellipsoid"]["ellalpha"] = ellipsoidal_slip_surface_alpha_double.get()

			# investigation
			if inzone_check_int.get() == 1:  # compute inzone automatically from DEM
				json_yaml_input_data["investigation"]["inzone"] = [[0, len(gridUniqueY)-1], [0, len(gridUniqueX)-1]]
			elif inzone_check_int.get() == 0:  # get from manual data
				json_yaml_input_data["investigation"]["inzone"] = [[inzone_min_i_int.get(), inzone_max_i_int.get()], [inzone_min_j_int.get(), inzone_max_j_int.get()]]

			if intime_check_int.get() == 1 or len(intime_str.get()) == 0:  # compute automatically
				json_yaml_input_data["investigation"]["time_to_analyse"] = [rainfall_time_max*convert_time]
			elif intime_check_int.get() == 0 and len(intime_str.get()) > 0:  # get from manual data
				temp_intime = intime_str.get().split(",")
				temp_intime = [float(p1.strip())*convert_time for p1 in temp_intime]  # strip all whitespaces and convert units
				json_yaml_input_data["investigation"]["time_to_analyse"] = temp_intime[:]

			json_yaml_input_data["investigation"]["sub_dis_num"] = max(int(ellipsoidal_slip_surface_min_sub_div_int.get()), 0)

			#####################
			## multiprocessing
			#####################			
			if multi_CPU_method_opt_int.get() >= 1:
				json_yaml_input_data["multiprocessing"]["multiprocessing_option"] = "S-MP-MP" # multi_CPU_method_str.get()
				json_yaml_input_data["multiprocessing"]["total_processes_mc"] = max_CPU_pool_int.get()  # MP_1st_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_ell"] = max_CPU_pool_int.get()  # MP_2nd_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_threads_ell"] = max_CPU_pool_int.get()  # MT_2nd_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_indmc"] = max_CPU_pool_int.get()  # MP_1st_CPU_pool_int.get()
				json_yaml_input_data["multiprocessing"]["total_processes_ellgen"] = max_CPU_pool_int.get()  # MP_2nd_CPU_pool_int.get()
			else:
				json_yaml_input_data["multiprocessing"]["multiprocessing_option"] = "S-SP-SP"
				json_yaml_input_data["multiprocessing"]["total_processes_mc"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_ell"] = 1
				json_yaml_input_data["multiprocessing"]["total_threads_ell"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_indmc"] = 1
				json_yaml_input_data["multiprocessing"]["total_processes_ellgen"] = 1

			#####################
			## material
			#####################
			zone_mat_param_temp = {
				# Cohesion parameters (Pa) - user assigned kPa
				"cohesion": {
					"mean_cInp": 0.0,
					"cov_cInp": 0.0,
					"dist_cInp": "Normal",
					"corrLenX_cInp": 'inf', 
					"corrLenY_cInp": 'inf' 
				},
				# Friction angle parameters (deg)
				"friction_angle": {
					"mean_phiInp": 0.0,
					"cov_phiInp": 0.0,
					"dist_phiInp": "Normal",
					"corrLenX_phiInp": 'inf',
					"corrLenY_phiInp": 'inf'
				},
				# Unit weight parameters (N/m3) - user assigned kN/m3
				"unit_weight": {
					"mean_uwsInp": 0.0, 
					"cov_uwsInp": 0.0, 
					"dist_uwsInp": "Normal",
					"corrLenX_uwsInp": 'inf',
					"corrLenY_uwsInp": 'inf'
				},
				# Saturated permeability parameters (m/s)
				"saturated_permeability": {
					"mean_kSatInp": 0.0,
					"cov_kSatInp": 0.0,
					"dist_kSatInp": "Normal",
					"corrLenX_kSatInp": 'inf',
					"corrLenY_kSatInp": 'inf'
				},
				# Diffusivity parameters (m2/s)
				"diffusivity": {
					"mean_diffusInp": 0.0,
					"cov_diffusInp": 0.0,
					"dist_diffusInp": "Lognormal",
					"corrLenX_diffusInp": 'inf',
					"corrLenY_diffusInp": 'inf'
				},
				# Undrained shear strength (for undrained analysis) (Pa) - user assigned kPa
				"undrained_shear_strength": {
					"mean_SuInp": 0.0,
					"cov_SuInp": 0.0,
					"dist_SuInp": "Normal",
					"corrLenX_SuInp": 'inf',
					"corrLenY_SuInp": 'inf'
				}
			}
		
			# uniform asignment
			if mat_assign_opt_str.get() == "Uniform" or num_mat_int.get() == 1:
				mID_max = 1
			elif mat_assign_opt_str.get() == "Zone-Based" and num_mat_int.get() > 1:
				mID_max = int(num_mat_int.get())

			for mID in range(1, 1+mID_max):

				zone_mat_param_template = deepcopy(zone_mat_param_temp)

				# deterministic
				if mc_iterations_int.get() == 1:
					zone_mat_param_template['cohesion']['mean_cInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['friction_angle']['mean_phiInp'] = mat_data_dict[mID]["soil_phi"][0].get()
					zone_mat_param_template['unit_weight']['mean_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][0].get()*1000.0
					zone_mat_param_template['saturated_permeability']['mean_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][0].get()
					zone_mat_param_template['diffusivity']['mean_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][0].get()
					zone_mat_param_template['undrained_shear_strength']['mean_SuInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0

				# Monte Carlo probabilistic
				elif mc_iterations_int.get() > 1:
					zone_mat_param_template['cohesion']['mean_cInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['cohesion']['cov_cInp'] = mat_data_dict[mID]["soil_c"][1].get()
					zone_mat_param_template['cohesion']['dist_cInp'] = "Normal" if mat_data_dict[mID]["soil_c"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_c"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal" 
					zone_mat_param_template['cohesion']['corrLenX_cInp'] = "inf" if mat_data_dict[mID]["soil_c"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][3].get()) if is_int(mat_data_dict[mID]["soil_c"][3].get()) else float(mat_data_dict[mID]["soil_c"][3].get()) if is_float(mat_data_dict[mID]["soil_c"][3].get()) else mat_data_dict[mID]["soil_c"][3].get()
					zone_mat_param_template['cohesion']['corrLenY_cInp'] = "inf" if mat_data_dict[mID]["soil_c"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][4].get()) if is_int(mat_data_dict[mID]["soil_c"][4].get()) else float(mat_data_dict[mID]["soil_c"][4].get()) if is_float(mat_data_dict[mID]["soil_c"][4].get()) else mat_data_dict[mID]["soil_c"][4].get()

					zone_mat_param_template['friction_angle']['mean_phiInp'] = mat_data_dict[mID]["soil_phi"][0].get()
					zone_mat_param_template['friction_angle']['cov_phiInp'] = mat_data_dict[mID]["soil_phi"][1].get()
					zone_mat_param_template['friction_angle']['dist_phiInp'] = "Normal" if mat_data_dict[mID]["soil_phi"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_phi"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['friction_angle']['corrLenX_phiInp'] = "inf" if mat_data_dict[mID]["soil_phi"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_phi"][3].get()) if is_int(mat_data_dict[mID]["soil_phi"][3].get()) else float(mat_data_dict[mID]["soil_phi"][3].get()) if is_float(mat_data_dict[mID]["soil_phi"][3].get()) else mat_data_dict[mID]["soil_phi"][3].get()
					zone_mat_param_template['friction_angle']['corrLenY_phiInp'] = "inf" if mat_data_dict[mID]["soil_phi"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_phi"][4].get()) if is_int(mat_data_dict[mID]["soil_phi"][4].get()) else float(mat_data_dict[mID]["soil_phi"][4].get()) if is_float(mat_data_dict[mID]["soil_phi"][4].get()) else mat_data_dict[mID]["soil_phi"][4].get()

					zone_mat_param_template['unit_weight']['mean_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][0].get()*1000.0
					zone_mat_param_template['unit_weight']['cov_uwsInp'] = mat_data_dict[mID]["soil_unit_weight"][1].get()
					zone_mat_param_template['unit_weight']['dist_uwsInp'] = "Normal" if mat_data_dict[mID]["soil_unit_weight"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_unit_weight"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['unit_weight']['corrLenX_uwsInp'] = "inf" if mat_data_dict[mID]["soil_unit_weight"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_unit_weight"][3].get()) if is_int(mat_data_dict[mID]["soil_unit_weight"][3].get()) else float(mat_data_dict[mID]["soil_unit_weight"][3].get()) if is_float(mat_data_dict[mID]["soil_unit_weight"][3].get()) else mat_data_dict[mID]["soil_unit_weight"][3].get()
					zone_mat_param_template['unit_weight']['corrLenY_uwsInp'] = "inf" if mat_data_dict[mID]["soil_unit_weight"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_unit_weight"][4].get()) if is_int(mat_data_dict[mID]["soil_unit_weight"][4].get()) else float(mat_data_dict[mID]["soil_unit_weight"][4].get()) if is_float(mat_data_dict[mID]["soil_unit_weight"][4].get()) else mat_data_dict[mID]["soil_unit_weight"][4].get()

					zone_mat_param_template['saturated_permeability']['mean_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][0].get()
					zone_mat_param_template['saturated_permeability']['cov_kSatInp'] = mat_data_dict[mID]["hydraulic_k_sat"][1].get()
					zone_mat_param_template['saturated_permeability']['dist_kSatInp'] = "Normal" if mat_data_dict[mID]["hydraulic_k_sat"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["hydraulic_k_sat"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['saturated_permeability']['corrLenX_kSatInp'] = "inf" if mat_data_dict[mID]["hydraulic_k_sat"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) if is_int(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) else float(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) if is_float(mat_data_dict[mID]["hydraulic_k_sat"][3].get()) else mat_data_dict[mID]["hydraulic_k_sat"][3].get()
					zone_mat_param_template['saturated_permeability']['corrLenY_kSatInp'] = "inf" if mat_data_dict[mID]["hydraulic_k_sat"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) if is_int(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) else float(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) if is_float(mat_data_dict[mID]["hydraulic_k_sat"][4].get()) else mat_data_dict[mID]["hydraulic_k_sat"][4].get()

					zone_mat_param_template['diffusivity']['mean_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][0].get()
					zone_mat_param_template['diffusivity']['cov_diffusInp'] = mat_data_dict[mID]["hydraulic_diffusivity"][1].get()
					zone_mat_param_template['diffusivity']['dist_diffusInp'] = "Normal" if mat_data_dict[mID]["hydraulic_diffusivity"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["hydraulic_diffusivity"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal"
					zone_mat_param_template['diffusivity']['corrLenX_diffusInp'] = "inf" if mat_data_dict[mID]["hydraulic_diffusivity"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) if is_int(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) else float(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) if is_float(mat_data_dict[mID]["hydraulic_diffusivity"][3].get()) else mat_data_dict[mID]["hydraulic_diffusivity"][3].get()
					zone_mat_param_template['diffusivity']['corrLenY_diffusInp'] = "inf" if mat_data_dict[mID]["hydraulic_diffusivity"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) if is_int(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) else float(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) if is_float(mat_data_dict[mID]["hydraulic_diffusivity"][4].get()) else mat_data_dict[mID]["hydraulic_diffusivity"][4].get()

					zone_mat_param_template['undrained_shear_strength']['mean_SuInp'] = mat_data_dict[mID]["soil_c"][0].get()*1000.0
					zone_mat_param_template['undrained_shear_strength']['cov_SuInp'] = mat_data_dict[mID]["soil_c"][1].get()
					zone_mat_param_template['undrained_shear_strength']['dist_SuInp'] = "Normal" if mat_data_dict[mID]["soil_c"][2].get() in ["Normal", "normal", "NORMAL"] else "Lognormal" if mat_data_dict[mID]["soil_c"][2].get() in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"] else "Normal" 
					zone_mat_param_template['undrained_shear_strength']['corrLenX_SuInp'] = "inf" if mat_data_dict[mID]["soil_c"][3].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][3].get()) if is_int(mat_data_dict[mID]["soil_c"][3].get()) else float(mat_data_dict[mID]["soil_c"][3].get()) if is_float(mat_data_dict[mID]["soil_c"][3].get()) else mat_data_dict[mID]["soil_c"][3].get()
					zone_mat_param_template['undrained_shear_strength']['corrLenY_SuInp'] = "inf" if mat_data_dict[mID]["soil_c"][4].get() in ["inf", "Inf", "INF"] else int(mat_data_dict[mID]["soil_c"][4].get()) if is_int(mat_data_dict[mID]["soil_c"][4].get()) else float(mat_data_dict[mID]["soil_c"][4].get()) if is_float(mat_data_dict[mID]["soil_c"][4].get()) else mat_data_dict[mID]["soil_c"][4].get()

				# add data
				json_yaml_input_data["soil_parameters"][f"zone_{mID}"] = deepcopy(zone_mat_param_template)

			######################################
			## copy paste the 3DPLS scripts
			######################################
			shutil.copy(r"./Main_3DPLS_v1_1_yaml.py", output_folder_str.get()+"/3DPLS/Codes/"+r"./Main_3DPLS_v1_1_yaml.py")
			shutil.copy(r"./Functions_3DPLS_v1_1.py", output_folder_str.get()+"/3DPLS/Codes/"+r"./Functions_3DPLS_v1_1.py")

			######################################
			## generate YAML file and save in input directory
			######################################
			with open(output_folder_str.get()+'/3DPLS/03-Input/'+'input_3DPLS.yaml', 'w') as yaml_file:
				yaml.safe_dump(json_yaml_input_data, yaml_file, default_flow_style=None, sort_keys=False)
    
			status.config(text = "simulation running ")

			######################################
			## open subprocess and start simulation
			######################################
			## check the operative system
			opsys = system()
			if not opsys in ["Windows", "Linux", "Darwin"]:
				print("Operating system {:s} not supported.\n".format(opsys))
				sys.exit(1)
				
			## write the cmd or terminal command line to run the 3DTS simulation
			# run_python_code = '\"' + output_folder_str.get()+'\\3DPLS\\Codes\\Main_3DPLS_v1_1_yaml.py\" \"'
			# run_code = "cd \""+output_folder_str.get()+"\\3DPLS\\Codes\\\" &&"

			## open new terminal or cmd to run 3DTS simulation
			if opsys == "Windows":  # cmd in windows
				popen_cmd_code = "python \".\Codes\Main_3DPLS_v1_1_yaml.py\" && pause && exit"
				proc = subprocess.Popen(popen_cmd_code, cwd=output_folder_str.get()+"\\3DPLS\\", shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')

			elif system() == "Linux": # Linux use #!/usr/bin/python3	
				popen_terminal_code = "python3 \".\Codes\Main_3DPLS_v1_1_yaml.py\""
				proc = subprocess.Popen(popen_terminal_code, cwd=output_folder_str.get()+"\\3DPLS\\", shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')

			elif system() == "Darwin":  # MacOS
				popen_terminal_code = "python3 \".\Codes\Main_3DPLS_v1_1_yaml.py\""
				proc = subprocess.Popen(popen_terminal_code, cwd=output_folder_str.get()+"\\3DPLS\\", shell=False, stdout=sys.stdout, stderr=subprocess.PIPE, encoding='ascii')

			while proc.poll() is None:
				pass

			proc.kill()     # close terminal to finish
			errX = proc.communicate()[1]  # export error message - for potential debugging

			# Compare the metadata of all files
			if errX == '':     # no error
				print("All 3DPLS simulation is complete! Check the results or simulation state")
			else:     # some sort of error occurred
				print("3DPLS simulation had error and terminated.\nError message:"+errX)

			status.config(text = "simulation finished ")

			return None

	# create template for rainfall history CSV file
	def csv_rainfall_template_command():

		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'
		
		# create csv template
		if rainfall_history_opt_str.get() == "Uniform":
			csv_temp_header = ['start time', 'end time', 'intensity']
		elif rainfall_history_opt_str.get() == "GIS file":
			csv_temp_header = ['start time', 'end time', 'GIS file name']
		elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge":
			csv_temp_header = ['start time', 'end time']
			for i in range(1, 6):
				csv_temp_header.extend([f"X{i}", f"Y{i}", f"I{i}"])
		elif rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":
			csv_temp_header = ['start time', 'end time']
			for i in range(1, 6):
				csv_temp_header.extend([f"X{i}", f"Y{i}", f"mean I{i}", f"CoV{i}", f"Prob Dist.{i}", f"CorLenX{i}", f"CorLenY{i}", f"Min{i}", f"Max{i}"])

		# load input file
		temp_file = filedialog.asksaveasfile(initialdir=file_path, title="Save rainfall template CSV file", mode='w', defaultextension=".csv", filetypes=[("comma-separated value","*.csv")])

		# asksaveasfile return `None` if dialog closed with "cancel".
		try:
			if temp_file is None:
				return

			elif len(temp_file.name) > 0:
				file_path_name = temp_file.name
				file_naming_list = file_path_name.split("/")
				# file_name_only = file_naming_list[-1]

				with open(file_path_name, 'w', newline='') as temp_file:
					csv_temp_writer = csv.writer(temp_file)
					csv_temp_writer.writerow(csv_temp_header[:])

				# update status to show similuation is running 
				status.config(text = "Rainfall History CSV file created ")

			else:
				return

		except:
			return 

	# open rainfall history CSV file command and fill in data
	def open_rainfall_history_csv_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_rainfall_history_GIS_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select rainfall history CSV file",
								filetypes=(
									("comma-separated value", "*.csv"),
								)   # only open valid type of format
							)
		
		# display output folder location in the output text
		try:
			if len(selected_rainfall_history_GIS_file) > 0 and os.path.isfile(selected_rainfall_history_GIS_file):

				# only need the filename
				file_path_name = selected_rainfall_history_GIS_file
				file_naming_list = file_path_name.split("/")
				file_name_only = file_naming_list[-1]

				# open data			
				rain_hist_column = csv2list_numbercheck(file_path_name, starting_row=0, end_row=1)[0]
				rain_hist_data = csv2list_numbercheck(file_path_name, starting_row=1)

				# check rainfall history options
				if 'intensity' in rain_hist_column:
					rainfall_history_opt_str.set("Uniform")
				elif 'GIS file' in rain_hist_column:
					rainfall_history_opt_str.set("GIS file")
				elif 'X1' in rain_hist_column and 'Y1' in rain_hist_column and 'I1' in rain_hist_column:
					rainfall_history_opt_str.set("Deterministic Rainfall Gauge")
				elif 'mean I1' in rain_hist_column and 'CoV1' in rain_hist_column and 'Prob Dist.1' in rain_hist_column:
					rainfall_history_opt_str.set("Probabilistic Rainfall Gauge")

				# assign dictionary values 
				for row_idx, row_data in enumerate(rain_hist_data):
					if rainfall_history_opt_str.get() == "Uniform":
						rain_hist_t_dict[row_idx+1][0].set(row_data[0])  # start time
						rain_hist_t_dict[row_idx+1][1].set(row_data[1])	 # end time
						rain_hist_t_dict[row_idx+1][2][0].set(row_data[2])  # intensity

					elif rainfall_history_opt_str.get() == "GIS file":
						rain_hist_t_dict[row_idx+1][0].set(row_data[0])  # start time
						rain_hist_t_dict[row_idx+1][1].set(row_data[1])	 # end time
						rain_hist_t_dict[row_idx+1][2][1].set(row_data[2])  # intensity GIS file name

					elif rainfall_history_opt_str.get() == "Deterministic Rainfall Gauge":
						rain_hist_t_dict[row_idx+1][0].set(row_data[0])  # start time
						rain_hist_t_dict[row_idx+1][1].set(row_data[1])	 # end time
						start_idx = 2
						for i in range(int(len(rain_hist_column)-2)//3):
							rain_hist_t_dict[row_idx+1][2][i][0].set(row_data[start_idx])
							rain_hist_t_dict[row_idx+1][2][i][1].set(row_data[start_idx+1])
							rain_hist_t_dict[row_idx+1][2][i][2].set(row_data[start_idx+2])
							start_idx += 3

					elif rainfall_history_opt_str.get() == "Probabilistic Rainfall Gauge":
						rain_hist_t_dict[row_idx+1][0].set(row_data[0])  # start time
						rain_hist_t_dict[row_idx+1][1].set(row_data[1])	 # end time
						start_idx = 2
						for i in range(int(len(rain_hist_column)-2)//9):
							rain_hist_t_dict[row_idx+1][2][i][0].set(row_data[start_idx])
							rain_hist_t_dict[row_idx+1][2][i][1].set(row_data[start_idx+1])
							rain_hist_t_dict[row_idx+1][2][i][2].set(row_data[start_idx+2])
							rain_hist_t_dict[row_idx+1][2][i][3].set(row_data[start_idx+3])
							rain_hist_t_dict[row_idx+1][2][i][4].set(row_data[start_idx+4])
							rain_hist_t_dict[row_idx+1][2][i][5].set(row_data[start_idx+5])
							rain_hist_t_dict[row_idx+1][2][i][6].set(row_data[start_idx+6])
							rain_hist_t_dict[row_idx+1][2][i][7].set(row_data[start_idx+7])
							rain_hist_t_dict[row_idx+1][2][i][8].set(row_data[start_idx+8])
							start_idx += 9

				# update status to show similuation is running 
				status.config(text = "rainfall history loaded ")
		except:
			pass

		return None

	# create template for material properties CSV file
	def csv_material_template_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# create csv template
		csv_temp_header = ['ID']

		# hydro
		if infil_model_str.get() == "Green-Ampt":
			csv_temp_header_pre = ['k_sat (m/s)', 'initial_suction (kPa)', 'SWCC_a (kPa)', 'SWCC_n', 'SWCC_m', 'theta_sat', 'theta_residual', 'soil_m_v', 'max_surface_storage (m)']

			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)", f"{htxt} Min", f"{htxt} Max"])	
		
		elif infil_model_str.get() == "Iverson":
			csv_temp_header_pre = ['k_sat (m/s)', 'diffusivity (m^2/s)']

			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)"])	

		# soil
		if slope_model_str.get() in ["Infinite Slope", "3D Translational Slide (3DTS)"]:
			csv_temp_header_pre = ['soil unit weight (kN/m^3)','phi (deg)', 'phi_b (deg)', 'c/Su (kPa)']

			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)", f"{htxt} Min", f"{htxt} Max"])	

		elif slope_model_str.get() in ["3D Normal", "3D Bishop", "3D Janbu"]:
			csv_temp_header_pre = ['soil unit weight (kN/m^3)','phi (deg)', 'c/Su (kPa)']

			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)"])	

		# root
		if root_reinforced_model_str.get() == "Constant with Depth":
			csv_temp_header_pre = ['root unit weight (kN/m^3)', 'root c_base (kPa)', 'root c_side (kPa)', 'root depth (m)']
			
			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)", f"{htxt} Min", f"{htxt} Max"])

		elif root_reinforced_model_str.get() == "van Zadelhoff et al. (2021)":
			csv_temp_header_pre = ['root unit weight (kN/m^3)', 'root alpha2', 'root beta2', 'root RR_max (kN/m)']

			if mc_iterations_int.get() == 1 or mat_assign_opt_str.get() == "GIS files":
				csv_temp_header.extend(csv_temp_header_pre)
			elif mc_iterations_int.get() > 1:
				for htxt in csv_temp_header_pre: 
					csv_temp_header.extend([f"{htxt} mean", f"{htxt} CoV", f"{htxt} Prob. Dist.", f"{htxt} CorL X (m)", f"{htxt} CorL Y (m)", f"{htxt} Min", f"{htxt} Max"])

		# load input file
		temp_file = filedialog.asksaveasfile(initialdir=file_path, title="Save material template CSV file", mode='w', defaultextension=".csv", filetypes=[("comma-separated value","*.csv")])

		# asksaveasfile return `None` if dialog closed with "cancel".
		try:
			if temp_file is None:
				return

			elif len(temp_file.name) > 0:
				file_path_name = temp_file.name
				file_naming_list = file_path_name.split("/")
				# file_name_only = file_naming_list[-1]

				with open(file_path_name, 'w', newline='') as temp_file:
					csv_temp_writer = csv.writer(temp_file)
					csv_temp_writer.writerow(csv_temp_header[:])

				# update status to show similuation is running 
				status.config(text = "Material CSV file created ")

			else:
				return

		except:
			return 

	# open material CSV file and fill in data
	def open_material_csv_file_command():
		# if input directory loading was done previously once and is valid, then reopen the input folder 
		try:
			if len(input_folder_entry.get()) > 0 and os.path.isdir(str(input_folder_entry.get())):
				status.config(text="selecting new input folder path ")
				file_path = str(input_folder_entry.get())
			# if invalid link, then by default open document
			else:
				status.config(text="")
				file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# if brand new, then by default open document
		except:
			status.config(text="")
			file_path = "C:/Users/"+os.getlogin()+'/Documents'

		# load directory
		selected_mat_csv_file = filedialog.askopenfilename(initialdir=file_path, 
								title="Select material data CSV file",
								filetypes=(
									("comma-separated value", "*.csv"),
								)   # only open valid type of format
							)

		# matching key and index
		matching_mat_csv_to_mat_data_key_dict = {
			'k_sat (m/s)': 'hydraulic_k_sat',
			'initial_suction (kPa)': 'hydraulic_initial_suction',
			'SWCC_a (kPa)': 'hydraulic_SWCC_a',
			'SWCC_n': 'hydraulic_SWCC_n',
			'SWCC_m': 'hydraulic_SWCC_m',
			'theta_sat': 'hydraulic_theta_sat',
			'theta_residual': 'hydraulic_theta_residual',
			'soil_m_v': 'hydraulic_soil_m_v',
			'max_surface_storage (m)': 'hydraulic_max_surface_storage',
			'diffusivity (m^2/s)': 'hydraulic_diffusivity',

			'soil unit weight (kN/m^3)': 'soil_unit_weight',
			'phi (deg)': 'soil_phi',
			'phi_b (deg)': 'soil_phi_b',
			'c/Su (kPa)': 'soil_c',

			'root unit weight (kN/m^3)': 'root_unit_weight',
			'root c_base (kPa)': 'root_c_base',
			'root c_side (kPa)': 'root_c_side',
			'root depth (m)': 'root_root_depth',
			'root alpha2': 'root_alpha2',
			'root beta2': 'root_beta2',
			'root RR_max (kN/m)': 'root_RR_max'
		}

		matching_mat_csv_to_mat_list_index_dict = {
			" mean": 0,
			" CoV": 1,
			" Prob. Dist.": 2,
			" CorL X (m)": 3,
			" CorL Y (m)": 4,
			" Min": 5,
			" Max": 6
		}
		
		# display output folder location in the output text
		try:
			if len(selected_mat_csv_file) > 0 and os.path.isfile(selected_mat_csv_file):

				# open data			
				mat_df = pd.read_csv(selected_mat_csv_file)

				# assign data
				for col_head, col_data in mat_df.items():
		
					if col_head == "ID":
						continue

					# match key and index to place
					matched_key = None 
					for key, value in matching_mat_csv_to_mat_data_key_dict.items():
						if key in col_head:
							matched_key = value
							break
					
					match_list_index = 0
					for key, value in matching_mat_csv_to_mat_list_index_dict.items():
						if key in col_head:
							match_list_index = value
							break

					# fill data							
					for row_idx, mat_data in enumerate(col_data):
						mID = mat_df["ID"][row_idx]
         
						if mat_data not in ["Normal", "normal", "NORMAL", "Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL", "inf", "Inf", "INF"]:
							if is_int(str(mat_data)) or is_float(str(mat_data)):
								mat_data_dict[mID][matched_key][match_list_index].set(mat_data)
							else:   # most likely a filename given in string
								mat_data_GIS_dict[matched_key].set(mat_data)

						elif mat_data in ["Normal", "normal", "NORMAL"]: 
							mat_data_dict[mID][matched_key][match_list_index].set("Normal")
						
						elif mat_data in ["Lognormal", "LogNormal", "lognormal", "LOGNORMAL", "Log-normal", "Log-Normal", "log-normal", "LOG-NORMAL", "Log normal", "Log Normal", "log normal", "LOG NORMAL", "Log_normal", "log_normal", "LOG_NORMAL"]: 
							mat_data_dict[mID][matched_key][match_list_index].set("Lognormal")

						elif mat_data in ["inf", "Inf", "INF"]: 
							mat_data_dict[mID][matched_key][match_list_index].set("inf")

				# add data not from CSV files
				for mIDx in range(1, 11):
					if infil_model_str.get() == "Iverson":
						mat_data_dict[mIDx]["hydraulic_SWCC_model"].set("Iverson")
						mat_data_GIS_dict["hydraulic_SWCC_model"].set("Iverson")
					else:
						mat_data_dict[mIDx]["hydraulic_SWCC_model"].set(SWCC_model_str.get())
						mat_data_GIS_dict["hydraulic_SWCC_model"].set(SWCC_model_str.get())

					mat_data_dict[mIDx]["root_model"].set(root_reinforced_model_str.get())
					mat_data_GIS_dict["root_model"].set(root_reinforced_model_str.get())

				# update status to show similuation is running 
				status.config(text = "material data CSV file loaded ")

		except:
			pass

		return None

	###########################################################################
	### Series of label, inputs, button and menus
	###########################################################################
	######################################
	## Software Information
	######################################
	# display input file name - or user can directly type in the name
	software_label = tk.Label(GUI_frame, text="Robust Areal Landslide Prediction (RALP)", font=("Arial", 16, 'bold')) 
	creator_label = tk.Label(GUI_frame, text="Dr. Enok Cheon (3DTSP & GUI) and Dr. Emir A. Oguz (3DPLS) - ver 1.00", font=("Arial", 12)) 

	# title and version
	software_label.grid(row=0, column=0, columnspan=8, padx=10, pady=(10,5), sticky="we")
	creator_label.grid(row=1, column=0, columnspan=8, padx=10, sticky="we")

	######################################
	# line separator - SW info vs project name
	######################################
	separator_col1_a = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col1_a.grid(row=2, column=0, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	## JSON overall 3DTSP folder directory
	######################################
	# display input folder locations - or user can directly type in the name
	overall_input_folder_label = tk.Label(GUI_frame, text="Restart JSON", font=("Arial", 12, 'bold'), anchor="w", justify="left")  
	overall_input_folder_str = tk.StringVar()
	overall_input_folder_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=overall_input_folder_str) 
	overall_input_folder_button = tk.Button(GUI_frame, text="Select File", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_overall_input_JSON_YAML_file_command) 

	overall_input_folder_label.grid(row=3, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	overall_input_folder_button.grid(row=3, column=1, columnspan=1, padx=5, pady=5)
	overall_input_folder_entry.grid(row=3, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## project name
	######################################
	"""
	label -> fixed text labelling each inputs
	str -> the variable that is saves the data into
	entry -> the textbox where user inputs the information
	"""

	# project name
	project_name_label = tk.Label(GUI_frame, text="Project Name", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	project_name_str = tk.StringVar()
	project_name_str.set("Project_number_000") 
	project_name_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=project_name_str) 

	project_name_label.grid(row=4, column=0, padx=5, pady=(0,5), sticky="w")
	project_name_entry.grid(row=4, column=1, columnspan=7, padx=5, sticky="we")

	######################################
	## input folder directory
	######################################
	# display input folder locations - or user can directly type in the name
	input_folder_label = tk.Label(GUI_frame, text="Input Directory", font=("Arial", 12, 'bold'), anchor="w", justify="left")  
	input_folder_str = tk.StringVar()
	input_folder_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=input_folder_str) 
	input_folder_button = tk.Button(GUI_frame, text="Select Folder", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_input_folder_command) 

	input_folder_label.grid(row=5, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	input_folder_button.grid(row=5, column=1, columnspan=1, padx=5, pady=5)
	input_folder_entry.grid(row=5, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## output folder directory
	######################################
	# display output folder locations - or user can directly type in the name
	output_folder_label = tk.Label(GUI_frame, text="Results Directory", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	output_folder_str = tk.StringVar()
	output_folder_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=output_folder_str) 
	output_folder_button = tk.Button(GUI_frame, text="Select Folder", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_output_folder_command) 

	output_folder_label.grid(row=6, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	output_folder_button.grid(row=6, column=1, columnspan=1, padx=5, pady=5)
	output_folder_entry.grid(row=6, column=2, columnspan=6, padx=5, pady=5, sticky="we")
	
	######################################
	# line separator - directories vs topographic inputs
	######################################
	separator_col1_b = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col1_b.grid(row=7, column=0, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	# Section Title - topographic inputs
	######################################
	topography_input = tk.Label(GUI_frame, text="Topography and GIS Input", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	topography_input.grid(row=8, column=0, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	## DEM - topographic inputs
	######################################
	# DEM file name
	DEM_filename_label = tk.Label(GUI_frame, text="DEM", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	DEM_filename_str = tk.StringVar()
	DEM_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=DEM_filename_str) 
	DEM_filename_button = tk.Button(GUI_frame, text="Select GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_DEM_file_command) 

	DEM_filename_label.grid(row=9, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	DEM_filename_button.grid(row=9, column=1, columnspan=1, padx=5, pady=5)
	DEM_filename_entry.grid(row=9, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## soil depth - topographic inputs
	######################################
	##############
	# soil depth inputs
	##############
	# option 1: ["uniform", H] - soil thickness = H
	uniform_soil_depth_double = tk.DoubleVar()

	# option 2: ["GIS", "soil thickness filename"] - soil thickness at each DEM cell provided in GIS file
	GIS_soil_depth_str = tk.StringVar()

	# option 3: ["Holm and Edvarson - Norway", H_min, H_max] - soil thickness = -2.578*tan(dip) + 2.612
	# also when probabilistic noise introduced
	min_soil_depth_double = tk.DoubleVar()
	max_soil_depth_double = tk.DoubleVar()

	# option 4: ["general multiregression", "linear"/"power", H_min, H_max, b0, ["param_1_filename", b1], ["param_2_filename", b2], ...] 
	#             - "linear" : soil thickness = b0 + b1*param_1 + b2*param_2 + ... + bn*param_n
	#             - "power"  : soil thickness = b0 * (param_1**b1) * (param_2**b2) * ... * (param_n**bn)
	# assuming number of parameters (n) is at max 10
	gen_reg_intercept_double = tk.DoubleVar()  # b0
	gen_reg_param1_filename_str = tk.StringVar()  # param_1_filename
	gen_reg_param1_double = tk.DoubleVar()  # b1	
	gen_reg_param2_filename_str = tk.StringVar()  # param_2_filename
	gen_reg_param2_double = tk.DoubleVar()  # b2
	gen_reg_param3_filename_str = tk.StringVar()  # param_3_filename
	gen_reg_param3_double = tk.DoubleVar()  # b3
	gen_reg_param4_filename_str = tk.StringVar()  # param_4_filename
	gen_reg_param4_double = tk.DoubleVar()  # b4
	gen_reg_param5_filename_str = tk.StringVar()  # param_5_filename
	gen_reg_param5_double = tk.DoubleVar()  # b5
	gen_reg_param6_filename_str = tk.StringVar()  # param_6_filename
	gen_reg_param6_double = tk.DoubleVar()  # b6
	gen_reg_param7_filename_str = tk.StringVar()  # param_7_filename
	gen_reg_param7_double = tk.DoubleVar()  # b7	
	gen_reg_param8_filename_str = tk.StringVar()  # param_8_filename
	gen_reg_param8_double = tk.DoubleVar()  # b8
	gen_reg_param9_filename_str = tk.StringVar()  # param_9_filename
	gen_reg_param9_double = tk.DoubleVar()  # b9
	gen_reg_param10_filename_str = tk.StringVar()  # param_10_filename
	gen_reg_param10_double = tk.DoubleVar()  # b10	

	# any probabilistic
	# option 1: ["prob - uniform", H_Mean, coefficient of variation (CoV), H_Minimum, H_Maximum] 
	# option 2: ["prob - GIS", "soil thickness filename", coefficient of variation (CoV), H_Minimum, H_Maximum] 
	#             - mean soil thickness at each DEM cell provided in GIS file
	# option 3: ["prob - Holm and Edvarson - Norway", coefficient of variation (CoV), H_Minimum, H_Maximum] 
	#             - mean soil thickness = -2.578*tan(dip) + 2.612
	# option 4: ["prob - general multiregression", "linear"/"power", coefficient of variation (CoV), H_Minimum, H_Maximum, b0, ["param_1_filename", b1], ["param_2_filename", b2], ...] 
	#             - "linear" : mean soil thickness = b0 + b1*param_1 + b2*param_2 + ... + bn*param_n
	#             - "power"  : mean soil thickness = b0 * (param_1**b1) * (param_2**b2) * ... * (param_n**bn)
	soil_depth_probabilistic_check_int = tk.IntVar()
	soil_depth_probabilistic_check_int.set(0)  # 0: no probabilistic, 1: probabilistic
	soil_depth_probabilistic_cov = tk.DoubleVar()
	soil_depth_probabilistic_cov.set(0.0)

	##############
	# soil depth model option
	##############
	# if checkbox is selected, probabilistic soil thickness considered
	soil_depth_prob_check_label = tk.Label(GUI_frame, text="Probabilistically Vary Depth", font=("Arial", 12), anchor="w", justify="left")
	soil_depth_prob_checkbutton = tk.Checkbutton(GUI_frame, variable=soil_depth_probabilistic_check_int, onvalue=1, offvalue=0)

	# assign data
	soil_depth_opt_label = tk.Label(GUI_frame, text="Soil Depth", font=("Arial", 12, 'bold'), anchor="w", justify="left")
	soil_depth_opt_str = tk.StringVar()
	# combo -> dropdown menus
	soil_depth_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Uniform Depth", "GIS file", "Holm (2012) & Edvarson (2013)", "Linear Multiregression", "Power Multiregression"],
		textvariable = soil_depth_opt_str,
		width=10,
		font=("Arial", 12)
	)
	soil_depth_opt_combo.current(0)   # default "Uniform Depth" - indicated by index number from values
	soil_depth_data_assign_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=soil_input_func)

	soil_depth_opt_label.grid(row=10, column=0, columnspan=1,  padx=5, pady=(0,5), sticky="we")

	soil_depth_prob_check_label.grid(row=10, column=1, columnspan=6, padx=5, pady=(0,5), sticky="we")
	soil_depth_prob_checkbutton.grid(row=10, column=7, columnspan=1, padx=(27, 0), pady=5, sticky="w")

	soil_depth_opt_combo.grid(row=11, column=1, columnspan=6, padx=5, pady=5, sticky="we")
	soil_depth_data_assign_button.grid(row=11, column=7, columnspan=1, padx=5, pady=5, sticky="e")


	# # check button
	# def check_soil():
	# 	print([
	# 		soil_depth_opt_str.get(),
	# 		uniform_soil_depth_double.get(),
	# 		GIS_soil_depth_str.get(),
	# 		min_soil_depth_double.get(),
	# 		max_soil_depth_double.get(),
	# 		gen_reg_intercept_double.get(),
	# 		gen_reg_param1_filename_str.get(),
	# 		gen_reg_param1_double.get(),
	# 		gen_reg_param2_filename_str.get(),
	# 		gen_reg_param2_double.get(),
	# 		gen_reg_param3_filename_str.get(),
	# 		gen_reg_param3_double.get(),
	# 		gen_reg_param4_filename_str.get(),
	# 		gen_reg_param4_double.get(),
	# 		gen_reg_param5_filename_str.get(),
	# 		gen_reg_param5_double.get(),
	# 		gen_reg_param6_filename_str.get(),
	# 		gen_reg_param6_double.get(),
	# 		gen_reg_param7_filename_str.get(),
	# 		gen_reg_param7_double.get(),
	# 		gen_reg_param8_filename_str.get(),
	# 		gen_reg_param8_double.get(),
	# 		gen_reg_param9_filename_str.get(),
	# 		gen_reg_param9_double.get(),
	# 		gen_reg_param10_filename_str.get(),
	# 		gen_reg_param10_double.get()
	# 	])
	# check_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=check_soil)
	# check_button.grid(row=12, column=0, columnspan=1, padx=5, pady=5, sticky="e")

	######################################
	## Groundwater table   
	######################################
	##############
	# groundwater table input option
	##############
	groundwater_opt_label = tk.Label(GUI_frame, text="Groundwater", font=("Arial", 12, 'bold'), anchor="w", justify="left")
	groundwater_opt_str = tk.StringVar()
	groundwater_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Thickness Above Bedrock", "Depth From Surface", "% of Soil Thickness Above Bedrock", "% of Soil Thickness From Surface", "GWT elevation GIS"],
		textvariable=groundwater_opt_str,
		width=10,
		font=("Arial", 12)
	)
	groundwater_opt_combo.current(0) # default "On Top of Bedrock Layer" - indicated by index number from values
	groundwater_data_assign_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=gwt_input_func)

	groundwater_opt_label.grid(row=12, column=0, columnspan=1,  padx=5, pady=(0,5), sticky="w")
	groundwater_opt_combo.grid(row=12, column=1, columnspan=6, padx=5, pady=5, sticky="we")
	groundwater_data_assign_button.grid(row=12, column=7, columnspan=1, padx=5, pady=5, sticky="e")

	##############
	# groundwater inputs
	##############
	# option 1: ["thickness above bedrock", thickness] - groundwater table elevation = bedrock surface elevation + thickness 
	# option 2: ["depth from surface", thickness] - groundwater table elevation = ground surface elevation - thickness
	# option 3: ["percentage of the soil thickness above bedrock", percentage] - groundwater table elevation = bedrock surface elevation + (percentage/100)*soil thickness
	# option 4: ["percentage of the soil thickness from surface", percentage] - groundwater table elevation = ground surface elevation - (percentage/100)*soil thickness
	# option 5: ["GWT elevation GIS ", file path and name] - groundwater table elevation
	gwt_value_double = tk.DoubleVar()  # groundwater table value - thickness or percentage
	gwt_GIS_filename_str = tk.StringVar()  # groundwater GIS file name - for RiZero GIS or cell-based GIS data option

	# # check button
	# def check_gwt():
	# 	print([
	# 		gwt_value_double.get(),
	# 		gwt_GIS_filename_str.get(),
	# 		groundwater_opt_str.get()
	# 	])
	# check_button = tk.Button(GUI_frame, text="Check", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=check_gwt)
	# check_button.grid(row=18, column=0, columnspan=1, padx=5, pady=5, sticky="e")

	##############
	# RiZero GIS file
	##############
	rizero_value_double = tk.DoubleVar()  # RiZero uniform value - thickness or percentage
	rizero_GIS_filename_str = tk.StringVar()  # RiZero GIS file name - for RiZero GIS or cell-based  

	RiZero_opt_label = tk.Label(GUI_frame, text="RiZero", font=("Arial", 12, 'bold'), anchor="w", justify="left")
	RiZero_opt_str = tk.StringVar()
	RiZero_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Uniform", "GIS file"],
		textvariable=RiZero_opt_str,
		width=10,
		font=("Arial", 12)
	)
	RiZero_opt_combo.current(0) # default "Uniform" - indicated by index number from values
	RiZero_assign_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=rizero_input_func)

	RiZero_opt_label.grid(row=13, column=0, columnspan=1,  padx=5, pady=(0,5), sticky="w")
	RiZero_opt_combo.grid(row=13, column=1, columnspan=6, padx=5, pady=5, sticky="we")
	RiZero_assign_button.grid(row=13, column=7, columnspan=1, padx=5, pady=5, sticky="e")

	######################################
	## dip surface - topographic inputs
	######################################
	# surface topography dip file name
	surf_dip_filename_label = tk.Label(GUI_frame, text="Surface Dip", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	surf_dip_filename_str = tk.StringVar()
	surf_dip_filename_str.set("(optional)") 
	surf_dip_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=surf_dip_filename_str)
	surf_dip_filename_button = tk.Button(GUI_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_surf_dip_file_command) 

	surf_dip_filename_label.grid(row=14, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	surf_dip_filename_button.grid(row=14, column=1, columnspan=1, padx=5, pady=5)
	surf_dip_filename_entry.grid(row=14, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## dip direction surface - topographic inputs
	######################################
	# surface topography dip direction file name
	surf_aspect_filename_label = tk.Label(GUI_frame, text="Surface Aspect", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	surf_aspect_filename_str = tk.StringVar()
	surf_aspect_filename_str.set("(optional)") 
	surf_aspect_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=surf_aspect_filename_str)
	surf_aspect_filename_button = tk.Button(GUI_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_surf_aspect_file_command) 

	surf_aspect_filename_label.grid(row=15, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	surf_aspect_filename_button.grid(row=15, column=1, columnspan=1, padx=5, pady=5)
	surf_aspect_filename_entry.grid(row=15, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## dip base - topographic inputs
	######################################
	# base topography dip file name
	base_dip_filename_label = tk.Label(GUI_frame, text="Bedrock Dip", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	base_dip_filename_str = tk.StringVar()
	base_dip_filename_str.set("(optional)") 
	base_dip_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=base_dip_filename_str)
	base_dip_filename_button = tk.Button(GUI_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_base_dip_file_command) 

	base_dip_filename_label.grid(row=16, column=0, columnspan=1, padx=5, pady=(0,5), sticky="w")
	base_dip_filename_button.grid(row=16, column=1, columnspan=1, padx=5, pady=5)
	base_dip_filename_entry.grid(row=16, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## dip direction base - topographic inputs
	######################################
	# surface topography dip direction file name
	base_aspect_filename_label = tk.Label(GUI_frame, text="Bedrock Aspect", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	base_aspect_filename_str = tk.StringVar()
	base_aspect_filename_str.set("(optional)") 
	base_aspect_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=base_aspect_filename_str)
	base_aspect_filename_button = tk.Button(GUI_frame, text="Open GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_base_aspect_file_command) 
 
	base_aspect_filename_label.grid(row=17, column=0, columnspan=1,  padx=5, pady=(0,5), sticky="w")
	base_aspect_filename_button.grid(row=17, column=1, columnspan=1, padx=5, pady=5)
	base_aspect_filename_entry.grid(row=17, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## local cell size - DEM to slopes
	######################################
	# size of DEM used to calculate topography dip and dip directions
	local_cell_DEM2dip_label = tk.Label(GUI_frame, text="Local Cell Size (Slopes from DEM)", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	local_cell_DEM2dip_int = tk.IntVar()
	local_cell_DEM2dip_int.set(1) 
	local_cell_DEM2dip_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=local_cell_DEM2dip_int)

	local_cell_DEM2dip_label.grid(row=18, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")
	local_cell_DEM2dip_entry.grid(row=18, column=2, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## Column 1 and 2 separator
	######################################
	separator_col1_col2 = ttk.Separator(GUI_frame, orient='vertical')
	separator_col1_col2.grid(row=0, column=8, rowspan=19, padx=1, pady=5, sticky="ns")

	######################################
	# Section Title - topographic inputs
	######################################
	slope_stability_analysis_input = tk.Label(GUI_frame, text="Slope Stability Analysis", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	slope_stability_analysis_input.grid(row=0, column=9, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	## Slope Model Option
	######################################
	slope_model_label = tk.Label(GUI_frame, text="Slope Model", font=("Arial", 12, "bold"), anchor="w", justify="left")
	slope_model_str = tk.StringVar()
	slope_model_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Skip (only perform infiltration)", "Infinite Slope", "3D Translational Slide (3DTS)", "3D Normal", "3D Bishop", "3D Janbu"],
		textvariable=slope_model_str,
		width=15,
		font=("Arial", 12)
	)
	slope_model_combo.current(2) # default "3D Translational Slide (3DTS)" (for now) - indicated by index number from values

	slope_model_str.trace_add("write", slope_model_func)  	# disable and able based combobox option

	slope_model_label.grid(row=1, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	slope_model_combo.grid(row=1, column=11, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	## 3DTS Slip Surface Option
	######################################
	# labels
	slip_surface_3DTS_label = tk.Label(GUI_frame, text="3DTS Slip Surface", font=("Arial", 12, "bold"), anchor="w", justify="left")
	min_cell_3DTS_label = tk.Label(GUI_frame, text="Min Cell", font=("Arial", 12), anchor="w", justify="left")
	max_cell_3DTS_label = tk.Label(GUI_frame, text="Max Cell", font=("Arial", 12), anchor="w", justify="left")
	superellipse_power_3DTS_label = tk.Label(GUI_frame, text="Superellipse Power", font=("Arial", 12), anchor="w", justify="left")
	superellipse_eccen_ratio_3DTS_label = tk.Label(GUI_frame, text="Superellipse Eccentricity Ratio", font=("Arial", 12), anchor="w", justify="left")

	# input variables
	min_cell_3DTS_int = tk.IntVar()
	max_cell_3DTS_int = tk.IntVar() 
	superellipse_power_3DTS_str = tk.StringVar()
	superellipse_eccen_ratio_3DTS_str = tk.StringVar()

	# initial input variables
	min_cell_3DTS_int.set(3)
	max_cell_3DTS_int.set(6)
	superellipse_power_3DTS_str.set("1.0, 2.0, 10.0")
	superellipse_eccen_ratio_3DTS_str.set("1.0, 1.3333, 1.5, 2.0")

	# entry box 
	min_cell_3DTS_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=min_cell_3DTS_int)
	max_cell_3DTS_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=max_cell_3DTS_int)
	superellipse_power_3DTS_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=superellipse_power_3DTS_str)
	superellipse_eccen_ratio_3DTS_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=superellipse_eccen_ratio_3DTS_str)

	# grid placement 
	slip_surface_3DTS_label.grid(row=2, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")

	min_cell_3DTS_label.grid(row=2, column=11, columnspan=1, padx=5, pady=(0,5), sticky="we")
	min_cell_3DTS_entry.grid(row=2, column=12, columnspan=2, padx=5, pady=(0,5), sticky="we")
	
	max_cell_3DTS_label.grid(row=2, column=14, columnspan=1, padx=5, pady=(0,5), sticky="we")
	max_cell_3DTS_entry.grid(row=2, column=15, columnspan=2, padx=5, pady=(0,5), sticky="we")
	
	superellipse_power_3DTS_label.grid(row=3, column=9, columnspan=3, padx=5, pady=(0,5), sticky="w")
	superellipse_power_3DTS_entry.grid(row=3, column=12, columnspan=5, padx=5, pady=(0,5), sticky="we")
	
	superellipse_eccen_ratio_3DTS_label.grid(row=4, column=9, columnspan=3, padx=5, pady=(0,5), sticky="w")
	superellipse_eccen_ratio_3DTS_entry.grid(row=4, column=12, columnspan=5, padx=5, pady=(0,5), sticky="we")

	######################################
	## 3DTS Analysis Option
	######################################
	##############
	# side resistance option
	##############
	resistances_3DTS_label = tk.Label(GUI_frame, text="3DTS Resistances", font=("Arial", 12, "bold"), anchor="w", justify="left")
	side_resistance_3DTS_label = tk.Label(GUI_frame, text="Side", font=("Arial", 12), anchor="w", justify="left")
	side_resistance_3DTS_int = tk.IntVar()
	side_resistance_3DTS_int.set(1) 
	side_resistance_3DTS_checkbutton = tk.Checkbutton(GUI_frame, variable=side_resistance_3DTS_int, onvalue=1, offvalue=0)

	resistances_3DTS_label.grid(row=5, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	side_resistance_3DTS_label.grid(row=5, column=11, columnspan=1, padx=5, pady=(0,5), sticky="w")
	side_resistance_3DTS_checkbutton.grid(row=5, column=12, padx=5, pady=5, sticky="w")

	##############
	## root reinforcement Option
	##############
	root_reinforced_model_label = tk.Label(GUI_frame, text="Root", font=("Arial", 12), anchor="w", justify="left")
	root_reinforced_model_str = tk.StringVar()
	root_reinforced_model_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["None", "Constant with Depth", "van Zadelhoff et al. (2021)"],
		textvariable=root_reinforced_model_str,
		width=10,
		font=("Arial", 12)
	)
	root_reinforced_model_combo.current(2) # default "van Zadelhoff et al. (2021)" (for now) - indicated by index number from values

	root_reinforced_model_label.grid(row=5, column=13, columnspan=1, padx=5, pady=(0,5), sticky="w")
	root_reinforced_model_combo.grid(row=5, column=14, columnspan=3, padx=5, pady=5, sticky="we")

	######################################
	## 3DPLS Analysis Option
	######################################
	##############
	# Drained or Undrained
	##############
	analysis_opt_3DPLS_label = tk.Label(GUI_frame, text="Type", font=("Arial", 12, "bold"), anchor="w", justify="left")
	analysis_opt_3DPLS_str = tk.StringVar()
	analysis_opt_3DPLS_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Drained", "Undrained"],
		textvariable=analysis_opt_3DPLS_str,
		width=10,
		font=("Arial", 12)
	)
	analysis_opt_3DPLS_combo.current(0) # default "Drained" (for now) - indicated by index number from values

	analysis_opt_3DPLS_label.grid(row=6, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	analysis_opt_3DPLS_combo.grid(row=6, column=11, columnspan=3, padx=5, pady=5, sticky="we")

	##############
	# Ellipsoidal slip surface
	##############
	# label
	ellipsoidal_slip_surface_label = tk.Label(GUI_frame, text="Ellipsoidal Slip Surface", font=("Arial", 12, "bold"), anchor="w", justify="left")
	ellipsoidal_slip_surface_a_label = tk.Label(GUI_frame, text="a (m)", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_b_label = tk.Label(GUI_frame, text="b (m)", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_c_label = tk.Label(GUI_frame, text="c (m)", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_z_label = tk.Label(GUI_frame, text="z (m)", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_alpha_comp_label = tk.Label(GUI_frame, text="Ellipsoidal \u03B1 Comp", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_alpha_label = tk.Label(GUI_frame, text="\u03B1 (\u00B0)", font=("Arial", 12), anchor="w", justify="left")
	ellipsoidal_slip_surface_min_sub_div_label = tk.Label(GUI_frame, text="Minimum Soil Column Number", font=("Arial", 12), anchor="w", justify="left")

	# parameters required
	ellipsoidal_slip_surface_a_double = tk.DoubleVar()
	ellipsoidal_slip_surface_b_double = tk.DoubleVar()
	ellipsoidal_slip_surface_c_double = tk.DoubleVar()
	ellipsoidal_slip_surface_z_double = tk.DoubleVar()
	ellipsoidal_slip_surface_alpha_double = tk.DoubleVar()
	ellipsoidal_slip_surface_alpha_comp_int = tk.IntVar()
	ellipsoidal_slip_surface_min_sub_div_int = tk.IntVar()

	# default values
	ellipsoidal_slip_surface_a_double.set(100.0)
	ellipsoidal_slip_surface_b_double.set(20.0)
	ellipsoidal_slip_surface_c_double.set(2.5)
	ellipsoidal_slip_surface_z_double.set(1.0)
	ellipsoidal_slip_surface_alpha_comp_int.set(1)   # 0 = user-defined, 1 = automatically compute
	ellipsoidal_slip_surface_min_sub_div_int.set(200)      # minimum ellipsoidal subdivisions soil column number

	# entry 
	ellipsoidal_slip_surface_a_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_a_double)
	ellipsoidal_slip_surface_b_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_b_double)
	ellipsoidal_slip_surface_c_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_c_double)
	ellipsoidal_slip_surface_z_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_z_double)
	ellipsoidal_slip_surface_alpha_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_alpha_double)
	ellipsoidal_slip_surface_min_sub_div_entry = tk.Entry(GUI_frame, width=8, bd=3, font=("Arial", 12), textvariable=ellipsoidal_slip_surface_min_sub_div_int)

	# checkbox
	ellipsoidal_slip_surface_alpha_comp_checkbutton = tk.Checkbutton(GUI_frame, variable=ellipsoidal_slip_surface_alpha_comp_int, onvalue=1, offvalue=0)

	# layout
	ellipsoidal_slip_surface_label.grid(row=7, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")

	ellipsoidal_slip_surface_a_label.grid(row=7, column=11, columnspan=1, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_a_entry.grid(row=7, column=12, columnspan=2, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_b_label.grid(row=7, column=14, columnspan=1, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_b_entry.grid(row=7, column=15, columnspan=2, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_c_label.grid(row=8, column=11, columnspan=1, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_c_entry.grid(row=8, column=12, columnspan=2, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_z_label.grid(row=8, column=14, columnspan=1, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_z_entry.grid(row=8, column=15, columnspan=2, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_alpha_comp_label.grid(row=9, column=11, columnspan=2, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_alpha_comp_checkbutton.grid(row=9, column=13, columnspan=1, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_alpha_label.grid(row=9, column=14, columnspan=1, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_alpha_entry.grid(row=9, column=15, columnspan=2, padx=5, pady=5, sticky="we")

	ellipsoidal_slip_surface_min_sub_div_label.grid(row=10, column=11, columnspan=3, padx=5, pady=(0,5), sticky="w")
	ellipsoidal_slip_surface_min_sub_div_entry.grid(row=10, column=14, columnspan=3, padx=5, pady=(0,5), sticky="we")

	# by default it is 3DTS so disabled
	analysis_opt_3DPLS_combo.config(state="disable")
	ellipsoidal_slip_surface_a_entry.config(state="disable")
	ellipsoidal_slip_surface_b_entry.config(state="disable")
	ellipsoidal_slip_surface_c_entry.config(state="disable")
	ellipsoidal_slip_surface_z_entry.config(state="disable")
	ellipsoidal_slip_surface_alpha_comp_checkbutton.config(state="disable")
	ellipsoidal_slip_surface_alpha_entry.config(state="disable")
	ellipsoidal_slip_surface_min_sub_div_entry.config(state="disable")

	def ellipsoidal_slip_surface_alpha_comp_func(*args):
		if ellipsoidal_slip_surface_alpha_comp_int.get() >= 1:  # automatically calculate
			ellipsoidal_slip_surface_alpha_entry.config(state="disable")
		elif ellipsoidal_slip_surface_alpha_comp_int.get() == 0:  # user input
			ellipsoidal_slip_surface_alpha_entry.config(state="normal")

	# disable and able based combobox option
	ellipsoidal_slip_surface_alpha_comp_int.trace_add("write", ellipsoidal_slip_surface_alpha_comp_func)

	######################################
	# Critical FS
	######################################
	critical_FS_label = tk.Label(GUI_frame, text='Critical FS', font=("Arial", 12, "bold"), anchor="w", justify="left")
	critical_FS_double = tk.DoubleVar()
	critical_FS_double.set(1.0) 
	critical_FS_entry = tk.Entry(GUI_frame, width=7, bd=3, font=("Arial", 12), textvariable=critical_FS_double)

	critical_FS_label.grid(row=11, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	critical_FS_entry.grid(row=11, column=11, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	# Debris-Flow Criteria (Kang et al. 2012)
	######################################
	##############
	# debris flow criteria options
	##############
	debris_flow_criteria_label = tk.Label(GUI_frame, text="Debris-Flow Criteria", font=("Arial", 12, "bold"), anchor="w", justify="left")
	debris_flow_criteria_int = tk.IntVar()
	debris_flow_criteria_int.set(0) 
	debris_flow_criteria_checkbutton = tk.Checkbutton(GUI_frame, variable=debris_flow_criteria_int, onvalue=1, offvalue=0)

	debris_flow_criteria_int.trace_add("write", debris_flow_criteria_func)  	# disable and able based combobox option

	debris_flow_criteria_label.grid(row=12, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	debris_flow_criteria_checkbutton.grid(row=12, column=11, padx=5, pady=5, sticky="w")

	##############
	# Upload files
	##############
	debris_flow_criteria_upload_label = tk.Label(GUI_frame, text="Upload Files", font=("Arial", 12), anchor="w", justify="left")

	debris_flow_criteria_network_str = tk.StringVar()
	debris_flow_criteria_UCA_str = tk.StringVar()
	debris_flow_criteria_Criteria_str = tk.StringVar()
	
	debris_flow_criteria_network_buttom = tk.Button(GUI_frame, text="network", width=6, height=1, padx=10, pady=5, font=("Arial", 12), command=open_DFC_network_file_command) 
	debris_flow_criteria_UCA_buttom = tk.Button(GUI_frame, text="UCA", width=6, height=1, padx=10, pady=5, font=("Arial", 12), command=open_DFC_UCA_file_command) 
	debris_flow_criteria_Criteria_buttom = tk.Button(GUI_frame, text="Criteria", width=6, height=1, padx=10, pady=5, font=("Arial", 12), command=open_DFC_Criteria_file_command) 

	debris_flow_criteria_upload_label.grid(row=12, column=12, columnspan=2, padx=5, pady=(0,5), sticky="w")
	debris_flow_criteria_network_buttom.grid(row=12, column=14, padx=5, pady=5, sticky="we")
	debris_flow_criteria_UCA_buttom.grid(row=12, column=15, padx=5, pady=5, sticky="we")
	debris_flow_criteria_Criteria_buttom.grid(row=12, column=16, padx=5, pady=5, sticky="we")
	
	debris_flow_criteria_network_buttom.config(state="disabled")
	debris_flow_criteria_UCA_buttom.config(state="disabled")
	debris_flow_criteria_Criteria_buttom.config(state="disabled")

	######################################
	# line separator - Hydraulic vs Slope Stability inputs
	######################################
	separator_col2_a = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col2_a.grid(row=13, column=9, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	## Hydraulic Analysis Header
	######################################
	hydraulic_analysis_input = tk.Label(GUI_frame, text="Hydraulic Analysis", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	hydraulic_analysis_input.grid(row=14, column=9, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	## Rainfall History
	######################################
	##############
	# rainfall model option
	##############
	rainfall_history_label = tk.Label(GUI_frame, text="Rainfall History", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	rainfall_history_opt_str = tk.StringVar()
	# combo -> dropdown menus
	rainfall_history_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Uniform", "GIS file", "Deterministic Rainfall Gauge", "Probabilistic Rainfall Gauge"],
		textvariable=rainfall_history_opt_str,
		width=10,
		justify="left",
		font=("Arial", 12)
	)
	rainfall_history_opt_combo.current(0)  	 # default "Uniform" - indicated by index number from values	
	rainfall_history_assign_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=rainfall_history_func)

	rainfall_history_label.grid(row=15, column=9, columnspan=1,  padx=5, pady=(0,5), sticky="w")
	rainfall_history_opt_combo.grid(row=15, column=10, columnspan=6, padx=5, pady=5, sticky="we")
	rainfall_history_assign_button.grid(row=15, column=16, columnspan=1, padx=5, pady=5, sticky="e")

	##############
	# rainfall input
	##############
	# 1) value uniformly applied everywhere. format = int or float
	# 2) filename of GIS that provide spatially varying rainfall intensity. format = string (must contain the file extension)
	# 3) series of rain gauge points for nearest neighbor interpolation (or Voronoi diagram). format = [[X, Y, recorded rainfall intensity value in int or float], ...]
	# 4) probabilistic of rain gauge points for nearest neighbor interpolation (or Voronoi diagram). format = [[X, Y, Mean, CoV, Prob. Dist., Corr. Length X, Corr. Length Y, Min, Max], ...]

	# assume rainfall history is 100 entries long
	# assume rainfall gauge poitns are max 5 points
	rain_hist_t_dict = {}
	for time_step in range(1, 101):
		# [start time, end time, rainfall intensity data]
		# rainfall intensity data = [0uniform, 1GIS filename, 2{idx: [0X, 1Y, 2Mean, 3CoV, 4Prob. Dist., 5Corr. Length X, 6Corr. Length Y, 7Min, 8Max], ...}]
		rain_hist_t_dict[time_step] = [
	  		tk.DoubleVar(), # start time
			tk.DoubleVar(), # end time
			[
				tk.DoubleVar(), # uniform rainfall intensity
				tk.StringVar(), # GIS filename for rainfall intensity
				{ 	# [0X, 1Y, 2Mean, 3CoV, 4Prob. Dist., 5Corr. Length X, 6Corr. Length Y, 7Min, 8Max]
					0: [tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()], 
					1: [tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()], 
					2: [tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()], 
					3: [tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()], 
					4: [tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()] 
				} 
			]
		]

	######################################
	## Rainfall History Options
	######################################
	##############
	# rainfall intensity unit
	##############
	rainfall_intensity_unit_label = tk.Label(GUI_frame, text="Intensity Unit", font=("Arial", 12), anchor="w", justify="left")
	rainfall_intensity_unit_str = tk.StringVar()
	rainfall_intensity_unit_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["mm/hr", "cm/hr", "m/hr", "mm/min", "cm/min", "m/min", "mm/s", "cm/s", "m/s"],
		textvariable=rainfall_intensity_unit_str,
		width=8,
		font=("Arial", 12)
	)
	rainfall_intensity_unit_combo.current(0) # default "mm/hr" - indicated by index number from values

	rainfall_intensity_unit_label.grid(row=16, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	rainfall_intensity_unit_combo.grid(row=16, column=11, columnspan=2, padx=5, pady=5, sticky="we")

	intime_unit_str = tk.StringVar()
	intime_unit_str.set("hr")
	def rainfall_intensity_unit_str_func(*args):
		if rainfall_intensity_unit_str.get() in ["mm/hr", "cm/hr", "m/hr"]:
			intime_unit_str.set("hr")
		elif rainfall_intensity_unit_str.get() in ["mm/min", "cm/min", "m/min"]:
			intime_unit_str.set("min")
		elif rainfall_intensity_unit_str.get() in ["mm/s", "cm/s", "m/s"]:
			intime_unit_str.set("s")
	
	rainfall_intensity_unit_str.trace_add("write", rainfall_intensity_unit_str_func)

	##############
	# rainfall history subdivision
	##############
	# add more output datapoints between two time histories
	rainfall_time_sudiv_label = tk.Label(GUI_frame, text="Time Subdivision", font=("Arial", 12), anchor="w", justify="left")
	rainfall_time_sudiv_int = tk.IntVar()
	rainfall_time_sudiv_int.set(1) 
	rainfall_time_sudiv_entry = tk.Entry(GUI_frame, width=12, bd=3, font=("Arial", 12), textvariable=rainfall_time_sudiv_int)

	rainfall_time_sudiv_label.grid(row=16, column=13, columnspan=2, padx=5, pady=(0,5), sticky="w")
	rainfall_time_sudiv_entry.grid(row=16, column=15, columnspan=2, padx=5, pady=5, sticky="we")

	######################################
	## Infiltration Model Options
	######################################
	##############
	# Infiltration Hydraulic Model
	##############
	infil_model_label = tk.Label(GUI_frame, text="Infiltration Model", font=("Arial", 12, "bold"), anchor="w", justify="left")
	infil_model_str = tk.StringVar()
	infil_model_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Green-Ampt", "Iverson"],
		textvariable=infil_model_str,
		width=12,
		font=("Arial", 12)
	)
	infil_model_combo.current(0) # default "Green-Ampt" - indicated by index number from values
	infil_model_combo.config(state="disable") # default "Green-Ampt" based on 3DTSP

	infil_model_str.trace_add("write", infil_model_func)  	# disable and able based combobox option

	infil_model_label.grid(row=17, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	infil_model_combo.grid(row=17, column=11, columnspan=2, padx=5, pady=5, sticky="we")

	##############
	# SWCC model
	##############
	SWCC_model_label = tk.Label(GUI_frame, text="SWCC Model", font=("Arial", 12), anchor="w", justify="left")
	SWCC_model_str = tk.StringVar()
	SWCC_model_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["van Genuchten (1980)", "Fredlund and Xing (1994)"],
		textvariable=SWCC_model_str,
		width=10,
		font=("Arial", 12)
	)
	SWCC_model_combo.current(0) # default "van Genuchten (1980)" - indicated by index number from values

	SWCC_model_label.grid(row=17, column=13, columnspan=1, padx=5, pady=(0,5), sticky="w")
	SWCC_model_combo.grid(row=17, column=15, columnspan=2, padx=5, pady=5, sticky="we")

	##############
	# unit weight of water
	##############
	# if checkbox is selected, surface dip angle is considered for Green-Ampt Model
	unit_weight_water_label = tk.Label(GUI_frame, text=u'\u0263_w', font=("Arial", 12, "bold"), anchor="w", justify="left")
	unit_weight_water_double = tk.DoubleVar()
	if infil_model_str.get() == "Green-Ampt":
		unit_weight_water_double.set(9.81) 
	elif infil_model_str.get() == "Iverson":
		unit_weight_water_double.set(10.0)
	unit_weight_water_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=unit_weight_water_double)

	"""NOTE by ECo: Perhaps add option to allow change of water unit weight in Iverson"""
	# if infil_model_str.get() == "Iverson":
	# 	unit_weight_water_entry.config(state="disabled")

	unit_weight_water_label.grid(row=18, column=9, columnspan=2, padx=5, pady=(0,5), sticky="w")
	unit_weight_water_entry.grid(row=18, column=11, columnspan=2, padx=5, pady=5, sticky="we")

	##############
	# Green-Ampt surface infiltration option
	##############
	# if checkbox is selected, surface dip angle is considered for Green-Ampt Model
	surf_dip_for_GA_label = tk.Label(GUI_frame, text="Surface Dip for Green-Ampt", font=("Arial", 12, "bold"), anchor="w", justify="left")
	surf_dip_for_GA_int = tk.IntVar()
	surf_dip_for_GA_int.set(0) 
	surf_dip_for_GA_checkbutton = tk.Checkbutton(GUI_frame, variable=surf_dip_for_GA_int, onvalue=1, offvalue=0)

	surf_dip_for_GA_label.grid(row=18, column=13, columnspan=3, padx=5, pady=(0,5), sticky="w")
	surf_dip_for_GA_checkbutton.grid(row=18, column=16, padx=(5,5), pady=5, sticky="w")

	######################################
	## Column 2 and 3 separator
	######################################
	separator_col2_col3 = ttk.Separator(GUI_frame, orient='vertical')
	separator_col2_col3.grid(row=0, column=17, rowspan=19, padx=1, pady=5, sticky="ns")

	############################################################################
	## Landslide Susceptibility Header
	############################################################################
	######################################
	# Section Title - topographic inputs
	######################################
	prob_analysis_input = tk.Label(GUI_frame, text="Probabilistic Analysis", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	prob_analysis_input.grid(row=0, column=18, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	# Monte Carlo Simulation iterations
	######################################
	mc_iterations_label = tk.Label(GUI_frame, text="Monte Carlo Iterations", font=("Arial", 12, "bold"), anchor="w", justify="left")
	mc_iterations_int = tk.IntVar()
	mc_iterations_int.set(1000)  # default 1000 iterations
	mc_iterations_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=mc_iterations_int)

	mc_iterations_label.grid(row=1, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	mc_iterations_entry.grid(row=1, column=20, columnspan=6, padx=5, pady=5, sticky="we")

	######################################
	# random field method
	######################################
	random_field_method_label = tk.Label(GUI_frame, text="Random Field Method", font=("Arial", 12, "bold"), anchor="w", justify="left")
	random_field_method_str = tk.StringVar()
	random_field_method_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["CMD", "SCMD"],
		textvariable=random_field_method_str,
		width=10,
		font=("Arial", 12)
	)
	random_field_method_combo.current(1)   # default "SCMD" (for now) - indicated by index number from values
	random_field_method_combo.config(state="disable")  # disable by default - uses 3DTSP

	random_field_method_label.grid(row=2, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	random_field_method_combo.grid(row=2, column=20, columnspan=2, padx=5, pady=5, sticky="we")

	random_field_save_label = tk.Label(GUI_frame, text="Save Correlation Matrix", font=("Arial", 12, "bold"), anchor="w", justify="left")
	random_field_save_int = tk.IntVar()
	random_field_save_int.set(1) 
	random_field_save_checkbutton = tk.Checkbutton(GUI_frame, variable=random_field_save_int, onvalue=1, offvalue=0)

	random_field_save_label.grid(row=2, column=22, columnspan=3, padx=5, pady=(0,5), sticky="w")
	random_field_save_checkbutton.grid(row=2, column=25, columnspan=1, padx=5, pady=5, sticky="w")

	######################################
	# disable when deterministic analysis
	######################################
	def mc_iterations_func(*args):
		try:
			if mc_iterations_int.get() == "" or  mc_iterations_int.get() <= 1:  # deterministic
				random_field_method_combo.config(state="disable")
				random_field_save_checkbutton.config(state="disable")
			elif mc_iterations_int.get() > 1:  # probabilistic
				random_field_method_combo.config(state="normal")
				random_field_save_checkbutton.config(state="normal")
		except Exception as e:
			# print(f"Error occurred: {e}")
			mc_iterations_int.set(1)
			random_field_method_combo.config(state="disable")
			random_field_save_checkbutton.config(state="disable")

	# disable and able based combobox option
	mc_iterations_int.trace_add("write", mc_iterations_func)

	######################################
	# line separator - Landslide Susceptibility vs Material Assignment
	######################################
	separator_col3_a = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col3_a.grid(row=3, column=18, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	# Section Title - Material
	######################################
	material_assignment_input = tk.Label(GUI_frame, text="Material Properties Assignment", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	material_assignment_input.grid(row=4, column=18, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	# Assign Material Properties
	######################################
	##############
	# Assigning Material Options
	##############
	mat_assign_opt_label = tk.Label(GUI_frame, text="Material Assign", font=("Arial", 12, "bold"), anchor="w", justify="left")
	mat_assign_opt_str = tk.StringVar()
	mat_assign_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["Uniform", "Zone-Based", "GIS files"],
		textvariable=mat_assign_opt_str,
		width=10,
		font=("Arial", 12)
	)
	mat_assign_opt_combo.current(0) # default "Uniform" (for now) - indicated by index number from values

	num_mat_label = tk.Label(GUI_frame, text="Material Number", font=("Arial", 12), anchor="w", justify="left")
	num_mat_int = tk.IntVar(value=1)  # default number of parameters is 1
	num_mat_combo = ttk.Combobox(
			GUI_frame,
			state="readonly",
			values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
			textvariable=num_mat_int,
			width=5,
			font=("Arial", 12)
		)
	num_mat_combo.current(0)  # set default value to 1

	mat_assign_button = tk.Button(GUI_frame, text="Assign", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=mat_assign_func)

	mat_assign_opt_label.grid(row=5, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	mat_assign_opt_combo.grid(row=5, column=20, columnspan=2, padx=5, pady=5, sticky="we")
	num_mat_label.grid(row=5, column=22, columnspan=2, padx=5, pady=(0,5), sticky="w")
	num_mat_combo.grid(row=5, column=24, columnspan=1, padx=5, pady=(0,5), sticky="w")
	mat_assign_button.grid(row=5, column=25, padx=5, pady=5, sticky="w")

	##############
	# material input
	##############
	mat_zone_filename_str = tk.StringVar()

	# assume max material ID is 10 
	mat_data_dict = {}
	for mID in range(1, 11):
		# prob data format [0Mean, 1CoV, 2Prob. Dist., 3Corr. Length X, 4Corr. Length Y, 5Min, 6Max]
		mat_data_dict[mID] = {
			"hydraulic_k_sat": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_initial_suction": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_SWCC_model": tk.StringVar(),
			"hydraulic_SWCC_a": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_SWCC_n": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_SWCC_m": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_theta_sat": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_theta_residual": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_soil_m_v": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_max_surface_storage": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"hydraulic_diffusivity": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],

			"soil_unit_weight": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"soil_phi": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"soil_phi_b": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"soil_c": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
   
			"root_model": tk.StringVar(),
			"root_unit_weight": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_c_base": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_c_side": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_root_depth": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_alpha2": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_beta2": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()],
			"root_RR_max": [tk.DoubleVar(), tk.DoubleVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()]
		}

	# GIS data
	mat_data_GIS_dict = {
		"hydraulic_k_sat": tk.StringVar(),
		"hydraulic_initial_suction": tk.StringVar(),
		"hydraulic_SWCC_model": tk.StringVar(),
		"hydraulic_SWCC_a": tk.StringVar(),
		"hydraulic_SWCC_n": tk.StringVar(),
		"hydraulic_SWCC_m": tk.StringVar(),
		"hydraulic_theta_sat": tk.StringVar(),
		"hydraulic_theta_residual": tk.StringVar(),
		"hydraulic_soil_m_v": tk.StringVar(),
		"hydraulic_max_surface_storage": tk.StringVar(),

		"soil_unit_weight": tk.StringVar(),
		"soil_phi": tk.StringVar(),
		"soil_phi_b": tk.StringVar(),
		"soil_c": tk.StringVar(),

		"root_unit_weight": tk.StringVar(),
		"root_model": tk.StringVar(),
		"root_c_base": tk.StringVar(),
		"root_c_side": tk.StringVar(),
		"root_root_depth": tk.StringVar(),
		"root_alpha2": tk.StringVar(),
		"root_beta2": tk.StringVar(),
		"root_RR_max": tk.StringVar()
	}

	######################################
	# line separator - Material Assignment vs Landslide Comparison Analysis
	######################################
	separator_col3_b = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col3_b.grid(row=6, column=18, columnspan=8, padx=1, pady=5, sticky="we")

	############################################################################
	## Landslide Comparison Analysis
	############################################################################
	######################################
	# Section Title - topographic inputs
	######################################
	Compare_analysis_title = tk.Label(GUI_frame, text="Post-Analysis (3DPLS)", font=("Arial", 14, 'bold'), anchor="w", justify="left") 
	Compare_analysis_title.grid(row=7, column=18, columnspan=8, padx=1, pady=5, sticky="w")

	######################################
	## landslide source - topographic inputs
	######################################
	# landslide_source file name
	landslide_source_filename_label = tk.Label(GUI_frame, text="Landslide Source", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	landslide_source_filename_str = tk.StringVar()
	landslide_source_filename_str.set("(optional)")
	landslide_source_filename_entry = tk.Entry(GUI_frame, width=10, bd=3, font=("Arial", 12), textvariable=landslide_source_filename_str) 
	landslide_source_filename_button = tk.Button(GUI_frame, text="Select GIS", width=8, height=1, padx=10, pady=5, font=("Arial", 12), command=open_source_file_command) 

	landslide_source_filename_label.grid(row=8, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	landslide_source_filename_button.grid(row=8, column=20, columnspan=2, padx=5, pady=5)
	landslide_source_filename_entry.grid(row=8, column=22, columnspan=4, padx=5, pady=5, sticky="we")

	######################################
	# selected zones row (i) and columns (j)
	######################################
	inzone_title_label = tk.Label(GUI_frame, text="Investigation Zone", font=("Arial", 12, "bold"), anchor="w", justify="left")

	inzone_check_label = tk.Label(GUI_frame, text="Full Extent", font=("Arial", 12), anchor="w", justify="center")
	inzone_check_int = tk.IntVar()
	inzone_check_int.set(1) 
	inzone_check_checkbutton = tk.Checkbutton(GUI_frame, variable=inzone_check_int, onvalue=1, offvalue=0)

	inzone_min_i_label = tk.Label(GUI_frame, text="min row", font=("Arial", 12), anchor="w", justify="left")
	inzone_min_j_label = tk.Label(GUI_frame, text="min col", font=("Arial", 12), anchor="w", justify="left")
	inzone_max_i_label = tk.Label(GUI_frame, text="max row", font=("Arial", 12), anchor="w", justify="left")
	inzone_max_j_label = tk.Label(GUI_frame, text="max col", font=("Arial", 12), anchor="w", justify="left")

	inzone_min_i_int = tk.IntVar()
	inzone_min_j_int = tk.IntVar()
	inzone_max_i_int = tk.IntVar()
	inzone_max_j_int = tk.IntVar()

	inzone_min_i_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=inzone_min_i_int)
	inzone_min_j_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=inzone_min_j_int)
	inzone_max_i_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=inzone_max_i_int)
	inzone_max_j_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=inzone_max_j_int)

	inzone_min_i_entry.config(state="disable")  # disable by default since using full extent
	inzone_min_j_entry.config(state="disable")  # disable by default since using full extent
	inzone_max_i_entry.config(state="disable")  # disable by default since using full extent
	inzone_max_j_entry.config(state="disable")  # disable by default since using full extent

	inzone_title_label.grid(row=9, column=18, columnspan=2, padx=1, pady=5, sticky="w")
	
	inzone_check_label.grid(row=9, column=20, columnspan=2, padx=1, pady=5, sticky="w")
	inzone_check_checkbutton.grid(row=9, column=22, columnspan=1, padx=1, pady=5, sticky="w")

	inzone_min_i_label.grid(row=10, column=18, columnspan=1, padx=1, pady=5, sticky="w")
	inzone_min_j_entry.grid(row=10, column=19, columnspan=1, padx=1, pady=5, sticky="we")
	inzone_min_j_label.grid(row=10, column=20, columnspan=1, padx=1, pady=5, sticky="w")
	inzone_min_i_entry.grid(row=10, column=21, columnspan=1, padx=1, pady=5, sticky="we")
	inzone_max_i_label.grid(row=10, column=22, columnspan=1, padx=1, pady=5, sticky="w")
	inzone_max_i_entry.grid(row=10, column=23, columnspan=1, padx=1, pady=5, sticky="we")
	inzone_max_j_label.grid(row=10, column=24, columnspan=1, padx=1, pady=5, sticky="w")
	inzone_max_j_entry.grid(row=10, column=25, columnspan=1, padx=1, pady=5, sticky="we")

	######################################
	# disable when full extent used
	######################################
	def inzone_check_func(*args):
		if inzone_check_int.get() >= 1:  # use full extent
			inzone_min_i_entry.config(state="disable")
			inzone_min_j_entry.config(state="disable")
			inzone_max_i_entry.config(state="disable")
			inzone_max_j_entry.config(state="disable")
		elif inzone_check_int.get() == 0:  
			inzone_min_i_entry.config(state="normal")
			inzone_min_j_entry.config(state="normal")
			inzone_max_i_entry.config(state="normal")
			inzone_max_j_entry.config(state="normal")

	# disable and able based combobox option
	inzone_check_int.trace_add("write", inzone_check_func)

	######################################
	# selected time
	######################################
	intime_title_label = tk.Label(GUI_frame, text="Investigation Time", font=("Arial", 12, "bold"), anchor="w", justify="left")

	intime_check_label = tk.Label(GUI_frame, text="Final Time", font=("Arial", 12), anchor="w", justify="center")
	intime_check_int = tk.IntVar()
	intime_check_int.set(1) 
	intime_check_checkbutton = tk.Checkbutton(GUI_frame, variable=intime_check_int, onvalue=1, offvalue=0)

	# input variables
	intime_str = tk.StringVar()
	intime_str.set("")
	intime_entry = tk.Entry(GUI_frame, width=5, bd=3, font=("Arial", 12), textvariable=intime_str)
	intime_entry.config(state="disable")  # disable by default since using final time
	intime_unit_label = tk.Label(GUI_frame, textvariable=intime_unit_str, font=("Arial", 12), anchor="w", justify="left")

	# layout
	intime_title_label.grid(row=11, column=18, columnspan=2, padx=1, pady=5, sticky="w")
	intime_check_label.grid(row=11, column=20, columnspan=1, padx=1, pady=5, sticky="w")
	intime_check_checkbutton.grid(row=11, column=21, columnspan=1, padx=1, pady=5, sticky="w")
	intime_entry.grid(row=11, column=22, columnspan=3, padx=1, pady=5, sticky="we")
	intime_unit_label.grid(row=11, column=25, columnspan=1, padx=1, pady=5, sticky="w")
	
	######################################
	# disable when final time used
	######################################
	def intime_check_func(*args):
		if intime_check_int.get() >= 1:  # use full extent
			intime_entry.config(state="disable")
		elif intime_check_int.get() == 0:  
			intime_entry.config(state="normal")

	# disable and able based combobox option
	intime_check_int.trace_add("write", intime_check_func)

	######################################
	# line separator - Landslide Comparison Analysis vs Options
	######################################
	separator_col3_c = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col3_c.grid(row=12, column=18, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	# Output format options
	######################################
	output_format_opt_label = tk.Label(GUI_frame, text="Result Format", font=("Arial", 12, "bold"), anchor="w", justify="left")
	output_format_opt_str = tk.StringVar()
	output_format_opt_combo = ttk.Combobox(
		GUI_frame,
		state="readonly",
		values=["asc", "csv", "grd"],
		textvariable=output_format_opt_str,
		width=7,
		font=("Arial", 12)
	)
	output_format_opt_combo.current(0) # default "asc" (for now) - indicated by index number from values

	output_format_opt_label.grid(row=13, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	output_format_opt_combo.grid(row=13, column=20, columnspan=2, padx=5, pady=5, sticky="we")

	######################################
	# Soil Vertical Spacing options
	######################################
	soil_dz_label = tk.Label(GUI_frame, text="Soil dZ", font=("Arial", 12, 'bold'), anchor="w", justify="left") 
	soil_dz_double = tk.DoubleVar()
	soil_dz_double.set(0.25) 
	soil_dz_entry = tk.Entry(GUI_frame, width=15, bd=3, font=("Arial", 12), textvariable=soil_dz_double) 

	soil_dz_label.grid(row=13, column=22, columnspan=2, padx=5, pady=(0,5), sticky="w")
	soil_dz_entry.grid(row=13, column=24, columnspan=2, padx=5, pady=(0,10), sticky="we")

	######################################
	# Generate Plot options
	######################################
	generate_plot_opt_label = tk.Label(GUI_frame, text="Generate Plots", font=("Arial", 12, "bold"), anchor="w", justify="left")
	generate_plot_opt_int = tk.IntVar()
	generate_plot_opt_int.set(1) 
	generate_plot_opt_checkbutton = tk.Checkbutton(GUI_frame, variable=generate_plot_opt_int, onvalue=1, offvalue=0)

	generate_plot_opt_label.grid(row=14, column=18, columnspan=2, padx=5, pady=(0,5), sticky="w")
	generate_plot_opt_checkbutton.grid(row=14, column=20, padx=5, pady=5, sticky="w")

	######################################
	# Multiprocessing Configurations
	######################################
	multi_CPU_method_label = tk.Label(GUI_frame, text="Multi CPU", font=("Arial", 12, "bold"), anchor="w", justify="left")
	multi_CPU_method_opt_int = tk.IntVar()
	multi_CPU_method_opt_int.set(1)   # use multiprocessing by default
	multi_CPU_method_checkbutton = tk.Checkbutton(GUI_frame, variable=multi_CPU_method_opt_int, onvalue=1, offvalue=0)

	# multi_CPU_method_str = tk.StringVar()
	# multi_CPU_method_combo = ttk.Combobox(
	# 	GUI_frame,
	# 	state="readonly",
	# 	# values=["Pool", "C-SP-SP", "C-MP-SP", "C-MP-MP", "C-MP-MT", "S-SP-SP", "S-SP-MP", "S-MP-SP", "S-MP-MP"],
	# 	values=["Pool", "S-MP-MP"],
	# 	textvariable=multi_CPU_method_str,
	# 	width=7,
	# 	font=("Arial", 12)
	# )
	# multi_CPU_method_combo.current(0) # default "Pool" (for now) - indicated by index number from values

	# multi_CPU_method_label.grid(row=14, column=22, columnspan=2, padx=5, pady=(0,5), sticky="w")
	# multi_CPU_method_checkbutton.grid(row=14, column=24, columnspan=2, padx=5, pady=5, sticky="w")

	multi_CPU_method_label.grid(row=14, column=22, columnspan=1, padx=5, pady=(0,5), sticky="w")
	multi_CPU_method_checkbutton.grid(row=14, column=23, columnspan=1, padx=5, pady=5, sticky="w")

	######################################
	# max CPU Pool number
	######################################
	max_CPU_pool_label = tk.Label(GUI_frame, text="maxCPU", font=("Arial", 12), anchor="w", justify="left") 
	# MP_1st_CPU_pool_label = tk.Label(GUI_frame, text="MC-MP", font=("Arial", 12), anchor="w", justify="left") 
	# MP_2nd_CPU_pool_label = tk.Label(GUI_frame, text="El-MP", font=("Arial", 12), anchor="w", justify="left") 
	# MT_2nd_CPU_pool_label = tk.Label(GUI_frame, text="El-MT", font=("Arial", 12), anchor="w", justify="left") 
	
	max_CPU_pool_int = tk.IntVar()
	# MP_1st_CPU_pool_int = tk.IntVar()
	# MP_2nd_CPU_pool_int = tk.IntVar()
	# MT_2nd_CPU_pool_int = tk.IntVar()

	max_CPU_pool_int.set(16) 
	# MP_1st_CPU_pool_int.set(0)
	# MP_2nd_CPU_pool_int.set(0)
	# MT_2nd_CPU_pool_int.set(0)

	max_CPU_pool_entry = tk.Entry(GUI_frame, width=6, bd=3, font=("Arial", 12), textvariable=max_CPU_pool_int) 
	# MP_1st_CPU_pool_entry = tk.Entry(GUI_frame, width=6, bd=3, font=("Arial", 12), textvariable=MP_1st_CPU_pool_int) 
	# MP_2nd_CPU_pool_entry = tk.Entry(GUI_frame, width=6, bd=3, font=("Arial", 12), textvariable=MP_2nd_CPU_pool_int) 
	# MT_2nd_CPU_pool_entry = tk.Entry(GUI_frame, width=6, bd=3, font=("Arial", 12), textvariable=MT_2nd_CPU_pool_int) 

	max_CPU_pool_label.grid(row=14, column=24, columnspan=1, padx=5, pady=(0,5), sticky="w")
	max_CPU_pool_entry.grid(row=14, column=25, columnspan=1, padx=5, pady=(0,10), sticky="we")

	# max_CPU_pool_label.grid(row=15, column=18, columnspan=1, padx=5, pady=(0,5), sticky="w")
	# max_CPU_pool_entry.grid(row=15, column=19, columnspan=1, padx=5, pady=(0,10), sticky="we")
	# MP_1st_CPU_pool_label.grid(row=15, column=20, columnspan=1, padx=5, pady=(0,5), sticky="w")
	# MP_1st_CPU_pool_entry.grid(row=15, column=21, columnspan=1, padx=5, pady=(0,10), sticky="we")
	# MP_2nd_CPU_pool_label.grid(row=15, column=22, columnspan=1, padx=5, pady=(0,5), sticky="w")
	# MP_2nd_CPU_pool_entry.grid(row=15, column=23, columnspan=1, padx=5, pady=(0,10), sticky="we")
	# MT_2nd_CPU_pool_label.grid(row=15, column=24, columnspan=1, padx=5, pady=(0,5), sticky="w")
	# MT_2nd_CPU_pool_entry.grid(row=15, column=25, columnspan=1, padx=5, pady=(0,10), sticky="we")

	# default - 3DTS
	# multi_CPU_method_str.set("Pool")
	# multi_CPU_method_combo.config(state="disable")
	max_CPU_pool_entry.config(state="normal")
	# MP_1st_CPU_pool_entry.config(state="disable")
	# MP_2nd_CPU_pool_entry.config(state="disable")
	# MT_2nd_CPU_pool_entry.config(state="disable")

	# # change default values
	# def multi_CPU_method_func(*args):
	# 	if multi_CPU_method_str.get() == "Pool":
	# 		MP_1st_CPU_pool_int.set(0)
	# 		MP_2nd_CPU_pool_int.set(0)
	# 		MT_2nd_CPU_pool_int.set(0)
	# 		max_CPU_pool_entry.config(state="normal")
	# 		MP_1st_CPU_pool_entry.config(state="disable")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "C-SP-SP":
	# 		MP_1st_CPU_pool_int.set(1)
	# 		MP_2nd_CPU_pool_int.set(1)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="disable")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")
		
	# 	elif multi_CPU_method_str.get() == "C-MP-SP":
	# 		MP_1st_CPU_pool_int.set(8)
	# 		MP_2nd_CPU_pool_int.set(1)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="normal")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "C-MP-MP":
	# 		MP_1st_CPU_pool_int.set(8)
	# 		MP_2nd_CPU_pool_int.set(8)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="normal")
	# 		MP_2nd_CPU_pool_entry.config(state="normal")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "C-MP-MT":
	# 		MP_1st_CPU_pool_int.set(8)
	# 		MP_2nd_CPU_pool_int.set(1)
	# 		MT_2nd_CPU_pool_int.set(8)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="normal")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="normal")

	# 	elif multi_CPU_method_str.get() == "S-SP-SP":
	# 		MP_1st_CPU_pool_int.set(1)
	# 		MP_2nd_CPU_pool_int.set(1)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="disable")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "S-SP-MP":
	# 		MP_1st_CPU_pool_int.set(1)
	# 		MP_2nd_CPU_pool_int.set(8)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="disable")
	# 		MP_2nd_CPU_pool_entry.config(state="normal")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "S-MP-SP":
	# 		MP_1st_CPU_pool_int.set(8)
	# 		MP_2nd_CPU_pool_int.set(1)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="normal")
	# 		MP_2nd_CPU_pool_entry.config(state="disable")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# 	elif multi_CPU_method_str.get() == "S-MP-MP":
	# 		MP_1st_CPU_pool_int.set(8)
	# 		MP_2nd_CPU_pool_int.set(8)
	# 		MT_2nd_CPU_pool_int.set(1)
	# 		max_CPU_pool_entry.config(state="disable")
	# 		MP_1st_CPU_pool_entry.config(state="normal")
	# 		MP_2nd_CPU_pool_entry.config(state="normal")
	# 		MT_2nd_CPU_pool_entry.config(state="disable")

	# multi_CPU_method_str.trace_add("write", multi_CPU_method_func)

	def multi_CPU_method_func(*args):
		if multi_CPU_method_opt_int.get() > 0:
			max_CPU_pool_entry.config(state="normal")
		elif multi_CPU_method_opt_int.get() == 0:
			max_CPU_pool_entry.config(state="disable")
	
	multi_CPU_method_opt_int.trace_add("write", multi_CPU_method_func)

	######################################
	# line separator - options vs functions
	######################################
	separator_col3_c = ttk.Separator(GUI_frame, orient='horizontal')
	separator_col3_c.grid(row=16, column=18, columnspan=8, padx=1, pady=5, sticky="we")

	######################################
	# function buttons
	######################################
	open_manual_button = tk.Button(GUI_frame, text="Help", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=open_manual_file_command) 
	open_input_result_folder_button = tk.Button(GUI_frame, text="Open Folders", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=open_input_result_folder_explorer_command)

	rain_template_button = tk.Button(GUI_frame, text="Rain Template", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=csv_rainfall_template_command) 
	rain_hist_csv_import_button = tk.Button(GUI_frame, text="Rain CSV", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=open_rainfall_history_csv_file_command) 

	mat_template_button = tk.Button(GUI_frame, text="Material Template", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=csv_material_template_command) 
	mat_csv_import_button = tk.Button(GUI_frame, text="Material CSV", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=open_material_csv_file_command) 

	make_yaml_bat_bash_button = tk.Button(GUI_frame, text="Setup", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=make_yaml_bat_bash_command) 
	start_simulation_button = tk.Button(GUI_frame, text="Run", width=13, height=1, padx=10, pady=5, font=("Arial", 12), command=start_simulation_command) 

	rain_template_button.grid(row=17, column=18, columnspan=2, padx=5, pady=(0,10), sticky="we")
	rain_hist_csv_import_button.grid(row=17, column=20, columnspan=2, padx=5, pady=(0,10), sticky="we")
	mat_template_button.grid(row=17, column=22, columnspan=2, padx=5, pady=(0,10), sticky="we")
	mat_csv_import_button.grid(row=17, column=24, columnspan=2, padx=5, pady=(0,10), sticky="we")

	open_manual_button.grid(row=18, column=18, columnspan=2, padx=5, pady=(0,10), sticky="we")
	open_input_result_folder_button.grid(row=18, column=20, columnspan=2, padx=5, pady=(0,10), sticky="we")
	make_yaml_bat_bash_button.grid(row=18, column=22, columnspan=2, padx=5, pady=(0,10), sticky="we")
	start_simulation_button.grid(row=18, column=24, columnspan=2, padx=5, pady=(0,10), sticky="we")

	#################################
	## status
	#################################
	status = tk.Label(GUI_frame, text="", bd=1, relief='sunken', anchor="e", font=("Arial", 12))
	status.grid(row=19, column=0, columnspan=26, sticky="we")

	###########################################################################
	## GUI operation
	###########################################################################
	# check if the closing the window is valid
	root.protocol("WM_DELETE_WINDOW", quit_command)

	# run GUI
	root.mainloop()

	######################################
	## 3DPLS Landslide Susceptibility - additional options
	######################################
	# """ placeholder """
	# placeholder_3DPLS_add_menu_button = tk.Button(GUI_frame, text="PLACEHOLDER FOR 3DPLSs", width=10, height=4, padx=10, pady=5, font=("Arial", 12), state="disabled")
	# placeholder_3DPLS_add_menu_button.grid(row=12, rowspan=5, column=18, columnspan=8, padx=5, pady=5, sticky="we")


if __name__ == '__main__':
	RALP_GUI()
