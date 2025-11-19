import re, types
from par.pyPEG import _not, _and, keyword, ignore, Symbol, parseLine
from .__init__ import SimpleVisitor, MDHTMLVisitor

class ResourceStore:
    def __init__(self, initial_data:dict|None=None):
        self.store = {'links_ext': [], 'links_int': [], 'toc_items': [], 'footnotes': [], 'images': [], 'videos': [], 'audios': []}
        if initial_data:
            self.store = {**self.store, **initial_data}

    def add(self, key, value):
        if key not in self.store:
            self.store[key] = []
        if isinstance(self.store[key], list):
            self.store[key].append(value)
        else:
            raise TypeError(f"Cannot add to key '{key}' as it is not a list.")
    
    def get(self, key):
        return self.store[key]
    
    def set(self, key, subkey, value):
        if isinstance(self.store[key], dict):
            self.store[key][subkey] = value
        else:
            raise TypeError(f"Cannot set subkey '{subkey}' for key '{key}' as it is not a dict.")

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

        def literal()          : return _(r'u?r?([\'"])(?:\\.|(?!\1).)*\1', re.I|re.DOTALL)
        def htmlentity()       : return _(r'&\w+;')
        def escape_string()    : return _(r'\\'), _(r'.')
        def string()           : return _(r'[^\\\*_\^~ \t\r\n`,<\[\]]+')

        def fmt_bold()         : return _(r'\*\*'), words , _(r'\*\*')
        def fmt_italic()       : return _(r'\*'),   words , _(r'\*')
        def fmt_bold2()        : return _(r'__'),   words , _(r'__')
        #def fmt_underline()    : return _(r'_'),    words , _(r'_')
        def fmt_italic2()      : return _(r'_'),    words , _(r'_')
        def fmt_code()         : return _(r'`'),    words , _(r'`')
        def fmt_subscript()    : return _(r',,'),   words , _(r',,')
        def fmt_superscript()  : return _(r'\^'),   words , _(r'\^')
        def fmt_strikethrough(): return _(r'~~'),   words , _(r'~~')

        ## inline
        def longdash()         : return _(r"--\B")
        def hr()               : return _(r'(?:([-_*])[ \t]*\1*){3,}'), blankline
        def star_rating()      : return _(r"[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+ */ *\d+")

        ## embedded html
        def html_block()       : return _(r'<(table|pre|div|p|ul|h1|h2|h3|h4|h5|h6|blockquote|code).*?>.*?<(/\1)>', re.I|re.DOTALL)
        def html_inline_block(): return _(r'<(span|del|font|a|b|code|i|em|strong|sub|sup|input).*?>.*?<(/\1)>|<(img|br|hr).*?/>', re.I|re.DOTALL)
        
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
    
        ## custom inline tag
        def inline_tag_name()  : return _(r'[^\}:]*')
        def inline_tag_index() : return _(r'[^\]]*')
        def inline_tag_class() : return _(r'[^\}:]*')
        def inline_tag()       : return _(r'\{'), inline_tag_name, 0, (_(r':'), inline_tag_class), _(r'\}'), 0, space, _(r'\['), inline_tag_index, _(r'\]')

        ## pre
        def indent_line_text() : return text
        def indent_line()      : return _(r' {4}|\t'), indent_line_text, blankline
        def indent_block()     : return -2, indent_line, -1, [indent_line, blankline]
        def pre_lang()         : return 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs))
        def pre_text1()        : return _(r'.+?(?=```|~~~)', re.M|re.DOTALL)
        def pre_text2()        : return _(r'.+?(?=</code>)', re.M|re.DOTALL)
        def pre_extra1()       : return _(r'```|~{3,}'), 0, pre_lang, blankline, pre_text1, _(r'```|~{3,}'), -2, blankline
        def pre_extra2()       : return _(r'<code>'), 0, pre_lang, blankline, pre_text2, _(r'</code>'), -2, blankline
        def pre()              : return [indent_block, pre_extra1, pre_extra2]
    
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
        def table_other()      : return _(r'[^\r\n]+')
        def table_head()       : return 0, table_sep, -2, table_td, -1, table_other, blankline
        def table_separator()  : return 0, table_sep, -2, table_horiz_line, -1, table_other, blankline
        def table_body_line()  : return 0, table_sep, -2, table_td, -1, table_other, blankline
        def table_body()       : return -2, table_body_line
        def table()            : return table_head, table_separator, table_body

        # Horizontal items
        def side_block_head()  : return _(r'\|\|\|'), blankline
        def side_block_cont()  : return [text, lists, paragraph], blankline
        def side_block_item()  : return side_block_head, -2, side_block_cont
        def side_block()       : return -2, side_block_item, -1, blankline

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
        def dl_dt()            : return _(r"^(?!=\s*[\*\d])"), -2, words(ig=r'--'), 0, _(r'--'), blankline
        def dl_dd_content()    : return 0, ignore(r"[ \t]+"), [lists, pre, paragraph]
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
        
        # Link components
        def link_text()        : return _(r'[^\]]+')
        def link_url()         : return _(r'[^\s\)]+')
        def link_title()       : return _(r'["\']([^"\']*)["\']|(\([^\)]*\))')
        def link_label()       : return _(r'[^\]]+')
        
        # Inline links
        def inline_link()      : return _(r'\['), link_text, _(r'\]'), _(r'\('), 0, space, link_url, 0, (space, link_title), 0, space, _(r'\)')
        
        # Reference links
        def reference_link()   : return _(r'\['), link_text, _(r'\]'), 0, space, _(r'\['), 0, link_label, _(r'\]')
        
        # Reference link definitions
        def link_ref_label()   : return _(r'[^\]]+')
        def link_ref_url()     : return _(r'[^\s]+')
        def link_ref_title()   : return _(r'["\']([^"\']*)["\']|(\([^\)]*\))')
        def link_reference()   : return _(r'^\s*\['), link_ref_label, _(r'\]:'), space, link_ref_url, 0, (space, link_ref_title), 0, space, blankline
        
        # Images - inline
        def image_alt()        : return _(r'[^\]]*')
        def image_url()        : return _(r'[^\s\)]+')
        def image_title()      : return _(r'["\']([^"\']*)["\']|(\([^\)]*\))')
        def inline_image()     : return _(r'!\['), image_alt, _(r'\]'), _(r'\('), 0, space, image_url, 0, (space, image_title), 0, space, _(r'\)')
        
        # Images - reference
        def image_ref_label()  : return _(r'[^\]]*')
        def reference_image()  : return _(r'!\['), image_alt, _(r'\]'), 0, space, _(r'\['), 0, image_ref_label, _(r'\]')
        
        # Wiki-style links
        def wiki_link_page()   : return _(r'[^\]#\|]+')
        def wiki_link_anchor() : return _(r'#[^\]#\|]*')
        def wiki_link_text()   : return _(r'[^\]]+')
        def wiki_link()        : return _(r'\[\['), 0, wiki_link_page, 0, wiki_link_anchor, 0, (_(r'\|'), wiki_link_text), _(r'\]\]')
        
        # Wiki-style images
        def wiki_image_file()  : return _(r'[^\|\]]+')
        def wiki_image_align() : return _(r'left|center|right', re.I)
        def wiki_image_width() : return _(r'\d+%?|\d+px|[\d\.]+(?:em|rem|vw)')
        def wiki_image_height(): return _(r'\d+%?|\d+px|[\d\.]+(?:em|rem|vh)')
        def wiki_image()       : return _(r'\[\[image:'), wiki_image_file, 0, (_(r'\|'), 0, wiki_image_align), 0, (_(r'\|'), 0, wiki_image_width), 0, (_(r'\|'), 0, wiki_image_height), _(r'\]\]')

        def word()             : return [
                escape_string,
                html_block, html_inline_block, inline_tag,
                # Links and images (before formatting)
                inline_image, reference_image, wiki_image,
                inline_link, reference_link, wiki_link,
                raw_url, email_address,
                # Formatting
                fmt_bold, fmt_bold2, fmt_italic, fmt_italic2, fmt_code,
                fmt_subscript, fmt_superscript, fmt_strikethrough,
                footnote, longdash,
                htmlentity, star_rating, string, wordlike
            ]

        ## article
        def content(): return -2, [blankline,
                link_reference,
                hr, directive,
                pre, html_block, lists,
                side_block, table, dl, blockquote, footnote_desc,
                title, paragraph ]

        def article(): return content

        # Finish up _get_rules() by returning the peg_rules and the 'root'
        peg_rules = {}
        for k, v in ((x, y) for (x, y) in list(locals().items()) if isinstance(y, types.FunctionType)):
            peg_rules[k] = v
        return peg_rules, article
    
    def parse(self, text:str, root=None, skipWS=False, **kwargs):
        # Normalise on unix-style line ending and we end with a newline
        text = re.sub(r'\r\n|\r', '\n', text + ("\n" if not text.endswith("\n") else ''))
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)


