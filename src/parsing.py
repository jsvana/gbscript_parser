from typing import Any, List, NamedTuple, Optional, Tuple


class ParseContext(NamedTuple):
    line: int
    base_character: int

    def info_str(self, offset: int) -> str:
        return f"line {self.line + 1}, character {self.base_character + offset + 1}"


class Consumption(NamedTuple):
    consumed: int
    trailing: str


class Block(NamedTuple):
    # Should be List[Function] but mypy doesn't support
    # recursive types
    functions: List[Any]


class Argument(NamedTuple):
    name: str
    values: List[str]


class Function(NamedTuple):
    name: str
    arguments: List[Argument]
    block: Optional[Block]


def read_word(content: str) -> Tuple[str, Consumption]:
    word = ""
    consumed = 0
    for char in content:
        if char.isalnum() or char == "_":
            word += char
            consumed += 1
        else:
            return word, Consumption(consumed, content[len(word) :])

    return word, Consumption(consumed, "")


def parse_string(content: str) -> Tuple[str, Consumption]:
    if content[0] != '"':
        raise ValueError("Attempted to parse non-string")

    content = content[1:]
    consumed = 1

    ret = ""
    for char in content:
        consumed += 1
        if char == '"':
            return ret, Consumption(consumed, content[len(ret) + 1 :])
        if char == "\n":
            raise ValueError(f"Attempted to span a string across lines: {ret}")
        ret += char

    raise ValueError(f'Unterminated string "{ret}"')


def parse_list(content: str) -> Tuple[List[str], Consumption]:
    if content[0] != "[":
        raise ValueError("Attempted to parse non-list")

    content = content[1:]
    consumed = 1

    found_end = False
    elements = []
    while content and content[0] != "]" and not found_end:
        element, consumption = parse_string(content)
        consumed += consumption.consumed
        content = consumption.trailing
        if not content:
            raise ValueError("Malformed list")

        if content[0] not in {",", "]"}:
            raise ValueError("Malformed list")

        if content[0] == "]":
            found_end = True

        content = content[1:]
        consumed += 1

        i = 0
        while content and content[i] == " ":
            i += 1

        consumed += i
        content = content[i:]

        elements.append(element)

    if not elements:
        content = content[1:]
        consumed += 1

    return elements, Consumption(consumed, content)


def parse_argument(content: str) -> Tuple[Argument, Consumption]:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.consumed
    if not content:
        raise ValueError(f"Unable to parse argument with name {name}")

    if content[0] != "=":
        raise ValueError(f'Bad argument "{name}"')

    content = content[1:]
    consumed += 1

    if content[0] == '"':
        value, consumption = parse_string(content)
        content = consumption.trailing
        consumed += consumption.consumed
        values = [value]
    elif content[0] == "[":
        values, consumption = parse_list(content)
        content = consumption.trailing
        consumed += consumption.consumed
    else:
        value, consumption = read_word(content)
        content = consumption.trailing
        consumed += consumption.consumed
        values = [value]

    return Argument(name, values), Consumption(consumed, content)


def parse_arguments(content: str) -> Tuple[List[Argument], Consumption]:
    arguments = []
    consumed = 0
    while content and content[0] != ")":
        argument, consumption = parse_argument(content)
        content = consumption.trailing
        consumed += consumption.consumed
        if not content:
            raise ValueError("Malformed function call")

        if content[0] not in {",", ")"}:
            raise ValueError("Malformed function call")

        content = content[1:]
        consumed += 1

        i = 0
        while content and content[i] == " ":
            i += 1

        consumed += i
        content = content[i:]

        arguments.append(argument)

    return arguments, Consumption(consumed, content)


def parse_function(context: ParseContext, content: str) -> Function:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = 0
    if not content:
        raise ValueError(
            'Malformed function with name "{}" on {}'.format(
                name, context.info_str(consumed)
            )
        )

    content = content[1:]
    consumed += 1
    if not content:
        raise ValueError(
            'Malformed function with name "{}" on {}'.format(
                name, context.info_str(consumed)
            )
        )

    if content == ")":
        return Function(name=name, arguments=[], block=None)

    arguments, consumption = parse_arguments(content)
    content = consumption.trailing
    consumed += consumption.consumed
    print(f"CONSUMED: {consumed}")
    if content:
        raise ValueError(
            'Malformed function with name "{}" on {}'.format(
                name, context.info_str(consumed)
            )
        )

    return Function(name=name, arguments=arguments, block=None)


def parse(content: str) -> Block:
    lines = content.split("\n")
    functions = []
    for i, line in enumerate(lines):
        if not line:
            continue

        functions.append(parse_function(ParseContext(line=i, base_character=0), line))

    return Block(functions=functions)
