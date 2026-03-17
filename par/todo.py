"""PEG-based TODO parsing and canonical plaintext rendering."""

import re, types
from dataclasses import dataclass, field
from datetime import date as Date
from enum import Enum
from functools import lru_cache
from typing import Any, ClassVar, Iterator

from .__init__ import SimpleVisitor
from .pyPEG import Symbol, parseLine


_ = lru_cache(maxsize=256)(re.compile)

_STATUS_NAMES = frozenset({'done', 'cancelled', 'blocked'})
_STATUS_AT    = frozenset({'done', 'cancelled', 'blocked'})
_TAG_TOKEN_RE = _(
    r'(?<!\w)(?:@(?P<mention_name>[A-Za-z][\w.-]*)(?:\((?P<mention_value>[^)]*)\))?'
    r'|(?P<meta_key>[a-z]\w*):(?P<meta_value>\S+)'
    r'|#(?P<hashtag_name>[A-Za-z][\w-]*)'
    r'|\+(?P<project_name>[A-Za-z][\w-]*))'
)


class TodoStatus(str, Enum):
    """Task completion state — comparable as a plain string for backward compatibility."""
    OPEN        = 'open'
    IN_PROGRESS = 'in_progress'
    DONE        = 'done'
    BLOCKED     = 'blocked'
    CANCELLED   = 'cancelled'

    def marker(self) -> str:
        return {TodoStatus.OPEN: '[ ]', TodoStatus.IN_PROGRESS: '[/]',
                TodoStatus.DONE: '[x]', TodoStatus.BLOCKED: '[-]',
                TodoStatus.CANCELLED: '[-]'}[self]

    def tag_name(self) -> str:
        """Internal tag name stored in StatusTag.name (progress ≠ in_progress)."""
        return 'progress' if self is TodoStatus.IN_PROGRESS else self.value

    @classmethod
    def from_char(cls, char: str) -> 'TodoStatus | None':
        return {'x': cls.DONE, '/': cls.IN_PROGRESS, '-': cls.CANCELLED}.get(char.lower())

    @classmethod
    def from_tag_name(cls, name: str) -> 'TodoStatus | None':
        return {'done': cls.DONE, 'cancelled': cls.CANCELLED,
                'blocked': cls.BLOCKED, 'progress': cls.IN_PROGRESS}.get(name)


@dataclass(frozen=True, slots=True)
class Tag:
    """A named signal extracted from item or heading text."""
    name:  str
    value: str | None = None
    kind:  ClassVar[str] = 'tag'

    def __repr__(self) -> str:
        value = f'={self.value}' if self.value else ''
        return f'Tag({self.kind}:{self.name}{value})'

    def to_dict(self) -> dict[str, str | None]:
        return {'kind': self.kind, 'name': self.name, 'value': self.value}


@dataclass(frozen=True, slots=True)
class StatusTag(Tag):
    kind: ClassVar[str] = 'status'

@dataclass(frozen=True, slots=True)
class MentionTag(Tag):
    kind: ClassVar[str] = 'mention'

@dataclass(frozen=True, slots=True)
class HashTag(Tag):
    kind: ClassVar[str] = 'hashtag'

@dataclass(frozen=True, slots=True)
class ProjectTag(Tag):
    kind: ClassVar[str] = 'project'

@dataclass(frozen=True, slots=True)
class MetaTag(Tag):
    kind: ClassVar[str] = 'meta'

@dataclass(frozen=True, slots=True)
class PriorityTag(Tag):
    kind: ClassVar[str] = 'priority'


