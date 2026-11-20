'''
Crop Model by Region
02/19/2026
Maya Gomez, migomez@usc.edu
USC/PIMS

Adapted from https://www.agisoft.com/forum/index.php?topic=12225.0 for Metashape 2.3.0
Written with the help of AI (ChatGPT).
'''

import Metashape

def crop_model_by_region():

    doc = Metashape.app.document
    chunk = doc.chunk

    if not chunk:
        print("No active chunk.")
        return

    if not chunk.model:
        print("No model in chunk.")
        return

    model = chunk.model
    region = chunk.region

    print("Cropping model by region...")

    R = region.rot
    C = region.center
    size = region.size
    half = size * 0.5

    vertices = model.vertices

    # First clear any previous selections manually
    for face in model.faces:
        face.selected = False

    # Select faces to remove
    for face in model.faces:

        for vid in face.vertices:

            v = vertices[vid].coord
            v_local = R.t() * (v - C)

            if (abs(v_local.x) > half.x or
                abs(v_local.y) > half.y or
                abs(v_local.z) > half.z):

                face.selected = True
                break

    print("Deleting selected faces...")
    model.removeSelection()

    Metashape.app.update()
    print("Finished.")


Metashape.app.addMenuItem(
    "Custom/Crop Model by Region",
    crop_model_by_region
)

