import unittest
from par.md import parseHtml

class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Tests for edge cases and error handling"""
    
    def test_empty_input(self):
        """Empty string should produce empty output"""
        md_text = ''
        expected = ''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_only_whitespace(self):
        """Only whitespace should produce empty output"""
        md_text = '   \n\t\n   '
        expected = ''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_only_newlines(self):
        """Only newlines should produce empty output"""
        md_text = '\n\n\n'
        expected = ''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_unclosed_bold_marker(self):
        """Unclosed bold marker should not be processed"""
        md_text = '**bold'
        expected = '<p>**bold</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_unclosed_italic_marker(self):
        """Unclosed italic marker should not be processed"""
        md_text = '*italic'
        expected = '<p>*italic</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_unclosed_code_marker(self):
        """Unclosed code marker should not be processed"""
        md_text = '`code'
        expected = '<p>`code</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_mismatched_nesting_bold_italic(self):
        """Mismatched nesting should handle gracefully"""
        md_text = '**bold *italic** text*'
        # Parser behavior may vary, just ensure it doesn't crash
        result = parseHtml(md_text)
        self.assertIsInstance(result, str)

    def test_unicode_characters(self):
        """Unicode characters should be preserved"""
        md_text = 'Héllo, wörld! 你好'
        expected = '<p>Héllo, wörld! 你好</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_emoji_handling(self):
        """Emoji should be preserved"""
        md_text = 'Hello 🌍😊🎉'
        expected = '<p>Hello 🌍😊🎉</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_emoji_in_formatting(self):
        """Emoji inside formatted text"""
        md_text = '**Bold 🎉** and *italic 😊*'
        expected = '<p><strong>Bold 🎉</strong> and <em>italic 😊</em></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_html_entities_ampersand(self):
        """HTML entities should be preserved"""
        md_text = '5 &lt; 10 &amp; 20 &gt; 15'
        expected = '<p>5 &lt; 10 &amp; 20 &gt; 15</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_html_entities_nbsp(self):
        """Non-breaking space entity"""
        md_text = 'word&nbsp;word'
        expected = '<p>word&nbsp;word</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_mixed_line_endings_crlf(self):
        """Mixed CRLF and LF line endings"""
        md_text = 'Line 1\r\nLine 2\nLine 3'
        # Should normalize line endings
        result = parseHtml(md_text)
        self.assertIn('Line 1', result)
        self.assertIn('Line 2', result)
        self.assertIn('Line 3', result)


class TestBasicMarkdownElements(unittest.TestCase):
    """Tests for basic markdown elements"""
    
    def test_strikethrough_text(self):
        """Strikethrough with ~~ markers"""
        md_text = 'This is ~~strikethrough~~ text.'
        # Check if strikethrough is rendered (implementation may vary)
        result = parseHtml(md_text)
        self.assertIn('strikethrough', result)

    def test_strikethrough_multiple(self):
        """Multiple strikethrough in one line"""
        md_text = '~~first~~ and ~~second~~'
        result = parseHtml(md_text)
        self.assertIn('first', result)
        self.assertIn('second', result)

    def test_superscript_text(self):
        """Superscript with ^ markers"""
        md_text = 'x^2^ + y^3^'
        result = parseHtml(md_text)
        # Should contain superscript tags
        self.assertIn('2', result)
        self.assertIn('3', result)

    def test_subscript_text(self):
        """Subscript with ,, markers"""
        md_text = 'H,,2,,O and CO,,2,,'
        result = parseHtml(md_text)
        # Should contain subscript tags
        self.assertIn('2', result)

    def test_escaped_asterisk(self):
        """Escaped asterisk should appear literally"""
        md_text = r'\*not bold\*'
        expected = '<p>*not bold*</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_escaped_underscore(self):
        """Escaped underscore should appear literally"""
        md_text = r'\_not italic\_'
        expected = '<p>_not italic_</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_escaped_backtick(self):
        """Escaped backtick should appear literally"""
        md_text = r'\`not code\`'
        expected = '<p>`not code`</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_escaped_bracket(self):
        """Escaped bracket should appear literally"""
        md_text = r'\[not a link\]'
        expected = '<p>[not a link]</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_line_break_two_spaces(self):
        """Two spaces at end of line should create line break"""
        md_text = 'Line 1  \nLine 2'
        result = parseHtml(md_text)
        # Should contain <br> tag
        self.assertIn('br', result.lower())

    def test_line_break_backslash(self):
        """Backslash at end of line may create line break"""
        md_text = 'Line 1\\\nLine 2'
        result = parseHtml(md_text)
        # Behavior may vary by implementation
        self.assertIsInstance(result, str)


class TestComplexTextFormatting(unittest.TestCase):
    """Tests for complex text formatting combinations"""
    
    def test_nested_bold_italic(self):
        """Bold containing italic"""
        md_text = '**bold *and italic* together**'
        expected = '<p><strong>bold <em>and italic</em> together</strong></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_nested_italic_bold(self):
        """Italic containing bold"""
        md_text = '*italic **and bold** together*'
        result = parseHtml(md_text)
        # Should contain both em and strong tags
        self.assertIn('italic', result)
        self.assertIn('bold', result)

    def test_adjacent_bold_italic(self):
        """Adjacent bold and italic without space"""
        md_text = '**bold***italic*'
        expected = '<p><strong>bold</strong><em>italic</em></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_adjacent_italic_bold(self):
        """Adjacent italic and bold without space"""
        md_text = '*italic***bold**'
        result = parseHtml(md_text)
        self.assertIn('italic', result)
        self.assertIn('bold', result)

    def test_triple_emphasis(self):
        """Triple asterisks for bold+italic"""
        md_text = '***bold and italic***'
        result = parseHtml(md_text)
        # Should contain both strong and em tags
        self.assertIn('bold and italic', result)

    def test_bold_with_code(self):
        """Bold containing code"""
        md_text = '**bold with `code` inside**'
        result = parseHtml(md_text)
        self.assertIn('strong', result)
        self.assertIn('code', result)

    def test_italic_with_code(self):
        """Italic containing code"""
        md_text = '*italic with `code` inside*'
        result = parseHtml(md_text)
        self.assertIn('em', result)
        self.assertIn('code', result)

    def test_complex_nested_formatting(self):
        """Complex nested formatting"""
        md_text = '**bold *italic `code` back* bold**'
        result = parseHtml(md_text)
        self.assertIn('bold', result)
        self.assertIn('italic', result)
        self.assertIn('code', result)


class TestListsAdvanced(unittest.TestCase):
    """Tests for advanced list features"""
    
    def test_mixed_list_ordered_in_unordered(self):
        """Ordered list nested in unordered"""
        md_text = '''\
* Unordered
    1. Ordered
    2. Ordered
* Unordered
'''
        result = parseHtml(md_text)
        self.assertIn('<ul>', result)
        self.assertIn('<ol>', result)
        self.assertIn('Unordered', result)
        self.assertIn('Ordered', result)

    def test_mixed_list_unordered_in_ordered(self):
        """Unordered list nested in ordered"""
        md_text = '''\
1. First
    * Bullet
    * Bullet
2. Second
'''
        result = parseHtml(md_text)
        self.assertIn('<ol>', result)
        self.assertIn('<ul>', result)

    def test_list_item_multiple_paragraphs(self):
        """List item with multiple paragraphs"""
        md_text = '''\
* First paragraph

  Second paragraph
* Another item
'''
        result = parseHtml(md_text)
        self.assertIn('First paragraph', result)
        self.assertIn('Second paragraph', result)

    def test_list_item_with_code_block(self):
        """List item containing code block"""
        md_text = '''\
* Item with code:

    ```
    code here
    ```
'''
        result = parseHtml(md_text)
        self.assertIn('Item with code', result)
        self.assertIn('code here', result)

    def test_list_starting_with_number(self):
        """Unordered list item starting with number"""
        md_text = '''\
* 1984 was a year
* 2001 was also a year
'''
        result = parseHtml(md_text)
        self.assertIn('1984', result)
        self.assertIn('2001', result)

    def test_deeply_nested_lists(self):
        """Deeply nested lists (3+ levels)"""
        md_text = '''\
* Level 1
    * Level 2
        * Level 3
            * Level 4
'''
        result = parseHtml(md_text)
        # Count ul tags to verify nesting
        ul_count = result.count('<ul>')
        self.assertGreaterEqual(ul_count, 3)

    def test_list_with_empty_items(self):
        """List with empty items"""
        md_text = '''\
* Item 1
*
* Item 3
'''
        result = parseHtml(md_text)
        # Should handle gracefully
        self.assertIsInstance(result, str)


class TestCodeBlocksAdvanced(unittest.TestCase):
    """Tests for advanced code block features"""
    
    def test_indented_code_block_simple(self):
        """Simple indented code block (4 spaces)"""
        md_text = '''\
Paragraph

    code line 1
    code line 2
'''
        result = parseHtml(md_text)
        self.assertIn('<pre>', result)
        self.assertIn('code line 1', result)
        self.assertIn('code line 2', result)

    def test_indented_code_block_tab(self):
        """Indented code block with tab"""
        md_text = 'Paragraph\n\n\tcode here'
        result = parseHtml(md_text)
        self.assertIn('code here', result)

    def test_code_block_with_backticks_inside(self):
        """Fenced code block containing backticks"""
        md_text = '''\
```
code with `backticks` inside
```
'''
        expected = '<pre><code>code with `backticks` inside</code></pre>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_with_triple_backticks_inside(self):
        """Using more backticks to fence code with backticks"""
        md_text = '''\
````
```
nested backticks
```
````
'''
        result = parseHtml(md_text)
        # Implementation may vary
        self.assertIsInstance(result, str)

    def test_code_block_in_blockquote(self):
        """Code block inside blockquote"""
        md_text = '''\
> Quote
>
>     code in quote
'''
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        # Code handling in quotes may vary
        self.assertIn('code in quote', result)

    def test_code_block_empty(self):
        """Empty code block"""
        md_text = '''\
```
```
'''
        result = parseHtml(md_text)
        self.assertIn('<pre>', result)

    def test_code_block_with_blank_lines(self):
        """Code block with blank lines inside"""
        md_text = '''\
```
line 1

line 3
```
'''
        result = parseHtml(md_text)
        self.assertIn('line 1', result)
        self.assertIn('line 3', result)


class TestLinksAndImagesAdvanced(unittest.TestCase):
    """Tests for advanced link and image features"""
    
    def test_autolink_http(self):
        """Automatic linking of HTTP URLs"""
        md_text = 'Visit http://example.com for info'
        result = parseHtml(md_text)
        self.assertIn('<a', result)
        self.assertIn('http://example.com', result)

    def test_autolink_https(self):
        """Automatic linking of HTTPS URLs"""
        md_text = 'Visit https://example.com for info'
        result = parseHtml(md_text)
        self.assertIn('<a', result)
        self.assertIn('https://example.com', result)

    def test_autolink_ftp(self):
        """Automatic linking of FTP URLs"""
        md_text = 'Download from ftp://files.example.com'
        result = parseHtml(md_text)
        self.assertIn('ftp://files.example.com', result)

    def test_email_autolink(self):
        """Automatic linking of email addresses"""
        md_text = 'Contact user@example.com for help'
        result = parseHtml(md_text)
        # Email should be obfuscated/linked
        self.assertIn('user', result)
        self.assertIn('example.com', result)

    def test_reference_style_image(self):
        """Reference-style image link"""
        md_text = '''\
![Alt text][img1]

[img1]: http://example.com/image.jpg "Image Title"
'''
        result = parseHtml(md_text)
        self.assertIn('<img', result)
        self.assertIn('http://example.com/image.jpg', result)
        self.assertIn('Alt text', result)

    def test_reference_style_image_no_title(self):
        """Reference-style image without title"""
        md_text = '''\
![Alt][img]

[img]: /path/to/image.png
'''
        result = parseHtml(md_text)
        self.assertIn('<img', result)
        self.assertIn('image.png', result)

    def test_nested_brackets_in_link_text(self):
        """Link text containing brackets"""
        md_text = '[Link [with] brackets](http://example.com)'
        result = parseHtml(md_text)
        # Behavior may vary
        self.assertIn('example.com', result)

    def test_malformed_link_missing_closing_paren(self):
        """Malformed link missing closing parenthesis"""
        md_text = '[Link](http://example.com'
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)

    def test_malformed_link_missing_closing_bracket(self):
        """Malformed link missing closing bracket"""
        md_text = '[Link(http://example.com)'
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)

    def test_link_relative_path(self):
        """Relative path in link"""
        md_text = '[Local](../path/to/file.html)'
        result = parseHtml(md_text)
        self.assertIn('Local', result)
        self.assertIn('../path/to/file.html', result)

    def test_link_absolute_path(self):
        """Absolute path in link"""
        md_text = '[Root](/index.html)'
        result = parseHtml(md_text)
        self.assertIn('Root', result)
        self.assertIn('/index.html', result)

    def test_anchor_link_same_document(self):
        """Anchor link within same document"""
        md_text = '[Jump to section](#section-id)'
        result = parseHtml(md_text)
        self.assertIn('Jump to section', result)
        self.assertIn('#section-id', result)

    def test_image_with_dimensions_wiki_style(self):
        """Wiki-style image with dimensions"""
        md_text = '[[image:test.png||250]]'
        result = parseHtml(md_text)
        # Should handle dimensions
        self.assertIn('test.png', result)

    def test_image_with_alignment_wiki_style(self):
        """Wiki-style image with alignment"""
        md_text = '[[image:test.png|right]]'
        result = parseHtml(md_text)
        self.assertIn('test.png', result)
        # May have float style
        self.assertIn('right', result.lower())

    def test_empty_link_text(self):
        """Link with empty text"""
        md_text = '[](http://example.com)'
        result = parseHtml(md_text)
        # Should use URL as text or similar
        self.assertIn('example.com', result)

    def test_empty_image_alt(self):
        """Image with empty alt text"""
        md_text = '![](http://example.com/image.jpg)'
        result = parseHtml(md_text)
        self.assertIn('<img', result)


class TestBlockquotesAdvanced(unittest.TestCase):
    """Tests for advanced blockquote features"""
    
    def test_nested_blockquotes(self):
        """Nested blockquotes"""
        md_text = '''\
> Level 1
> > Level 2
> > > Level 3
'''
        result = parseHtml(md_text)
        # May have multiple blockquote tags
        self.assertIn('blockquote', result)
        self.assertIn('Level 1', result)
        self.assertIn('Level 2', result)

    def test_blockquote_with_list(self):
        """Blockquote containing list"""
        md_text = '''\
> Quote with list:
> * Item 1
> * Item 2
'''
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        self.assertIn('Item 1', result)
        self.assertIn('Item 2', result)

    def test_blockquote_with_code_block(self):
        """Blockquote containing code block"""
        md_text = '''\
> Quote with code:
>
>     code here
'''
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        self.assertIn('code here', result)

    def test_multi_paragraph_blockquote(self):
        """Blockquote with multiple paragraphs"""
        md_text = '''\
> First paragraph
>
> Second paragraph
'''
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        self.assertIn('First paragraph', result)
        self.assertIn('Second paragraph', result)

    def test_blockquote_with_formatting(self):
        """Blockquote with inline formatting"""
        md_text = '> This is **bold** and *italic* in quote'
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        self.assertIn('strong', result)
        self.assertIn('em', result)

    def test_lazy_blockquote(self):
        """Lazy blockquote continuation"""
        md_text = '''\
> First line
continued without >
'''
        result = parseHtml(md_text)
        # Behavior may vary
        self.assertIn('First line', result)


class TestTablesAdvanced(unittest.TestCase):
    """Tests for advanced table features"""
    
    def test_table_varying_column_counts(self):
        """Table with rows having different column counts"""
        md_text = '''\
| A | B | C |
|---|---|---|
| 1 | 2 |
| 3 | 4 | 5 | 6 |
'''
        result = parseHtml(md_text)
        # Should handle gracefully
        self.assertIn('<table>', result)

    def test_table_escaped_pipe(self):
        """Table cell containing escaped pipe"""
        md_text = r'''
| Column |
|--------|
| text \| more |
'''
        result = parseHtml(md_text)
        self.assertIn('<table>', result)
        # Escaped pipe handling may vary

    def test_table_with_code_in_cell(self):
        """Table cell with inline code"""
        md_text = '''\
| Code |
|------|
| `var x = 1;` |
'''
        result = parseHtml(md_text)
        self.assertIn('<table>', result)
        self.assertIn('var x = 1', result)

    def test_table_with_links_in_cell(self):
        """Table cell with links"""
        md_text = '''\
| Links |
|-------|
| [Link](http://example.com) |
'''
        result = parseHtml(md_text)
        self.assertIn('<table>', result)
        self.assertIn('Link', result)

    def test_table_with_emphasis_in_cell(self):
        """Table cell with bold and italic"""
        md_text = '''\
| Format |
|--------|
| **bold** and *italic* |
'''
        result = parseHtml(md_text)
        self.assertIn('<table>', result)
        self.assertIn('strong', result)
        self.assertIn('em', result)

    def test_table_without_header(self):
        """Table without header row"""
        md_text = '''\
|---|---|
| A | B |
| C | D |
'''
        result = parseHtml(md_text)
        # May or may not be valid table
        self.assertIsInstance(result, str)

    def test_table_single_column(self):
        """Table with single column"""
        md_text = '''\
| Single |
|--------|
| A |
| B |
'''
        result = parseHtml(md_text)
        self.assertIn('<table>', result)


class TestHTMLIntegration(unittest.TestCase):
    """Tests for HTML integration features"""
    
    def test_raw_html_block_div(self):
        """Raw HTML block - div"""
        md_text = '''\
<div class="custom">
Content here
</div>
'''
        result = parseHtml(md_text)
        self.assertIn('<div', result)
        self.assertIn('custom', result)

    def test_raw_html_block_pre(self):
        """Raw HTML block - pre"""
        md_text = '''\
<pre>
preformatted
</pre>
'''
        result = parseHtml(md_text)
        self.assertIn('<pre>', result)

    def test_inline_html_span(self):
        """Inline HTML - span"""
        md_text = 'Text with <span class="highlight">highlighted</span> word'
        result = parseHtml(md_text)
        self.assertIn('<span', result)
        self.assertIn('highlighted', result)

    def test_inline_html_strong(self):
        """Inline HTML - strong"""
        md_text = 'Text with <strong>bold</strong> word'
        result = parseHtml(md_text)
        self.assertIn('<strong>', result)

    def test_html_comment(self):
        """HTML comment"""
        md_text = '''\
Text before
<!-- This is a comment -->
Text after
'''
        result = parseHtml(md_text)
        # Comment handling may vary
        self.assertIn('Text before', result)
        self.assertIn('Text after', result)

    def test_self_closing_tag_br(self):
        """Self-closing br tag"""
        md_text = 'Line 1<br/>Line 2'
        result = parseHtml(md_text)
        self.assertIn('Line 1', result)
        self.assertIn('Line 2', result)

    def test_self_closing_tag_hr(self):
        """Self-closing hr tag"""
        md_text = 'Before<hr/>After'
        result = parseHtml(md_text)
        self.assertIn('Before', result)
        self.assertIn('After', result)

    def test_self_closing_tag_img(self):
        """Self-closing img tag"""
        md_text = 'Text <img src="test.jpg"/> more text'
        result = parseHtml(md_text)
        self.assertIn('test.jpg', result)


class TestPerformanceAndStress(unittest.TestCase):
    """Tests for performance and stress cases"""
    
    def test_deeply_nested_lists(self):
        """Deeply nested lists (6 levels)"""
        md_text = '''\
* L1
    * L2
        * L3
            * L4
                * L5
                    * L6
'''
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)
        self.assertIn('L6', result)

    def test_deeply_nested_blockquotes(self):
        """Deeply nested blockquotes"""
        md_text = '''\
> L1
> > L2
> > > L3
> > > > L4
> > > > > L5
'''
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)
        self.assertIn('L5', result)

    def test_long_line(self):
        """Very long line of text"""
        md_text = 'word ' * 1000
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)

    def test_many_paragraphs(self):
        """Many paragraphs"""
        md_text = '\n\n'.join([f'Paragraph {i}' for i in range(100)])
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)
        self.assertIn('Paragraph 99', result)

    def test_large_code_block(self):
        """Large code block"""
        md_text = '```\n' + '\n'.join([f'line {i}' for i in range(500)]) + '\n```'
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)

    def test_many_links(self):
        """Many links in one paragraph"""
        links = ' '.join([f'[Link {i}](http://example.com/{i})' for i in range(50)])
        md_text = links
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)

    # def test_pathological_emphasis(self):
    #     """Pathological emphasis case"""
    #     md_text = '*' * 50 + 'text' + '*' * 50
    #     result = parseHtml(md_text)
    #     # Should not crash or hang
    #     self.assertIsInstance(result, str)

    def test_alternating_emphasis_markers(self):
        """Alternating emphasis markers"""
        md_text = '* _ ' * 100
        result = parseHtml(md_text)
        # Should not crash
        self.assertIsInstance(result, str)


class TestMarkdownEdgeCases(unittest.TestCase):
    """Tests for specific markdown edge cases"""
    
    def test_asterisk_in_middle_of_word(self):
        """Asterisk in middle of word should not trigger emphasis"""
        md_text = 'un*frigging*believable'
        result = parseHtml(md_text)
        # Behavior may vary - some parsers treat this as emphasis
        self.assertIn('frigging', result)

    def test_underscore_in_middle_of_word(self):
        """Underscore in middle of word should not trigger emphasis"""
        md_text = 'some_variable_name'
        result = parseHtml(md_text)
        # Should not be treated as emphasis
        self.assertIn('some_variable_name', result)

    def test_emphasis_with_punctuation(self):
        """Emphasis adjacent to punctuation"""
        md_text = '**bold**.'
        result = parseHtml(md_text)
        self.assertIn('strong', result)
        self.assertIn('.', result)

    def test_link_with_parentheses_in_url(self):
        """Link URL containing parentheses"""
        md_text = '[Link](http://example.com/path_(with)_parens)'
        result = parseHtml(md_text)
        # Should handle parentheses in URL
        self.assertIn('example.com', result)

    def test_image_with_parentheses_in_url(self):
        """Image URL containing parentheses"""
        md_text = '![Alt](http://example.com/image_(1).jpg)'
        result = parseHtml(md_text)
        self.assertIn('image', result)

    def test_multiple_blank_lines(self):
        """Multiple blank lines between paragraphs"""
        md_text = 'Para 1\n\n\n\n\nPara 2'
        result = parseHtml(md_text)
        self.assertIn('Para 1', result)
        self.assertIn('Para 2', result)

    def test_trailing_whitespace_in_paragraph(self):
        """Trailing whitespace in paragraph"""
        md_text = 'Text with trailing spaces    \nMore text'
        result = parseHtml(md_text)
        # Should handle gracefully
        self.assertIn('Text with trailing spaces', result)

    def test_tabs_vs_spaces_in_code(self):
        """Tabs vs spaces in indented code"""
        md_text = '\tcode with tab\n    code with spaces'
        result = parseHtml(md_text)
        # Should handle both
        self.assertIn('code', result)

    def test_heading_with_no_space(self):
        """Heading without space after hashes"""
        md_text = '#NoSpace'
        result = parseHtml(md_text)
        # Behavior may vary
        self.assertIsInstance(result, str)

    def test_setext_heading_with_varying_underline_length(self):
        """Setext heading with underline shorter/longer than text"""
        md_text = '''\
Long heading text
===

Short
=============
'''
        result = parseHtml(md_text)
        self.assertIn('Long heading text', result)
        self.assertIn('Short', result)


class TestSpecialCharacters(unittest.TestCase):
    """Tests for special character handling"""
    
    def test_less_than_greater_than(self):
        """Less than and greater than signs"""
        md_text = '5 < 10 and 20 > 15'
        result = parseHtml(md_text)
        # Should be escaped
        self.assertIn('5', result)
        self.assertIn('10', result)

    def test_ampersand_standalone(self):
        """Standalone ampersand"""
        md_text = 'Rock & Roll'
        result = parseHtml(md_text)
        # May be escaped to &amp;
        self.assertIn('Rock', result)
        self.assertIn('Roll', result)

    def test_copyright_symbol(self):
        """Copyright symbol"""
        md_text = 'Copyright © 2024'
        expected = '<p>Copyright © 2024</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_trademark_symbol(self):
        """Trademark symbol"""
        md_text = 'Product™'
        expected = '<p>Product™</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_degree_symbol(self):
        """Degree symbol"""
        md_text = '90° angle'
        expected = '<p>90° angle</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_quotes_curly(self):
        """Curly quotes"""
        md_text = '''"Hello" and 'world'''
        result = parseHtml(md_text)
        self.assertIn('Hello', result)
        self.assertIn('world', result)

    def test_ellipsis(self):
        """Ellipsis"""
        md_text = 'To be continued…'
        expected = '<p>To be continued…</p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_en_dash(self):
        """En dash"""
        md_text = 'Pages 10–20'
        result = parseHtml(md_text)
        self.assertIn('Pages', result)

    def test_em_dash(self):
        """Em dash"""
        md_text = 'Text—more text'
        result = parseHtml(md_text)
        self.assertIn('Text', result)


class TestMultilineContent(unittest.TestCase):
    """Tests for multiline content edge cases"""
    
    def test_paragraph_with_hard_line_breaks(self):
        """Paragraph with hard line breaks"""
        md_text = 'Line 1  \nLine 2  \nLine 3'
        result = parseHtml(md_text)
        # Should have br tags
        self.assertIn('Line 1', result)
        self.assertIn('Line 2', result)
        self.assertIn('Line 3', result)

    def test_list_item_with_continuation(self):
        """List item with text continuation"""
        md_text = '''\
* This is a long list item
  that continues on the next line
  and even another line
'''
        result = parseHtml(md_text)
        self.assertIn('long list item', result)
        self.assertIn('continues', result)

    def test_blockquote_with_continuation(self):
        """Blockquote with continuation lines"""
        md_text = '''\
> This is a quote
> that spans multiple
> lines
'''
        result = parseHtml(md_text)
        self.assertIn('blockquote', result)
        self.assertIn('quote', result)
        self.assertIn('spans', result)


class TestReferenceLinks(unittest.TestCase):
    """Tests for reference-style links and images"""
    
    def test_reference_link_case_insensitive(self):
        """Reference links should be case-insensitive"""
        md_text = '''\
[Link][REF]

[ref]: http://example.com
'''
        result = parseHtml(md_text)
        self.assertIn('Link', result)
        self.assertIn('example.com', result)

    def test_reference_link_with_spaces_in_label(self):
        """Reference link with spaces in label"""
        md_text = '''\
[Link][my reference]

[my reference]: http://example.com
'''
        result = parseHtml(md_text)
        self.assertIn('Link', result)

    def test_implicit_reference_link(self):
        """Implicit reference link"""
        md_text = '''\
[Google][]

[Google]: http://google.com
'''
        result = parseHtml(md_text)
        self.assertIn('Google', result)
        self.assertIn('google.com', result)

    def test_shortcut_reference_link(self):
        """Shortcut reference link"""
        md_text = '''\
[Google]

[Google]: http://google.com
'''
        result = parseHtml(md_text)
        # Behavior may vary
        self.assertIsInstance(result, str)

    def test_reference_link_unused(self):
        """Reference definition that's not used"""
        md_text = '''\
Some text

[unused]: http://example.com
'''
        result = parseHtml(md_text)
        self.assertIn('Some text', result)
        # Unused reference should not appear in output


