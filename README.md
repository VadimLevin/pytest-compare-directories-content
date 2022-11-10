# Example on how to generate tests for directories content comparison

Generates PyTest test cases performing deep directories content comparison.

## Usage

```shell
pytest tests --from-dir <from-directory> --to-dir <to-directory>
```

## Implementation details

Tests are generated using 2 PyTest hooks defined in `tests/conftest.py`:

- `pytest_configure`

    This hook runs once command line options are parsed and customized to
    collect common files found in both directories selected for comparison.

- `pytest_generate_tests`

    This hook runs once all test meta-functions are collected and allows to
    perform their parametrization. In this hook every test receives values for each required fixture e.g. if paths to directories selected for comparison.

Essentially the solution generates 2 types of tests:

- Comparison of directories trees using `filecmp.dircmp` [class](https://docs.python.org/3/library/filecmp.html#the-dircmp-class).

    ```python
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

    left_only, right_only = compare_directories_tree(
        filecmp.dircmp(from_dir, to_dir)
    )

    assert len(left_only) == len(right_only) == 0
    ```

- Common files content comparison using `filecmp.cmp` [function](https://docs.python.org/3/library/filecmp.html#filecmp.cmp).

    ```python
    assert filecmp.cmp(from_dir / file_subpath, to_dir / filesubpath, shallow=False)
    ```

  If test fails diff report is generated using `difflib.HtmlDiff` [class](https://docs.python.org/3/library/difflib.html#difflib.HtmlDiff).

  **NOTE** The diff is supported only for UTF-8 encoded text files.
