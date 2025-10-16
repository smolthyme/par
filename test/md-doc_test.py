import sys; from par.md import parseHtml

from par.md import parseHtml

def test_headers_and_links():
    r"""
    >>> text = '''
    ... # Markdown: Syntax
    ... 
    ... *   [Overview](#overview)
    ...     *   [Philosophy](#philosophy)
    ...     *   [Inline HTML](#html)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <section id="section-markdown-syntax">
    <h1 id="title_0-1">Markdown: Syntax<a class="anchor" href="#title_0-1"></a></h1>
    </section>
    <ul>
    <li><p><a href="#overview">Overview</a></p>
    <ul>
    <li><a href="#philosophy">Philosophy</a></li>
    <li><a href="#html">Inline HTML</a></li>
    </ul></li>
    </ul>
    <BLANKLINE>
    """

def test_horizontal_rule():
    r"""
    >>> text = '''
    ... Some text before
    ... 
    ... ----
    ... 
    ... Some text after
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>Some text before</p>
    <hr/>
    <p>Some text after</p>
    <BLANKLINE>
    """

def test_paragraphs():
    r"""
    >>> text = '''
    ... A paragraph is simply one or more consecutive lines of text, separated by one or more blank lines.
    ... Normal paragraphs should not be indented with spaces or tabs.
    ... 
    ... This is a second paragraph.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>A paragraph is simply one or more consecutive lines of text, separated by one or more blank lines.
    Normal paragraphs should not be indented with spaces or tabs.</p>
    <p>This is a second paragraph.</p>
    <BLANKLINE>
    """

def test_line_breaks():
    r"""
    >>> text = '''
    ... When you *do* want to insert a break tag  
    ... you end a line with two or more spaces.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>When you <em>do</em> want to insert a break tag<br/>
    you end a line with two or more spaces.</p>
    <BLANKLINE>
    """

def test_atx_headers():
    r"""
    >>> text = '''
    ... ## This is a level 2 header
    ... 
    ... ### This is a level 3 header ###
    ... 
    ... #### This is a level 4 header
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <section id="section-this-is-a-level-2-header">
    <h2 id="title_0-1">This is a level 2 header<a class="anchor" href="#title_0-1"></a></h2>
    </section>
    <section id="section-this-is-a-level-3-header">
    <h3 id="title_0-2">This is a level 3 header<a class="anchor" href="#title_0-2"></a></h3>
    </section>
    <section id="section-this-is-a-level-4-header">
    <h4 id="title_0-3">This is a level 4 header<a class="anchor" href="#title_0-3"></a></h4>
    </section>
    """

def test_simple_blockquotes():
    r"""
    >>> text = '''
    ... > This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet.
    ... > 
    ... > Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <blockquote>
    <p>This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet.</p>
    <p>Donec sit amet nisl. Aliquam semper ipsum sit amet velit.</p>
    </blockquote>
    <BLANKLINE>
    """

def test_lazy_blockquotes():
    r"""
    >>> text = '''
    ... > This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet,
    ... consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.
    ... 
    ... > Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <blockquote>
    <p>This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet,
    consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.</p>
    </blockquote>
    <blockquote>
    <p>Donec sit amet nisl. Aliquam semper ipsum sit amet velit.</p>
    </blockquote>
    <BLANKLINE>
    """

def test_nested_blockquotes():
    r"""
    >>> text = '''
    ... > This is the first level of quoting.
    ... >
    ... > > This is nested blockquote.
    ... >
    ... > Back to the first level.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <blockquote>
    <p>This is the first level of quoting.</p>
    <blockquote>
    <p>This is nested blockquote.</p>
    </blockquote>
    <p>Back to the first level.</p>
    </blockquote>
    <BLANKLINE>
    """

def test_blockquotes_with_other_elements():
    r"""
    >>> text = '''
    ... > ## This is a header.
    ... > 
    ... > 1.   This is the first list item.
    ... > 2.   This is the second list item.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <blockquote>
    <section id="section-this-is-a-header">
    <h2 id="title_0-1">This is a header.<a class="anchor" href="#title_0-1"></a></h2>
    </section>
    <ol>
    <li>This is the first list item.</li>
    <li>This is the second list item.</li>
    </ol>
    </blockquote>
    <BLANKLINE>
    """

