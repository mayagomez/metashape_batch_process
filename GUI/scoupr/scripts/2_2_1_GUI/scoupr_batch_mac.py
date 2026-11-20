# Mac batch adaptation of the original HPC-specific template script scoupr_1_8_3_lowco.py by Maya Gomez (USC/PIMS). Adaptation generated using Chat GPT.
# Original acknowledgements: Will Greene, Sam Marshall, Wyatt Million, Asif-ul Islam.
# Run inside Metashape Professional 2.2.1: Tools > Run Script.
# Each immediate child folder is one photoset; processing is sequential.

from pathlib import Path
import csv, gc, math, traceback
from datetime import datetime
import Metashape
from PySide2 import QtCore, QtWidgets

INPUT_FOLDER = "/Volumes/Maya_Frag/frag/images/Alfeus/111226"
OUTPUT_ROOT = "/Volumes/Maya_Frag/frag/models/Alfeus"
SCALEBARS_FILE = "/Users/migomez/Documents/USC/Photogrammetry/Scales:Coords/Adjustable3Scale_BARSTICKERS_060123.txt"
IMAGE_EXTENSIONS = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
DRY_RUN = True # Set by the Setup window; starts in Dry run mode each time
# Existing output prefixes are skipped, including partial builds; move those outputs before retrying.

class BatchSetup(QtWidgets.QDialog):
    def __init__(self):
        super().__init__(); self.setWindowTitle("SCOUPR Batch Process — Setup"); self.resize(400, 400); self.setSizeGripEnabled(True); self.settings = QtCore.QSettings("SCOUPR", "BatchProcess"); self.fields = {}; layout = QtWidgets.QVBoxLayout(self); info = QtWidgets.QLabel("Select the parent folder containing one folder per photoset."); info.setWordWrap(True); layout.addWidget(info); form = QtWidgets.QFormLayout(); form.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows); form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow); layout.addLayout(form)
        for key, label, default, directory in [("input", "Photoset parent folder", INPUT_FOLDER, True), ("output", "Output root folder", OUTPUT_ROOT, True), ("scalebars", "Scalebar file", SCALEBARS_FILE, False)]:
            row = QtWidgets.QWidget(); row_layout = QtWidgets.QHBoxLayout(row); row_layout.setContentsMargins(0, 0, 0, 0); edit = QtWidgets.QLineEdit(str(self.settings.value(key, default))); self.fields[key] = edit; row_layout.addWidget(edit, 1); button = QtWidgets.QPushButton("Browse…"); button.clicked.connect(lambda checked=False, k=key, d=directory: self.browse(k, d)); row_layout.addWidget(button); form.addRow(label, row)
        self.destination = QtWidgets.QLabel(); self.destination.setTextFormat(QtCore.Qt.PlainText); self.destination.setWordWrap(True); layout.addWidget(self.destination); self.fields["input"].textChanged.connect(self.update_destination); self.fields["output"].textChanged.connect(self.update_destination); self.update_destination(); self.mode = QtWidgets.QComboBox(); self.mode.addItems(["Dry run — check files, do not build", "Build models"]); form.addRow("Run mode", self.mode); buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel); buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Run"); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def update_destination(self, *unused): self.destination.setText("Models will be saved to: " + str(Path(self.fields["output"].text().strip()).expanduser() / Path(self.fields["input"].text().strip()).name))
    def browse(self, key, directory):
        current = str(Path(self.fields[key].text().strip()).expanduser()); selected = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder", current) if directory else QtWidgets.QFileDialog.getOpenFileName(self, "Select reference file", current, "Reference files (*.txt *.csv);;All files (*)")[0]
        if selected: self.fields[key].setText(selected)
    def accept(self):
        values = {key: edit.text().strip() for key, edit in self.fields.items()}
        try:
            if not all(values.values()): raise ValueError("Select all three paths.")
            if not Path(values["input"]).expanduser().is_dir(): raise ValueError("The photoset parent folder does not exist or the drive is disconnected.")
            for key in ("scalebars",):
                if not Path(values[key]).expanduser().is_file(): raise ValueError(f"The {key} file does not exist or is unavailable.")
            target = Path(values["output"]).expanduser()
            if target.exists() and not target.is_dir(): raise ValueError("The output root must be a folder.")
            read_scalebars(Path(values["scalebars"]).expanduser())
        except (OSError, ValueError) as error: QtWidgets.QMessageBox.warning(self, "Check your selections", str(error)); return
        for key, value in values.items(): self.settings.setValue(key, value)
        self.settings.sync()
        if self.settings.status() != QtCore.QSettings.NoError: QtWidgets.QMessageBox.warning(self, "Settings not saved", "These paths can be used now, but could not be remembered for next time.")
        super().accept()

def configure_batch():
    global INPUT_FOLDER, OUTPUT_ROOT, SCALEBARS_FILE, DRY_RUN
    dialog = BatchSetup()
    if dialog.exec_() != QtWidgets.QDialog.Accepted: return False
    INPUT_FOLDER, OUTPUT_ROOT, SCALEBARS_FILE = [dialog.fields[key].text().strip() for key in ("input", "output", "scalebars")]; DRY_RUN = dialog.mode.currentIndex() == 0; return True

