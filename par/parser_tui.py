#! env python
"""Interactive terminal UI for testing Par parsers."""

from bisect import bisect_right
from enum import Enum, auto
from importlib import import_module
from pathlib import Path
from typing import Any, Callable

try:
    from .pyPEG import Symbol
except ImportError:
    from par.pyPEG import Symbol
import urwid


PALETTE = [
    # (foreground, background, attr, ..., fg-hex, bg-hex)
    ("header"           ,"light gray,bold", "default"    , "bold"    , "#ffd866", ""),
    ("footer"           , "light gray"    , "default"    , ""        , "#d6d6d6", ""),
    ("status_ok"        , "light green"   , "default"    , ""        , "#8bd88b", ""),
    ("status_err"       , "light red,bold", "default"    , "bold"    , "#fb8076", ""),
    ("status_info"      , "yellow"        , "default"    , ""        , "#ffd866", ""),
    ("status_warn"      , "brown"         , "default"    , ""        , "#ffb86b", ""),
    ("key_hint"         , "light cyan"    , "default"    , ""        , "#7fc1ca", ""),

    ("input_text"       , "white"         , "default"    , ""        , "#d6d6d6", ""),
    ("output_text"      , "light gray"    , "default"    , ""        , "#cfcfcf", ""),
    ("output_symbol"    , "light cyan"    , "default"    , ""        , "#89c2b0", ""),
    ("output_name"      , "yellow"        , "default"    , ""        , "#ffd866", ""),
    ("panel_title"      ,"light gray,bold", "default"    , "bold"    , "#d6d6d6", ""),
    ("panel_title_focus", "yellow,bold"   , "default"    , "bold"    , "#ffd866", ""),

    # Tree styles
    ("tree_symbol"      , "light cyan"    , "default"    , ""        , "#89c2b0", ""),
    ("tree_symbol_focus", "black"         , "default"    , "standout", "#000000", ""),
    ("tree_name"        , "yellow"        , "default"    , ""        , "#ffd866", ""),
    ("tree_name_focus"  , "black"         , "default"    , "standout", "#000000", ""),
    ("tree_text"        , "brown"         , "default"    , ""        , "#ffb86b", ""),
    ("tree_text_focus"  , "black"         , "default"    , "standout", "#000000", ""),
    ("tree_node"        , "light gray"    , "default"    , ""        , "#d6d6d6", ""),
    ("tree_node_focus"  , "black"         , "default"    , "standout", "#000000", ""),
    ("tree_meta"        , "dark gray"     , "default"    , ""        , "#8a8a8a", ""),

    # Dialog
    ("dialog"           , "white"         , "default"    , ""        , "#d6d6d6", ""),
    ("dialog_title"     , "white,bold"    , "default"    , "bold"    , "#d6d6d6", ""),
    ("button"           , "white"         , "default"    , ""        , "#d6d6d6", ""),
    ("button_focus"     , "white,bold"    , "default"    , "bold"    , "#d6d6d6", ""),
]

AVAILABLE_PARSERS = {"md": "par.md", "scss": "par.scss", "filoname": "par.filoname"}

def get_parser(name: str) -> ParserWrapper:
    if name not in AVAILABLE_PARSERS:
        raise KeyError(f"Unknown parser '{name}'")
    return ParserWrapper(import_module(AVAILABLE_PARSERS[name]))


