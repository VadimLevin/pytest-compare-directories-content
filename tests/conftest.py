import os
import argparse
from datetime import datetime
from typing import Union, Sequence
from pathlib import Path

import pytest


def existing_dir_path(path: Union[os.PathLike, str]) -> Path:
    path = Path(path)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(
            f"{path} doesn't reference an existing directory"
        )
    return path.resolve()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("Directories content comparison parameters")
    group.addoption("--output-dir", type=Path, required=False,
                    default=Path.cwd() / "outputs" / "testing",
                    help="Path to directory containing failed comparison "
                    "tests output")
    group.addoption("--do-not-generate-output-timestamp", action="store_true",
                    help="If this option is omitted than each test run "
                    "generates its own subdirectory in output directory named "
                    "by run start timestamp")
    group.addoption("--from-dir", type=existing_dir_path, required=True,
                    help="Path to 'from' existing directory. Usually this "
                    "directory contains 'gold' (or 'expected') file set")
    group.addoption("--to-dir", type=existing_dir_path, required=True,
                    help="Path to 'to' existing directory. Usually this "
                    "directory contains 'new' (or 'actual') file set")
    group.addoption("--skip-tree-comparison", action="store_true",
                    help="Use this option to skip directories tree comparison "
                    "test and perform common files comparison only")


COMMON_FILES: Sequence[Path]
OUTPUT_DIR: Path


@pytest.fixture
def output_dir() -> Path:
    return OUTPUT_DIR


def pytest_configure(config: pytest.Config) -> None:
    global OUTPUT_DIR, COMMON_FILES

    OUTPUT_DIR = config.getoption("output_dir")
    if not config.getoption("do_not_generate_output_timestamp"):
        timestamp = datetime.now() \
                            .isoformat(timespec="seconds") \
                            .replace(":", "-")
        OUTPUT_DIR /= timestamp

    # Find common files in both directories for comparison
    from_dir: Path = config.getoption("from_dir")
    to_dir: Path = config.getoption("to_dir")
    common_files = []
    for p in filter(lambda p: p.is_file(), from_dir.rglob("*")):
        file = p.relative_to(from_dir)
        if (to_dir / file).is_file():
            common_files.append(file)
    COMMON_FILES = tuple(common_files)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    global COMMON_FILES
    if "file_to_compare" in metafunc.fixturenames:
        metafunc.parametrize("file_to_compare", COMMON_FILES,
                             ids=lambda p: str(p))

    for param in ("from_dir", "to_dir"):
        if param in metafunc.fixturenames:
            param_value = metafunc.config.getoption(param)
            if isinstance(param_value, (Path, str)):
                param_value = (param_value, )
            metafunc.parametrize(param, param_value)
