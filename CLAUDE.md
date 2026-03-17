# CATE FreeSurfer 7 — Neuroimaging Pipeline Context

## Overview

End-to-end pipeline for processing Alzheimer's disease neuroimaging data (MRI + PET) from raw Dropbox downloads through BIDS organization, FreeSurfer 7 structural processing, and PET quantification (SUVR/centiloid scores). Developed for the NWSI/UF research initiative.

---

## Project Structure

```
cate_freesurfer7/
├── bids/                          # Step 1–4: Raw data → BIDS structure
│   ├── README.md
│   ├── download.py                # Download zips from Dropbox via CSV
│   ├── prefix.py                  # Add MRI_/PET_ prefixes to subject folders
│   ├── dropbox_mri_to_bids.py     # Reorganize MRI into BIDS-like layout
│   ├── dropbox_pet_to_bids.py     # Reorganize PET into BIDS-like layout
│   └── unzip_files.sh             # Batch unzip utility
│
├── fs7/                           # Step 5: FreeSurfer structural processing
│   ├── README.md
│   └── mri_processing.py          # recon-all + hippocampal subregions segmentation
│
├── suvr/                          # Steps 6–8: PET quantification
│   ├── README.md
│   ├── prepare_suvr_folder.py     # Build SUVR directory structure
│   ├── registration.py            # PET→MRI registration (FSL FLIRT)
│   └── suvr.py                    # SUVR + centiloid calculation
│
├── Dockerfile                     # Ubuntu 22.04 + FSL + FreeSurfer 7.4.1
└── processing_container.py        # Docker orchestration for FS7 processing
```

---

## Full Pipeline (Data Flow)

```
1. download.py          CSV with Dropbox links → download + extract zips
2. prefix.py            Add MRI_/PET_ prefixes to subject folders
3. dropbox_mri_to_bids  MRI_subjid-session_MMDDYYYY → ADRC/subjid/YYYYMMDD/{anat,modalities}/
4. dropbox_pet_to_bids  PET_subjid-session_MMDDYYYY → ADRC/subjid/YYYYMMDD/{pet,ct}/
5. mri_processing.py    recon-all + segmentHA_T1.sh → freesurfer741/ output
6. prepare_suvr_folder  Build suvr/petDATE_mriDATE/{MRI,register_scan,res}/ structure
7. registration.py      FSL FLIRT: PET→MRI registration → register_scan/*.nii
8. suvr.py              SUVR + centiloid scores → res/*.csv
```

---

## Module Details

### bids/

#### download.py
Downloads and extracts Dropbox zip archives from a CSV file.
- **Input:** CSV with `name` and `link` columns; `--type MRI|PET`
- **Output:** MRI/ or PET/ folder next to CSV, extracted contents
- **Usage:** `python download.py file.csv --type MRI`

#### prefix.py
Renames subject folders by prepending a standardized prefix. Skips already-prefixed folders.
- **Usage:** `python prefix.py /path/to/folder --prefix MRI_ [--dry-run]`

#### dropbox_mri_to_bids.py
Parses `MRI_subjid-session_MMDDYYYY` folder names and reorganizes `.nii` files into:
```
ADRC/
└── subjid/
    └── YYYYMMDD/
        ├── anat/         ← T1w.nii (or CorMPRAGE.nii as fallback)
        └── modalities/   ← all original files
```
- **T1w priority:** prefers files matching `T1w`; falls back to `CorMPRAGE`
- **Usage:** `python dropbox_mri_to_bids.py /batch/MRI [--target_dir /output]`

#### dropbox_pet_to_bids.py
Same structure as MRI version but for PET data:
```
ADRC/subjid/YYYYMMDD/
├── pet/    ← files matching mean_5mmblur, PET_6mmblur, etc.
└── ct/     ← files matching amyloid_pet_ct, pet_ct, etc.
```
- **Usage:** `python dropbox_pet_to_bids.py /batch/PET [--target_dir /output]`

---

### fs7/

