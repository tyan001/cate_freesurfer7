# CATE FS7 Prepping Scripts
---------------------------------------------------------------------------------------------------------------------

Use to download the zip file from dropbox
```
    curl -L -o folder_name.zip "Url-link"
```
----------------------------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------------------------

Use to unzip all zip files

```
    ./unzip_files.sh path/to/directory_with_zip_files
```

----------------------------------------------------------------------------------------------------------------------

## Prepping NWSI data for BIDS format

These scripts is to convert the UF data structure for grant number starting at 320 to BIDS format.
example of UF data structure:
MRI_320000-session_MMDDYYYY
PET_320000-session_MMDDYYYY

Use the prefix.py to add the prefix to the subject id
```
    python3 prefix.py /path/to/folder_with_subjects --prefix MRI_
    python3 prefix.py /path/to/folder_with_subjects --prefix PET_
```

```

```
# UF data structure for MRI scans
📦/batch/MRI (/path/to/source_dir)
 ┣ 📂MRI_subjid01-session_MMDDYYYY
 ┃ ┣ 📜subjid01-session_MMDDYYYY.Cor_MPRAGE.nii
 ┃ ┣ 📜subjid01-session_MMDDYYYY.T1.nii
 ┃ ┣ 📜(Other files and modalities)
 ┣ 📂MRI_subjid02-session_MMDDYYYY
 ┃ ┣ 📜subjid02-session_MMDDYYYY.Cor_MPRAGE.nii
 ┃ ┣ 📜subjid02-session_MMDDYYYY.T1.nii
 ┃ ┣ 📜(Other files and modalities)

# UF data structure for PET scans

📦/batch/PET (/path/to/source_dir)
 ┣ 📂PET_subjid01-session_MMDDYYYY
 ┃ ┣ 📜subjid01-session_MMDDYYYY_mean_5mmblur.nii
 ┃ ┣ 📜subjid01-session_MMDDYYYY.Amyloid_PET_CT.nii
 ┃ ┣ 📜(Other files)
 ┣ 📂PET_subjid02-session_MMDDYYYY
 ┃ ┣ 📜subjid02-session_MMDDYYYY_mean_5mmblur.nii
 ┃ ┣ 📜subjid02-session_MMDDYYYY.Amyloid_PET_CT.nii
 ┃ ┣ 📜(Other files)


### BIDS from dropbox

Usage:
    python script_name.py /path/to/source_dir --target_dir /path/to/output
    example: python3 dropbox_mri_to_bids.py /batch/MRI --target_dir batch/

Input files structure:

📦/batch/MRI (/path/to/source_dir)
 ┣ 📂MRI_subjid01-session_MMDDYYYY
 ┃ ┣ 📜subjid01-session_MMDDYYYY.Cor_MPRAGE.nii
 ┃ ┣ 📜subjid01-session_MMDDYYYY.T1.nii
 ┃ ┣ 📜(Other files and modalities)
 ┣ 📂MRI_subjid02-session_MMDDYYYY
 ┃ ┣ 📜subjid02-session_MMDDYYYY.Cor_MPRAGE.nii
 ┃ ┣ 📜subjid02-session_MMDDYYYY.T1.nii
 ┃ ┣ 📜(Other files and modalities)

Each subject's data will be organized as:

batch/📦ADRC (/path/to/output)/ADRC
┣ 📂subjid01
┃ ┣ 📂YYYYMMDD
┃ ┃ ┣ 📂anat
┃ ┃ ┃ ┗ 📜subjid01-YYYYMMDD_T1w.nii or subjid01-YYYYMMDD_CorMPRAGE.nii (CorMPRAGE is the fallback if T1 don't exist)
┃ ┃ ┗ 📂modalities
┃ ┃ ┃ ┣ 📜[all original files]
┃ ┃ ┗ 📂freesurfer741
┃ ┃ ┃ ┗📂subjid01-YYYYMMDD_T1w
┃ ┃ ┃ ┗📂subjid01-YYYYMMDD_CorMPRAGE
┣ 📂subjid02
┃ ┣ 📂YYYYMMDD
┃ ┃ ┣ 📂anat
┃ ┃ ┃ ┗ 📜subjid02-YYYYMMDD_T1w.nii or subjid02-YYYYMMDD_CorMPRAGE.nii
┃ ┃ ┗ 📂modalities
┃ ┃ ┃ ┣ 📜[all original files]


Usage:
    python script_name.py /path/to/source_dir --target_dir /path/to/output
    example: python3 dropbox_pet_to_bids.py /batch/PET --target_dir batch/
Input files structure:

📦/batch/PET (/path/to/source_dir)
 ┣ 📂PET_subjid01-session_MMDDYYYY
 ┃ ┣ 📜subjid01-session_MMDDYYYY_mean_5mmblur.nii
 ┃ ┣ 📜subjid01-session_MMDDYYYY.Amyloid_PET_CT.nii
 ┃ ┣ 📜(Other files)
 ┣ 📂PET_subjid02-session_MMDDYYYY
 ┃ ┣ 📜subjid02-session_MMDDYYYY_mean_5mmblur.nii
 ┃ ┣ 📜subjid02-session_MMDDYYYY.Amyloid_PET_CT.nii
 ┃ ┣ 📜(Other files)

Each subject's data will be organized as:

batch/📦ADRC (/path/to/output)
┣ 📂subjid01
┃ ┣ 📂YYYYMMDD
┃ ┃ ┣ 📂pet
┃ ┃ ┃ ┗ 📜subjid01-YYYYMMDD_PET.nii
┃ ┃ ┣ 📂ct
┃ ┃ ┃ ┗ 📜subjid01-YYYYMMDD_CT.nii
┣ 📂subjid02
┃ ┣ 📂YYYYMMDD
┃ ┃ ┣ 📂pet
┃ ┃ ┃ ┗ 📜subjid02-YYYYMMDD_PET.nii
┃ ┃ ┣ 📂ct
┃ ┃ ┃ ┗ 📜subjid02-YYYYMMDD_CT.nii

Copies all files from source to destination, excluding freesurfer and suvr folders. For the future for when moving to FS8
```
    rsync -av --exclude='*/freesurfer/' --exclude='*/suvr/' /source/directory/ /destination/directory/
```

----------------------------------------------------------------------------------------------------------------------