# Parser Infrastructure
class ParserWrapper:
    """Lightweight wrapper: call common parse helpers and extract pyPEG Symbol."""

    def __init__(self, module: Any) -> None:
        self.module = module
        self._grammar_cache: type | None = None

    def _is_symbol(self, obj: Any) -> bool:
        # Prefer explicit pyPEG types
        if isinstance(obj, Symbol):
            return True
        # Narrow fallback for other symbol-like objects (rare)
        if obj is not None and getattr(obj, "text", None) is not None and getattr(obj, "what", None) is not None:
            return True
        return False

    def _safe_call(self, fn: Callable, text: str, *, packrat: bool) -> Any:
        try:
            return fn(text, packrat=packrat)
        except TypeError:
            try:
                return fn(text)
            except TypeError:
                # Unable to call this function with expected signatures; skip it.
                return None

    def _find_symbol(self, obj: Any, depth: int = 0) -> Symbol | None:
        """Recursively search for a pyPEG Symbol in nested structures."""
        if depth > 50:
            return None
        if isinstance(obj, Symbol):
            return obj
        if isinstance(obj, (list, tuple)):
            for item in obj:
                if found := self._find_symbol(item, depth + 1):
                    return found
        return None

    def _get_grammar_class(self) -> type | None:
        """Find and cache the Grammar class from the module."""
        if self._grammar_cache is not None:
            return self._grammar_cache
        # Prefer an explicit `Grammar` attribute if present
        cls = getattr(self.module, "Grammar", None)
        if isinstance(cls, type):
            self._grammar_cache = cls
            return cls
        # Fallback: scan attributes containing 'Grammar'
        for attr in dir(self.module):
            if "Grammar" in attr:
                cls = getattr(self.module, attr)
                if isinstance(cls, type):
                    self._grammar_cache = cls
                    return cls
        return None

    def _parse_via_grammar(self, text: str, packrat: bool) -> Any | None:
        """Try to get AST by calling Grammar.parse() directly."""
        if (cls := self._get_grammar_class()) is None:
            return None
        try:
            inst = cls()
            if parse_fn := getattr(inst, "parse", None):
                call_kwargs = (
                    {"packrat": packrat},
                    {"skipWS": False, "packrat": packrat},
                    {"skipWS": True, "packrat": packrat},
                    {"skipWS": False},
                    {"skipWS": True},
                    {},
                )
                for kwargs in call_kwargs:
                    try:
                        out = parse_fn(text, **kwargs)
                    except (TypeError, SyntaxError):
                        continue
                    except Exception:
                        continue

                    if found := self._find_symbol(out):
                        return found
        except Exception:
            pass
        return None

    def parse(self, text: str, packrat: bool = False) -> tuple[Any, Any | None]:
        """Attempt known parse helpers, return (result, ast_or_None)."""
        candidates = (
            ("parseHtmlDebug", False),
            ("parseHtml", True),
            ("parseText", True),
            ("parseSCSSText", True),
            ("parseFileName", False),
            ("parseDebug", False),
            ("parse", True),
        )

        for name, supports_packrat in candidates:
            fn = getattr(self.module, name, None)
            if not callable(fn):
                continue
            out = self._safe_call(fn, text, packrat=packrat if supports_packrat else False)
            # If the function couldn't be called due to an incompatible signature,
            # skip to the next candidate.
            if out is None:
                continue
            found_ast = self._find_symbol(out)

            if found_ast is None:
                found_ast = self._parse_via_grammar(text, packrat)

            if isinstance(out, tuple):
                # Debug functions return (result, resources) - try grammar for AST
                return out, found_ast
            if self._is_symbol(out):
                return None, out
            return out, found_ast

        # Fallback: use Grammar.parse() directly
        if ast := self._parse_via_grammar(text, packrat):
            return None, ast

        return None, None

# AST Node Model
class NodeType(Enum):
    SYMBOL = auto();    TEXT = auto();    ROOT = auto()