#### mri_processing.py
Runs FreeSurfer `recon-all` followed by `segmentHA_T1.sh` (hippocampal segmentation) for each subject. Supports multiprocessing (1 process/subject).
- **Input:** `ADRC/subjid/YYYYMMDD/anat/*.nii`
- **Output:** `freesurfer741/subjid/` with full recon-all results
- **Flags:** `--hc-only` to run hippocampal segmentation on already-processed subjects
- **Usage:** `python mri_processing.py /path/to/ADRC [--hc-only]`
- **Container:** `python processing_container.py /path/to/ADRC [--license license.txt]`

---

### suvr/

#### prepare_suvr_folder.py
Builds the directory structure pairing each PET scan date with its closest/corresponding MRI date. Also extracts FreeSurfer volume stats.
- **Output:** `ADRC/subjid/YYYYMMDD/suvr/petDATE_mriDATE/{MRI/,register_scan/,res/}`
- **Parallelization:** `--parallel-mode subjects|combinations`, `--cores N`
- **Usage:** `python prepare_suvr_folder.py /path/to/ADRC [--cores N]`

#### registration.py
Registers PET scans to MRI space using FSL FLIRT (12 DOF, corratio, 90° search).
- **Input:** SUVR folder with MRI and PET `.nii` files
- **Output:** `register_scan/petID_reg_mriID_mriModality.nii` + `.mat` transform
- **Usage:** `python registration.py /path/to/ADRC [--cores N] [--single] [--verbose]`

#### suvr.py
Calculates SUVR (Standardized Uptake Value Ratio) and centiloid scores by ROI using registered PET + FreeSurfer `aparc+aseg` segmentation.

**ROIs:** AnteriorCingulate, PosteriorCingulate, Frontal, Temporal, Parietal, Global, Total
**Reference region:** Cerebellum gray matter (volume-weighted)

**Centiloid formulas:**
- Amyvid (pre-2016-09-27): `183.07 × global_SUVR − 177.26`
- Neuraceq (≥2016-09-27): `153.4 × global_SUVR − 154.9`

**Output CSVs in `res/`:**
- Per-ROI statistics (mean, median, sum, SUVR)
- Combined results with centiloid scores
- Gray-matter-normalized variants

**Usage:** `python suvr.py /path/to/ADRC [--compound neuraceq|amyvid] [--single-subject subjid] [-v]`

---

### Docker / Container

#### Dockerfile
- Base: `ubuntu:22.04`
- Installs: FSL (via conda), FreeSurfer 7.4.1, MCR R2019b, Python 3
- Sets: `FREESURFER_HOME=/usr/local/freesurfer`, `FSLDIR=/usr/local/fsl`
- Copies `mri_processing.py` and `suvr/*` to `/workspace`

#### processing_container.py
Launches the Docker container with CPU cores proportional to subject count. Verifies FreeSurfer license before starting.
- **CPU logic:** `min(n_subjects + 1, available_cpus - 1)`
- **Mounts:** data directory + license file
- **Usage:** `python processing_container.py /path/to/ADRC [--license /path/to/license.txt]`

---

## Naming Conventions

| Pattern | Description |
|--------|-------------|
| `MRI_subjid-session_MMDDYYYY` | Raw MRI download folder name |
| `PET_subjid-session_MMDDYYYY` | Raw PET download folder name |
| `subjid-YYYYMMDD_T1w.nii` | Post-BIDS MRI filename |
| `subjid-YYYYMMDD_PET.nii` | Post-BIDS PET filename |
| `petID_reg_mriID_mriModality.nii` | Registered PET filename |

---

## Environment Requirements

| Requirement | Details |
|-------------|---------|
| Python 3.x | nibabel, pandas, numpy, tqdm, pathlib |
| FreeSurfer 7.4.1 | `FREESURFER_HOME` env var + valid `license.txt` |
| FSL | `FSLDIR` env var, FLIRT for registration |
| Docker | Optional — used via `processing_container.py` |
| `SUBJECTS_DIR` | FreeSurfer subjects directory (for stats extraction) |
| `CPU_CORES` | Set by container; controls parallel jobs |

---

## Key Logging Behavior

All major scripts create timestamped log files:
- BIDS scripts → `logs/` next to input data
- FS7 script → per-subject log files
- SUVR scripts → `suvr/logs/` directory

Each run generates both a summary log and per-subject detail logs.
