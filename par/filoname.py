"""Parser for file names which breaks them into their component parts"""

# BIG HUEG NOTE: This is a work in progress, and is not intended for use yet. 2023/07

import re, types
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .pyPEG import *

rx = re.compile
ig = ignore

@dataclass
class FileParts():
    """Simple dataclass to hold the parts of a filename, either as a definite set or set of regular expression."""
    title: str
    tags : List[str]      = field(default_factory=list)
    meta : Dict[str, str] = field(default_factory=dict)
    group: Optional[str]  = None
    exts : Optional[str]  = None
    sort : Optional[str]  = None
    
    def __str__(self):
        # Meta is a dict-like syntax
        meta_str = f" {{{','.join([f'{k}={v}' for k, v in self.meta.items()])}}}" if self.meta and self.meta != {} else ""
        
        # Tags are represented as hashtags
        tag_str   = "".join([f" #{tag}" for tag in self.tags])
        
        # e.g. "1.0 Title #tag1 [group] {meta1=val1,meta2=val2}.txt"
        return  f"{self.sort.strip(" .") + ' ' if self.sort else ''}{self.title}{tag_str}" \
                f"{f' [{self.group}]' if self.group else ''}{meta_str}" \
                f"{f'.{self.exts}' if self.exts  else ''}"
    
    def __eq__(self, ck_parts: 'FileParts') -> bool:
        """Checks if a file's properties match a given pattern.
        Returns True if they ALL match in their respective way."""
        
        simple_ext_chars_re = re.compile(r'^[\.a-z]+$')
        
        if ck_parts.title and not re.match(ck_parts.title, self.title):
            return False
        elif ck_parts.exts and self.exts:
            # if they only consist of [\.a-z] characters, we can do a simple comparison
            if re.match(simple_ext_chars_re, ck_parts.exts) and ck_parts.exts == self.exts:
                return True
            elif re.match(ck_parts.exts, self.exts):
                return True
        
        elif ck_parts.group and self.group and not re.match(ck_parts.group, self.group):
            return False
        elif ck_parts.tags and not any([tag in self.tags for tag in ck_parts.tags]):
            return False
        # if ck_parts.meta and not all([self.meta.get(k) == v for k, v in ck_parts.meta.items()]):
        #     return False
        
        elif ck_parts.sort and self.sort and ck_parts.sort == self.sort:
            return True
        
        return True
    
    def __hash__(self):
        return hash(self.title)
    
    def __lt__(self, other):
        if not isinstance(other, FileParts):
            return NotImplemented
        elif self.sort and other.sort:
            return self.sort < other.sort
        elif self.sort and not hasattr(other, 'sort'):
            return self.sort < other.title
        else:
            return self.title < other.title

class FilonameGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)

    def _get_rules(self):
        # Whitespace
        def ws(): return ig(r'\s+')

        # Word (for tags, keys, etc)
        def word(): return rx(r"[\w\-']+")

        # Date prefix: YYYY.MM.DD- or YYYY-MM-DD_
        def date_prefix(): return ig(r'\d{4}[\.\-]\d{2}[\.\-]\d{2}[-_ ]+'), 0, ws

        # Sort prefix: e.g. 01., 3.0, 3, ^., ^, 1.Lantè's
        def sort_order():
            # Capture ^_ special chars or number (with optional . or .0), but don't include trailing dot in group
            return rx(r'((?:[\^_])|(?:\d+(?:\.\d+)?))\.?'), 0, ws

        # Prefix: date and/or sort
        def prefix(): return 0, date_prefix, 0, sort_order

        # Title: everything up to group, meta, extension, or end
        def title():
            # Stop at: {, [, #, ., /, or end
            return rx(r"[^\{\[]+?(?=(?:\.[a-zA-Z\d]{2,5}){1,2}\b|[\#\[\{]|/|$)"), 0, ws

        # Tag: #tag
        def tag(): return word
        def hashtags(): return ig(r"\#"), tag, -1, ig(r"[,; ]")

        # Group: [group]
        def group_name(): return word
        def group(): return ig(r"\[ *"), group_name, ig(r" *\]"), 0, ws

        # Meta: {key=val}
        def key(): return word
        def key_n_val(): return key, ig(r'\s*[=:]\s*'), word, -1, ig(r"[,; ]")
        def metas(): return ig(r"\{"), -1, [key_n_val, ws], ig(r"\}"), 0, ws

        # Extension: .ext or .ext.ext
        def extension():
            # Accepts .md.txt, .card.yaml, .svg, .ttf, etc.
            return ig(r'\.'), rx(r'([a-zA-Z\d]{2,5}(?:\.[a-zA-Z\d]{2,5})?)$')

        # Main rule: meta must come before extension!
        def filoname_parts():
            return 0, prefix, title, 0, group, 0, hashtags, 0, metas, 0, extension

        _peg_rules = {(k, v) for (k, v) in locals().items() if isinstance(v, types.FunctionType)}
        return _peg_rules, filoname_parts

    def parse(self, text, root=None, skipWS=False, **kwargs):
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

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

    title      = rootnode.find("title").text.strip()
    sort_order = rootnode.find("sort_order").text.strip() if rootnode.find("sort_order") else None
    tags       = [tag.text for tag in rootnode.find_all("tag")]
    group      = rootnode.find("group_name").text if rootnode.find("group") else None  # FIXME: 'Group' is the wrong word for this
    meta_dict  = {match[0].text: match[1].text for match in rootnode.find_all("key_n_val")}
    extensions = rootnode.find("extension").text if rootnode.find("extension") else None
    
    return FileParts(sort=sort_order, title=title, group=group, tags=tags, meta=meta_dict , exts=extensions)

def normalize_alpha(string: str) -> float:
    """Returns a float value for alphabetic sorting using all alphabetic characters in the string."""
    return sum(
        (ord(char) - ord('a') + 1) / (26 ** i)
        for i, char in enumerate(c for c in string.strip().lower() if c.isalpha())
    )

def file_sort_init(sort_var:Optional[None|str], title:str, sort_default=1.0) -> float:
    """While the filename parser is good, the sort variable sometimes contains strange values.
        This function is a helper to ensure that sort is always a float"""
    first = -888.0  ; firstchars = "^!"
    last  =  888.0  ; lastchars  = "_z"
    
    if not sort_var and title != "": return normalize_alpha(title)
    elif not sort_var              : return sort_default
    elif sort_var[0] in firstchars : return first
    elif sort_var[0] in lastchars  : return last
    else:
        try:
            floaty = float(sort_var)
            return floaty / 10
        except ValueError:           return sort_default