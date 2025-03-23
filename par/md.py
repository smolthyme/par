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
        def space()            : return _(r'[ \t]+')
        def eol()              : return _(r'\r\n|\r|\n')
        def separator()        : return _(r'[\.,!?$ \t\^]')
        def blankline()        : return 0, space, eol

        def literal()          : return _(r'u?r?"[^"\\]*(?:\\.[^"\\]*)*"', re.I|re.DOTALL)
        def literal1()         : return _(r"u?r?'[^'\\]*(?:\\.[^'\\]*)*'", re.I|re.DOTALL)

        def htmlentity()       : return _(r'&\w+;')
        def longdash()         : return _(r"--\B")

        def escape_string()    : return _(r'\\'), _(r'.')
        def string()           : return _(r'[^\\\*_\^~ \t\r\n`,<\[]+', re.U)
        def code_string_short(): return _(r'`'), _(r'[^`]*'), _(r'`')
        def code_string()      : return _(r'``'), _(r'.+(?=``)'), _(r'``')
        def default_string()   : return _(r'\S+')

        ## paragraph
        #def simple_op()       : return _(r'[ \t]+(\*\*|__|\*|_|~~|\^|,,)(?=\r|\n|[ \t]+)')
        def op_string()        : return _(r'\*{1,3}|_{1,3}|~~|\^|,,')
        def op()               : return [(-1, longdash, separator, op_string), (op_string, -1, separator)]

        ## html block
        def html_block()       : return _(r'<(table|pre|div|p|ul|h1|h2|h3|h4|h5|h6|blockquote|code).*?>.*?<(/\1)>', re.I|re.DOTALL), -2, blankline
        def html_inline_block(): return _(r'<(span|del|font|a|b|code|i|em|strong|sub|sup).*?>.*?<(/\1)>|<(img|br).*?/>', re.I|re.DOTALL)

        def star_rating()      : return _(r"[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+ */ *\d+")

        def word()             : return [ # Tries to show parse-order
                escape_string, 
                code_string, code_string_short,
                html_inline_block, inline_tag,
                footnote, link, 
                htmlentity, longdash, star_rating,
                string, default_string
            ]
        
        def words()            : return [op, word], -1, [op, space, word]
        #def words()           : return -1, [word, space]
        def line()             : return 0, space, words, eol
        def common_text()      : return _(r'(?:[^\-\+#\r\n\*>\d]|(?:\*|\+|-)\S+|>\S+|\d+\.\S+)[^\r\n]*')
        def common_line()      : return common_text, eol


        def blanklines()       : return -2, blankline
        def paragraph()        : return line, -1, (0, space, common_line), -1, blanklines
        

        def directive_name()   : return _(r'\w+')
        def directive_title()  : return _(r'[^\n\r]+')
        def directive()        : return _(r'\.\.'), 0, space, directive_name, 0, space, _(r'::'), 0, directive_title
    
        ## footnote
        def footnote()         : return _(r'\[\^\w+\]')
        def footnote_text()    : return list_first_para, -1, [list_indent_lines, list_lines]
        def footnote_desc()    : return footnote, _(r':'), footnote_text
    
        ## custom inline tag
        def inline_tag_name()  : return _(r'[^\}:]*')
        def inline_tag_index() : return _(r'[^\]]*')
        def inline_tag_class() : return _(r'[^\}:]*')
        def inline_tag()       : return _(r'\{'), inline_tag_name, 0, (_(r':'), inline_tag_class), _(r'\}'), 0, space, _(r'\['), inline_tag_index, _(r'\]')
    
        ## hr  # Note: is something like (?:([-_\*])[ \t]*\1){3,} slower?
        def hr1()              : return _(r'\*[ \t]*\*[ \t]*\*[ \t]*[\* \t]*'), -2, blankline
        def hr2()              : return _(r'\-[ \t]*\-[ \t]*\-[ \t]*[\- \t]*'), -2, blankline
        def hr3()              : return _(r'\_[ \t]*\_[ \t]*\_[ \t]*[\_ \t]*'), -2, blankline
        def hr()               : return [hr1, hr2, hr3]

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
        
        ## subject
        def setext_title1()    : return title_text, 0, space, 0, attr_def, blankline, _(r'={1,}'), -2, blankline
        def setext_title2()    : return title_text, 0, space, 0, attr_def, blankline, _(r'-{1,}'), -2, blankline
        def title_text()       : return _(r'.+?(?= #| \{#| \{\.)|.+', re.U)
        def atx_title1()       : return _(r'# '),  title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def atx_title2()       : return _(r'## '), title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title1()           : return [atx_title1, setext_title1]
        def title2()           : return [atx_title2, setext_title2]
        def title3()           : return _(r'### '),    title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title4()           : return _(r'#### '),   title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title5()           : return _(r'##### '),  title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title6()           : return _(r'###### '), title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title()            : return [title6, title5, title4, title3, title2, title1]
    
        ## table
        def table_column()     : return _(r'.+?(?=\|\|)'), _(r'\|\|')
        def table_line()       : return _(r'\|\|'), -2, table_column, eol
        def table()            : return -2, table_line, -1, blankline
        def table_td()         : return _(r'[^\|\r\n]*\|')
        def table_horiz_line() : return _(r'\s*:?-+:?\s*\|')
        def table_other()      : return _(r'[^\r\n]+')
        def table_head()       : return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_separator()  : return 0, _(r'\|'), -2, table_horiz_line, -1, table_other, blankline
        def table_body_line()  : return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_body()       : return -2, table_body_line
        def table2()           : return table_head, table_separator, table_body
        
        ## definition lists
        def dl_dt_1()          : return _(r'[^ \t\r\n]+.*--'), -2, blankline
        def dl_dd_1()          : return -1, [list_indent_lines, blankline]
        def dl_dt_2()          : return _(r'[^ \t\r\n]+.*'), -1, blankline
        def dl_dd_2()          : return _(r':'), _(r' {1,3}'), list_rest_of_line, -1, [list_indent_lines, blankline]
        def dl_line_1()        : return dl_dt_1, dl_dd_1
        def dl_line_2()        : return dl_dt_2, -2, dl_dd_2
        def dl()               : return [dl_line_1, dl_line_2], -1, [blankline, dl_line_1, dl_line_2]
    
        def block_kwargs_key() : return _(r'[^=,\)\n]+')
        def block_kwargs_val() : return _(r'[^\),\n]+')
        def block_kwargs()     : return block_kwargs_key, 0, (_(r'='), block_kwargs_val)

        def new_block()        : return _(r'\{%\s*([a-zA-Z_\-][a-zA-Z_\-0-9]*)(.*?)%\}(.*?)\{%\s*end\1\s*%\}', re.DOTALL), eol

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
        def link_refer_title() : return [_(r'\([^\)]*\)'), literal, literal1]
        def link_refer_note()  : return 0, _(r' {1,3}'), link_inline_capt, _(
            r':'), space, link_refer_link, 0, (ws, link_refer_title), -2, blankline
        
        def link(): return [inline_image, image_refer, link_inline, link_refer, link_image_raw, link_raw, link_wiki, link_mailto], -1, space

        ## article
        def content(): return \
            -2, [   blanklines, hr, title, link_refer_note, directive,
                    pre, html_block,
                    side_block, new_block,
                    table, table2,
                    lists, dl,
                    blockquote, footnote_desc,
                    paragraph 
                ]

        def article(): return content

        # Finish up _get_rules() by returning the peg_rules and the 'root'
        peg_rules = {}
        for k, v in ((x, y) for (x, y) in list(locals().items()) if isinstance(y, types.FunctionType)):
            peg_rules[k] = v
        return peg_rules, article
    
    def parse(self, text="\n", root=None, skipWS=False, **kwargs):
        if text[-1] not in ('\r', '\n'):
            text = text + '\n'
        text = re.sub('\r\n|\r', '\n', text)
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)


