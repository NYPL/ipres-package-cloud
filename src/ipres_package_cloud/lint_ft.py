import argparse
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

LOGGER = logging.getLogger(__name__)

def _configure_logging(log_folder: Path):
    log_fn = datetime.now().strftime("lint_%Y_%m_%d_%H_%M.log")
    log_fpath = log_folder / log_fn
    if not log_fpath.is_file():
        log_fpath.touch()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_fpath,
        encoding="utf-8",
    )

def parse_args() -> argparse.Namespace:
    """Validate and return command-line args"""

    def extant_dir(p):
        path = Path(p)
        if not path.is_dir():
            raise argparse.ArgumentTypeError(
                f'{path} does not exist'
            )
        return path

    def list_of_paths(p):
        path = extant_dir(p)
        child_dirs = []
        for child in path.iterdir():
            if child.is_dir():
                child_dirs.append(child)
        return child_dirs

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--package',
        type=extant_dir,
        nargs='+',
        dest='packages',
        action='extend'
    )
    parser.add_argument(
        '--directory',
        type=list_of_paths,
        dest='packages',
        action='extend'
    )
    parser.add_argument(
        '--log_folder',
        help='''Optional. Designate where to save the log file,
        or it will be saved in current directory''',
        default='.'
    )


    return parser.parse_args()

def package_has_valid_name(package: Path) -> bool:
    """Top level folder name has to conform to ACQ_####_######"""
    folder_name = package.name
    match = re.fullmatch(r"ACQ_[0-9]{4}_[0-9]{6}", folder_name)

    if match:
        return True
    else:
        LOGGER.error(f"{folder_name} does not conform to ACQ_####_######")
        return False

def package_has_two_subfolders(package: Path) -> bool:
    """There must be two subfolders in the package"""
    pkg_folders = [ x for x in package.iterdir() if x.is_dir() ]
    if len(pkg_folders) == 2:
        return True
    else:
        LOGGER.error(f"{package} does not have exactly two subfolders")
        return False

def package_has_valid_subfolder_names(package: Path) -> bool:
    """Second level folders must be objects and metadata folder"""
    expected = set(["objects", "metadata"])
    found = set([x.name for x in package.iterdir()])

    if expected == found:
        return True
    else:
        LOGGER.error(
            f"{package.name} subfolders should have objects and metadata, found {found}"
        )
        return False

def package_has_no_hidden_file(package: Path) -> bool:
    """The package should not have any hidden file"""
    hidden_ls = [
        h
        for h in package.rglob("*")
        if h.name.startswith(".") or h.name.startswith("Thumbs")
    ]
    if hidden_ls:
        LOGGER.warning(f"{package.name} has hidden files {hidden_ls}")
        return False
    else:
        return True

def package_has_no_zero_bytes_file(package: Path) -> bool:
    """The package should not have any zero bytes file"""
    all_file = [ f for f in package.rglob("*") if f.is_file() ]
    zero_bytes_ls = [ f for f in all_file if f.stat().st_size == 0 ]

    if zero_bytes_ls:
        LOGGER.warning(f"{package.name} has zero bytes file {zero_bytes_ls}")
        return False
    else:
        return True

def metadata_folder_is_flat(package: Path) -> bool:
    """The metadata folder should not have folder structure"""
    metadata_path = package / "metadata"
    md_dir_ls = [x for x in metadata_path.iterdir() if x.is_dir()]
    if md_dir_ls:
        LOGGER.error(f"{package.name} has unexpected directory: {md_dir_ls}")
        return False
    else:
        return True

def metadata_folder_has_files(package: Path) -> bool:
    """The metadata folder should have one or more file"""
    metadata_path = package / "metadata"
    md_files_ls = [ x for x in metadata_path.rglob("*") if x.is_file() ]
    if md_files_ls:
        return True
    else:
        LOGGER.warning(f"{package.name} metadata folder does not have any files")
        return False

def metadata_has_correct_naming_convention(package: Path) -> bool:
    """The metadata file name should be in the accepted list"""
    metadata_path = package / "metadata"
    accepted_fn = ["rclone.log"]

    md_files_ls = [ x for x in metadata_path.rglob("*") if x.is_file() ]
    nonconforming = []
    for file in md_files_ls:
        if not file.name in accepted_fn:
            nonconforming.append(file)

    if nonconforming:
        LOGGER.error(f"""{package.name} has nonconforming metadata file(s):
                     {nonconforming}""")
        return False
    else:
        return True

def objects_folder_correct_structure(package: Path) -> bool:
    """objects folder should have a data folder, which includes four files:
    bag-info.txt, bagit.txt, manifest-md5.txt and tagmanifest-md5.txt"""
    expected_paths = []
    expected_files = ["bag-info.txt", "bagit.txt",
                      "manifest-md5.txt", "tagmanifest-md5.txt"]
    missing = []

    data_folder = package / "objects" / "data"
    expected_paths.append(data_folder)

    for file in expected_files:
        expected_fp = package / "objects" / file
        expected_paths.append(expected_fp)

    for fp in expected_paths:
        if not fp.exists():
            missing.append(fp.name)

    if missing:
        LOGGER.error(f"""{package.name} has incorrect structure.
                     missing {missing}""")
        return False
    else:
        return True

def objects_folder_has_no_empty_folder(package: Path) -> bool:
    """The objects folder should not have any empty folders"""
    objects_path = package / "objects"
    folder_in_obj = [ x for x in objects_path.rglob("*") if x.is_dir() ]
    empty = []

    for folder in folder_in_obj:
        if not any(folder.iterdir()):
            empty.append(folder)

    if empty:
        LOGGER.error(f"{package.name} has empty folder: {empty}")
        return False
    else:
        return True

def lint_package(package: Path) -> Literal["valide", "invalide", "needs review"]:
    """Run all linting tests against a package"""
    result = "valid"

    less_strict_tests = [
        package_has_no_hidden_file,
        package_has_no_zero_bytes_file,
        metadata_folder_has_files
    ]

    for test in less_strict_tests:
        if not test(package):
            result = "needs review"

    strict_tests = [
        package_has_valid_name,
        package_has_two_subfolders,
        package_has_valid_subfolder_names,
        metadata_folder_is_flat,
        metadata_has_correct_naming_convention,
        objects_folder_correct_structure,
        objects_folder_has_no_empty_folder
    ]

    for test in strict_tests:
        if not test(package):
            result = "invalid"

    return result

def main():
    args = parse_args()
    _configure_logging(args.log_folder)

    valid = []
    invalid = []
    needs_review = []

    counter = 0

    for package in args.packages:
        counter += 1
        result = lint_package(package)
        if result == "valid":
            valid.append(package.name)
        elif result == "invalid":
            invalid.append(package.name)
        else:
            needs_review.append(package.name)
    print(f"\nTotal packages ran: {counter}")
    if valid:
        print(
            f"""
        The following {len(valid)} packages are valid: {valid}"""
        )
    if invalid:
        print(
            f"""
        The following {len(invalid)} packages are invalid: {invalid}"""
        )
    if needs_review:
        print(
            f"""
        The following {len(needs_review)} packages need review.
        They may be passed without change after review: {needs_review}""")

if __name__ == "__main__":
    main()