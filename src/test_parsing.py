import unittest

from . import parsing

FAKE_CONTEXT = parsing.Context(line=0, base_character=0)


class ParserTests(unittest.TestCase):
    def test_read_word(self) -> None:
        word, consumption = parsing.read_word("asdf(fdsa)")

        self.assertEqual(word, "asdf")
        self.assertEqual(consumption.characters_consumed, 4)
        self.assertEqual(consumption.trailing, "(fdsa)")

        word, consumption = parsing.read_word("(fdsa)")

        self.assertEqual(word, "")
        self.assertEqual(consumption.characters_consumed, 0)
        self.assertEqual(consumption.trailing, "(fdsa)")

    def test_parse_string(self) -> None:
        string, consumption = parsing.parse_string(FAKE_CONTEXT, '"foobar"])')

        self.assertEqual(string, "foobar")
        self.assertEqual(consumption.characters_consumed, 8)
        self.assertEqual(consumption.trailing, "])")

        string, consumption = parsing.parse_string(FAKE_CONTEXT, '""])')

        self.assertEqual(string, "")
        self.assertEqual(consumption.characters_consumed, 2)
        self.assertEqual(consumption.trailing, "])")

        with self.assertRaises(ValueError):
            parsing.parse_string(FAKE_CONTEXT, 'asdf"')

        with self.assertRaises(ValueError):
            parsing.parse_string(FAKE_CONTEXT, '"asdf\nfdsa"')

    def test_parse_list(self) -> None:
        values, consumption = parsing.parse_list(FAKE_CONTEXT, '["foobar"])')

        self.assertEqual(values, ["foobar"])
        self.assertEqual(consumption.characters_consumed, 10)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list(FAKE_CONTEXT, "[])")

        self.assertEqual(values, [])
        self.assertEqual(consumption.characters_consumed, 2)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list(FAKE_CONTEXT, '["foobar", "asdf"])')

        self.assertEqual(values, ["foobar", "asdf"])
        self.assertEqual(consumption.characters_consumed, 18)
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
        self.assertEqual(consumption.characters_consumed, 13)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf=["foobar"])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=["foobar"]))
        self.assertEqual(consumption.characters_consumed, 15)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(
            FAKE_CONTEXT, 'asdf=["foobar", "baz"])'
        )

        self.assertEqual(
            argument, parsing.Argument(name="asdf", values=["foobar", "baz"])
        )
        self.assertEqual(consumption.characters_consumed, 22)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, "asdf=[])")

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[]))
        self.assertEqual(consumption.characters_consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf="")')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.characters_consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument(FAKE_CONTEXT, 'asdf=[""])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.characters_consumed, 9)
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
        self.assertEqual(consumption.characters_consumed, 15)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(FAKE_CONTEXT, '(asdf="")asdf')

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[""])])
        self.assertEqual(consumption.characters_consumed, 9)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(
            FAKE_CONTEXT, '(asdf=[""])asdf'
        )

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[""])])
        self.assertEqual(consumption.characters_consumed, 11)
        self.assertEqual(consumption.trailing, "asdf")

        arguments, consumption = parsing.parse_arguments(FAKE_CONTEXT, "(asdf=[])asdf")

        self.assertEqual(arguments, [parsing.Argument(name="asdf", values=[])])
        self.assertEqual(consumption.characters_consumed, 9)
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
        self.assertEqual(consumption.characters_consumed, 18)
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
        self.assertEqual(consumption.characters_consumed, 18)
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
        self.assertEqual(consumption.characters_consumed, 24)
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
        function, consumption = parsing.parse_function(
            parsing.Context(0, 0), 'foo(asdf="bar")'
        )

        self.assertEqual(
            function,
            parsing.Function(
                name="foo", arguments=[parsing.Argument(name="asdf", values=["bar"])]
            ),
        )
        self.assertEqual(consumption.characters_consumed, 15)
        self.assertEqual(consumption.lines_consumed, 0)
        self.assertEqual(consumption.trailing, "")

        function, consumption = parsing.parse_function(parsing.Context(0, 0), "foo()")
        self.assertEqual(consumption.characters_consumed, 5)
        self.assertEqual(consumption.lines_consumed, 0)
        self.assertEqual(consumption.trailing, "")

        self.assertEqual(function, parsing.Function(name="foo", arguments=[]))

        with self.assertRaises(ValueError):
            parsing.parse_function(parsing.Context(0, 0), "foo")

        with self.assertRaises(ValueError):
            parsing.parse_function(parsing.Context(0, 0), "foo()asdf")

    def test_parse_block(self) -> None:
        block, consumption = parsing.parse_block(
            parsing.Context(0, 0), ['foo(asdf="bar")', 'func2(a="")'], 0
        )
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=[""])],
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )
        self.assertEqual(consumption.characters_consumed, 44)
        self.assertEqual(consumption.lines_consumed, 2)

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0), ['foo(asdf="bar")', 'func2(a="")'], 0
        )
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=[""])],
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0), ['foo(asdf="bar")', 'func2(a=["a", "b"])'], 0
        )
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=["a", "b"])],
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0),
            ['foo(asdf="bar")', 'func2(a=["a", "b"])', "EVENT_END()"],
            0,
        )
        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                    ),
                    parsing.Function(
                        name="func2",
                        arguments=[parsing.Argument(name="a", values=["a", "b"])],
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0),
            [
                'foo(asdf="bar")',
                "IF_TRUE()",
                '  asdf(a=["a", "b"])',
                "IF_FALSE()",
                "  fdsa()",
            ],
            0,
        )

        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        true=parsing.Block(
                            functions=[
                                parsing.Function(
                                    name="asdf",
                                    arguments=[
                                        parsing.Argument(name="a", values=["a", "b"])
                                    ],
                                ),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                        false=parsing.Block(
                            functions=[
                                parsing.Function(name="fdsa", arguments=[]),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0),
            [
                'foo(asdf="bar")',
                "IF_TRUE()",
                '  asdf(a=["a", "b"])',
                "IF_FALSE()",
                "  fdsa()",
                '  bar(a="b")',
                "  IF_TRUE()",
                '    baz(b="c")',
                "  IF_FALSE()",
                '    fdsa(c="d")',
            ],
            0,
        )

        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        true=parsing.Block(
                            functions=[
                                parsing.Function(
                                    name="asdf",
                                    arguments=[
                                        parsing.Argument(name="a", values=["a", "b"])
                                    ],
                                ),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                        false=parsing.Block(
                            functions=[
                                parsing.Function(name="fdsa", arguments=[]),
                                parsing.Function(
                                    name="bar",
                                    arguments=[
                                        parsing.Argument(name="a", values=["b"])
                                    ],
                                    true=parsing.Block(
                                        functions=[
                                            parsing.Function(
                                                name="baz",
                                                arguments=[
                                                    parsing.Argument(
                                                        name="b", values=["c"]
                                                    )
                                                ],
                                            ),
                                            parsing.Function(
                                                name="EVENT_END", arguments=[]
                                            ),
                                        ]
                                    ),
                                    false=parsing.Block(
                                        functions=[
                                            parsing.Function(
                                                name="fdsa",
                                                arguments=[
                                                    parsing.Argument(
                                                        name="c", values=["d"]
                                                    )
                                                ],
                                            ),
                                            parsing.Function(
                                                name="EVENT_END", arguments=[]
                                            ),
                                        ]
                                    ),
                                ),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )

        block, consumption = parsing.parse_block(
            parsing.Context(0, 0),
            [
                'foo(asdf="bar")',
                "IF_TRUE()",
                '  asdf(a=["a", "b"])',
                '  bar(a="b")',
                "  IF_TRUE()",
                '    baz(b="c")',
                "  IF_FALSE()",
                '    fdsa(c="d")',
                "IF_FALSE()",
                "  fdsa()",
            ],
            0,
        )

        self.assertEqual(
            block,
            parsing.Block(
                functions=[
                    parsing.Function(
                        name="foo",
                        arguments=[parsing.Argument(name="asdf", values=["bar"])],
                        true=parsing.Block(
                            functions=[
                                parsing.Function(
                                    name="asdf",
                                    arguments=[
                                        parsing.Argument(name="a", values=["a", "b"])
                                    ],
                                ),
                                parsing.Function(
                                    name="bar",
                                    arguments=[
                                        parsing.Argument(name="a", values=["b"])
                                    ],
                                    true=parsing.Block(
                                        functions=[
                                            parsing.Function(
                                                name="baz",
                                                arguments=[
                                                    parsing.Argument(
                                                        name="b", values=["c"]
                                                    )
                                                ],
                                            ),
                                            parsing.Function(
                                                name="EVENT_END", arguments=[]
                                            ),
                                        ]
                                    ),
                                    false=parsing.Block(
                                        functions=[
                                            parsing.Function(
                                                name="fdsa",
                                                arguments=[
                                                    parsing.Argument(
                                                        name="c", values=["d"]
                                                    )
                                                ],
                                            ),
                                            parsing.Function(
                                                name="EVENT_END", arguments=[]
                                            ),
                                        ]
                                    ),
                                ),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                        false=parsing.Block(
                            functions=[
                                parsing.Function(name="fdsa", arguments=[]),
                                parsing.Function(name="EVENT_END", arguments=[]),
                            ]
                        ),
                    ),
                    parsing.Function(name="EVENT_END", arguments=[]),
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
