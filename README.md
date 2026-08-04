# metashape_batch_process

This high throughput, fully automated photogrammetry processing pipeline utilizes custom scripts and accessory files to remotely process hundreds of scaled 3D models from 2D images with command-line Agisoft Metashape and USC’s high performance computing system. Put simply, this workflow replicates a template script for each photoset in a timepoint/project and runs each script in sequence until batch completion, thus requiring only one Metashape license for batch processing. Outputs include Metashape specific 3D model files (.psz), build reports (.pdf), and shape/accessory files (.jpg, .mtl, .obj) for use in other 3D model viewing and phenotyping softwares, such as MeshLab.

This workflow is utilized by the Cnidarian Evolutionary Ecology Lab at USC for the construction of 3D models of coral outplants (in-water photogrammetry) as well as corals grown on plugs in aquaria systems (in-air photogrammetry). Time series photosets unlock the tracking of key morphological and growth related traits, such linear extension, volume, surface area, convexity, and interstitial space, with greater accuracy and precision than traditional by hand methods.

The template scripts utilized for batch processing 3D models varies slightly by the image capture method. All models are scaled according to the distances between unique Agisoft Metashape markers in the target region. Scripts were originally written and tested on Metashape 1.8.3 and 2.2.1, however 2.2.1 scripts should work for 2.0+. 

Image capture methods:

1. **SCOUPR** (Scaling and Color Object for Underwater Photogrammetry Reference): manually collected images of coral outplants (in-water). Please see https://www.protocols.io/view/image-capture-for-3d-photogrammetry-of-stony-coral-c9qkz5uw for in-water image capture details. SCOUPRs were formally known as "Adjustables". If you see the word "Adjustable" in any script, it can be replaced with "scoupr".

2. **Fragrammeter**: automatically captured images of corals captures with the custom built Fragrammeter imaging station (in-air). Corals are positioned within a custom 3D printed holder with Metashape targets, which allows for scaling and the construction of a local coordinate system for model alignment across sequential timepoints. Please see https://www.protocols.io/edit/the-fragrammeter-an-open-source-instrument-to-phot-g8qebzvtf for details on the Fragrammeter.
   
3. **Rack:** manually captured images of up to 10 corals held within a custom rack to increase throughput (in-water and in-air). This method relies on the ability for coral fragments to be physically moved and secured in the rack holders. Method used for CalcExpt.
<br>

Regardless of the precise image capture method, the batch processing pipeline requires the following three scripts, where the XXX is replaced with the name of the image capture method.
- **XXX_template.py**: template python script for running Metashape on the command line
- **buildscripts_XXX.sh**: bash commands which duplicate the template script, populate variables, serially replace the photoset name, and generate the final slurm script
- **template_MetashapeJobSubmit.slm**: final script for job submission
  
Please see https://www.protocols.io/edit/batch-processing-scaled-3d-models-using-agisoft-me-haiwb2cff for support in running the batch processing scripts on an HPC.


**v2** batch processing release by Maya Gomez (migomez@usc.edu)
**v1** release by Wyatt Million: https://github.com/wyattmillion/Coral3DPhotogram
