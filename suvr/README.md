Scripts to process whole folder.

find /path/to/search -type d -name "suvr" -exec rm -r {} +

Example usage of automate scripts:

```
    python3 prepare_suvr_folder.py /path/to/folder_with_subjects
    python3 registration.py /path/to/folder_with_subjects
    python3 suvr_calculation.py /path/to/folder_with_subjects
```

```
    python3 prepare_suvr_folder.py /mnt/backup/dev/Processing/Both/batch70/ADRC
    python3 registration.py /mnt/backup/dev/Processing/Both/batch70/ADRC
    python3 suvr.py /mnt/backup/dev/Processing/Both/batch70/ADRC
```