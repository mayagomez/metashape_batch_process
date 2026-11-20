# Maya Gomez
# Created in affiliation with the Cnidarian Evolutionary Ecology Lab (CEE) at the University Southern California and the Perry Institute for Marine Science (PIMS)

# PURPOSE: This script uses provided photosets to build scaled models of individual coral colonies via command line Agisoft Metashape. Scales are based on the adjustables that surround each coral during the imaging process.
# Tested in Metashape 2.2.1 (64 bit)

# ACKNOWLEDGEMENTS:
# This script has been influenced by the following people and their open source scripts:
# 1. Will Greene and Sam Marshall (PIMS). Github link: https://github.com/Perry-Institute/Metashape_Reef/blob/main/FullUW_dialog_SM_202210.py
# 2. Wyatt Million (CEE). Github link: https://github.com/wyattmillion/Coral3DPhotogram/blob/master/metashapeBase.py

##### SUMMARY STEPS FOR HOW TO BATCH PROCESS METASHAPE MODELS #####
# 1. For a given timepoint, organize all photosets into unique folders labeled with identifying information (Timepoint/Modetype/Date_Reef_Array) on your machine (ex. ORCC_October2022/Rack/102422_Looe/Tag2).
# 2. Secure copy the timepoint directory (containing all photosets) from my machine to the HPC (/scratch1/migomez/3Dmodels/source_images).
# $ scp -r /Users/migomez/Documents/USC/3Dmodels/source_images/ORCC_October2023/Rack migomez@hpc-transfer1.usc.edu:/scratch1/migomez/3Dmodels/source_images/ORCC_October2023/Rack
# 3. Automatically build a unique python script for each photoset (ex. rackfull_template.py) and generate a slurm script containing a submission value for each new python script.
# $ ./buildscripts_rack.sh ORCC_October2022 (run on Endeavor within /project/ckenkel_26/software/metashape-pro)
# 4. Submit a batch job to process one or more models by running the slurm script that was created in the prior step.
# $ sbatch ORCC_October2022_MetashapeJobSubmit.slm (run on Endeavor)
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


## Set file paths:
source_images = "/scratch1/migomez/3Dmodels/source_images/SinglePolyp/090425/090425_31-F-L"
project = "SinglePolyp" #CalcExpt_Skeletons # replace this if changing projects!

## Set output filepath based on the 5th element in the source_images filepath
array=source_images.split('/')
timepoint=array[6]
output=f"/scratch1/migomez/3Dmodels/models/{project}/{timepoint}/"


## Point to the scalebar and coordinate files
scalebars_path = "/project2/ckenkel_26/software/metashape-pro/Scales/FragramScale_050625.txt"
FragramCoords = "/project2/ckenkel_26/software/metashape-pro/Scales/FragramCoords_050625.txt"

# Other options:
#Adjustable1AScale_011623.txt Adjustable2AScale_011623.txt MoteScaleBars.txt RackCoords_101422_OLD.txt RackScale_012423.txt
#Adjustable1BScale_011623.txt Adjustable2BScale_011623.txt RackCoords_011723.txt RackCoords_101422.txt RackScale_101422.txt
#Adjustable1BScale_041823.txt Adjustable3Scale_BARSTICKERS_060123.txt RackCoords_012423.txt RackScale_011723.txt


## Set constants:
doc = Metashape.app.document
chunk = doc.addChunk()



### 2. Load in photos & save to output location
os.chdir(source_images)
cwd = os.getcwd()
print(cwd)
swd = cwd.split("/") # split the name into a list by the '/'

photoset=glob.glob(cwd+"/*.png") # directs metashape to photos to be used to build the model. There is a chance you have to change between .jpg/.JPG/.bmp/.png
chunk.addPhotos(photoset) # adds photos to project
doc.save(output+swd[-1]+'.psz') # names the Metashape Project file based on the last portion of swd


## Rename the chunk to the file name
chunk.label = os.path.splitext(os.path.basename(doc.path))[0]




### 3. Detect markers

# NOTE: Tolerance is how sensitive the algorithm is to detecting targets. Range is 0 - 100. If tolerance is high, then there is risk of overdetecting markers (ie. thinks something is a marker that is not). If tole>
chunk.detectMarkers(target_type = Metashape.CircularTarget12bit, tolerance=50, filter_mask=False, inverted=False, noparity=False, maximum_residual=5, minimum_size=0, minimum_dist=5)




### 4. Align photos and build the sparse point cloud

# NOTES:
# Select image matching accuracy (downscale) is based on the following scales: Highest = 0, High = 1, Medium = 2, Low = 4, Lowest = 8
# generic_preselection = True saves time. However, if not limited by processing power (ie. HPC) then generic_preselection = False is preferred. It takes longer but results in fewer situations where photos don't match.
# Originally Wyatt had: chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=False)
# filter_stationary_points=True is importatant with this style of photogrammetry where the cameras are fixed and the stage moves!
# Many of the details below are not doing anything at the moment, but they are also not hurting - so just leave for now! Can be used for refining in the future.
# Ex. subdivide_task is not doing anything now, BUT could be really useful in the future for a senario that divides work across multiple nodes.

