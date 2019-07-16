import sys

from .parsing import parse


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <source_file>", file=sys.stderr)
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
