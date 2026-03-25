# fs7 — FreeSurfer Processing Module

## Pipeline Position

This module now runs **before** BIDS conversion. The new processing-first order is:

```
download → prepare_nifti.py → mri_processing.py → (BIDS conversion) → SUVR
```

---

## Scripts

### prepare_nifti.py

Extracts the T1 structural scan from each raw MRI download folder and copies it into a flat `nifti/` output directory with a standardized filename.

**Input:** A directory containing raw MRI scan folders. Folder names may or may not have the `MRI_` prefix:
- `MRI_subjID-session_MMDDYYYY/`
- `subjID-session_MMDDYYYY/`

**Output:** `nifti/subjID-scandate_T1w.nii` (flat directory, one file per subject/session)

**T1 file selection priority:**
1. File whose modality is `T1` (e.g. `subjid.T1.nii`)
2. File whose modality is `Cor_MPRAGE` or `CorMPRAGE` (fallback)

**Behavior:**
- `MRI_` prefix in folder name is optional and stripped automatically before parsing
- Folders that don't match the `subjID-session_MMDDYYYY` date pattern are skipped with a warning
- Skips output files that already exist (safe to re-run)
- Writes a timestamped log to `nifti/logs/`

**Usage:**
```bash
# Output defaults to nifti/ sibling to the source directory
python prepare_nifti.py /path/to/MRI

# Explicit output path
python prepare_nifti.py /path/to/MRI --output /path/to/nifti
```

**Output structure:**
```
nifti/
├── logs/
│   └── prepare_nifti_YYYYMMDD_HHMMSS.log
├── subjid01-20230102_T1w.nii
└── subjid02-20230304_T1w.nii
```

---

### mri_processing.py

Runs FreeSurfer `recon-all` followed by `segmentHA_T1.sh` (hippocampal subfield segmentation) for each subject. Supports multiprocessing (1 process per subject).

**Input:** Directory containing `.nii` files in `anat/` subdirectories (BIDS structure)
> ⚠️ Currently expects BIDS structure. To be updated to accept the flat `nifti/` output from `prepare_nifti.py`.

**Output:** `freesurfer741/subjid/` with full `recon-all` results

**Flags:**
- `--hc-only` — run hippocampal segmentation only on already-processed subjects

**Usage:**
```bash
python mri_processing.py /path/to/ADRC [--hc-only]
```

**Environment variables:**
- `CPU_CORES` — number of parallel subjects (default: 1)
- `CONTAINER_NAME` — used as the log filename prefix (default: hostname)
