# YPL parser 1.5

# written by VB.

import re
import sys

from typing import Union, Pattern, Callable, List, Tuple, Any, Generator, Optional
from dataclasses import dataclass

class keyword(str): pass

class _and(object):
    def __init__(self, something: 'ParsePattern'):
        self._obj = something

    @property
    def obj(self) -> 'ParsePattern':
        return self._obj

class _not(_and): pass

class ignore(object):
    def __init__(self, regex_text: str, *args):
        self._regex = re.compile(regex_text, *args)

    @property
    def regex(self) -> Pattern[str]:
        return self._regex


class Name(str):
    def __init__(self, *args):
        self.line = 0
        self.file = ""

ParsePattern = Union[
    Pattern[str],                      # compiled regex
    str,                               # literal text 
    keyword,                           # named word match
    _not,                              # negative lookahead
    _and,                              # positive lookahead
    ignore,                            # ignore specific text via regex
    int,                               # integer repetition count
    Tuple["int | ParsePattern", ...],  # tuple with optional integer repetition counts
    List["ParsePattern"],              # alternatives (OR)
    Callable[[], "ParsePattern"]       # callable returning another pattern
]

class Symbol(list):
    def __init__(self, name: str, what: Any):
        self.__name__ = name
        self.what = what
        self.extend(what)
    
    def __call__(self) -> Any:
        return self.what
    
    def __repr__(self) -> str:
        return f"Symbol<{self.__name__}>: {self.what}"
    
    def render(self, index: int = 0) -> str:
        indent = f"{' ' * 2 * index}"
        if isinstance(self.what, str):
            return f"{indent}{self.__name__}:{self.what}\n"
        buf = [f"{indent}{self.__name__}:\n"]
        buf.extend(
            f"{' ' * 2 * (index + 1)}:{x}\n" if isinstance(x, str) else x.render(index + 1)
            for x in self.what
        )
        return ''.join(buf)
    
    def find(self, name: str) -> Optional['Symbol']:
        for x in self.what:
            if not isinstance(x, str):
                if x.__name__ == name:
                    return x
                elif (r := x.find(name)):
                    return r
        return None
    
    def find_all(self, name: str) -> Generator['Symbol', None, None]:
        for x in self.what:
            if not isinstance(x, str):
                if x.__name__ == name:
                    yield x
                yield from x.find_all(name)
    
    def find_all_here(self, name: str) -> Generator['Symbol', None, None]:
        yield from (x for x in self.what if not isinstance(x, str) and x.__name__ == name)
    
    @property
    def text(self) -> str:
        return ''.join(node if isinstance(node, str) else node.text for node in self.what)


word_regex = re.compile(r"\w+")
rest_regex = re.compile(r".*")

