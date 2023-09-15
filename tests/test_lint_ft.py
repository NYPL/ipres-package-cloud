from pathlib import Path

import pytest

import ipres_package_cloud.lint_ft as lint_ft

# Unit tests
# Argument tests
def test_package_argument(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "sys.argv",
        ["script", "--package", str(tmp_path)],
    )

    args = lint_ft.parse_args()

    assert tmp_path in args.packages


def test_directory_argument(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    child_dir = tmp_path / "child"
    child_dir.mkdir()

    monkeypatch.setattr(
        "sys.argv",
        ["script", "--directory", str(tmp_path)],
    )

    args = lint_ft.parse_args()

    assert child_dir in args.packages

# linting tests
@pytest.fixture
def good_package(tmp_path: Path):
    pkg = tmp_path.joinpath("ACQ_1234_123456")
    f_object_data = pkg / "objects" / "data"
    f_object_data.mkdir(parents=True)

    bag_files = ["bag-info.txt", "bagit.txt", "manifest-md5.txt", "tagmanifest-md5.txt"]
    for f in bag_files:
        filepath = pkg / "objects" / f
        filepath.touch()
        filepath.write_bytes(b"some bytes for file")

    obj_data_file = f_object_data / "file_1.txt"
    obj_data_file.touch()
    obj_data_file.write_bytes(b"some bytes for file")

    obj_data_folder = f_object_data / "folder1"
    obj_data_folder.mkdir(parents=True, exist_ok=True)

    obj_data_folder_file = obj_data_folder / "fileinfolder.txt"
    obj_data_folder_file.touch()
    obj_data_folder_file.write_bytes(b"some bytes for file")

    f_metadata = pkg.joinpath("metadata")
    f_metadata.mkdir()

    metadata_filepath = f_metadata.joinpath("rclone.log")
    metadata_filepath.touch()
    metadata_filepath.write_bytes(b"some bytes for metadata")

    return pkg


