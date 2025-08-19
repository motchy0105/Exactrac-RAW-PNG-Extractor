# --- Optimisation des imports ---
import os, zlib, shutil, time, threading
from pathlib import Path
from multiprocessing import Pool, cpu_count, freeze_support, Manager
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pydicom
import numpy as np
from PIL import Image

# --- CONFIG ---
IMAGE_SHAPE = (768, 768)
BYTES_PER_IMAGE = IMAGE_SHAPE[0] * IMAGE_SHAPE[1] * 2  # uint16

# --- FONCTIONS UTILITAIRES ---
def add_dcm_extension(root_dir: Path):
    for file_path in root_dir.rglob("*"):
        if file_path.is_file() and not file_path.suffix:
            file_path.rename(file_path.with_suffix(".dcm"))

def decompress_and_convert(dicom_path, base_output_dir):
    dicom_path = Path(dicom_path)
    try:
        ds = pydicom.dcmread(dicom_path, force=True)
        study_date = getattr(ds, "StudyDate", "UnknownDate")
        study_date_fmt = f"{study_date[6:8]}-{study_date[4:6]}-{study_date[0:4]}" if study_date != "UnknownDate" else "UnknownDate"

        raw_data = None
        for elem in ds.iterall():
            if isinstance(elem.value, bytes) and len(elem.value) > 9:
                try:
                    decompressed = zlib.decompress(elem.value[9:], zlib.MAX_WBITS | 32)
                    if len(decompressed) >= BYTES_PER_IMAGE:
                        raw_data = decompressed[:BYTES_PER_IMAGE]
                        break
                except Exception:
                    continue

        if raw_data is None:
            return (str(dicom_path), "NO_COMPRESSED_DATA", "")

        if np.frombuffer(raw_data, dtype=np.uint16).max() == 65535:
            return (str(dicom_path), "BAD_IMAGE", "Pixel max 65535")

        patient_id = getattr(ds, "PatientID", "UnknownPatient")
        out_dir = Path(base_output_dir) / "Patients" / patient_id / study_date_fmt
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / dicom_path.stem

        (base.with_suffix(".raw")).write_bytes(raw_data)
        img = Image.frombuffer('I;16', IMAGE_SHAPE, raw_data, 'raw', 'I;16', 0, 1)
        img.save(base.with_suffix(".png"), optimize=True)

        return (str(dicom_path), "OK", "")
    except Exception as e:
        return (str(dicom_path), "ERROR", str(e))

def collect_dicom_files(root_dir: Path):
    return list(root_dir.rglob("*.dcm"))

# --- Multiprocessing ---
def worker(args):
    return decompress_and_convert(*args)

def process_files_worker(dicom_files, queue, base_output_dir):
    results = []
    args_list = [(f, base_output_dir) for f in dicom_files]
    with Pool(cpu_count()) as pool:
        for res in pool.imap_unordered(worker, args_list, chunksize=10):
            results.append(res)
            queue.put("PROGRESS")
    queue.put(("DONE", results))

# --- Tkinter ---
class DicomProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Décompression rapide")
        self.geometry("600x300")
        self.resizable(False, False)
        self.dicom_folder = None
        self.dicom_files = []
        self.create_widgets()

    def create_widgets(self):
        self.select_button = ttk.Button(self, text="Sélectionner dossier DICOM", command=self.select_folder)
        self.select_button.pack(pady=10)
        self.status_label = ttk.Label(self, text="Aucun dossier sélectionné")
        self.status_label.pack()
        self.process_button = ttk.Button(self, text="Lancer traitement", command=self.start_processing, state='disabled')
        self.process_button.pack(pady=10)
        self.progress = ttk.Progressbar(self, length=500, mode='determinate')
        self.progress.pack(pady=10)
        self.log_text = tk.Text(self, height=8, width=70, state='disabled')
        self.log_text.pack(padx=10, pady=5)

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.dicom_folder = Path(folder_selected)
            self.status_label.config(text="Recherche des fichiers DICOM...")
            self.update()
            add_dcm_extension(self.dicom_folder)
            self.dicom_files = collect_dicom_files(self.dicom_folder)
            self.status_label.config(text=f"{len(self.dicom_files)} fichiers DICOM trouvés.")
            self.process_button.config(state='normal' if self.dicom_files else 'disabled')
            self.progress['value'] = 0
            self.clear_log()

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')

    def start_processing(self):
        if not self.dicom_files:
            messagebox.showwarning("Avertissement", "Aucun fichier DICOM à traiter.")
            return
        self.process_button.config(state='disabled')
        self.select_button.config(state='disabled')
        self.clear_log()
        self.log(f"Traitement de {len(self.dicom_files)} fichiers sur {cpu_count()} cœurs...")
        threading.Thread(target=self.process_files, daemon=True).start()

    def process_files(self):
        start_time = time.perf_counter()
        queue = Manager().Queue()
        thread = threading.Thread(target=process_files_worker, args=(self.dicom_files, queue, self.dicom_folder), daemon=True)
        thread.start()

        total_files = len(self.dicom_files)
        processed = 0
        results = []

        def check_queue():
            nonlocal processed, results
            while not queue.empty():
                msg = queue.get()
                if msg == "PROGRESS":
                    processed += 1
                    self.progress['value'] = (processed / total_files) * 100
                    self.update_idletasks()
                elif isinstance(msg, tuple) and msg[0] == "DONE":
                    results = msg[1]
                    finish()
                    return
            self.after(100, check_queue)

        def finish():
            elapsed = time.perf_counter() - start_time
            self.log(f"Traitement terminé en {elapsed:.2f}s")
            errors = [r for r in results if r[1] not in ("OK", "NO_COMPRESSED_DATA", "BAD_IMAGE")]
            if errors:
                self.log(f"{len(errors)} fichiers ont rencontré des erreurs:")
                for p, s, m in errors:
                    self.log(f" - [{s}] {p}: {m}")
            else:
                self.log("Tous les fichiers traités avec succès ✅")
            self.process_button.config(state='normal')
            self.select_button.config(state='normal')

        check_queue()

if __name__ == "__main__":
    freeze_support()
    app = DicomProcessorApp()
    app.mainloop()