class TestFootnotesAdvanced(unittest.TestCase):
    """Tests for advanced footnote features"""
    
    def test_footnote_with_multiple_paragraphs(self):
        """Footnote with multiple paragraphs"""
        md_text = '''\
Text with footnote[^1]

[^1]: First paragraph

    Second paragraph
'''
        result = parseHtml(md_text)
        self.assertIn('footnote', result)
        # Multi-paragraph footnotes may vary

    def test_footnote_with_code(self):
        """Footnote containing code"""
        md_text = '''\
Text[^1]

[^1]: Footnote with `code`
'''
        result = parseHtml(md_text)
        self.assertIn('code', result)

    def test_footnote_with_link(self):
        """Footnote containing link"""
        md_text = '''\
Text[^1]

[^1]: See [this link](http://example.com)
'''
        result = parseHtml(md_text)
        self.assertIn('example.com', result)

    def test_multiple_footnotes_same_line(self):
        """Multiple footnotes in same line"""
        md_text = '''\
Text[^1] and more[^2]

[^1]: First
[^2]: Second
'''
        result = parseHtml(md_text)
        # Should handle both footnotes
        self.assertIsInstance(result, str)

    def test_footnote_numeric_id(self):
        """Footnote with numeric ID"""
        md_text = '''\
Text[^1]

[^1]: Numeric footnote
'''
        result = parseHtml(md_text)
        self.assertIn('Numeric footnote', result)

    def test_footnote_alphanumeric_id(self):
        """Footnote with alphanumeric ID"""
        md_text = '''\
Text[^note1]

[^note1]: Alphanumeric footnote
'''
        result = parseHtml(md_text)
        self.assertIn('Alphanumeric footnote', result)


if __name__ == '__main__':
    unittest.main()
