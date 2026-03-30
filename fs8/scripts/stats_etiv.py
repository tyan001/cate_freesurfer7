"""
FreeSurfer statistics extraction and CSV conversion pipeline.

Runs FreeSurfer table-extraction tools (asegstats2table, aparcstats2table,
ConcatenateSubregionsResults.sh) against a SUBJECTS_DIR, then converts the
resulting .stats tables to CSV files.  Lateralized concat outputs
(hipposubfields, amygdalar-nuclei) are merged into a single CSV with lh_/rh_
column prefixes.
"""
import argparse
import subprocess
import pandas as pd
from pathlib import Path
import os


def run_freesurfer_stats(subjects_dir, subjects, table_dir):
    """Run FreeSurfer stat-extraction commands and write .stats tables to table_dir."""
    print("Extracting statistics...")

    commands = [
        f"asegstats2table --subjects {' '.join(subjects)} --meas volume --etiv --skip --statsfile wmparc.stats --all-segs --tablefile {table_dir}/wmparc_stats.stats",
        f"asegstats2table --subjects {' '.join(subjects)} --meas volume --etiv --skip --tablefile {table_dir}/aseg_stats.stats",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi lh --meas volume --etiv --skip --tablefile {table_dir}/aparc_volume_lh.stats",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi lh --meas thickness --etiv --skip --tablefile {table_dir}/aparc_thickness_lh.stats",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi rh --meas volume --etiv --skip --tablefile {table_dir}/aparc_volume_rh.stats",
        f"aparcstats2table --subjects {' '.join(subjects)} --hemi rh --meas thickness --etiv --skip --tablefile {table_dir}/aparc_thickness_rh.stats",
        f"ConcatenateSubregionsResults.sh  -f hipposubfields.lh.T1.v22.stats -f hipposubfields.rh.T1.v22.stats -f amygdalar-nuclei.lh.T1.v22.stats -f amygdalar-nuclei.rh.T1.v22.stats -s {subjects_dir} -o {table_dir}",
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, cwd=subjects_dir)


def merge_lateralized_concat(table_dir: Path, csv_dir: Path, name: str):
    """Merge lh/rh _concat.stats files into one CSV with lh_/rh_ column prefixes.

    Reads ``<name>.lh.T1.v22_concat.stats`` and ``<name>.rh.T1.v22_concat.stats``
    from table_dir, prefixes every column except the first (subject ID) with
    ``lh_`` or ``rh_``, merges on the subject ID column, and writes the result
    to ``<csv_dir>/<name>.csv``.
    
    As of when this was written for freesurfer 8.2.0, the subregions outputs for hipposubfields and amygdalar-nuclei 
    using segmentHA_T1.sh where name as follows:
    - hipposubfields.lh.T1.v22.stats
    - hipposubfields.rh.T1.v22.stats
    - amygdalar-nuclei.lh.T1.v22.stats
    - amygdalar-nuclei.rh.T1.v22.stats
    
    """
    lh_file = table_dir / f"{name}.lh.T1.v22_concat.stats"
    rh_file = table_dir / f"{name}.rh.T1.v22_concat.stats"

    if not lh_file.exists() or not rh_file.exists():
        print(f"Skipping {name} merge: missing lh or rh concat file in {table_dir}")
        return

    lh_df = pd.read_table(lh_file, delimiter=' ')
    rh_df = pd.read_table(rh_file, delimiter=' ')

    subj_col = str(lh_df.columns[0])

    lh_df = lh_df.rename(columns={c: f"lh_{c}" for c in lh_df.columns[1:]})
    rh_df = rh_df.rename(columns={c: f"rh_{c}" for c in rh_df.columns[1:]})

    merged = pd.merge(lh_df, rh_df, left_on=subj_col, right_on=rh_df.columns[0])
    merged = merged.sort_values(by=subj_col)

    out_file = csv_dir / f"{name}.csv"
    merged.to_csv(out_file, index=False)
    print(f'CREATED: {out_file.name} in ./csv/')


def convert_table_to_csv(table_file: Path, output_dir: Path):
    """Convert a tab-delimited .stats table to a sorted CSV file in output_dir."""
    df = pd.read_table(table_file, delimiter='\t')
    df = df.sort_values(by=df.columns[0]) # type: ignore
    csv_file = output_dir / f"{table_file.stem}.csv"
    df.to_csv(csv_file, index=False)
    print(f'CREATED: {csv_file.name} in ./csv/')
    

def main():
    """Entry point: parse arguments, run extraction, and produce CSV outputs."""
    # python3 stats.py -sd fsout/
    parser = argparse.ArgumentParser(description="Process FreeSurfer stats and convert to CSV.")
    parser.add_argument('-sd', '--subjects-dir', type=str, required=True, help='Path to SUBJECTS_DIR containing subject folders')
    args = parser.parse_args()
    
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

    # Create 'stats' folder in current working directory
    stats_dir = Path.cwd() / "stats_etiv"
    table_dir = stats_dir / "tables"
    csv_dir = stats_dir / "csv"

    # Make output folders
    stats_dir.mkdir(exist_ok=True)
    table_dir.mkdir(exist_ok=True)
    csv_dir.mkdir(exist_ok=True)
    
    # Run stats extraction
    run_freesurfer_stats(subjects_dir, subjects, table_dir)

    for table_file in table_dir.glob("*.stats"):
        if not table_file.name.endswith("_concat.stats"): # skipping the hipposubfields and amygdalar-nuclei concat files since they are merged separately
            convert_table_to_csv(table_file, csv_dir)
        
    # Merge lateralized concat outputs into single CSVs with lh_/rh_ prefixes
    merge_lateralized_concat(table_dir, csv_dir, "hipposubfields")
    merge_lateralized_concat(table_dir, csv_dir, "amygdalar-nuclei")
    print('---------------------------------------')

    print("CSV files created:", [f.name for f in csv_dir.glob("*.csv")])
    print('DONE.')

if __name__ == "__main__":
    main()