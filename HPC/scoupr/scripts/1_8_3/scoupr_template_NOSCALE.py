# Maya Gomez
# Created in affiliation with the Cnidarian Evolutionary Ecology Lab (CEE) at the University Southern California and the Perry Institute for Marine Science (PIMS)

# PURPOSE: This script uses provided photosets to build scaled models of individual coral colonies via command line Agisoft Metashape. Scales are based on the adjustables that surround each coral during the imaging process.
# Tested in Metashape 1.8.3 (64 bit)

# ACKNOWLEDGEMENTS:
# This script has been influenced by the following people and their open source scripts:
	# 1. Will Greene and Sam Marshall (PIMS). Github link: https://github.com/Perry-Institute/Metashape_Reef/blob/main/FullUW_dialog_SM_202210.py
	# 2. Wyatt Million (CEE). Github link: https://github.com/wyattmillion/Coral3DPhotogram/blob/master/metashapeBase.py

##### SUMMARY STEPS FOR HOW TO BATCH PROCESS METASHAPE MODELS #####
# 1. For a given timepoint, organize all photosets into unique folders labeled with identifying information (Timepoint/Modetype/Date_Reef_Array) on your machine (ex. ORCC_October2022/Rack/102422_Looe/Tag2).
# 2. Secure copy the timepoint directory (containing all photosets) from my machine to the HPC (/scratch1/migomez/3Dmodels/source_images).
	# $ scp -r /Users/migomez/Documents/USC/3Dmodels/source_images/ORCC_October2023/Rack migomez@hpc-transfer1.usc.edu:/scratch1/migomez/3Dmodels/source_images/ORCC_October2023/Rack
# 3. Automatically build a unique python script for each photoset (ex. rackfull_template.py) and generate a slurm script containing a submission value for each new python script.
	# $ ./buildscripts_rack.sh ORCC_October2022	(run on Endeavor within /project/ckenkel_26/software/metashape-pro)
# 4. Submit a batch job to process one or more models by running the slurm script that was created in the prior step.
	# $ sbatch ORCC_October2022_MetashapeJobSubmit.slm 	(run on Endeavor)
# 5. Once you recieve a batch job completion email, then secure copy the entire timepoint output directory (including all .psz, .obj, report, ect) to my computer.
	# $ scp -r migomez@hpc-transfer1.usc.edu:/scratch1/migomez/3Dmodels/models/ORCC_October2023/Rack /Users/migomez/Documents/USC/3Dmodels/models/October2023/Rack
# 6. Visualize models in Metashape!



### WORKFLOW FOR BUILDING METASHAPE MODELS ###

###### PART I - SET UP ######

### 1. Set up environment: Load modules, set filepaths & set constants

## Load modules:
import Metashape
import os
import glob
import math
#import sys


## Set file paths:
source_images = "PHOTOSET"

# Set output filepath based on the 5th element in the source_images filepath
array=source_images.split('/')
timepoint=array[5]
output="/scratch1/avinton/3Dmodels/models/{}/scoupr/".format(timepoint)
#output = "/scratch1/migomez/3Dmodels/models/DRTO_June2023/scoupr/"



## Set constants:
doc = Metashape.app.document
chunk = doc.addChunk() # If running on the HPC, include this.
# chunk = doc.chunk # If running on my machine, include this.



### 2. Load in photos & save to output location
os.chdir(source_images)
cwd = os.getcwd()
print(cwd)
swd = cwd.split("/") # split the name into a list by the '/'

photoset=glob.glob(cwd+"/*.JPG") 	# directs metashape to photos to be used to build the model
chunk.addPhotos(photoset) 	# adds photos to project
doc.save(output+swd[-1]+'.psz') 	# names the Metashape Project file based on the last portion of swd



### 3. Align photos and build the sparse point cloud

# NOTES:
# Select image matching accuracy (downscale) is based on the following scales: Highest = 0, High = 1, Medium = 2, Low = 4, Lowest = 8
# generic_preselection = True saves time. However, if not limited by processing power (ie. HPC) then generic_preselection = False is preferred. It takes longer but results in fewer situations where photos don't match.
	# Originally Wyatt had: chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=False)
# Many of the details below are not doing anything at the moment, but they are also not hurting - so just leave for now! Can be used for refining in the future.
	# Ex. subdivide_task is not doing anything now, BUT could be really useful in the future for a senario that divides work across multiple nodes.	
chunk.matchPhotos(downscale = 1, keypoint_limit_per_mpx = 300, generic_preselection = False, reference_preselection=True, filter_mask=False, mask_tiepoints=True,
			filter_stationary_points=True, keypoint_limit=40000, tiepoint_limit=4000, keep_keypoints=False, guided_matching=False,
                    reset_matches=False, subdivide_task=True, workitem_size_cameras=20, workitem_size_pairs=80, max_workgroup_size=100)
doc.save()

chunk.alignCameras(adaptive_fitting = True, min_image=2, reset_alignment=False, subdivide_task=True)
doc.save()

# NOTE: If having an issue where all of the photos are not aligning, then something to try to help alignment is to switch the order of the above steps such that steps 3 (Detect Markers) and 4 (Reference Coord System) come before 2 (Align Photos).



### 4. Detect markers

