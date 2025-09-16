#!/bin/bash
# Maya Gomez
# Created in affiliation with the Cnidarian Evolutionary Ecology Lab (CEE) at the University Southern California and the Perry Institute for Marine Science (PIMS)

# PURPOSE: This script creates an individual Metashape script for each photoset within the provided TIMEPOINT directory & generates a slurm script to process all photosets at once. 
# To run, simply input the name of the directory that holds all of the photoset directories (ie. the timepoint directory) after calling the command. 
# Ex: ./buildscripts.sh ORCC_October2022  

# Acknowledgements:
	# This script has been influenced by Meta_expand.sh, a script written by Wyatt Million (CEE) - Github link: https://github.com/wyattmillion/Coral3DPhotogram/blob/master/Meta_expand.sh


###### SET UP ######

# Set file paths & constants: 
TIMEPOINT=$1
TEMPLATE=adjustables_template_JD.py	# Option to change this to the template script of your choosing.
SCOUPR=$2
DIR=/scratch1/migomez/3Dmodels/source_images/$TIMEPOINT/scoupr/$SCOUPR	# Option to change this location. All you should need to do is change migomez to your username.

# Create an output directory based on the timepoint directory name and save all subsequent outputs here. 
#mkdir /project/ckenkel_26/software/metashape-pro/ToRun/$TIMEPOINT		# Option to change this location.
#mkdir /project/ckenkel_26/software/metashape-pro/ToRun/$TIMEPOINT/scoupr          # Option to change this location.
mkdir /project/ckenkel_26/software/metashape-pro/ToRun/$TIMEPOINT/scoupr/$SCOUPR          # Option to change this location.
OUT=/project/ckenkel_26/software/metashape-pro/ToRun/$TIMEPOINT/scoupr/$SCOUPR     	# Option to change this location.


# If TIMEPOINT or MODELTYPE is not provided when ./buildscripts.sh is run, then exit and output the following text:
if [ "$#" -ne 2 ]
        then
        echo ""
        echo "Missing timepoint and/or model type directory"
        echo "Usage: ./buildscripts.sh TIMEPOINT MODELTYPE"
        echo "Where"
        echo "  TIMEPOINT: directory that holds photosets from a specific timepoint for batch processing"
        echo "  SCOUPR: scoupr1A_Maya  scoupr1B_Erich  scoupr2A_Joe  scoupr2B_Ian"
        echo "For example: ./buildscripts.sh ORCC_October2022 Rack'"
        echo ""
        exit
fi



###### SCRIPT ######

# Compile a list of the absolute file paths for each photoset directory within the timepoint directory and place in the output ($OUT) directory. 
ls -d -1 $DIR/** > $OUT/PhotosetDirs.txt


# Create a unique Metashape script (based on rack_template.py) for each photoset and save to the output directory. This simply takes rack_template.py and replaces the PHOTOSET variable.
(set -f 	# this is required so that echo does not expand the * wildcards within the newly created py scripts
for line in `cat $OUT/PhotosetDirs.txt`; do
    IFS='/' read -ra NAME <<< "$line";		# this splits the file path
    name1="${NAME[8]}";				# this picks the 6th thing in the file path and names the output .py as such
    while read script; do
        echo ${script//PHOTOSET/$line};
    done < $TEMPLATE > $OUT/${name1}.py 	# Option to change to the name of the base script that you would like to use as a template HERE
done
)


# Create a list of all of the newly created python scripts.
ls $OUT/*.py > $OUT/listofscripts.txt


# Then replace any instances of REPLACEME and ALSOREPLACE with the following hard coded if statements. This is necessary because in the prior step, when the template script is echoed to a new file, all formatting is removed (ie. tabs) and if statements no longer work.
for file in `cat $OUT/listofscripts.txt`; do
   sed -i 's/REPLACEME/if found_major_version != compatible_major_version: \n\t raise Exception("Incompatible Metashape version: {} != {}".format(found_major_version, compatible_major_version))/' $file
   sed -i 's/ALSOREPLACE/if chunk.crs: \n\t m = chunk.crs.localframe(v_t) \nelse: \n\t m = Metashape.Matrix().Diag([1, 1, 1, 1])/' $file
   sed -i 's#SCALEBARSDEF#def Create_Scalebars(): \n\n   iNumScaleBars=len(chunk.scalebars) \n   iNumMarkers=len(chunk.markers) \n   if (iNumMarkers == 0): \n      raise Exception("No markers found. Unable to create scalebars") \n   if (iNumScaleBars > 0): \n      print("There are already ",iNumScaleBars," scalebars in this project.") \n\n   file = open(scalebars_path) \n   eof = False \n   line = file.readline() \n   while not eof: \n      point1, point2, dist, acc = line.split(",") \n      scalebarfound=0 \n      if (iNumScaleBars > 0): \n         for sbScaleBar in chunk.scalebars: \n            strScaleBarLabel_1=point1+"_"+point2 \n            strScaleBarLabel_2=point2+"_"+point1 \n            if sbScaleBar.label==strScaleBarLabel_1 or sbScaleBar.label==strScaleBarLabel_2: \n               scalebarfound=1 \n               sbScaleBar.reference.distance=float(dist) \n               sbScaleBar.reference.accuracy=float(acc) \n      if (scalebarfound==0): \n         bMarker1Found=0 \n         for marker in chunk.markers: \n            if (marker.label == point1): \n               marker1 = marker \n               bMarker1Found=1 \n               break \n         bMarker2Found=0 \n         for marker in chunk.markers: \n            if (marker.label == point2): \n               marker2 = marker \n               bMarker2Found=1 \n               break \n         if bMarker1Found==1 and bMarker2Found==1: \n            sbScaleBar = chunk.addScalebar(marker1,marker2) \n            sbScaleBar.reference.distance=float(dist) \n            sbScaleBar.reference.accuracy=float(acc) \n         else: \n            if (bMarker1Found == 0): \n               print("Marker "+point1+" was not found") \n            if (bMarker2Found == 0): \n               print("Marker "+point2+" was not found") \n      line = file.readline() \n      if not len(line): \n         eof = True \n         break \n\n   file.close() \n   Metashape.app.update() \n\nCreate_Scalebars()#' $file
done

#Note on the 3rd sed command above, the / breaks when it gets to the URL

# Make all newly created python scripts executable.
chmod +x $OUT/*.py


# Create a list of the full command that calls each unique python script so that they can be run one after another in a slurm script. Save as ToDo.txt
for i in `ls ToRun/$TIMEPOINT/scoupr/$SCOUPR/*.py`; do		# This could also be done as follows: for i in `cat $OUT/listofscripts.txt`; do 
    echo bash metashape.sh -r $i -platform offscreen >> $OUT/ToDo.txt; 
done


# Finally, append ToDo.txt to the template Metashape job submission script (template_MetashapeJobSubmit.slm) and make it executable.
cat template_MetashapeJobSubmit.slm $OUT/ToDo.txt > ${TIMEPOINT}_${SCOUPR}_MetashapeJobSubmit.slm
chmod +x ${TIMEPOINT}_${SCOUPR}_MetashapeJobSubmit.slm