class BatchStatus(QtWidgets.QWidget):
    changed = QtCore.Signal(str)
    def __init__(self):
        super().__init__(None, QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint); self.setWindowTitle("SCOUPR Batch Process"); self.resize(640, 420); self.context = ""; self.stage = ""; self.rows = {}; self.states = {}; layout = QtWidgets.QVBoxLayout(self); self.label = QtWidgets.QLabel(); self.label.setTextFormat(QtCore.Qt.PlainText); self.label.setWordWrap(True); layout.addWidget(self.label); self.table = QtWidgets.QTableWidget(0, 2); self.table.setHorizontalHeaderLabels(["Photoset", "Status"]); self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers); self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows); self.table.verticalHeader().setVisible(False); self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch); self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents); layout.addWidget(self.table); self.note = QtWidgets.QLabel("Closing this window does not cancel processing. Existing outputs are skipped, including partial models."); self.note.setWordWrap(True); layout.addWidget(self.note); self.changed.connect(self.render); self.show(); self.raise_()
    def render(self, text): self.label.setText(text); self.repaint()
    def refresh(self):
        if QtCore.QThread.currentThread() == self.thread(): QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
    def set_photosets(self, names):
        names = list(names); self.rows = {name: i for i, name in enumerate(names)}; self.states = {}; self.table.setRowCount(len(names))
        for name, row in self.rows.items(): self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(name)); self.set_state(name, "Awaiting processing")
        self.refresh()
    def set_state(self, name, state, detail=""):
        self.states[name] = state; item = QtWidgets.QTableWidgetItem(state); item.setToolTip(detail); self.table.setItem(self.rows[name], 1, item); self.refresh()
    def update_status(self, stage, unused_percent=None): self.stage = stage; self.changed.emit(self.context + "\n" + stage); self.refresh()
    def progress(self, unused_percent): self.refresh()
    def step(self, stage): self.update_status(stage); return self.progress

STATUS = None

def read_scalebars(path):
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for number, row in enumerate(csv.reader(handle), 1):
            if not row or not any(v.strip() for v in row) or row[0].lstrip().startswith("#"): continue
            if len(row) != 4: raise ValueError(f"Scalebar line {number}: expected marker1,marker2,distance,accuracy (no header)")
            a, b, distance, accuracy = [v.strip() for v in row]; distance, accuracy = float(distance), float(accuracy)
            if not a or not b or a == b or not math.isfinite(distance) or not math.isfinite(accuracy) or min(distance, accuracy) <= 0: raise ValueError(f"Invalid scalebar on line {number}")
            rows.append((a, b, distance, accuracy))
    if not rows: raise ValueError("Scalebar file has no data")
    return rows

def create_scalebars(chunk, rows):
    markers = {m.label: m for m in chunk.markers}; created = 0
    for a, b, distance, accuracy in rows:
        if a not in markers or b not in markers: print(f"WARNING: skipping scalebar {a} / {b}: marker missing"); continue
        bar = chunk.addScalebar(markers[a], markers[b]); bar.reference.distance = distance; bar.reference.accuracy = accuracy; bar.reference.enabled = True; created += 1
    if not created: raise RuntimeError("No scalebars could be created; check target detection and marker labels")

def discover(root):
    return [(folder, sorted((p for p in folder.iterdir() if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in IMAGE_EXTENSIONS), key=lambda p: p.name.lower())) for folder in sorted(root.iterdir(), key=lambda p: p.name.lower()) if folder.is_dir() and not folder.name.startswith('.')]

