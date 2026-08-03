'''
Move Region Vertically
02/19/2026
Maya Gomez, migomez@usc.edu
USC/PIMS

Written with the help of AI (ChatGPT).
'''

import Metashape
from PySide2 import QtWidgets

def move_region_vertical():

    chunk = Metashape.app.document.chunk
    if not chunk:
        print("No active chunk.")
        return

    # Prompt user
    value, ok = QtWidgets.QInputDialog.getDouble(
        None,
        "Move Region",
        "Enter vertical movement (meters):",
        0.055,      # default value
        -10.0,     # minimum
        10.0,      # maximum
        4          # decimals
    )

    if not ok:
        return  # user cancelled

    region = chunk.region
    scale = chunk.transform.scale

    delta_internal = value / scale

    # Region's local Z axis
    box_z_axis = region.rot * Metashape.Vector([0, 0, 1])

    new_center = Metashape.Vector(region.center)
    new_center += box_z_axis * delta_internal

    region.center = new_center
    chunk.region = region

    print(f"Moved region by {value} meters")
    Metashape.app.update()


label = "Custom/Move Region Vertically"
try:
    Metashape.app.removeMenuItem(label)
except:
    pass

Metashape.app.addMenuItem(label, move_region_vertical)
