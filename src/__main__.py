import argparse
import pathlib
import sys
import uuid

from .gbsproj_parser import GbsProjectMetadata, ParseError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gbsproj_metafile",
        metavar="FILENAME",
        type=pathlib.Path,
        help="Name of metafile to parse",
    )
    parser.add_argument(
        "--output-file",
        "-o",
        metavar="FILENAME",
        type=pathlib.Path,
        help="Write new script to specified file",
    )
    args = parser.parse_args()

    metadata = GbsProjectMetadata.from_file(args.gbsproj_metafile)

    try:
        metadata.parse()
    except ParseError as e:
        print('Error parsing "{}": {}'.format(e.path, e.message), file=sys.stderr)
        return 1

    output = metadata.to_json()
    if args.output_file is None:
        print(output)
    else:
        with args.output_file.open("w") as f:
            f.write(output)

    return 0


sys.exit(main())
