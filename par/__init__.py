#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Based on pyPEG (previous author: Limodou)
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

__author__ = 'smolchoad'
__author_email__ = None
__url__ = None
__license__ = 'BSD'
__version__ = '1.4.2'

_ = re.compile

class SimpleVisitor(object):
    def __init__(self, grammar=None):
        self.grammar = grammar
    
    def visit(self, nodes: Symbol|list[Symbol], root=False) -> str:
        buf = []
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        
        # Cache class dict for faster method lookups
        methods = self.__class__.__dict__
        
        if root and (method := methods.get('__begin__')):
            buf.append(method(self))
        
        for node in nodes:
            if isinstance(node, str):
                buf.append(node)
            else:
                node_name = node.__name__
                
                if (method := methods.get('before_visit')):
                    buf.append(method(self, node))
                if (method := methods.get(f'visit_{node_name}_begin')):
                    buf.append(method(self, node))
                if (method := methods.get(f'visit_{node_name}')):
                    buf.append(method(self, node))
                else:
                    buf.append(node.what if isinstance(node.what, str) else self.visit(node.what))
                if (method := methods.get(f'visit_{node_name}_end')):
                    buf.append(method(self, node))
                if (method := methods.get('after_visit')):
                    buf.append(method(self, node))
        
        if root and (method := methods.get('__end__')):
            buf.append(method(self))
        
        return ''.join(buf)

class HTMLVisitor(SimpleVisitor):
    tag_class = {}
    
    def __init__(self, grammar=None, tag_class=None):
        super(HTMLVisitor, self).__init__(grammar)
    
    def tag(self, tag: str, child='', attrs='', enclose=0, newline=True, **kwargs) -> str:
        """HTML tag generator
        Args:
          * child -- complete tag content
          * attrs -- additional attributes
          * enclose -- 1: self-closing tag, 2: open+close tag, 3: close tag
        """
        
        kw = kwargs.copy()
        _class = f"{kw.pop('_class', '')} {kw.pop('class', '')}".strip()
        _id = kw.pop('_id', None)
        if _id is not None:
            kw['id'] = _id
        tag_class = ''#self.tag_class.get(tag, '')

        if tag_class:
            kw['class'] = f"{tag_class[1:]} {_class}".strip() if tag_class.startswith('+') else tag_class
        else:
            kw['class'] = _class

        kwattrs = ' '.join(x if y is True else f'{x}="{y}"' for x, y in sorted(kw.items()) if y)
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
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class MDHTMLVisitor(HTMLVisitor):
    def __init__(self, grammar=None, tag_class=None):
        super(MDHTMLVisitor, self).__init__(grammar)
        self.titles_ids = {}
        self.tag_class = tag_class or self.__class__.tag_class
