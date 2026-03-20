"""PEG-based TODO parsing, AST nodes, and canonical plaintext rendering.

    parse(text)         -> TodoDocument
    parse_to_dict(text) -> dict
    parse_tree(text)    -> raw pyPEG Symbol tree
    render(node)        -> canonical plaintext
"""

import re, types
from dataclasses import dataclass, field
from datetime import date as Date
from enum import Enum
from functools import lru_cache
from typing import Any, Iterator, Literal

from .pyPEG import Symbol, parseLine

_ = lru_cache(maxsize=256)(re.compile)

_TAG_TOKEN_RE = _(r'(?<!\w)(?:@(?P<mention_name>[A-Za-z][\w.-]*)(?:\((?P<mention_value>[^)]*)\))?|(?P<meta_key>[a-z]\w*):(?P<meta_value>\S+)|#(?P<hashtag_name>[A-Za-z][\w-]*)|\+(?P<project_name>[A-Za-z][\w-]*))')
_STATUS_NAMES = frozenset({'done', 'cancelled', 'blocked'})
_STATUS_AT = frozenset({'done', 'cancelled', 'blocked'})
_CLOSED = frozenset({'done', 'cancelled'})
_STATUS_MARKERS = {'open': '[ ]', 'progress': '[/]', 'done': '[x]', 'blocked': '[-]', 'cancelled': '[-]'}
_CYCLE_STATUS   = ['open', 'progress', 'done', 'cancelled']
_CHAR_MAP       = { 'x': 'done', 'y': 'done', '/': 'progress', '-': 'cancelled',
                    ' ': 'open', 'o': 'open', 'n': 'cancelled'}

type ThingKind = Literal['item', 'section', 'session']


class TodoStatus(str, Enum):
    OPEN = 'open'
    PROGRESS = 'progress'
    DONE = 'done'
    BLOCKED = 'blocked'
    CANCELLED = 'cancelled'

    def marker(self) -> str:
        return _STATUS_MARKERS[self.value]

    def tag_name(self) -> str:
        return 'progress' if self is TodoStatus.PROGRESS else self.value

    @classmethod
    def from_char(cls, char: str) -> 'TodoStatus | None':
        return cls(value) if (value := _CHAR_MAP.get(char.lower())) else None

    @classmethod
    def from_tag_name(cls, name: str) -> 'TodoStatus | None':
        try:
            return cls(name)
        except ValueError:
            return None

    @classmethod
    def from_any(cls, value: 'str | TodoStatus') -> 'TodoStatus':
        match value:
            case TodoStatus():
                return value
            case str() if status := cls.from_char(value):
                return status
            case str():
                return cls(value)
            case _:
                return cls(str(value))


@dataclass(frozen=True, slots=True)
class Tag:
    kind: str
    name: str
    value: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {'kind': self.kind, 'name': self.name, 'value': self.value}

    @classmethod
    def status(cls, name: str, value: str | None = None) -> 'Tag':
        return cls('status', name, value)

    @classmethod
    def mention(cls, name: str, value: str | None = None) -> 'Tag':
        return cls('mention', name, value)

    @classmethod
    def hashtag(cls, name: str) -> 'Tag':
        return cls('hashtag', name)

    @classmethod
    def project(cls, name: str) -> 'Tag':
        return cls('project', name)

    @classmethod
    def meta(cls, name: str, value: str | None = None) -> 'Tag':
        return cls('meta', name, value)

    @classmethod
    def priority(cls, name: str, value: str | None = None) -> 'Tag':
        return cls('priority', name, value)


