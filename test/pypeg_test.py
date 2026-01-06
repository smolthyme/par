import unittest
import sys, re
from io import StringIO

from par.pyPEG import _and, _not, ignore, keyword, parser, parse, parseLine, Name, Symbol


class TestKeyword(unittest.TestCase):
    def test_keyword_is_string(self):
        kw = keyword("class")
        self.assertIsInstance(kw, str)
        self.assertEqual(kw, "class")


class TestIgnore(unittest.TestCase):
    def test_ignore_stores_regex(self):
        ign = ignore(r"\s+")
        self.assertIsNotNone(ign.regex)
        self.assertTrue(ign.regex.match("   "))
    
    def test_ignore_with_flags(self):
        ign = ignore(r"[a-z]+", re.IGNORECASE)
        self.assertTrue(ign.regex.match("ABC"))


class TestAndNot(unittest.TestCase):
    def test_and_stores_object(self):
        pattern = keyword("test")
        and_obj = _and(pattern)
        self.assertEqual(and_obj.obj, pattern)
    
    def test_not_inherits_from_and(self):
        pattern = keyword("test")
        not_obj = _not(pattern)
        self.assertIsInstance(not_obj, _and)
        self.assertEqual(not_obj.obj, pattern)


class TestName(unittest.TestCase):
    def test_name_is_string(self):
        name = Name("test")
        self.assertIsInstance(name, str)
        self.assertEqual(name, "test")
    
    def test_name_has_line_and_file(self):
        name = Name("test")
        self.assertEqual(name.line, 0)
        self.assertEqual(name.file, "")


class TestSymbol(unittest.TestCase):
    def test_symbol_creation(self):
        sym = Symbol("test", "value")
        self.assertEqual(sym.__name__, "test")
        self.assertEqual(sym.what, "value")
        self.assertEqual(str(sym), "value")
    
    def test_symbol_call(self):
        sym = Symbol("test", ["a", "b"])
        self.assertEqual(sym(), ["a", "b"])
    
    def test_symbol_repr(self):
        sym = Symbol("test", "value")
        self.assertIn("Symbol<test, value>", repr(sym))
    
    def test_symbol_text_simple(self):
        sym = Symbol("test", "hello")
        self.assertEqual(sym.text, "hello")
    
    def test_symbol_text_nested(self):
        inner = Symbol("inner", "world")
        outer = Symbol("outer", ["hello ", inner])
        self.assertEqual(outer.text, "hello world")
    
    def test_symbol_find(self):
        inner = Symbol("target", "found")
        outer = Symbol("root", [Symbol("other", "x"), inner])
        result = outer.find("target")
        self.assertEqual(result, inner)
    
    def test_symbol_find_not_found(self):
        sym = Symbol("root", ["test"])
        self.assertIsNone(sym.find("missing"))
    
    def test_symbol_find_all(self):
        sym = Symbol("root", [
            Symbol("item", "1"),
            Symbol("other", [Symbol("item", "2")]),
            Symbol("item", "3")
        ])
        items = list(sym.find_all("item"))
        self.assertEqual(len(items), 3)
    
    def test_symbol_find_all_here(self):
        sym = Symbol("root", [
            Symbol("item", "1"),
            Symbol("other", [Symbol("item", "2")]),
            Symbol("item", "3")
        ])
        items = list(sym.find_all_here("item"))
        self.assertEqual(len(items), 2)
    
    def test_ascii_tree_leaf_with_value(self):
        """Leaf node with string value shows name: 'value'"""
        sym = Symbol("leaf", "hello")
        rendered = sym.utf8_tree_str()
        self.assertRegex(rendered, r"^leaf: 'hello'\n$")
    
    def test_ascii_tree_simple_nesting(self):
        """Parent with single child uses └── connector"""
        inner = Symbol("child", "data")
        outer = Symbol("parent", [inner])
        lines = outer.utf8_tree_str().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r"^parent$")
        self.assertRegex(lines[1], r"^└── child: 'data'$")
    
    def test_ascii_tree_multiple_children(self):
        """Multiple siblings: non-last use ├──, last uses └──"""
        a = Symbol("first", "1")
        b = Symbol("second", "2")
        c = Symbol("third", "3")
        root = Symbol("root", [a, b, c])
        lines = root.utf8_tree_str().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertRegex(lines[0], r"^root$")
        self.assertRegex(lines[1], r"^├── first: '1'$")
        self.assertRegex(lines[2], r"^├── second: '2'$")
        self.assertRegex(lines[3], r"^└── third: '3'$")
    
    def test_ascii_tree_deep_nesting(self):
        """Deep tree maintains proper indent continuation"""
        leaf = Symbol("leaf", "deep")
        mid = Symbol("mid", [leaf])
        root = Symbol("root", [mid])
        lines = root.utf8_tree_str().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertRegex(lines[0], r"^root$")
        self.assertRegex(lines[1], r"^└── mid$")
        self.assertRegex(lines[2], r"^    └── leaf: 'deep'$")
    
    def test_ascii_tree_complex_structure(self):
        """Complex tree with branches and continuation lines"""
        # Build:  root -> branch1 -> [leaf_a, leaf_b]
        #              -> branch2 -> [leaf_c]
        leaf_a = Symbol("leaf_a", "a")
        leaf_b = Symbol("leaf_b", "b")
        leaf_c = Symbol("leaf_c", "c")
        branch1 = Symbol("branch1", [leaf_a, leaf_b])
        branch2 = Symbol("branch2", [leaf_c])
        root = Symbol("root", [branch1, branch2])
        
        lines = root.utf8_tree_str().splitlines()
        self.assertEqual(len(lines), 6)
        self.assertRegex(lines[0], r"^root$")
        self.assertRegex(lines[1], r"^├── branch1$")
        self.assertRegex(lines[2], r"^│   ├── leaf_a: 'a'$")
        self.assertRegex(lines[3], r"^│   └── leaf_b: 'b'$")
        self.assertRegex(lines[4], r"^└── branch2$")
        self.assertRegex(lines[5], r"^    └── leaf_c: 'c'$")
    
    def test_ascii_tree_long_value_truncation(self):
        """Values over 60 chars are truncated with ellipsis"""
        long_val = "x" * 70
        sym = Symbol("node", long_val)
        rendered = sym.utf8_tree_str()
        self.assertRegex(rendered, r"^node: 'x{60}'\.\.\.\n$")
        

