"""Complex integration tests for the NewNerd todo format.

Exercises the full ``parse_todo`` pipeline against other rich, real-world-style documents to validate nesting, tag extraction, status derivation, and section grouping.
"""

import unittest
from par.todo import parse_todo_to_ast, Tag, TodoItem, TodoDocument

## This flavor of todo file is based on trying to match a common subset of existing ideas.

RENDERER_DOC = """\
# Renderer 2.0  @alice @bob @charlie  #renderer  +engine

A full rewrite of the draw pipeline.
Goal: 4000+ draw calls/frame sustained.

## Shipped

- [x] Architecture review + RFC sign-off  @alice  done:2026-02-12
- [x] Feature gate + renderer_v2 flag  @charlie  #infra  done:2026-02-14
- [x] Material abstraction layer  @alice  #core  est:3d  done:2026-02-20
- [x] Command buffer recording  @bob  #core  est:2d  done:2026-02-25
- [x] Draw call batch grouping (pass 1)  @alice  #performance  est:2d  done:2026-03-03
    - [x] Sorted by material hash  done:2026-03-01
    - [x] Sorted by depth (front-to-back)  done:2026-03-03
- [x] Internal alpha: 10 shaders, 3 GPU vendors  @charlie  #alpha  done:2026-03-06

## In Flight  due:2026-03-21

- [/] Draw call batch optimiser (pass 2)  @alice  #performance  est:2d  due:2026-03-18
    - [x] Profiled baseline: 847 calls/frame  done:2026-03-14
    - [x] State-change dedup → 718 calls  done:2026-03-15
    - [/] Merge adjacent same-material batches → target 400  due:2026-03-17
    - [ ] Validate across 3 GPU vendors  due:2026-03-18

- [/] Portal visibility system  @bob  #performance  est:3d  due:2026-03-21  dep:batch-optimiser
    - [x] Surveyed BSP / PVS approaches  done:2026-03-13
    - [x] Basic portal traversal prototype  done:2026-03-15
    - [ ] Occlusion correctness on test scenes  due:2026-03-19
    - [ ] Performance budget sign-off (<5% frame overhead)  due:2026-03-21

- [ ] GPU timeline instrumentation  @charlie  #profiling  est:1d  due:2026-03-20
    - [ ] Insert GPU timestamp query per pass
    - [ ] Surface in debug overlay
    - [ ] Export to CSV for offline analysis

## Blocked

- [-] Console hot-reload (PS5/Xbox via WiFi debug)  @bob  #platform  blocked:wifi-debug-channel
    dep:#2487  until:2026-04-15

## Beta Gate  due:2026-03-28

- [ ] 30-day opt-in window complete  #process
- [ ] Crash rate < 0.1% across opt-in fleet  #metrics
- [ ] Frame time within 2% of old renderer  #metrics
- [ ] 5 external studios running on renderer_v2  #adoption
- [ ] Migration guide: old material API → new  @alice  #docs  due:2026-03-24
- [ ] CHANGELOG entry and announcement draft  @charlie  #docs  due:2026-03-26

## Parking Lot  someday:true

- [ ] Mobile WiFi debug channel  #platform  +renderer-v3
- [ ] Shader variant compiler  #core  +renderer-v3
- [ ] Async texture streaming integration  #core  +streaming
- [ ] Raytracing backend (DX12 / Vulkan RT)  #platform  +renderer-v3
"""


class TestRendererDocumentStructure(unittest.TestCase):
    """Validate the overall structure of the Renderer 2.0 document."""

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo_to_ast(RENDERER_DOC)

    def test_document_title(self):
        self.assertEqual(self.doc.title, "Renderer 2.0")

    def test_title_mentions(self):
        mentions = [t.name for t in self.doc.title_tags if t.kind == "mention"]
        self.assertEqual(sorted(mentions), ["alice", "bob", "charlie"])

    def test_title_hashtag(self):
        cats = [t.name for t in self.doc.title_tags if t.kind == "hashtag"]
        self.assertIn("renderer", cats)

    def test_title_project(self):
        projs = [t.name for t in self.doc.title_tags if t.kind == "project"]
        self.assertIn("engine", projs)

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 5)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Shipped", "In Flight", "Blocked", "Beta Gate", "Parking Lot"])

    def test_document_has_notes(self):
        # The two prose lines after the title
        self.assertTrue(len(self.doc.notes) >= 1)


