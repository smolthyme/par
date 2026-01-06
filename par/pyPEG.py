# 
# Based on YPL parser 1.5 by 'VB' -- Thanks!
# Hacked on by serpn subsequently

from __future__ import annotations
import sys, re
from typing import Union, Pattern, Callable, List, Tuple, Any, Generator, Optional, Dict, Iterator

print_trace = False # For debugging

word_regex = re.compile(r"\w+")
rest_regex = re.compile(r".*")

class keyword(str): pass

class ignore(object):
    def __init__(self, regex_text: str, *args):
        self._regex = re.compile(regex_text, *args)

    @property
    def regex(self) -> Pattern[str]:
        return self._regex

class _and(object):
    def __init__(self, something: ParsePattern):
        self._obj = something

    @property
    def obj(self) -> ParsePattern:
        return self._obj

class _not(_and): pass

# Type alias for parse patterns
ParsePattern = Union[
    Pattern[str],                      # compiled regex
    str,                               # literal text 
    keyword,                           # named word match
    ignore,                            # ignore specific text via regex
    _not,                              # negative lookahead
    _and,                              # positive lookahead
    int,                               # integer repetition count
    list,                              # alternatives (OR) - list of ParsePatterns
    tuple,                             # sequence - tuple of ParsePatterns and/or ints
    Callable[[], 'ParsePattern']       # callable returning another pattern
]

class Name(str):
    def __init__(self, *args):
        self.line = 0
        self.file = ""

class Symbol(list):
    def __init__(self, name: str, what: Any):
        self.__name__ = name
        self.what = what
        self.extend(what)
    
    def __call__(self) -> Any:
        return self.what
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"Symbol<{self.__name__}, {self.what[:16]}{'...' if len(self.what) > 40 else ''}>"
    
    def utf8_tree_str(self, prefix: str = "", connector: str = "") -> str:
        val = f": {self.what[:60]!r}..." if isinstance(self.what, str) and len(self.what) > 60 \
                else f": {self.what!r}" if isinstance(self.what, str) else ""
        kids = [n for n in self.what if isinstance(n, Symbol)] if isinstance(self.what, list) else []
        result = f"{prefix}{connector}{self.__name__}{val}\n"
        for i, c in enumerate(kids):
            is_last = (i == len(kids) - 1)
            new_prefix = prefix + ("" if not connector else ("    " if connector == "└── " else "│   "))
            result += c.utf8_tree_str(new_prefix, "└── " if is_last else "├── ")
        return result
    
    def find(self, name: str) -> Optional['Symbol']:
        """Find the first node with the given name."""
        for node in self.what:
            if not isinstance(node, str):
                if node.__name__ == name:
                    return node
                elif (r := node.find(name)):
                    return r
    
    def find_all(self, name: str) -> Generator['Symbol', None, None]:
        """Find all nodes with matching name anywhere in the decendants."""
        for node in self.what:
            if not isinstance(node, str):
                if node.__name__ == name:
                    yield node
                yield from node.find_all(name)
    
    def find_all_here(self, name: str) -> Generator['Symbol', None, None]:
        """Find all nodes with matching name in the immediate child nodes."""
        yield from (x for x in self.what if not isinstance(x, str) and x.__name__ == name)
    
    @property
    def text(self) -> str:
        return ''.join(node if isinstance(node, str) else node.text for node in self.what)

def skip(skipper, text: str, skipWS: bool, skipComments: Union[Callable, None]) -> str:
    t = text.lstrip() if skipWS else text
    while skipComments:
        try:
            skip, t = skipper.parseLine(t, skipComments, [], skipWS, None)
            if skipWS:
                t = t.lstrip()
        except:
            break
    return t