# NOTE: Tolerance is how sensitive the algorithm is to detecting targets. Range is 0 - 100. If tolerance is high, then there is risk of overdetecting markers (ie. thinks something is a marker that is not). If tolerance is low, then it only picks up with markers are super clear. 
chunk.detectMarkers(target_type = Metashape.CircularTarget12bit, tolerance=50, filter_mask=False, inverted=False, noparity=False, maximum_residual=5, minimum_size=0, minimum_dist=5)




### 5. Set local coordinate system (required to scale model, but that step has been removed from this script)

# Change to local coordinate system
chunk.crs = Metashape.CoordinateSystem('LOCAL_CS["Local Coordinates (m)",LOCAL_DATUM["Local Datum",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
doc.save()




### 6. Optimize camera alignment
# This step optimizes camera distortion model and camera locations based on deletion of bad tie points
# Original script written by Asif-ul Islam (Middlebury College) for use with underwater photogrammetry. Updated May 2022 by Will Greene (PIMS), adapted by Maya Gomez November 2022 (USC/PIMS)
		    
# Define thresholds for reconstruction uncertainty and projection accuracy
reconun = float(25)
projecac = float(15)
    
# Initiate filters, remote points above thresholds
f = Metashape.PointCloud.Filter()
f.init(chunk, Metashape.PointCloud.Filter.ReconstructionUncertainty)
f.removePoints(reconun)
    
f = Metashape.PointCloud.Filter()
f.init(chunk, Metashape.PointCloud.Filter.ProjectionAccuracy)
f.removePoints(projecac)    

# Optimize camera locations based on all distortion parameters
chunk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=True, fit_b2=True, fit_k1=True, fit_k2=True, fit_k3=True, 
						fit_k4=True, fit_p1=True, fit_p2=True, fit_corrections=True, adaptive_fitting=False, tiepoint_covariance=False)
doc.save()




###### PART II - GENERATE PRODUCTS ######

### 1. Build mesh

# NOTES:
# Select depth maps quality (downscale) based on the following scale: Ultra = 1, High = 2, Medium = 4, Low = 8, Lowest = 16
	# Ultra will take 4x as long as High. Ultra also has a higher likelihood of having holes (lower settings can fill in larger holes). Will recommends using high or medium quality (ultra is not better!).
	# Wyatt had it at low quality (8), possibly just to make it run faster?
chunk.buildDepthMaps(downscale = 2, filter_mode = Metashape.MildFiltering, reuse_depth = True, max_neighbors=16, subdivide_task=True, workitem_size_cameras=20, max_workgroup_size=100)
doc.save()

# NOTES:
# face_count=Metashape.HighFaceCount means that Metashape uses as many triangles as it thinks it needs to represent the mesh (mesh = series of interconnected triangles that represent the surface) vs. forcing it to use fewer triangles with LowFaceCount.
	# Wyatt had face_count=Metashape.LowFaceCount - which is not preferable.
chunk.buildModel(surface_type = Metashape.Arbitrary, interpolation = Metashape.EnabledInterpolation, face_count=Metashape.HighFaceCount, 
				face_count_custom = 1000000, source_data = Metashape.DepthMapsData, keep_depth = False) # change this to false to avoid wasted space? 
doc.save()



### 2. Build texture

# NOTES: 
# chunk.buildUV and chunk.buildTexture are not necessary. They are simply a visual tool. Remove these to reduce processing time.
# If the output is too pixelated, increase the texture_size up to 8192x2 (always increase in groupings of 8192). 
	# Wyatt originally had texture_size=25000 which may be why models were taking so long to build and why their file sizes were huge.
chunk.buildUV(mapping_mode=Metashape.GenericMapping) #part of build texture step
chunk.buildTexture(blending_mode=Metashape.MosaicBlending, texture_size=8192, fill_holes=True) #rest of build texture step
doc.save()


# List of other Metashape functions that could be applicable in the future:
# chunk.buildDenseCloud(point_colors = True)
# chunk.buildOrthomosaic(resolution = 0.0005, surface_data=Metashape.ModelData, blending_mode=Metashape.MosaicBlending, fill_holes=True, ghosting_filter=False,
                    	# cull_faces=False, refine_seamlines=False, flip_x=False, flip_y=False, flip_z=False, subdivide_task=True, workitem_size_cameras=20, workitem_size_tiles=10, max_workgroup_size=100)
# chunk.buildDem(source_data = Metashape.ModelData, interpolation = Metashape.DisabledInterpolation, flip_x=False, flip_y=False, flip_z=False,
                # resolution=0, subdivide_task=True, workitem_size_tiles=10, max_workgroup_size=100)
	# chunk.buildDem() builds a 2D rainbow map of depth    



 
###### PART III - EXPORT PRODUCTS #####

### 1. Clean project
depthmaps = chunk.depth_maps
depthmaps.clear() #remove depth maps (if present)
#sparsecloud = chunk.point_cloud
#sparsecloud.removeKeypoints() #remove key points(if present)
doc.save()

 
### 2. Export products as .OBJ (and other supplementary files) for use in MeshLab
chunk.exportModel(output+swd[-1]+".obj", binary=True, precision=6, save_normals=True, save_colors=True, save_cameras=True, save_markers=True, save_udim=False, strip_extensions=False)


### 3. Generate report
# Option to add a description beneath the title. Ex. description = "Processing report for ORCC October 2022 Rack Model - Timepoint 0"
chunk.exportReport(path = output+swd[-1]+"_report.pdf", title = swd[-1], font_size=12, page_numbers=True, include_system_info=True)

doc.save()