class ASTNode:
    """Display-model node for the AST tree."""

    __slots__ = ("name", "text", "node_type", "children", "parent", "line")

    def __init__(
        self,
        name: str,
        text: str = "",
        node_type: NodeType = NodeType.SYMBOL,
        line: int | None = None,
    ) -> None:
        self.name = name
        self.text = text
        self.node_type = node_type
        self.line = line
        self.children: list[ASTNode] = []
        self.parent: ASTNode | None = None

    def add_child(self, child: ASTNode) -> None:
        child.parent = self
        self.children.append(child)

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @staticmethod
    def from_pyPEG(
        symbol: Any,
        *,
        seen: set[int] | None = None,
        depth: int = 0,
        line_for_offset: Callable[[int | None], int | None] | None = None,
    ) -> ASTNode:
        """Convert a pyPEG Symbol tree to ASTNode, deriving line numbers from offsets."""
        if seen is None:
            seen = set()

        # Plain string without pyPEG metadata (handle before cycle checks,
        # otherwise interned/reused strings may be incorrectly flagged as cycles).
        if isinstance(symbol, str):
            truncated = (symbol[:60] + "…") if len(symbol) > 60 else symbol
            return ASTNode("text", text=truncated, node_type=NodeType.TEXT)

        if depth > 100:
            return ASTNode("[max depth]", node_type=NodeType.TEXT)
        node_id = id(symbol)
        if node_id in seen:
            return ASTNode("[cycle]", node_type=NodeType.TEXT)
        seen.add(node_id)

        # pyPEG Symbol (explicit list-like)
        if isinstance(symbol, Symbol):
            name = getattr(symbol, "__name__", None) or type(symbol).__name__
            text_val = getattr(symbol, "text", "") or ""
            if len(text_val) > 60:
                text_val = text_val[:60] + "…"

            line = getattr(symbol, "line", None)
            if line is None and line_for_offset is not None:
                line = line_for_offset(getattr(symbol, "offset", None))

            node = ASTNode(name, text=text_val, node_type=NodeType.SYMBOL, line=line)

            for child in symbol:
                child_node = ASTNode.from_pyPEG(
                    child,
                    seen=seen,
                    depth=depth + 1,
                    line_for_offset=line_for_offset,
                )
                node.add_child(child_node)

            return node

        # Fallback for other symbol-like objects
        name = getattr(symbol, "__name__", None) or type(symbol).__name__
        text_val = getattr(symbol, "text", "") or ""
        if len(text_val) > 60:
            text_val = text_val[:60] + "…"

        line = getattr(symbol, "line", None)
        if line is None and line_for_offset is not None:
            line = line_for_offset(getattr(symbol, "offset", None))

        node = ASTNode(name, text=text_val, node_type=NodeType.SYMBOL, line=line)

        # If it's iterable (but not a string), try to walk children conservatively
        if isinstance(symbol, (list, tuple)):
            for child in symbol:
                child_node = ASTNode.from_pyPEG(
                    child,
                    seen=seen,
                    depth=depth + 1,
                    line_for_offset=line_for_offset,
                )
                node.add_child(child_node)

        return node


# urwid Tree Widgets
class ASTTreeWidget(urwid.TreeWidget):
    """Widget for displaying a single AST node."""

    # indent_cols = 1
    unexpanded_icon = urwid.SelectableIcon("▶", 0)
    expanded_icon = urwid.SelectableIcon("▼", 0)

    def get_display_text(self) -> list[tuple[str, str] | str]:
        node: ASTNode = self.get_node().get_value()
        parts: list[tuple[str, str] | str] = []

        style = {
            NodeType.SYMBOL: "tree_symbol",
            NodeType.TEXT: "tree_text",
            NodeType.ROOT: "tree_node",
        }.get(node.node_type, "tree_node")

        parts.append((style, node.name))

        if node.text:
            escaped = node.text.replace("\n", "⏎").replace("\t", "→")
            parts.append(("tree_text", f' "{escaped}"'))

        if node.line is not None:
            parts.append(("tree_meta", f" @{node.line}"))

        if node.children:
            parts.append(("tree_meta", f" ({len(node.children)})"))

        return parts

    def load_inner_widget(self) -> urwid.Widget:
        text = urwid.Text(self.get_display_text(), wrap="clip")
        return urwid.AttrMap(text, "tree_node", "tree_node_focus")

    def selectable(self) -> bool:
        return True

    def keypress(self, size: tuple[int], key: str) -> str | None:
        if key in ("right", "+", "l"):
            self.expanded = True
            self.update_expanded_icon()
            return None
        if key in ("left", "-", "h"):
            self.expanded = False
            self.update_expanded_icon()
            return None
        if key == " ":
            self.expanded = not self.expanded
            self.update_expanded_icon()
            return None
        return super().keypress(size, key)


class ASTTreeNode(urwid.TreeNode):
    def load_widget(self) -> ASTTreeWidget:
        return ASTTreeWidget(self)


class ASTParentNode(urwid.ParentNode):
    def load_widget(self) -> ASTTreeWidget:
        return ASTTreeWidget(self)

    def load_child_keys(self) -> list[int]:
        node: ASTNode = self.get_value()
        return list(range(len(node.children)))

    def load_child_node(self, key: int) -> urwid.TreeNode:
        node: ASTNode = self.get_value()
        child = node.children[key]
        depth = self.get_depth() + 1
        if child.children:
            return ASTParentNode(child, parent=self, key=key, depth=depth)
        return ASTTreeNode(child, parent=self, key=key, depth=depth)


