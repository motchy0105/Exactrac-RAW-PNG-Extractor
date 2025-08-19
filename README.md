# Exactrac-RAW-PNG-Extractor
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-Free-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

Fast and simple decompression of Exactrac images into **PNG** and **RAW**.


---

## Overview

**Exactrac RAW-PNG Extractor** is a lightweight tool to **decompress and convert Exactrac DICOM files** into **RAW** and **PNG** images.  
It features a simple **Tkinter GUI** and supports **multi-core processing** for faster performance.

---

## Features

- Rapid decompression of Exactrac DICOM files  
- Automatic conversion to **RAW** and **PNG** formats  
- Automatic organization by **Patient** and **Study Date**  
- Intuitive GUI with progress bar  
- Multi-core support to accelerate processing  

---

## Requirements

- Python 3.10+  
- Ensure that **patient folders are archived and extracted from the Exactrac workstation** before running the tool.  
- Sufficient disk space for RAW and PNG output files  

## Installation

1. Clone the repository:
```bash
git clone https://github.com/motchy0105/Exactrac-RAW-PNG-Extractor.git
cd Exactrac-RAW-PNG-Extractor
```
2. Set up a virtual environment:
```bash
python -m venv Exac_py
Exac_py\Scripts\activate      # Windows
pip install -r requirements.txt
```
3. Usage
Run the application:
```bash
python Decompress_Exactrac_final.py
```

- Click Select DICOM Folder and choose the folder containing your DICOM files.
- Click Start Processing to generate RAW and PNG images.
- Files will be automatically organized by Patient and Study Date.

Alternatively, you can simply use the provided executable.

## License

This project is free for personal and educational use. Feel free to experiment and modify as you like.