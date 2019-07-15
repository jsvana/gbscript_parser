import unittest

from . import parsing


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
        string, consumption = parsing.parse_string('"foobar"])')

        self.assertEqual(string, "foobar")
        self.assertEqual(consumption.consumed, 8)
        self.assertEqual(consumption.trailing, "])")

        string, consumption = parsing.parse_string('""])')

        self.assertEqual(string, "")
        self.assertEqual(consumption.consumed, 2)
        self.assertEqual(consumption.trailing, "])")

        with self.assertRaises(ValueError):
            parsing.parse_string('asdf"')

        with self.assertRaises(ValueError):
            parsing.parse_string('"asdf\nfdsa"')

    def test_parse_list(self) -> None:
        values, consumption = parsing.parse_list('["foobar"])')

        self.assertEqual(values, ["foobar"])
        self.assertEqual(consumption.consumed, 10)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list("[])")

        self.assertEqual(values, [])
        self.assertEqual(consumption.consumed, 2)
        self.assertEqual(consumption.trailing, ")")

        values, consumption = parsing.parse_list('["foobar", "asdf"])')

        self.assertEqual(values, ["foobar", "asdf"])
        self.assertEqual(consumption.consumed, 18)
        self.assertEqual(consumption.trailing, ")")

        with self.assertRaises(ValueError):
            parsing.parse_list('"asdf", "fdsa"]')

        with self.assertRaises(ValueError):
            parsing.parse_list('["asdf" "fdsa"]')

        with self.assertRaises(ValueError):
            parsing.parse_list('["asdf", "fdsa"')

    def test_argument(self) -> None:
        argument, consumption = parsing.parse_argument('asdf="foobar")')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=["foobar"]))
        self.assertEqual(consumption.consumed, 13)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument('asdf=["foobar"])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=["foobar"]))
        self.assertEqual(consumption.consumed, 15)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument('asdf=["foobar", "baz"])')

        self.assertEqual(
            argument, parsing.Argument(name="asdf", values=["foobar", "baz"])
        )
        self.assertEqual(consumption.consumed, 22)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument("asdf=[])")

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[]))
        self.assertEqual(consumption.consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument('asdf="")')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.consumed, 7)
        self.assertEqual(consumption.trailing, ")")

        argument, consumption = parsing.parse_argument('asdf=[""])')

        self.assertEqual(argument, parsing.Argument(name="asdf", values=[""]))
        self.assertEqual(consumption.consumed, 9)
        self.assertEqual(consumption.trailing, ")")

        with self.assertRaises(ValueError):
            parsing.parse_argument("foo")

        with self.assertRaises(ValueError):
            parsing.parse_argument('foo"bar"')


if __name__ == "__main__":
    unittest.main()
