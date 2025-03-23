#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: limodou@gmail.com
# This program is based on pyPEG
#
# license: BSD

from .pyPEG import *

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

    def visit(self, nodes, root=False):
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

# from enum import Enum
# class TagClose(Enum):
#     open       = 0 # <tag>
#     self_close = 1 # <tag/>
#     wrap       = 2 # <tag></tag>
#     close      = 3 # </tag>

class HTMLVisitor(SimpleVisitor):
    tag_class = {}
    
    # Pretty sure filename can be removed
    def __init__(self, grammar=None, filename=None, tag_class=None):
        super(HTMLVisitor, self).__init__(grammar, filename)
        #self.tag_class = tag_class or self.__class__.tag_class
        self._template = '<html><head><title>{title}</title></head><body>{body}</body></html>'
    
    def tag(self, tag:str, child='', enclose=0, newline=True, **kwargs):
        """An HTML tag with optional child(ren) and attributes."""
        kw = kwargs.copy()
        _class = kw.pop('_class', '')
        _class += ' ' + kw.pop('class', '')
        tag_class = self.tag_class.get(tag, '')
        
        # Add classes to the tag
        if tag_class:
            kw['class'] = f"{tag_class[1:]} {_class.lstrip()}" if tag_class.startswith('+') else tag_class.lstrip()
        else:
            kw['class'] = _class.lstrip()

        if tag == 'a':
            href = kw.get('href', '#')
            _cls = 'outter' if href.startswith(('http:', 'https:', 'ftp:')) else 'inner'
            kw['href'] = href
            kw['class'] = f"{kw.get('class', '')} {_cls}".strip()

        attrs = f" {' '.join(f'{x}="{y}"' for x, y in sorted(kw.items()) if y)}"
        nline = '\n' if newline else ''
        enclose = 2 if child else enclose

        match enclose:
            case 1:
                return f'<{tag}{attrs}/>{nline}'
            case 2:
                return f'<{tag}{attrs}>{child}</{tag}>{nline}'
            case _:
                return f'<{tag}{attrs}>{nline}'
    
    def to_html(self, text: str) -> str:
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

class MDHTMLVisitor(HTMLVisitor):
    # Pretty sure filename can be removed
    def __init__(self, grammar=None, filename=None, title="", tag_class=None, block_callback=None, init_callback=None):
        super(MDHTMLVisitor, self).__init__(grammar, filename)
        # self.indent = 0
        self.title = title
        self.titles_ids = {}
        self.tag_class = tag_class or self.__class__.tag_class

        self.block_callback = block_callback or {}
        self.init_callback = init_callback
        
        self._template = '{body}'
    

    def get_title_id(self, level:int, begin=1) -> str:
        self.titles_ids[level] = self.titles_ids.get(level, 0) + 1
        _ids = [self.titles_ids.get(x, 0) for x in range(begin, level + 1)]
        return f'title_{'-'.join(map(str, _ids))}'

