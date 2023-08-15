"""Parser for file names which breaks them into their component parts"""

# BIG HUEG NOTE: This is a work in progress, and is not intended for use yet. 2023/07

from .pyPEG import *
import re
import types
from .__init__ import SimpleVisitor

rx = re.compile
ig = ignore

class FilonameGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
        
    def _get_rules(self):
        ## Cheats for return value repeats, similar to regex
        #  0 = ?         -1 = *          -2 = +
        def ws()        : return ig(r' +')          # All whitespace incl newline/return/half spaces etc

        def extension() : return ig(r'\.'), rx(r'((?:[\w\.]{1,5}){1,2})$')
        def meta()      : return [typer, tags]

        def tag_val()   : return rx(r'[\w]+\s*=\s*[\w\'"]+|\w+')
        def tags()      : return ig(r"\{"), -1, tag_val, ig(r"\}"), 0, ws
        def typer()     : return ig(r"\["), rx(r'\w+'),  ig(r"\]"), 0, ws

        def title()     : return rx(r'[^\{\.]+'), 0, ws

        def fname_spam(): return ig(r'[^a-z\s\.]{6,10}'), ws
        def sort_order(): return rx(r'[\-\d_!][\d\.\^]{0,5}')

        def prefix()    : return [fname_spam, sort_order]

        def filoname_parts(): return 0, prefix, title, -1, meta, -1,extension

        # Collect functions from this funct and add them to the peg_rules dict, for returning with the top level rule
        _peg_rules = {(k, v) for (k, v) in locals().items() if isinstance(v, types.FunctionType)}
        return _peg_rules, filoname_parts
    
    def parse(self, text, root=None, skipWS=False, **kwargs):
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

class FiloNameVisitor(SimpleVisitor):
    def __init__(self, grammar=None, filename=None):
        super().__init__(grammar, filename)

    # More elegant version of visit_filoname_parts() to roll logic into the return statement
    def visit_filoname_parts(self, node):
        prefix     = self.visit(node.find("prefix")) if node.find("prefix") else ""
        title      = node.find("title").text.strip()
        tags       = list(node.find_all("tag_val"))
        taglist    = " {" + ",".join([t.text.strip() for t in tags]) + "}" if tags != [] else ""
        extensions = node.find("extension").text if node.find("extension") else ""
        
        # Directories do not have extensions; Space before tags if there are any; Space after prefix if present
        return (prefix + " " if prefix else "") + title + (taglist if tags != [] else "") + ("." + extensions if extensions else "")

    def visit_title(self, node):
        return node.text.strip()
    
    def visit_sort_order(self, node):
        txt = node.text.strip()
        if txt[0] in "_!":
            return txt[0]
        else:
            order_float = float(txt)
            order_int = int(order_float)
            if order_float != order_int:
                return f"{order_float:02.1f}" if order_float != 0.0 else ""
            else:
                return f"{order_int:d}." if order_int != 0 else "" # {order_int:02d}

def parseFiloname(text, root=None, skipWS=False, **kwargs):
    g = FilonameGrammar()
    v = FiloNameVisitor(g)
    result, rest = g.parse(text, resultSoFar=[], skipWS=False)
    return v.visit(result)


from dataclasses import dataclass

@dataclass
class FileParts():
    """Simple dataclass to hold the parts of a filename."""
    sort   : str|None; title  : str; tags : str|None; extensions : str|None  # meta = str; prefix     : str

    def __str__(self):
        return f"{self.sort + ' ' if self.sort else ''}{self.title}{f' {{{self.tags}}}' if self.tags else ''}{'.' + self.extensions if self.extensions else ''}"

def get_filename_parts(fname_str: str) -> FileParts:
    g = FilonameGrammar()
    result, rest = g.parse(fname_str, resultSoFar=[], skipWS=False)

    rootnode   = result[0]
    sort_order = rootnode.find("sort_order").text.strip() if rootnode.find("sort_order") else ""
    title      = rootnode.find("title").text.strip()
    extensions = rootnode.find("extension").text if rootnode.find("extension") else ""
    tags       = list(rootnode.find_all("tag_val"))
    tags_str   = f'{",".join([t.text.strip() for t in tags])}' if len(tags) > 0 else ""

    return FileParts(sort=sort_order, title=title, tags=tags_str, extensions=extensions)
