from typing import Any, List, NamedTuple, Optional, Tuple

INDENT = 2


class Context(NamedTuple):
    line: int
    base_character: int

    def info_str(self, offset: int) -> str:
        return f"line {self.line + 1}, character {self.base_character + offset + 1}"

    def from_self_with_offset(self, offset: int) -> "Context":
        return Context(line=self.line, base_character=self.base_character + offset)


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
    true: Optional[Block]
    false: Optional[Block]


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


def parse_string(context: Context, content: str) -> Tuple[str, Consumption]:
    if content[0] != '"':
        raise ValueError(
            "Attempted to parse non-string at {}".format(context.info_str(0))
        )

    content = content[1:]
    consumed = 1

    ret = ""
    for char in content:
        consumed += 1
        if char == '"':
            return ret, Consumption(consumed, content[len(ret) + 1 :])
        if char == "\n":
            raise ValueError(
                "Attempted to span a string across lines at {}".format(
                    context.info_str(consumed)
                )
            )
        ret += char

    raise ValueError(
        'Unterminated string "{}" at {}'.format(ret, context.info_str(consumed))
    )


def parse_list(context: Context, content: str) -> Tuple[List[str], Consumption]:
    if content[0] != "[":
        raise ValueError("Attempted to parse non-list")

    content = content[1:]
    consumed = 1

    found_end = False
    elements = []
    while content and content[0] != "]" and not found_end:
        element, consumption = parse_string(
            context.from_self_with_offset(consumed), content
        )
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


def parse_argument(context: Context, content: str) -> Tuple[Argument, Consumption]:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.consumed
    if not content:
        raise ValueError(
            "Unable to parse argument with name {} at {}".format(
                name, context.info_str(consumed)
            )
        )

    if content[0] != "=":
        raise ValueError(
            'Bad argument "{}" at {}'.format(name, context.info_str(consumed))
        )

    content = content[1:]
    consumed += 1

    call_context = context.from_self_with_offset(consumed)
    if content[0] == '"':
        value, consumption = parse_string(call_context, content)
        content = consumption.trailing
        consumed += consumption.consumed
        values = [value]
    elif content[0] == "[":
        values, consumption = parse_list(call_context, content)
        content = consumption.trailing
        consumed += consumption.consumed
    else:
        value, consumption = read_word(content)
        content = consumption.trailing
        consumed += consumption.consumed
        values = [value]

    return Argument(name, values), Consumption(consumed, content)


def parse_arguments(
    context: Context, content: str
) -> Tuple[List[Argument], Consumption]:
    if content[0] != "(":
        raise ValueError(
            "attempted to parse non-argument at {}".format(context.info_str(0))
        )

    content = content[1:]
    consumed = 1

    found_end = False
    arguments = []
    while content and content[0] != ")" and not found_end:
        argument, consumption = parse_argument(
            context.from_self_with_offset(consumed), content
        )
        content = consumption.trailing
        consumed += consumption.consumed
        if not content:
            raise ValueError(
                "malformed function call at {}".format(context.info_str(consumed))
            )

        if content[0] not in {",", ")"}:
            raise ValueError(
                "malformed function call at {}".format(context.info_str(consumed))
            )

        if content[0] == ")":
            found_end = True

        if content.startswith(",)"):
            raise ValueError(
                "trailing comma on function call at {}".format(
                    context.info_str(consumed)
                )
            )

        content = content[1:]
        consumed += 1

        i = 0
        while content and content[i] == " ":
            i += 1

        consumed += i
        content = content[i:]

        arguments.append(argument)

    if not arguments:
        content = content[1:]
        consumed += 1

    return arguments, Consumption(consumed, content)


def parse_function(context: Context, content: str) -> Tuple[Function, Consumption]:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.consumed + context.base_character
    if not content:
        raise ValueError(
            'malformed function with name "{}" at {}'.format(
                name, context.info_str(consumed)
            )
        )

    arguments, consumption = parse_arguments(
        Context(line=context.line, base_character=consumed), content
    )
    content = consumption.trailing
    consumed += consumption.consumed
    if content:
        raise ValueError(
            'malformed function with name "{}" at {}'.format(
                name, context.info_str(consumed)
            )
        )

    return (
        Function(name=name, arguments=arguments, true=None, false=None),
        Consumption(consumed=consumed, trailing=""),
    )


def parse_block(
    context: Context, content: str, expected_indent: int
) -> Tuple[Block, Consumption, int]:
    lines = content.split("\n")
    functions: List[Function] = []
    consumed = 0
    total_lines_consumed = context.line

    for i, line in enumerate(lines):
        if not line:
            # Takes care of the newline
            consumed += 1
            total_lines_consumed += 1
            continue

        c = 0
        while line[c] == " ":
            c += 1

        line = line[c:]

        if c < expected_indent:
            if functions and functions[-1].name != "EVENT_END":
                functions.append(
                    Function(name="EVENT_END", arguments=[], true=None, false=None)
                )
                return (
                    Block(functions=functions),
                    Consumption(consumed=consumed, trailing="\n".join(lines[i + 1 :])),
                    i + total_lines_consumed,
                )

        # Done after because we're not consuming the next line
        consumed += c

        function, consumption = parse_function(
            Context(line=i + total_lines_consumed, base_character=consumed), line
        )
        consumed += consumption.consumed
        if function.name in {"IF_TRUE", "IF_FALSE"}:
            block, consumption, lines_consumed = parse_block(
                Context(line=i + total_lines_consumed + 1, base_character=consumed),
                "\n".join(lines[i + 1 :]),
                expected_indent + INDENT,
            )
            consumed += consumption.consumed
            total_lines_consumed += lines_consumed
            lines = consumption.trailing.split("\n")

        # Newline
        consumed += 1

        functions.append(function)

    if functions and functions[-1].name != "EVENT_END":
        functions.append(
            Function(name="EVENT_END", arguments=[], true=None, false=None)
        )

    return (
        Block(functions=functions),
        Consumption(consumed, content),
        total_lines_consumed,
    )


def parse(content: str) -> Block:
    block, *_ = parse_block(Context(line=0, base_character=0), content, 0)
    return block