@dataclass(slots=True)
class TodoItem:
    """A task item with tags, notes, and optional nested children."""

    raw:      str
    text:     str
    indent:   int              = 0
    kind:     str              = 'task'
    tags:     list[Tag]        = field(default_factory=list)
    children: list['TodoItem'] = field(default_factory=list)
    notes:    list[str]        = field(default_factory=list)

    @property
    def status(self) -> TodoStatus:
        for tag in self.tags:
            if isinstance(tag, StatusTag):
                if s := TodoStatus.from_tag_name(tag.name):
                    return s
        return TodoStatus.OPEN

    @property
    def is_done(self) -> bool:
        return self.status is TodoStatus.DONE

    @property
    def due(self) -> str | None:
        return next((tag.value for tag in self.tags if tag.name == 'due'), None)

    @property
    def due_date(self) -> Date | None:
        if raw := self.due:
            try:
                return Date.fromisoformat(raw)
            except ValueError:
                pass
        return None

    @property
    def priority(self) -> str | None:
        return next((tag.value or tag.name for tag in self.tags if isinstance(tag, PriorityTag)), None)

    @property
    def assignees(self) -> list[str]:
        return [tag.name for tag in self.tags if isinstance(tag, MentionTag)]

    @property
    def categories(self) -> list[str]:
        return [tag.name for tag in self.tags if isinstance(tag, HashTag)]

    @property
    def projects(self) -> list[str]:
        return [tag.name for tag in self.tags if isinstance(tag, ProjectTag)]

    def all_items(self) -> Iterator['TodoItem']:
        yield self
        for child in self.children:
            yield from child.all_items()

    def to_text(self) -> str:
        return TodoTextVisitor().visit(self)


@dataclass(slots=True)
class TodoSection:
    """A named group of TODO items."""

    name:  str
    level: int            = 2
    items: list[TodoItem] = field(default_factory=list)
    notes: list[str]      = field(default_factory=list)
    tags:  list[Tag]      = field(default_factory=list)

    def all_items(self) -> Iterator[TodoItem]:
        for item in self.items:
            yield from item.all_items()

    def to_text(self) -> str:
        return TodoTextVisitor().visit(self)


@dataclass(slots=True)
class TodoDocument:
    """Logical AST root of a parsed TODO document."""

    title:      str | None        = None
    title_tags: list[Tag]         = field(default_factory=list)
    sections:   list[TodoSection] = field(default_factory=list)
    items:      list[TodoItem]    = field(default_factory=list)
    notes:      list[str]         = field(default_factory=list)

    def all_items(self) -> Iterator[TodoItem]:
        for item in self.items:
            yield from item.all_items()
        for section in self.sections:
            yield from section.all_items()

    def all_sections(self) -> list[TodoSection]:
        return list(self.sections)

    def to_text(self) -> str:
        return TodoTextVisitor().visit(self)


#  Internal helpers 

def _strip_eol(text: str) -> str:
    return text.rstrip('\n')


def _get_child_text(node: Symbol, name: str, *, strip: bool = False) -> str:
    text = child.text if (child := node.find(name)) else ''
    return text.strip() if strip else text


def _extract_tags(line: str) -> tuple[str, list[Tag]]:
    """Extract and remove inline tags from *line*; return (clean_text, tags)."""
    text, tags = line.strip(), []

    while text:
        if match := _(r'^\[([ xX/\-])\](?:\s+|$)').match(text):
            if status := TodoStatus.from_char(match.group(1)):
                tags.append(StatusTag(status.tag_name()))
        elif match := _(r'^x\s+(?:(\d{4}-\d{2}-\d{2})\s+)?').match(text):
            tags.append(StatusTag('done', match.group(1)))
        elif match := _(r'^\(([A-Z])\)(?:\s+|$)').match(text):
            tags.append(PriorityTag(match.group(1), match.group(1)))
        else:
            break
        text = text[match.end():].lstrip()

    parts, last = [], 0
    for match in _TAG_TOKEN_RE.finditer(text):
        parts.append(text[last:match.start()])
        last = match.end()

        if name := match.group('mention_name'):
            value = match.group('mention_value')
            tags.append(
                MetaTag('due', 'today') if name == 'today' else
                MetaTag('est', value) if name == 'estimate' else
                PriorityTag(value or 'priority', value) if name == 'priority' else
                StatusTag(name, value) if name in _STATUS_AT else
                MentionTag(name, value)
            )
        elif key := match.group('meta_key'):
            tags.append(StatusTag(key, match.group('meta_value')) if key in _STATUS_NAMES else MetaTag(key, match.group('meta_value')))
        elif name := match.group('hashtag_name'):
            tags.append(HashTag(name))
        elif name := match.group('project_name'):
            tags.append(ProjectTag(name))

    deduped: list[Tag] = []
    status_index: dict[str, int] = {}
    for tag in tags:
        if not isinstance(tag, StatusTag) or (i := status_index.get(tag.name)) is None:
            if isinstance(tag, StatusTag):
                status_index[tag.name] = len(deduped)
            deduped.append(tag)
        elif tag.value and not deduped[i].value:
            deduped[i] = tag

    return ' '.join((''.join([*parts, text[last:]])).split()).strip(), deduped


