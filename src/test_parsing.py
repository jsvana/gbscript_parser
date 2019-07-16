import unittest

from . import parsing

FAKE_CONTEXT = parsing.Context(line=0, base_character=0)


class ParserTests(unittest.TestCase):
    def test_read_word(self) -> None:
        word, consumption = parsing.read_word("asdf(fdsa)")

        self.assertEqual(word, "asdf")
        self.assertEqual(consumption.consumed, 4)
        self.assertEqual(consumption.trailing, "(fdsa)")

        word, consumption = parsing.read_word("(fdsa)")

        self.assertEqual(word, "")
        self.assertEqual(consumption.consumed, 0)
        self.assertEqual(consumption.trailing, "(fdsa)")

    def test_parse_string(self) -> None:
        string, consumption = parsing.parse_string(FAKE_CONTEXT, '"foobar"])')

        self.assertEqual(string, "foobar")
        self.assertEqual(consumption.consumed, 8)
        self.assertEqual(consumption.trailing, "])")

        string, consumption = parsing.parse_string(FAKE_CONTEXT, '""])')

        self.assertEqual(string, "")
        self.assertEqual(consumption.consumed, 2)
        self.assertEqual(consumption.trailing, "])")

        with self.assertRaises(ValueError):
            parsing.parse_string(FAKE_CONTEXT, 'asdf"')

        with self.assertRaises(ValueError):
            parsing.parse_string(FAKE_CONTEXT, '"asdf\nfdsa"')

    def test_parse_list(self) -> None:
        values, consumption = parsing.parse_list(FAKE_CONTEXT, '["foobar"])')

        self.assertEqual(values, ["foobar"])
        self.assertEqual(consumption.consumed, 10)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list(FAKE_CONTEXT, "[])")

        self.assertEqual(values, [])
        self.assertEqual(consumption.consumed, 2)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list(FAKE_CONTEXT, '["foobar", "asdf"])')

        self.assertEqual(values, ["foobar", "asdf"])
        self.assertEqual(consumption.consumed, 18)
        self.assertEqual(consumption.trailing, ")")

        with self.assertRaises(ValueError):
            parsing.parse_list(FAKE_CONTEXT, '"asdf", "fdsa"]')

        with self.assertRaises(ValueError):
            parsing.parse_list(FAKE_CONTEXT, '["asdf" "fdsa"]')

        with self.assertRaises(ValueError):
            parsing.parse_list(FAKE_CONTEXT, '["asdf", "fdsa"')

    def test_parse_argument(self) -> None:
        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf="foobar")')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=["foobar"]))
        self.assertEqual(consumption.consumed, 13)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf=["foobar"])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=["foobar"]))
        self.assertEqual(consumption.consumed, 15)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(
            FAKE_CONTEXT, 'asdf=["foobar", "baz"])'
        )

        self.assertEqual(
            argument, parsing.Argument(name="asdf", values=["foobar", "baz"])
        )
        self.assertEqual(consumption.consumed, 22)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, "asdf=[])")

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[]))
        self.assertEqual(consumption.consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf="")')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf=[""])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.consumed, 9)
        self.assertEqual(consumption.trailing, ")")

        with self.assertRaises(ValueError):
            parsing.parse_argument(FAKE_CONTEXT, "foo")

        with self.assertRaises(ValueError):
            parsing.parse_argument(FAKE_CONTEXT, 'foo"bar"')

    def test_parse_arguments(self) -> None:
        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf="foobar")asdf'
        )

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=["foobar"])])
        self.assertEqual(consumption.consumed, 15)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(FAKE_CONTEXT, '(asdf="")asdf')

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[""])])
        self.assertEqual(consumption.consumed, 9)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf=[""])asdf'
        )

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[""])])
        self.assertEqual(consumption.consumed, 11)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(FAKE_CONTEXT, "(asdf=[])asdf")

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[])])
        self.assertEqual(consumption.consumed, 9)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf=[], fdsa="")asdf'
        )

        self.assertEqual(
            arguments,
            [
                parsing.Argument(name="asdf", values=[]),
                parsing.Argument(name="fdsa", values=[""]),
            ],
        )
        self.assertEqual(consumption.consumed, 18)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf="", fdsa=[])asdf'
        )

        self.assertEqual(
            arguments,
            [
                parsing.Argument(name="asdf", values=[""]),
                parsing.Argument(name="fdsa", values=[]),
            ],
        )
        self.assertEqual(consumption.consumed, 18)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf="foo", fdsa="bar")asdf'
        )

        self.assertEqual(
            arguments,
            [
                parsing.Argument(name="asdf", values=["foo"]),
                parsing.Argument(name="fdsa", values=["bar"]),
            ],
        )
        self.assertEqual(consumption.consumed, 24)
        self.assertEqual(consumption.trailing, "asdf")

        with self.assertRaises(ValueError):
            parsing.parse_arguments(FAKE_CONTEXT, '(asdf="foo"')

        with self.assertRaises(ValueError):
            parsing.parse_arguments(FAKE_CONTEXT, '(asdf="foo", fdsa="bar"')

        with self.assertRaises(ValueError):
            parsing.parse_arguments(FAKE_CONTEXT, '(asdf="foo",asdf')

        with self.assertRaises(ValueError):
            parsing.parse_arguments(FAKE_CONTEXT, '(asdf="foo", fdsa="bar",asdf')

        with self.assertRaises(ValueError):
            parsing.parse_arguments(FAKE_CONTEXT, '(asdf="foo", fdsa="bar",)')

    def test_parse_function(self) -> None:
        function = parsing.parse_function(parsing.Context(0, 0), 'foo(asdf="bar")')

        self.assertEqual(
            function,
            parsing.Function(
                name="foo",
                arguments=[parsing.Argument(name="asdf", values=["bar"])],
                block=None,
            ),
        )

        function = parsing.parse_function(parsing.Context(0, 0), "foo()")

        self.assertEqual(
            function, parsing.Function(name="foo", arguments=[], block=None)
        )

        with self.assertRaises(ValueError):
            parsing.parse_function(parsing.Context(0, 0), "foo")

        with self.assertRaises(ValueError):
            parsing.parse_function(parsing.Context(0, 0), "foo()asdf")

    def test_parse(self) -> None:
        block = parsing.parse('foo(asdf="bar")\nfunc2(a="")')
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        block=None,
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=[""])],
                        block=None,
                    ),
                    parsing.Function(name="EVENT_END", arguments=[], block=None),
                ]
            ),
        )

        block = parsing.parse('foo(asdf="bar")\nfunc2(a="")\n')
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        block=None,
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=[""])],
                        block=None,
                    ),
                    parsing.Function(name="EVENT_END", arguments=[], block=None),
                ]
            ),
        )

        block = parsing.parse('foo(asdf="bar")\nfunc2(a=["a", "b"])\n')
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        block=None,
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=["a", "b"])],
                        block=None,
                    ),
                    parsing.Function(name="EVENT_END", arguments=[], block=None),
                ]
            ),
        )

        block = parsing.parse('foo(asdf="bar")\nfunc2(a=["a", "b"])\nEVENT_END()\n')
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        block=None,
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=["a", "b"])],
                        block=None,
                    ),
                    parsing.Function(name="EVENT_END", arguments=[], block=None),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