class MarkdownHtmlVisitor(MDHTMLVisitor):
    tag_class = {}

    def __init__(self, template=None, tag_class=None, grammar=None, title='Untitled', footnote_id=None, filename=None, resources=None):
        super().__init__(grammar, filename)
        
        self.title       = title
        self.tag_class   = tag_class or self.__class__.tag_class
        self.footnote_id = footnote_id or 1
        self.resources   = ResourceStore(resources)
        self._current_section_level = None
        self.link_references = {}  # Store reference link definitions
        self.image_references = {}  # Store reference image definitions

    def visit(self, nodes: Symbol, root=False) -> str:
        if root:
            # Collect link and image references first
            [self._collect_link_reference(obj) for obj in nodes[0].find_all('link_reference')]
            # Collect titles for ToC
            [self._alt_title(onk) for onk in nodes[0].find_all('title')]
        
        return super(MarkdownHtmlVisitor, self).visit(nodes, root)

    def parse_markdown(self, text, peg=None):
        g = self.grammar or MarkdownGrammar()
        if isinstance(peg, str):
            peg = g[peg]
        resultSoFar = []
        result, rest = g.parse(text, root=peg, resultSoFar=resultSoFar, skipWS=False)
        v = self.__class__('', self.tag_class, g, filename=self.filename, footnote_id=self.footnote_id)
        v.resources = self.resources
        parsed_output = v.visit(result[0])
        self.footnote_id = v.footnote_id
        
        return parsed_output
    
    def visit_string(self, node: Symbol) -> str:
        return self.to_html_charcodes(node.text)

    def visit_blankline(self, node: Symbol) -> str:
        return '\n'

    def visit_longdash(self, node: Symbol) -> str:
        return '—'

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
        return node.text.strip()

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
            return t[3:-4].rstrip() if t.count('<p>') == 1 and t.startswith('<p>') and t.endswith('</p>') else t

        def create_list(lists):
            buf = []; old = None; parent = None

            for _type, _node in lists:
                if _type == old:
                    buf.append(self.tag('li', process_node(_node)))
                else:
                    if parent:
                        buf.append(self.tag(parent, enclose=3))
                    parent = 'ul' if _type == 'b' else 'ol'
                    buf.append(self.tag(parent))
                    buf.append(self.tag('li', process_node(_node)))
                    old = _type
            if len(buf) > 0 and parent:
                buf.append(self.tag(parent, enclose=3))
            
            return ''.join(buf)
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
        a = node.find('words')
        return self.visit(a) if a else node.text.strip("*_")

    def visit_fmt_bold_end(self, node: Symbol) -> str:
        return self.tag('strong', enclose=3, newline=False)
    
    visit_fmt_bold2_begin = visit_fmt_bold_begin
    visit_fmt_bold2 = visit_fmt_bold
    visit_fmt_bold2_end = visit_fmt_bold_end

    def visit_fmt_italic_begin(self, node: Symbol) -> str:
        return self.tag('em', newline=False)

    def visit_fmt_italic(self, node: Symbol) -> str:
        a = node.find('words')
        return self.visit(a) if a else node.text.strip("*_")
    
    def visit_fmt_italic_end(self, node: Symbol) -> str:
        return self.tag('em', enclose=3, newline=False)
    
    visit_fmt_italic2_begin = visit_fmt_italic_begin
    visit_fmt_italic2 = visit_fmt_italic
    visit_fmt_italic2_end = visit_fmt_italic_end

    def visit_fmt_underline_begin(self, node: Symbol) -> str:
        return self.tag('u', newline=False)
    
    def visit_fmt_underline(self, node: Symbol) -> str:
        a = node.find('words')
        return self.visit(a) if a else node.text.strip("_")
    
    def visit_fmt_underline_end(self, node: Symbol) -> str:
        return self.tag('u', enclose=3, newline=False)

    def visit_fmt_code_begin(self, node: Symbol) -> str:
        return self.tag('code', newline=False)
    
    def visit_fmt_code(self, node: Symbol) -> str:
        a = node.find('words')
        return self.visit(a) if a else node.text.strip("`")

    def visit_fmt_code_end(self, node: Symbol) -> str:
        return self.tag('code', enclose=3, newline=False)

    def visit_fmt_subscript_begin(self, node: Symbol) -> str:
        return self.tag('sub', newline=False)
    
    def visit_fmt_subscript(self, node: Symbol) -> str:
        return node.text.strip(",")

    def visit_fmt_subscript_end(self, node: Symbol) -> str:
        return self.tag('sub', enclose=3, newline=False)

    def visit_fmt_superscript_begin(self, node: Symbol) -> str:
        return self.tag('sup', newline=False)
    
    def visit_fmt_superscript(self, node: Symbol) -> str:
        return node.text.strip("^")

    def visit_fmt_superscript_end(self, node: Symbol) -> str:
        return self.tag('sup', enclose=3, newline=False)

    def visit_fmt_strikethrough_begin(self, node: Symbol) -> str:
        return self.tag('span', style="text-decoration: line-through", newline=False)

    def visit_fmt_strikethrough(self, node: Symbol) -> str:
        return node.text.strip("~")

    def visit_fmt_strikethrough_end(self, node: Symbol) -> str:
        return self.tag('span', enclose=3, newline=False)

    # def visit_indent_line(self, node: Symbol):
    #     return (text_node := node.find('indent_line_text')) and text_node.text + '\n'

    def visit_pre(self, node: Symbol) -> str:
        cwargs = {}; kwargs = {}
        if (lang := node.find('pre_lang')):
            for n in lang.find_all('block_kwargs'):
                if (k := n.find('block_kwargs_key')):
                    key = k.text.strip()
                    val = v_node.text.strip() if (v_node := n.find('block_kwargs_val')) else None

                    if key == 'lang' or val is None:
                        cwargs['class'] = 'language-' + (val or key)
                    else:
                        kwargs[key] = val or 'language-' + key
        
        if pre_text := node.find('pre_text1') or node.find('pre_text2'):
            code_content = self.to_html_charcodes(pre_text.text.strip("` \t\n"))
            return self.tag('pre', self.tag('code', code_content, newline=False, **cwargs), **kwargs)
        else:
            return self.tag('pre', self.tag('code', node.text.strip("` \t\n"), newline=False, **cwargs), **kwargs)


    def visit_quote_line(self, node: Symbol) -> str:
        return node.text[2:]

    def visit_blockquote(self, node: Symbol) -> str:
        text = []
        for line in node.find_all('quote_lines'):
            text.append(self.visit(line))
        result = self.parse_markdown(''.join(text), 'content')
        
        attrib = node.find("quote_name")
        atrdat = node.find("quote_date")
        if attrib:
            result = f"{result} &mdash; {self.tag('i', attrib.text, _class='quote-attrib')}"
        if atrdat:
            result = result + self.tag('span', self.tag("span", atrdat.text, _class='text-date'), _class='quote-timeplace')
        return self.tag('blockquote', result.strip())

    def visit_table_sep(self, node: Symbol) -> str:
        return ''

    def get_title_id(self, level:int, begin=1) -> str:
        self.titles_ids[level] = self.titles_ids.get(level, 0) + 1
        _ids = [self.titles_ids.get(x, 0) for x in range(begin, level + 1)]
        return f"title_{'-'.join(map(str, _ids))}"

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
        
        _id_node = node.find('attr_def_id')
        _id = self.get_title_id(level) if not _id_node else (_id_node.text[1:] if _id_node.text else '')
        title = (title_node := node.find('title_text')) and title_node.text.strip()
        self.resources.add('toc_items', (level, _id, title))

    def _get_title(self, node: Symbol, level: int):
        _id_node = node.find('attr_def_id')
        _id = self.get_title_id(level) if not _id_node else (_id_node.text[1:] if _id_node.text else '')
        title = (title_node := node.find('title_text')) and title_node.text.strip() or "!Bad title!"
        anchor = self.tag('a', enclose=2, newline=False, _class='anchor', href=f'#{_id}')
        _cls = [x.text[1:].strip() for x in node.find_all('attr_def_class')]
        #section_s = self._open_section(f"{title}".lower().replace(' ', '-'))
        section_s = self._open_section(self.slug(f"{title}"))

        # Combine section opening with title tag
        return section_s + self.tag(f'h{level}', f"{title}{anchor}", id=_id, _class=(' '.join(_cls)))

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
        r = _(r"(?P<stars>[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+) */ *(?P<outta>\d+)")
        if (m := r.match(node.text)):
            return self.tag('span', '⭐'*len(m.group('stars')), _class='star-rating', title=f"{len(m.group('stars'))} stars out of {m.group('outta')}")
        else:
            return self.tag('span', '⭐'*5, _class='star-rating')

    def visit_inline_tag(self, node: Symbol) -> str:
        if ( rel := node.find('inline_tag_index')):
            if (name := node.find('inline_tag_name')):
                _c = node.find('inline_tag_class')
                cls = ' ' + _c.text.strip() if _c is not None else ''
                return self.tag('span', name.text.strip(), _class=f"inline-tag{cls}", attrs=f'data-rel="{rel.text.strip()}"')
        return self.tag('span', node.text, _class='inline-tag')

    def visit_side_block(self, node: Symbol) -> str:
        content = [self.parse_markdown(thing.text, 'content').strip()
                for thing in node.find_all('side_block_cont')]
        return self.tag('div', f"\n{'\n'.join(content)}\n", enclose=1, _class="collection-horiz") # node[kwargs]

    def visit_table_begin(self, node: Symbol) -> str:
        self.table_align = {}
        if separator := node.find('table_separator'):
            for i, x in enumerate(list(separator.find_all('table_horiz_line')) + list(separator.find_all('table_other'))):
                t = x.text.strip("| \t")
                self.table_align[i] = 'center' if t.startswith(':') and t.endswith(':') else 'left' if t.startswith(':') else 'right' if t.endswith(':') else ''
        return self.tag('table')

    def visit_table_end(self, node: Symbol) -> str:
        return self.tag('table', enclose=3)

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
    
    def visit_directive(self, node: Symbol):
        if (name := node.find('directive_name')) and name.text in ['toc', 'contents'] and self.resources.get('toc_items'):
            toc = [self.tag('section', _class='toc')]
            count = 1; hi = 0
            for lvl, anchor, title in self.resources.get('toc_items'):
                if lvl > hi:
                    toc.append(self.tag('ul'))
                elif lvl < hi:
                    toc.append(self.tag('ul', enclose=3))
                hi = lvl
                toc.append(self.tag('li', self.tag('a', title, href=f"#toc_{count}", newline=False)))
                count += 1
            toc.append(self.tag('ul', enclose=3))
            toc.append(self.tag('section', enclose=3, newline=False))
            # Since we visited these before generating, reset the dict to make sure headings get correct id's
            self.titles_ids = {}
            return ''.join(toc)

    def visit_footnote(self, node: Symbol) -> str:
        name = node.text[2:-1]
        _id = self.footnote_id
        self.footnote_id += 1
        return self.tag('sup', self.tag('a', f"{_id}", href=f"#fn-{name}", _class='footnote-rel inner', newline=False), id=f"fnref-{name}")

    def visit_footnote_desc(self, node):
        name = node.find('footnote').text.strip('[^]')
        if name in [fn['name'] for fn in self.resources.get('footnotes')]:
            raise Exception("The footnote %s is already existed" % name)

        txt = self.visit(node.find('footnote_text')).rstrip()
        text = self.parse_markdown(txt, 'content').rstrip()
        self.resources.add('footnotes', {'name': name, 'text': text})
        return ''

    visit_blanklines = visit_blankline
    visit_quote_blank_line = visit_blankline


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

    def _collect_link_reference(self, node: Symbol):
        """Collect reference link definitions during initial pass"""
        label_node = node.find('link_ref_label')
        url_node = node.find('link_ref_url')
        title_node = node.find('link_ref_title')
        
        if label_node and url_node:
            label = label_node.text.strip().lower()
            url = url_node.text.strip()
            title = self._extract_title(title_node.text) if title_node else None
            
            # Store both as link reference and image reference
            self.link_references[label] = {'url': url, 'title': title}
            self.image_references[label] = {'url': url, 'title': title}

    def _extract_title(self, text: str) -> str:
        """Extract title from quoted or parenthesized text"""
        if not text:
            return ""
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
        elif text.startswith('(') and text.endswith(')'):
            return text[1:-1]
        return text

    def _is_safe_url(self, url: str) -> bool:
        """Check if URL is safe (not javascript:, vbscript:, data:)"""
        if not url:
            return False
        url_lower = url.lower().strip()
        dangerous = ['javascript:', 'vbscript:', 'data:']
        return not any(url_lower.startswith(d) for d in dangerous)

    def _is_video_file(self, url: str) -> bool:
        """Check if URL points to a video file"""
        video_exts = ['.mp4', '.m4v', '.mkv', '.webm']
        return any(url.lower().endswith(ext) for ext in video_exts)

    def _is_audio_file(self, url: str) -> bool:
        """Check if URL points to an audio file"""
        audio_exts = ['.mp3', '.m4a', '.aac', '.ogg', '.oga', '.opus']
        return any(url.lower().endswith(ext) for ext in audio_exts)

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'youtube.com/embed/',
            'youtube.com/v/'
        ]
        return any(pattern in url.lower() for pattern in youtube_patterns)

    def _extract_youtube_id(self, url: str) -> str | None:
        """Extract YouTube video ID from URL"""
        patterns = [
            _(r'youtube\.com/watch\?v=([^&]{11})'),
            _(r'youtu\.be/([^?]{11})'),
            _(r'youtube\.com/embed/([^?]{11})'),
            _(r'youtube\.com/v/([^?]{11})')
        ]
        for pattern in patterns:
            if match := pattern.search(url):
                return match.group(1)
        return None

    def _obfuscate_email(self, email: str) -> str:
        """Obfuscate email address for spam protection"""
        result = []
        for char in email:
            if char == '@':
                result.append('&#64;')
            elif char == '.':
                result.append('&#46;')
            else:
                # Random mix of decimal and hex encoding
                import random
                if random.choice([True, False]):
                    result.append(f'&#x{ord(char):x};')
                else:
                    result.append(f'&#{ord(char)};')
        return ''.join(result)

    def _prefix_local_image(self, url: str) -> str:
        """Prefix local images with images/ directory if not already prefixed"""
        if url.startswith(('http://', 'https://', 'ftp://', '/')):
            return url
        if not url.startswith('images/'):
            return f'images/{url}'
        return url

    # Link visitors
    def visit_raw_url(self, node: Symbol) -> str:
        url = node.text
        if self._is_safe_url(url):
            self.resources.add('links_ext', url)
            return self.tag('a', url, href=url, newline=False)
        return url

    def visit_email_address(self, node: Symbol) -> str:
        email = node.text
        obfuscated = self._obfuscate_email(email)
        return self.tag('a', obfuscated, href=f'mailto:{email}', newline=False)

    def visit_inline_link(self, node: Symbol) -> str:
        text_node = node.find('link_text')
        url_node = node.find('link_url')
        title_node = node.find('link_title')
        
        if not text_node or not url_node:
            return node.text
        
        text = text_node.text.strip()
        url = url_node.text.strip()
        title = self._extract_title(title_node.text) if title_node else None
        
        if not self._is_safe_url(url):
            return text
        
        self.resources.add('links_ext', url)
        return self.tag('a', text, href=url, title=title, newline=False)

    def visit_reference_link(self, node: Symbol) -> str:
        text_node = node.find('link_text')
        label_node = node.find('link_label')
        
        if not text_node:
            return node.text
        
        text = text_node.text.strip()
        # If no label, use text as label (implicit reference)
        label = label_node.text.strip().lower() if label_node and label_node.text.strip() else text.lower()
        
        ref = self.link_references.get(label)
        if not ref:
            return node.text
        
        url = ref['url']
        if not self._is_safe_url(url):
            return text
        
        self.resources.add('links_ext', url)
        return self.tag('a', text, href=url, title=ref.get('title'), newline=False)

    def visit_link_reference(self, node: Symbol) -> str:
        # Reference definitions don't produce output, they're collected in visit()
        return ''

    def visit_wiki_link(self, node: Symbol) -> str:
        page_node = node.find('wiki_link_page')
        anchor_node = node.find('wiki_link_anchor')
        text_node = node.find('wiki_link_text')
        
        page = page_node.text.strip() if page_node else ''
        anchor = anchor_node.text.strip() if anchor_node else ''
        text = text_node.text.strip() if text_node else page
        
        # Build URL: convert spaces to dashes, add .html
        if page:
            url = page.lower().replace(' ', '-') + '.html' + anchor
        else:
            url = anchor  # Anchor-only link
        
        self.resources.add('links_int', url)
        return self.tag('a', text or page, href=url, newline=False)

    # Image visitors
    def visit_inline_image(self, node: Symbol) -> str:
        alt_node = node.find('image_alt')
        url_node = node.find('image_url')
        title_node = node.find('image_title')
        
        if not url_node:
            return node.text
        
        alt = alt_node.text.strip() if alt_node else ''
        url = url_node.text.strip()
        title = self._extract_title(title_node.text) if title_node else None
        
        if not self._is_safe_url(url):
            return node.text
        
        # Check for special media types
        if self._is_youtube_url(url):
            if video_id := self._extract_youtube_id(url):
                self.resources.add('videos', url)
                embed_url = f'https://www.youtube.com/embed/{video_id}'
                return self.tag('object', '', attrs=f' class="yt-embed" data="{embed_url}"', enclose=2)
        elif self._is_video_file(url):
            self.resources.add('videos', url)
            prefixed_url = self._prefix_local_image(url)
            return self.tag('video', controls="yesplz", disablePictureInPicture="True", playsinline="True",
                src=prefixed_url, type=f'video/mp4', enclose=1)
        elif self._is_audio_file(url):
            self.resources.add('audios', url)
            prefixed_url = self._prefix_local_image(url)
            return self.tag('audio', controls="yesplz", src=prefixed_url, type=f'audio/mpeg', enclose=1)

        # Regular image
        prefixed_url = self._prefix_local_image(url)
        self.resources.add('images', prefixed_url)
        return self.tag('img', '', src=prefixed_url, alt=alt, title=title, enclose=1, newline=False)

    def visit_reference_image(self, node: Symbol) -> str:
        alt_node = node.find('image_alt')
        label_node = node.find('image_ref_label')
        
        alt = alt_node.text.strip() if alt_node else ''
        # If no label, use alt as label (implicit reference)
        label = label_node.text.strip().lower() if label_node and label_node.text.strip() else alt.lower()
        
        ref = self.image_references.get(label)
        if not ref:
            return node.text
        
        url = ref['url']
        title = ref.get('title')
        
        if not self._is_safe_url(url):
            return node.text
        
        # Check for special media types (same as inline_image)
        if self._is_youtube_url(url):
            video_id = self._extract_youtube_id(url)
            if video_id:
                self.resources.add('videos', url)
                embed_url = f'https://www.youtube.com/embed/{video_id}'
                return self.tag('iframe', '', width='560', height='315',
                              src=embed_url, frameborder='0',
                              allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture',
                              allowfullscreen='allowfullscreen', title=alt or 'YouTube video', enclose=2)
        
        if self._is_video_file(url):
            self.resources.add('videos', url)
            prefixed_url = self._prefix_local_image(url)
            return self.tag('video',
                          self.tag('source', '', src=prefixed_url, type=f'video/{url.split(".")[-1]}', enclose=2),
                          controls='controls', title=title, enclose=2)
        
        if self._is_audio_file(url):
            self.resources.add('audios', url)
            prefixed_url = self._prefix_local_image(url)
            return self.tag('audio',
                          self.tag('source', '', src=prefixed_url, type=f'audio/{url.split(".")[-1]}', enclose=2),
                          controls='controls', title=title, enclose=2)
        
        # Regular image
        prefixed_url = self._prefix_local_image(url)
        self.resources.add('images', prefixed_url)
        return self.tag('img', '', src=prefixed_url, alt=alt, title=title, enclose=2, newline=False)

    def visit_wiki_image(self, node: Symbol) -> str:
        file_node = node.find('wiki_image_file')
        align_node = node.find('wiki_image_align')
        width_node = node.find('wiki_image_width')
        height_node = node.find('wiki_image_height')
        
        if not file_node:
            return node.text
        
        url = file_node.text.strip()
        align = align_node.text.strip().lower() if align_node else None
        width = width_node.text.strip() if width_node else None
        height = height_node.text.strip() if height_node else None
        
        if not self._is_safe_url(url):
            return node.text
        
        # Build style attributes
        styles = []
        if align:
            if align == 'left':
                styles.append('float: left; margin-right: 1em;')
            elif align == 'right':
                styles.append('float: right; margin-left: 1em;')
            elif align == 'center':
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
        
        prefixed_url = self._prefix_local_image(url)
        self.resources.add('images', prefixed_url)
        return self.tag('img', '', src=prefixed_url, alt='', style=style, enclose=2, newline=False)

    def __end__(self):
        s = []; 
        if hasattr(self, '_current_section_level'):
            s.append(self._close_section())
            self._current_section_level = None

        footnotes = self.resources.get('footnotes')
        if len(footnotes) > 0:
            s.append(self.tag('div', _class='footnotes', newline=False) + self.tag('ol', newline=False))
            for note in footnotes:
                s.append(self.tag('li', id=f"fn-{note['name']}", newline=False, enclose=0))
                s.append(note['text'] + "\n")
                s.append(self.tag('a', '↩', href=f'#fnref-{note['name']}', _class='footnote-backref inner', newline=False))
                s.append(self.tag('li', enclose=3, newline=False))
            s.append(self.tag('ol', enclose=3, newline=False) + self.tag('div', enclose=3, newline=False))
        return '\n'.join(s).strip()


    def template(self, node: Symbol):
        if self.grammar is None:
            raise ValueError("Grammar is not defined.")
        body = self.visit(node, self.grammar.root)
        if self._template:
            return self._template.format_map({'title':self.title, 'body':body})
        else:
            return body


def parseHtml(text, template=None, tag_class=None, filename=None, grammer=None, visitor=None):
    g = (grammer or MarkdownGrammar)()
    resultSoFar = []
    result, rest = g.parse(text, resultSoFar=resultSoFar, skipWS=False)
    v = (visitor or MarkdownHtmlVisitor)( # args below
            template or '{body}', tag_class or {}, g,
            filename=filename)
    out = v.template(result[0])
    return out

def parseEmbeddedHtml(text):
    parsed = parseHtml(text)
    clean = re.compile(r"</?p\b[^>]*>", re.I | re.MULTILINE)
    if len(_("<p>").findall(parsed)) == 1:
        parsed = re.sub(clean, "", parsed)
    return parsed

def parseText(text, filename=None, grammer=None, visitor=None):
    g = (grammer or MarkdownGrammar)()
    resultSoFar = []
    result, rest = g.parse(text, resultSoFar=resultSoFar, skipWS=False)
    v = (visitor or SimpleVisitor)(g, filename=filename)

    return v.visit(result, root=True)