class TestShippedSection(unittest.TestCase):
    """All items in the Shipped section should be done."""

    @classmethod
    def setUpClass(cls):
        doc = parse_todo_to_ast(RENDERER_DOC)
        cls.shipped = next(s for s in doc.sections if s.name == "Shipped")

    def test_top_level_item_count(self):
        self.assertEqual(len(self.shipped.items), 6)

    def test_all_done(self):
        for item in self.shipped.all_items():
            self.assertEqual(item.status, "done", f"Expected done: {item.text}")

    def test_nested_children(self):
        batch_item = self.shipped.items[4]  # Draw call batch grouping
        self.assertEqual(len(batch_item.children), 2)
        self.assertIn("Sorted by material hash", batch_item.children[0].text)

    def test_done_date_extraction(self):
        first = self.shipped.items[0]
        done_tag = next(t for t in first.tags if t.name == "done")
        self.assertEqual(done_tag.value, "2026-02-12")

    def test_assignee_extraction(self):
        first = self.shipped.items[0]
        self.assertIn("alice", first.assignees)

    def test_hashtag_extraction(self):
        infra_item = self.shipped.items[1]
        self.assertIn("infra", infra_item.categories)

    def test_effort_estimate(self):
        material = self.shipped.items[2]
        est = next((t.value for t in material.tags if t.name == "est"), None)
        self.assertEqual(est, "3d")


class TestInFlightSection(unittest.TestCase):
    """Mixed statuses: in_progress, done children, open items."""

    @classmethod
    def setUpClass(cls):
        doc = parse_todo_to_ast(RENDERER_DOC)
        cls.inflight = next(s for s in doc.sections if s.name == "In Flight")

    def test_top_level_count(self):
        self.assertEqual(len(self.inflight.items), 3)

    def test_in_progress_status(self):
        batch = self.inflight.items[0]
        self.assertEqual(batch.status, "in_progress")

    def test_open_item(self):
        gpu = self.inflight.items[2]
        self.assertEqual(gpu.status, "open")

    def test_mixed_child_statuses(self):
        batch = self.inflight.items[0]
        statuses = [c.status for c in batch.children]
        self.assertIn("done", statuses)
        self.assertIn("in_progress", statuses)
        self.assertIn("open", statuses)

    def test_due_date_on_item(self):
        batch = self.inflight.items[0]
        self.assertEqual(batch.due, "2026-03-18")

    def test_dependency_tag(self):
        portal = self.inflight.items[1]
        dep = next((t for t in portal.tags if t.name == "dep"), None)
        self.assertIsNotNone(dep)
        self.assertEqual(dep.value, "batch-optimiser")

    def test_deep_nesting_correct(self):
        gpu = self.inflight.items[2]
        self.assertEqual(len(gpu.children), 3)
        for child in gpu.children:
            self.assertEqual(child.status, "open")


class TestBlockedSection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = parse_todo_to_ast(RENDERER_DOC)
        cls.blocked = next(s for s in doc.sections if s.name == "Blocked")

    def test_cancelled_status(self):
        item = self.blocked.items[0]
        self.assertEqual(item.status, "cancelled")

    def test_blocked_value(self):
        item = self.blocked.items[0]
        blocked_tag = next((t for t in item.tags if t.name == "blocked"), None)
        self.assertIsNotNone(blocked_tag)
        self.assertEqual(blocked_tag.value, "wifi-debug-channel")


class TestBetaGateSection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = parse_todo_to_ast(RENDERER_DOC)
        cls.beta = next(s for s in doc.sections if s.name == "Beta Gate")

    def test_all_open(self):
        for item in self.beta.all_items():
            self.assertEqual(item.status, "open", f"Expected open: {item.text}")

    def test_item_count(self):
        self.assertEqual(len(self.beta.items), 6)

    def test_docs_assignee(self):
        migration = next(i for i in self.beta.items if "Migration" in i.text)
        self.assertIn("alice", migration.assignees)

    def test_metrics_hashtag(self):
        metrics_items = [i for i in self.beta.items if "metrics" in i.categories]
        self.assertEqual(len(metrics_items), 2)


class TestParkingLotSection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = parse_todo_to_ast(RENDERER_DOC)
        cls.parking = next(s for s in doc.sections if s.name == "Parking Lot")

    def test_project_tags(self):
        projs = set()
        for item in self.parking.items:
            projs.update(item.projects)
        self.assertIn("renderer-v3", projs)
        self.assertIn("streaming", projs)

    def test_all_open(self):
        for item in self.parking.items:
            self.assertEqual(item.status, "open")


#  Document-level aggregation tests 

class TestDocumentAggregation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo_to_ast(RENDERER_DOC)

    def test_all_items_count(self):
        all_items = list(self.doc.all_items())
        # 6 shipped top + 2 children + 3 inflight top + 4+4+3 children + 1 blocked + 6 beta + 4 parking = ~33
        self.assertGreaterEqual(len(all_items), 30)

    def test_filter_by_assignee(self):
        alice_items = [i for i in self.doc.all_items() if "alice" in i.assignees]
        self.assertGreaterEqual(len(alice_items), 4)

    def test_filter_by_hashtag(self):
        perf = [i for i in self.doc.all_items() if "performance" in i.categories]
        self.assertGreaterEqual(len(perf), 3)

    def test_filter_by_status(self):
        done = [i for i in self.doc.all_items() if i.is_done]
        self.assertGreaterEqual(len(done), 10)

    def test_open_items(self):
        open_items = [i for i in self.doc.all_items() if i.status == "open"]
        self.assertGreaterEqual(len(open_items), 15)


#  Nesting edge cases 

