.phony: test

test:
	/usr/bin/env python3 -m unittest --verbose src/test_parsing.py