print_trace = False

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
        self.restlen = -1 
        if not(another):
            self.skipper = parser(True, p)
            self.skipper.packrat = p
        else:
            self.skipper = self
        self.lines = []
        self.textlen = 0
        self.memory = {}
        self.packrat = p

    # parseLine():
    # * textline:     text to parse
    # * pattern:      pyPEG language description
    # * resultSoFar:  parsing result so far (default: blank list [])
    # * skipWS:       Flag if whitespace should be skipped (default: True)
    # * skipComments: Python functions returning pyPEG for matching comments
    #   
    #   - returns:    pyAST, textrest
    #   - raises:     SyntaxError(reason) if textline is detected not being in language described by pattern
    #                 SyntaxError(reason) if pattern is an illegal language description

    def parseLine(self, textline, pattern:ParsePattern, resultSoFar=[], skipWS=True, skipComments: Union[Callable, None]=None) -> Tuple[list, str]:
        name = None
        _textline = textline
        _pattern = pattern

        def R(result: object, text: str) -> tuple:
            if __debug__ and print_trace:
                try:
                    if (pattern_name := getattr(_pattern, "__name__")) != "comment":
                        sys.stderr.write(f"match: {pattern_name}\n")
                except: pass

            if self.restlen == -1:
                self.restlen = len(text)
            else:
                self.restlen = min(self.restlen, len(text))
            
            res = resultSoFar
            if name and result:
                name.line = self.lineNo()
                res.append(Symbol(name, result))
            elif name:
                name.line = self.lineNo()
                res.append(Symbol(name, []))
            elif result:
                if type(result) is type([]):
                    res.extend(result)
                else:
                    res.extend([result])
            
            if self.packrat:
                self.memory[(len(_textline), id(_pattern))] = (res, text)
            
            return res, text

        def syntaxError(error=None):
            if self.packrat:
                self.memory[(len(_textline), id(_pattern))] = False
            raise SyntaxError(error)


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
        pattern_type = type(pattern)

        if type(pattern) is str:
            if text[:len(pattern)] == pattern:
                text = skip(self.skipper, text[len(pattern):], skipWS, skipComments)
                return R(None, text)
            else:
                syntaxError()

        elif type(pattern) is keyword:
            m = word_regex.match(text)
            if m:
                if m.group(0) == pattern and isinstance(pattern, str):
                    text = skip(self.skipper, text[len(pattern):], skipWS, skipComments)
                    return R(None, text)
                else:
                    syntaxError()
            else:
                syntaxError(word_regex.pattern)

        elif type(pattern) is _not:
            try:
                r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            except:
                return resultSoFar, textline
            syntaxError()

        elif type(pattern) is _and:
            r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            return resultSoFar, textline

        elif type(pattern) in (type(word_regex), ignore):
            if type(pattern) is ignore and hasattr(pattern, "regex"):
                    pattern = pattern.regex
            if isinstance(pattern, Pattern) and (m := pattern.match(text)):
                text = skip(self.skipper, text[len(m.group(0)):], skipWS, skipComments)
                if pattern_type is ignore:
                    return R(None, text)
                else:
                    return R(m.group(0), text)
            else:
                #syntaxError(pattern.pattern+' text='+repr(text))
                syntaxError()

        elif type(pattern) is tuple:
            result = []
            n = 1
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
                            #syntaxError()
                    n = 1
            return R(result, text)

        elif type(pattern) is list:
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
                return R(result, text)
            else:
                syntaxError()

        else:
            raise SyntaxError(f"illegal type in grammar: {pattern_type}")
        
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

# plain module API

def parseLine(textline, pattern, resultSoFar = [], skipWS = True, skipComments = None, packrat = False) -> Tuple[List[Any], str]:
    p = parser(p=packrat)
    text = skip(p.skipper, textline, skipWS, skipComments)
    return p.parseLine(text, pattern, resultSoFar, skipWS, skipComments)

# parse():
# * language     : pyPEG language description
# * lineSource   : a fileinput.FileInput object
# * skipWS:      :  Flag if whitespace should be skipped (default: True)
# * skipComments : Python function which returns pyPEG for matching comments
# * packrat      : use memoization
# * lineCount    : add line number information to AST
#   
#   - returns    pyAST
#   - raises     SyntaxError(reason), if a parsed line is not in language
#                SyntaxError(reason), if the language description is illegal

def parse(language, lineSource, skipWS = True, skipComments = None, packrat = False, lineCount = True):
    lines, lineNo = [], 0

    # while callable(language):    # Fairly sure this is handled in the parser anyway.
        # language = language()    # Remove: Late 2025

    orig = ""
    for line in lineSource:
        lines.append((len(orig), lineSource.filename(), lineSource.lineno() - 1))
        orig += line

    textlen = len(orig)

    try:
        p = parser(p=packrat)
        p.textlen = len(orig)
        if lineCount:
            p.lines = lines
        else:
            p.lines = []
        text = skip(p.skipper, orig, skipWS, skipComments)
        result, text = p.parseLine(text, language, [], skipWS, skipComments)
        if text:
            raise SyntaxError()

    except SyntaxError as msg:
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