class parser(object):
    def __init__(self, another=False, p=False): 
        if not(another):
            self.skipper = parser(True, p)
            self.skipper.packrat = p
        else:
            self.skipper = self
        self.textlen = 0
        self.restlen = -1
        self.lines   = []
        self.memory  = {}
        self.packrat = p

    def parseLine(self, textline, pattern:ParsePattern, resultSoFar=[], skipWS=True, skipComments: Union[Callable, None]=None) -> Tuple[list, str]:
        """\
* textline     : text to parse
* pattern      : pyPEG language description
* resultSoFar  : parsing result so far (default: blank list [])
* skipWS       : should whitespace be skipped (default: True)
* skipComments : function which returns pyPEG for matching comments

- returns:    pyAST, textrest"""
        name = None
        _textline = textline
        _pattern = pattern

        def syntaxError(error=None):
            if self.packrat:
                self.memory[(len(_textline), id(_pattern))] = False
            raise SyntaxError(error)

        def Result(result: object, text: str) -> tuple:
            if __debug__ and print_trace:
                try:
                    if (pattern_name := getattr(_pattern, "__name__")) != "comment":
                        sys.stderr.write(f"match: {pattern_name}\n")
                except: pass

            if self.restlen == -1:
                self.restlen = len(text)
            else:
                self.restlen = min(self.restlen, len(text))
            
            results = resultSoFar
            if name and result:
                name.line = self.lineNo()
                results.append(Symbol(name, result))
            elif name:
                name.line = self.lineNo()
                results.append(Symbol(name, []))
            elif result:
                if type(result) is type([]):
                    results.extend(result)
                else:
                    results.extend([result])
            
            if self.packrat:
                self.memory[(len(_textline), id(_pattern))] = (results, text)
            
            return results, text        
        
        if self.packrat:
            try:
                result = self.memory[(len(textline), id(pattern))]
                if result:
                    return result
                else:
                    raise SyntaxError()
            except: pass

        if callable(pattern):
            if __debug__:
                if print_trace:
                    try:
                        if pattern.__name__ != "comment":
                            sys.stderr.write(f"testing with {pattern.__name__}: {textline[:40]}\n")
                    except: pass

            if pattern.__name__[0] != "_":
                name = Name(pattern.__name__)

            pattern = pattern()
            if callable(pattern):
                pattern = (pattern,)

        text = skip(self.skipper, textline, skipWS, skipComments)

        if isinstance(pattern, str):
            if text[:len(pattern)] == pattern:
                text = skip(self.skipper, text[len(pattern):], skipWS, skipComments)
                return Result(None, text)
            else:
                syntaxError()
        
        elif isinstance(pattern, keyword):
            if m := word_regex.match(text):
                if m.group(0) == pattern:
                    text = skip(self.skipper, text[len(pattern):], skipWS, skipComments)
                    return Result(None, text)
                else:
                    syntaxError()
            else:
                syntaxError(word_regex.pattern)
        
        elif isinstance(pattern, _not):
            try:
                r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            except:
                return resultSoFar, textline
            syntaxError()
        
        elif isinstance(pattern, _and):
            r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            return resultSoFar, textline
        
        elif isinstance(pattern, ignore):
            if m := pattern.regex.match(text):
                text = skip(self.skipper, text[len(m.group(0)):], skipWS, skipComments)
                return Result(None, text)
            else:
                syntaxError()
        
        elif isinstance(pattern, tuple):
            n = 1; result = []
            for p in pattern:
                if type(p) is type(0):
                    n = p
                elif isinstance(n, int):
                    if n > 0:
                        for i in range(n):
                            result, text = self.parseLine(text, p, result, skipWS, skipComments)
                    elif n == 0:
                        if text == "":
                            pass
                        else:
                            try:
                                newResult, newText = self.parseLine(text, p, result, skipWS, skipComments)
                                result, text = newResult, newText
                            except SyntaxError:
                                pass
                    elif n < 0:
                        found = False
                        while True:
                            try:
                                newResult, newText = self.parseLine(text, p, result, skipWS, skipComments)
                                result, text, found = newResult, newText, True
                            except SyntaxError:
                                break
                        if n == -2 and not(found):
                            syntaxError(f"{text} function={p}")
                    n = 1
            return Result(result, text)
        
        elif isinstance(pattern, list):
            result = []
            found = False
            for p in pattern:
                try:
                    result, text = self.parseLine(text, p, result, skipWS, skipComments)
                    found = True
                except SyntaxError:
                    pass
                if found:
                    break
            if found:
                return Result(result, text)
            else:
                syntaxError()
        
        elif isinstance(pattern, re.Pattern):
            # Handle compiled regex patterns
            if m := pattern.match(text):
                text = skip(self.skipper, text[len(m.group(0)):], skipWS, skipComments)
                return Result(m.group(0), text)
            else:
                syntaxError()
        
        else:
            raise SyntaxError(f"illegal type in grammar: {type(pattern)}")
        
        return resultSoFar, textline # Should never reach this point
    
    def lineNo(self) -> int:
        # NOTE TEST: This is a re-write of a function that was clearly broken. It... partially works?
        if not self.lines or self.restlen == -1:
            return -1  # Return -1 to indicate an invalid line number

        parsed = self.textlen - self.restlen
        left, right = 0, len(self.lines) - 1

        while left <= right:
            mid = (left + right) // 2
            if self.lines[mid][0] <= parsed:
                if mid + 1 < len(self.lines) and self.lines[mid + 1][0] > parsed:
                    return self.lines[mid][1]
                left  = mid + 1
            else:
                right = mid - 1

        return -1  # Return -1 if no valid line number is found

def parseLine(textline, pattern, resultSoFar = [], skipWS = True, skipComments = None, packrat = False) -> Tuple[List[Any], str]:
    p = parser(p=packrat)
    text = skip(p.skipper, textline, skipWS, skipComments)
    return p.parseLine(text, pattern, resultSoFar, skipWS, skipComments)

def parse(language, lineSource, skipWS = True, skipComments = None, packrat = False, lineCount = True):
    lines, lineNo = [], 0
    """\
* language     : pyPEG language description
* lineSource   : a fileinput.FileInput object
* skipWS:      : should whitespace be skipped (default: True)
* skipComments : function which returns pyPEG for matching comments
* packrat      : cache parse results at each position to avoid redundant work (packrat)
* lineCount    : add line number information to AST

- returns   pyAST"""
    
    orig = ""
    for line in lineSource:
        lines.append((len(orig), lineSource.filename(), lineSource.lineno() - 1))
        orig += line
    
    p = parser(p=packrat)
    p.textlen = len(orig)
    p.lines = [] if not lineCount else lines 
    
    try:
        text = skip(p.skipper, orig, skipWS, skipComments)
        result, text = p.parseLine(text, language, [], skipWS, skipComments)
        if text:
            raise SyntaxError()
    
    except SyntaxError as msg:
        textlen = len(orig)
        parsed = textlen - p.restlen
        textlen = 0
        nn, lineNo, file = 0, 0, ""
        for n, ld, l in lines:
            if n >= parsed:
                break
            else:
                lineNo = l
                nn    += 1
                file   = ld
        
        lineNo += 1
        nn -= 1
        lineCont = orig.splitlines()[nn]
        raise SyntaxError(f"syntax error in {file}:{lineNo} : {lineCont}")

    return result