chunk.matchPhotos(downscale = 1, keypoint_limit_per_mpx = 300, generic_preselection = True, reference_preselection=True, filter_mask=False, mask_tiepoints=True,
filter_stationary_points=True, keypoint_limit=40000, tiepoint_limit=4000, keep_keypoints=False, guided_matching=False,
reset_matches=False, subdivide_task=True, workitem_size_cameras=20, workitem_size_pairs=80, max_workgroup_size=100)
doc.save()

chunk.alignCameras(adaptive_fitting = True, min_image=2, reset_alignment=False, subdivide_task=True)
doc.save()




### 5. Create reference coordinate system

# Change to a local coordinate system
crs_local = Metashape.CoordinateSystem('LOCAL_CS["Local Coordinates (m)",LOCAL_DATUM["Local Datum",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]') # Defines crs as local coordinate system instead of WGS 84 (ESPSG::4326)

# Set
chunk.importReference(path = FragramCoords, format = Metashape.ReferenceFormatCSV, delimiter = ',', columns = "nXYZxyz", skip_rows = 2, crs = crs_local, ignore_labels=False, create_markers=False, threshold=0.1, shutter_lag=0)
# Additional options: columns = "nxyz", items = Metashape.ReferenceItemsMarkers

chunk.updateTransform()
doc.save()



### 6. Scale model
# Create scalebars from a CSV file

# This script was originally based on a script for creating scalebars in Photoscan available at:
# http://hairystickman.co.uk/photoscan-scale-bars/

# Updated May 2022 by Will Greene / Perry Institute for Marine Science and Asif-ul Islam / Middlebury College for use with underwater photogrammetry

# CSV file format must be as follows:
# Marker_1_label,Marker_2_label,distance,accuracy
# ex:
# point 1,point 2,9.903500,0.002000
# point 2,point 3,9.949000,0.002000
# point 3,point 4,9.913000,0.002000
# PS: no additional spaces should be inserted

from PySide2 import QtCore, QtGui

# Expand the following variable upon script duplication.
def Create_Scalebars(): 

   iNumScaleBars=len(chunk.scalebars) 
   iNumMarkers=len(chunk.markers) 
   if (iNumMarkers == 0): 
      raise Exception("No markers found. Unable to create scalebars") 
   if (iNumScaleBars > 0): 
      print("There are already ",iNumScaleBars," scalebars in this project.") 

   file = open(scalebars_path) 
   eof = False 
   line = file.readline() 
   while not eof: 
      point1, point2, dist, acc = line.split(",") 
      scalebarfound=0 
      if (iNumScaleBars > 0): 
         for sbScaleBar in chunk.scalebars: 
            strScaleBarLabel_1=point1+"_"+point2 
            strScaleBarLabel_2=point2+"_"+point1 
            if sbScaleBar.label==strScaleBarLabel_1 or sbScaleBar.label==strScaleBarLabel_2: 
               scalebarfound=1 
               sbScaleBar.reference.distance=float(dist) 
               sbScaleBar.reference.accuracy=float(acc) 
      if (scalebarfound==0): 
         bMarker1Found=0 
         for marker in chunk.markers: 
            if (marker.label == point1): 
               marker1 = marker 
               bMarker1Found=1 
               break 
         bMarker2Found=0 
         for marker in chunk.markers: 
            if (marker.label == point2): 
               marker2 = marker 
               bMarker2Found=1 
               break 
         if bMarker1Found==1 and bMarker2Found==1: 
            sbScaleBar = chunk.addScalebar(marker1,marker2) 
            sbScaleBar.reference.distance=float(dist) 
            sbScaleBar.reference.accuracy=float(acc) 
         else: 
            if (bMarker1Found == 0): 
               print("Marker "+point1+" was not found") 
            if (bMarker2Found == 0): 
               print("Marker "+point2+" was not found") 
      line = file.readline() 
      if not len(line): 
         eof = True 
         break 

   file.close() 
   Metashape.app.update() 

Create_Scalebars()

doc.save()


### X. Optimize camera alignment ---- NOT NECESSARY FOR FRAGRAM MODELS
# This step optimizes camera distortion model and camera locations based on deletion of bad tie points
# Original script written by Asif-ul Islam (Middlebury College) for use with underwater photogrammetry. Updated May 2022 by Will Greene (PIMS), adapted by Maya Gomez November 2022 (USC/PIMS)

# Metashape 2.0+ changed "PointCloud" to "TiePoints". That has been reflected below.

# Define thresholds for reconstruction uncertainty and projection accuracy
#reconun = float(25)
#projecac = float(15)

# Initiate filters, remote points above thresholds
#f = Metashape.TiePoints.Filter()
#f.init(chunk, Metashape.TiePoints.Filter.ReconstructionUncertainty)
#f.removePoints(reconun)

#f = Metashape.TiePoints.Filter()
#f.init(chunk, Metashape.TiePoints.Filter.ProjectionAccuracy)
#f.removePoints(projecac)

