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


def _extract_tags(line: str) -> tuple[str, list[Tag]]:
    """Extract and remove inline tags from *line*; return (clean_text, tags)."""
    tags: list[Tag] = []
    text = line

    if match := _(r'\[([ xX/\-])\]').search(text):
        if status := TodoStatus.from_char(match.group(1).lower()):
            tags.append(StatusTag(status.tag_name()))
        text = text[:match.start()] + text[match.end():]
    elif match := _(r'^x\s+(\d{4}-\d{2}-\d{2}\s+)?').match(text):
        tags.append(StatusTag('done', match.group(1).strip() if match.group(1) else None))
        text = text[match.end():]

    if match := _(r'^\(([A-Z])\)\s+').match(text):
        tags.append(PriorityTag(match.group(1), match.group(1)))
        text = text[match.end():]

    for match in _(r'(?<!\w)@([A-Za-z][\w.-]*)(?:\(([^)]*)\))?').finditer(text):
        name, value = match.group(1), match.group(2)
        match name:
            case 'today':
                tags.append(MetaTag('due', 'today'))
            case 'estimate':
                tags.append(MetaTag('est', value))
            case 'priority':
                tags.append(PriorityTag(value or 'priority', value))
            case _ if name in _STATUS_AT:
                tags.append(StatusTag(name, value))
            case _:
                tags.append(MentionTag(name, value))
    text = _(r'(?<!\w)@([A-Za-z][\w.-]*)(?:\(([^)]*)\))?').sub('', text)

    for match in _(r'(?<!\w)([a-z]\w*):(\S+)').finditer(text):
        key, value = match.group(1), match.group(2)
        tags.append(StatusTag(key, value) if key in _STATUS_NAMES else MetaTag(key, value))
    text = _(r'(?<!\w)([a-z]\w*):(\S+)').sub('', text)

    for match in _(r'(?<!\w)#([A-Za-z][\w-]*)').finditer(text):
        tags.append(HashTag(match.group(1)))
    text = _(r'(?<!\w)#([A-Za-z][\w-]*)').sub('', text)

    for match in _(r'(?<!\w)\+([A-Za-z][\w-]*)').finditer(text):
        tags.append(ProjectTag(match.group(1)))
    text = _(r'(?<!\w)\+([A-Za-z][\w-]*)').sub('', text)

    # Deduplicate status tags with the same name: keep the one with a value.
    seen: dict[str, int] = {}
    for i, tag in enumerate(tags):
        if isinstance(tag, StatusTag) and tag.name in seen:
            j = seen[tag.name]
            if tag.value and not tags[j].value:
                tags[j] = tag
            tags[i] = None  # type: ignore[assignment]
        elif isinstance(tag, StatusTag):
            seen[tag.name] = i
    tags = [t for t in tags if t is not None]

    return ' '.join(text.split()).strip(), tags


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
        def eol():
            return _(r'\r\n|\r|\n')

        def blank_line():
            return _(r'[ \t]*'), eol

        def markdown_heading_line():
            return _(r'#{1,6}[ \t]+[^\n]*'), eol

        def component_header_line():
            return _(r'\S.*?[ \t]+TODO:[ \t]*'), eol

        def doing_field_line():
            return _(r'[ \t]*(?:Start|End|Notes)\s*:[^\n]*'), eol

        def taskpaper_project_line():
            return _(r'\S[^:\n]*\s*:[ \t]*'), eol

        def list_item_line():
            return _(r'[ \t]*(?:(?:[-*•+]|\d+[.)])\s+(?:\[[ xX/\-]\]\s*)?[^\n]*|\[[ xX/\-]\]\s*[^\n]*)'), eol

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

    def _append_list_item(self, line: str) -> None:
        self._flush_doing()
        parts = _(
            r'^(?P<indent>[ \t]*)'
            r'(?:(?P<bullet>[-*\u2022+]|\d+[.)])\s+)?'
            r'(?:(?P<checkbox>\[[ xX/\-]\])\s+)?'
            r'(?P<body>.*)$'
        ).match(line)
        if not parts:
            self.visit_plain_line(Symbol('plain_line', [line, '\n']))
            return

        indent = len(parts.group('indent').expandtabs(4))
        checkbox = parts.group('checkbox')
        body = parts.group('body').strip()
        source = f'{checkbox} {body}'.strip() if checkbox else body
        text, tags = _extract_tags(source)
        item = TodoItem(raw=line.rstrip(), text=text, tags=tags, indent=indent)

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
        line = _strip_eol(node.text)
        if match := _(r'^(#{1,6})\s+(.*)').match(line):
            level = len(match.group(1))
            title, tags = _extract_tags(match.group(2).strip())
            if level == 1 and not self.title_seen:
                self.document.title      = title or None
                self.document.title_tags = tags
                self.title_seen          = True
                self.stack.clear()
                return ''
            self._start_section(title, tags, level=level)
        return ''

    def visit_component_header_line(self, node: Symbol) -> str:
        line = _strip_eol(node.text)
        if match := _(r'^(\S.*?)\s+TODO:\s*$', re.IGNORECASE).match(line):
            name, tags = _extract_tags(match.group(1).strip())
            self._start_section(name, tags, level=2)
        return ''

    def visit_taskpaper_project_line(self, node: Symbol) -> str:
        line = _strip_eol(node.text)
        if match := _(r'^(\S[^:]*)\s*:\s*$').match(line):
            name, tags = _extract_tags(match.group(1).strip())
            self._start_section(name, tags, level=2)
        return ''

    def visit_doing_field_line(self, node: Symbol) -> str:
        line = _strip_eol(node.text)
        if match := _(r'^\s*(Start|End|Notes)\s*:\s*(.*)', re.IGNORECASE).match(line):
            self.doing[match.group(1).lower()] = match.group(2).strip()
            self.title_seen = True
        return ''

    def visit_list_item_line(self, node: Symbol) -> str:
        self._append_list_item(_strip_eol(node.text))
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