class ASTTreeListBox(urwid.TreeListBox):
    """ListBox displaying the navigable AST tree."""

    def __init__(self, root: ASTNode | None = None) -> None:
        self._root = root
        if root:
            node = ASTParentNode(root) if root.children else ASTTreeNode(root)
            walker = urwid.TreeWalker(node)
        else:
            walker = urwid.SimpleFocusListWalker([urwid.Text(("tree_meta", "(no AST)"))])
        super().__init__(walker)

    def set_root(self, root: ASTNode | None) -> None:
        self._root = root
        if root:
            node = ASTParentNode(root) if root.children else ASTTreeNode(root)
            self.body = urwid.TreeWalker(node)
        else:
            self.body = urwid.SimpleFocusListWalker([urwid.Text(("tree_meta", "(no AST)"))])

    def _set_all_expanded(self, node: urwid.TreeNode, expanded: bool) -> None:
        """Recursively expand or collapse all nodes."""
        widget = node.get_widget()
        if hasattr(widget, "expanded"):
            widget.expanded = expanded
            widget.update_expanded_icon()
        if isinstance(node, urwid.ParentNode):
            for key in node.load_child_keys():
                self._set_all_expanded(node.load_child_node(key), expanded)

    def expand_all(self) -> None:
        if isinstance(self.body, urwid.TreeWalker):
            self._set_all_expanded(self.body.get_focus()[1], True)
            self._invalidate()

    def collapse_all(self) -> None:
        if isinstance(self.body, urwid.TreeWalker):
            self._set_all_expanded(self.body.get_focus()[1], False)
            self._invalidate()

    def keypress(self, size: tuple[int, int], key: str) -> str | None:
        if key == "e":
            self.expand_all()
            return None
        if key == "c":
            self.collapse_all()
            return None
        return super().keypress(size, key)


# Panel Widgets
class FocusableLineBox(urwid.LineBox):
    """LineBox that changes title style when focused."""

    def __init__(self, widget: urwid.Widget, title: str = "") -> None:
        super().__init__(
            widget,
            title=title,
            title_attr="panel_title",
            tline   ="─", bline   ="─", lline   ="│", rline   ="│",
            tlcorner="╭", trcorner="╮", blcorner="╰", brcorner="╯",
        )
        self._base_title = title

    def render(self, size: tuple[int, int], focus: bool = False) -> Any:
        self.title_attr = "panel_title_focus" if focus else "panel_title"
        return super().render(size, focus)


class InputPanel(urwid.Edit):
    """Multi-line text input with change callback."""

    def __init__(self, on_change: Callable[[str], None]) -> None:
        super().__init__(edit_text="", multiline=True, allow_tab=False)
        self._on_change = on_change
        urwid.connect_signal(self, "change", lambda w, t: self._on_change(t))


class OutputPanel(urwid.WidgetPlaceholder):
    """Switchable output: navigable tree view or rendered output."""

    def __init__(self) -> None:
        self._tree_view: ASTTreeListBox = ASTTreeListBox()
        # Two possible views: 'ast' (navigable AST tree) and 'html' (rendered output the Visitor, e.g. HTML for Markdown
        self._render_widget = urwid.Text("", wrap="any")
        self._render_view = urwid.ListBox(urwid.SimpleFocusListWalker([self._render_widget]))
        self._view_mode = "ast"
        super().__init__(self._tree_view)

    @property
    def view_mode(self) -> str:
        """Return current view mode: 'ast' or 'html'."""
        return self._view_mode

    def toggle_view_mode(self) -> None:
        """Cycle views: ast -> html -> ast."""
        if self._view_mode == "ast":
            self._view_mode = "html"
            self.original_widget = self._render_view
        else:
            self._view_mode = "ast"
            self.original_widget = self._tree_view

    @staticmethod
    def _build_line_lookup(source_text: str) -> Callable[[int | None], int | None]:
        line_starts = [0]
        line_starts.extend(i + 1 for i, ch in enumerate(source_text) if ch == "\n")
        source_len = len(source_text)

        def line_for_offset(offset: int | None) -> int | None:
            if offset is None or offset < 0:
                return None
            return bisect_right(line_starts, min(offset, source_len))

        return line_for_offset

    def set_ast(self, ast: Any, *, source_text: str = "") -> None:
        if ast:
            try:
                root = ASTNode.from_pyPEG(
                    ast,
                    line_for_offset=self._build_line_lookup(source_text),
                )
                self._tree_view.set_root(root)
            except Exception:
                self._tree_view.set_root(None)
        else:
            self._tree_view.set_root(None)

    def set_render(self, content: str) -> None:
        """Set the rendered output (e.g. HTML) for the render view."""
        try:
            self._render_widget.set_text(content or "")
        except Exception:
            # Fall back to a safe string representation
            self._render_widget.set_text(str(content) if content is not None else "")

    def clear(self) -> None:
        self._tree_view.set_root(None)
        self._render_widget.set_text("")