class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = parser()
    
    def test_parse_literal_string(self):
        result, rest = self.parser.parseLine("hello world", "hello")
        self.assertEqual(rest, "world")
    
    def test_parse_literal_string_fail(self):
        with self.assertRaises(SyntaxError):
            self.parser.parseLine("goodbye world", "hello")
    
    def test_parse_keyword(self):
        result, rest = self.parser.parseLine("class MyClass", keyword("class"))
        self.assertEqual(rest.strip(), "MyClass")
    
    def test_parse_keyword_fail(self):
        with self.assertRaises(SyntaxError):
            self.parser.parseLine("def func", keyword("class"))
    
    def test_parse_regex(self):
        pattern = re.compile(r"\d+")
        result, rest = self.parser.parseLine("123 abc", pattern)
        self.assertEqual(result[0], "123")
        self.assertEqual(rest.strip(), "abc")
    
    def test_parse_ignore(self):
        pattern = ignore(r"\d+")
        result, rest = self.parser.parseLine("123 abc", pattern)
        self.assertEqual(rest.strip(), "abc")
        self.assertEqual(len([r for r in result if isinstance(r, str)]), 0)
    
    def test_parse_tuple_sequence(self):
        pattern = ("hello", " ", "world")
        result, rest = self.parser.parseLine("hello world!", pattern, skipWS=False)
        self.assertEqual(rest, "!")
    
    def test_parse_tuple_with_repetition(self):
        pattern = (3, re.compile(r"\d"))
        result, rest = self.parser.parseLine("123 abc", pattern, skipWS=False)
        self.assertEqual(len([r for r in result if isinstance(r, str)]), 3)
    
    def test_parse_tuple_optional(self):
        pattern = (0, "optional", "required")
        result, rest = self.parser.parseLine("required thing", pattern)
        self.assertIn("thing", rest)
    
    def test_parse_tuple_zero_or_more(self):
        pattern = (-1, re.compile(r"\d"), " end")
        result, rest = self.parser.parseLine("123 end", pattern, skipWS=False)
        self.assertEqual(rest, "")
    
    def test_parse_tuple_one_or_more(self):
        pattern = (-2, re.compile(r"\d"), " end")
        result, rest = self.parser.parseLine("123 end", pattern, skipWS=False)
        self.assertEqual(rest, "")
    
    def test_parse_tuple_one_or_more_fail(self):
        pattern = (-2, re.compile(r"\d"), " end")
        with self.assertRaises(SyntaxError):
            self.parser.parseLine(" end", pattern, skipWS=False)
    
    def test_parse_list_alternatives(self):
        pattern = [keyword("class"), keyword("def")]
        result, rest = self.parser.parseLine("def func", pattern)
        self.assertEqual(rest.strip(), "func")
    
    def test_parse_list_alternatives_fail(self):
        pattern = [keyword("class"), keyword("def")]
        with self.assertRaises(SyntaxError):
            self.parser.parseLine("import sys", pattern)
    
    def test_parse_callable(self):
        def rule():
            return "test"
        result, rest = self.parser.parseLine("test value", rule)
        self.assertEqual(rest.strip(), "value")
    
    def test_parse_callable_with_name(self):
        def my_rule():
            return "test"
        result, rest = self.parser.parseLine("test", my_rule)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Symbol)
        self.assertEqual(result[0].__name__, "my_rule")
    
    def test_parse_and_lookahead(self):
        pattern = (_and("test"), "test")
        result, rest = self.parser.parseLine("test", pattern)
        self.assertEqual(rest, "")
    
    def test_parse_not_lookahead(self):
        pattern = (_not("bad"), "good")
        result, rest = self.parser.parseLine("good", pattern)
        self.assertEqual(rest, "")
    
    def test_parse_not_lookahead_fail(self):
        pattern = (_not("bad"), "bad")
        with self.assertRaises(SyntaxError):
            self.parser.parseLine("bad", pattern)
    
    def test_skip_whitespace(self):
        result, rest = self.parser.parseLine("  hello  world", "hello", skipWS=True)
        self.assertEqual(rest.strip(), "world")
    
    def test_no_skip_whitespace(self):
        with self.assertRaises(SyntaxError):
            self.parser.parseLine("  hello", "hello", skipWS=False)