def _items_of(section: TodoSection | None, document: TodoDocument) -> list[TodoItem]:
    return section.items if section else document.items

def _notes_of(section: TodoSection | None, document: TodoDocument) -> list[str]:
    return section.notes if section else document.notes

def _note_lines(notes: list[str]) -> list[str]:
    lines: list[str] = []
    for note in notes:
        lines.extend(note.splitlines() or [''])
    return lines

def _format_tag(tag: Tag) -> str:
    if isinstance(tag, MentionTag):
        return f'@{tag.name}{f"({tag.value})" if tag.value else ""}'
    if isinstance(tag, HashTag):
        return f'#{tag.name}'
    if isinstance(tag, ProjectTag):
        return f'+{tag.name}'
    if isinstance(tag, PriorityTag):
        return f'pri:{tag.value or tag.name}'
    if tag.value is not None:
        return f'{tag.name}:{tag.value}'
    return tag.name

def _format_tags(tags: list[Tag], *, primary_status: TodoStatus | None = None) -> str:
    mentions:   list[str] = []
    hashtags:   list[str] = []
    projects:   list[str] = []
    priorities: list[str] = []
    meta:       list[str] = []

    for tag in tags:
        if isinstance(tag, MentionTag):
            mentions.append(_format_tag(tag))
        elif isinstance(tag, HashTag):
            hashtags.append(_format_tag(tag))
        elif isinstance(tag, ProjectTag):
            projects.append(_format_tag(tag))
        elif isinstance(tag, PriorityTag):
            priorities.append(_format_tag(tag))
        elif (isinstance(tag, StatusTag) and tag.value is None
              and primary_status is not None
              and TodoStatus.from_tag_name(tag.name) == primary_status):
            continue  # suppress checkbox-derived status tag (shown as marker already)
        else:
            meta.append(_format_tag(tag))

    parts = [*mentions, *hashtags, *projects, *priorities, *meta]
    return '  '.join(p for p in parts if p)


def _coerce_grammar(grammar: 'TodoGrammar | type[TodoGrammar] | None') -> 'TodoGrammar':
    if grammar is None:
        return TodoGrammar()
    return grammar() if isinstance(grammar, type) else grammar

def _coerce_visitor(visitor: Any, default_cls: type[Any], *args: Any) -> Any:
    if visitor is None:
        return default_cls(*args)
    return visitor(*args) if isinstance(visitor, type) else visitor


#  Grammar 

