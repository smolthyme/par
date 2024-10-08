from urllib.parse import urljoin

# Parsing Markdown
# This version has some differences between Standard Markdown
# Syntax according from http://daringfireball.net/projects/markdown/syntax
# 
# They are:
#   || `^super^script` || <sup>super</sup>script ||
#   || `,,sub,,script` || <sub>sub</sub>script ||
#   || `~~strikeout~~` || <span style="text-decoration: line-through">strikeout</span> ||
#  
#   directly url and image support, e.g.:
#     http://code.google.com/images/code_sm.png
#     http://www.google.com
#   Table support
#   Difinition list support <dl><dt><dd>
#   github flavored Markdown support:
#     Multiple underscores in words
#     Fenced code blocks
#     Syntax highlighting



from par.pyPEG import *
import re
import types
from par.gwiki import WikiGrammar, WikiHtmlVisitor, SimpleVisitor

_ = re.compile

class MarkdownGrammar(WikiGrammar):
    def __init__(self):
        super(MarkdownGrammar, self).__init__()
        
    def _get_rules(self):
        ## Cheats for return value repeats
        #  0 ?
        # -1 *
        # -2 +

        ## basic
        def ws():       return _(r'\s+')
        def space():    return _(r'[ \t]+')
        def eol():      return _(r'\r\n|\r|\n')
        def seperator():return _(r'[\.,!?$ \t\^]')
    
        def blankline(): return 0, space, eol

        def literal():  return _(r'u?r?"[^"\\]*(?:\\.[^"\\]*)*"', re.I|re.DOTALL)
        def literal1(): return _(r"u?r?'[^'\\]*(?:\\.[^'\\]*)*'", re.I|re.DOTALL)

        def htmlentity(): return _(r'&\w+;')
        def longdash():   return _(r"--\B")

        def escape_string():    return _(r'\\'), _(r'.')
        def string():           return _(r'[^\\\*_\^~ \t\r\n`,<\[]+', re.U)
        def code_string_short():return _(r'`'), _(r'[^`]*'), _(r'`')
        def code_string():      return _(r'``'), _(r'.+(?=``)'), _(r'``')
        def default_string():   return _(r'\S+')

        ## paragraph
        #def simple_op(): return _(r'[ \t]+(\*\*|__|\*|_|~~|\^|,,)(?=\r|\n|[ \t]+)')
        def op_string(): return _(r'\*{1,3}|_{1,3}|~~|\^|,,')
        def op(): return [(-1, longdash, seperator, op_string), (op_string, -1, seperator)]
        # def underscore_words(): return _(r'[\w\d]+_[\w\d]+[\w\d_]*')
        # def identifer(): return _(r'[a-zA-Z_][a-zA-Z_0-9]*', re.U)

        def star_rating(): return _(r"[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+ */ *\d+")

        def word(): return [ # Tries to show parse-order
                escape_string, 
                code_string, code_string_short,
                html_inline_block, inline_tag,
                footnote, link, 
                htmlentity, longdash, star_rating,
                string, default_string
            ]
        
        def words(): return [op, word], -1, [op, space, word]
        #def words(): return -1, [word, space]
        def line(): return 0, space, words, eol
        def common_text(): return _(r'(?:[^\-\+#\r\n\*>\d]|(?:\*|\+|-)\S+|>\S+|\d+\.\S+)[^\r\n]*')
        def common_line(): return common_text, eol 

        def paragraph(): return line, -1, (0, space, common_line), -1, blanklines
        def blanklines(): return -2, blankline

        def directive_name(): return _(r'\w+')
        def directive_title(): return _(r'[^\n\r]+')
        def directive(): return _(r'\.\.'), 0, space, directive_name, 0, space, _(r'::'), 0, directive_title
    
        ## footnote
        def footnote(): return _(r'\[\^\w+\]')
        def footnote_text(): return list_first_para, -1, [list_content_indent_lines, list_content_lines]
        def footnote_desc(): return footnote, _(r':'), footnote_text
    
        ## custom inline tag
        def inline_tag_name():  return _(r'[^\}:]*')
        def inline_tag_index(): return _(r'[^\]]*')
        def inline_tag_class(): return _(r'[^\}:]*')
        def inline_tag(): return _(r'\{'), inline_tag_name, 0, (_(r':'), inline_tag_class), _(r'\}'), 0, space, _(r'\['), inline_tag_index, _(r'\]')
    
        ## hr
        # Note: is something like (?:([-_\*])[ \t]*\1){3,} slower?
        def hr1(): return _(r'\*[ \t]*\*[ \t]*\*[ \t]*[\* \t]*'), -2, blankline
        def hr2(): return _(r'\-[ \t]*\-[ \t]*\-[ \t]*[\- \t]*'), -2, blankline
        def hr3(): return _(r'\_[ \t]*\_[ \t]*\_[ \t]*[\_ \t]*'), -2, blankline
        def hr(): return [hr1, hr2, hr3]

        ## html block
        def html_block(): return _(r'<(table|pre|div|p|ul|h1|h2|h3|h4|h5|h6|blockquote|code).*?>.*?<(/\1)>', re.I|re.DOTALL), -2, blankline
        def html_inline_block(): return _(r'<(span|del|font|a|b|code|i|em|strong|sub|sup).*?>.*?<(/\1)>|<(img|br).*?/>', re.I|re.DOTALL)

        ## pre
        def indent_line_text(): return _(r'.+')
        def indent_line(): return _(r'[ ]{4}|\t'), indent_line_text, eol
        def indent_block(): return -2, [indent_line, blankline]
        def pre_lang(): return 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs))
        def pre_text1():    return _(r'.+?(?=```|~~~)', re.M|re.DOTALL)
        def pre_text2():    return _(r'.+?(?=</code>)', re.M|re.DOTALL)
        def pre_extra1():   return _(r'```|~{3,}'), 0, pre_lang, 0, space, eol, pre_text1, _(r'```|~{3,}'), -2, blankline
        def pre_extra2():   return _(r'<code>'), 0, pre_lang, 0, space, eol, pre_text2, _(r'</code>'), -2, blankline
        def pre(): return [indent_block, pre_extra1, pre_extra2]
    
        ## class and id definition
        def attr_def_id(): return _(r'#[^\s\}]+')
        def attr_def_class(): return _(r'\.[^\s\}]+')
        def attr_def_set(): return [attr_def_id, attr_def_class], -1, (space, [attr_def_id, attr_def_class])
        def attr_def(): return _(r'\{'), attr_def_set, _(r'\}')
        
        ## subject
        def setext_title1(): return title_text, 0, space, 0, attr_def, blankline, _(r'={1,}'), -2, blankline
        def setext_title2(): return title_text, 0, space, 0, attr_def, blankline, _(r'-{1,}'), -2, blankline
        def title_text(): return _(r'.+?(?= #| \{#| \{\.)|.+', re.U)
        def atx_title1(): return _(r'# '),  title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def atx_title2(): return _(r'## '), title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title1(): return [atx_title1, setext_title1]
        def title2(): return [atx_title2, setext_title2]
        def title3(): return _(r'### '),    title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title4(): return _(r'#### '),   title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title5(): return _(r'##### '),  title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title6(): return _(r'###### '), title_text, 0, _(r' #+'), 0, space, 0, attr_def, -2, blankline
        def title(): return [title6, title5, title4, title3, title2, title1]
    
        ## table
        # def table_column(): return -2, [space, escape_string, code_string_short, code_string, op, link, _(r'[^\\\*_\^~ \t\r\n`,\|]+', re.U)], _(r'\|\|')
        def table_column(): return _(r'.+?(?=\|\|)'), _(r'\|\|')
        def table_line():   return _(r'\|\|'), -2, table_column, eol
        def table(): return -2, table_line, -1, blankline
        def table_td(): return _(r'[^\|\r\n]*\|')
        def table_separator_line(): return _(r'\s*:?-+:?\s*\|')
        # def table_separator_char(): return _(r'\|')
        def table_other(): return _(r'[^\r\n]+')
        def table_head(): return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_separator(): return 0, _(r'\|'), -2, table_separator_line, -1, table_other, blankline
        def table_body_line(): return 0, _(r'\|'), -2, table_td, -1, table_other, blankline
        def table_body(): return -2, table_body_line
        def table2(): return table_head, table_separator, table_body
        
        ## definition lists
        def dl_dt_1(): return _(r'[^ \t\r\n]+.*--'), -2, blankline
        def dl_dd_1(): return -1, [list_content_indent_lines, blankline]
        def dl_dt_2(): return _(r'[^ \t\r\n]+.*'), -1, blankline
        def dl_dd_2(): return _(r':'), _(r' {1,3}'), list_rest_of_line, -1, [list_content_indent_lines, blankline]
        def dl_line_1(): return dl_dt_1, dl_dd_1
        def dl_line_2(): return dl_dt_2, -2, dl_dd_2
        def dl(): return [dl_line_1, dl_line_2], -1, [blankline, dl_line_1, dl_line_2]
    
        ## block
        #   [[tabs(filename=hello.html)]]:
        #       content
        #
        # def block_name(): return _(r'[a-zA-Z_\-][a-zA-Z_\-0-9]*')
        def block_kwargs_key():     return _(r'[^=,\)\n]+')
        def block_kwargs_value():   return _(r'[^\),\n]+')
        def block_kwargs(): return block_kwargs_key, 0, (_(r'='), block_kwargs_value)
        # def block_args(): return _(r'\('), 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs)), 0, space, _(r'\)')
        # def block_head(): return _(r'\[\['), 0, space, block_name, 0, space, 0, block_args, 0, space, _(r'\]\]:'), eol
        # def block_body(): return list_content_indent_lines
        # def block_item(): return block_head, block_body
        # def block(): return -2, block_item
    
        ## new block NB
        #  {% blockname para_name=para_value[, para_name, para_name=para_value] %}
        #  content
        #  {% endblockname %}
        #

        # def new_block_args(): return 0, space, 0, (block_kwargs, -1, (_(r','), block_kwargs)), 0, space
        # def new_block_name(): return _(r'([a-zA-Z_\-][a-zA-Z_\-0-9]*)')
        # def new_block_head(): return _(r'\{%'), 0, space, new_block_name, new_block_args, _(r'%\}'), eol
        # def new_block_end(): return _(r'\{%'), 0, space, _(r'end\1'), 0, space, _(r'%\}'), eol
        # def new_block_item(): return new_block_head, new_block_body, new_block_end
        # def new_block(): return -2, new_block_item
        def new_block(): return _(r'\{%\s*([a-zA-Z_\-][a-zA-Z_\-0-9]*)(.*?)%\}(.*?)\{%\s*end\1\s*%\}', re.DOTALL), eol


        def side_block_head(): return _(r'\|\|\|'), eol
        def side_block_content(): return -2, [common_line, space]
        def side_block_item():  return side_block_head, -2, side_block_content
        def side_block(): return -2, side_block_item

        ## lists
        def check_radio(): return _(r'\[[\*Xx ]?\]|<[\*Xx ]?>'), space
        def list_rest_of_line(): return _(r'.+'), eol
        def list_first_para(): return 0, check_radio, list_rest_of_line, -1, (0, space, common_line), -1, blanklines
        # def list_content_text(): return list_rest_of_line, -1, [list_content_norm_line, blankline]
        def list_content_line(): return _(r'[ \t]+([\*+\-]\S+|\d+\.[\S$]*|\d+[^\.]*|[^\-\+\r\n#>]).*')
        def list_content_lines(): return list_content_norm_line, -1, [list_content_indent_lines, blankline]
        def list_content_indent_line(): return _(r' {4}|\t'), list_rest_of_line
        def list_content_norm_line(): return _(r' {1,3}'), common_line, -1, (0, space, common_line), -1, blanklines
        def list_content_indent_lines(): return list_content_indent_line, -1, [list_content_indent_line, list_content_line], -1, blanklines
        def list_content(): return list_first_para, -1, [list_content_indent_lines, list_content_lines]
        def bullet_list_item(): return 0, _(r' {1,3}'), _(r'\*|\+|-'), space, list_content
        def number_list_item(): return 0, _(r' {1,3}'), _(r'\d+\.'), space, list_content
        def list_item(): return -2, [bullet_list_item, number_list_item]
        def lists(): return -2, list_item, -1, blankline

        ## quote
        def quote_text():       return _(r'[^\r\n]*'), eol
        def quote_blank_line(): return _(r'>[ \t]*'), eol
        def quote_line():       return _(r'> (?!- )'), quote_text
        def quote_name():       return _(r'[^\r\n\(\)\d]*')
        def quote_date():       return _(r'[^\r\n\)]+')
        def quote_attr():       return _(r'> --? '), quote_name, 0, (_(r"\("), quote_date, _(r"\)")), eol 
        def quote_lines(): return [quote_blank_line, quote_line]
        def blockquote(): return -2, quote_lines, 0, quote_attr, -1, blankline

        ## links
        # def protocal(): return [_(r'http://'), _(r'https://'), _(r'ftp://')]
        def direct_link():  return _(r'(<)?(?:http://|https://|ftp://)[\w\d\-\.,@\?\^=%&:/~+#]+(?(1)>)')
        def image_link():   return _(r'(<)?(?:http://|https://|ftp://).*?(?:\.png|\.jpg|\.gif|\.jpeg)(?(1)>)', re.I)
        def mailto():       return _(r'<(mailto:)?[a-zA-Z_0-9-/\.]+@[a-zA-Z_0-9-/\.]+>')
        def wiki_link():    return _(r'(\[\[)(.*?)((1)?\]\])')

        # def inline_image_title(): return literal
        def inline_text():      return _(r'[^\]\^]*')
        def inline_image_alt(): return _(r'!\['), inline_text, _(r'\]')
        def inline_href():      return _(r'[^\s\)]+')
        def inline_image_link():return _(r'\('), inline_href, 0, space, 0, inline_link_title, 0, space, _(r'\)')
        def inline_image(): return inline_image_alt, inline_image_link

        def refer_image_alt():  return _(r'!\['), inline_text, _(r'\]')
        def refer_image_refer():return _(r'[^\]]*')
        def refer_image():      return refer_image_alt, 0, space, _(r'\['), refer_image_refer, _(r'\]')
        # def refer_image_title(): return [literal, literal1, r'\(.*?\)']

        def inline_link_caption(): return _(r'\['), _(r'[^\]\^]*'), _(r'\]')
        def inline_link_title(): return literal
        def inline_link_link(): return _(r'\('), _(r'[^\s\)]+'), 0, space, 0, inline_link_title, 0, space, _(r'\)')
        def inline_link(): return inline_link_caption, inline_link_link

        def refer_link_caption(): return _(r'\['), _(r'[^\]\^]*'), _(r'\]')
        def refer_link_refer(): return _(r'[^\]]*')
        def refer_link(): return refer_link_caption, 0, space, _(r'\['), refer_link_refer, _(r'\]')
        def refer_link_link(): return 0, _(r'(<)?(\S+)(?(1)>)')
        def refer_link_title(): return [_(r'\([^\)]*\)'), literal, literal1]
        def refer_link_note(): return 0, _(r' {1,3}'), inline_link_caption, _(
            r':'), space, refer_link_link, 0, (ws, refer_link_title), -2, blankline
        
        def link(): return [inline_image, refer_image, inline_link, refer_link, image_link, direct_link, wiki_link, mailto], -1, space

        ## article
        def content(): return -2, [ blanklines, hr, title, refer_link_note, directive,
                                    pre, html_block,
                                    side_block, new_block,
                                    table, table2,
                                    lists, dl,
                                    blockquote, footnote_desc,
                                    paragraph
                                ]
        #def metacontent(): return -2, [ content ]
        def article(): return content

        peg_rules = {}
        for k, v in ((x, y) for (x, y) in list(locals().items()) if isinstance(y, types.FunctionType)):
            peg_rules[k] = v
        return peg_rules, article