class TestParserPackrat(unittest.TestCase):
    def test_packrat_caching(self):
        p = parser(p=True)
        pattern = re.compile(r"\d+")
        result1, rest1 = p.parseLine("123", pattern)
        # Second call should use cached result
        result2, rest2 = p.parseLine("123", pattern)
        self.assertEqual(result1, result2)
        self.assertEqual(rest1, rest2)


class TestParseLineFunctions(unittest.TestCase):
    def test_parseLine_function(self):
        result, rest = parseLine("hello world", "hello")
        self.assertEqual(rest.strip(), "world")
    
    def test_parseLine_with_packrat(self):
        result, rest = parseLine("123", re.compile(r"\d+"), packrat=True)
        self.assertEqual(result[0], "123")


class TestParse(unittest.TestCase):
    def test_parse_simple_grammar(self):
        def grammar():
            return (keyword("hello"), keyword("world"))
        
        class FakeInput:
            def __init__(self, lines):
                self.lines = lines
                self.index = 0
                self._filename = "test.txt"
                self._lineno = 0
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self.index < len(self.lines):
                    line = self.lines[self.index]
                    self.index += 1
                    self._lineno += 1
                    return line
                raise StopIteration
            
            def filename(self):
                return self._filename
            
            def lineno(self):
                return self._lineno
        
        source = FakeInput(["hello world\n"])
        result = parse(grammar, source)
        self.assertIsInstance(result, list)
    
    def test_parse_syntax_error(self):
        def grammar():
            return keyword("expected")
        
        class FakeInput:
            def __init__(self, lines):
                self.lines = lines
                self.index = 0
                self._filename = "test.txt"
                self._lineno = 0
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self.index < len(self.lines):
                    line = self.lines[self.index]
                    self.index += 1
                    self._lineno += 1
                    return line
                raise StopIteration
            
            def filename(self):
                return self._filename
            
            def lineno(self):
                return self._lineno
        
        source = FakeInput(["unexpected\n"])
        with self.assertRaises(SyntaxError) as cm:
            parse(grammar, source)
        self.assertIn("syntax error", str(cm.exception))


class TestComplexGrammar(unittest.TestCase):
    def test_nested_grammar(self):
        def value():
            return re.compile(r"\w+")
        
        def pair():
            return (value, "=", value)
        
        result, rest = parseLine("key=val", pair)
        self.assertEqual(rest, "")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__name__, "pair")
    
    def test_recursive_list(self):
        def item():
            return re.compile(r"\w+")
        
        def item_list():
            return (item, -1, (",", item))
        
        result, rest = parseLine("a,b,c", item_list)
        self.assertEqual(rest, "")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__name__, "item_list")
        self.assertEqual(len(list(result[0].find_all("item"))), 3)


class TestLineNumbers(unittest.TestCase):
    def test_lineNo_calculation(self):
        p = parser()
        p.textlen = 100
        p.restlen = 50
        p.lines = [(0, 1), (20, 2), (40, 3), (60, 4), (80, 5)]
        
        line = p.lineNo()
        self.assertGreaterEqual(line, 1)


if __name__ == '__main__':
    unittest.main()