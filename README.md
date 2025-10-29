# Analysis of Global Settlement Expansion and Biodiversity Impact

This repository contains the Python scripts used for the analysis in our paper, "Global rural settlement expansion rivals its urban counterpart in biodiversity impact", which has been accepted for publication in *Communications Earth & Environment*.

---

## Description

The scripts in this repository process global land use and settlement data to quantify the differential impacts of urban and rural expansion on biodiversity. The workflow consists of two main components:

1.  **`split_raster.py`**: A command-line utility to split large geospatial raster files into smaller, manageable tiles with a defined overlap, preparing them for parallel processing.
2.  **`run_hq_batch.py`**: A batch-processing script to run the InVEST Habitat Quality model on the tiled rasters, automating the setup, execution, and organization of model runs.

## Requirements

All necessary Python libraries are listed in the `requirements.txt` file. They can be installed using `pip`:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- Python 3.9+
- `natcap.invest`
- `rasterio`
- `pandas`
- `numpy`

## Usage

### 1. Splitting Raster Data
To split a large raster file (e.g., a global land cover map) into smaller tiles, use the `split_raster.py` script.

**Command-line example:**
```bash
python split_raster.py --input_raster "path/to/your/large_raster.tif" --output_dir "path/to/save/tiles" --grid_size_km 3000 --overlap_km 25
```

### 2. Running the Habitat Quality Model in Batch
After preparing the tiled input data and the necessary CSV tables (as described in the Methods section of our paper), use the `run_hq_batch.py` script to execute the model runs.

**Command-line example:**
```bash
python run_hq_batch.py --workspace "path/to/your/invest_workspace" --lulc_dir "path/to/save/tiles" --threats_template "path/to/your/threats_template.csv" --sensitivity_table "path/to/your/sensitivity.csv"
```

## Citation

Please cite our paper if you use this code in your research. The full citation will be added here upon publication.

---