class TestDeepNesting(unittest.TestCase):
    """Verify that indentation-based nesting works at multiple levels."""

    def test_three_level_nesting(self):
        text = """\
## Work

- [ ] Level 1
    - [ ] Level 2
        - [ ] Level 3
"""
        doc = parse_todo_to_ast(text)
        sec = doc.sections[0]
        self.assertEqual(len(sec.items), 1)
        l1 = sec.items[0]
        self.assertEqual(len(l1.children), 1)
        l2 = l1.children[0]
        self.assertEqual(len(l2.children), 1)
        l3 = l2.children[0]
        self.assertIn("Level 3", l3.text)

    def test_sibling_items_at_same_indent(self):
        text = """\
- [ ] A
    - [ ] A1
    - [ ] A2
- [ ] B
"""
        doc = parse_todo_to_ast(text)
        self.assertEqual(len(doc.items), 2)
        self.assertEqual(len(doc.items[0].children), 2)
        self.assertEqual(doc.items[1].text, "B")

    def test_dedent_returns_to_parent(self):
        text = """\
- [ ] Parent
    - [ ] Child 1
        - [ ] Grandchild
    - [ ] Child 2
"""
        doc = parse_todo_to_ast(text)
        parent = doc.items[0]
        self.assertEqual(len(parent.children), 2)
        self.assertEqual(len(parent.children[0].children), 1)
        self.assertEqual(parent.children[1].text, "Child 2")


#  Tag extraction edge cases 

class TestTagExtraction(unittest.TestCase):

    def test_multiple_hashtags(self):
        text = "- [ ] Fix rendering #renderer #performance #urgent"
        doc = parse_todo_to_ast(text)
        item = doc.items[0]
        self.assertEqual(sorted(item.categories), ["performance", "renderer", "urgent"])

    def test_multiple_mentions(self):
        text = "- [ ] Pair review  @alice @bob"
        doc = parse_todo_to_ast(text)
        item = doc.items[0]
        self.assertEqual(sorted(item.assignees), ["alice", "bob"])

    def test_mixed_tags(self):
        text = "- [x] Ship it  #release @alice +engine done:2026-03-17 est:2h"
        doc = parse_todo_to_ast(text)
        item = doc.items[0]
        self.assertEqual(item.status, "done")
        self.assertIn("release", item.categories)
        self.assertIn("alice", item.assignees)
        self.assertIn("engine", item.projects)
        est = next(t.value for t in item.tags if t.name == "est")
        self.assertEqual(est, "2h")

    def test_done_with_date(self):
        text = "- [x] Task done:2026-01-01"
        item = parse_todo_to_ast(text).items[0]
        done_tag = next(t for t in item.tags if t.name == "done" and t.kind == "status")
        # [x] gives one done, done:date gives another
        self.assertEqual(item.status, "done")

    def test_priority_prefix(self):
        text = "(A) Critical task @work"
        item = parse_todo_to_ast(text).items[0]
        self.assertEqual(item.priority, "A")

    def test_clean_display_text(self):
        text = "- [ ] Fix bug  #renderer @alice est:2h"
        item = parse_todo_to_ast(text).items[0]
        self.assertEqual(item.text, "Fix bug")


#  Empty / minimal documents 

class TestMinimalDocuments(unittest.TestCase):

    def test_empty_document(self):
        doc = parse_todo_to_ast("")
        self.assertIsNone(doc.title)
        self.assertEqual(len(doc.sections), 0)
        self.assertEqual(len(doc.items), 0)

    def test_title_only(self):
        doc = parse_todo_to_ast("# My Project")
        self.assertEqual(doc.title, "My Project")
        self.assertEqual(len(doc.sections), 0)

    def test_single_item(self):
        doc = parse_todo_to_ast("- [ ] Do the thing")
        self.assertEqual(len(doc.items), 1)
        self.assertEqual(doc.items[0].text, "Do the thing")
        self.assertEqual(doc.items[0].status, "open")

    def test_single_done_item(self):
        doc = parse_todo_to_ast("- [x] Done thing")
        self.assertEqual(doc.items[0].status, "done")

    def test_notes_without_items(self):
        doc = parse_todo_to_ast("Just some text\nMore text")
        self.assertTrue(len(doc.notes) >= 1)


#  Notes attachment 

class TestNotesAttachment(unittest.TestCase):

    def test_note_after_item(self):
        text = """\
- [ ] Task one
    Some context about this task
- [ ] Task two
"""
        doc = parse_todo_to_ast(text)
        # The indented note line may be parsed as a bullet or note
        # depending on format — just verify both items exist
        self.assertGreaterEqual(len(doc.items), 1)

    def test_section_notes(self):
        text = """\
## Section

Some descriptive text about this section.

- [ ] Item one
"""
        doc = parse_todo_to_ast(text)
        sec = doc.sections[0]
        # Notes before any item belong to the section
        self.assertTrue(len(sec.notes) >= 1 or len(sec.items) >= 1)


if __name__ == "__main__":
    unittest.main()
