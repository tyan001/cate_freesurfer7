Notes on how to use the freesurfer scripts

license.txt has to be located where the create_config script is located.
python3 scripts/freesurfer/processing_container.py Processing/Both/batch81

---

mri_processing.py: Script to process MRI data using FreeSurfer. Is going to look for all anat directory and get the mri in there. to run the FS7 recon-all and hippocampus.

This is also how the data should be structured:
📦ADRC <- Can be any name but is the input I used
┣ 📂110000 <--- Fake subject
┃ ┗ 📂20181111
┃ ┃ ┣ 📂anat
┃ ┃ ┃ ┗ 📜110000-20181111_T1w.nii
┣ 📂110011 <--- Fake subject
┃ ┗ 📂20180101
┃ ┃ ┣ 📂anat
┃ ┃ ┃ ┗ 📜110011-20180101_T1w.nii

command I used to run the script. run it in the background and save the output to a file
nohup python3 mri_processing.py data/ADRC/ > processing.log 2>&1 &

---
