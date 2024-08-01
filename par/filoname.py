"""Parser for file names which breaks them into their component parts"""

# BIG HUEG NOTE: This is a work in progress, and is not intended for use yet. 2023/07

import re, types
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .pyPEG import *
from .__init__ import SimpleVisitor

rx = re.compile
ig = ignore

@dataclass
class FileParts():
    """Simple dataclass to hold the parts of a filename, either as a definite set or set of regular expression."""
    title: str
    tags: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    group: Optional[str] = None
    exts: Optional[str] = None
    sort: Optional[str] = None
    
    def __str__(self):
        # Meta is a dict-like syntax
        meta_str = f" {{{','.join([f'{k}={v}' for k, v in self.meta.items()])}}}" if self.meta and self.meta != {} else ""
        
        # Tags are represented as hashtags
        tag_str   = "".join([f" #{tag}" for tag in self.tags])
        
        # e.g. "1.0 Title #tag1 [group] {meta1=val1,meta2=val2}.txt"
        return  f"{self.sort + ' ' if self.sort else ''}{self.title}{tag_str}" \
                f"{f' [{self.group}]' if self.group else ''}{meta_str}" \
                f"{f'.{self.exts}' if self.exts  else ''}"
    
    def __eq__(self, ck_parts) -> bool:
        """Checks if a file's properties match a given pattern.
        Returns True if they ALL match in their respective way."""
        
        simple_ext_chars_re = re.compile(r'^[\.a-z]+$')
        
        
        if ck_parts.title and not re.match(ck_parts.title, self.title):
            return False
        if ck_parts.exts and self.exts:
            # if they only consist of [\.a-z] characters, we can do a simple comparison
            if re.match(simple_ext_chars_re, ck_parts.exts) and ck_parts.exts == self.exts:
                return True
            elif re.match(ck_parts.exts, self.exts):
                return True
        
        if ck_parts.group and self.group and not re.match(ck_parts.group, self.group):
            return False
        if ck_parts.tags and not any([tag in self.tags for tag in ck_parts.tags]):
            return False
        if ck_parts.meta and not all([self.meta.get(k) == v for k, v in ck_parts.meta.items()]):
            return False
        
        if ck_parts.sort and self.sort and ck_parts.sort == self.sort:
            return True
        
        return True


class FilonameGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
    
    def _get_rules(self):
        ## Cheats for return value repeats, similar to regex
        #  0 = ?         -1 = *          -2 = +
        def ws()        : return ig(r'\s+')         # All whitespace incl newline/return/half spaces etc
        def word()      : return rx(r'\w+')         # Word character
        #return rx(r'[\w]+\s*=\s*[\w\'"]+')
        
        def fname_spam(): return ig(r'[^a-z\s\.]{6,10}'), ws
        def sort_order(): return rx(r'[\-\d_!][\d\.\^]{0,5}')
        def prefix()    : return [fname_spam, sort_order]
        
        def title()     : return rx(r'[^\[\{\.]+'), 0, ws
        
        def tag()       : return word
        def hashtags()  : return ig(r"\#"), tag, -1, ig(r"[,; ]")
        
        def group_name(): return word
        def group()     : return ig(r"\[ *"), group_name,  ig(r" *\]"), 0, ws
        
        def key()       : return word
        def key_n_val() : return key, ig(r'\s*[=:]\s*'), word, -1, ig(r"[,; ]")
        def metas()     : return ig(r"\{"), -1, [key_n_val, ws], ig(r"\}"), 0, ws
        
        def extension() : return ig(r'\.'), rx(r'((?:[\w\.]{1,5}){1,2})$')
        
        def filoname_parts(): return 0, prefix, title, 0, group, 0, hashtags, 0, metas, -1, extension
        
        # Collect functions from this funct and add them to the peg_rules dict, for returning with the top level rule
        _peg_rules = {(k, v) for (k, v) in locals().items() if isinstance(v, types.FunctionType)}
        return _peg_rules, filoname_parts
    
    def parse(self, text, root=None, skipWS=False, **kwargs):
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

class FiloNameVisitor(SimpleVisitor):
    def __init__(self, grammar=None, filename=None):
        super().__init__(grammar, filename)
    
    # More elegant version of visit_filoname_parts() to roll logic into the return statement
    # def visit_filoname_parts(self, node):
    #     prefix     = self.visit(node.find("prefix")) if node.find("prefix") else ""
    #     title      = node.find("title").text.strip()
    #     typen       = list(node.find_all("group_name"))
    #     type_str   = f"[{','.join([t.text.strip() for t in typen])}]" if typen != [] else ""
    #     meta       = list(node.find_all("key_n_val"))
    #     meta_info    = " {" + ",".join([t.text.strip() for t in meta]) + "}" if meta != [] else ""
    #     extensions = node.find("extension").text if node.find("extension") else ""
    
    #     # Directories do not have extensions; Space before tags if there are any; Space after prefix if present
    #     return (prefix + " " if prefix else "") + title + type_str + (meta_info if meta != [] else "") + ("." + extensions if extensions else "")
    
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

def get_filename_parts(fname_str: str) -> FileParts:
    """Parse a filename string into its component parts if possible.
    There are MANY valid filenames which will not parse, this is acceptable.
    In the case that parsing is not possible, just use a FileParts object with the filename."""
    
    try:
        g = FilonameGrammar()
        result, rest = g.parse(fname_str, resultSoFar=[], skipWS=False)
    except:
        return FileParts(title=fname_str)
    
    rootnode   = result[0]
    sort_order = rootnode.find("sort_order").text.strip() if rootnode.find("sort_order") else None
    title      = rootnode.find("title").text.strip()
    tags       = [tag.text for tag in rootnode.find_all("tag")]
    group      = rootnode.find("group_name").text if rootnode.find("group") else None  # FIXME: 'Group' is the wrong word for this
    meta_dict  = {match[0].text: match[1].text for match in rootnode.find_all("key_n_val")}
    extensions = rootnode.find("extension").text if rootnode.find("extension") else None
    
    return FileParts(sort=sort_order, title=title, group=group, tags=tags, meta=meta_dict , exts=extensions)