class Dialog(urwid.WidgetWrap):
    """Modal dialog box."""

    def __init__(
        self,
        title: str,
        body: urwid.Widget,
        buttons: list[tuple[str, Callable[[], None]]],
    ) -> None:
        button_widgets = []
        for label, callback in buttons:
            btn = urwid.Button(label)
            urwid.connect_signal(btn, "click", lambda b, cb=callback: cb())
            button_widgets.append(urwid.AttrMap(btn, "button", "button_focus"))

        pile = urwid.Pile(
            [
                urwid.AttrMap(urwid.Text(title, align="center"), "dialog_title"),
                urwid.Divider("─"),
                body,
                urwid.Divider(),
                urwid.Columns(button_widgets, dividechars=2),
            ]
        )
        box = urwid.LineBox(urwid.Filler(pile, valign="top"))
        super().__init__(urwid.AttrMap(box, "dialog"))


# Main Application
class ParserTUI:
    """Two-panel TUI for interactive parser testing."""

    def __init__(self) -> None:
        self._parser_names = list(AVAILABLE_PARSERS.keys())
        self._parser_idx = 0
        self._parser = get_parser(self._parser_names[0])
        self._packrat = False
        self._current_file: Path | None = None
        self._last_error: str | None = None
        self._loop: urwid.MainLoop | None = None
        self._dialog_open = False

        # Build UI
        self._input = InputPanel(self._on_input_change)
        self._output = OutputPanel()

        self._input_box = FocusableLineBox(
            urwid.AttrMap(
                urwid.ListBox(urwid.SimpleFocusListWalker([self._input])),
                "input_text",
            ),
            title=" Input ",
        )
        self._output_box = FocusableLineBox(
            urwid.AttrMap(self._output, "output_text"),
            title=" Output ",
        )

        self._columns = urwid.Columns(
            [("weight", 1, self._input_box), ("weight", 1, self._output_box)],
            dividechars=1,
        )

        self._header = urwid.AttrMap(
            urwid.Text(" Par Parser Tester ", align="center"), "header"
        )

        self._status_left = urwid.Text("")
        self._status_right = urwid.Text("", align="right")
        self._footer = urwid.AttrMap(
            urwid.Columns(
                [("weight", 2, self._status_left), ("weight", 1, self._status_right)]
            ),
            "footer",
        )

        self._frame = urwid.Frame(
            body=self._columns, header=self._header, footer=self._footer
        )

        self._update_status()

    @property
    def _current_parser_name(self) -> str:
        return self._parser_names[self._parser_idx]

    def _update_status(self) -> None:
        mode = self._output.view_mode
        packrat = "•packrat" if self._packrat else ""
        file_info = self._current_file.name if self._current_file else "(unsaved)"

        keys = "F1:View F2:Parser F3:Load F5:Parse F6:Packrat F7:View Tab:Switch q:Quit"

        if self._last_error:
            left = [("status_err", f" ✗ {self._last_error[:60]}")]
        else:
            left = [
                ("status_ok", f" ✓ {self._current_parser_name} "),
                ("status_info", f"[{mode}] "),
                ("status_warn", f"{packrat} ") if packrat else "",
                ("footer", f" {file_info}"),
            ]

        self._status_left.set_text([p for p in left if p])
        self._status_right.set_text(("key_hint", keys))

        # Update output title
        title = f" Output ({mode}) "
        self._output_box.set_title(title)

    def _on_input_change(self, text: str) -> None:
        self._parse_and_display(text)

    def _parse_and_display(self, text: str) -> None:
        if not text.strip():
            self._output.clear()
            self._last_error = None
            self._update_status()
            return

        try:
            result, ast = self._parser.parse(text, packrat=self._packrat)

            self._output.set_ast(ast, source_text=text)
            # Also set rendered output (e.g. HTML). If the parser returned a
            # debug tuple like (html, resources) prefer the first element.
            render_text = ""
            if result is None:
                render_text = ""
            elif isinstance(result, (tuple, list)) and result and isinstance(result[0], str):
                render_text = result[0]
            elif isinstance(result, str):
                render_text = result
            else:
                try:
                    render_text = str(result)
                except Exception:
                    render_text = ""

            self._output.set_render(render_text)
            self._last_error = None

        except Exception as e:
            self._last_error = f"{type(e).__name__}: {e}"

        self._update_status()

    def _cycle_parser(self) -> None:
        self._parser_idx = (self._parser_idx + 1) % len(self._parser_names)
        self._parser = get_parser(self._current_parser_name)
        self._last_error = None
        self._parse_and_display(self._input.edit_text)

    def _toggle_packrat(self) -> None:
        self._packrat = not self._packrat
        self._parse_and_display(self._input.edit_text)

    def _toggle_tree_view(self) -> None:
        # Cycle the output view (ast -> html -> ast)
        self._output.toggle_view_mode()
        self._update_status()

    def _show_dialog(self, dialog: urwid.Widget, width: int = 60, height: int = 10) -> None:
        overlay = urwid.Overlay(
            dialog,
            self._frame,
            align="center",
            width=("relative", width),
            valign="middle",
            height=height,
        )
        if self._loop:
            self._loop.widget = overlay
        self._dialog_open = True

    def _close_dialog(self) -> None:
        if self._loop:
            self._loop.widget = self._frame
        self._dialog_open = False
        self._update_status()

    def _load_file(self) -> None:
        edit = urwid.Edit("Path: ")

        def do_load() -> None:
            path = Path(edit.edit_text.strip())
            if path.exists() and path.is_file():
                try:
                    self._input.set_edit_text(path.read_text(encoding="utf-8"))
                    self._current_file = path
                    self._last_error = None
                except Exception as e:
                    self._last_error = f"Load failed: {e}"
            else:
                self._last_error = f"Not found: {path}"
            self._close_dialog()

        dialog = Dialog("Load File", edit, [("Load", do_load), ("Cancel", self._close_dialog)])
        self._show_dialog(dialog, height=8)

    def _handle_input(self, key: str) -> None:
        # Close any dialog on key
        if self._dialog_open and self._loop:
            if key == "esc":
                self._close_dialog()
            elif self._loop.widget is not self._frame and key not in (
                "up", "down", "left", "right", "enter", "tab", "backspace"
            ):
                # Help dialog closes on any key
                if isinstance(self._loop.widget, urwid.Overlay):
                    top = self._loop.widget.top_w
                    if isinstance(top, urwid.LineBox) and "Help" in str(getattr(top, "title_widget", "")):
                        self._close_dialog()
            return

        match key:
            case "f1" | "f7":
                self._toggle_tree_view()
            case "f2":
                self._cycle_parser()
            case "f3":
                self._load_file()
            case "f5":
                self._parse_and_display(self._input.edit_text)
            case "f6":
                self._toggle_packrat()
            case "f10" | "q":
                raise urwid.ExitMainLoop()
            case "tab":
                # Toggle focus between input and output panes
                self._columns.focus_position = 1 - self._columns.focus_position
            case "ctrl k":
                self._input.set_edit_text("")
                self._current_file = None

    def run(self) -> None:
        self._loop = urwid.MainLoop(
            self._frame, palette=PALETTE, unhandled_input=self._handle_input, handle_mouse=True, )

        try:
            self._loop.screen.set_terminal_properties(colors=256)
        except Exception:
            pass

        self._input.set_edit_text("# Type or paste text here\n## Press F1 for change view mode\n\n**bold** and _italic_\n")
        self._loop.run()


def main() -> None:
    ParserTUI().run()


if __name__ == "__main__":
    main()