@dataclass(slots=True)
class TodoThing:
    kind: ThingKind
    text: str
    raw: str = ''
    level: int = 0
    indent: int = 0
    tags: list[Tag] = field(default_factory=list)
    nodes: list['TodoThing'] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    parent: 'TodoDocument | TodoThing | None' = field(default=None, repr=False, compare=False)

    @property
    def is_section(self) -> bool:
        return self.kind == 'section'

    @property
    def is_item(self) -> bool:
        return self.kind == 'item'

    @property
    def is_session(self) -> bool:
        return self.kind == 'session'

    @property
    def label(self) -> str:
        return self.text

    @property
    def title(self) -> str:
        return self.text

    @property
    def items(self) -> list['TodoThing']:
        return [node for node in self.nodes if not node.is_section]

    @property
    def sections(self) -> list['TodoThing']:
        return [node for node in self.nodes if node.is_section]

    @property
    def tasks(self) -> list['TodoThing']:
        return self.items

    @property
    def visual_depth(self) -> int:
        return self.indent or max(self.level - 2, 0) * 2

    @property
    def own_status(self) -> TodoStatus:
        return next((status for tag in self.tags if tag.kind == 'status' and (status := TodoStatus.from_tag_name(tag.name))), TodoStatus.OPEN)

    @property
    def branch_status(self) -> TodoStatus:
        if not self.is_section and not self.nodes:
            return self.own_status
        if not (items := [*self.all_items()]):
            return TodoStatus.OPEN
        statuses = [item.own_status for item in items]
        return (
            TodoStatus.CANCELLED if all(status is TodoStatus.CANCELLED for status in statuses) else
            TodoStatus.DONE if all(status.value in _CLOSED for status in statuses) else
            TodoStatus.PROGRESS if any(status is not TodoStatus.OPEN for status in statuses) else
            TodoStatus.OPEN
        )

    @property
    def status(self) -> TodoStatus:
        return self.branch_status if self.is_section else self.own_status

    @property
    def is_done(self) -> bool:
        return self.status is TodoStatus.DONE

    @property
    def is_complete(self) -> bool:
        return self.branch_status.value in _CLOSED

    @property
    def due(self) -> str | None:
        return next((tag.value for tag in self.tags if tag.name == 'due'), None)

    @property
    def due_date(self) -> Date | None:
        if not (value := self.due):
            return None
        try:
            return Date.fromisoformat(value)
        except ValueError:
            return None

    @property
    def priority(self) -> str | None:
        return next((tag.value or tag.name for tag in self.tags if tag.kind == 'priority'), None)

    @property
    def assignees(self) -> list[str]:
        return [tag.name for tag in self.tags if tag.kind == 'mention']

    @property
    def categories(self) -> list[str]:
        return [tag.name for tag in self.tags if tag.kind == 'hashtag']

    @property
    def projects(self) -> list[str]:
        return [tag.name for tag in self.tags if tag.kind == 'project']

    def walk(self, *, include_self: bool = True) -> Iterator['TodoThing']:
        if include_self:
            yield self
        for node in self.nodes:
            yield from node.walk()

    def descendants(self, *, include_self: bool = False) -> Iterator['TodoThing']:
        yield from self.walk(include_self=include_self)

    def all_items(self) -> Iterator['TodoThing']:
        if not self.is_section:
            yield self
        for node in self.nodes:
            yield from node.all_items()

    def all_sections(self) -> Iterator['TodoThing']:
        if self.is_section:
            yield self
        for node in self.sections:
            yield from node.all_sections()

    def set_status(self, value: str | TodoStatus, *, cascade: bool = True) -> 'TodoThing':
        target = TodoStatus.from_any(value)
        if self.is_section:
            for item in self.all_items():
                item.set_status(target, cascade=False)
            return self
        self.tags = [tag for tag in self.tags if tag.kind != 'status']
        if target is not TodoStatus.OPEN:
            self.tags.insert(0, Tag.status('done', Date.today().isoformat()) if target is TodoStatus.DONE else Tag.status(target.tag_name()))
        if cascade:
            for node in self.nodes:
                node.set_status(target, cascade=True)
        return self

    def cycle_status(self) -> 'TodoThing':
        current = self.branch_status.value if self.is_section else self.status.value
        return self.set_status(_CYCLE_STATUS[(_CYCLE_STATUS.index(current) + 1) % len(_CYCLE_STATUS)])

    def toggle_status(self) -> 'TodoThing':
        return self.set_status(TodoStatus.OPEN if self.is_complete else TodoStatus.DONE)

    def edit_text(self, new_text: str) -> 'TodoThing':
        clean, tags = _extract_tags(new_text)
        if (old_status := [tag for tag in self.tags if tag.kind == 'status']) and not any(tag.kind == 'status' for tag in tags):
            tags = [*old_status, *tags]
        self.text, self.tags, self.raw = clean, tags, ''
        return self

    def to_text(self) -> str:
        return _render_section(self) if self.is_section else _render_item(self, depth=0)

    def to_dict(self) -> dict:
        return {
            'kind': self.kind,
            'text': self.text,
            'status': self.status.value,
            'branch_status': self.branch_status.value,
            'level': self.level,
            'indent': self.indent,
            'tags': [tag.to_dict() for tag in self.tags],
            'notes': self.notes,
            'nodes': [node.to_dict() for node in self.nodes],
            'assignees': self.assignees,
            'categories': self.categories,
            'projects': self.projects,
            'priority': self.priority,
            'due': self.due,
        }


