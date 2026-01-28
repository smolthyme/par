
"""Advanced Markdown parsing and HTML conversion."""
from .__init__ import SimpleVisitor, MDHTMLVisitor # Visits parsed nodes and converts to HTML/text etc.

import re, types
from par.pyPEG import _not, _and, keyword, ignore, Symbol, parseLine

from dataclasses import dataclass, field, asdict

@dataclass(slots=True)
class ResourceStore:
    """Centralized storage for all resources tracked during markdown parsing."""
    
    links_ext: list = field(default_factory=list)
    links_int: list = field(default_factory=list)
    toc_items: list = field(default_factory=list)
    footnotes: list = field(default_factory=list)
    images:    list = field(default_factory=list)
    videos:    list = field(default_factory=list)
    audios:    list = field(default_factory=list)
    
    titles_ids:       dict = field(default_factory=dict)
    link_references:  dict = field(default_factory=dict)
    image_references: dict = field(default_factory=dict)
    
    
    def to_dict(self):
        """Return all resources as a dictionary for external access."""
        return asdict(self)
    
    #Create isolated context for visitor with fresh title IDs
    def nested_store(self):
        return ResourceStore(
            links_ext=self.links_ext,
            links_int=self.links_int,
            toc_items=[],  # Don't share ToC items for nested parsing
            footnotes=self.footnotes,
            images=self.images,
            videos=self.videos,
            audios=self.audios,
            titles_ids={},  # Fresh title IDs for nested content
            link_references=self.link_references,
            image_references=self.image_references,
        )

_ = re.compile

class MarkdownGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
        
    def _get_rules(self):
        ## Cheats for return value repeats
        #  0 = ? = Optional ; -1 = * = Zero or more ; -2 = + = One or more ; n = n matches
        
        ## basic
        def eol()              : return _(r'\r\n|\r|\n')
        def space()            : return _(r'[ \t]+')
        def wordlike()         : return _(r'[^\*_\s\d\.`]+') # Remove brackets maybe?
        def blankline()        : return 0, space, eol
        def blanklines()       : return -2, blankline
        
        ## shared content patterns
        def rest_of_line()     : return _(r'[^\r\n]+')
        def title_string()     : return _(r'["\']([^"\'\n\r]*)["\']|(\([^\)]*\))')
        def in_braces()        : return _(r'[^\s\)]+')
        def in_sq_braces()     : return _(r'[^\]]+')


        def literal()          : return _(r'u?r?([\'"])(?:\\.|(?!\1).)*\1', re.I|re.DOTALL)
        def htmlentity()       : return _(r'&\w+;')
        def escape_string()    : return _(r'\\'), _(r'.')
        def string()           : return _(r'[^\\\*_\^~ \t\r\n`,<\[\]]+')
        
        def fmt_bold()         : return _(r'\*\*'), words , _(r'\*\*')
        def fmt_italic()       : return _(r'\*'),   words , _(r'\*')
        def fmt_bold2()        : return _(r'(?<!\w)__'),   words , _(r'__(?!\w)')
        #def fmt_underline()    : return _(r'_'),    words , _(r'_')
        def fmt_italic2()      : return _(r'(?<!\w)_'),    words , _(r'_(?!\w)')
        def fmt_code()         : return _(r'`'),    words , _(r'`')
        def fmt_subscript()    : return _(r',,'),   words , _(r',,')
        def fmt_superscript()  : return _(r'\^'),   words , _(r'\^')
        def fmt_strikethrough(): return _(r'~~'),   words , _(r'~~')
        
        ## inline
        def longdash()         : return _(r"--\B")
        def hr()               : return _(r'(?:([-_*])[ \t]*\1*){3,}'), blankline
        def star_rating()      : return _(r"[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+ */ *\d+")
        
        ## embedded html
        def html_block()       : return _(r'<(table|pre|div|p|ul|h1|h2|h3|h4|h5|h6|blockquote|code|iframe)\b[^>]*?>[^<]*?<(/\1)>', re.I|re.DOTALL)
        def html_inline()      : return _(r'<(span|del|font|a|b|code|i|em|strong|sub|sup|input)\b[^>]*?>[^<]*?<(/\1)>|<(img|br|hr).*?/>', re.I|re.DOTALL)
        
        #def words()            : return word, -1, [space, word]
        def words(ig=r'(?!)')  : return word, -1, [space, ignore(ig), word] # (?!) is a negative lookahead that never matches   
        def text()             : return 0, space, -2, words
        def paragraph()        : return text, -1, [space, text], blanklines
        
        def directive_name()   : return _(r'\w+')
        def directive_title()  : return _(r'[^\n\r]+')
        def directive()        : return _(r'\.\.'), 0, space, directive_name, 0, space, _(r'::'), 0, directive_title
        
        def block_kwargs_key() : return _(r'[^=,\)\n]+')
        def block_kwargs_val() : return _(r'[^\),\n]+')
        def block_kwargs()     : return block_kwargs_key, 0, (_(r'='), block_kwargs_val)
        
        ## footnote
        def footnote()         : return _(r'\[\^\w+\]')
        def footnote_text()    : return list_first_para, -1, [list_indent_lines, list_lines]
        def footnote_desc()    : return footnote, _(r':'), footnote_text
        
        ## pre
        def pre_lang()         : return 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs))
        def pre_text()         : return _(r'.*?(?=```|~~~+|</code>)', re.M|re.DOTALL)
        def pre_indented()     : return _(r'(?:(?:    |\t).+\n?)+', re.M), -1, blankline  # Plain indented code block
        def pre_fenced()       : return _(r'```|~~~+|<code>'), 0, pre_lang, blankline, pre_text, _(r'```|~~~+|</code>'), -2, blankline
        def pre()              : return [pre_indented, pre_fenced]
        
        ## class and id definition
        def attr_def_id()      : return _(r'#[^\s\}]+')
        def attr_def_class()   : return _(r'\.[^\s\}]+')
        def attr_def_set()     : return [attr_def_id, attr_def_class], -1, (space, [attr_def_id, attr_def_class])
        def attr_def()         : return _(r'\{'), attr_def_set, _(r'\}')
        
        ## titles / subject
        def title_text()       : return _(r'[^\[\]\n#\{\}]+', re.U)
        def hashes()           : return _(r'#{1,6}')
        def atx_title()        : return hashes, 0, space, title_text, 0, space, 0, hashes, 0, space, 0, attr_def, -2, blankline
        def setext_underline() : return _(r'[ \t]*[-=]+[ \t]*')
        def setext_title()     : return title_text, 0, space, 0, attr_def, blankline, setext_underline, -2, blankline
        def title()            : return [atx_title, setext_title]
        
        ## table
        def table_sep()        : return _(r'\|')
        def table_td()         : return _(r'[^\|\r\n]*'), table_sep
        def table_horiz_line() : return _(r'\s*:?-+:?\s*'), table_sep
        def table_other()      : return rest_of_line()
        def table_head()       : return 0, table_sep, -2, table_td, -1, table_other, blankline
        def table_separator()  : return 0, table_sep, -2, table_horiz_line, -1, table_other, blankline
        def table_body_line()  : return 0, table_sep, -2, table_td, -1, table_other, blankline
        def table_body()       : return -2, table_body_line
        def table()            : return table_head, table_separator, table_body
        
        # Cards
        def card_content()     : return _(r'(?:(?!\|\]).)+', re.DOTALL)
        def card()             : return _(r'\[\|'), 0, space, 0, card_content, 0, space, _(r'\|\]'), 0, attr_def
        
        # Horizontal items
        def side_block_head()  : return _(r'\|\|\|'), 0, space, 0, attr_def, blankline
        def side_block_cont()  : return _not(_(r'\|\|\|')), [card, text, lists, paragraph], blankline
        def side_block()       : return side_block_head, -2, side_block_cont, -1, blankline
        
        ## lists
        def check_radio()      : return _(r'\[[\*Xx ]?\]|<[\*Xx ]?>'), space
        def list_rest_of_line(): return _(r'.+'), blankline
        def list_first_para()  : return 0, check_radio, -1, (0, space, text), -1, blanklines
        def list_lines()       : return list_norm_line, -1, [list_indent_lines, blankline]
        def list_indent_line() : return _(r' {4}|\t'), list_rest_of_line
        def list_norm_line()   : return _(r' {1,4}'), text, -1, (0, space, text), -1, blanklines
        def list_indent_lines(): return list_indent_line, -1, list_indent_line, -1, blanklines
        def list_content()     : return list_first_para, -1, [list_indent_lines, list_lines]
        def bullet_list_item() : return 0, _(r' {1,4}'), _(r'[\*\+\-]'), space, list_content
        def number_list_item() : return 0, _(r' {1,4}'), _(r'\d+\.'), space, list_content
        def lists()            : return -2, [bullet_list_item, number_list_item], -1, blankline
        
        ## Definition Lists
        def dl_dt()            : return _(r"^(?!=\s*[\*\d])"), -2, words(ig=r'--\B'), 0, _(r'--'), blankline
        def dl_dd_content()    : return 0, _(r"[ \t]+"), [lists, pre, paragraph]
        def dl_dd()            : return [space, _(r':\s*')], dl_dd_content
        def dl_dt_n_dd()       : return dl_dt, dl_dd, -1, dl_dd
        def dl()               : return -2, dl_dt_n_dd
        
        ## quote
        def quote_text()       : return text, blankline
        def quote_blank_line() : return _(r'>[ \t]*'), blankline
        def quote_line()       : return _(r'> (?!- )'), quote_text
        def quote_name()       : return text
        def quote_date()       : return _(r'[^\r\n\)]+')
        def quote_attr()       : return _(r'> --? '), quote_name, 0, (_(r"\("), quote_date, _(r"\)")), blankline
        def quote_lines()      : return [quote_blank_line, quote_line]
        def blockquote()       : return -2, quote_lines, 0, quote_attr, -1, blankline
        
        # Raw URLs
        def raw_url()          : return _(r'(?<![\(\[])\b(?:https?|ftp)://[^\s\)<>]+(?:\([^\s\)<>]*\))?[^\s\)<>]*', re.I)
        
        # Email addresses
        def email_address()    : return _(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Link components (using shared patterns)
        def link_text()        : return in_sq_braces()
        def link_url()         : return in_braces()
        def link_title()       : return title_string()
        def link_label()       : return in_sq_braces()
        
        # Inline links
        def inline_link()      : return _(r'\['), 0, link_text, _(r'\]'), _(r'\('), 0, space, link_url, 0, (space, link_title), 0, space, _(r'\)')
        
        # Reference links
        def reference_link()   : return _(r'\['), link_text, _(r'\]'), 0, space, _(r'\['), 0, link_label, _(r'\]')
        
        # Reference link definitions (using shared patterns)
        def link_ref_label()   : return in_sq_braces()
        def link_ref_url()     : return _(r'[^\s]+')
        def link_ref_title()   : return title_string()
        def link_reference()   : return _(r'^\s*\['), link_ref_label, _(r'\]:'), space, link_ref_url, 0, (space, link_ref_title), 0, space, blankline
        
        # Images - inline (using shared patterns)
        def image_alt()        : return in_sq_braces()
        def image_url()        : return in_braces()
        def image_title()      : return title_string()
        def inline_image()     : return _(r'!\['), 0, image_alt, _(r'\]'), _(r'\('), 0, space, image_url, 0, (space, image_title), 0, space, _(r'\)'), 0, attr_def
        
        # Images - reference (note: allows empty label)
        def image_ref_label()  : return _(r'[^\]]*')
        def reference_image()  : return _(r'!\['), 0, image_alt, _(r'\]'), 0, space, _(r'\['), 0, image_ref_label, _(r'\]'), 0, attr_def
        
        # Clickable images (inline image wrapped in inline link)
        def image_link()       : return _(r'\['), _(r'!\['), 0, image_alt, _(r'\]'), _(r'\('), 0, space, image_url, 0, (space, image_title), 0, space, _(r'\)'), _(r'\]'), _(r'\('), 0, space, link_url, 0, (space, link_title), 0, space, _(r'\)'), 0, attr_def

        # Buttons - syntax: ((Label|>url)), ((Label|>> url)), ((Label|/form-id or /action)), ((Label|$ js))
        def button_label()    : return _(r'[^|\)]+')
        # Allow any content up until the closing '))' sequence (so JS with parens is permitted)
        def button_action()   : return _(r'(?:>>|>|/|\$)'), 0, _(r'.*(?=\)\))', re.S)
        def button()          : return _(r'\(\('), 0, button_label, _(r'\|'), 0, button_action, _(r'\)\)'), 0, attr_def
        
        # Wiki-style links (wiki_link_text uses shared bracketed_text)
        def wiki_link_page()   : return _(r'[^\]#\|]+')
        def wiki_link_anchor() : return _(r'#[^\]#\|]*')
        def wiki_link_text()   : return in_sq_braces()
        def wiki_link()        : return _(r'\[\['), 0, wiki_link_page, 0, wiki_link_anchor, 0, (_(r'\|'), wiki_link_text), _(r'\]\]')
        
        # Wiki-style images
        def wiki_image_file()  : return _(r'[^\|\]]+')
        def wiki_image_align() : return _(r'left|center|right', re.I)
        def wiki_image_width() : return _(r'\d+%?|\d+px|[\d\.]+(?:em|rem|vw)')
        def wiki_image_height(): return _(r'\d+%?|\d+px|[\d\.]+(?:em|rem|vh)')
        def wiki_image()       : return _(r'\[\[image:'), wiki_image_file, 0, (_(r'\|'), 0, wiki_image_align), 0, (_(r'\|'), 0, wiki_image_width), 0, (_(r'\|'), 0, wiki_image_height), _(r'\]\]')
        
        def word()             : return [
                escape_string,
                html_block, html_inline,
                # Links and images (before formatting)
                image_link, button, inline_image, reference_image, wiki_image,
                inline_link, reference_link, wiki_link,
                raw_url, email_address,
                # Formatting
                fmt_bold, fmt_bold2, fmt_italic, fmt_italic2, fmt_code,
                fmt_subscript, fmt_superscript, fmt_strikethrough,
                footnote, longdash,
                htmlentity, star_rating, string, wordlike
            ]
        
        def content(): return -2, [blankline,
                link_reference,
                hr, directive,
                pre, html_block, lists,
                card, side_block, table, dl, blockquote, footnote_desc,
                title, paragraph ]
        
        def article(): return content
        
        return {k: v for k, v in locals().items() if isinstance(v, types.FunctionType)}, article
    
    def parse(self, text:str, root=None, skipWS=False, **kwargs):
        # Normalise on unix-style line ending and we end with a newline
        text = re.sub(r'\r\n|\r', '\n', text + ("\n" if not text.endswith("\n") else ''))
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)