# Optimize camera locations based on all distortion parameters
#chunk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=True, fit_b2=True, fit_k1=True, fit_k2=True, fit_k3=True,
#fit_k4=True, fit_p1=True, fit_p2=True, fit_corrections=True, adaptive_fitting=False, tiepoint_covariance=False)
#doc.save()






### 7. Adjust bounding box based on coordinate system.

# Define variables to be used below:
T = chunk.transform.matrix
crs = chunk.crs


## 7A. First rotate the bounding box in line with the coordinate system. Bounding box size is kept.
# Script adapted from: https://github.com/agisoft-llc/metashape-scripts/blob/master/src/bounding_box_to_coordinate_system.py

# Checking compatibility (not sure why it needs this but is seems as though it does)
#compatible_major_version = "1.8"
#found_major_version = ".".join(Metashape.app.version.split('.')[:2])

# "replaceme" in all caps goes here but I am removing it for the moment bc I dont think its necessary

# The definition of replaceme is as follows. It gets replaced during script duplication. This is necessary because echo causes formatting issues (ignores tabs) that prevent if statements from working.
#if found_major_version != compatible_major_version:
# raise Exception("Incompatible Metashape version: {} != {}".format(found_major_version, compatible_major_version))


v_t = T.mulp(Metashape.Vector([0, 0, 0]))

if chunk.crs: 
	 m = chunk.crs.localframe(v_t) 
else: 
	 m = Metashape.Matrix().Diag([1, 1, 1, 1])

# The definition of alsoreplace is as follows. It also gets replaced during the script duplication phase.
#if chunk.crs:
#m = chunk.crs.localframe(v_t)
#else:
#m = Metashape.Matrix().Diag([1, 1, 1, 1])

m = m * T
s = math.sqrt(m[0, 0] ** 2 + m[0, 1] ** 2 + m[0, 2] ** 2) # scale factor # s = m.scale()
R = Metashape.Matrix([[m[0, 0], m[0, 1], m[0, 2]],
[m[1, 0], m[1, 1], m[1, 2]],
[m[2, 0], m[2, 1], m[2, 2]]])

R = R * (1. / s)

reg = chunk.region
reg.rot = R.t()
chunk.region = reg






## 7B. Then change the size of the bounding box.
# Script adapted from: https://www.agisoft.com/forum/index.php?topic=13222.0

# Define your Bounding Box center, size and angle:

# If using MY block and you want to keep the plug
#center = (0,0,0.06) # (X,Y,Z) in CRS coordinates - could do (0,0,0.1) to move the box up
#size = (0.1,0.1,0.11) # (width,depth,height)in meters
#angle = 90 # float - rotation angle of the region (in degrees)

# If using MY block and you want to chop out the plug
#center = (0,0,0.068) # (X,Y,Z) in CRS coordinates
#size = (0.1,0.1,0.11) # (width,depth,height)in meters
#angle = 90 # float - rotation angle of the region (in degrees)

# If using MY block and you want to include the entire thing
center = (0,0,0.02) # (X,Y,Z) in CRS coordinates
size = (0.1,0.1,0.14) # (width,depth,height)in meters
angle = 90 # float - rotation angle of the region (in degrees)

# If using the CRL block
#center = (0,0,0.078) # (X,Y,Z) in CRS coordinates - could do (0,0,0.1) to move the box up
#size = (0.1,0.1,0.11) # (width,depth,height)in meters
#angle = 90 # float - rotation angle of the region (in degrees)




center = Metashape.Vector((center[0],center[1],center[2]))
center = T.inv().mulp(crs.unproject(center))
m = crs.localframe(T.mulp(center)) * T
R = m.rotation() * (1. / m.scale())
size = Metashape.Vector((size[0],size[1],size[2])) / m.scale() # scaling the size is required

# Option 1:
#s = math.sin(angle * math.pi / 180.)
#c = math.cos(angle * math.pi / 180.)
#rot = Metashape.Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
#rotation = R.t() * rot

# Option 2: This is cleaner, but I cannot figure how to call np commands (which I believe are from the numpy package)
#angle = np.radians(angle)
#rot = Metashape.Matrix([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
#rotation = R.t() * rot

#chunk.region.rot = rotation # When rotation is added in, it breaks the next chunk.buildDepthMaps step. This works fine without rotation for now.
chunk.region.center = center
chunk.region.size = size



# Only run the the following if you are working on your computer
#chunk.updateTransform()
#doc.save()



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
# If you set it to high then it ignores the face_count_custom
# Wyatt had face_count=Metashape.LowFaceCount - which is not preferable.
chunk.buildModel(surface_type = Metashape.Arbitrary, interpolation = Metashape.EnabledInterpolation, face_count=Metashape.HighFaceCount,
face_count_custom = 1000000, source_data = Metashape.DepthMapsData, keep_depth = False) # change this to false to avoid wasted space?
doc.save()


### 2. Clean Model
# This removes shards and leaves only the big coral mesh behind

# This only works with 2.2.1
chunk.model.cleanModel(criterion=Metashape.Model.Criterion.ComponentSize, level=99)

# Theres's a chance this works with 1.8.3 but need to test. Tried this once and it didnt work.
#chunk.model.removeComponents(max_components=1)


### 3. Build texture

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
