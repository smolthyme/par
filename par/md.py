# This version has some differences between Standard Markdown
# Syntax according from http://daringfireball.net/projects/markdown/syntax

import types
from par.pyPEG import *
from .__init__ import SimpleVisitor, MDHTMLVisitor

_ = re.compile

class MarkdownGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
        
    def _get_rules(self):
        ## Cheats for return value repeats
        #  0 = ? = Optional ; -1 = * = Zero or more ; -2 = + = One or more ; n = n matches

        ## basic
        def ws()               : return _(r'\s+')
        def eol()              : return _(r'\r\n|\r|\n')
        def space()            : return _(r'[ \t]+')
        def wordlike()         : return _(r'\S+')
        def separator()        : return _(r'[\.,!?$ \t\^]')
        def blankline()        : return 0, space, eol
        def blanklines()       : return -2, blankline

        def literal()          : return _(r'u?r?([\'"])(?:\\.|(?!\1).)*\1', re.I|re.DOTALL)
        def htmlentity()       : return _(r'&\w+;')
        def escape_string()    : return _(r'\\'), _(r'.')
        def string()           : return _(r'[^\\\*_\^~ \t\r\n`,<\[]+', re.U)
        def code_string_short(): return _(r'`'), _(r'[^`]*'), _(r'`')
        def code_string()      : return _(r'``'), _(r'.+(?=``)'), _(r'``')

        ## inline
        def op_string()        : return _(r'\*{1,3}|_{1,3}|~~|,,|[`\^]')
        def op()               : return [(-1, longdash, separator, op_string), (op_string, -1, separator)]
        def longdash()         : return _(r"--\B")
        def hr()               : return _(r'(?:([-_*])[ \t]*\1?){3,}'), -2, blankline
        def star_rating()      : return _(r"[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+ */ *\d+")

        ## embedded html
        def html_block()       : return _(r'<(table|pre|div|p|ul|h1|h2|h3|h4|h5|h6|blockquote|code).*?>.*?<(/\1)>', re.I|re.DOTALL)
        def html_inline_block(): return _(r'<(span|del|font|a|b|code|i|em|strong|sub|sup|input).*?>.*?<(/\1)>|<(img|br|hr).*?/>', re.I|re.DOTALL)

        def word()             : return [ # Tries to show parse-order
                escape_string, 
                code_string, code_string_short,
                html_inline_block, inline_tag,
                footnote, link, 
                htmlentity, longdash, star_rating,
                string, wordlike
            ]
        
        def words()            : return [op, word], -1, [op, space, word]
        def line()             : return 0, space, words, eol
        def common_text()      : return _(r'(?:[^\-\+#\r\n\*>\d]|(?:\*|\+|-)\S+|>\S+|\d+\.\S+)[^\r\n]*')
        def common_line()      : return common_text, eol
        def paragraph()        : return line, -1, (0, space, common_line), -1, blanklines

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
        def indent_line_text() : return _(r'.+')
        def indent_line()      : return _(r'[ ]{4}|\t'), indent_line_text, eol
        def indent_block()     : return -2, [indent_line, blankline]
        def pre_lang()         : return 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs))
        def pre_text1()        : return _(r'.+?(?=```|~~~)', re.M|re.DOTALL)
        def pre_text2()        : return _(r'.+?(?=</code>)', re.M|re.DOTALL)
        def pre_extra1()       : return _(r'```|~{3,}'), 0, pre_lang, 0, space, eol, pre_text1, _(r'```|~{3,}'), -2, blankline
        def pre_extra2()       : return _(r'<code>'), 0, pre_lang, 0, space, eol, pre_text2, _(r'</code>'), -2, blankline
        def pre()              : return [indent_block, pre_extra1, pre_extra2]
    
        ## class and id definition
        def attr_def_id()      : return _(r'#[^\s\}]+')
        def attr_def_class()   : return _(r'\.[^\s\}]+')
        def attr_def_set()     : return [attr_def_id, attr_def_class], -1, (space, [attr_def_id, attr_def_class])
        def attr_def()         : return _(r'\{'), attr_def_set, _(r'\}')
        
        ## titles / subject
        def title_text()       : return _(r'[^\]\[\n#\{\}]+', re.U)
        def hashes()           : return _(r'#{1,6}')
        def atx_title()        : return hashes, 0, space, title_text, 0, space, 0, hashes, 0, space, 0, attr_def, -2, blankline
        def setext_underline() : return _(r'[ \t]*[-=]+[ \t]*')
        def setext_title()     : return title_text, 0, space, 0, attr_def, blankline, setext_underline, -2, blankline
        def title()            : return [atx_title, setext_title]
    
        ## table
        # def table_column()     : return _(r'[^\|\r\n]+')
        # def table_line()       : return _(r'\|\|'), -2, table_column, _(r'\|\|'), eol
        # def table()            : return -2, table_line, -1, blankline
        def table_td()         : return _(r'[^\|\r\n]*\|')
        def table_horiz_line() : return _(r'\s*:?-+:?\s*\|')
        def table_other()      : return _(r'[^\r\n]+')
        def table_head()       : return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_separator()  : return 0, _(r'\|'), -2, table_horiz_line, -1, table_other, blankline
        def table_body_line()  : return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_body()       : return -2, table_body_line
        def table()           : return table_head, table_separator, table_body
        
        ## definition lists
        def dl_dt_1()          : return _(r'[^ \t\r\n]+.*--'), -2, blankline
        def dl_dd_1()          : return -1, [list_indent_lines, blankline]
        def dl_dt_2()          : return _(r'[^ \t\r\n]+.*'), -1, blankline
        def dl_dd_2()          : return _(r':'), _(r' {1,3}'), list_rest_of_line, -1, [list_indent_lines, blankline]
        def dl_line_1()        : return dl_dt_1, dl_dd_1
        def dl_line_2()        : return dl_dt_2, -2, dl_dd_2
        def dl()               : return [dl_line_1, dl_line_2], -1, [blankline, dl_line_1, dl_line_2]

        # Horizontal items
        def side_block_head()  : return _(r'\|\|\|'), eol
        def side_block_cont()  : return -2, [common_line, space]
        def side_block_item()  : return side_block_head, -2, side_block_cont
        def side_block()       : return -2, side_block_item

        ## lists
        def check_radio()      : return _(r'\[[\*Xx ]?\]|<[\*Xx ]?>'), space
        def list_rest_of_line(): return _(r'.+'), eol
        def list_first_para()  : return 0, check_radio, list_rest_of_line, -1, (0, space, common_line), -1, blanklines
        def list_line()        : return _(r'[ \t]+([\*+\-]\S+|\d+\.[\S$]*|\d+[^\.]*|[^\-\+\r\n#>]).*')
        def list_lines()       : return list_norm_line, -1, [list_indent_lines, blankline]
        def list_indent_line() : return _(r' {4}|\t'), list_rest_of_line
        def list_norm_line()   : return _(r' {1,3}'), common_line, -1, (0, space, common_line), -1, blanklines
        def list_indent_lines(): return list_indent_line, -1, [list_indent_line, list_line], -1, blanklines
        def list_content()     : return list_first_para, -1, [list_indent_lines, list_lines]
        def bullet_list_item() : return 0, _(r' {1,3}'), _(r'\*|\+|-'), space, list_content
        def number_list_item() : return 0, _(r' {1,3}'), _(r'\d+\.'), space, list_content
        def list_item()        : return -2, [bullet_list_item, number_list_item]
        def lists()            : return -2, list_item, -1, blankline

        ## quote
        def quote_text()       : return _(r'[^\r\n]*'), eol
        def quote_blank_line() : return _(r'>[ \t]*'), eol
        def quote_line()       : return _(r'> (?!- )'), quote_text
        def quote_name()       : return _(r'[^\r\n\(\)\d]*')
        def quote_date()       : return _(r'[^\r\n\)]+')
        def quote_attr()       : return _(r'> --? '), quote_name, 0, (_(r"\("), quote_date, _(r"\)")), eol
        def quote_lines()      : return [quote_blank_line, quote_line]
        def blockquote()       : return -2, quote_lines, 0, quote_attr, -1, blankline

        ## links
        def link_raw()         : return _(r'(<)?(?:http://|https://|ftp://)[\w\d\-\.,@\?\^=%&:/~+#]+(?(1)>)')
        def link_image_raw()   : return _(r'(<)?(?:http://|https://|ftp://).*?(?:\.png|\.jpg|\.gif|\.jpeg)(?(1)>)', re.I)
        def link_mailto()      : return _(r'<(mailto:)?[a-zA-Z_0-9-/\.]+@[a-zA-Z_0-9-/\.]+>')
        def link_wiki()        : return _(r'(\[\[)(.*?)((1)?\]\])')

        def inline_text()      : return _(r'[^\]\^]*')
        def inline_href()      : return _(r'[^\s\)]+')
        def inline_image_alt() : return _(r'!\['), inline_text, _(r'\]')
        def inline_image_link(): return _(r'\('), inline_href, 0, space, 0, link_inline_title, 0, space, _(r'\)')
        def inline_image()     : return inline_image_alt, inline_image_link

        def image_refer_alt()  : return _(r'!\['), inline_text, _(r'\]')
        def image_refer_refer(): return _(r'[^\]]*')
        def image_refer()      : return image_refer_alt, 0, space, _(r'\['), image_refer_refer, _(r'\]')

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
            r':'), space, link_refer_link, 0, (ws, link_refer_title), -2, blankline
        
        def link(): return [inline_image, image_refer, link_inline, link_refer, link_image_raw, link_raw, link_wiki, link_mailto], -1, space

        ## article
        def content(): return -2, [blanklines, \
                hr, title, link_refer_note, directive,
                pre, html_block,
                side_block, table, lists, dl, blockquote, footnote_desc,
                paragraph ]

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
    op_maps = {
        '*'  :  ['<em>',          '</em>'],
        '**' :  ['<strong>',      '</strong>'],
        '***':  ['<strong><em>',  '</em></strong>'],
        '_'  :  ['<em>',          '</em>'],
        '__' :  ['<strong>',      '</strong>'],
        '___':  ['<strong><em>',  '</em></strong>'],
        '`'  :  ['<code>',        '</code>'],
        '^'  :  ['<sup>',         '</sup>'],
        ',,' :  ['<sub>',         '</sub>'],
        '~~' :  ['<span style="text-decoration: line-through">', '</span>'],
    }
    # Sort ops_maps by key length to parse correctly (long match first, not 3 * 1 '*')
    op_maps = {k: v for k, v in sorted(op_maps.items(), key=lambda item: len(item[0]), reverse=True)}
    tag_class = {}

    def __init__(self, template=None, tag_class=None, grammar=None, title='Untitled',
                    block_callback=None, init_callback=None, footnote_id=None, filename=None):
        super().__init__(grammar, filename)
        
        self.title       = title
        self.tag_class   = tag_class or self.__class__.tag_class
        self.chars       = sorted(self.op_maps.keys(), key      =lambda x: len(x), reverse=True)
        self.footnote_id = footnote_id or 1
        self.footnodes   = []
        self.tocitems    = []
        self.link_refers = {}
        self.block_callback = block_callback or {}
        self.init_callback  = init_callback

    def process_line(self, line: str) -> str:
        pos = []; buf = []
        codes = re.split(r"\s+", line)
        
        for left in codes:
            for c in self.chars:
                if left.startswith(c):
                    buf.append(c)
                    pos.append(len(buf) - 1)
                    left = left[len(c):]
                    break
            for c in self.chars:
                if left.endswith(c):
                    p = left[:-len(c)]
                    while pos:
                        t = pos.pop()
                        if buf[t] == c:
                            buf[t] = self.op_maps[c][0]
                            buf.extend([p, self.op_maps[c][1]])
                            left = ''
                            break
                    break
            if left:
                buf.append(left)
        return ' '.join(buf)

    def visit(self, nodes: Symbol, root=False) -> str:
        if root:# Collect titles for use in ToC, global things
            [self.visit_link_refer_note(obj) for obj in nodes[0].find_all('link_refer_note')]
            [self._alt_title(onk) for onk in nodes[0].find_all('title')]
        
        return super(MarkdownHtmlVisitor, self).visit(nodes, root)

    def parse_text(self, text, peg=None):
        g = self.grammar or MarkdownGrammar()
        if isinstance(peg, str):
            peg = g[peg]
        resultSoFar = []
        result, rest = g.parse(text, root=peg, resultSoFar=resultSoFar, skipWS=False)
        v = self.__class__('', self.tag_class, g, block_callback=self.block_callback,
                        init_callback=self.init_callback, filename=self.filename,
                        footnote_id=self.footnote_id)
        v.link_refers = self.link_refers
        r = v.visit(result[0])
        self.footnote_id = v.footnote_id
        
        return r
    
    def visit_string(self, node: Symbol) -> str:
        return self.to_html(node.text)

    def visit_blankline(self, node: Symbol) -> str:
        return '\n'

    def visit_longdash(self, node: Symbol) -> str:
        return '—' # &mdash;

    def visit_hr(self, node: Symbol) -> str:
        return self.tag('hr', enclose=1)
    
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
        self.tocitems.append((level, _id, title))

    def _get_title(self, node: Symbol, level: int):
        _id_node = node.find('attr_def_id')
        _id = self.get_title_id(level) if not _id_node else (_id_node.text[1:] if _id_node.text else '')
        title = (title_node := node.find('title_text')) and title_node.text.strip() or "!Bad title!"
        anchor = self.tag('a', enclose=2, newline=False, _class='anchor', href=f'#{_id}')
        _cls = [x.text[1:].strip() for x in node.find_all('attr_def_class')]

        return self.tag(f'h{level}', f"{title}{anchor}", id=_id, _class=(' '.join(_cls)))

    def visit_atx_title(self, node: Symbol) -> str:
        level = len(level.text) if (level := node.find('hashes')) and level.text else 1
        return self._get_title(node, level)

    def visit_setext_title(self, node: Symbol) -> str:
        marker = noder.text[0] if (noder := node.find('setext_underline')) else '='
        level = 1 if marker == '=' else 2
        return self._get_title(node, level)

    def visit_indent_block_line(self, node: Symbol) -> str:
        return node[1].text

    def visit_indent_line(self, node: Symbol):
        return (text_node := node.find('indent_line_text')) and text_node.text + '\n'

    def visit_paragraph(self, node: Symbol) -> str:
        txt = node.text.rstrip().replace('\n', ' ')
        return self.tag('p', self.process_line(self.parse_text(txt, 'paragraph')))

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
        code_content = self.to_html(self.visit(node).rstrip())
        
        return self.tag('pre', self.tag('code', code_content, newline=False, **cwargs), **kwargs)

    def visit_pre_extra1(self, node: Symbol):
        return (text_node := node.find('pre_text1')) and text_node.text.rstrip()

    def visit_pre_extra2(self, node: Symbol):
        return (text_node := node.find('pre_text2')) and text_node.text.rstrip()

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

            src = "images/" + location  # later may need to split media so bbl
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

        return self.tag('img', enclose=1, **kwargs)

    def visit_link_refer(self, node: Symbol) -> str:
        caption = noder[1] if (noder := node.find('link_refer_capt')) else ''
        key = node.find('link_refer_refer')
        key = key.text if key else caption
        
        return self.tag('a', caption, **self.link_refers.get(key.upper(), {}), newline=False)

    def visit_image_refer(self, node: Symbol) -> str:
        alt = node.find('image_refer_alt')
        alt_text = noder.text if alt and (noder := alt.find('inline_text')) else ''

        key = node.find('image_refer_refer')
        key_text = key.text if key else alt_text

        d = self.link_refers.get(key_text.upper(), {})
        kwargs = {'src': d.get('href', ''), 'title': d.get('title', '')}

        return self.tag('img', enclose=1, **kwargs)

    def visit_link_refer_note(self, node: Symbol) -> str:
        key = noder.text.strip("][").upper() if (noder := node.find('link_inline_capt')) else ''
        self.link_refers[key] = {'href': noder.text if (noder := node.find('link_refer_link')) else ''}

        if (r := node.find('link_refer_title')):
            self.link_refers[key]['title'] = r.text.strip(r")(\"'")
        
        return ''

    def visit_link_raw(self, node: Symbol) -> str:
        href = node.text.strip('<>')
        return self.tag('a', href, href=href)

    def visit_link_wiki(self, node: Symbol) -> str:
        """ # TODO: Needs a resource store to validate, path etc.
        [[(type:)name(#anchor)(|alter name)]] / [[(image:)filelink(|align|width|height)]]"""
        t = node.text.strip(r" \]\[")
        type, begin = ('image', 6) if t[:6].lower() == 'image:'\
                else (  'wiki', 5) if t[:5].lower() == 'wiki:' else ('wiki', 0)
        t = t[begin:]
        filename, align, width, height = (t.split('|') + ['', '', ''])[:4]
        
        if type == 'wiki':
            _v,  caption = ( t.split('|', 1) + [''])[:2]
            name, anchor = (_v.split('#', 1) + [''])[:2]
            return self.tag('a', caption or name, href=f"{name}.html#{anchor}" if anchor else f"{name}.html") \
                if name else self.tag('a', caption, href=anchor)
        
        cls = []
        if width:
            cls.append( f'width="{width}px"'  if width.isdigit()  else f'width="{width}"')
        if height:
            cls.append(f'height="{height}px"' if height.isdigit() else f'height="{height}"')
        
        img_tag = self.tag('img', '', attrs=' '.join(cls), src=f"images/{filename}", enclose=1)
        return    self.tag('div', img_tag, _class=f"float{align}", enclose=1) if align else img_tag

    def visit_image_link(self, node: Symbol) -> str:
        href = node.text.strip('<>')
        return self.tag('img', src=f"images/{href}", enclose=1)

    def visit_link_mailto(self, node: Symbol) -> str:
        import random
        href = node.text[1:-1]
        if href.startswith('mailto:'):
            href = href[7:]

        shuffle = lambda text: ''.join(f'&#x{ord(x):X};' if random.choice('01') == '1' else x for x in text)

        return self.tag('a', shuffle(href), href=shuffle("mailto:" + href), newline=False)

    def visit_quote_line(self, node: Symbol) -> str:
        return node.text[2:]

    def visit_blockquote(self, node: Symbol) -> str:
        text = []
        for line in node.find_all('quote_lines'):
            text.append(self.visit(line))
        result = self.parse_text(''.join(text), 'content')
        
        attrib = node.find("quote_name")
        atrdat = node.find("quote_date")
        if attrib:
            result = f"{result} &mdash; {self.tag('i', attrib.text, _class='quote-attrib')}"
        if atrdat:
            result = result + self.tag('span', self.tag("span", atrdat.text, _class='text-date'), _class='quote-timeplace')
        return self.tag('blockquote', result)

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
            t = self.parse_text(text, 'content').rstrip()
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
        return self.tag('dl')

    def visit_dl_end(self, node: Symbol) -> str:
        return self.tag('dl', enclose=3, newline=False)

    def visit_dl_dt_1(self, node: Symbol) -> str:
        txt = node.text.rstrip()[:-3]
        text = self.parse_text(txt, 'line')
        return self.tag('dt', self.process_line(text), enclose=1)

    def visit_dl_dd_1(self, node: Symbol) -> str:
        txt = self.visit(node).rstrip()
        text = self.parse_text(txt, 'content')
        return self.tag('dd', text, enclose=1)

    def visit_dl_dt_2(self, node: Symbol) -> str:
        txt = node.text.rstrip()
        text = self.parse_text(txt, 'line')
        return self.tag('dt', self.process_line(text), enclose=1)

    def visit_dl_dd_2(self, node: Symbol) -> str:
        txt = self.visit(node).rstrip()
        text = self.parse_text(txt[1:].lstrip(), 'content')
        return self.tag('dd', text, enclose=1)

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
                return self.tag('span', name.text.strip(), _class=f"inline-tag{cls}", data_rel=rel.text.strip())
        return self.tag('span', node.text, _class='inline-tag')

    def visit_side_block_item(self, node: Symbol) -> str:
        content = [self.parse_text(thing.text, 'content') 
                for thing in node.find_all('side_block_cont')]
        return self.tag('div', "\n".join(content), enclose=1, _class="collection-horiz") # node[kwargs]

    def visit_table_begin(self, node: Symbol) -> str:
        self.table_align = {}
        if separator := node.find('table_separator'):
            for i, x in enumerate(list(separator.find_all('table_horiz_line')) + list(separator.find_all('table_other'))):
                t = x.text.rstrip('|').strip()
                self.table_align[i] = 'center' if t.startswith(':') and t.endswith(':') else 'left' if t.startswith(':') else 'right' if t.endswith(':') else ''
        return self.tag('table')

    def visit_table_end(self, node: Symbol) -> str:
        return '</table>\n'

    def visit_table_head(self, node: Symbol) -> str:
        s = ['<thead>\n<tr>']
        for t in ('table_td', 'table_other'):
            for x in node.find_all(t):
                s.append(f'<th>{self.process_line(x.text.rstrip("|").strip())}</th>')
        s.append('</tr>\n</thead>\n')
        return ''.join(s)

    def visit_table_separator(self, node: Symbol) -> str:
        return ''

    def visit_table_body(self, node: Symbol) -> str:
        return f"<tbody>\n{self.visit(node)}</tbody>"

    def visit_table_body_line(self, node: Symbol) -> str:
        nodes = list(node.find_all('table_td')) + list(node.find_all('table_other'))
        s = [self.tag('tr', newline=False)]
        for i, x in enumerate(nodes):
            text = x.text.strip("| ")
            if text != "":
                s.append(self.tag('td', self.parse_text(text, 'line').strip(),
                    align=self.table_align.get(i, ''), newline=False, enclose=2))
            else:
                s.append(self.tag("td", "", newline=False, enclose=2))
        s.append(self.tag('tr', enclose=3))
        return ''.join(s)
    
    def visit_directive(self, node: Symbol):
        if (name := node.find('directive_name')) and name.text in ['toc', 'contents'] and self.tocitems:
            toc = [self.tag('section', _class='toc')]
            count = 1; hi = 0

            for lvl, anchor, title in self.tocitems:
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
        # self.footnodes.append({'name': name, 'text': node.text[2:-1]})
        #return f'<sup id="fnref-{name}"><a href="#fn-{name}" class="footnote-rel inner">{_id}</a></sup>'
        return self.tag('sup', self.tag('a', f"{_id}", href=f"#fn-{name}", _class='footnote-rel inner'), id=f"fnref-{name}")

    def visit_footnote_desc(self, node):
        name = node.find('footnote').text[2:-1]
        if name in self.footnodes:
            raise Exception("The footnote %s is already existed" % name)

        txt = self.visit(node.find('footnote_text')).rstrip()
        text = self.parse_text(txt, 'article')
        n = {'name': '%s' % name, 'text': text}
        self.footnodes.append(n)
        return ''

    visit_blanklines = visit_blankline
    visit_quote_blank_line = visit_blankline

    def __end__(self):
        if len(self.footnodes) > 0:
            s = []
            s.append(self.tag('div', _class='footnotes', newline=False))
            s.append(self.tag('ol', newline=False))
            for note in self.footnodes:
                name = note['name']
                s.append(self.tag('li', id=f"fn-{name}"))
                s.append(self.tag('p', note['text'], newline=False))
                s.append(self.tag('a', '↩', href=f'#fnref-{name}', _class='footnote-backref inner'))
                s.append(self.tag('li', enclose=3))
            s.append(self.tag('ol', enclose=3, newline=False))
            s.append(self.tag('div', enclose=3, newline=False))
            return '\n'.join(s)
        return ''

    def template(self, node: Symbol):
        if self.grammar is None:
            raise ValueError("Grammar is not defined.")
        body = self.visit(node, self.grammar.root)
        if self.init_callback:
            self.init_callback(self)
        if self._template:
            return self._template.format_map({'title':self.title, 'body':body})
        else:
            return body


