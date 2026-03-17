"""Tests for TODO parse-tree access, JSON export, and plaintext rendering."""

import json
import unittest

from par.todo import parseTree, parse_todo, renderText


SAMPLE = """\
# Project Phoenix @alice #ops +phoenix

## In Flight due:2026-04-01
[ ] Ship parser rewrite @bob #backend est:2d
    Remember to benchmark packrat mode
[/] Add JSON export @alice dep:parser-rewrite
"""


class TestTodoParseTree(unittest.TestCase):

    def test_returns_document_symbol(self):
        tree = parseTree(SAMPLE)
        self.assertEqual(tree.__name__, 'document')
        self.assertIsNotNone(tree.find('markdown_heading_line'))
        self.assertIsNotNone(tree.find('list_item_line'))


class TestTodoPlaintextRender(unittest.TestCase):

    def test_render_from_parsed_document(self):
        document = parse_todo(SAMPLE)
        rendered = renderText(document)

        self.assertIn('# Project Phoenix  @alice  #ops  +phoenix', rendered)
        self.assertIn('## In Flight  due:2026-04-01', rendered)
        self.assertIn('[ ] Ship parser rewrite  @bob  #backend  est:2d', rendered)
        self.assertIn('    Remember to benchmark packrat mode', rendered)
        self.assertIn('[/] Add JSON export  @alice  dep:parser-rewrite', rendered)


if __name__ == '__main__':
    unittest.main()
