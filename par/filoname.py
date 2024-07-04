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
        def ws()        : return ig(r'\s+')         # All whitespace incl newline/return/half spaces etc
        def word()      : return rx(r'\w+')         # Word character
        #return rx(r'[\w]+\s*=\s*[\w\'"]+')
        
        def fname_spam(): return ig(r'[^a-z\s\.]{6,10}'), ws
        def sort_order(): return rx(r'[\-\d_!][\d\.\^]{0,5}')
        def prefix()    : return [fname_spam, sort_order]
        
        def title()     : return rx(r'[^\{\.]+'), 0, ws
        
        def tag()       : return word
        def hashtags()  : return ig(r"\#"), tag, -1, ig(r"[,; ]")
        
        def group_name(): return word
        def group()     : return ig(r"\["), group_name,  ig(r"\]"), 0, ws
        
        def key()       : return word
        def key_n_val() : return key, ig(r'\s*[=:]\s*'), word, -1, ig(r"[,; ]")
        def metas()     : return ig(r"\{"), -1, [key_n_val, ws], ig(r"\}"), 0, ws
        
        def extension() : return ig(r'\.'), rx(r'((?:[\w\.]{1,5}){1,2})$')
        
        def filoname_parts(): return 0, prefix, title, 0, hashtags, 0, group, 0, metas, -1, extension
        
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


from dataclasses import dataclass

@dataclass
class FileParts():
    """Simple dataclass to hold the parts of a filename."""
    sort   : str|None; title  : str; tags : list; meta : dict; extensions : str ; group: str; #prefix     : str
    
    def __str__(self):
        meta_str = f" {{{','.join([f'{k}={v}' for k, v in self.meta.items()])}}}" if self.meta and self.meta != {} else ""
        tag_str   = "".join([f"#{tag} " for tag in self.tags])
        return f"{self.sort + ' ' if self.sort else ''}{self.title}{tag_str}{f"[{self.group}]" if self.group != '' else ''}{meta_str}{'.' + self.extensions if self.extensions not in ["", "/"] else ''}"

def get_filename_parts(fname_str: str) -> FileParts:
    g = FilonameGrammar()
    result, rest = g.parse(fname_str, resultSoFar=[], skipWS=False)
    
    rootnode   = result[0]
    sort_order = rootnode.find("sort_order").text.strip() if rootnode.find("sort_order") else ""
    title      = rootnode.find("title").text.strip()
    extensions = rootnode.find("extension").text if rootnode.find("extension") else ""
    group      = rootnode.find("group_name").text.strip() if rootnode.find("group_name") else ""
    tags       = [tag.text for tag in rootnode.find_all("tag")]
    meta_dict  = {match[0].text: match[1].text for match in rootnode.find_all("key_n_val")}
    
    return FileParts(sort=sort_order, title=title, group=group, tags=tags, meta=meta_dict , extensions=extensions)

class fileoFilter():
    """Uses a registry to filter files based on their parts.
        Classes register themselves with a decorator. The decorator specifies the filter criteria.
        Criteria include: fname regex, extension, group and meta info matching."""
    
    def __init__(self):
        self.filters = {}
    
    def register(self, fname_re=None, ext=None, group=None, meta=None):
        def decorator(cls):
            self.filters[cls.__name__] = (cls, (fname_re, ext, group, meta))
            return cls
        return decorator
    
    def check_file(self, fileparts: FileParts):
        for name, (cls, (fname_re, ext, group, meta)) in self.filters.items():
            if  (fname_re is None or re.match(fname_re, fileparts.title)) and \
                (ext is None or fileparts.extensions == ext) and \
                (group is None or fileparts.group == group) and \
                (meta is None or all(fileparts.meta.get(k) == v for k, v in meta.items())):
                
                return cls
        return None