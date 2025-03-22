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