"""
Check recon-all output completeness for all subjects in an fsout directory.

Usage:
    python3 check_outputs.py data/ADRC/nifti/fsout/
"""

import argparse
from pathlib import Path


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


def check_subject(subject_dir: Path) -> list[str]:
    return [f for f in REQUIRED_FILES if not (subject_dir / f).exists()]


def main():
    parser = argparse.ArgumentParser(description="Check recon-all outputs for all subjects.")
    parser.add_argument("fsout", type=str, help="Path to fsout directory.")
    args = parser.parse_args()

    fsout = Path(args.fsout)
    subject_dirs = sorted([d for d in fsout.iterdir() if d.is_dir()])

    if not subject_dirs:
        print(f"No subject directories found in {fsout}")
        return

    complete, incomplete = [], []

    for subject_dir in subject_dirs:
        missing = check_subject(subject_dir)
        if missing:
            incomplete.append((subject_dir.name, missing))
        else:
            complete.append(subject_dir.name)

    print(f"=== RESULTS: {len(complete)} complete, {len(incomplete)} incomplete ===")
    if incomplete:
        print("\nINCOMPLETE:")
        for subject, missing in incomplete:
            print(f"  {subject}")
            for f in missing:
                print(f"    missing: {f}")
    if complete:
        print(f"\nCOMPLETE ({len(complete)}):")
        for subject in complete:
            print(f"  {subject}")


if __name__ == "__main__":
    main()
