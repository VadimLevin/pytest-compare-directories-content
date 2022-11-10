__all__ = ("get_unified_file_name_with_enclosing_folder", "generate_html_diff",
           "generate_html_diff_file")

import os
import argparse
import difflib
from pathlib import Path
from typing import Sequence, Tuple, Union


def _existing_file_path(path: Union[os.PathLike, str, Path]) -> Path:
    path = Path(path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(
            f"{path} doesn't reference an existing file"
        )
    return path


def get_unified_file_name_with_enclosing_folder(file_path: Path) -> str:
    name = file_path.name
    for char in ("/", "."):
        name = name.replace(char, "_")
    name = file_path.absolute().parent.stem + "_" + name
    return name


def _prepare_file_content_for_comparison(file_path: Path) \
        -> Tuple[str, Sequence[str]]:

    if file_path.is_dir():
        raise ValueError(f"{file_path} is a directory")

    descriptive_file_name = get_unified_file_name_with_enclosing_folder(
        file_path
    )
    if file_path.is_file():
        try:
            file_content = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as e:
            # It means that this file is binary...
            raise TypeError("Binary files diff are not supported") from e
    else:
        file_content = []
    return descriptive_file_name, file_content


def generate_html_diff(from_file_path: Path, to_file_path: Path,
                       context: bool = False, num_lines: int = 5) -> str:
    from_file_desc, from_file_content = _prepare_file_content_for_comparison(
        from_file_path
    )
    to_file_desc, to_file_content = _prepare_file_content_for_comparison(
        to_file_path
    )

    return difflib.HtmlDiff().make_file(from_file_content, to_file_content,
                                        from_file_desc, to_file_desc,
                                        context=context, numlines=num_lines)


def generate_html_diff_file(from_file_path: Path, to_file_path: Path,
                            output: Path, context: bool = False,
                            num_lines: int = 5) -> Path:
    diff = generate_html_diff(from_file_path, to_file_path, context, num_lines)

    if output.suffix != ".html":
        output = Path(
            output,
            "_vs_".join(map(get_unified_file_name_with_enclosing_folder,
                            (from_file_path, to_file_path)))
        ).with_suffix(".html")
    output.parent.mkdir(exist_ok=True, parents=True)

    output.write_text(diff)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("from_file", type=_existing_file_path,
                        help="Path to 'from' file selected for comparison")
    parser.add_argument("to_file", type=_existing_file_path,
                        help="Path to 'to' file selected for comparison")
    parser.add_argument("--out", dest="output_dir", type=Path,
                        default=Path.cwd() / "outputs",
                        help="Path to output directory containing difference "
                        "between 'from' and 'to' files in HTML format")
    args = parser.parse_args()

    output_file_path = generate_html_diff_file(args.from_file, args.to_file,
                                               args.output_dir)
    print("Diff is written to", output_file_path)

    return 0


if __name__ == '__main__':
    main()