def test_unordered_lists():
    r"""
    >>> text = '''
    ... *   Red
    ... *   Green
    ... *   Blue
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li>Red</li>
    <li>Green</li>
    <li>Blue</li>
    </ul>
    <BLANKLINE>
    """

def test_unordered_lists_plus():
    r"""
    >>> text = '''
    ... +   Red
    ... +   Green
    ... +   Blue
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li>Red</li>
    <li>Green</li>
    <li>Blue</li>
    </ul>
    <BLANKLINE>
    """

def test_unordered_lists_hyphen():
    r"""
    >>> text = '''
    ... -   Red
    ... -   Green
    ... -   Blue
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li>Red</li>
    <li>Green</li>
    <li>Blue</li>
    </ul>
    <BLANKLINE>
    """

def test_ordered_lists():
    r"""
    >>> text = '''
    ... 1.  Bird
    ... 2.  McHale
    ... 3.  Parish
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li>Bird</li>
    <li>McHale</li>
    <li>Parish</li>
    </ol>
    <BLANKLINE>
    """

def test_ordered_lists_same_number():
    r"""
    >>> text = '''
    ... 1.  Bird
    ... 1.  McHale
    ... 1.  Parish
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li>Bird</li>
    <li>McHale</li>
    <li>Parish</li>
    </ol>
    <BLANKLINE>
    """

def test_ordered_lists_mixed_numbers():
    r"""
    >>> text = '''
    ... 3. Bird
    ... 1. McHale
    ... 8. Parish
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li>Bird</li>
    <li>McHale</li>
    <li>Parish</li>
    </ol>
    <BLANKLINE>
    """

def test_list_with_paragraphs():
    r"""
    >>> text = '''
    ... 1.  This is a list item with two paragraphs. Lorem ipsum dolor sit amet,
    ...     consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.
    ... 
    ...     Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.
    ...     Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
    ... 
    ... 2.  Suspendisse id sem consectetuer libero luctus adipiscing.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li><p>This is a list item with two paragraphs. Lorem ipsum dolor sit amet,
    consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.</p>
    <p>Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.
    Donec sit amet nisl. Aliquam semper ipsum sit amet velit.</p></li>
    <li><p>Suspendisse id sem consectetuer libero luctus adipiscing.</p></li>
    </ol>
    <BLANKLINE>
    """

def test_list_with_blockquote():
    r"""
    >>> text = '''
    ... *   A list item with a blockquote:
    ... 
    ...     > This is a blockquote inside a list item.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li><p>A list item with a blockquote:</p>
    <blockquote>
    <p>This is a blockquote inside a list item.</p>
    </blockquote></li>
    </ul>
    <BLANKLINE>
    """

def test_list_with_code_block():
    r"""
    >>> text = '''
    ... *   A list item with a code block:
    ... 
    ...         <code goes here>
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li><p>A list item with a code block:</p>
    <pre><code>&lt;code goes here&gt;</code></pre></li>
    </ul>
    <BLANKLINE>
    """

def test_code_block_indented():
    r"""
    >>> text = '''
    ... This is a normal paragraph:
    ... 
    ...     This is a code block.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is a normal paragraph:</p>
    <pre><code>This is a code block.</code></pre>
    <BLANKLINE>
    """

def test_code_block_fenced():
    r"""
    >>> text = '''
    ... ```
    ... tell application "Foo"
    ...     beep
    ... end tell
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre><code>tell application "Foo"
    beep
    end tell</code></pre>
    <BLANKLINE>
    """

def test_inline_links():
    r"""
    >>> text = '''
    ... This is [an example](http://example.com/) inline link.
    ... 
    ... [This link](http://example.net/) has no title attribute.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <a href="http://example.com/">an example</a> inline link.</p>
    <p><a href="http://example.net/">This link</a> has no title attribute.</p>
    <BLANKLINE>
    """