def run_batch():
    global STATUS
    STATUS = BatchStatus(); STATUS.update_status("Checking paths and reference files")
    root = Path(INPUT_FOLDER).expanduser(); output = Path(OUTPUT_ROOT).expanduser() / root.name
    if not root.is_dir(): raise FileNotFoundError(f"Photoset parent folder not found: {root}")
    for path in (SCALEBARS_FILE,):
        if not Path(path).expanduser().is_file(): raise FileNotFoundError(f"Reference file not found: {path}")
    rows = read_scalebars(Path(SCALEBARS_FILE).expanduser()); sets = discover(root); STATUS.set_photosets(folder.name for folder, _ in sets)
    if not any(photos for _, photos in sets): raise ValueError("No photos found in immediate child folders; put each photoset in its own folder")
    print(f"Metashape {Metashape.app.version}; output: {output}")
    if not str(Metashape.app.version).startswith('2.2.'): print("WARNING: adapted for Metashape 2.2.1; other versions have not been validated")
    if not DRY_RUN: output.mkdir(parents=True, exist_ok=True)
    log = output / ("batch_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".csv"); results = []
    for index, (folder, photos) in enumerate(sets, 1):
        STATUS.context = f'Processing Photoset: {folder.name} (Photoset {index}/{len(sets)})'; STATUS.update_status("Checking photoset")
        stem = output / folder.name; status = ""; detail = ""
        print(f'Checking {folder.name}, photoset {index}/{len(sets)} ({len(photos)} images)', flush=True)
        if not photos: status = "empty"
        elif output.exists() and any(p.name.startswith(folder.name + '.') or p.name == folder.name + '_report.pdf' or p.name == folder.name + '_error.txt' for p in output.iterdir()): status = "existing_outputs"
        elif DRY_RUN: status = "planned"
        else:
            print(f'Processing Photoset: {folder.name} (Photoset {index}/{len(sets)})', flush=True)
            STATUS.set_state(folder.name, "Processing")
            try: process_photoset(folder, photos, stem, rows); status = "completed"
            except Exception as error: status = "failed"; detail = str(error); traceback.print_exc(); (output / (folder.name + "_error.txt")).write_text(traceback.format_exc(), encoding="utf-8")
            finally: gc.collect()
        STATUS.set_state(folder.name, {"completed": "Completed", "failed": "Failed", "planned": "Awaiting processing (dry run)", "empty": "Skipped — no photos", "existing_outputs": "Skipped — existing outputs"}[status], detail)
        STATUS.update_status("Dry run: planned (no build)" if status == "planned" else status, 100)
        results.append((folder.name, len(photos), status, detail)); print(f'{folder.name}, photoset {index}/{len(sets)}: {status}', flush=True)
        if not DRY_RUN:
            with log.open("w", newline="", encoding="utf-8") as handle: writer = csv.writer(handle); writer.writerow(("photoset", "images", "status", "detail")); writer.writerows(results)
    print("Batch finished: " + ", ".join(f"{s}: {sum(r[2] == s for r in results)}" for s in sorted({r[2] for r in results})))
    if not DRY_RUN: print(f"Summary: {log}")
    STATUS.context = "Dry run finished" if DRY_RUN else "Batch finished"; STATUS.update_status(", ".join(f"{state}: {sum(r[2] == state for r in results)}" for state in sorted({r[2] for r in results})), 100)
    return results

def process_photoset(folder, photos, stem, scale_rows):
    STATUS.update_status("Loading photos and saving project")
    doc = Metashape.Document(); chunk = doc.addChunk(); chunk.label = folder.name; chunk.addPhotos([str(p) for p in photos]); doc.save(str(stem) + ".psz")
    chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=False, filter_stationary_points=False, keypoint_limit=40000, tiepoint_limit=4000, reset_matches=True, progress=STATUS.step('Matching photos'))
    STATUS.update_status("Saving project")
    doc.save()
    chunk.alignCameras(adaptive_fitting=True, reset_alignment=True, progress=STATUS.step('Aligning cameras'))
    STATUS.update_status("Saving project")
    doc.save()
    chunk.detectMarkers(target_type=Metashape.CircularTarget12bit, tolerance=50, filter_mask=False, inverted=False, noparity=False, maximum_residual=5, minimum_size=0, minimum_dist=5, progress=STATUS.step('Detecting markers'))
    STATUS.update_status("Setting local coordinates")
    chunk.crs = Metashape.CoordinateSystem('LOCAL_CS["Local Coordinates (m)",LOCAL_DATUM["Local Datum",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
    STATUS.update_status("Saving project")
    doc.save()
    STATUS.update_status("Creating scalebars")
    create_scalebars(chunk, scale_rows)
    STATUS.update_status("Saving project")
    doc.save()
    STATUS.update_status("Updating model scale")
    chunk.updateTransform()
    chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering, reuse_depth=False, max_neighbors=16, progress=STATUS.step('Building depth maps'))
    STATUS.update_status("Saving project")
    doc.save()
    chunk.buildModel(surface_type=Metashape.Arbitrary, source_data=Metashape.DepthMapsData, interpolation=Metashape.EnabledInterpolation, face_count=Metashape.HighFaceCount, progress=STATUS.step('Building mesh'))
    STATUS.update_status("Saving project")
    doc.save()
    chunk.buildUV(mapping_mode=Metashape.GenericMapping, progress=STATUS.step('Building UV mapping'))
    chunk.buildTexture(blending_mode=Metashape.MosaicBlending, texture_size=8192, fill_holes=True, progress=STATUS.step('Building texture'))
    STATUS.update_status("Saving project")
    doc.save()
    STATUS.update_status("Saving project")
    doc.save()
    chunk.exportModel(str(stem) + '.obj', binary=True, precision=6, save_normals=True, save_colors=True, save_cameras=True, save_markers=True, save_udim=False, strip_extensions=False, progress=STATUS.step('Exporting OBJ'))
    chunk.exportReport(path=str(stem) + '_report.pdf', title=folder.name, font_size=12, page_numbers=True, include_system_info=True, progress=STATUS.step('Exporting PDF report'))

if __name__ == "__main__":
    try:
        if configure_batch(): run_batch()
    except BaseException:
        if STATUS is not None: STATUS.update_status("Stopped: " + traceback.format_exc().splitlines()[-1])
        raise
