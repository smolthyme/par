#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: limodou@gmail.com
# This program is based on pyPEG
#
# license: BSD

from .pyPEG import *

import re, unicodedata
from html.entities import name2codepoint

HTML_NAMED_ENTITY_RE= re.compile(r'&(%s);' % '|'.join(name2codepoint))
HTML_HEX_ENTITY_RE  = re.compile(r'&#x([\da-fA-F]+);')
HTML_DECIMAL_RE     = re.compile(r'&#(\d+);')
QUOTE_CHARS_RE      = re.compile(r'[\'\"]+')
DUPLICATE_DASH_RE   = re.compile(r'--+')
NUM_SEP_COMMAS_RE   = re.compile(r'(?<=\d),(?=\d)')
VALID_SLUG_RE       = re.compile(r'^[-a-zA-Z0-9]+$')

__author__ = 'limodou'
__author_email__ = 'limodou@gmail.com'
__url__ = 'https://github.com/limodou/par'
__license__ = 'BSD'
__version__ = '1.3.4'

_ = re.compile

class SimpleVisitor(object):
    def __init__(self, grammar=None, filename=None):
        self.grammar = grammar
        self.filename = filename
    
    def visit(self, nodes: Symbol|list[Symbol], root=False) -> str:
        buf = []
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        if root:
            if (method := getattr(self, '__begin__', None)):
                buf.append(method())
        for node in nodes:
            if isinstance(node, str):
                buf.append(node)
            else:
                if (method := getattr(self, 'before_visit', None)):
                    buf.append(method(node))
                if (method := getattr(self, f'visit_{node.__name__}_begin', None)):
                    buf.append(method(node))
                if (method := getattr(self, f'visit_{node.__name__}', None)):
                    buf.append(method(node))
                else:
                    if isinstance(node.what, str):
                        buf.append(node.what)
                    else:
                        buf.append(self.visit(node.what))
                if (method := getattr(self, f'visit_{node.__name__}_end', None)):
                    buf.append(method(node))
                if (method := getattr(self, 'after_visit', None)):
                    buf.append(method(node))
        if root:
            if (method := getattr(self, '__end__', None)):
                buf.append(method())
        return ''.join(buf)

class HTMLVisitor(SimpleVisitor):
    tag_class = {}
    
    # Pretty sure filename can be removed
    def __init__(self, grammar=None, filename=None, tag_class=None):
        super(HTMLVisitor, self).__init__(grammar, filename)
        #self.tag_class = tag_class or self.__class__.tag_class
        self._template = '<html><head><title>{title}</title></head><body>{body}</body></html>'
    
    def tag(self, tag: str, child='', attrs='', enclose=0, newline=True, **kwargs) -> str:
        """HTML tag generator
        Args:
          * child -- complete tag content
          * attrs -- additional attributes
          * enclose -- 1: self-closing tag, 2: open+close tag, 3: close tag
        """
        
        kw = kwargs.copy()
        _class = kw.pop('_class', '')
        _class += ' ' + kw.pop('class', '')
        tag_class = ''#self.tag_class.get(tag, '')

        if tag_class:
            kw['class'] = f"{tag_class[1:]} {_class.lstrip()}" if tag_class.startswith('+') else tag_class
        else:
            kw['class'] = _class.strip()

        kwattrs = ' '.join(f'{x}="{y}"' for x, y in sorted(kw.items()) if y)
        kwattrs = f' {kwattrs}{f" {attrs}" if attrs != '' else ""}' if kwattrs else attrs
        nline = '\n' if newline else ''
        enclose = 2 if child else enclose

        match enclose: # The spacing makes it more obvious... I tell myself
            case 1:   return f'<{ tag}{kwattrs}/>{nline}'
            case 2:   return f'<{ tag}{kwattrs}>{ child}</{tag}>{nline}'
            case 3:   return f'</{tag}>{nline}'
            case _:   return f'<{ tag}{kwattrs}>{ nline}'
    
    @staticmethod
    def slug(text: str, reject_chars_re=re.compile(r'[^-a-zA-Z0-9]+'), separator='-', replace_pairs=(),
                max_length=0, lowercase=True, clean_html=True):
        """Normalizes a string by removing non-alphanumeric characters and replacing gaps with the separator."""
        
        if replace_pairs:  # user-specific replacements
            for old, new in replace_pairs:
                text = text.replace(old, new)
        
        text = unicodedata.normalize('NFKD', text)    # try avoid lookalike characters etc
        text = text.casefold() if lowercase else text # make the text lowercase (optional)
        text = QUOTE_CHARS_RE.sub(separator, text)    # replace quotes before entity replacement
        
        if clean_html:                                # character entity reference
            text = HTML_NAMED_ENTITY_RE.sub(lambda m: chr(name2codepoint[m.group(1)]), text)
            text =      HTML_DECIMAL_RE.sub(lambda m: chr(int(m.group(1))), text) if HTML_DECIMAL_RE.match(text) else text
            text =   HTML_HEX_ENTITY_RE.sub(lambda m: chr(int(m.group(1), 16)), text) if HTML_HEX_ENTITY_RE.match(text) else text
        
        text = QUOTE_CHARS_RE.sub('', text)           # remove surplus quotes
        text = NUM_SEP_COMMAS_RE.sub('', text)        # cleanup numbers
        text = re.sub(reject_chars_re, separator, text)
        text = DUPLICATE_DASH_RE.sub(separator, text).strip(separator) # remove redundant
        
        if replace_pairs:                             # finalize user-specific replacements
            for old, new in replace_pairs:
                text = text.replace(old, new)
        
        assert re.match(VALID_SLUG_RE, text)
        return text[:max_length] if max_length > 0 else text

    def to_html_charcodes(self, text: str) -> str:
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

class MDHTMLVisitor(HTMLVisitor):
    # Pretty sure filename can be removed
    def __init__(self, grammar=None, filename=None, title="", tag_class=None):
        super(MDHTMLVisitor, self).__init__(grammar, filename)
        self.title = title
        self.titles_ids = {}
        self.tag_class = tag_class or self.__class__.tag_class
        self._template = '{body}'
    



