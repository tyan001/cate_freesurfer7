"""
Run hippocampal subregion segmentation on existing FreeSurfer outputs.

Usage:
    nohup python3 segment_hippo.py /path/to/fsout > hippo.log 2>&1 &

Every subdirectory in fsout (except fsaverage) is treated as a subject.
"""

import argparse
import logging
import multiprocessing as mp
import os
import socket
import time
from functools import partial
from pathlib import Path


def setup_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("segment_hippo")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    for handler in (logging.FileHandler(log_file), logging.StreamHandler()):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


def find_subjects(fsout: Path) -> list[Path]:
    """Return subject directories with completed recon-all runs."""
    skip = {"fsaverage"}
    return [
        p for p in sorted(fsout.iterdir())
        if p.is_dir() and p.name not in skip and (p / "mri" / "aparc+aseg.mgz").exists()
    ]


def process_subject(subject_dir: Path, fsout: Path, logger: logging.Logger) -> dict:
    subject = subject_dir.name
    logger.info(f"[{subject}] Starting segmentHA_T1.sh")

    start = time.time()
    cmd = f"segmentHA_T1.sh {subject} {fsout}"
    rc = os.system(cmd)
    elapsed = time.time() - start

    success = rc == 0
    if success:
        logger.info(f"[{subject}] Completed in {elapsed:.1f}s")
    else:
        logger.error(f"[{subject}] Failed (exit {rc}) after {elapsed:.1f}s")

    return {"subject": subject, "success": success, "time": elapsed}


def main():
    parser = argparse.ArgumentParser(description="Run hippocampal subregion segmentation.")
    parser.add_argument("fsout", type=str, help="Path to fsout directory containing subject folders.")
    parser.add_argument("--cores", type=int, default=None, help="Number of parallel workers (default: CPU_CORES env or 1).")
    args = parser.parse_args()

    fsout = Path(args.fsout)

    if not fsout.exists():
        raise SystemExit(f"Error: {fsout} not found. Run recon_all.py first.")

    cores = args.cores or int(os.getenv("CPU_CORES", 1))
    container = os.getenv("CONTAINER_NAME", socket.gethostname())

    log_file = fsout.parent / "fs_logs" / f"segment_hippo_{container}.log"
    logger = setup_logger(log_file)

    subjects = find_subjects(fsout)
    logger.info(f"Found {len(subjects)} subjects in {fsout}, processing with {cores} workers")

    if not subjects:
        logger.warning("No subjects found. Nothing to do.")
        return

    func = partial(process_subject, fsout=fsout, logger=logger)
    with mp.Pool(processes=cores) as pool:
        results = pool.map(func, subjects)

    # Summary
    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    logger.info("=== SUMMARY ===")
    logger.info(f"Total: {len(results)} | Succeeded: {len(succeeded)} | Failed: {len(failed)}")
    if failed:
        logger.info(f"Failed subjects: {', '.join(r['subject'] for r in failed)}")
    if succeeded:
        times = [r["time"] for r in succeeded]
        logger.info(f"Avg time: {sum(times)/len(times):.1f}s | Total time: {sum(times):.1f}s")
    logger.info("=== DONE ===")


if __name__ == "__main__":
    main()
