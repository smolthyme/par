# This version has some differences between Standard Markdown
# Syntax according from http://daringfireball.net/projects/markdown/syntax

import re
import types
from par.pyPEG import _not, _and, keyword, ignore, Symbol, parseLine
from .__init__ import SimpleVisitor, MDHTMLVisitor

class ResourceStore:
    def __init__(self, initial_data:dict|None=None):
        self.store = {'link_refers': {}, 'tocitems': [], 'footnotes': [], 'images': []}
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
        def wordlike()         : return _(r'[^\*\_\s\d\.`]+') # Remove brackets maybe?
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

        def word()             : return [ # Tries to show parse-order
                escape_string,
                html_block, html_inline_block, inline_tag,
                fmt_bold, fmt_bold2, fmt_italic, fmt_italic2, fmt_code,# fmt_underline,
                fmt_subscript, fmt_superscript, fmt_strikethrough,
                footnote, link, longdash,
                htmlentity, star_rating, string, wordlike
            ]
        
        #def words()            : return word, -1, [space, word]
        def words(ig='(?!)')   : return word, -1, [space, ignore(ig), word]
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
        #def list_line()        : return _(r'[ \t]+([\*+\-]\S+|\d+\.[\S$]*|\d+[^\.]*|[^\-\+\r\n#>]).*')
        def list_lines()       : return list_norm_line, -1, [list_indent_lines, blankline]
        def list_indent_line() : return _(r' {4}|\t'), list_rest_of_line
        def list_norm_line()   : return _(r' {1,4}'), text, -1, (0, space, text), -1, blanklines
        def list_indent_lines(): return list_indent_line, -1, list_indent_line, -1, blanklines
        def list_content()     : return list_first_para, -1, [list_indent_lines, list_lines]
        def bullet_list_item() : return 0, _(r' {1,4}'), _(r'[\*\+\-]'), space, list_content
        def number_list_item() : return 0, _(r' {1,4}'), _(r'\d+\.'), space, list_content
        def lists()            : return -2, [bullet_list_item, number_list_item], -1, blankline

        ## Definition Lists
        def dl_dt()            : return _(r"^(?!=\s*[\*\d])"), -2, words(ig='--'), 0, _(r'--'), blankline
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

        def image_refer_alt()  : return _(r'!\['), inline_text, _(r'\]')
        def image_refer_refer(): return _(r'[^\]]*')
        def image_refer()      : return image_refer_alt, 0, space, _(r'\['), image_refer_refer, _(r'\]')

        def inline_text()      : return _(r'[^\]\^]*')
        def inline_href()      : return _(r'[^\s\)]+')
        def inline_image_alt() : return _(r'!\['), inline_text, _(r'\]')
        def inline_image_link(): return _(r'\('), inline_href, 0, space, 0, link_inline_title, 0, space, _(r'\)')
        def inline_image()     : return inline_image_alt, inline_image_link

        ## links
        def link_raw()         : return _(r'(<)?(?:http://|https://|ftp://)[\w\d\-\.,@\?\^=%&:/~+#]+(?(1)>)')
        def link_image_raw()   : return _(r'(<)?(?:http://|https://|ftp://).*?(?:\.png|\.jpg|\.gif|\.jpeg)(?(1)>)')
        def link_mailto()      : return _(r'[a-zA-Z_0-9-/\.]+@[a-zA-Z_0-9-/\.]+')
        def link_wiki()        : return _(r'\[\[[^\[\]]*\]\]')

        def link_inline_capt() : return _(r'\['), _(r'[^\]\^]*'), _(r'\]')
        def link_inline_title(): return literal
        def link_inline_link() : return _(r'\('), _(r'[^\s\)]+'), 0, space, 0, link_inline_title, 0, space, _(r'\)')
        def link_inline()      : return link_inline_capt, link_inline_link

        def link_refer_capt()  : return _(r'\['), _(r'[^\]\^]*'), _(r'\]')
        def link_refer_refer() : return _(r'[^\]]*')
        def link_refer()       : return link_refer_capt, 0, space, _(r'\['), link_refer_refer, _(r'\]')
        def link_refer_link()  : return 0, _(r'(<)?(\S+)(?(1)>)')
        def link_refer_title() : return [_(r'\([^\)]*\)'), literal]
        def link_refer_note()  : return 0, _(r' {1,3}'), link_inline_capt, _(
            r':'), space, link_refer_link, 0, space, link_refer_title, -2, blankline
        
        def link(): return [inline_image, image_refer, link_inline, link_refer, link_image_raw, link_raw, link_wiki, link_mailto]

        ## article
        def content(): return -2, [blankline,
                hr, link_refer_note, directive,
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

    def visit(self, nodes: Symbol, root=False) -> str:
        if root:# Collect titles for use in ToC, global things
            [self.visit_link_refer_note(obj) for obj in nodes[0].find_all('link_refer_note')]
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
            text = ''.join(self.visit(node) for node in n)
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

    def visit_link_inline(self, node: Symbol):
        # FIXME: What is opaque? oh, this code
        kwargs = {'href': node[1][1]}
        if len(node[1]) > 3:
            kwargs['title'] = node[1][3].text[1:-1]
        caption = node[0].text[1:-1].strip() or kwargs['href']
        
        return self.tag('a', caption, **kwargs, newline=False)

    def visit_inline_image(self, node: Symbol) -> str:
        kwargs = {}
        if (location := node.find('inline_href')):
            location = location.text

            if (scheme := re.search(r'^(\w{3,5})://.+', location)):
                if scheme.group(1).lower() in ['javascript', 'vbscript', 'data']: #Just be safe
                    return ""
                if ( yt_id := re.search(r"""youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed|v\/)([^\?&"'>]+)""", location)):
                    return self.tag('object', _class='yt-embed', data=f"https://www.youtube.com/embed/{yt_id.group(1)}", newline=False, enclose=2)

            src = f"images/{location}" if not location.strip().startswith('http') else location.strip('<>')
            kwargs['src'] = src
            if (title := node.find('link_inline_title')):
                kwargs['title'] = title.text[1:-1]
            if (alt := node.find('inline_text')):
                kwargs['alt'] = alt.text

            # controls disablePictureInPicture playsinline
            if src.endswith(".mp4") or src.endswith(".m4v") or src.endswith(".mkv") or src.endswith(".webm"):
                return self.tag('video', enclose=1, type="video/mp4", controls="yesplz", disablePictureInPicture=True,
                                playsinline="True", **kwargs)
            elif src.endswith(".m4a") or src.endswith(".aac") or src.endswith(".ogg") or src.endswith(".oga") or src.endswith(".opus"):
                return self.tag('audio', enclose=1, type="video/mp4", controls="yesplz", **kwargs)
            elif src.endswith(".mp3"):
                return self.tag('audio', enclose=1, type="video/mp3", controls="yesplz", **kwargs)

        self.resources.add('images', src)
        return self.tag('img', enclose=1, **kwargs, newline=False)

    def visit_link_refer(self, node: Symbol) -> str:
        caption = noder[1] if (noder := node.find('link_refer_capt')) else ''
        key = node.find('link_refer_refer')
        key = key.text if key else caption
        
        return self.tag('a', caption, **self.resources.get('link_refers').get(key.upper(), {}), newline=False)

    def visit_image_refer(self, node: Symbol) -> str:
        alt = node.find('image_refer_alt')
        alt_text = noder.text if alt and (noder := alt.find('inline_text')) else ''

        key = node.find('image_refer_refer')
        key_text = key.text if key else alt_text

        d = self.resources.get('link_refers').get(key_text.upper(), {})
        kwargs = {'src': d.get('href', ''), 'title': d.get('title', '')}

        self.resources.add('images', kwargs['src'])
        return self.tag('img', enclose=1, **kwargs, newline=False)

    def visit_link_refer_note(self, node: Symbol) -> str:
        key = noder.text.strip("][").upper() if (noder := node.find('link_inline_capt')) else ''
        self.resources.set('link_refers', key, {'href': noder.text if (noder := node.find('link_refer_link')) else ''})

        if (r := node.find('link_refer_title')):
            self.resources.get('link_refers')[key]['title'] = r.text.strip(r")(\"'")
        return ''

    def visit_link_raw(self, node: Symbol) -> str:
        href = node.text.strip('<>')
        return self.tag('a', href, href=href, newline=False)

    def visit_link_wiki(self, node: Symbol) -> str:
        """ # TODO: Needs a resource store to validate, path etc.
        [[(type:)name(#anchor)(|alter name)]] / [[(image:)filelink(|align|width|height)]]"""
        t = node.text.strip(r" \]\[")
        type, begin = ('image', 6) if t[:6].lower() == 'image:'\
                else (  'wiki', 5) if t[:5].lower() == 'wiki:' else ('wiki', 0)
        t = t[begin:]
        
        if type == 'wiki':
            _v,  caption = ( t.split('|', 1) + [''])[:2]
            name, anchor = (_v.split('#', 1) + [''])[:2]
            return self.tag('a', caption or name, href=f"{name}.html#{anchor}" if anchor else f"{name}.html", newline=False) \
                if name else self.tag('a', caption, href=f"#{anchor}", newline=False)
        
        filename, align, width, height = (t.split('|') + ['', '', ''])[:4]
        href = f"images/{filename}" if not filename.strip().startswith('http') else filename.strip()
        cls = []
        if width:
            cls.append( f'width="{width}px"'  if width.isdigit()  else f'width="{width}"')
        if height:
            cls.append(f'height="{height}px"' if height.isdigit() else f'height="{height}"')
        
        self.resources.add('images', href)
        img_tag = self.tag('img', '', src=href, attrs=' '.join(cls), enclose=1, newline=False)
        return    self.tag('div', img_tag, _class=f"float{align}", enclose=1, newline=False) if align else img_tag

    def visit_image_link(self, node: Symbol) -> str:
        # If the image is a link, just use that for href, else it's a local link
        href = f"images/{node.text.strip('<>')}" if not node.text.strip().startswith('http') else node.text.strip('<>')
        self.resources.add('images', href)
        return self.tag('img', src=href, enclose=1, newline=False)

    def visit_link_mailto(self, node: Symbol) -> str:
        import random
        shuffle = lambda text: ''.join(f'&#x{ord(x):X};' if random.choice('01') == '1' else x for x in text)
        
        href = node.text
        return self.tag('a', shuffle(href), href=shuffle("mailto:" + href), newline=False)

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
        return self.tag('blockquote', result)

    def visit_table_sep(self, node: Symbol) -> str:
        return ''

    def get_title_id(self, level:int, begin=1) -> str:
        self.titles_ids[level] = self.titles_ids.get(level, 0) + 1
        _ids = [self.titles_ids.get(x, 0) for x in range(begin, level + 1)]
        return f'title_{'-'.join(map(str, _ids))}'

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
        self.resources.add('tocitems', (level, _id, title))

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
        if (name := node.find('directive_name')) and name.text in ['toc', 'contents'] and self.resources.get('tocitems'):
            toc = [self.tag('section', _class='toc')]
            count = 1; hi = 0
            for lvl, anchor, title in self.resources.get('tocitems'):
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