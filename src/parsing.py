from typing import Any, List, NamedTuple, Optional, Tuple


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


def parse_function(context: Context, content: str) -> Function:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.consumed
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

    return Function(name=name, arguments=arguments, block=None)


def parse(content: str) -> Block:
    lines = content.split("\n")
    functions = []
    for i, line in enumerate(lines):
        if not line:
            continue

        c = 0
        while line[c] == " ":
            c += 1

        functions.append(parse_function(Context(line=i, base_character=c), line[c:]))

    if functions and functions[-1].name != "EVENT_END":
        functions.append(Function(name="EVENT_END", arguments=[], block=None))

    return Block(functions=functions)