def test_emphasis():
    r"""
    >>> text = '''
    ... *single asterisks*
    ... 
    ... _single underscores_
    ... 
    ... **double asterisks**
    ... 
    ... __double underscores__
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p><em>single asterisks</em></p>
    <p><em>single underscores</em></p>
    <p><strong>double asterisks</strong></p>
    <p><strong>double underscores</strong></p>
    <BLANKLINE>
    """

def test_code_span():
    r"""
    >>> text = '''
    ... Use the `printf()` function.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>Use the <code>printf()</code> function.</p>
    <BLANKLINE>
    """

def test_combined_markdown_elements():
    r"""
    >>> text = '''
    ... ## Header with **bold** and *italic*
    ... 
    ... > A blockquote with a [link](http://example.com)
    ... > 
    ... > And some `code` inside
    ... 
    ... 1. List item with **strong** text
    ... 2. Another item with `code`
    ... 
    ... ```
    ... Some code block
    ... with multiple lines
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <section id="section-header-with-bold-and-italic">
    <h2 id="title_0-1">Header with <strong>bold</strong> and <em>italic</em><a class="anchor" href="#title_0-1"></a></h2>
    </section>
    <blockquote>
    <p>A blockquote with a <a href="http://example.com">link</a></p>
    <p>And some <code>code</code> inside</p>
    </blockquote>
    <ol>
    <li>List item with <strong>strong</strong> text</li>
    <li>Another item with <code>code</code></li>
    </ol>
    <pre><code>Some code block
    with multiple lines</code></pre>
    <BLANKLINE>
    """


