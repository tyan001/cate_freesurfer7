import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mri_processing import find_nii_paths


# ---------------------------------------------------------------------------
# find_nii_paths
# Expects a flat nifti/ directory produced by prepare_nifti.py.
# Real output filenames: subjectID-YYYYMMDD_T1w.nii
# e.g. 120600-20250812_T1w.nii, 120573-20240717_T1w.nii
# ---------------------------------------------------------------------------

class TestFindNiiPaths:
    def test_finds_nii_files(self, tmp_path):
        (tmp_path / "777001-20000101_T1w.nii").touch()
        (tmp_path / "888002-20000202_T1w.nii").touch()
        result = find_nii_paths(tmp_path)
        assert len(result) == 2

    def test_ignores_non_nii_files(self, tmp_path):
        (tmp_path / "777001-20000101_T1w.nii").touch()
        (tmp_path / "notes.txt").touch()
        (tmp_path / "777001-20000101_T1w.nii.gz").touch()
        result = find_nii_paths(tmp_path)
        assert len(result) == 1
        assert result[0].suffix == ".nii"

    def test_ignores_nii_in_subdirectories(self, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "777001-20000101_T1w.nii").touch()
        result = find_nii_paths(tmp_path)
        assert len(result) == 0

    def test_empty_directory(self, tmp_path):
        result = find_nii_paths(tmp_path)
        assert result == []

    def test_returns_sorted_paths(self, tmp_path):
        for name in ["999003-20000303_T1w.nii", "777001-20000101_T1w.nii", "888002-20000202_T1w.nii"]:
            (tmp_path / name).touch()
        result = find_nii_paths(tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)

    def test_returns_path_objects(self, tmp_path):
        (tmp_path / "777001-20000101_T1w.nii").touch()
        result = find_nii_paths(tmp_path)
        assert all(isinstance(p, Path) for p in result)