type TodoNode = TodoThing


@dataclass(slots=True)
class TodoDocument:
    title: str | None = None
    title_tags: list[Tag] = field(default_factory=list)
    nodes: list[TodoThing] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def items(self) -> list[TodoThing]:
        return [node for node in self.nodes if not node.is_section]

    @property
    def tasks(self) -> list[TodoThing]:
        return self.items

    @property
    def sections(self) -> list[TodoThing]:
        return [section for node in self.nodes for section in node.all_sections()]

    @property
    def status(self) -> TodoStatus:
        if not (items := [*self.all_items()]):
            return TodoStatus.OPEN
        statuses = [item.own_status for item in items]
        return (
            TodoStatus.CANCELLED if all(status is TodoStatus.CANCELLED for status in statuses) else
            TodoStatus.DONE if all(status.value in _CLOSED for status in statuses) else
            TodoStatus.PROGRESS if any(status is not TodoStatus.OPEN for status in statuses) else
            TodoStatus.OPEN
        )

    @property
    def is_complete(self) -> bool:
        return self.status.value in _CLOSED

    def walk(self, *, include_self: bool = False):
        if include_self:
            yield self
        for node in self.nodes:
            yield from node.walk()

    def descendants(self, *, include_self: bool = False):
        yield from self.walk(include_self=include_self)

    def all_items(self) -> Iterator[TodoThing]:
        for node in self.nodes:
            yield from node.all_items()

    def all_sections(self) -> Iterator[TodoThing]:
        for node in self.nodes:
            yield from node.all_sections()

    def root_sections(self) -> list[TodoThing]:
        return [node for node in self.nodes if node.is_section]

    def find_section(self, text: str) -> TodoThing | None:
        target = text.lower()
        return next((section for section in self.sections if section.text.lower() == target), None)

    def find_item(self, index: int) -> TodoThing | None:
        return next((item for i, item in enumerate(self.all_items(), 1) if i == index), None)

    def indexed_items(self) -> list[tuple[int, TodoThing]]:
        return [(i, item) for i, item in enumerate(self.all_items(), 1)]

    def to_text(self) -> str:
        return _render_document(self)

    def to_dict(self) -> dict:
        return {
            'kind': 'document',
            'title': self.title,
            'status': self.status.value,
            'title_tags': [tag.to_dict() for tag in self.title_tags],
            'notes': self.notes,
            'nodes': [node.to_dict() for node in self.nodes],
        }


class TodoGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)

    def _get_rules(self):
        eol_re = r'\r\n|\r|\n'

        def eol(): return _(eol_re)
        def space(): return _(r'[ \t]+')
        def blank(): return _(r'[ \t]*'), eol
        def indent(): return _(r'[ \t]*')
        def heading_level(): return _(r'#{1,6}')
        def heading_text(): return _(r'[^\n]*')
        def heading(): return heading_level, space, heading_text, eol
        def header(): return name, _(r'[ \t]+TODO:[ \t]*', re.IGNORECASE), eol
        def project_name(): return _(rf'\S(?:.*?\S)?(?=\s*:[ \t]*(?:{eol_re}))')
        def project(): return indent, project_name, _(r'\s*:[ \t]*'), eol
        def checkbox(): return _(r'\[[ xX/\-]\]')
        def text(): return _(r'[^\n]*')
        def bullet(): return _(r'[-*\u2022+]|\d+[.)]')
        def bullet_item(): return indent, bullet, space, 0, checkbox, 0, space, text
        def checkbox_item(): return indent, checkbox, 0, space, text
        def item(): return [bullet_item, checkbox_item], eol
        def name(): return _(rf'\S(?:.*?\S)?(?=[ \t]+TODO:[ \t]*(?:{eol_re}))')
        def key(): return _(r'Start|End|Notes', re.IGNORECASE)
        def value(): return _(r'[^\n]*')
        def field(): return indent, key, _(r'\s*:\s*'), value, eol
        def inline():
            return _(r'(?:(?:x\s+(?:\d{4}-\d{2}-\d{2}\s+)?|\([A-Z]\)\s+)[^\n]*|(?=[^\n]*(?<!\w)(?:\+[A-Za-z][\w-]*|@[A-Za-z][\w.-]*(?:\([^)]+\))?|#[A-Za-z][\w-]*))[^\n]+)'), eol
        def note(): return _(r'[^\n]+'), eol
        
        def document(): return -1, [blank, heading, header, field, project, item, inline, note]
        
        return {name: value for name, value in locals().items() 
                if isinstance(value, types.FunctionType)}, document

    def parse(self, text: str, root=None, skipWS: bool = False, **kw: Any):
        text = _(r'\r\n|\r').sub('\n', text + ('\n' if not text.endswith('\n') else ''))
        kw.setdefault('packrat', True)
        kw.setdefault('resultSoFar', [])
        return parseLine(text, root or self.root, skipWS=skipWS, **kw)


