"""Per-variant compatibility tests.

Each test class exercises one of the documented todo-format families using
example content drawn from the corresponding ``par/todo docs/*.md`` files.
"""

import unittest
from par.todo import parse_todo, Tag, TodoItem


#  1. todo.txt

TODOTXT = """\
(A) Optimize renderer draw calls +renderer @work
(A) Fix physics edge case collisions +physics @debug
(B) Implement portal visibility system +renderer
(B) Improve rigid body solver @work
(C) Add debug visualization tools +general
(C) Simplify material state system +renderer
Optimize GPU pipeline stalls +renderer
Profile lighting calculations +renderer @perf
x 2026-03-10 Setup initial engine structure +general
x 2026-03-12 Implement basic mesh loader +general
x 2026-03-14 Create initial render loop +renderer
x 2026-03-15 Add basic physics integration +physics
"""


class TestTodoTxt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(TODOTXT)

    def test_all_items_parsed(self):
        self.assertEqual(len(list(self.doc.all_items())), 12)

    def test_priority_a(self):
        items = list(self.doc.all_items())
        a_items = [i for i in items if i.priority == "A"]
        self.assertEqual(len(a_items), 2)

    def test_priority_levels(self):
        items = list(self.doc.all_items())
        priorities = {i.priority for i in items if i.priority}
        self.assertEqual(priorities, {"A", "B", "C"})

    def test_project_tags(self):
        items = list(self.doc.all_items())
        renderer = [i for i in items if "renderer" in i.projects]
        self.assertGreaterEqual(len(renderer), 4)

    def test_context_as_mention(self):
        items = list(self.doc.all_items())
        work = [i for i in items if "work" in i.assignees]
        self.assertGreaterEqual(len(work), 2)

    def test_done_items(self):
        done = [i for i in self.doc.all_items() if i.is_done]
        self.assertEqual(len(done), 4)

    def test_done_date(self):
        done = [i for i in self.doc.all_items() if i.is_done]
        dates = [next((t.value for t in i.tags if t.name == "done"), None) for i in done]
        self.assertIn("2026-03-10", dates)

    def test_open_items(self):
        open_items = [i for i in self.doc.all_items() if i.status == "open"]
        self.assertEqual(len(open_items), 8)


TODOTXT_COOKING = """\
(A) Prep mise en place +dinner @kitchen
(B) Marinate protein +dinner @prep
(B) Chop vegetables +dinner @prep
(C) Set table +dinner @dining
Review recipe timing @kitchen
Cook rice +dinner
Prepare sauce +dinner @stove
x 2026-03-17 Shop for ingredients +dinner
x 2026-03-17 Pre-heat oven +dinner @kitchen
"""


class TestTodoTxtCooking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(TODOTXT_COOKING)

    def test_total_items(self):
        self.assertEqual(len(list(self.doc.all_items())), 9)

    def test_dinner_project(self):
        dinner = [i for i in self.doc.all_items() if "dinner" in i.projects]
        self.assertGreaterEqual(len(dinner), 7)

    def test_done_count(self):
        done = [i for i in self.doc.all_items() if i.is_done]
        self.assertEqual(len(done), 2)


#  2. TODO.md  (Markdown checkboxes + sections)

TODOMD = """\
# Game Engine Development

## Renderer
- [x] Basic mesh loading
- [x] Simple render loop
- [ ] Implement portal visibility
- [ ] Optimize BSP traversal
- [ ] Reduce draw calls during scene traversal
- [ ] Evaluate texture compression impact

## Physics
- [x] Basic rigid body integration
- [ ] Improve collision edge cases
- [ ] Test new rigid body solver
- [ ] Profile physics step cost
- [ ] Remove redundant collision checks

## Performance
- [ ] Investigate lightmap precision problems
- [ ] Investigate GPU pipeline stalls
- [ ] Profile rendering hot paths
- [ ] Optimize triangle batching

## Completed
- [x] Engine structure scaffolding
- [x] Memory management foundation
- [x] Basic logging system
"""


