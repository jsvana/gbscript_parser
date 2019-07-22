import argparse
import pathlib
import sys
import uuid

from .gbsproj_parser import GbsProjectMetadata
from .parsing import parse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "gbsproj_metafile",
        metavar="FILENAME",
        type=pathlib.Path,
        help="Name of metafile to parse",
    )
    args = parser.parse_args()

    print(str(uuid.uuid4()))

    metadata = GbsProjectMetadata.from_file(args.gbsproj_metafile)

    print(metadata.project.scene_names_to_ids)

    return 1

    with open(sys.argv[1]) as f:
        try:
            block = parse(f.read())
        except ValueError as e:
            print(f'Error parsing "{sys.argv[1]}": {e}', file=sys.stderr)
            return 1

    print(block)

    return 0


sys.exit(main())