class _ASTBuilder:
    def __init__(self):
        self.doc = TodoDocument()
        self.current_section: TodoThing | None = None
        self.section_stack: list[TodoThing] = []
        self.item_stack: list[TodoThing] = []
        self.session_fields: dict[str, str] = {}
        self.title_seen = False

    def build(self, nodes: Symbol | list) -> TodoDocument:
        self._walk(nodes if isinstance(nodes, list) else [nodes])
        self._flush_session()
        return self.doc

    def _walk(self, nodes: list) -> None:
        for node in nodes:
            if isinstance(node, str):
                continue
            if handler := getattr(self, f'_visit_{node.__name__}', None):
                handler(node)
            elif not isinstance(node.what, str):
                self._walk(node.what)

    def _flush_session(self) -> None:
        if not self.session_fields:
            return
        parent = self.current_section or self.doc
        tags = [Tag.meta(key, self.session_fields[key]) for key in ('start', 'end') if key in self.session_fields]
        notes = [self.session_fields['notes']] if self.session_fields.get('notes') else []
        _target_nodes(self.current_section, self.doc).append(TodoThing(kind='session', text='', tags=tags, notes=notes, parent=parent))
        self.session_fields.clear()

    def _start_section(self, text: str, tags: list[Tag] | None = None, *, level: int = 2, indent: int = 0) -> None:
        self._flush_session()
        self.item_stack.clear()
        section = TodoThing(kind='section', text=text, tags=tags or [], level=level, indent=indent)
        while self.section_stack and self.section_stack[-1].visual_depth >= section.visual_depth:
            self.section_stack.pop()
        if self.section_stack:
            section.parent = self.section_stack[-1]
            self.section_stack[-1].nodes.append(section)
        else:
            section.parent = self.doc
            self.doc.nodes.append(section)
        self.section_stack.append(section)
        self.current_section = section
        self.title_seen = True

    def _append_list_item(self, node: Symbol) -> None:
        self._flush_session()
        indent = len(_child_text(node, 'indent').expandtabs(4))
        source = ' '.join(filter(None, (_child_text(node, 'checkbox', strip=True), _child_text(node, 'text', strip=True))))
        text, tags = _extract_tags(source)
        item = TodoThing(kind='item', raw=_strip_eol(node.text).rstrip(), text=text, tags=tags, indent=indent)
        while self.item_stack and self.item_stack[-1].indent >= indent:
            self.item_stack.pop()
        parent = self.item_stack[-1] if self.item_stack else self.current_section or self.doc
        item.parent = parent
        (self.item_stack[-1].nodes if self.item_stack else _target_nodes(self.current_section, self.doc)).append(item)
        self.item_stack.append(item)
        self.title_seen = True

    def _append_flat_item(self, line: str) -> None:
        self._flush_session()
        self.item_stack.clear()
        text, tags = _extract_tags(line.strip())
        _target_nodes(self.current_section, self.doc).append(TodoThing(kind='item', raw=line.rstrip(), text=text, tags=tags, parent=self.current_section or self.doc))
        self.title_seen = True

    def _visit_blank(self, node: Symbol) -> None:
        self._flush_session()
        self.item_stack.clear()

    def _visit_heading(self, node: Symbol) -> None:
        level = len(_child_text(node, 'heading_level'))
        text, tags = _extract_tags(_child_text(node, 'heading_text', strip=True))
        if level == 1 and not self.title_seen:
            self.doc.title, self.doc.title_tags = text or None, tags
            self.title_seen = True
            self.current_section = None
            self.section_stack.clear()
            self.item_stack.clear()
            return
        self._start_section(text, tags, level=level)

    def _visit_header(self, node: Symbol) -> None:
        text, tags = _extract_tags(_child_text(node, 'name', strip=True))
        self._start_section(text, tags, level=2)

    def _visit_project(self, node: Symbol) -> None:
        indent = len(_child_text(node, 'indent').expandtabs(4))
        text, tags = _extract_tags(_child_text(node, 'project_name', strip=True))
        self._start_section(text, tags, level=2, indent=indent)

    def _visit_field(self, node: Symbol) -> None:
        if key := _child_text(node, 'key', strip=True).lower():
            self.session_fields[key] = _child_text(node, 'value', strip=True)
            self.title_seen = True

    def _visit_item(self, node: Symbol) -> None:
        self._append_list_item(node)

    def _visit_inline(self, node: Symbol) -> None:
        self._append_flat_item(_strip_eol(node.text))

    def _visit_note(self, node: Symbol) -> None:
        line = _strip_eol(node.text)
        stripped = line.strip()
        if not self.title_seen and stripped:
            self.title_seen = True
        if self.session_fields:
            prev = self.session_fields.get('notes', '')
            self.session_fields['notes'] = f'{prev}\n{stripped}'.lstrip('\n') if prev else stripped
        elif self.item_stack:
            self.item_stack[-1].notes.append(stripped)
        else:
            _target_notes(self.current_section, self.doc).append(stripped)