class TodoGrammar(dict):
    """Line-oriented pyPEG grammar for TODO-family documents."""

    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)

    def _get_rules(self):
        eol_re = r'\r\n|\r|\n'

        def eol():
            return _(eol_re)

        def space():
            return _(r'[ \t]+')

        def list_indent():
            return _(r'[ \t]*')

        def list_bullet():
            return _(r'[-*•+]|\d+[.)]')

        def list_checkbox():
            return _(r'\[[ xX/\-]\]')

        def list_body():
            return _(r'[^\n]*')

        def bullet_list_item():
            return list_indent, list_bullet, space, 0, list_checkbox, 0, space, list_body

        def checkbox_list_item():
            return list_indent, list_checkbox, 0, space, list_body

        def heading_level():
            return _(r'#{1,6}')

        def heading_title():
            return _(r'[^\n]*')

        def component_name():
            return _(rf'\S(?:.*?\S)?(?=[ \t]+TODO:[ \t]*(?:{eol_re}))')

        def taskpaper_project_name():
            return _(rf'\S(?:.*?\S)?(?=\s*:[ \t]*(?:{eol_re}))')

        def field_indent():
            return _(r'[ \t]*')

        def field_name():
            return _(r'Start|End|Notes', re.IGNORECASE)

        def field_value():
            return _(r'[^\n]*')

        def blank_line():
            return _(r'[ \t]*'), eol

        def markdown_heading_line():
            return heading_level, space, heading_title, eol

        def component_header_line():
            return component_name, _(r'[ \t]+TODO:[ \t]*', re.IGNORECASE), eol

        def doing_field_line():
            return field_indent, field_name, _(r'\s*:\s*'), field_value, eol

        def taskpaper_project_line():
            return taskpaper_project_name, _(r'\s*:[ \t]*'), eol

        def list_item_line():
            return [bullet_list_item, checkbox_list_item], eol

        def todo_txt_line():
            return _(r'(?:'
                     r'(?:x\s+(?:\d{4}-\d{2}-\d{2}\s+)?|\([A-Z]\)\s+)[^\n]*'
                     r'|(?=[^\n]*(?<!\w)(?:\+[A-Za-z][\w-]*|@[A-Za-z][\w.-]*(?:\([^)]+\))?|#[A-Za-z][\w-]*))[^\n]+'
                     r')'), eol

        def plain_line():
            return _(r'[^\n]+'), eol

        def document():
            return -1, [
                blank_line,
                markdown_heading_line,
                component_header_line,
                doing_field_line,
                taskpaper_project_line,
                list_item_line,
                todo_txt_line,
                plain_line,
            ]

        return {key: value for key, value in locals().items() if isinstance(value, types.FunctionType)}, document

    def parse(self, text: str, root=None, skipWS: bool = False, **kwargs: Any):
        text = _(r'\r\n|\r').sub('\n', text + ('\n' if not text.endswith('\n') else ''))
        kwargs.setdefault('packrat', True)
        kwargs.setdefault('resultSoFar', [])
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)


#  AST builder 

