"""
Run FreeSurfer recon-all on all .nii files in a directory.

Usage:
    nohup python3 recon_all.py data/ADRC/nifti/ > recon.log 2>&1 &

Output goes to <nifti_dir>/fsout/<subject_id>/
"""

import argparse
import logging
import multiprocessing as mp
import os
import socket
import time
from functools import partial
from pathlib import Path


# Critical files that must exist after a successful recon-all run.
# If any are missing, the run is considered failed regardless of exit code.
REQUIRED_FILES = [
    "mri/aparc+aseg.mgz",
    "surf/lh.white",
    "surf/rh.white",
    "surf/lh.pial",
    "surf/rh.pial",
    "surf/lh.thickness",
    "surf/rh.thickness",
    "stats/aseg.stats",
]


def setup_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("recon_all")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for handler in (logging.FileHandler(log_file), logging.StreamHandler()):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


def validate_outputs(subject_dir: Path) -> list[str]:
    """Check that all critical recon-all output files exist.

    Returns a list of missing files (empty if everything looks good).
    """
    missing = []
    for rel_path in REQUIRED_FILES:
        if not (subject_dir / rel_path).exists():
            missing.append(rel_path)
    return missing


def process_subject(nii_path: Path, fsout: Path, logger: logging.Logger) -> dict:
    subject = nii_path.stem
    subject_dir = fsout / subject
    logger.info(f"[{subject}] Starting recon-all")

    start = time.time()
    cmd = f"recon-all -i {nii_path} -subjid {subject} -sd {fsout} -all"
    rc = os.system(cmd)
    elapsed = time.time() - start

    # FS8 may not create recon-all.done/error, so validate by checking
    # that all critical output files were actually produced.
    missing = validate_outputs(subject_dir)

    if rc != 0:
        logger.error(f"[{subject}] recon-all exited with code {rc} after {elapsed:.1f}s")
    if missing:
        logger.error(f"[{subject}] Missing output files: {', '.join(missing)}")

    success = rc == 0 and len(missing) == 0

    if success:
        logger.info(f"[{subject}] Completed successfully in {elapsed:.1f}s")
    elif rc == 256:
        logger.warning(f"[{subject}] Completed successfully in {elapsed:.1f}s with return code {rc}")
    else:
        logger.error(f"[{subject}] FAILED after {elapsed:.1f}s")

    return {"subject": subject, "success": success, "time": elapsed, "missing": missing}


def main():
    parser = argparse.ArgumentParser(description="Run recon-all on .nii files.")
    parser.add_argument("directory", type=str, help="Path to directory containing .nii files.")
    parser.add_argument("--cores", type=int, default=None, help="Number of parallel workers (default: CPU_CORES env or 1).")
    args = parser.parse_args()

    nifti_dir = Path(args.directory)
    fsout = nifti_dir / "fsout"
    fsout.mkdir(exist_ok=True)

    cores = args.cores or int(os.getenv("CPU_CORES", 1))
    container = os.getenv("CONTAINER_NAME", socket.gethostname())

    log_file = nifti_dir / "fs_logs" / f"recon_all_{container}.log"
    logger = setup_logger(log_file)

    nii_paths = sorted(nifti_dir.glob("*.nii"))
    logger.info(f"Found {len(nii_paths)} .nii files, processing with {cores} workers")

    func = partial(process_subject, fsout=fsout, logger=logger)
    with mp.Pool(processes=cores) as pool:
        results = pool.map(func, nii_paths)

    # Summary
    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    logger.info("=== SUMMARY ===")
    logger.info(f"Total: {len(results)} | Succeeded: {len(succeeded)} | Failed: {len(failed)}")
    if failed:
        for r in failed:
            detail = f"  {r['subject']}"
            if r["missing"]:
                detail += f" (missing: {', '.join(r['missing'])})"
            logger.info(detail)
    if succeeded:
        times = [r["time"] for r in succeeded]
        logger.info(f"Avg time: {sum(times)/len(times):.1f}s | Total time: {sum(times):.1f}s")
    logger.info("=== DONE ===")


if __name__ == "__main__":
    main()
