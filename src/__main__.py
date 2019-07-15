import sys

from .parsing import parse


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <source_file>", file=sys.stderr)
        return 1

    with open(sys.argv[1]) as f:
        block = parse(f.read())

    print(block)

    return 0


sys.exit(main())