def parseHtml(text, template=None, tag_class=None, block_callback=None,
                init_callback=None, filename=None, grammer=None, visitor=None):
    template = template or ''
    tag_class = tag_class or {}
    g = (grammer or MarkdownGrammar)()
    resultSoFar = []
    result, rest = g.parse(text, resultSoFar=resultSoFar, skipWS=False)
    v = (visitor or MarkdownHtmlVisitor)(template, tag_class, g,
                                            block_callback=block_callback,
                                            init_callback=init_callback,
                                            filename=filename)
    return v.template(result[0])


def parseEmbeddedHtml(text, template=None, tag_class=None, block_callback=None,
                init_callback=None, filename=None, grammer=None, visitor=None):
    tag_class = tag_class or {}
    g = (grammer or MarkdownGrammar)()
    resultSoFar = []
    result, rest = g.parse(text, resultSoFar=resultSoFar, skipWS=False)
    v = (visitor or MarkdownHtmlVisitor)(template, tag_class, g,
                                            block_callback=block_callback,
                                            init_callback=init_callback,
                                            filename=filename)
    parsed = v.template(result[0])

    reobj = re.compile("<p>")
    clean = re.compile(r"</?p\b[^>]*>", re.I | re.MULTILINE)
    if len(reobj.findall(parsed)) == 1:
        parsed = re.sub(clean, "", parsed)

    return parsed


def parseText(text, filename=None, grammer=None, visitor=None):
    g = (grammer or MarkdownGrammar)()
    resultSoFar = []
    result, rest = g.parse(text, resultSoFar=resultSoFar, skipWS=False)
    v = (visitor or SimpleVisitor)(g, filename=filename)

    return v.visit(result, root=True)