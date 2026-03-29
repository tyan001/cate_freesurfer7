import logging
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prepare_nifti import parse_folder_name, find_t1_file

logger = logging.getLogger("test")


# ---------------------------------------------------------------------------
# parse_folder_name
# Real folder name patterns observed in batch81/MRI/:
#   MRI_120600_08122025       → no session
#   MRI_220242-01_08142024    → numeric session
#   MRI_320095-C2_01122026    → alphanumeric session
#   MRI_320103-D1_12042025    → alphanumeric session
#   120573-01_07172024        → no MRI_ prefix, numeric session
#   120605_06092025           → no MRI_ prefix, no session
# ---------------------------------------------------------------------------

class TestParseFolderName:
    # --- with MRI_ prefix ---

    def test_mri_prefix_no_session(self):
        result = parse_folder_name("MRI_777001_08122025", logger)
        assert result == ("777001", "20250812")

    def test_mri_prefix_numeric_session(self):
        result = parse_folder_name("MRI_888002-01_08142024", logger)
        assert result == ("888002", "20240814")

    def test_mri_prefix_alphanumeric_session_c2(self):
        result = parse_folder_name("MRI_999003-C2_01122026", logger)
        assert result == ("999003", "20260112")

    def test_mri_prefix_alphanumeric_session_d1(self):
        result = parse_folder_name("MRI_777004-D1_12042025", logger)
        assert result == ("777004", "20251204")

    # --- without MRI_ prefix ---

    def test_no_prefix_with_session(self):
        result = parse_folder_name("888005-01_07172024", logger)
        assert result == ("888005", "20240717")

    def test_no_prefix_no_session(self):
        result = parse_folder_name("999006_06092025", logger)
        assert result == ("999006", "20250609")

    # --- MRI_ prefix is case-insensitive ---

    def test_mri_prefix_lowercase(self):
        result = parse_folder_name("mri_777001_08122025", logger)
        assert result == ("777001", "20250812")

    # --- date edge cases ---

    def test_date_end_of_year(self):
        result = parse_folder_name("MRI_777007_12312022", logger)
        assert result == ("777007", "20221231")

    # --- invalid / unrecognised folders ---

    def test_invalid_no_date(self):
        result = parse_folder_name("MRI_777007_nodatehere", logger)
        assert result is None

    def test_invalid_empty_string(self):
        result = parse_folder_name("", logger)
        assert result is None

    def test_invalid_logs_folder(self):
        result = parse_folder_name("logs", logger)
        assert result is None


# ---------------------------------------------------------------------------
# find_t1_file
# Real file pattern: subjectid_scandate.T1.nii
# e.g. 120600_08122025.T1.nii, 120573-01_07172024.T1.nii
# ---------------------------------------------------------------------------

class TestFindT1File:
    def test_finds_t1_among_multiple_modalities(self, tmp_path):
        for modality in ["DTI1000", "HighResHippocampus", "SWI", "SWIa", "T2", "T2GRE", "T1"]:
            (tmp_path / f"777001_01012000.{modality}.nii").touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen.name == "777001_01012000.T1.nii"
        assert label == "T1w"

    def test_finds_t1_with_session_in_filename(self, tmp_path):
        (tmp_path / "888002-01_01012000.T1.nii").touch()
        (tmp_path / "888002-01_01012000.T2FLAIR.nii").touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen.name == "888002-01_01012000.T1.nii"
        assert label == "T1w"

    def test_t1_takes_priority_over_cormprage(self, tmp_path):
        (tmp_path / "999003_01012000.T1.nii").touch()
        (tmp_path / "999003_01012000.Cor_MPRAGE.nii").touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen.name == "999003_01012000.T1.nii"

    def test_cormprage_fallback_when_no_t1(self, tmp_path):
        (tmp_path / "777004_01012000.Cor_MPRAGE.nii").touch()
        (tmp_path / "777004_01012000.DTI1000.nii").touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen.name == "777004_01012000.Cor_MPRAGE.nii"
        assert label == "T1w"

    def test_no_structural_file_returns_none(self, tmp_path):
        for name in ["888005_01012000.DTI1000.nii", "888005_01012000.SWI.nii", "888005_01012000.T2.nii"]:
            (tmp_path / name).touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen is None
        assert label is None

    def test_empty_folder_returns_none(self, tmp_path):
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen is None

    def test_finds_nii_in_subdirectory(self, tmp_path):
        subdir = tmp_path / "dicom"
        subdir.mkdir()
        (subdir / "999006_01012000.T1.nii").touch()
        chosen, label = find_t1_file(tmp_path, logger)
        assert chosen is not None
        assert chosen.name == "999006_01012000.T1.nii"
