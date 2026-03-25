# CATE FreeSurfer 7 — Neuroimaging Pipeline

End-to-end pipeline for processing Alzheimer's disease neuroimaging data (MRI + PET) from raw Dropbox downloads through FreeSurfer 7 structural processing and PET quantification (SUVR / centiloid scores). Developed for the NWSI/UF research initiative.

---

## Pipeline Overview

The pipeline is split into two tracks that run independently before converging at the SUVR step.

```
MRI track
─────────
download.py  →  prepare_nifti.py  →  mri_processing.py
                                              │
                                              ▼
                                    (BIDS conversion)  →  prepare_suvr_folder.py  →  registration.py  →  suvr.py
                                              ▲
PET track                                     │
─────────
download.py  →  dropbox_pet_to_bids.py ───────┘
```

### Step-by-step

| Step | Script | Description |
|------|--------|-------------|
| 1 | `bids/download.py` | Download MRI and PET zip archives from Dropbox via CSV |
| 2 | `fs7/prepare_nifti.py` | Extract T1 scans from raw MRI folders into a flat `nifti/` directory |
| 3 | `fs7/mri_processing.py` | Run FreeSurfer `recon-all` + hippocampal segmentation on all files in `nifti/` |
| 4 | `bids/dropbox_mri_to_bids.py` | Reorganise MRI downloads into BIDS structure |
| 5 | `bids/dropbox_pet_to_bids.py` | Reorganise PET downloads into BIDS structure |
| 6 | `suvr/prepare_suvr_folder.py` | Build SUVR directory structure pairing PET and MRI dates |
| 7 | `suvr/registration.py` | Register PET to MRI space using FSL FLIRT |
| 8 | `suvr/suvr.py` | Calculate SUVR and centiloid scores by ROI |

> `bids/prefix.py` is a utility to add `MRI_` / `PET_` prefixes to subject folders if missing. Use it between steps 1 and 2 if needed.

---

## Project Structure

```
cate_freesurfer7/
├── bids/
│   ├── download.py               # Step 1 — download zips from Dropbox
│   ├── prefix.py                 # Utility — add MRI_/PET_ prefixes
│   ├── dropbox_mri_to_bids.py    # Step 4 — MRI → BIDS
│   └── dropbox_pet_to_bids.py    # Step 5 — PET → BIDS
│
├── fs7/
│   ├── prepare_nifti.py          # Step 2 — extract T1 files into nifti/
│   ├── mri_processing.py         # Step 3 — recon-all + hippocampal segmentation
│   ├── CLAUDE.md                 # Module context for AI-assisted development
│   └── tests/
│       ├── test_prepare_nifti.py
│       └── test_mri_processing.py
│
├── suvr/
│   ├── prepare_suvr_folder.py    # Step 6 — build SUVR directory structure
│   ├── registration.py           # Step 7 — FSL FLIRT PET→MRI registration
│   └── suvr.py                   # Step 8 — SUVR + centiloid calculation
│
├── Dockerfile                    # Ubuntu 22.04 + FSL + FreeSurfer 7.4.1
├── processing_container.py       # Docker orchestration for FS7 processing
└── pyproject.toml                # Python project config (uv)
```

---

## MRI Track — Detailed Usage

### Step 1 — Download MRI scans

```bash
python bids/download.py mri_links.csv --type MRI
```

Downloads and extracts zips into an `MRI/` folder next to the CSV.

---

### Step 2 — Extract T1 files (`prepare_nifti.py`)

Scans every subdirectory in `MRI/`, identifies the T1 structural scan, and copies it to a flat `nifti/` folder with a standardised filename.

**Supported folder name formats:**
```
MRI_subjID-session_MMDDYYYY    # with prefix and session
MRI_subjID_MMDDYYYY            # with prefix, no session
subjID-session_MMDDYYYY        # no prefix
subjID_MMDDYYYY                # no prefix, no session
```

**Output filename format:** `subjID-YYYYMMDD_T1w.nii`

**T1 selection priority:**
1. File with modality `.T1.nii`
2. File with modality `.Cor_MPRAGE.nii` (legacy fallback)

```bash
# Output defaults to nifti/ sibling to MRI/
python fs7/prepare_nifti.py /path/to/MRI

# Explicit output path
python fs7/prepare_nifti.py /path/to/MRI --output /path/to/nifti
```

**Resulting structure:**
```
nifti/
├── logs/
│   └── prepare_nifti_YYYYMMDD_HHMMSS.log
├── 120600-20250812_T1w.nii
├── 120573-20240717_T1w.nii
└── ...
```

---

### Step 3 — FreeSurfer processing (`mri_processing.py`)

Runs `recon-all` followed by `segmentHA_T1.sh` on every `.nii` file in the `nifti/` directory. Output is written to `$SUBJECTS_DIR` (FreeSurfer default).

**Requirements:**
- `FREESURFER_HOME` environment variable set with a valid `license.txt`
- `SUBJECTS_DIR` environment variable pointing to the desired output directory

```bash
export SUBJECTS_DIR=/path/to/freesurfer/subjects

# Full processing (recon-all + hippocampal segmentation)
python fs7/mri_processing.py /path/to/nifti

# Hippocampal segmentation only on already-processed subjects
python fs7/mri_processing.py /path/to/nifti --hc-only
```

Parallelism is controlled by the `CPU_CORES` environment variable (default: 1).

---

## PET Track — Detailed Usage

### Step 1 — Download PET scans

```bash
python bids/download.py pet_links.csv --type PET
```

### Step 5 — Reorganise into BIDS

```bash
python bids/dropbox_pet_to_bids.py /path/to/PET [--target_dir /output]
```

---

## SUVR Track — Detailed Usage

### Step 6 — Prepare SUVR folder structure

```bash
python suvr/prepare_suvr_folder.py /path/to/ADRC [--cores N]
```

### Step 7 — PET → MRI registration

```bash
python suvr/registration.py /path/to/ADRC [--cores N]
```

### Step 8 — Calculate SUVR and centiloid scores

```bash
python suvr/suvr.py /path/to/ADRC [--compound neuraceq|amyvid] [--single-subject subjid]
```

**ROIs:** AnteriorCingulate, PosteriorCingulate, Frontal, Temporal, Parietal, Global, Total

**Centiloid formulas:**
- Amyvid (pre 2016-09-27): `183.07 × global_SUVR − 177.26`
- Neuraceq (≥ 2016-09-27): `153.4 × global_SUVR − 154.9`

---

## Docker / Container

```bash
python processing_container.py /path/to/ADRC [--license /path/to/license.txt]
```

Launches a Docker container with FreeSurfer 7.4.1 and FSL pre-installed. CPU cores are allocated as `min(n_subjects + 1, available_cpus - 1)`.

---

## Environment Requirements

| Requirement | Details |
|-------------|---------|
| Python 3.12+ | managed via `uv` |
| FreeSurfer 7.4.1 | `FREESURFER_HOME` + valid `license.txt` |
| `SUBJECTS_DIR` | FreeSurfer output directory |
| FSL | `FSLDIR` set, FLIRT used for registration |
| Docker | Optional — used by `processing_container.py` |

---

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest fs7/tests/ -v
```

Tests cover the pure-Python logic in `prepare_nifti.py` and `mri_processing.py` (folder name parsing, T1 file selection, nifti discovery) using real folder/filename patterns from the dataset.