class MarkdownHtmlVisitor(MDHTMLVisitor):    
    def __init__(self, tag_class={}, grammar=None, footnote_id=1, resources=None):
        super().__init__(grammar)
        
        self.tag_class   = tag_class
        self.footnote_id = footnote_id
        self.resources   = resources if resources is not None else ResourceStore()
        self._current_section_level = None
        self._title_id_begin_level: int | None = 1
    
    def visit(self, nodes: Symbol|list[Symbol], root=False) -> str:
        if root:
            # Collect link and image references first
            [self._collect_link_reference(obj) for obj in nodes[0].find_all('link_reference')]
            # Collect titles for ToC
            [self._alt_title(onk) for onk in nodes[0].find_all('title')]
        
        return super(MarkdownHtmlVisitor, self).visit(nodes, root)
    
    def parse_markdown(self, text, peg=None, *, title_id_begin_level: int | None = 1):
        g = self.grammar or MarkdownGrammar()
        if isinstance(peg, str):
            peg = g[peg]
        resultSoFar = []
        result, rest = g.parse(text, root=peg, resultSoFar=resultSoFar, skipWS=False)
        # Create nested visitor with fresh title IDs for isolated context
        nested_resources = self.resources.nested_store()
        v = self.__class__(self.tag_class, g, footnote_id=self.footnote_id, resources=nested_resources)
        v._title_id_begin_level = title_id_begin_level
        parsed_output = v.visit(result[0])
        self.footnote_id = v.footnote_id
        # Ensure any open sections are closed
        parsed_output += v._close_section()
        
        return parsed_output

    def fmt_tag(self, node: Symbol, html_tag: str, strip_chars: str) -> str:
        if a := node.find('words'):
            return self.visit(a)
        return node.text.strip(strip_chars)
    
    def visit_string(self, node: Symbol) -> str:
        return self.to_html_charcodes(node.text)

    def visit_blankline(self, node: Symbol) -> str:
        return '\n'

    def visit_longdash(self, node: Symbol) -> str:
        return '—'

    def visit_escape_string(self, node: Symbol) -> str:
        # Return the literal character following the escape backslash
        return node.text[1:] if node.text and node.text.startswith('\\') else node.text

    def visit_htmlentity(self, node: Symbol) -> str:
        # Preserve HTML entities like &nbsp; without double-escaping
        return node.text

    def visit_hr(self, node: Symbol) -> str:
        return self.tag('hr', enclose=1)

    def visit_paragraph(self, node: Symbol) -> str:
        if content := self.visit(node).strip():
            return self.tag('p', content, enclose=2)
        else:
            return ''

    def visit_lists_begin(self, node: Symbol) -> str:
        self.lists = []
        return ''

    def visit_list_line(self, node: Symbol) -> str:
        return node.text

    def visit_list_indent_line(self, node: Symbol):
        return (text_node := node.find('list_rest_of_line')) and text_node.text

    def visit_bullet_list_item(self, node: Symbol) -> str:
        self.lists.append(('b', node.find('list_content')))
        return ''

    def visit_number_list_item(self, node: Symbol) -> str:
        self.lists.append(('n', node.find('list_content')))
        return ''

    def visit_check_radio(self, node: Symbol) -> str:
        return self.tag('input', '', newline=False, attrs=('checked' if node.text[1] in ['x', 'X', '*'] else ""), enclose=2,
                type='checkbox' if node.text[0] == '[' else 'radio' if node.text[0] == '<' else '')

    def visit_lists_end(self, node: Symbol) -> str:
        def process_node(n):
            text = ''.join(self.visit(x) for x in n)
            t = self.parse_markdown(text, 'content').rstrip()
            
            # If content starts with a single paragraph, unwrap it
            if t.startswith('<p>') and t.count('<p>') == 1:
                if (close_idx := t.find('</p>')) != -1:
                    return t[3:close_idx] + t[close_idx+4:] # i.e. <p> and </p>
            
            return t

        def create_list(lists):
            l_items = []; old = None; parent = None
            
            for _type, _node in lists:
                if _type == old:
                    l_items.append(self.tag('li', process_node(_node)))
                else:
                    if parent:
                        l_items.append(self.tag(parent, enclose=3))
                    parent = 'ul' if _type == 'b' else 'ol'
                    l_items.append(self.tag(parent))
                    l_items.append(self.tag('li', process_node(_node)))
                    old = _type
            if len(l_items) > 0 and parent:
                l_items.append(self.tag(parent, enclose=3))
            
            return ''.join(l_items)
        return create_list(self.lists)

    def visit_dl_begin(self, node: Symbol) -> str:
        return self.tag('dl', newline=True)

    def visit_dl_end(self, node: Symbol) -> str:
        return self.tag('dl', enclose=3)

    def visit_dl_dt(self, node: Symbol) -> str:
        return self.tag('dt', self.visit(node).strip(), enclose=2, newline=True)

    def visit_dl_dd(self, node: Symbol) -> str:
        description_nodes = node.find_all('dl_dd_content')
        description_content = ''.join(self.visit(n) for n in description_nodes).strip()
        return self.tag('dd', description_content+'\n', newline=True)

    def visit_fmt_bold_begin(self, node: Symbol) -> str:
        return self.tag('strong', newline=False)
    
    def visit_fmt_bold(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'strong', '*_')

    def visit_fmt_bold_end(self, node: Symbol) -> str:
        return self.tag('strong', enclose=3, newline=False)
    
    visit_fmt_bold2_begin = visit_fmt_bold_begin
    visit_fmt_bold2 = visit_fmt_bold
    visit_fmt_bold2_end = visit_fmt_bold_end

    def visit_fmt_italic_begin(self, node: Symbol) -> str:
        return self.tag('em', newline=False)

    def visit_fmt_italic(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'em', '*_')
    
    def visit_fmt_italic_end(self, node: Symbol) -> str:
        return self.tag('em', enclose=3, newline=False)
    
    visit_fmt_italic2_begin = visit_fmt_italic_begin
    visit_fmt_italic2 = visit_fmt_italic
    visit_fmt_italic2_end = visit_fmt_italic_end

    def visit_fmt_underline_begin(self, node: Symbol) -> str:
        return self.tag('u', newline=False)
    
    def visit_fmt_underline(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'u', '_')
    
    def visit_fmt_underline_end(self, node: Symbol) -> str:
        return self.tag('u', enclose=3, newline=False)

    def visit_fmt_code_begin(self, node: Symbol) -> str:
        return self.tag('code', newline=False)
    
    def visit_fmt_code(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'code', '`')

    def visit_fmt_code_end(self, node: Symbol) -> str:
        return self.tag('code', enclose=3, newline=False)

    def visit_fmt_subscript_begin(self, node: Symbol) -> str:
        return self.tag('sub', newline=False)
    
    def visit_fmt_subscript(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'sub', ',')

    def visit_fmt_subscript_end(self, node: Symbol) -> str:
        return self.tag('sub', enclose=3, newline=False)

    def visit_fmt_superscript_begin(self, node: Symbol) -> str:
        return self.tag('sup', newline=False)
    
    def visit_fmt_superscript(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'sup', '^')

    def visit_fmt_superscript_end(self, node: Symbol) -> str:
        return self.tag('sup', enclose=3, newline=False)

    def visit_fmt_strikethrough_begin(self, node: Symbol) -> str:
        return self.tag('span', style="text-decoration: line-through", newline=False)

    def visit_fmt_strikethrough(self, node: Symbol) -> str:
        return self.fmt_tag(node, 'span', '~')

    def visit_fmt_strikethrough_end(self, node: Symbol) -> str:
        return self.tag('span', enclose=3, newline=False)

    def visit_pre(self, node: Symbol) -> str:
        cwargs = {}; kwargs = {}
        if (lang := node.find('pre_lang')):
            for n in lang.find_all('block_kwargs'):
                if (k := n.find('block_kwargs_key')):
                    key = k.text
                    val = v_node.text if (v_node := n.find('block_kwargs_val')) else None
                    if key == 'lang' or val is None:
                        cwargs['class'] = 'language-' + (val or key)
                    else:
                        kwargs[key] = val or 'language-' + key
        
        if pre_text := node.find('pre_text') or node.find('pre_indented'):
            pre_txt = pre_text.text
            # Find the minimum indent among non-empty lines and remove it
            lines = pre_txt.splitlines()
            indent_len = min((len(line) - len(line.lstrip(' \t')) for line in lines if line.strip()), default=0)
            if indent_len > 0:
                pre_txt = '\n'.join(line[indent_len:] if len(line) >= indent_len else line for line in lines)
            
            code_content = self.to_html_charcodes(pre_txt.strip("` \t\n"))
            return self.tag('pre', self.tag('code', code_content, newline=False, **cwargs), **kwargs)
        else:
            return self.tag('pre', self.tag('code', node.text.strip("` \t\n"), newline=False, **cwargs), **kwargs)


    def visit_quote_line(self, node: Symbol) -> str:
        # Grammar: quote_line = '> (?!- )', quote_text - visit the quote_text child directly
        return (qt.text if (qt := node.find('quote_text')) else node.text.lstrip('> '))

    def visit_blockquote(self, node: Symbol) -> str:
        # Strip leading '>' markers from each line and parse the inner markdown so nested
        lines = node.text.splitlines()
        stripped = '\n'.join(line.lstrip('> ').rstrip() for line in lines).strip() + '\n'
        result = self.parse_markdown(stripped, 'content')
        
        attrib = node.find("quote_name")
        atrdat = node.find("quote_date")
        if attrib:
            result = f"{result} &mdash; {self.tag('i', attrib.text, _class='quote-attrib')}"
        if atrdat:
            result = result + self.tag('span', self.tag("span", atrdat.text, _class='text-date'), _class='quote-timeplace')
        return self.tag('blockquote', result.strip())

    def visit_table_sep(self, node: Symbol) -> str:
        return ''

    def get_title_id(self, level: int, begin: int | None = None) -> str:
        """Generate a deterministic heading id."""
        begin = self._title_id_begin_level if begin is None else begin
        if begin is None:
            begin = level
            self._title_id_begin_level = begin

        titles = self.resources.titles_ids
        titles[level] = titles.get(level, 0) + 1

        ids = [str(titles.get(l, 0)) for l in range(begin, level + 1)]
        return f"title_{'-'.join(ids)}"

    def _alt_title(self, node: Symbol):
        node  = node.what[0]
        level = 1
        match node.__name__:
            case 'atx_title':
                if (level := node.find('hashes')) and level.text:
                    level = len(level.text)
                else:level = 1
            case 'setext_title':
                if (marker := node.find('setext_underline')) and marker.text:
                    level = 1 if marker.text[0] == '=' else 2
        
        _cls, _id = self._extract_attrs(node)
        _id = _id or self.get_title_id(level)
        title = (title_node := node.find('title_text')) and title_node.text
        self.resources.toc_items.append((level, _id, title))

    def _get_title(self, node: Symbol, level: int):
        _cls, _id = self._extract_attrs(node)
        _id = _id or self.get_title_id(level)
        title_raw = (title_node := node.find('title_text')) and title_node.text.strip() or "!Bad title!"
        # Render inline markdown within titles (support bold/italic/code/longdash etc.)
        title_rendered = self.parse_markdown(title_raw, 'text').strip()
        anchor = self.tag('a', enclose=2, newline=False, _class='anchor', href=f'#{_id}')
        section_s = self._open_section(self.slug(f"{title_raw}"))
        
        return section_s + self.tag(f'h{level}', f"{title_rendered}{anchor}", id=_id, _class=_cls)

    def visit_atx_title(self, node: Symbol) -> str:
        level = len(level.text) if (level := node.find('hashes')) and level.text else 1
        return self._get_title(node, level)

    def visit_setext_title(self, node: Symbol) -> str:
        marker = noder.text[0] if (noder := node.find('setext_underline')) else '='
        level = 1 if marker == '=' else 2
        return self._get_title(node, level)

    def visit_indent_block_line(self, node: Symbol) -> str:
        return node[1].text

    def visit_star_rating(self, node: Symbol) -> str:
        # Grammar already matched pattern, just split on '/'
        parts = node.text.split('/')
        stars = len(parts[0].strip())
        outta = parts[1].strip() if len(parts) > 1 else '5'
        return self.tag('span', '⭐'*stars, _class='star-rating', title=f"{stars} stars out of {outta}")

    def visit_card(self, node: Symbol) -> str:
        if content_node := node.find('card_content'):
            # Cards act like isolated documents: start heading ids at title_1 regardless of level.
            content = self.parse_markdown(content_node.text.strip(), 'content', title_id_begin_level=None).strip()
        else:
            content = ''
        
        _cls, _id = self._extract_attrs(node)
        return self.tag('div', f"\n{content}\n", _class=f"card {_cls}".strip(), id=_id or None)

    def visit_side_block(self, node: Symbol) -> str:
        content = [self.parse_markdown(thing.text, 'content').strip()
                for thing in node.find_all('side_block_cont')]
        
        if head := node.find('side_block_head'):
            _cls, _id = self._extract_attrs(head)
            return self.tag('div', f"\n{'\n'.join(content)}\n", enclose=1, _class=f"collection-horiz {_cls or ''}", id=_id)
        else:
            return self.tag('div', f"\n{'\n'.join(content)}\n", enclose=1, _class="collection-horiz")

    def visit_table_begin(self, node: Symbol) -> str:
        self.table_align = {}
        if separator := node.find('table_separator'):
            for i, x in enumerate(list(separator.find_all('table_horiz_line')) + list(separator.find_all('table_other'))):
                t = x.text.strip("| \t")
                self.table_align[i] = 'center' if t.startswith(':') and t.endswith(':') else 'left' if t.startswith(':') else 'right' if t.endswith(':') else ''
        return self.tag('table')

    def visit_table_head(self, node: Symbol) -> str:
        s = [self.tag('thead')+self.tag('tr', newline=False)]
        for t in ('table_td', 'table_other'):
            for x in node.find_all(t):
                s.append(self.tag('th', child=self.visit(x).strip(), enclose=2, newline=False))
        s.append(self.tag('tr', enclose=3)+self.tag('thead', enclose=3))
        return ''.join(s)

    def visit_table_separator(self, node: Symbol) -> str:
        return ''

    def visit_table_body(self, node: Symbol) -> str:
        return self.tag('tbody', "\n"+self.visit(node), enclose=2, newline=False)

    def visit_table_body_line(self, node: Symbol) -> str:
        nodes = list(node.find_all('table_td')) + list(node.find_all('table_other'))
        s = [self.tag('tr', newline=False)]
        for i, x in enumerate(nodes):
            text = self.visit(x)
            if text != "":
                s.append(self.tag('td', self.parse_markdown(text, 'text').strip(),
                    align=self.table_align.get(i, ''), newline=False, enclose=2))
            else:
                s.append(self.tag("td", "", newline=False, enclose=2))
        s.append(self.tag('tr', enclose=3))
        return ''.join(s)

    def visit_table_end(self, node: Symbol) -> str:
        return self.tag('table', enclose=3)

    def visit_directive(self, node: Symbol):
        if (name := node.find('directive_name')) and name.text in ['toc', 'contents'] and self.resources.toc_items:
            toc = [self.tag('section', _class='toc')]
            count = 1; hi = 0
            for lvl, anchor, title in self.resources.toc_items:
                if lvl > hi:
                    toc.append(self.tag('ul'))
                elif lvl < hi:
                    toc.append(self.tag('ul', enclose=3))
                hi = lvl
                toc.append(self.tag('li', self.tag('a', title, href=f"#{anchor}", newline=False)))
                count += 1
            toc.append(self.tag('ul', enclose=3))
            toc.append(self.tag('section', enclose=3, newline=False))
            # Since we visited these before generating, reset the dict to make sure headings get correct id's
            self.resources.titles_ids.clear()
            return ''.join(toc)

    def visit_footnote(self, node: Symbol) -> str:
        name = node.text[2:-1]
        _id = self.footnote_id
        self.footnote_id += 1
        return self.tag('sup', self.tag('a', f"{_id}", href=f"#fn-{name}", _class='footnote-rel inner', newline=False), id=f"fnref-{name}")

    def visit_footnote_desc(self, node):
        name = node.find('footnote').text.strip('[^]')
        if name in [fn['name'] for fn in self.resources.footnotes]:
            raise Exception("The footnote %s is already existed" % name)

        txt = self.visit(node.find('footnote_text')).rstrip()
        text = self.parse_markdown(txt, 'content').rstrip()
        self.resources.footnotes.append({'name': name, 'text': text})
        return ''

    def _open_section(self, id):
        stry = ""
        if self._current_section_level is not None:
            stry += self._close_section()
        self._current_section_level = id
        return stry+self.tag('section', '', id=f'section-{id}')

    def _close_section(self):
        if hasattr(self, '_current_section_level') and self._current_section_level is not None:
            self._current_section_level = None
            return self.tag('section', enclose=3)
        return ''

    def _extract_title(self, text: str) -> str:
        """Extract title from quoted or parenthesized text"""
        text = text.strip()
        if  (text.startswith('"') and text.endswith('"')) or \
            (text.startswith("'") and text.endswith("'")) or \
            (text.startswith('(') and text.endswith(')')):
            return text[1:-1]
        return text

    def _collect_link_reference(self, node: Symbol):
        """Collect reference link definitions during initial pass"""
        if (label_node :=node.find('link_ref_label')) and ( url_node := node.find('link_ref_url')):
            title_node = node.find('link_ref_title')
            label = label_node.text.lower()
            url = url_node.text
            title = self._extract_title(title_node.text) if title_node else None
            
            # Store both as link reference and image reference
            self.resources.link_references[label]  = {'url': url, 'title': title}
            self.resources.image_references[label] = {'url': url, 'title': title}

    def _is_safe_url(self, url: str) -> bool:
        """Check if URL is safe (not javascript:, vbscript:, data:)"""
        return not any(url.lower().strip().startswith(d) for d in ['javascript:', 'vbscript:', 'data:'])

    def _get_media_type(self, url: str) -> tuple[str, str | None]:
        """Determine media type and metadata from URL."""
        if 'youtube.com' in url or 'youtu.be' in url:
            for pattern in [
                _(r'youtube\.com/watch\?v=([^&]{11})'),
                _(r'youtu\.be/([^?]{11})'),
                _(r'youtube\.com/embed/([^?]{11})'),
                _(r'youtube\.com/v/([^?]{11})')]:
                if match := pattern.search(url):
                    return 'youtube', match.group(1)
        
        ext = url.lower().split('.')[-1] if '.' in url else ''
        if ext in {'mp4', 'm4v', 'mkv', 'webm'}:
            return 'video', ext
        if ext in {'mp3', 'm4a', 'aac', 'ogg', 'oga', 'opus'}:
            return 'audio', ext
        
        return 'image', None

    def _render_media(self, url: str, alt: str, title: str | None = None, enclose: int = 1, style: str | None = None, content: str = '', _class: str = '', _id: str = '') -> str:
        """Unified media rendering logic"""
        media_type, meta = self._get_media_type(url)
        
        if media_type == 'youtube':
            self.resources.videos.append(url)
            yt_class = f'yt-embed {_class}'.strip() if _class else 'yt-embed'
            return self.tag('object', '', attrs=f' class="{yt_class}" data="https://www.youtube.com/embed/{meta}"', enclose=2)
        
        elif media_type == 'video':
            self.resources.videos.append(url)
            src = self._prefix_local_image(url)
            return self.tag('video', controls="yesplz", disablePictureInPicture="True", 
                            playsinline="True", src=src, type=f'video/{meta}', enclose=enclose, _class=_class, id=_id or None)
        
        elif media_type == 'audio':
            self.resources.audios.append(url)
            src = self._prefix_local_image(url)
            mime = 'audio/mpeg' if meta == 'mp3' else f'audio/{meta}'
            return self.tag('audio', controls="yesplz", src=src, type=mime, enclose=enclose, _class=_class, id=_id or None)
            
        else: # Image
            self.resources.images.append(url)
            src = self._prefix_local_image(url)
            return self.tag('img', content, src=src, alt=alt, title=title, style=style, enclose=enclose, newline=False, _class=_class, id=_id or None)

    def _render_link(self, url: str, text: str, title: str | None = None) -> str:
        """Unified link rendering logic"""
        if not self._is_safe_url(url):
            return text
            
        self.resources.links_ext.append(url)
        return self.tag('a', text, href=url, title=title, newline=False)

    def visit_raw_url(self, node: Symbol) -> str:
        return self._render_link(node.text, node.text)

    def visit_email_address(self, node: Symbol) -> str:
        import random
        email = node.text
        result = [  '&#64;' if char == '@' else
                    '&#46;' if char == '.' else
                    (f'&#x{ord(char):x};' if random.choice([True, False]) else f'&#{ord(char)};')
                    for char in email ]
        return self.tag('a', ''.join(result), href=f'mailto:{email}', newline=False)

    def visit_inline_link(self, node: Symbol) -> str:
        if not (url_node := node.find('link_url')):
            return self.tag('a', "Malformed link")
        
        text = (text_node.text if (text_node := node.find('link_text')) else url_node.text)
        url = url_node.text
        title = (self._extract_title(title_node.text) if (title_node := node.find('link_title')) else None)
        
        return self._render_link(url, text, title)

    def visit_reference_link(self, node: Symbol) -> str:
        if not (text_node := node.find('link_text')):
            return node.text
        
        text = text_node.text
        label = (label_node.text.lower() 
                if (label_node := node.find('link_label')) and label_node.text 
                else text.lower())
        
        if not (ref := self.resources.link_references.get(label)):
            return node.text
        
        return self._render_link(ref['url'], text, ref.get('title'))

    def visit_button(self, node: Symbol) -> str:
        if label := (node.find('button_label')):
            label = label.text.strip()
            action_node = node.find('button_action')
            if not action_node:
                return node.text
            action = action_node.text.strip()
            if action.startswith('>>'):
                marker = '>>'
                rest = action[2:].strip()
            else:
                marker = action[0]
                rest = action[1:].strip()

            _cls, _id = self._extract_attrs(node)
            cls_str = _cls.strip() if _cls else ''

            # Buttons that navigate to a URL (single or double >)
            if marker in ('>', '>>'):
                url = rest
                if not self._is_safe_url(url):
                    return node.text
                target = '_blank' if marker == '>>' else None
                attrs = f'class="{cls_str}"' if cls_str else ''
                if _id:
                    attrs += (f' id="{_id}"') if attrs else f'id="{_id}"'
                # Render inner button without trailing newline to avoid extra newline before closing form
                return self.tag('form', self.tag('button', label, attrs=' type="submit"', newline=False), action=url, method='get', target=target, attrs=attrs)

            # Slash-prefixed: form action (POST) if 'submit' in path, otherwise a button referencing form id
            if marker == '/':
                if 'submit' in action.lower():
                    attrs = f'class="{cls_str}"' if cls_str else ''
                    if _id:
                        attrs += (f' id="{_id}"') if attrs else f'id="{_id}"'
                    return self.tag('form', self.tag('button', label, attrs=' type="submit"', newline=False), action=action, method='post', attrs=attrs)
                else:
                    formid = rest.lstrip('/').strip()
                    # Pass class on button if present; preserve desired attribute order
                    if cls_str:
                        return self.tag('button', label, attrs=f' type="submit" form="{formid}"', _class=cls_str)
                    return self.tag('button', label, attrs=f' type="submit" form="{formid}"')

            # JS onclick
            if marker == '$':
                return self.tag('button', label, attrs=f' type="button" onclick="{rest}"', _class=cls_str if cls_str else '')

        return node.text

    def visit_link_reference(self, node: Symbol) -> str:
        return ''

    def visit_wiki_link(self, node: Symbol) -> str:
        page   = (page_node.text   if   (page_node := node.find('wiki_link_page')) else '')
        anchor = (anchor_node.text if (anchor_node := node.find('wiki_link_anchor')) else '')
        text   = (text_node.text   if   (text_node := node.find('wiki_link_text')) else page)
        
        url = (page.lower().replace(' ', '-') + '.html' + anchor) if page else anchor
        
        self.resources.links_int.append(url)
        return self.tag('a', text or page, href=url, newline=False)

    def _prefix_local_image(self, url: str) -> str:
        """Prefix local images with images/ directory if not already prefixed"""
        if url.startswith(('http://', 'https://', 'ftp://', '/')):
            return url
        if not url.startswith('images/'):
            return f'images/{url}'
        return url

    def visit_image_link(self, node: Symbol) -> str:
        """Handle [![alt](image-url)](link-url) syntax - generates <a><img/></a>"""
        alt = (alt_node.text if (alt_node := node.find('image_alt')) else None)
        
        # Extract image URL and title
        image_url = (image_url_node.text if (image_url_node := node.find('image_url')) else '')
        image_title_nodes = list(node.find_all('image_title'))
        image_title = self._extract_title(image_title_nodes[0].text) if image_title_nodes else None
        
        link_title = None
        link_title_nodes = list(node.find_all('link_title'))
        if link_title_nodes:
            idx = 1 if image_title else 0
            if len(link_title_nodes) > idx:
                link_title = self._extract_title(link_title_nodes[idx].text)
        
        # Safety checks
        link_url = (link_url_node.text if (link_url_node := node.find('link_url')) else '')
        if not self._is_safe_url(image_url) or not self._is_safe_url(link_url):
            return node.text
        
        img_tag = self._render_media(image_url, alt or "", image_title, enclose=0, content=alt or "")
        
        _cls, _id = self._extract_attrs(node)
        self.resources.links_ext.append(link_url)
        return self.tag('a', img_tag, href=link_url, title=link_title, newline=False, _class=_cls, id=_id or None)

    def _extract_attrs(self, node: Symbol) -> tuple[str, str]:
        """Extract class and id attributes from attr_def nodes"""
        _id = _class = ''
        
        if (attr_def := next((n for n in node.find_all_here('attr_def')), None)):
            for class_node in attr_def.find_all('attr_def_class'):
                _class += (class_node.text[1:] + ' ')  # Skip the leading '.'
            
            if id_node := attr_def.find('attr_def_id'):
                _id = id_node.text[1:]  # Skip the leading '#'
        
        return _class, _id

    # Image visitors
    def visit_inline_image(self, node: Symbol) -> str:
        if not (url_node := node.find('image_url')):
            return node.text
        
        alt = (alt_node.text if (alt_node := node.find('image_alt')) else '')
        url = url_node.text
        title = (self._extract_title(title_node.text) 
                if (title_node := node.find('image_title')) else None)
        
        if not self._is_safe_url(url):
            return node.text
        
        _cls, _id = self._extract_attrs(node)
        return self._render_media(url, alt, title, enclose=1, _class=_cls, _id=_id)

    def visit_reference_image(self, node: Symbol) -> str:
        alt = (alt_node.text if (alt_node := node.find('image_alt')) else '')
        label = (label_node.text.lower() 
                if (label_node := node.find('image_ref_label')) and label_node.text 
                else alt.lower())
        
        if not (ref := self.resources.image_references.get(label)):
            return node.text
        
        url = ref['url']
        title = ref.get('title')
        
        if not self._is_safe_url(url):
            return node.text
        
        _cls, _id = self._extract_attrs(node)
        return self._render_media(url, alt, title, enclose=2, _class=_cls, _id=_id)

    def visit_wiki_image(self, node: Symbol) -> str:
        if not (file_node := node.find('wiki_image_file')):
            return node.text
        
        url = file_node.text
        align  = ( align_node.text if  (align_node := node.find('wiki_image_align')) else "")
        width  = ( width_node.text if  (width_node := node.find('wiki_image_width')) else None)
        height = (height_node.text if (height_node := node.find('wiki_image_height')) else None)
        
        if not self._is_safe_url(url):
            return node.text
        
        # Build style attributes
        styles = []

        match align.strip().lower():
            case 'left':
                styles.append('float: left; margin-right: 1em;')
            case 'right':
                styles.append('float: right; margin-left: 1em;')
            case 'center':
                styles.append('display: block; margin-left: auto; margin-right: auto;')
        
        if width:
            if not any(unit in width for unit in ['%', 'px', 'em', 'rem', 'vw']):
                width = f'{width}px'
            styles.append(f'width: {width};')
        
        if height:
            if not any(unit in height for unit in ['%', 'px', 'em', 'rem', 'vh']):
                height = f'{height}px'
            styles.append(f'height: {height};')
        
        style = ' '.join(styles) if styles else None
        
        return self._render_media(url, '', None, enclose=2, style=style)

    def __end__(self):
        s = []; 
        if hasattr(self, '_current_section_level'):
            s.append(self._close_section())
            self._current_section_level = None

        if self.resources.footnotes:
            s.append(self.tag('div', _class='footnotes', newline=False) + self.tag('ol', newline=False))
            for note in self.resources.footnotes:
                s.append(self.tag('li', id=f"fn-{note['name']}", newline=False, enclose=0))
                s.append(note['text'] + "\n")
                s.append(self.tag('a', '↩', href=f'#fnref-{note['name']}', _class='footnote-backref inner', newline=False))
                s.append(self.tag('li', enclose=3, newline=False))
            s.append(self.tag('ol', enclose=3, newline=False) + self.tag('div', enclose=3, newline=False))
        return '\n'.join(s).strip()