class MarkdownHtmlVisitor(WikiHtmlVisitor):
    op_maps = {
        '`'  :  ['<code>',          '</code>'],
        '*'  :  ['<em>',            '</em>'],
        '_'  :  ['<em>',            '</em>'],
        '**' :  ['<strong>',        '</strong>'],
        '***':  ['<strong><em>',    '</em></strong>'],
        '___':  ['<strong><em>',    '</em></strong>'],
        '__' :  ['<strong>',        '</strong>'],
        '^'  :  ['<sup>',           '</sup>'],
        ',,' :  ['<sub>',           '</sub>'],
        '~~' :  ['<span style="text-decoration: line-through">', '</span>'],
    }
    tag_class = {}

    def __init__(self, template=None, tag_class=None, grammar=None,
                    title='Untitled', block_callback=None, init_callback=None,
                    wiki_prefix='./', footnote_id=None, filename=None):
        super(MarkdownHtmlVisitor, self).__init__(template, tag_class,
                                                    grammar, title, block_callback, init_callback, filename=filename)

        self.refer_links = {}
        self.chars = list(self.op_maps.keys())
        self.chars.sort(key=lambda x: len(x), reverse=True)
        self.wiki_prefix = wiki_prefix
        self.footnote_id = footnote_id or 1
        self.footnodes = []
        self.tocitems = []

    def visit(self, nodes, root=False):
        if root:
            for obj in nodes[0].find_all('refer_link_note'):
                self.visit_refer_link_note(obj)

            # Collect titles for use in ToC
            for onk in nodes[0].find_all('title'):
                self._alt_title(onk)
        
        return super(MarkdownHtmlVisitor, self).visit(nodes, root)

    def parse_text(self, text, peg=None):
        g = self.grammar or MarkdownGrammar()
        if isinstance(peg, str):
            peg = g[peg]
        resultSoFar = []
        result, rest = g.parse(text, root=peg, resultSoFar=resultSoFar, skipWS=False)
        v = self.__class__('', self.tag_class, g, block_callback=self.block_callback,
                        init_callback=self.init_callback, wiki_prefix=self.wiki_prefix, filename=self.filename,
                        footnote_id=self.footnote_id)
        v.refer_links = self.refer_links
        r = v.visit(result)
        self.footnote_id = v.footnote_id
        
        return r


    def process_line(self, line):
        chars = self.chars
        op_maps = self.op_maps

        buf = []
        pos = []  # stack of special chars
        i = 0
        codes = re.split(r"\\s+", line)
        while i < len(codes):
            left = codes[i]

            # process begin match
            for c in chars:
                if left.startswith(c):
                    p = left[len(c):]
                    if p:
                        buf.append(c)
                        pos.append(len(buf) - 1)
                        left = p
                    else:
                        buf.append(left)
                        left = ''
                    break

            # process end match
            if left:
                for c in chars:
                    if left.endswith(c):
                        p = left[:-len(c)]
                        if p:
                            while len(pos) > 0:
                                t = pos.pop()
                                if buf[t] == c:
                                    buf[t] = op_maps[c][0]
                                    buf.append(p)
                                    buf.append(op_maps[c][1])
                                    left = ''
                                    break
                        break

            if left:
                buf.append(left)

            i += 1
            if i < len(codes):
                buf.append(codes[i])
                i += 1
        
        return ''.join(buf)

    def visit_string(self, node):
        return self.to_html(node.text)

    def visit_blanklines(self, node):
        return '\n'

    def visit_blankline(self, node):
        return '\n'

    def visit_longdash(self, node):
        return '—' # &mdash;

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

        # process classes
        _cls = []
        for x in node.find_all('attr_def_class'):
            _cls.append(x.text[1:])

        return self.tag('h' + str(level), title + anchor, id=_id, _class=' '.join(_cls))

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
        text = self.parse_text(txt, 'words')

        return self.tag('p', self.process_line(text))

    def visit_pre(self, node):
        lang = node.find('pre_lang')
        kwargs = {}
        cwargs = {}
        if lang:
            for n in lang.find_all('block_kwargs'):
                k = n.find('block_kwargs_key').text.strip()
                v_node = n.find('block_kwargs_value')
                if v_node:
                    v = v_node.text.strip()
                    if k == 'lang':
                        k = 'class'
                        v = 'language-' + v
                        cwargs[k] = v
                        continue
                else:
                    v = 'language-' + k
                    k = 'class'
                    cwargs[k] = v
                    continue
                kwargs[k] = v
        
        return self.tag('pre', self.tag('code', self.to_html(self.visit(node).rstrip()), newline=False, **cwargs),
                        **kwargs)

    def visit_pre_extra1(self, node):
        return node.find('pre_text1').text.rstrip()

    def visit_pre_extra2(self, node):
        return node.find('pre_text2').text.rstrip()

    def visit_inline_link(self, node):
        kwargs = {'href': node[1][1]}
        if len(node[1]) > 3:
            kwargs['title'] = node[1][3].text[1:-1]
        caption = node[0].text[1:-1].strip()
        if not caption:
            caption = kwargs['href']
        
        return self.tag('a', caption, newline=False, **kwargs)

    def visit_inline_image(self, node):
        kwargs = {}
        title = node.find('inline_link_title')
        alt = node.find('inline_text')
        location = node.find('inline_href').text

        # TODO: Move to .tag
        scheme = re.search(r'^(\w{3,5})://.+', location)
        if scheme:
            scheme = scheme.group(1)
            
            if scheme.lower() in ['javascript', 'vbscript', 'data']: #Just be safe
                return ""
            yt_id = re.search(r"""youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed|v\/)([^\?&"'>]+)""", location)
            if yt_id:
                return f"<object class='yt-embed' data='https://www.youtube.com/embed/{yt_id.group(1)}'></object>"
        location = "images/" + location  # later may need to split media so bbl

        src = location
        kwargs['src'] = src
        if title:
            kwargs['title'] = title.text[1:-1]
        if alt:
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

    def visit_refer_link(self, node):
        caption = node.find('refer_link_caption')[1]
        key = node.find('refer_link_refer')

        if not key:
            key = caption
        else:
            key = key.text
        
        return self.tag('a', caption, **self.refer_links.get(key.upper(), {}))

    def visit_refer_image(self, node):
        kwargs = {}

        alt = node.find('refer_image_alt')
        if alt:
            alt = alt.find('inline_text').text
        else:
            alt = ''
        key = node.find('refer_image_refer')
        if not key:
            key = alt
        else:
            key = key.text
        
        d = self.refer_links.get(key.upper(), {})
        kwargs.update({'src': d.get('href', ''), 'title': d.get('title', '')})

        return self.tag('img', enclose=1, **kwargs)

    def visit_refer_link_note(self, node):
        key = node.find('inline_link_caption').text[1:-1].upper()
        self.refer_links[key] = {'href': node.find('refer_link_link').text}

        r = node.find('refer_link_title')
        if r:
            self.refer_links[key]['title'] = r.text[1:-1]
        
        return ''

    def template(self, node):
        body = self.visit(node, True)
        return self._template % {'title': self.title, 'body': body}

    def visit_direct_link(self, node):
        t = node.text

        if t.startswith('<'):
            t = t[1:-1]
        href = t

        return self.tag('a', href, newline=False, href=href)

    def visit_wiki_link(self, node):
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
                    cls += ' width="%spx"' % width
                else:
                    cls += ' width="%s"' % width
            if height:
                if height.isdigit():
                    cls += ' height="%spx"' % height
                else:
                    cls += ' height="%s"' % height

            # TODO: Move to .tag
            s = '<img src="images/%s" %s/>' % (filename, cls)
            if align:
                s = '<div class="float%s">%s</div>' % (align, s)
            
            return s

    def visit_image_link(self, node):
        t = node.text
        if t.startswith('<'):
            e = -1
            b = 1
        else:
            b = 0
            e = len(t)
        href = t[b:e]

        return self.tag('img', src="images/" + href, enclose=1)

    def visit_mailto(self, node):
        href = node.text[1:-1]
        if href.startswith('mailto:'):
            href = href[7:]

        def shuffle(text):
            import random

            t = []
            for x in text:
                if random.choice('01') == '1':
                    t.append('&#x%X;' % ord(x))
                else:
                    t.append(x)
            return ''.join(t)

        return self.tag('a', shuffle(href), href=shuffle("mailto:" + href), newline=False)

    def visit_quote_line(self, node):
        return node.text[2:]

    def visit_quote_blank_line(self, node):
        return '\n'

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

    def visit_list_content_line(self, node):
        return node.text.strip()

    def visit_list_content_indent_line(self, node):
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

        return ('<span class="inline-tag%s" data-rel="' % cls) + rel + '">' + name + '</span>'

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
                v = node.find('block_kwargs_value')
                if v:
                    v = v.text.strip()
                kwargs[k] = v
            
            block = {'name': m.group(1), 'body': m.group(3).strip(), 'kwargs': kwargs}
            
        func = self.block_callback.get(block['name'])
        if func:
            return func(self, block)
        else:
            return ''
