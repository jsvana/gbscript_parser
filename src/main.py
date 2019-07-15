import sys
from typing import Any, List, NamedTuple, Optional, Tuple


class Block(NamedTuple):
    # Should be List[Function] but mypy doesn't support
    # recursive types
    functions: List[Any]


class Argument(NamedTuple):
    name: str
    value: str


class Function(NamedTuple):
    name: str
    arguments: List[Argument]
    block: Optional[Block]


def read_word(content: str) -> Tuple[str, str]:
    word = ""
    for char in content:
        if char.isalnum() or char == "_":
            word += char
        else:
            return word, content[len(word) :]

    return word, ""


def parse_string(content: str) -> Tuple[str, str]:
    if content[0] != '"':
        raise ValueError("Attempted to parse non-string")

    content = content[1:]

    ret = ""
    for char in content:
        if char == '"':
            return ret, content[len(ret) + 1 :]
        if char == "\n":
            raise ValueError(f"Attempted to span a string across lines: {ret}")
        ret += char

    raise ValueError(f'Unterminated string "{ret}"')


def parse_argument(content: str) -> Tuple[Argument, str]:
    name, content = read_word(content)
    if not content:
        raise ValueError(f"Unable to parse argument with name {name}")

    if content[0] != "=":
        raise ValueError(f'Bad argument "{name}"')

    content = content[1:]

    if content[0] == '"':
        value, content = parse_string(content)
    else:
        value, content = read_word(content)

    return Argument(name, value), content


def parse_arguments(content: str) -> Tuple[List[Argument], str]:
    arguments = []
    while content and content[0] != ")":
        argument, content = parse_argument(content)
        if not content:
            raise ValueError("Malformed function call")

        if content[0] not in {",", ")"}:
            raise ValueError("Malformed function call")

        content = content[1:]

        i = 0
        while content and content[i] == " ":
            i += 1

        content = content[i:]

        arguments.append(argument)

    return arguments, content


def parse_function(content: str) -> Function:
    name, content = read_word(content)
    if not content:
        raise ValueError(f'Malformed function with name "{name}"')
    content = content[1:]
    if not content:
        raise ValueError(f'Malformed function with name "{name}"')
    if content == ")":
        return Function(name=name, arguments=[], block=None)

    arguments, content = parse_arguments(content)
    if content:
        raise ValueError(f'Malformed function with name "{name}"')

    return Function(name=name, arguments=arguments, block=None)


def parse(content: str) -> Block:
    lines = content.split("\n")
    functions = []
    for line in lines:
        if not line:
            continue

        functions.append(parse_function(line))

    return Block(functions=functions)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <source_file>", file=sys.stderr)
        return 1

    with open(sys.argv[1]) as f:
        block = parse(f.read())

    print(block)

    return 0


sys.exit(main())
