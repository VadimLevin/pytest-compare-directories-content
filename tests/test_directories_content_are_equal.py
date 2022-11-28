import pytest
import filecmp
from pathlib import Path
from typing import Sequence, Optional, List

from utils import generate_html_diff_file


@pytest.mark.skipif("config.getoption('--skip-tree-comparison')",
                    reason="remove --skip-tree-comparison option to run")
def test_directories_tree_are_same(from_dir: Path, to_dir: Path) -> None:
    def compare_directories_tree(comparator: filecmp.dircmp,
                                 parent_dir: Optional[Path] = None):
        if parent_dir is None:
            parent_dir = Path()

        left_only: List[Path] = []
        left_only.extend(parent_dir / f for f in comparator.left_only)
        right_only: List[Path] = []
        right_only.extend(parent_dir / f for f in comparator.right_only)

        for subdir, common_subdir_comparator in comparator.subdirs.items():
            lhs, rhs = compare_directories_tree(common_subdir_comparator,
                                                parent_dir=parent_dir / subdir)
            left_only.extend(lhs)
            right_only.extend(rhs)
        return left_only, right_only

    def generate_files_and_directories_list_str(paths: Sequence) -> str:
        return '\n'.join("\t- " + str(path) for path in paths)

    left_only, right_only = compare_directories_tree(
        filecmp.dircmp(from_dir, to_dir)
    )
    assert len(left_only) == len(right_only) == 0, \
        "Directories tree are different\n" \
        f"{from_dir.absolute()} unique files and directories:\n" \
        f"{generate_files_and_directories_list_str(left_only)}\n" \
        f"{to_dir.absolute()} unique files and directories:\n" \
        f"{generate_files_and_directories_list_str(right_only)}"


def test_common_files_content_is_same(from_dir: Path, to_dir: Path,
                                      file_to_compare: Path,
                                      output_dir: Path) -> None:
    from_file = from_dir / file_to_compare
    to_file = to_dir / file_to_compare
    are_files_content_same = filecmp.cmp(from_file, to_file, False)
    if not are_files_content_same:
        try:
            diff_file_path = generate_html_diff_file(from_file, to_file,
                                                     output=output_dir)
            diff_info = f"Generated diff file is written to {diff_file_path}"
        except TypeError as e:
            diff_info = f"Failed to generate diff file. Reason: {e}"
    else:
        diff_info = None

    assert are_files_content_same, \
        f"Content of '{file_to_compare.name}' files in '{from_dir}' and " \
        f" '{to_dir}' are different.\n{diff_info}"
