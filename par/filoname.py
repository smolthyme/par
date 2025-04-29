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
        ## Cheats for return value repeats, similar to regex
        #  0 = ?         -1 = *          -2 = +
        def ws()        : return ig(r'\s+')         # All whitespace incl newline/return/half spaces etc
        def word()      : return rx(r'[\w\-]+')         # Word character
        
        # Avoid the title getting filled with spam from some software/cameras etc
        def fname_spam(): return ig(r'[^a-z\s\.]{6,10}'), ws
        # Looks for a numerical value to sort things by if its before the title
        def sort_order(): return rx(r'(?!\d+\.\w+$)[\-\d_!][\d\.\^]{0,5}')
        def prefix()    : return [fname_spam, sort_order]
        
        # Try to find the title by avoiding extensions and tags (Can we do it without?)
        def title()     : return rx(r'[^\{\[]+?(?=(\.[a-zA-Z\d]{2,5}){1,2}\b|/|[\[\{])'), 0, ws
        
        def tag()       : return word
        def hashtags()  : return ig(r"\#"), tag, -1, ig(r"[,; ]")
        
        def group_name(): return word
        def group()     : return ig(r"\[ *"), group_name,  ig(r" *\]"), 0, ws
        
        def key()       : return word
        def key_n_val() : return key, ig(r'\s*[=:]\s*'), word, -1, ig(r"[,; ]")
        def metas()     : return ig(r"\{"), -1, [key_n_val, ws], ig(r"\}"), 0, ws
        
        def extension() : return ig(r'\.'), rx(r'(\w{1,5}(?:\.\w{1,5})?)$')
        
        def filoname_parts(): return 0, prefix, title, 0, group, 0, hashtags, 0, metas, 0, extension
        
        # Collect functions from this funct and add them to the peg_rules dict, for returning with the top level rule
        _peg_rules = {(k, v) for (k, v) in locals().items() if isinstance(v, types.FunctionType)}
        return _peg_rules, filoname_parts
    
    def parse(self, text, root=None, skipWS=False, **kwargs):
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

def normalize_alpha(string) -> float:
    """Normalizes a string to a float value based on the sum of the alphabetical positions of its characters."""
    return sum((ord(char.lower()) - ord('a') + 1) for char in string if char.isalpha()) / len(string)

def file_sort_init(sort_var, title:str, sort_default=1.0) -> float:
    """While the filename parser is good, the sort variable sometimes contains strange values.
        This function is a helper to ensure that sort is always a float"""
    first = -888.0  ; firstchars = "^!"
    last  =  888.0  ; lastchars  = "_zv"
    
    if not sort_var                : return sort_default
    if not sort_var and title != "": return normalize_alpha(title)
    elif sort_var[0] in firstchars : return first
    elif sort_var[0] in lastchars  : return last
    else:
        try:                         return float(sort_var)
        except ValueError:           return sort_default

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
