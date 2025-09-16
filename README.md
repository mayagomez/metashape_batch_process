# metashape_batch_process

This high throughput, fully automated photogrammetry processing pipeline utilizes custom scripts and accessory files to remotely process hundreds of scaled 3D models with command-line Agisoft Metashape and USC’s high performance computing system. Put simply, this workflow replicates a template script for each photoset in a timepoint/project and runs each script in sequence until batch completion, thus requiring only one Metashape license for batch processing. Outputs include Metashape specific 3D model files (.psz), build reports (.pdf), and shape/accessory files (.jpg, .mtl, .obj) for use in other 3D model viewing and phenotyping softwares, such as MeshLab.

This workflow is utilized by the Cnidarian Evolutionary Ecology Lab at USC for the construction of 3D models of individual Acropora cervicornis coral outplants (in-water photogrammetry) as well as corals grown on plugs in aquaria systems (in-air photogrammetry). Time series photosets unlock the tracking of key morpholgocial and growth related traits, such linear extension, volume, surface area, convexity, and interstitial space, with greater accuracy and precision than traditional by hand methods.

Scripts tested in Metashape 1.8.3 and/or 2.2.1 (see script for specifications).

Please see https://www.protocols.io/view/image-capture-for-3d-photogrammetry-of-coral-colon-c9qkz5uw?step=2.1 for image capture details.