#            return node.text

    def visit_side_block_item(self, node):
        txt = self.visit(node).rstrip()
        content = [self.parse_text(thing.text, 'content')
                    for thing in node.find('side_block_content')]

        # node[kwargs]
        return self.tag('div', "\n".join(content), enclose=1, _class="collection-horiz")


    def visit_table_column(self, node):
        text = self.parse_text(node.text[:-2].strip(), 'words')
        return self.tag('td', self.process_line(text), newline=False)

    def visit_table2_begin(self, node):
        self.table_align = {}
        separator = node.find('table_separator')
        for i, x in enumerate(list(separator.find_all('table_separator_line')) +
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
                s.append('<th>%s</th>' % self.process_line(text.strip()))
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

        def get_node():
            for t in ('table_td', 'table_other'):
                for x in node.find_all(t):
                    yield x

        s = ['<tr>']
        for i, x in enumerate(get_node()):
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
        title = node.find('directive_title')

        s = []

        if name in ['toc', 'contents']:
            if len(self.tocitems):
                hi = 0
                s.append("<section class='toc'><ul>")
                for lvl, anchor, title in self.tocitems:
                    if lvl > hi:
                        hi = lvl
                        s.append("<ul>")
                    elif lvl < hi:
                        hi = lvl
                        s.append("</ul>")
                    s.append(f"<li><a href='#{anchor}'>{title}</a></li>")
                    
                s.append("</ul></section>")

            # Since we visited these before generating, reset the dict to make sure headings get correct id's
            self.titles_ids = {}

        return ''.join(s)

    def visit_footnote(self, node):
        name = node.text[2:-1]
        _id = self.footnote_id
        self.footnote_id += 1

        return '<sup id="fnref-%s"><a href="#fn-%s" class="footnote-rel inner">%d</a></sup>' % (name, name, _id)

    def visit_footnote_desc(self, node):
        name = node.find('footnote').text[2:-1]
        if name in self.footnodes:
            raise Exception("The footnote %s is already existed" % name)

        txt = self.visit(node.find('footnote_text')).rstrip()
        text = self.parse_text(txt, 'article')
        n = {'name': '%s' % name, 'text': text}
        self.footnodes.append(n)

        return ''

    def visit_star_rating(self, node):
        r = _(r"(?P<stars>[★☆⚝✩✪✫✬✭✮✯✰✱✲✳✴✶✷✻⭐⭑⭒🌟🟀🟂🟃🟄🟆🟇🟈🟉🟊🟌🟍⍟]+) */ *(?P<outta>\d+)")
        m = r.match(node.text)
        if m:
            numstars = len(str(m.group("stars")))

            return f"<span>{'⭐' * numstars}</span>"

    def __end__(self):
        s = []
        
        if len(self.footnodes) > 0:
            s.append('<div class="footnotes"><ol>')
            for n in self.footnodes:
                name = n['name']
                s.append('<li id="fn-%s">' % (name, ))
                s.append(n['text'])
                s.append(self.tag('a', '↩', href='#fnref-%s' %
                                    name, _class='footnote-backref'))
                s.append('</li>')
            s.append('</ol></div>')
        
        return '\n'.join(s)


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