class TestTodoMd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(TODOMD)

    def test_title(self):
        self.assertEqual(self.doc.title, "Game Engine Development")

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 4)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Renderer", "Physics", "Performance", "Completed"])

    def test_renderer_items(self):
        renderer = self.doc.sections[0]
        self.assertEqual(len(renderer.items), 6)

    def test_renderer_done_count(self):
        renderer = self.doc.sections[0]
        done = [i for i in renderer.items if i.is_done]
        self.assertEqual(len(done), 2)

    def test_completed_section_all_done(self):
        completed = self.doc.sections[3]
        for item in completed.items:
            self.assertEqual(item.status, "done", f"Expected done: {item.text}")

    def test_total_items(self):
        all_items = list(self.doc.all_items())
        self.assertEqual(len(all_items), 18)

    def test_open_items(self):
        open_items = [i for i in self.doc.all_items() if i.status == "open"]
        self.assertEqual(len(open_items), 12)


TODOMD_COOKING = """\
# Dinner Preparation

## Preparation
- [x] Shop for ingredients
- [x] Review recipe timing
- [ ] Prep mise en place (chop vegetables, measure spices)
- [ ] Marinate protein (4 hours needed)

## Main Course
- [ ] Cook rice
- [ ] Prepare sauce
- [ ] Cook protein on stove
- [ ] Plate and garnish

## Completed (Yesterday's Prep)
- [x] Made stock for sauce
- [x] Prepped spice blends
"""


class TestTodoMdCooking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(TODOMD_COOKING)

    def test_title(self):
        self.assertEqual(self.doc.title, "Dinner Preparation")

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 3)

    def test_prep_done(self):
        prep = self.doc.sections[0]
        done = [i for i in prep.items if i.is_done]
        self.assertEqual(len(done), 2)


#  3. TaskPaper

TASKPAPER = """\
Renderer Optimization:
\t- Implement portal visibility system @priority(1) @due(2026-03-20)
\t\t- Research BSP tree techniques
\t\t- Benchmark current approach
\t- Remove redundant state changes
\t- @done Implement basic mesh loader

Physics Engine:
\t- Improve collision edge cases @priority(1)
\t- Test new rigid body solver
\t- @done Basic rigid body integration

Infrastructure:
\t- Improve build time @priority(2)
\t- Add debug visualization tools @today
\t- @done Initial engine scaffolding
"""


class TestTaskPaper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(TASKPAPER)

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 3)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Renderer Optimization", "Physics Engine", "Infrastructure"])

    def test_renderer_items(self):
        renderer = self.doc.sections[0]
        self.assertGreaterEqual(len(renderer.items), 3)

    def test_done_via_at_done(self):
        renderer = self.doc.sections[0]
        all_items = list(renderer.all_items())
        done = [i for i in all_items if i.is_done]
        self.assertGreaterEqual(len(done), 1)

    def test_priority_tag(self):
        renderer = self.doc.sections[0]
        portal = renderer.items[0]
        self.assertEqual(portal.priority, "1")

    def test_due_tag(self):
        renderer = self.doc.sections[0]
        portal = renderer.items[0]
        self.assertEqual(portal.due, "2026-03-20")

    def test_nested_subtasks(self):
        renderer = self.doc.sections[0]
        portal = renderer.items[0]
        self.assertEqual(len(portal.children), 2)

    def test_today_tag(self):
        infra = self.doc.sections[2]
        debug_item = next(i for i in infra.items if "debug" in i.text.lower())
        self.assertEqual(debug_item.due, "today")

    def test_total_done(self):
        all_done = [i for i in self.doc.all_items() if i.is_done]
        self.assertEqual(len(all_done), 3)


#  4. Hybrid Markdown + Tags

HYBRID = """\
- [x] Initial project scaffolding #repo
- [x] Setup CI pipeline #devops
- [x] Setup basic engine structure #repo #infra
- [x] Implement basic mesh loader #renderer
- [x] Create initial render loop #renderer #core
- [x] Add physics integration #physics #core
- [ ] Improve portal visibility system #renderer #performance
- [ ] Optimize BSP traversal #renderer #optimization
- [ ] Reduce draw calls during scene #renderer #performance #urgent
- [ ] Test rigid body solver #physics #testing
- [ ] Improve collision edge cases #physics #urgent
- [ ] Profile physics step cost #physics #performance
- [ ] Investigate GPU pipeline stalls #renderer #debug #urgent
"""


