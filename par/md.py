"""Markdown PEG generally informed by https://daringfireball.net/projects/markdown/syntax"""

import types
from par.pyPEG import re, _not, _and, keyword, ignore, Symbol, parseLine
from .__init__ import SimpleVisitor, MDHTMLVisitor

_ = re.compile

class MarkdownGrammar(dict):
    def __init__(self):
        peg, self.root = self._get_rules()
        self.update(peg)
        
    def _get_rules(self):
        ## Return values control matching/repetition
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

        def word()             : return [ # Tries to show parse-order
                escape_string,
                html_block, html_inline_block, inline_tag,
                fmt_bold, fmt_bold2, fmt_italic, fmt_italic2, fmt_code,# fmt_underline,
                fmt_subscript, fmt_superscript, fmt_strikethrough,
                footnote, link, longdash,
                htmlentity, star_rating, string, wordlike
            ]
        
        #def words()            : return word, -1, [space, word]
        def words(ig='(?!)')   : return word, -1, [space, ignore(ig), word] # (?!) is a negative lookahead that never matches   
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

        ## whole article containing content and metadata etc
        def content(): return -2, [blankline,
                hr, link_refer_note, directive,
                pre, html_block, lists,
                side_block, table, dl, blockquote, footnote_desc,
                title, paragraph ]

        def article(): return content

        # Finish up _get_rules() by returning the peg_rules and the 'root'
        peg_rules = {k: v for k, v in locals().items() \
                        if isinstance(v, types.FunctionType)}
        return peg_rules, article
    
    def parse(self, text:str, root=None, skipWS=False, **kwargs):
        # Normalise on unix-style line ending and we end with a newline
        text = re.sub(r'\r\n|\r', '\n', text + ("\n" if not text.endswith("\n") else ''))
        return parseLine(text, root or self.root, skipWS=skipWS, **kwargs)

def parseHtml(text, template=None, tag_class=None, filename=None, grammer=None, visitor=None):
    from .md_html import MarkdownHtmlVisitor
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