def _render_document(doc: TodoDocument) -> str:
    blocks = [f'# {doc.title}{f"  {tag_text}" if (tag_text := _format_tags(doc.title_tags)) else ""}' if doc.title else '']
    if doc.notes:
        blocks.append('\n'.join(_note_lines(doc.notes)))
    blocks.extend(_render_nodes(doc.nodes))
    return '\n\n'.join(block for block in blocks if block).strip()

def _render_nodes(nodes: list[TodoThing]) -> list[str]:
    result: list[str] = []
    item_cache: list[str] = []
    for node in nodes:
        if node.is_section:
            if item_cache:
                result.append('\n'.join(item_cache))
                item_cache.clear()
            result.append(_render_section(node))
        else:
            item_cache.append(_render_item(node, depth=0))
    return result + (['\n'.join(item_cache)] if item_cache else [])

def _render_section(node: TodoThing) -> str:
    heading = f"{' ' * node.visual_depth}{node.text}:".rstrip()
    if tag_text := _format_tags(node.tags):
        heading = f'{heading}  {tag_text}'
    return '\n\n'.join(block for block in [heading, *_render_nodes(node.nodes)] if block)


def _render_item(node: TodoThing, *, depth: int) -> str:
    indent = ' ' * node.indent if node.indent else '  ' * depth
    if node.is_session and not node.text:
        meta = {tag.name: tag.value for tag in node.tags if tag.kind == 'meta'}
        lines = [
            *[f'{indent}Start: {value}' for value in [meta.get('start')] if value],
            *[f'{indent}End: {value}' for value in [meta.get('end')] if value],
            *[f'{indent}{"Notes: " if i == 0 else "       "}{line}' for i, line in enumerate(_note_lines(node.notes))],
        ]
        return '\n'.join(lines).rstrip()
    line = f'{indent}{node.status.marker()} {node.text}{f"  {tag_text}" if (tag_text := _format_tags(node.tags, primary_status=node.status)) else ""}'.rstrip()
    lines = [line, *[f'{indent}  {note}'.rstrip() for note in _note_lines(node.notes)], *[_render_item(child, depth=depth + 1) for child in node.nodes]]
    return '\n'.join(line for line in lines if line).rstrip()