def parseText(text, grammar=None, visitor=None):
    """Parse markdown text and return plain text representation"""
    g = (grammar or MarkdownGrammar)()
    result, rest = g.parse(text, resultSoFar=[], skipWS=False)
    v = (visitor or SimpleVisitor)(g)
    return v.visit(result, root=True)

def parseHtml(text, tag_class=None, grammar=None, visitor=None):
    """Parse markdown text and return HTML"""
    g = (grammar or MarkdownGrammar)()
    result, rest = g.parse(text, resultSoFar=[], skipWS=False)
    v = (visitor or MarkdownHtmlVisitor)(tag_class or {}, g)
    return v.visit(result[0], root=True)

def parseEmbeddedHtml(text):
    """Parse markdown and strip outer <p> tags if only one paragraph"""
    parsed = parseHtml(text)
    clean = re.compile(r"</?p\b[^>]*>", re.I | re.MULTILINE)
    if len(_("<p>").findall(parsed)) == 1:
        parsed = re.sub(clean, "", parsed)
    return parsed

def parseHtmlDebug(text, tag_class=None, grammar=None, visitor=None):
    """Parse markdown text and return tuple of (HTML, resources_dict)
       * resources_dict contains all tracked resources including links, images, videos, etc.
    """
    g = (grammar or MarkdownGrammar)()
    result, rest = g.parse(text, resultSoFar=[], skipWS=False)
    v = (visitor or MarkdownHtmlVisitor)(tag_class or {}, g)
    html = v.visit(result[0], root=True)
    return (html, v.resources.to_dict())