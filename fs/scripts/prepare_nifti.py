import re
import shutil
import logging
from pathlib import Path
import argparse
from datetime import datetime

"""
T1 NIfTI Extractor

Scans each subdirectory in a raw MRI/ download folder, identifies the T1w
(or CorMPRAGE fallback) file, and copies it into a flat nifti/ output folder
with a standardized filename.

Folder name format expected: [MRI_]subjID-session_MMDDYYYY  (MRI_ prefix optional)
Output filename format:      subjID-scandate_T1w.nii

Input structure:
    MRI/
    ├── MRI_subjid01-01_01022023/
    │   ├── subjid01-01_01022023.T1.nii
    │   └── ...
    └── MRI_subjid02-01_01022023/
        ├── subjid02-01_01022023.Cor_MPRAGE.nii
        └── ...

Output structure:
    nifti/
    ├── subjid01-20230102_T1w.nii
    └── subjid02-20230102_T1w.nii

Usage:
    python prepare_nifti.py /path/to/MRI [--output /path/to/nifti]
"""


def setup_logging(output_dir: Path) -> logging.Logger:
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"prepare_nifti_{timestamp}.log"

    logger = logging.getLogger("PrepareNifti")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s - %(message)s")

    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def parse_folder_name(folder_name: str, logger: logging.Logger):
    """
    Parse MRI_subjID-session_MMDDYYYY or subjID-session_MMDDYYYY → (subject_id, scandate).
    The MRI_ prefix is optional. Session part is optional.
    Returns None if the folder name does not match.
    """
    # Strip leading MRI_ prefix if present (case-insensitive)
    name = re.sub(r"^MRI_", "", folder_name, flags=re.IGNORECASE)

    pattern = r"(.*?)(?:-([A-Za-z0-9]+))?_(\d{2})(\d{2})(\d{4})$"
    match = re.match(pattern, name)
    if not match:
        logger.warning(f"Skipping — could not parse folder name: {folder_name}")
        return None

    subj_base, _session, month, day, year = match.groups()
    scandate = f"{year}{month}{day}"
    logger.info(f"Parsed '{folder_name}' → subject='{subj_base}', date='{scandate}'")
    return subj_base, scandate


def find_t1_file(folder: Path, logger: logging.Logger):
    """
    Return the best T1 candidate .nii file in *folder*.

    Priority:
      1. Any .nii whose name contains 'T1' (case-insensitive, not 'T1w')
      2. Any .nii whose name contains 'Cor_MPRAGE' / 'CorMPRAGE' (case-insensitive)

    Mirrors the logic used in dropbox_mri_to_bids.py.
    """
    nii_files = list(folder.rglob("*.nii"))
    logger.info(f"  Found {len(nii_files)} .nii file(s) in {folder.name}")

    t1_candidates = []
    mprage_candidates = []

    for f in nii_files:
        # Extract the modality portion: filename format is base.Modality.nii
        modality_match = re.search(r"\.([^.]+)\.nii$", f.name, re.IGNORECASE)
        if modality_match:
            modality = modality_match.group(1).lower()
        else:
            modality = f.stem.lower()

        if modality == "t1":
            t1_candidates.append(f)
        elif modality in ("cor_mprage", "cormprage"):
            mprage_candidates.append(f)

    if t1_candidates:
        chosen = t1_candidates[0]
        logger.info(f"  Selected T1 file: {chosen.name}")
        return chosen, "T1w"

    if mprage_candidates:
        chosen = mprage_candidates[0]
        logger.info(f"  No T1 found; using CorMPRAGE fallback: {chosen.name}")
        return chosen, "T1w"

    logger.warning(f"  No T1 or CorMPRAGE file found in {folder.name}")
    return None, None


def process_mri_folder(
    source_dir: Path,
    output_dir: Path,
    logger: logging.Logger,
) -> dict:
    """
    Iterate over all MRI_* subfolders in *source_dir*, extract the T1 file
    from each, and write it to *output_dir* as subjID-scandate_T1w.nii.

    Returns a summary dict with counts.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    mri_folders = sorted(f for f in source_dir.iterdir() if f.is_dir())

    if not mri_folders:
        logger.warning(f"No subfolders found in {source_dir}")
        return {"found": 0, "copied": 0, "skipped": 0}

    logger.info(f"Found {len(mri_folders)} MRI_* folder(s) in {source_dir}")

    copied = skipped = 0

    for folder in mri_folders:
        logger.info(f"Processing: {folder.name}")

        parsed = parse_folder_name(folder.name, logger)
        if parsed is None:
            skipped += 1
            continue

        subject_id, scandate = parsed

        t1_file, modality_label = find_t1_file(folder, logger)
        if t1_file is None:
            skipped += 1
            continue

        dest_name = f"{subject_id}-{scandate}_T1w.nii"
        dest_path = output_dir / dest_name

        if dest_path.exists():
            logger.warning(f"  Output already exists, skipping: {dest_name}")
            skipped += 1
            continue

        try:
            shutil.copy2(t1_file, dest_path)
            logger.info(f"  COPIED → {dest_name}")
            copied += 1
        except Exception as e:
            logger.error(f"  Failed to copy {t1_file}: {e}")
            skipped += 1

    return {"found": len(mri_folders), "copied": copied, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(
        description="Extract T1 NIfTI files from raw MRI_* download folders into a flat nifti/ directory."
    )
    parser.add_argument(
        "source_dir",
        help="Path to the MRI/ folder containing MRI_subjID-session_MMDDYYYY subfolders.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for nifti files (default: nifti/ sibling to source_dir).",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()

    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        output_dir = source_dir.parent / "nifti"

    logger = setup_logging(output_dir)

    logger.info("=" * 70)
    logger.info(f"Source : {source_dir}")
    logger.info(f"Output : {output_dir}")
    logger.info("=" * 70)

    summary = process_mri_folder(source_dir, output_dir, logger)

    logger.info("=" * 70)
    logger.info(f"Folders found : {summary['found']}")
    logger.info(f"Files copied  : {summary['copied']}")
    logger.info(f"Skipped       : {summary['skipped']}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
