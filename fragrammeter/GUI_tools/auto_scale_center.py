'''
Scale and Center Model within a Local Coordinate System
10/28/2026
Maya Gomez, migomez@usc.edu
USC/PIMS

Location for this file:
Windows: C:\Users\[YOUR USERNAME]\AppData\Local\Agisoft\Metashape Pro\scripts
Mac: /Users/[YOUR USERNAME]/Library/Application Support/Agisoft/Metashape Pro/scripts


Script adapted from Steps 5-7 in the batch processing script found here: https://github.com/mayagomez/metashape_batch_process/blob/main/fragrammeter/scripts/2_2_1_GUI/fragram_template_221_GUI.py

Combined and modified with assistance from ChatGPT.

'''

import csv, math, os, Metashape

COORDINATES_PATH = ""  # Optional default file path shown in the popup.
SCALEBARS_PATH = ""
COORDINATE_SKIP_ROWS = 2
REGION_CENTER = (0, 0, 0.02)
REGION_SIZE = (0.13, 0.13, 0.15)
MENU = "Custom/Auto Scale and Center"

def choose_file(QtWidgets, dialog, field, title):
    path, _ = QtWidgets.QFileDialog.getOpenFileName(dialog, title, field.text(), "CSV and text files (*.csv *.txt);;All files (*)")
    if path: field.setText(path)

def accept_settings(QtWidgets, dialog, paths):
    for label, field in paths:
        if not os.path.isfile(field.text().strip()): QtWidgets.QMessageBox.warning(dialog, "Select a file", "Choose a valid {} file.".format(label.lower())); return
    dialog.accept()

def scale_center_settings():
    try: from PySide2 import QtWidgets
    except ImportError: from PySide6 import QtWidgets
    dialog = QtWidgets.QDialog(QtWidgets.QApplication.activeWindow()); dialog.setWindowTitle("Auto Scale and Center"); dialog.setMinimumWidth(640); layout = QtWidgets.QGridLayout(dialog); fields = []; paths = []
    for row, (label, default) in enumerate((("Scalebar", SCALEBARS_PATH), ("Coordinates", COORDINATES_PATH))):
        field = QtWidgets.QLineEdit(default); button = QtWidgets.QPushButton("Browse…"); button.clicked.connect(lambda checked=False, field=field, label=label: choose_file(QtWidgets, dialog, field, "Choose {} file".format(label.lower()))); layout.addWidget(QtWidgets.QLabel(label + " file"), row, 0); layout.addWidget(field, row, 1, 1, 3); layout.addWidget(button, row, 4); paths.append((label, field))
    layout.addWidget(QtWidgets.QLabel("Bounding box: metres relative to the target coordinate system."), 2, 0, 1, 5)
    for column, axis in enumerate(("X", "Y", "Z"), 1): layout.addWidget(QtWidgets.QLabel(axis), 3, column)
    for row, (label, defaults) in enumerate((("Center (m)", REGION_CENTER), ("Size (m)", REGION_SIZE)), 4):
        layout.addWidget(QtWidgets.QLabel(label), row, 0); group = []
        for column, default in enumerate(defaults, 1):
            field = QtWidgets.QDoubleSpinBox(); field.setDecimals(6); field.setRange(-1000000 if row == 4 else 0.000001, 1000000); field.setSingleStep(0.001); field.setValue(default); layout.addWidget(field, row, column); group.append(field)
        fields.append(group)
    buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel); buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply"); buttons.accepted.connect(lambda: accept_settings(QtWidgets, dialog, paths)); buttons.rejected.connect(dialog.reject); layout.addWidget(buttons, 6, 0, 1, 5)
    execute = getattr(dialog, "exec", None) or dialog.exec_
    if execute() != QtWidgets.QDialog.Accepted: return None
    return (paths[0][1].text().strip(), paths[1][1].text().strip(), *(tuple(field.value() for field in group) for group in fields))