class TodoDocumentVisitor(SimpleVisitor):
    """Build the logical TODO AST from the pyPEG parse tree."""

    def __init__(self, grammar: TodoGrammar | None = None):
        super().__init__(grammar)
        self.document = TodoDocument()
        self.section: TodoSection | None = None
        self.stack: list[TodoItem] = []
        self.doing: dict[str, str] = {}
        self.title_seen = False

    def build(self, nodes: Symbol | list[Symbol]) -> TodoDocument:
        super().visit(nodes, root=True)
        self._flush_doing()
        return self.document

    def __end__(self) -> str:
        self._flush_doing()
        return ''

    def _flush_doing(self) -> None:
        if not self.doing:
            return
        tags: list[Tag]  = [MetaTag(key, self.doing[key]) for key in ('start', 'end') if key in self.doing]
        notes = [self.doing['notes']] if self.doing.get('notes') else []
        _items_of(self.section, self.document).append(
            TodoItem(raw='', text='', tags=tags, notes=notes, kind='session')
        )
        self.doing.clear()

    def _start_section(self, name: str, tags: list[Tag] | None = None, *, level: int = 2) -> None:
        self._flush_doing()
        self.stack.clear()
        self.section = TodoSection(name=name, tags=tags or [], level=level)
        self.document.sections.append(self.section)
        self.title_seen = True

    def _append_list_item(self, node: Symbol) -> None:
        self._flush_doing()
        indent = len(_get_child_text(node, 'list_indent').expandtabs(4))
        source = ' '.join(filter(None, (
            _get_child_text(node, 'list_checkbox', strip=True),
            _get_child_text(node, 'list_body', strip=True),
        )))
        text, tags = _extract_tags(source)
        item = TodoItem(raw=_strip_eol(node.text).rstrip(), text=text, tags=tags, indent=indent)

        while self.stack and self.stack[-1].indent >= indent:
            self.stack.pop()
        (self.stack[-1].children if self.stack else _items_of(self.section, self.document)).append(item)
        self.stack.append(item)
        self.title_seen = True

    def _append_flat_item(self, line: str) -> None:
        self._flush_doing()
        self.stack.clear()
        text, tags = _extract_tags(line.strip())
        _items_of(self.section, self.document).append(TodoItem(raw=line.rstrip(), text=text, tags=tags))
        self.title_seen = True

    def visit_blank_line(self, node: Symbol) -> str:
        self._flush_doing()
        self.stack.clear()
        return ''

    def visit_markdown_heading_line(self, node: Symbol) -> str:
        level = len(_get_child_text(node, 'heading_level'))
        title, tags = _extract_tags(_get_child_text(node, 'heading_title', strip=True))
        if level == 1 and not self.title_seen:
            self.document.title      = title or None
            self.document.title_tags = tags
            self.title_seen          = True
            self.stack.clear()
            return ''
        self._start_section(title, tags, level=level)
        return ''

    def visit_component_header_line(self, node: Symbol) -> str:
        name, tags = _extract_tags(_get_child_text(node, 'component_name', strip=True))
        self._start_section(name, tags, level=2)
        return ''

    def visit_taskpaper_project_line(self, node: Symbol) -> str:
        name, tags = _extract_tags(_get_child_text(node, 'taskpaper_project_name', strip=True))
        self._start_section(name, tags, level=2)
        return ''

    def visit_doing_field_line(self, node: Symbol) -> str:
        if name := _get_child_text(node, 'field_name', strip=True).lower():
            self.doing[name] = _get_child_text(node, 'field_value', strip=True)
            self.title_seen = True
        return ''

    def visit_list_item_line(self, node: Symbol) -> str:
        self._append_list_item(node)
        return ''

    def visit_todo_txt_line(self, node: Symbol) -> str:
        self._append_flat_item(_strip_eol(node.text))
        return ''

    def visit_plain_line(self, node: Symbol) -> str:
        line = _strip_eol(node.text)
        stripped = line.strip()
        if not self.title_seen and stripped:
            self.title_seen = True

        if self.doing:
            previous = self.doing.get('notes', '')
            self.doing['notes'] = f'{previous}\n{stripped}'.lstrip('\n') if previous else stripped
        elif self.stack:
            self.stack[-1].notes.append(stripped)
        else:
            _notes_of(self.section, self.document).append(stripped)
        return ''


#  Text renderer 