class TestHybridMarkdownTags(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(HYBRID)

    def test_no_sections(self):
        # Hybrid format is flat, no sections
        self.assertEqual(len(self.doc.sections), 0)

    def test_total_items(self):
        self.assertEqual(len(list(self.doc.all_items())), 13)

    def test_done_count(self):
        done = [i for i in self.doc.all_items() if i.is_done]
        self.assertEqual(len(done), 6)

    def test_urgent_hashtag(self):
        urgent = [i for i in self.doc.all_items() if "urgent" in i.categories]
        self.assertEqual(len(urgent), 3)

    def test_multiple_hashtags(self):
        engine = next(i for i in self.doc.all_items() if "engine structure" in i.text.lower())
        self.assertEqual(sorted(engine.categories), ["infra", "repo"])

    def test_filter_renderer(self):
        renderer = [i for i in self.doc.all_items() if "renderer" in i.categories]
        self.assertGreaterEqual(len(renderer), 5)

    def test_filter_performance(self):
        perf = [i for i in self.doc.all_items() if "performance" in i.categories]
        self.assertGreaterEqual(len(perf), 3)


HYBRID_COOKING = """\
- [x] Shop for ingredients #planning
- [x] Prepped dry ingredients #prep
- [ ] Chop vegetables #prep #urgent
- [ ] Marinate protein (4 hours) #prep #urgent
- [ ] Cook rice (20 mins) #cooking #parallel
- [ ] Simmer sauce (30 mins) #cooking #parallel
- [ ] Sear protein (10 mins) #cooking
- [ ] Plate main component #plating #urgent
"""


class TestHybridCooking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(HYBRID_COOKING)

    def test_total(self):
        self.assertEqual(len(list(self.doc.all_items())), 8)

    def test_urgent(self):
        urgent = [i for i in self.doc.all_items() if "urgent" in i.categories]
        self.assertEqual(len(urgent), 3)

    def test_parallel(self):
        par = [i for i in self.doc.all_items() if "parallel" in i.categories]
        self.assertEqual(len(par), 2)


#  5. doing.txt  (time-tracking sessions)

DOING_TXT = """\
# Work Log

## Renderer optimization pass
Start: 2026-03-15 09:00
End: 2026-03-15 11:30
Notes: Profiled current draw call count. Reduced to ~720 calls.

## Physics solver improvements
Start: 2026-03-15 13:00
End: 2026-03-15 15:15
Notes: Improved rigid body constraint solver. Edge case found.

## Asset pipeline refactoring
Start: 2026-03-16 09:00
End: 2026-03-16 12:00
Notes: Simplified asset loading code, removed ~200 LOC debt.
"""


class TestDoingTxt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(DOING_TXT)

    def test_section_count(self):
        # # Title + 3 ## sections
        self.assertEqual(len(self.doc.sections), 3)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertIn("Renderer optimization pass", names)
        self.assertIn("Physics solver improvements", names)
        self.assertIn("Asset pipeline refactoring", names)

    def test_items_have_start_end(self):
        for sec in self.doc.sections:
            if sec.items:
                item = sec.items[0]
                start = next((t.value for t in item.tags if t.name == "start"), None)
                end = next((t.value for t in item.tags if t.name == "end"), None)
                self.assertIsNotNone(start, f"Missing start in {sec.name}")
                self.assertIsNotNone(end, f"Missing end in {sec.name}")


#  6. Linux Roadmap (temporal horizon sections)

LINUX_ROADMAP = """\
# Renderer Roadmap

## Short Term
- [ ] Optimize draw call batching
- [ ] Fix shadow map precision
- [ ] Add GPU timestamp queries

## Medium Term
- [ ] Implement portal visibility
- [ ] Add compute-based occlusion

## Long Term
- [ ] Raytracing integration
- [ ] Mobile GPU backend
"""


class TestLinuxRoadmap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(LINUX_ROADMAP)

    def test_title(self):
        self.assertEqual(self.doc.title, "Renderer Roadmap")

    def test_sections(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Short Term", "Medium Term", "Long Term"])

    def test_short_term_items(self):
        short = self.doc.sections[0]
        self.assertEqual(len(short.items), 3)

    def test_all_open(self):
        for item in self.doc.all_items():
            self.assertEqual(item.status, "open")


#  7. Rust Tracking Issue (phase sections + checkboxes)

RUST_TRACKING = """\
# Feature: Renderer V2

## Implementation
- [x] Core pipeline rewrite
- [x] Material abstraction
- [ ] Portal visibility
- [ ] Batch optimizer pass 2

## Testing
- [x] Unit tests for pipeline
- [ ] Integration tests
- [ ] Performance benchmarks

## Stabilization
- [ ] 30-day bake period
- [ ] Documentation review
"""


class TestRustTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(RUST_TRACKING)

    def test_title(self):
        self.assertIn("Renderer V2", self.doc.title)

    def test_sections(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Implementation", "Testing", "Stabilization"])

    def test_implementation_progress(self):
        impl = self.doc.sections[0]
        done = [i for i in impl.items if i.is_done]
        self.assertEqual(len(done), 2)
        open_items = [i for i in impl.items if i.status == "open"]
        self.assertEqual(len(open_items), 2)

    def test_testing_progress(self):
        testing = self.doc.sections[1]
        done = [i for i in testing.items if i.is_done]
        self.assertEqual(len(done), 1)


#  8. Kubernetes KEP (proposal sections)

KEP = """\
# KEP-2401: Renderer V2 Pipeline

## Goals
- [ ] 4000+ draw calls/frame sustained
- [ ] Hot-reload in dev builds
- [ ] Zero release overhead

## Proposal
- [ ] Command buffer architecture
- [ ] Material abstraction layer
- [ ] Portal-based visibility

## Graduation Criteria
- [ ] Alpha: 10 studios opt-in
- [ ] Beta: crash rate < 0.1%
- [ ] GA: 10 shipped titles
"""


class TestKubernetesKEP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(KEP)

    def test_title(self):
        self.assertIn("KEP-2401", self.doc.title)

    def test_sections(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Goals", "Proposal", "Graduation Criteria"])

    def test_goals_items(self):
        goals = self.doc.sections[0]
        self.assertEqual(len(goals.items), 3)

    def test_all_open(self):
        for item in self.doc.all_items():
            self.assertEqual(item.status, "open")


#  9. 90s-style engineering TODO

NINETIES = """\
Renderer TODO:
- Optimize draw calls
- Fix shadow precision
- Add GPU profiling hooks

Physics TODO:
- Improve collision edge cases
- Test constraint solver
- Profile physics step cost

Infrastructure TODO:
- Simplify build system
- Add debug visualization
- Update documentation
"""


class TestNinetiesStyle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(NINETIES)

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 3)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Renderer", "Physics", "Infrastructure"])

    def test_renderer_items(self):
        renderer = self.doc.sections[0]
        self.assertEqual(len(renderer.items), 3)

    def test_all_open(self):
        for item in self.doc.all_items():
            self.assertEqual(item.status, "open")

    def test_total_items(self):
        self.assertEqual(len(list(self.doc.all_items())), 9)


#  Cross-variant: mixed format tolerance

MIXED_FORMAT = """\
# Project Alpha  @lead +alpha

## Backlog
- [ ] Feature A  #core
- [ ] Feature B  #core @alice due:2026-04-01

## In Progress
- [/] Feature C  #core est:3d
    - [x] Subtask C.1 done:2026-03-10
    - [ ] Subtask C.2

## Done
- [x] Setup repo  #infra done:2026-03-01
(A) Review architecture +alpha @work
x 2026-03-05 Initial scaffolding +alpha
"""


class TestMixedFormat(unittest.TestCase):
    """Verifies the parser handles mixing of formats in one document."""

    @classmethod
    def setUpClass(cls):
        cls.doc = parse_todo(MIXED_FORMAT)

    def test_title(self):
        self.assertEqual(self.doc.title, "Project Alpha")

    def test_sections(self):
        names = [s.name for s in self.doc.sections]
        self.assertEqual(names, ["Backlog", "In Progress", "Done"])

    def test_in_progress_status(self):
        ip = self.doc.sections[1]
        self.assertEqual(ip.items[0].status, "in_progress")

    def test_nested_child_done(self):
        ip = self.doc.sections[1]
        parent = ip.items[0]
        self.assertEqual(parent.children[0].status, "done")
        self.assertEqual(parent.children[1].status, "open")

    def test_todotxt_done_in_section(self):
        done_sec = self.doc.sections[2]
        done_items = [i for i in done_sec.items if i.is_done]
        # [x] Setup repo + x 2026-03-05 Initial scaffolding
        self.assertGreaterEqual(len(done_items), 2)

    def test_due_date(self):
        backlog = self.doc.sections[0]
        feat_b = backlog.items[1]
        self.assertEqual(feat_b.due, "2026-04-01")


if __name__ == "__main__":
    unittest.main()
