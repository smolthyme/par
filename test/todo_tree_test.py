"""Tree-structure tests for the TODO grammar."""

import unittest

from par.todo import parse_todo_tree
from par.pyPEG import Symbol


class TestTodoTreeStructure(unittest.TestCase):

    def _must_find(self, node: Symbol, name: str) -> Symbol:
        if (found := node.find(name)) is None:
            self.fail(f"Expected {name!r} in {node.__name__!r}")
        return found

    def test_list_item_children(self):
        tree = parse_todo_tree("- [/] Ship renderer  @alice #perf +engine")
        line = self._must_find(tree, 'item')
        self.assertEqual(next(line.find_all('indent')).text, '')
        self.assertEqual(self._must_find(line, 'bullet').text, '-')
        self.assertEqual(self._must_find(line, 'checkbox').text, '[/]')
        self.assertEqual(self._must_find(line, 'text').text.strip(), 'Ship renderer  @alice #perf +engine')

    def test_heading_children(self):
        tree = parse_todo_tree("## In Flight  due:2026-03-21")
        line = self._must_find(tree, 'heading')
        self.assertEqual(self._must_find(line, 'heading_level').text, '##')
        self.assertEqual(self._must_find(line, 'heading_text').text.strip(), 'In Flight  due:2026-03-21')

    def test_component_header_children(self):
        tree = parse_todo_tree("Renderer TODO:")
        line = self._must_find(tree, 'header')
        self.assertEqual(self._must_find(line, 'name').text, 'Renderer')

    def test_taskpaper_project_children(self):
        tree = parse_todo_tree("Infrastructure:")
        line = self._must_find(tree, 'project')
        self.assertEqual(self._must_find(line, 'project_name').text, 'Infrastructure')

    def test_doing_field_children(self):
        tree = parse_todo_tree("Start: 2026-03-15 09:00")
        line = self._must_find(tree, 'field')
        self.assertEqual(self._must_find(line, 'key').text, 'Start')
        self.assertEqual(self._must_find(line, 'value').text, '2026-03-15 09:00')


if __name__ == '__main__':
    unittest.main()
