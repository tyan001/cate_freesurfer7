import argparse
import subprocess
import pandas as pd
from pathlib import Path
import os
import shutil

def run_freesurfer_stats(subjects_dir, subjects):
    print("Extracting statistics...")

    commands = [
        f"asegstats2table --subjects {' '.join(subjects)} --meas volume --skip --statsfile wmparc.stats --all-segs --tablefile wmparc_stats.txt",
        f"asegstats2table --subjects {' '.join(subjects)} --meas volume --skip --tablefile aseg_stats.txt",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi lh --meas volume --skip --tablefile aparc_volume_lh.txt",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi lh --meas thickness --skip --tablefile aparc_thickness_lh.txt",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi rh --meas volume --skip --tablefile aparc_volume_rh.txt",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi rh --meas thickness --skip --tablefile aparc_thickness_rh.txt",
        f"ConcatenateSubregionsResults.sh  -f hipposubfields.lh.T1.v22.stats -f hipposubfields.rh.T1.v22.stats -f amygdalar-nuclei.lh.T1.v22.stats -f amygdalar-nuclei.rh.T1.v22.stats -s {subjects_dir} -o .",
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, cwd=subjects_dir)

def replace_slash(file_path: Path, output_path: Path):
    data = file_path.read_text()
    data = data.replace(".nii", "").replace("/", "").replace(" ", "\t")
    new_file = output_path / (file_path.stem + "_new.txt")
    new_file.write_text(data)
    print(f'CREATED: {new_file.name}')
    return new_file

def convert_txt_to_csv(txt_file: Path, output_dir: Path):
    df = pd.read_csv(txt_file, delimiter='\t')
    csv_file = output_dir / (txt_file.stem.replace("_new", "") + ".csv")
    df.to_csv(csv_file, index=False)
    print(f'CREATED: {csv_file.name} in ./csv/')

def main():
    parser = argparse.ArgumentParser(description="Process FreeSurfer stats and convert to CSV.")
    parser.add_argument('-sd', '--subjects-dir', type=str, required=True, help='Path to SUBJECTS_DIR containing subject folders')
    args = parser.parse_args()

    # python3 stats.py -sd fsout/
    
    # Inside main()
    subjects_dir = Path(args.subjects_dir).resolve()

    # Set environment variable
    os.environ["SUBJECTS_DIR"] = str(subjects_dir)

    if not subjects_dir.exists() or not subjects_dir.is_dir():
        print("Invalid subjects directory.")
        return

    # Get subject folder names
    subjects = [p.name for p in subjects_dir.iterdir() if p.is_dir()]
    if not subjects:
        print("No subject folders found.")
        return

    # Run stats extraction
    run_freesurfer_stats(subjects_dir, subjects)

    # Create 'stats' folder in current working directory
    stats_dir = Path.cwd() / "stats"
    txt_dir = stats_dir / "txt"
    csv_dir = stats_dir / "csv"

    # Make output folders
    stats_dir.mkdir(exist_ok=True)
    txt_dir.mkdir(exist_ok=True)
    csv_dir.mkdir(exist_ok=True)

    # Move *.txt to txt/ directory
    for txt_file in list(subjects_dir.glob("*.txt")) + list(Path.cwd().glob("*.txt")):
        shutil.move(str(txt_file), str(txt_dir / txt_file.name))

    # Clean .txt files
    new_txt_files = []
    for txt_file in txt_dir.glob("*.txt"):
        if not txt_file.name.endswith("_new.txt"):
            new_txt = replace_slash(txt_file, txt_dir)
            new_txt_files.append(new_txt)
            txt_file.unlink()

    print('---------------------------------------')

    # Convert to CSV
    for new_txt_file in new_txt_files:
        convert_txt_to_csv(new_txt_file, csv_dir)

    print('---------------------------------------')
    print("CSV files created:", [f.name for f in csv_dir.glob("*.csv")])
    print('DONE.')

if __name__ == "__main__":
    main()