class TodoTextVisitor:
    """Render the logical TODO AST as canonical plaintext."""

    def visit(self, node: 'TodoDocument | TodoSection | TodoItem | list') -> str:
        match node:
            case TodoDocument():   return self._render_document(node)
            case TodoSection():    return self._render_section(node)
            case TodoItem():       return self._render_item(node, depth=0)
            case list():           return '\n\n'.join(self.visit(n) for n in node)
            case _:                return ''

    def _render_document(self, doc: TodoDocument) -> str:
        blocks: list[str] = []
        if doc.title:
            title = f'# {doc.title}'
            if tag_text := _format_tags(doc.title_tags):
                title = f'{title}  {tag_text}'
            blocks.append(title)
        if doc.notes:
            blocks.append('\n'.join(_note_lines(doc.notes)))
        if doc.items:
            blocks.append('\n'.join(self._render_item(item, depth=0) for item in doc.items))
        blocks.extend(self._render_section(s) for s in doc.sections)
        return '\n\n'.join(b for b in blocks if b).strip()

    def _render_section(self, section: TodoSection) -> str:
        heading = f"{'#' * max(2, section.level)} {section.name}".rstrip()
        if tag_text := _format_tags(section.tags):
            heading = f'{heading}  {tag_text}'
        blocks = [heading]
        if section.notes:
            blocks.append('\n'.join(_note_lines(section.notes)))
        if section.items:
            blocks.append('\n'.join(self._render_item(item, depth=0) for item in section.items))
        return '\n\n'.join(b for b in blocks if b)

    def _render_item(self, item: TodoItem, *, depth: int) -> str:
        indent = '    ' * depth

        if item.kind == 'session' and not item.text:
            lines: list[str] = []
            tag_map = {t.name: t.value for t in item.tags if isinstance(t, MetaTag)}
            if start := tag_map.get('start'):
                lines.append(f'{indent}Start: {start}')
            if end := tag_map.get('end'):
                lines.append(f'{indent}End: {end}')
            for i, note_line in enumerate(_note_lines(item.notes)):
                prefix = 'Notes: ' if i == 0 else '       '
                lines.append(f'{indent}{prefix}{note_line}')
            return '\n'.join(lines).rstrip()

        marker = item.status.marker()
        line   = f'{indent}{marker} {item.text}'.rstrip()
        if tag_text := _format_tags(item.tags, primary_status=item.status):
            line = f'{line}  {tag_text}'

        lines = [line]
        for note_line in _note_lines(item.notes):
            lines.append(f'{indent}    {note_line}'.rstrip())
        for child in item.children:
            lines.append(self._render_item(child, depth=depth + 1))
        return '\n'.join(lines).rstrip()


#  Public API 

def parse_todo_tree(text: str, grammar: 'TodoGrammar | type[TodoGrammar] | None' = None) -> Symbol:
    """Parse TODO text and return the raw pyPEG tree."""
    parser = _coerce_grammar(grammar)
    result, _rest = parser.parse(text, resultSoFar=[], skipWS=False)
    return result[0]

def parse_todo(
    text: str,
    grammar: 'TodoGrammar | type[TodoGrammar] | None' = None,
    visitor: 'TodoDocumentVisitor | type[TodoDocumentVisitor] | None' = None,
) -> TodoDocument:
    """Parse a TODO document into the logical TODO AST."""
    parser  = _coerce_grammar(grammar)
    tree    = parse_todo_tree(text, parser)
    builder = _coerce_visitor(visitor, TodoDocumentVisitor, parser)
    return builder.build(tree)

def parse_todo_items(text: str) -> list[TodoItem]:
    """Convenience helper returning all items in document order."""
    return list(parse_todo(text).all_items())

def render_text(
    todo: 'TodoDocument | TodoSection | TodoItem',
    visitor: 'TodoTextVisitor | type[TodoTextVisitor] | None' = None,
) -> str:
    """Render a parsed TODO AST node as canonical plaintext."""
    renderer = _coerce_visitor(visitor, TodoTextVisitor)
    return renderer.visit(todo)

def parseText(
    text: str,
    grammar: 'TodoGrammar | type[TodoGrammar] | None' = None,
    visitor: 'TodoTextVisitor | type[TodoTextVisitor] | None' = None,
) -> str:
    """Parse TODO text and return canonical plaintext output."""
    return render_text(parse_todo(text, grammar=grammar), visitor=visitor)

def parse_text(
    text: str,
    grammar: 'TodoGrammar | type[TodoGrammar] | None' = None,
    visitor: 'TodoTextVisitor | type[TodoTextVisitor] | None' = None,
) -> str:
    """Parse TODO text and return canonical plaintext output."""
    return parseText(text, grammar=grammar, visitor=visitor)

def parseTree(text: str, grammar: 'TodoGrammar | type[TodoGrammar] | None' = None) -> Symbol:
    """Backward-friendly alias for parse_todo_tree."""
    return parse_todo_tree(text, grammar=grammar)

def renderText(
    todo: 'TodoDocument | TodoSection | TodoItem',
    visitor: 'TodoTextVisitor | type[TodoTextVisitor] | None' = None,
) -> str:
    """Backward-friendly alias for render_text."""
    return render_text(todo, visitor=visitor)