class termfont:
    # foreground              # background              # end/reset
    fg_black    = '\033[30m'; bg_black    = '\033[40m'; endc         = '\033[0m'   
    fg_red      = '\033[31m'; bg_red      = '\033[41m'; 
    fg_green    = '\033[32m'; bg_green    = '\033[42m'; # effects 
    fg_orange   = '\033[33m'; bg_orange   = '\033[43m'; ef_bold      = '\033[1m'   # 'bright'?
    fg_blue     = '\033[34m'; bg_blue     = '\033[44m'; ef_dim       = '\033[2m'
    fg_magenta  = '\033[35m'; bg_magenta  = '\033[45m'; ef_underline = '\033[4m'
    fg_cyan     = '\033[36m'; bg_cyan     = '\033[46m'; ef_flash     = '\033[5m'
    fg_white    = '\033[37m'; bg_white    = '\033[47m'; ef_highlight = '\033[7m'

    fg_default  = '\033[39m'; bg_default  = '\033[49m'; ef_default   = '\033[22m'  # test?

    @staticmethod # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    def windows_enable_term_features():
        import sys
        if sys.platform=='win32': from ctypes import windll as Wd;Wd.kernel32.SetConsoleMode(Wd.kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def term_size(): import shutil; return (shutil.get_terminal_size().columns, shutil.get_terminal_size().lines)

def display_diff(sample, expected, result, term_width):
    """
    Display short diffs in the terminal, formatted into blocks or printed line-by-line if too wide.
    """

    sample_lines = sample.splitlines()
    expected_lines = expected.splitlines()
    result_lines = result.splitlines() if result != '' else ['']

    from difflib import Differ
    d = Differ()
    diff_lines = list(d.compare(expected_lines, result_lines))

    # Determine the maximum line length for padding
    max_line_length = max(
        max(len(line) for line in sample_lines),
        max(len(line) for line in expected_lines),
        max(len(line) for line in result_lines),
        max(len(line) for line in diff_lines),
    )
    # If blocks are too wide, print lines in order and return
    if (max_line_length *4) > term_width:
        print(f"{termfont.fg_orange}{sample}{termfont.endc}")
        print(f"{termfont.fg_green}{expected}{termfont.endc}")
        print(f"{termfont.fg_red}{result}{termfont.endc}")
        return

    max_line_length = term_width // 4 - 2  # Adjust for terminal width and padding

    # Determine the maximum number of lines for height padding
    max_lines = max(len(sample_lines), len(expected_lines), len(result_lines), len(diff_lines))

    # Pad lines to the maximum length and height
    pad_line = lambda line: line.ljust(max_line_length)
    pad_height = lambda lines: lines + [' ' * max_line_length] * (max_lines - len(lines))

    sample_lines = color_lines([pad_line(line) for line in pad_height(sample_lines)], color=termfont.fg_orange)
    expected_lines = color_lines([pad_line(line) for line in pad_height(expected_lines)], color=termfont.fg_green)
    result_lines = [pad_line(line) for line in pad_height(result_lines)]
    diff_lines = color_lines([pad_line(line) for line in pad_height(diff_lines)], color='diff')

    # Calculate the total width of the blocks
    block_width = max_line_length + 2  # Add 2 for padding
    total_width = block_width * 4  # Four blocks side by side

    if args.verbose:
        # print headers padded to widths
        headers = ['sample', 'expected', 'result', 'diff']
        headerstr = '  '.join(f"{termfont.fg_cyan}{h.ljust(max_line_length)}{termfont.endc}" for h in headers)
        print(headerstr)
        print(f"-" * total_width)

    # Combine lines into blocks
    for s, e, r, d in zip(sample_lines, expected_lines, result_lines, diff_lines):
        print(f"{s}  {e}  {r}  {d}")


def color_lines(lines: list[str], color) -> list[str]:
    if color == 'diff':
        for i in range(len(lines)):
            first_char = lines[i][0]
            match first_char:
                case ' ' , _: continue 
                case '+': lines[i] = termfont.fg_green  + lines[i] + termfont.endc
                case '-': lines[i] = termfont.fg_red    + lines[i] + termfont.endc
                case '!': lines[i] = termfont.fg_orange + lines[i] + termfont.endc
                case '@': lines[i] = termfont.fg_orange + lines[i] + termfont.endc
    elif color is not None:
        for i in range(len(lines)):
            lines[i] = color + lines[i] + termfont.endc
    return lines

import doctest, difflib
from doctest import DocTestFailure, DocTestRunner, DebugRunner

def run_tests(test_name=None):
    """Run doctests and display formatted output for failed tests."""
    termfont.windows_enable_term_features()

    finder = doctest.DocTestFinder()
    runner = DebugRunner()
    tests = finder.find(sys.modules[__name__])
    term_width = termfont.term_size()[0] or 80

    if test_name:
        tests = [test for test in tests if test.name[9:].startswith(test_name)]

    n_failed = 0
    n_run = 0
    total_line_delta = 0  # <-- Add this

    for test in tests:
        runner.test = test
        runner.test.globs = {'parseHtml': parseHtml}
        try:
            runner.run(test)
        except DocTestFailure as failed:
            sample = failed.test.examples[0].source.strip()[11:-4:]
            expected = failed.example.want.strip()
            got = failed.got.strip()

            # Calculate line delta for this failure
            expected_lines = expected.splitlines()
            got_lines = got.splitlines()
            diff = list(difflib.ndiff(expected_lines, got_lines))
            # Count lines that start with '+' or '-'
            line_delta = sum(1 for line in diff if line.startswith('+ ') or line.startswith('- '))
            total_line_delta += line_delta

            print(f"Name: {test.name[9:]} Exception: {type(failed.exc).__name__} Line delta: {line_delta}")
            display_diff(sample, expected, got, term_width)
            print(f"{termfont.fg_cyan}{' - ' * (term_width // 4)}{termfont.endc}")
            n_failed += 1
        n_run += 1

    print(f"{termfont.fg_red if n_failed > 0 else termfont.fg_green}Tests failed: {n_failed}{termfont.endc}")
    print(f"{termfont.fg_green}Tests run: {n_run}{termfont.endc}")
    print(f"{termfont.fg_orange}Total line delta: {total_line_delta}{termfont.endc}")  # <-- Add this

if __name__ == '__main__':
    def get_args():
        import argparse
        argz = argparse.ArgumentParser(description="Run tests for the Markdown parser.")
        argz.add_argument('--verbose', '-v', action='store_true', help='Run tests in verbose mode.')
        argz.add_argument('-n', '--name', type=str, help='(start of-) Name of the test(s) to run.')
        return argz.parse_args()

    args = get_args()
    run_tests(test_name=args.name)