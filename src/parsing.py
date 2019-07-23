import uuid
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

INDENT = 2


class Context(NamedTuple):
    line: int
    base_character: int

    def info_str(self, offset: int) -> str:
        return f"line {self.line + 1}, character {self.base_character + offset + 1}"

    def from_self_with_offset(self, offset: int) -> "Context":
        return Context(line=self.line, base_character=self.base_character + offset)


class Consumption(NamedTuple):
    characters_consumed: int
    lines_consumed: int
    trailing: str


class Block(NamedTuple):
    # Should be List[Function] but mypy doesn't support
    # recursive types
    functions: List[Any]
    context: Context

    def to_dict(self, scene_names_to_ids: Dict[str, str]) -> List[Dict[str, Any]]:
        ret = []
        for function in self.functions:
            ret.append(function.to_dict(scene_names_to_ids))
        return ret

    def validate(self) -> None:
        for function in self.functions:
            function.validate()

        if self.functions and self.functions[-1].name != "EVENT_END":
            raise ValueError(
                "block doesn't end with EVENT_END() at {}".format(
                    self.context.info_str(0)
                )
            )


class Argument(NamedTuple):
    name: str
    values: List[str]
    context: Context

    def validate(self) -> None:
        pass


class Function:
    __slots__ = ["name", "arguments", "context", "true", "false"]

    def __init__(
        self,
        name: str,
        arguments: List[Argument],
        context: Context,
        true: Optional[Block] = None,
        false: Optional[Block] = None,
    ) -> None:
        name = name.upper()
        if not name.startswith("EVENT_"):
            name = f"EVENT_{name}"
        self.name = name
        self.arguments = arguments
        self.context = context
        self.true = true
        self.false = false

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Function):
            return False

        return (
            self.name == other.name
            and self.arguments == other.arguments
            and self.true == other.true
            and self.false == other.false
        )

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return (
            f"Function(name={self.name}, arguments={self.arguments}, "
            f"true={self.true}, false={self.false})"
        )

    def to_dict(self, scene_names_to_ids: Dict[str, str]) -> Dict[str, Any]:
        ret: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "command": self.name,
            "args": {},
        }

        for argument in self.arguments:
            if argument.name == "sceneName":
                scene_name = argument.values[0]
                scene_id = scene_names_to_ids.get(scene_name)
                if scene_id is None:
                    raise ValueError(
                        'unknown scene name "{}" at {}'.format(
                            scene_name, argument.context.info_str(0)
                        )
                    )

                ret["args"]["sceneId"] = scene_id
                continue

            if len(argument.values) == 1:
                ret["args"][argument.name] = argument.values[0]
            else:
                ret["args"][argument.name] = argument.values

        if self.true is not None:
            ret["true"] = self.true.to_dict(scene_names_to_ids)

        if self.false is not None:
            ret["false"] = self.false.to_dict(scene_names_to_ids)

        return ret

    def validate(self) -> None:
        if self.true is not None:
            if self.false is None:
                raise ValueError(
                    'function "{}" is missing an IF_FALSE() at {}'.format(
                        self.name, self.context.info_str(0)
                    )
                )

            self.true.validate()

        if self.false is not None:
            if self.true is None:
                raise ValueError(
                    'function "{}" is missing an IF_TRUE() at {}'.format(
                        self.name, self.context.info_str(0)
                    )
                )

            self.false.validate()

        for argument in self.arguments:
            argument.validate()


def read_word(content: str) -> Tuple[str, Consumption]:
    word = ""
    consumed = 0
    for char in content:
        if char.isalnum() or char == "_":
            word += char
            consumed += 1
        else:
            return (
                word,
                Consumption(
                    characters_consumed=consumed,
                    lines_consumed=0,
                    trailing=content[len(word) :],
                ),
            )

    return (
        word,
        Consumption(characters_consumed=consumed, lines_consumed=0, trailing=""),
    )


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
            return (
                ret,
                Consumption(
                    characters_consumed=consumed,
                    lines_consumed=0,
                    trailing=content[len(ret) + 1 :],
                ),
            )
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
        consumed += consumption.characters_consumed
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

    return (
        elements,
        Consumption(characters_consumed=consumed, lines_consumed=0, trailing=content),
    )