def read_bars(path, markers):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as source:
        for number, row in enumerate(csv.reader(source, skipinitialspace=True), 1):
            if not row or not any(value.strip() for value in row): continue
            row = [value.strip() for value in row]
            if row[0].lower() == "marker_1_label": continue
            if len(row) != 4: raise ValueError("Scalebar row {} must have four columns.".format(number))
            first, second, distance, accuracy = row; distance, accuracy = float(distance), float(accuracy)
            if not all(math.isfinite(value) and value > 0 for value in (distance, accuracy)): raise ValueError("Distances and accuracies must be positive finite values in metres.")
            if first == second: raise ValueError("A scalebar needs two different targets.")
            if first not in markers or second not in markers: raise ValueError("Missing target in scalebar row {}: {}, {}".format(number, first, second))
            if markers[first].position is None or markers[second].position is None: raise ValueError("Scalebar targets must have reconstructed 3D positions: {}, {}".format(first, second))
            rows.append((markers[first], markers[second], distance, accuracy))
    if not rows: raise ValueError("No scalebars found in the selected file.")
    return rows

def run():
    doc = Metashape.app.document; chunk = doc.chunk
    if chunk is None: raise ValueError("Open a project and select a chunk first.")
    if not doc.path: raise ValueError("Save the project before running this command.")
    if not chunk.markers: raise ValueError("Detect or place targets first.")
    markers = {marker.label: marker for marker in chunk.markers}
    if len(markers) != len(chunk.markers): raise ValueError("Target labels must be unique.")
    settings = scale_center_settings()
    if settings is None: return
    scalebars, coordinates, region_center, region_size = settings
    rows = read_bars(scalebars, markers)
    crs = Metashape.CoordinateSystem('LOCAL_CS["Local Coordinates (m)",LOCAL_DATUM["Local Datum",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
    chunk.crs = crs; chunk.marker_crs = crs
    for camera in chunk.cameras: camera.reference.enabled = False
    for marker in chunk.markers: marker.reference.enabled = False
    chunk.importReference(path=coordinates, format=Metashape.ReferenceFormatCSV, delimiter=",", columns="nXYZxyz", skip_rows=COORDINATE_SKIP_ROWS, crs=crs, items=Metashape.ReferenceItemsMarkers, ignore_labels=False, create_markers=False)
    with open(coordinates, newline="", encoding="utf-8-sig") as source: coordinate_labels = {row[0] for row in list(csv.reader(source))[COORDINATE_SKIP_ROWS:] if row}
    for marker in chunk.markers: marker.reference.enabled = marker.label in coordinate_labels and marker.reference.location is not None
    controls = [marker for marker in chunk.markers if marker.reference.enabled and marker.reference.location is not None and marker.position is not None]
    if len(controls) < 3: raise ValueError("At least three reconstructed, enabled coordinate targets are required; check labels and CSV format. Targets must not all lie on one line.")
    existing = {frozenset((bar.point0.key, bar.point1.key)): bar for bar in chunk.scalebars}
    for first, second, distance, accuracy in rows:
        key = frozenset((first.key, second.key)); bar = existing.get(key)
        if bar is None: bar = chunk.addScalebar(first, second); existing[key] = bar
        bar.reference.distance = distance; bar.reference.accuracy = accuracy; bar.reference.enabled = True
    chunk.updateTransform()
    transform = chunk.transform.matrix; center = transform.inv().mulp(crs.unproject(Metashape.Vector(region_center))); local = crs.localframe(transform.mulp(center)) * transform; scale = local.scale()
    if not math.isfinite(scale) or scale <= 0: raise ValueError("Invalid transform scale.")
    region = chunk.region; region.center = center; region.size = Metashape.Vector(region_size) / scale; region.rot = local.rotation().t(); chunk.region = region
    doc.save(); Metashape.app.update(); Metashape.app.messageBox("Scaling and centering complete. Project saved.")

def auto_scale_center():
    try: run()
    except Exception as error: print("Auto Scale and Center:", error); Metashape.app.messageBox("Auto Scale and Center stopped: {}\nChanges made before this error may remain in memory; inspect before saving.".format(error))

Metashape.app.addMenuItem(MENU, auto_scale_center)
print("Registered " + MENU)
