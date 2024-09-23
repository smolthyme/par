"""Uuuultra-simple SCSS parser and visitor"""

# Proof-of-concept -- giving reasonable access to selectors and properties

from .pyPEG import *
import re
import types
from .__init__ import SimpleVisitor

rx = re.compile
ig = ignore

class SCSSGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
        
    def _get_rules(self):
        ## Cheats for return value repeats, similar to regex
        #  0 = ?         -1 = *          -2 = +

        def ws()               : return ig(r'\s+')          # All whitespace
        def space()            : return ig(r'[ \t]+')       # Usual horizontal spacers
        def eol()              : return ig(r'\r\n|\r|\n')   # End of line(s)

        def comment_ln()       : return rx(r'//.*'), eol
        def comment_bk()       : return rx(r'/\*.*?\*/')

        def css_at_rule_name() : return rx(r'(@[a-z-]+)')
        def css_at_rule_query(): return rx(r'([^;{]+?)(?=\s*[{;])', re.ASCII)
        def css_at_rule()      : return css_at_rule_name, 0, css_at_rule_query

        def css_selector()     : return rx(r'([\.\#\w\_\-\=\~\*\^\>\?\:\(\)\[\]\'\" ]+)')
        def css_selectors()    : return -2, [css_at_rule, css_selector, ig(",")]

        def css_block()        : return -2, css_selectors, ig(r'\{'), css_block_content, ig(r'\}')
        def css_block_content(): return -1, [css_block, css_property]

        def css_prop_name()    : return rx(r'([\*\w\-]+)', re.ASCII)  # the \* might be useless, check googles code
        def css_prop_value()   : return rx(r'([\w\!\.,\$\%\#\+\-\(\)\'\"\:\/\* ]+)')
        def css_property()     : return css_prop_name, ig(r'\s*:\s*'), css_prop_value, 0, ig(r';')

        def scss_doc()         : return -1, [ ws, css_block]
    
        peg_rules = {}
        for k, v in ((x, y) for (x, y) in list(locals().items()) if isinstance(y, types.FunctionType)):
            peg_rules[k] = v

        return peg_rules, scss_doc
    
    def parse(self, text, root=None, skipWS=False, **kwargs):
        # if not text:
        #     text = '\n'
        # elif text[-1] not in ('\r', '\n'):
        #     text = text + '\n'
        # text = re.sub('\r\n|\r', '\n', text)
        
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

class SCSSVisitor(SimpleVisitor):
    def __init__(self, grammar=None, filename=None):
        super().__init__(grammar, filename)

    def visit_css_selectors(self, node):
        return ", ".join([self.visit(n) for n in node])

    def visit_css_block_content_begin(self, node):
        return " {"

    def visit_css_block_content(self, node, idnt="\n  "):
        str = ""
        for n in node.find_all_here('css_property'):
            _name  = n.find('css_prop_name' ).text
            _value = n.find('css_prop_value').text     
            str += f"{idnt}{_name}: {_value};"
        for z in node.find_all_here('css_block'):
            if str != "": str += "\n"
            for p in self.visit(z).splitlines():
                str += f"{idnt}{p}" 
        return str
    
    def visit_css_block_content_end(self, node):
        return "\n}\n"

def parseSCSSText(text: str):
    g = SCSSGrammar()
    v = SCSSVisitor(g)
    result, rest = g.parse(text, skipWS=True)
    return v.visit(result, root=True)
