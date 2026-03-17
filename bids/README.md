# CATE FS7 BIDS Prepping Scripts

Scripts for downloading, organizing, and converting NWSI/UF neuroimaging data (MRI and PET) into BIDS-like format for FreeSurfer 7 processing.

---

## Table of Contents

1. [Download & Unzip](#1-download--unzip)
2. [Add Subject Prefixes](#2-add-subject-prefixes)
3. [Convert MRI to BIDS](#3-convert-mri-to-bids)
4. [Convert PET to BIDS](#4-convert-pet-to-bids)
5. [Sync Data (Excluding Processing Outputs)](#5-sync-data-excluding-processing-outputs)

---

## 1. Download & Unzip

Download a zip file from Dropbox:

```bash
curl -L -o folder_name.zip "URL"
```

Unzip all zip files in a directory:

```bash
./unzip_files.sh /path/to/directory_with_zip_files
```

---

## 2. Add Subject Prefixes

UF grant subjects (IDs starting at 320) need `MRI_` or `PET_` prefixes added to their folder names before conversion.

```bash
python3 prefix.py /path/to/folder_with_subjects --prefix MRI_
python3 prefix.py /path/to/folder_with_subjects --prefix PET_
```

---

## 3. Convert MRI to BIDS

**Script:** `dropbox_mri_to_bids.py`

```bash
python3 dropbox_mri_to_bids.py /path/to/source_dir --target_dir /path/to/output
# Example:
python3 dropbox_mri_to_bids.py /batch/MRI --target_dir batch/
```

### Input structure

```
    📦/batch/MRI (/path/to/source_dir)
    ┣ 📂MRI_subjid01-session_MMDDYYYY
    ┃ ┣ 📜subjid01-session_MMDDYYYY.Cor_MPRAGE.nii
    ┃ ┣ 📜subjid01-session_MMDDYYYY.T1.nii
    ┃ ┣ 📜(Other files and modalities)
    ┣ 📂MRI_subjid02-session_MMDDYYYY
    ┃ ┣ 📜subjid02-session_MMDDYYYY.Cor_MPRAGE.nii
    ┃ ┣ 📜(Other files and modalities)
```

### Output structure

```
    batch/📦ADRC (/path/to/output)/ADRC
    ┣ 📂subjid01
    ┃ ┣ 📂YYYYMMDD
    ┃ ┃ ┣ 📂anat
    ┃ ┃ ┃ ┗ 📜subjid01-YYYYMMDD_T1w.nii or subjid01-YYYYMMDD_CorMPRAGE.nii (CorMPRAGE is the fallback if T1 don't exist)
    ┃ ┃ ┗ 📂modalities
    ┃ ┃ ┃ ┣ 📜[all original files]
    ┣ 📂subjid02
    ┃ ┣ 📂YYYYMMDD
    ┃ ┃ ┣ 📂anat
    ┃ ┃ ┃ ┗ 📜subjid02-YYYYMMDD_T1w.nii or subjid02-YYYYMMDD_CorMPRAGE.nii
    ┃ ┃ ┗ 📂modalities
    ┃ ┃ ┃ ┣ 📜[all original files]
```

> The `_T1w` scan is preferred; `_CorMPRAGE` is used as a fallback when T1 is absent.

---

## 4. Convert PET to BIDS

**Script:** `dropbox_pet_to_bids.py`

```bash
python3 dropbox_pet_to_bids.py /path/to/source_dir --target_dir /path/to/output
# Example:
python3 dropbox_pet_to_bids.py /batch/PET --target_dir batch/
```

### Input structure

```
/batch/PET/
├── PET_subjid01-session_MMDDYYYY/
│   ├── subjid01-session_MMDDYYYY_mean_5mmblur.nii
│   ├── subjid01-session_MMDDYYYY.Amyloid_PET_CT.nii
│   └── (other files)
└── PET_subjid02-session_MMDDYYYY/
    └── ...
```

### Output structure

```
batch/ADRC/
├── subjid01/
│   └── YYYYMMDD/
│       ├── pet/
│       │   └── subjid01-YYYYMMDD_PET.nii
│       └── ct/
│           └── subjid01-YYYYMMDD_CT.nii
└── subjid02/
    └── ...
```

---

## 5. Sync Data (Excluding Processing Outputs)

Copy data to a new location while skipping `freesurfer` and `suvr` output folders (e.g., when migrating to FS8):

```bash
rsync -av --exclude='*/freesurfer/' --exclude='*/suvr/' /source/directory/ /destination/directory/
```