class MarkdownHtmlVisitor(MDHTMLVisitor):
    op_maps = {
        '`'  :  ['<code>',        '</code>'],
        '*'  :  ['<em>',          '</em>'],
        '_'  :  ['<em>',          '</em>'],
        '**' :  ['<strong>',      '</strong>'],
        '***':  ['<strong><em>',  '</em></strong>'],
        '___':  ['<strong><em>',  '</em></strong>'],
        '__' :  ['<strong>',      '</strong>'],
        '^'  :  ['<sup>',         '</sup>'],
        ',,' :  ['<sub>',         '</sub>'],
        '~~' :  ['<span style="text-decoration: line-through">', '</span>'],
    }
    tag_class = {}

    def __init__(self, template=None, tag_class=None, grammar=None,
                    title='Untitled', block_callback=None, init_callback=None, footnote_id=None, filename=None):
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

    def process_line(self, line):
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

    def visit(self, nodes, root=False):
        if root:
            [self.visit_link_refer_note(obj) for obj in nodes[0].find_all('link_refer_note')]

            # Collect titles for use in ToC
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
        r = v.visit(result)
        self.footnote_id = v.footnote_id
        
        return r
    
    def visit_string(self, node):
        return self.to_html(node.text)

    def visit_blankline(self, node):
        return '\n'
    
    visit_blanklines = visit_blankline
    visit_quote_blank_line = visit_blankline

    def visit_longdash(self, node):
        return '—' # &mdash;

    def visit_hr(self, node):
        return self.tag('hr', enclose=1)

    def _alt_title(self, node):
        node = node.what[0]

        match node.__name__:
            case 'title1':  level = 1
            case 'title2':  level = 2
            case 'title3':  level = 3
            case 'title4':  level = 4
            case 'title5':  level = 5
            case _:         level = 1
        
        if node.find('attr_def_id'):
            _id = node.find('attr_def_id').text[1:]
        else:
            _id = self.get_title_id(level)
        
        title = node.find('title_text').text.strip()
        self.tocitems.append((level, _id, title))

    def _get_title(self, node, level):
        if node.find('attr_def_id'):
            _id = node.find('attr_def_id').text[1:]
        else:
            _id = self.get_title_id(level)
        
        anchor = '<a class="anchor" href="#{}"></a>'.format(_id)
        title = node.find('title_text').text.strip()
        _cls = [x.text[1:] for x in node.find_all('attr_def_class')]

        return self.tag(f'h{level}', title + anchor, id=_id, _class=' '.join(_cls))

    def visit_title1(self, node):
        return self._get_title(node, 1)

    def visit_setext_title1(self, node):
        return node[0]

    def visit_atx_title1(self, node):
        return node[1].text

    def visit_title2(self, node):
        return self._get_title(node, 2)

    def visit_setext_title2(self, node):
        return node[0]

    def visit_atx_title2(self, node):
        return node[1].text

    def visit_title3(self, node):
        return self._get_title(node, 3)

    def visit_title4(self, node):
        return self._get_title(node, 4)

    def visit_title5(self, node):
        return self._get_title(node, 5)

    def visit_title6(self, node):
        return self._get_title(node, 6)

    def visit_indent_block_line(self, node):
        return node[1].text

    def visit_indent_line(self, node):
        return node.find('indent_line_text').text + '\n'

    def visit_paragraph(self, node):
        txt = node.text.rstrip().replace('\n', ' ')
        return self.tag('p', self.process_line(self.parse_text(txt, 'words')))

    def visit_pre(self, node):
        cwargs = {}; kwargs = {}
        if (lang := node.find('pre_lang')):
            for n in lang.find_all('block_kwargs'):
                key = n.find('block_kwargs_key').text.strip()
                v_node = n.find('block_kwargs_val')
                val = v_node.text.strip() if v_node else None

                if key == 'lang':
                    cwargs['class'] = 'language-' + (val or key)
                else:
                    kwargs[key] = val or 'language-' + key
        code_content = self.to_html(self.visit(node).rstrip())
        
        return self.tag('pre', self.tag('code', code_content, newline=False, **cwargs), **kwargs)

    def visit_pre_extra1(self, node):
        return node.find('pre_text1').text.rstrip()

    def visit_pre_extra2(self, node):
        return node.find('pre_text2').text.rstrip()

    def visit_link_inline(self, node):
        kwargs = {'href': node[1][1]}
        if len(node[1]) > 3:
            kwargs['title'] = node[1][3].text[1:-1]
        caption = node[0].text[1:-1].strip() or kwargs['href']
        
        return self.tag('a', caption, newline=False, **kwargs)

    def visit_inline_image(self, node):
        kwargs = {}
        location = node.find('inline_href').text

        if (scheme := re.search(r'^(\w{3,5})://.+', location)):
            if scheme.group(1).lower() in ['javascript', 'vbscript', 'data']: #Just be safe
                return ""
            if ( yt_id := re.search(r"""youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed|v\/)([^\?&"'>]+)""", location)):
                return f"<object class='yt-embed' data='https://www.youtube.com/embed/{yt_id.group(1)}'></object>"

        src = "images/" + location  # later may need to split media so bbl
        kwargs['src'] = src
        if ( title := node.find('link_inline_title') ):
            kwargs['title'] = title.text[1:-1]
        if ( alt := node.find('inline_text') ):
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

    def visit_link_refer(self, node):
        caption = node.find('link_refer_capt')[1]
        key = node.find('link_refer_refer')
        key = key.text if key else caption
        
        return self.tag('a', caption, **self.link_refers.get(key.upper(), {}))

    def visit_image_refer(self, node):
        alt = node.find('image_refer_alt')
        alt_text = alt.find('inline_text').text if alt else ''

        key = node.find('image_refer_refer')
        key_text = key.text if key else alt_text

        d = self.link_refers.get(key_text.upper(), {})
        kwargs = {'src': d.get('href', ''), 'title': d.get('title', '')}

        return self.tag('img', enclose=1, **kwargs)

    def visit_link_refer_note(self, node):
        key = node.find('link_inline_capt').text[1:-1].upper()
        self.link_refers[key] = {'href': node.find('link_refer_link').text}

        if (r := node.find('link_refer_title')):
            self.link_refers[key]['title'] = r.text[1:-1]
        
        return ''

    def visit_link_raw(self, node):
        href = node.text.strip('<>')
        return self.tag('a', href, newline=False, href=href)

    def visit_link_wiki(self, node):
        """
        [[(type:)name(#anchor)(|alter name)]]
        type = 'wiki', or 'image'
        if type == 'wiki':
            [[(wiki:)name(#anchor)(|alter name)]]
        if type == 'image':
            [[(image:)filelink(|align|width|height)]]
            float = 'left', 'right'
            width or height = '' will not set
        """

        t = node.text[2:-2].strip()
        type = 'wiki'
        begin = 0
        if t[:6].lower() == 'image:':
            type = 'image'
            begin = 6
        elif t[:5].lower() == 'wiki:':
            type = 'wiki'
            begin = 5

        t = t[begin:]
        if type == 'wiki':
            #_prefix = self.wiki_prefix # FIXME: Should go back to using this
            _v,   caption = (t.split('|', 1) + [''])[:2]
            name, anchor = (_v.split('#', 1) + [''])[:2]
            if anchor:
                anchor = "#" + anchor

            if not caption:
                caption = name
            
            if not name:
                return self.tag('a', caption, href=anchor)

            # FIXME: file path should be verified since 'wiki' is local. //central store??
            return self.tag('a', caption, href=f"{name}.html{anchor}")

        elif type == 'image':
            _v = (t.split('|') + ['', '', ''])[:4]
            filename, align, width, height = _v
            cls = ''
            if width:
                if width.isdigit():
                    cls += f' width="{width}px"'
                else:
                    cls += f' width="{width}"'
            if height:
                if height.isdigit():
                    cls += f' height="{height}px"'
                else:
                    cls += f' height="{height}"'

            # TODO: Move to .tag
            s = f'<img src="images/{filename}" {cls}/>'
            if align:
                s = f'<div class="float{align}">{s}</div>'
            
            return s

    def visit_image_link(self, node):
        href = node.text.strip('<>')
        return self.tag('img', src=f"images/{href}", enclose=1)

    def visit_link_mailto(self, node):
        import random
        href = node.text[1:-1]
        if href.startswith('mailto:'):
            href = href[7:]

        shuffle = lambda text: ''.join(f'&#x{ord(x):X};' if random.choice('01') == '1' else x for x in text)

        return self.tag('a', shuffle(href), href=shuffle("mailto:" + href), newline=False)

    def visit_quote_line(self, node):
        return node.text[2:]

    def visit_blockquote(self, node):
        text = []
        for line in node.find_all('quote_lines'):
            text.append(self.visit(line))
        result = self.parse_text(''.join(text), 'article')
        
        attrib = node.find("quote_name")
        atrdat = node.find("quote_date")
        if attrib:
            result = result + f"&mdash; <i class='quote-attrib'>{attrib.text}</i>"
        if atrdat:
            result = result + f"<span class='quote-timeplace'>(<span class='text-date'>{atrdat.text}</span>)</span>"
        return self.tag('blockquote', result)

    def visit_lists_begin(self, node):
        self.lists = []
        return ''

    def visit_list_line(self, node):
        return node.text.strip()

    def visit_list_indent_line(self, node):
        return node.find('list_rest_of_line').text

    def visit_bullet_list_item(self, node):
        self.lists.append(('b', node.find('list_content')))
        return ''

    def visit_number_list_item(self, node):
        self.lists.append(('n', node.find('list_content')))
        return ''

    def visit_check_radio(self, node):
        tag = []
        if node.text[0] == '[':
            tag.append('<input type="checkbox"')
        else:
            tag.append('<input type="radio"')
        if node.text[1] == '*' or node.text[1].upper() == 'X':
            tag.append(' checked')
        tag.append('></input> ')

        return ''.join(tag)

    def visit_lists_end(self, node):
        def process_node(n):
            txt = []
            for node in n:
                txt.append(self.visit(node))
            text = ''.join(txt)
            t = self.parse_text(text, 'article').rstrip()
            if t.count('<p>') == 1 and t.startswith('<p>') and t.endswith('</p>'):
                ret = t[3:-4].rstrip()
            else:
                ret = t
            
            return ret

        def create_list(lists):
            buf = []
            old = None
            parent = None

            for _type, _node in lists:
                if _type == old:
                    buf.append(self.tag('li', process_node(_node)))
                else:
                    # find another list
                    if parent:
                        buf.append('</' + parent + '>\n')
                    if _type == 'b':
                        parent = 'ul'
                    else:
                        parent = 'ol'
                    buf.append(self.tag(parent))
                    buf.append(self.tag('li', process_node(_node)))
                    old = _type
            if buf and parent:
                buf.append('</' + parent + '>\n')
            
            return ''.join(buf)

        return create_list(self.lists)

    def visit_dl_begin(self, node):
        return self.tag('dl')

    def visit_dl_end(self, node):
        return '</dl>'

    def visit_dl_dt_1(self, node):
        txt = node.text.rstrip()[:-3]
        text = self.parse_text(txt, 'words')
        return self.tag('dt', self.process_line(text), enclose=1)

    def visit_dl_dd_1(self, node):
        txt = self.visit(node).rstrip()
        text = self.parse_text(txt, 'article')
        return self.tag('dd', text, enclose=1)

    def visit_dl_dt_2(self, node):
        txt = node.text.rstrip()
        text = self.parse_text(txt, 'words')
        return self.tag('dt', self.process_line(text), enclose=1)

    def visit_dl_dd_2(self, node):
        txt = self.visit(node).rstrip()
        text = self.parse_text(txt[1:].lstrip(), 'article')
        return self.tag('dd', text, enclose=1)

    def visit_inline_tag(self, node):
        rel = node.find('inline_tag_index').text.strip()
        name = node.find('inline_tag_name').text.strip()
        _c = node.find('inline_tag_class')
        rel = rel or name
        cls = ' ' + _c.text.strip() if _c is not None else ''

        return f'<span class="inline-tag{cls}" data-rel="{rel}">{name}</span>'

    def visit_new_block(self, node):
        block = { 'new': True }
        r = re.compile(r'\{%\s*([a-zA-Z_\-][a-zA-Z_\-0-9]*)\s*(.*?)%\}(.*?)\{%\s*end\1\s*%\}', re.DOTALL)
        m = r.match(node.text)
        if m and self.grammar:
            block_args = m.group(2).strip()
            resultSoFar = []
            result, rest = self.grammar.parse(block_args, root=self.grammar['new_block_args'], resultSoFar=resultSoFar, skipWS=False)
            kwargs = {}
            for node in result[0].find_all('block_kwargs'):
                k = node.find('block_kwargs_key').text.strip()
                v = node.find('block_kwargs_val')
                if v:
                    v = v.text.strip()
                kwargs[k] = v
            
            block = {'name': m.group(1), 'body': m.group(3).strip(), 'kwargs': kwargs}
            
        func = self.block_callback.get(block['name'])
        if func:
            return func(self, block)
        else:
            return '' # return node.text

    def visit_side_block_item(self, node):
        content = [self.parse_text(thing.text, 'content') 
                for thing in node.find('side_block_cont')]
        return self.tag('div', "\n".join(content), enclose=1, _class="collection-horiz") # node[kwargs]


    def visit_table_column(self, node):
        text = self.parse_text(node.text[:-2].strip(), 'words')
        return self.tag('td', self.process_line(text), newline=False)

    def visit_table2_begin(self, node):
        self.table_align = {}
        separator = node.find('table_separator')
        for i, x in enumerate(  list(separator.find_all('table_horiz_line')) +
                                list(separator.find_all('table_other'))):
            t = x.text
            if t.endswith('|'):
                t = t[:-1]
            t = t.strip()
            left = t.startswith(':')
            right = t.endswith(':')
            if left and right:
                align = 'center'
            elif left:
                align = 'left'
            elif right:
                align = 'right'
            else:
                align = ''
            self.table_align[i] = align

        return self.tag('table', newline=True)

    def visit_table2_end(self, node):
        return '</table>\n'

    def visit_table_head(self, node):
        s = ['<thead>\n<tr>']
        for t in ('table_td', 'table_other'):
            for x in node.find_all(t):
                text = x.text
                if text.endswith('|'):
                    text = text[:-1]
                s.append(f'<th>{self.process_line(text.strip())}</th>')
        s.append('</tr>\n</thead>\n')

        return ''.join(s)

    def visit_table_separator(self, node):
        return ''

    def visit_table_body(self, node):
        s = ['<tbody>\n']
        s.append(self.visit(node))
        s.append('</tbody>')

        return ''.join(s)

    def visit_table_body_line(self, node):
        nodes = list(node.find_all('table_td')) + list(node.find_all('table_other'))
        s = ['<tr>']
        for i, x in enumerate(nodes):
            text = x.text
            if text.endswith('|'):
                text = text[:-1]
            s.append(self.tag('td', self.parse_text(text.strip(), 'words'),
                                align=self.table_align.get(i, ''),
                                newline=False,
                                enclose=2))
        s.append('</tr>\n')

        return ''.join(s)
    
    def visit_directive(self, node):
        name = node.find('directive_name').text
        if name in ['toc', 'contents'] and self.tocitems:
            toc = []
            toc.append("<section class='toc'><ul>")
            hi = 0
            for lvl, anchor, title in self.tocitems:
                if lvl > hi:
                    toc.append("<ul>")
                elif lvl < hi:
                    toc.append("</ul>")
                hi = lvl
                toc.append(f"<li><a href='#{anchor}'>{title}</a></li>")
            toc.append("</ul></section>")
            # Since we visited these before generating, reset the dict to make sure headings get correct id's
            self.titles_ids = {}
            return ''.join(toc)

    def visit_footnote(self, node):
        name = node.text[2:-1]
        _id = self.footnote_id
        self.footnote_id += 1

        return f'<sup id="fnref-{name}"><a href="#fn-{name}" class="footnote-rel inner">{_id}</a></sup>'

    def visit_footnote_desc(self, node):
        name = node.find('footnote').text[2:-1]
        if name in self.footnodes:
            raise Exception(f"The footnote {name} is already exists")
        txt = self.visit(node.find('footnote_text')).rstrip()
        text = self.parse_text(txt, 'article')
        n = {'name': name, 'text': text}
        self.footnodes.append(n)

        return ''

    def visit_star_rating(self, node):
        r = _(r"(?P<stars>[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+) */ *(?P<outta>\d+)")
        if (m := r.match(node.text)):
            return f"<span>{'⭐' * len(str(m.group("stars")))}</span>"

    def __end__(self):
        s = []
        if len(self.footnodes) > 0:
            s.append('<div class="footnotes"><ol>')
            for n in self.footnodes:
                name = n['name']
                s.append(f'<li id="fn-{name}">')
                s.append(n['text'])
                s.append(self.tag('a', '↩', href=f'#fnref-{name}', _class='footnote-backref'))
                s.append('</li>')
            s.append('</ol></div>')
        
        return '\n'.join(s)

    def template(self, node):
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
    return v.template(result)


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
    parsed = v.template(result)

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