def _extract_tags(line: str) -> tuple[str, list[Tag]]:
    text, tags = line.strip(), []
    while text:
        match text:
            case _ if (m := _(r'^\[([ xX/\-])\](?:\s+|$)').match(text)) and (status := TodoStatus.from_char(m.group(1))):
                tags.append(Tag.status(status.tag_name()))
                text = text[m.end():].lstrip()
            case _ if m := _(r'^x\s+(?:(\d{4}-\d{2}-\d{2})\s+)?').match(text):
                tags.append(Tag.status('done', m.group(1)))
                text = text[m.end():].lstrip()
            case _ if m := _(r'^\(([A-Z])\)(?:\s+|$)').match(text):
                tags.append(Tag.priority(m.group(1), m.group(1)))
                text = text[m.end():].lstrip()
            case _:
                break
    parts, last = [], 0
    for match in _TAG_TOKEN_RE.finditer(text):
        parts.append(text[last:match.start()])
        last = match.end()
        if name := match.group('mention_name'):
            value = match.group('mention_value')
            tags.append(
                Tag.meta('due', 'today') if name == 'today' else
                Tag.meta('est', value) if name == 'estimate' else
                Tag.priority(value or 'priority', value) if name == 'priority' else
                Tag.status(name, value) if name in _STATUS_AT else
                Tag.mention(name, value)
            )
        elif key := match.group('meta_key'):
            tags.append(Tag.status(key, match.group('meta_value')) if key in _STATUS_NAMES else Tag.meta(key, match.group('meta_value')))
        elif name := match.group('hashtag_name'):
            tags.append(Tag.hashtag(name))
        elif name := match.group('project_name'):
            tags.append(Tag.project(name))
    deduped: list[Tag] = []
    status_index: dict[str, int] = {}
    for tag in tags:
        if tag.kind != 'status' or (i := status_index.get(tag.name)) is None:
            if tag.kind == 'status':
                status_index[tag.name] = len(deduped)
            deduped.append(tag)
        elif tag.value and not deduped[i].value:
            deduped[i] = tag
    clean = ' '.join((''.join([*parts, text[last:]])).split()).strip()
    return clean, deduped


def _format_tag(tag: Tag) -> str:
    return (
        f'@{tag.name}{f"({tag.value})" if tag.value else ""}' if tag.kind == 'mention' else
        f'#{tag.name}' if tag.kind == 'hashtag' else
        f'+{tag.name}' if tag.kind == 'project' else
        f'({tag.value or tag.name})' if tag.kind == 'priority' else
        f'{tag.name}:{tag.value}' if tag.value else
        tag.name
    )


def _format_tags(tags: list[Tag], *, primary_status: TodoStatus | None = None) -> str:
    groups = {'mention': [], 'hashtag': [], 'project': [], 'priority': [], 'meta': []}
    for tag in tags:
        match tag.kind:
            case 'mention':
                groups['mention'].append(_format_tag(tag))
            case 'hashtag':
                groups['hashtag'].append(_format_tag(tag))
            case 'project':
                groups['project'].append(_format_tag(tag))
            case 'priority':
                groups['priority'].append(_format_tag(tag))
            case 'status' if tag.value is None and primary_status and TodoStatus.from_tag_name(tag.name) == primary_status:
                pass
            case _:
                groups['meta'].append(_format_tag(tag))
    return '  '.join(part for part in [*groups['mention'], *groups['hashtag'], *groups['project'], *groups['priority'], *groups['meta']] if part)


def _strip_eol(text: str) -> str:
    return text.rstrip('\n')

def _child_text(node: Symbol, name: str, *, strip: bool = False) -> str:
    text = child.text if (child := node.find(name)) else ''
    return text.strip() if strip else text

def _target_nodes(section: TodoThing | None, doc: TodoDocument) -> list[TodoThing]:
    return section.nodes if section else doc.nodes

def _target_notes(section: TodoThing | None, doc: TodoDocument) -> list[str]:
    return section.notes if section else doc.notes

def _note_lines(notes: list[str]) -> list[str]:
    return [line for note in notes for line in note.splitlines() or ['']]


_grammar_singleton: TodoGrammar | None = None


def the_grammar() -> TodoGrammar:
    global _grammar_singleton
    if _grammar_singleton is None:
        _grammar_singleton = TodoGrammar()
    return _grammar_singleton

def parse_tree(text: str) -> Symbol:
    result, _ = the_grammar().parse(text, resultSoFar=[], skipWS=False)
    return result[0]

def parse(text: str) -> TodoDocument:
    return _ASTBuilder().build(parse_tree(text))

def parse_to_dict(text: str) -> dict:
    return parse(text).to_dict()

def render(node: TodoDocument | TodoThing) -> str:
    return node.to_text()