def parse_argument(context: Context, content: str) -> Tuple[Argument, Consumption]:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.characters_consumed
    if not content:
        raise ValueError(
            "unable to parse argument with name {} at {}".format(
                name, context.info_str(consumed)
            )
        )

    if content[0] != "=":
        raise ValueError(
            'bad argument "{}" at {}'.format(name, context.info_str(consumed))
        )

    content = content[1:]
    consumed += 1

    call_context = context.from_self_with_offset(consumed)
    if content[0] == '"':
        value, consumption = parse_string(call_context, content)
        content = consumption.trailing
        consumed += consumption.characters_consumed
        values = [value]
    elif content[0] == "[":
        values, consumption = parse_list(call_context, content)
        content = consumption.trailing
        consumed += consumption.characters_consumed
    else:
        value, consumption = read_word(content)
        content = consumption.trailing
        consumed += consumption.characters_consumed
        values = [value]

    return (
        Argument(name, values, context),
        Consumption(characters_consumed=consumed, lines_consumed=0, trailing=content),
    )


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
        consumed += consumption.characters_consumed
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

    return (
        arguments,
        Consumption(characters_consumed=consumed, lines_consumed=0, trailing=content),
    )


def parse_function(context: Context, content: str) -> Tuple[Function, Consumption]:
    name, consumption = read_word(content)
    content = consumption.trailing
    consumed = consumption.characters_consumed + context.base_character
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
    consumed += consumption.characters_consumed
    if content:
        raise ValueError(
            'malformed function with name "{}" at {}'.format(
                name, context.info_str(consumed)
            )
        )

    return (
        Function(name=name, arguments=arguments, context=context),
        Consumption(characters_consumed=consumed, lines_consumed=0, trailing=""),
    )


def append_event_end(block: Block) -> None:
    if block.functions and block.functions[-1].name != "EVENT_END":
        block.functions.append(
            Function(name="EVENT_END", arguments=[], context=Context(-1, -1))
        )


def parse_block(
    context: Context, lines: List[str], expected_indent: int
) -> Tuple[Block, Consumption]:
    # TODO(jsvana): add EVENT_END add after parsing everything instead
    consumed = 0
    total_lines_consumed = context.line

    block = Block(functions=[], context=context)

    i = 0
    while i < len(lines):
        line_consumed = 0

        line = lines[i]
        if not line:
            # Takes care of the newline
            i += 1
            consumed += 1
            line_consumed += 1
            total_lines_consumed += 1
            continue

        c = 0
        while line[c] == " ":
            c += 1

        line = line[c:]

        if c < expected_indent:
            append_event_end(block)

            lines_consumed = i

            return (
                block,
                Consumption(
                    characters_consumed=consumed,
                    lines_consumed=lines_consumed,
                    trailing="",
                ),
            )

        # Done after because we're not consuming the next line
        consumed += c
        line_consumed += c

        append = True
        function, consumption = parse_function(
            Context(line=i + total_lines_consumed, base_character=line_consumed), line
        )
        consumed += consumption.characters_consumed
        if function.name in {"EVENT_IF_TRUE", "EVENT_IF_FALSE"}:
            append = False
            child_block, consumption = parse_block(
                Context(line=i + 1, base_character=consumed),
                lines[i + 1 :],
                expected_indent + INDENT,
            )

            last_function = block.functions[-1]

            if function.name == "EVENT_IF_TRUE":
                last_function.true = child_block
            else:
                last_function.false = child_block

            consumed += consumption.characters_consumed
            total_lines_consumed += consumption.lines_consumed
            i += consumption.lines_consumed

        # Newline
        consumed += 1

        if append:
            block.functions.append(function)

        i += 1

    append_event_end(block)

    return (
        block,
        Consumption(
            characters_consumed=consumed,
            lines_consumed=total_lines_consumed,
            trailing="",
        ),
    )


def parse(content: str) -> Block:
    block, *_ = parse_block(
        Context(line=0, base_character=0), content.split("\n"), expected_indent=0
    )

    block.validate()

    return block
