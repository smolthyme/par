import unittest
from par.md import parseHtml

class TestFormattingSimpleHTML(unittest.TestCase):
    def test_single_para_with_bold_fmt(self):
        md_text = '''This is **a** bold **test**.'''
        expected = '''<p>This is <strong>a</strong> bold <strong>test</strong>.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_bold_text(self):
        md_text = '''This is **bold** text.'''
        expected = '''<p>This is <strong>bold</strong> text.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_italic_text(self):
        md_text = '''This is *italic* text.'''
        expected = '''<p>This is <em>italic</em> text.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_bold_and_italic_text(self):
        md_text = '''This is ***bold and italic*** text.'''
        expected = '''<p>This is <strong><em>bold and italic</em></strong> text.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_code_text(self):
        md_text = '''This is `inline code`.'''
        expected = '''<p>This is <code>inline code</code>.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_bold_and_code_text(self):
        md_text = '''This is **bold** and `code`.'''
        expected = '''<p>This is <strong>bold</strong> and <code>code</code>.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_combined_formatting_text(self):
        md_text = '''This is **bold**, *italic*, and `code` in one sentence.'''
        expected = '''<p>This is <strong>bold</strong>, <em>italic</em>, and <code>code</code> in one sentence.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestListsSimpleHTML(unittest.TestCase):
    def test_two_item_unordered_list(self):
        md_text = '''\
* a
* b
'''
        expected = '''\
<ul>
<li>a</li>
<li>b</li>
</ul>
'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_two_item_ordered_list(self):
        md_text = '''\
1. a
2. b
'''
        expected = '''\
<ol>
<li>a</li>
<li>b</li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_two_unordered_lists_separated(self):
        md_text = '''\
* a
* b

* c
* d
'''
        expected = '''\
<ul>
<li>a</li>
<li>b</li>
<li>c</li>
<li>d</li>
</ul>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_nested_unordered_list(self):
        md_text = '''\
* a
    * b
    * c
* d
    * e
    '''
        expected = '''\
<ul>
<li><p>a</p>
<ul>
<li>b</li>
<li>c</li>
</ul></li>
<li><p>d</p>
<ul>
<li>e</li>
</ul></li>
</ul>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_numbered_list_with_paragraphs(self):
        md_text = '''\
1. Abacus
2. Bubbles
3. Seals
4. Cunning
'''
        expected = '''\
<ol>
<li>Abacus</li>
<li>Bubbles</li>
<li>Seals</li>
<li>Cunning</li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_list_with_tilde_characters(self):
        md_text = '''\
* 3 km (1.9 mi) ~5 min
* 5 km (3.1 mi) ~10 min
* 10 km (6.2 mi) ~20 min
'''
        expected = '''\
<ul>
<li>3 km (1.9 mi) ~5 min</li>
<li>5 km (3.1 mi) ~10 min</li>
<li>10 km (6.2 mi) ~20 min</li>
</ul>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestListsComplexHTML(unittest.TestCase):
    def test_complex_nested_lists(self):
        md_text = '''\
*   Abacus
    * answer
*   Bubbles
    1.  bunk
    2.  bupkis
        * BELITTLER
    3. burper
*   Cunning
'''
        expected = '''\
<ul>
<li>Abacus
<ul>
<li>answer</li>
</ul></li>
<li>Bubbles
<ol>
<li>bunk</li>
<li>bupkis</li>
<ul>
<li>BELITTLER</li>
</ul></li>
<li>burper</li>
</ol></li>
<li>Cunning</li>
</ul>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


    def test_ordered_list_with_code_block(self):
        md_text = '''\
1. abc

    ```
    code
    ```
'''
        expected = '''\
<ol>
<li><p>abc</p>
<pre><code>code</code></pre></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_ordered_list_with_indented_code(self):
        md_text = '''\
1. abc

        code
'''
        expected = '''\
<ol>
<li><p>abc</p>
<pre><code>code</code></pre></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_nested_definition_list_in_ordered_list(self):
        md_text = '''\
1. aaa

    defaults --
        test:
        
        ```
        return {}
        ```
'''
        expected = '''\
<ol>
<li><p>aaa</p>
<dl>
<dt>defaults</dt>
<dd><p>test:</p>
<pre><code>return {}</code></pre>
</dd>
</dl></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_ordered_list_with_paragraph_and_code(self):
        md_text = '''\
1. abc

    cde

    ```
    code
    ```
'''
        expected = '''\
<ol>
<li><p>abc</p>
<p>cde</p>
<pre><code>code</code></pre></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_list_with_checkboxes_and_radios(self):
        md_text = '''\
* [] a
* [*] b
    * <*> c
    * < > d
* [] a
    * [*] b
    * <*> c
    * < > d
'''
        expected = '''\
<ul>
<li><input type="checkbox"></input>a</li>
<li><p><input type="checkbox" checked></input>b</p>
<ul>
<li><input type="radio" checked></input>c</li>
<li><input type="radio"></input>d</li>
</ul></li>
<li><p><input type="checkbox"></input>a</p>
<ul>
<li><input type="checkbox" checked></input>b</li>
<li><input type="radio" checked></input>c</li>
<li><input type="radio"></input>d</li>
</ul></li>
</ul>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestDefinitionListsHTML(unittest.TestCase):
    def test_definition_list_dash_syntax(self):
        md_text = '''\
a --
    abc

b --
    cde
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dt>b</dt>
<dd><p>cde</p>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_with_formatting_and_list(self):
        md_text = '''\
a --
    abc

**b** --
    * li
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dt><strong>b</strong></dt>
<dd><ul>
<li>li</li>
</ul>
</dd>
</dl>
'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_colon_syntax(self):
        md_text = '''\
a
:   abc

**b**
:   * li
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dt><strong>b</strong></dt>
<dd><ul>
<li>li</li>
</ul>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_with_code_block_dash(self):
        md_text = '''\
a --
    abc

    ```
    code
    ```
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dd><pre><code>code</code></pre>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_with_indented_code_block_def(self):
        md_text = '''\
a
:   abc

    ```
    code
    ```
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dd><pre><code>code</code></pre>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_with_complex_content(self):
        known_failure = "The padding before the code block is kept"
        md_text = '''\
a --
    abc
    
    ```
    code
    abcd
    ```
    
    test

b --c --
    abc
    
    ```
    code
    abcd
    ```
    
    test
'''
        expected = '''\
<dl>
<dt>a</dt>
<dd><p>abc</p>
</dd>
<dd><pre><code>code
abcd</code></pre>
</dd>
<dd><p>test</p>
</dd>
<dt>b --c</dt>
<dd><p>abc</p>
</dd>
<dd><pre><code>code
abcd</code></pre>
</dd>
<dd><p>test</p>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_definition_list_multiple_definitions(self):
        md_text = '''\
Term
: Definition

Another Term
: Its definition
: Can have multiple defs
'''
        expected = '''\
<dl>
<dt>Term</dt>
<dd><p>Definition</p>
</dd>
<dt>Another Term</dt>
<dd><p>Its definition</p>
</dd>
<dd><p>Can have multiple defs</p>
</dd>
</dl>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_horizontal_rules(self):
        md_text = '''\
* * * *
----
__ __ __
'''
        expected = '''\
<hr/>
<hr/>
<hr/>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestLinksHTML(unittest.TestCase):
    def test_inline_link_with_title(self):
        md_text = '''This is [an example](http://example.com/ "Title") inline link.'''
        expected = '''<p>This is <a href="http://example.com/" title="Title">an example</a> inline link.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_link_without_title(self):
        md_text = '''This is [an example](http://example.com/) inline link.'''
        expected = '''<p>This is <a href="http://example.com/">an example</a> inline link.</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_image_with_alt_and_title(self):
        md_text = '''![Alt text](http://example.com/image.jpg "Image Title")'''
        expected = '''<p><img alt="Alt text" src="http://example.com/image.jpg" title="Image Title"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_image_with_alt_only(self):
        md_text = '''![Alt text](http://example.com/image.jpg)'''
        expected = '''<p><img alt="Alt text" src="http://example.com/image.jpg"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestLinksComplexHTML(unittest.TestCase):
    def test_reference_link_double_quotes(self):
        md_text = '''\
This is [Test][foo] .

[foo]: http://example.com/  "Optional Title Here"
    '''
        expected = '''<p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_reference_link_single_quotes(self):
        md_text = '''\
This is [Test][foo] .

[foo]: http://example.com/  'Optional Title Here'
    '''
        expected = '''<p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_reference_link_parentheses(self):
        md_text = '''\
This is [Test][foo] .

[foo]: http://example.com/  (Optional Title Here)
    '''
        expected = '''<p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_reference_link_implicit(self):
        md_text = '''\
This is [foo][] .

[foo]: http://example.com/  (Optional Title Here)
    '''
        expected = '''<p>This is <a href="http://example.com/" title="Optional Title Here">foo</a> .</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_footnotes(self):
        self.maxDiff = None
        md_text = '''\
This is the first topic. [^first]

This is another topic. [^second]

[^first]: This is the first footnote.
[^second]: This is the second footnote.
'''
        expected = '''\
<p>This is the first topic. <sup id="fnref-first"><a class="footnote-rel inner" href="#fn-first">1</a></sup></p>
<p>This is another topic. <sup id="fnref-second"><a class="footnote-rel inner" href="#fn-second">2</a></sup></p>
<div class="footnotes"><ol>
<li id="fn-first">
<p>This is the first footnote.</p>

<a class="footnote-backref inner" href="#fnref-first">↩</a>
</li>
<li id="fn-second">
<p>This is the second footnote.</p>

<a class="footnote-backref inner" href="#fnref-second">↩</a>
</li>
</ol></div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_footnote_with_formatting(self):
        md_text = '''\
That's some text with a footnote.[^1]

[^1]: **aaaa**
'''
        expected = '''\
<p>That's some text with a footnote.<sup id="fnref-1"><a class="footnote-rel inner" href="#fn-1">1</a></sup></p>
<div class="footnotes"><ol>
<li id="fn-1">
<p><strong>aaaa</strong></p>

<a class="footnote-backref inner" href="#fnref-1">↩</a>
</li>
</ol></div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


    def test_image_wrapped_in_link(self):
        md_text = '''\
[![Alt](https://example.com/image.png)](https://example.com/target)
[![Alt text](https://example.com/image.png)](https://example.com)
'''
        expected = '''\
<p><a href="https://example.com/target"><img src="https://example.com/image.png" alt="Alt"/></a></p>
<p><a href="https://example.com"><img src="https://example.com/image.png" alt="Alt text"/></a></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_wiki_style_links_and_images(self):
        md_text = '''\
[[Page|Hello world]]
[[Page#title|Hello world]]
[[wiki:Page|Hello world]]

[[image:a.png]]
[[image:a.png|right]]
[[image:a.png||250]]
'''
        expected = '''\
<p><a href="page.html">Hello world</a></p>
<p><a href="page.html#title">Hello world</a></p>
<p><a href="wiki:page.html">Hello world</a></p>
<p><img src="images/a.png"></img></p>
<p><img src="images/a.png" style="float: right; margin-left: 1em;"></img></p>
<p><img src="images/a.png" style="width: 250px;"></img></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_various_link_formats(self):
        md_text = '''\
[](http://aaaa.com)
![](http://aaaa.com)
[](page)
[[Page]]
[[#edit]]
'''
        expected = '''\
<p><a href="http://aaaa.com">http://aaaa.com</a></p>
<p><img src="http://aaaa.com"/></p>
<p><a href="page">page</a></p>
<p><a href="page.html">Page</a></p>
<p><a href="#edit"></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_video_embed_mp4(self):
        md_text = '''![](cool.mp4)'''
        expected = '''<p><video controls="yesplz" disablePictureInPicture="True" playsinline="True" src="images/cool.mp4" type="video/mp4"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_video_embed_youtube(self):
        md_text = '''![](https://www.youtube.com/watch?v=iNiImDNtLpQ)'''
        expected = '''<p><object class="yt-embed" data="https://www.youtube.com/embed/iNiImDNtLpQ"></object></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestTablesHTML(unittest.TestCase):
    def test_table_with_empty_cells(self):
        md_text = '''\
|aa|bb|
|--|--|
|asd||
'''
        expected = '''\
<table>
<thead>
<tr><th>aa</th><th>bb</th></tr>
</thead>
<tbody>
<tr><td>asd</td><td></td></tr>
</tbody></table>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_table_with_headers(self):
        md_text = '''\
First Header  | Second Header
------------- | -------------
Content Cell  | Content Cell
Content Cell  | Content Cell
'''
        expected = '''\
<table>
<thead>
<tr><th>First Header</th><th>Second Header</th></tr>
</thead>
<tbody>
<tr><td>Content Cell</td><td>Content Cell</td></tr>
<tr><td>Content Cell</td><td>Content Cell</td></tr>
</tbody></table>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_table_with_alignment(self):
        md_text = '''\
First Header  | Second Header | Third Header
:------------ | ------------: | :----------:
Content Cell  | Content Cell  | Content Cell 
Content Cell  | Content Cell  | Content Cell 
'''
        expected = '''\
<table>
<thead>
<tr><th>First Header</th><th>Second Header</th><th>Third Header</th></tr>
</thead>
<tbody>
<tr><td align="left">Content Cell</td><td align="right">Content Cell</td><td align="center">Content Cell</td></tr>
<tr><td align="left">Content Cell</td><td align="right">Content Cell</td><td align="center">Content Cell</td></tr>
</tbody></table>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_table_with_inline_formatting(self):
        md_text = '''\
| First Header  | Second Header |
| :------------ | ------------: |
| **cell**      | Content Cell  |
| Content Cell  | Content Cell  |
'''
        expected = '''\
<table>
<thead>
<tr><th>First Header</th><th>Second Header</th></tr>
</thead>
<tbody>
<tr><td align="left"><strong>cell</strong></td><td align="right">Content Cell</td></tr>
<tr><td align="left">Content Cell</td><td align="right">Content Cell</td></tr>
</tbody></table>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_table_minimal_syntax(self):
        md_text = '''\
|aa|bb|
|--|--|
|asd||
'''
        expected = '''\
<table>
<thead>
<tr><th>aa</th><th>bb</th></tr>
</thead>
<tbody>
<tr><td>asd</td><td></td></tr>
</tbody></table>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestMiscInlineHTML(unittest.TestCase):
    def test_star_rating_no_parse(self):
        md_text = '''★★★★ / wombat wontparse'''
        expected = '''<p>★★★★ / wombat wontparse</p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestMiscBlocksHTML(unittest.TestCase):
    def test_blockquote_with_attribution(self):
        md_text = '''> "I have been using the AquaBoostAG liquefied polymer" -- Mystery Mountain Grove'''
        expected = '''<blockquote><p>"I have been using the AquaBoostAG liquefied polymer" — Mystery Mountain Grove</p></blockquote>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestCodeBlocksHTML(unittest.TestCase):
    def test_code_block_with_language_and_id(self):
        md_text = '''\
```lang=python,id=test
a
b
c
```
'''
        expected = '''\
<pre id="test"><code class="language-python">a
b
c</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_with_language(self):
        md_text = '''\
```python
a
b
c
```
'''
        expected = '''\
<pre><code class="language-python">a
b
c</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_with_id_only(self):
        md_text = '''\
```id=test
a
b
c
```
'''
        expected = '''\
<pre id="test"><code>a
b
c</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_plain(self):
        md_text = '''\
```
a
b
c
```
'''
        expected = '''\
<pre><code>a
b
c</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_tilde_fence(self):
        md_text = '''\
~~~~~~
asfadsf
~~~~~~
'''
        expected = '''<pre><code>asfadsf</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_code_block_with_class(self):
        md_text = '''\
```class=linenums
a
b
c
```
'''
        expected = '''\
<pre class="linenums"><code>a
b
c</code></pre>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestHeadingsHTML(unittest.TestCase):
    def test_heading_attributes_various_styles(self):
        md_text = '''\
test  {#test}
====

## hello ## {#hello}

### subject ### {#subject}
### subject {#subject}

[link to anchor](#anchor)
'''
        expected = '''\
<section id="section-test">
<h1 id="test">test<a class="anchor" href="#test"></a></h1>
</section>
<section id="section-hello">
<h2 id="hello">hello<a class="anchor" href="#hello"></a></h2>
</section>
<section id="section-subject">
<h3 id="subject">subject<a class="anchor" href="#subject"></a></h3>
</section>
<section id="section-subject">
<h3 id="subject">subject<a class="anchor" href="#subject"></a></h3>
<p><a href="#anchor">link to anchor</a></p>
</section>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_heading_attributes_id_and_class(self):
        md_text = '''\
## hello ## {#hello}
## hello ## {.hello}
## hello  {#hello}
## hello  {.hello}
## hello  {.hello #title .class}
'''
        expected = '''\
<section id="section-hello">
<h2 id="hello">hello<a class="anchor" href="#hello"></a></h2>
</section>
<section id="section-hello">
<h2 class="hello" id="title_0-3">hello<a class="anchor" href="#title_0-3"></a></h2>
</section>
<section id="section-hello">
<h2 id="hello">hello<a class="anchor" href="#hello"></a></h2>
</section>
<section id="section-hello">
<h2 class="hello" id="title_0-4">hello<a class="anchor" href="#title_0-4"></a></h2>
</section>
<section id="section-hello">
<h2 class="hello class" id="title">hello<a class="anchor" href="#title"></a></h2>
</section>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


    def test_table_of_contents(self):
        md_text = '''\
.. toc::
## First heading
Something here
## Second heading
'''
        expected = '''\
<section class="toc">
<ul>
<li><a href="#toc_1">First heading</a></li>
<li><a href="#toc_2">Second heading</a></li>
</ul>
</section>
<section id="section-first-heading">
<h2 id="title_0-1">First heading<a class="anchor" href="#title_0-1"></a></h2>
<p>Something here</p>
</section>
<section id="section-second-heading">
<h2 id="title_0-2">Second heading<a class="anchor" href="#title_0-2"></a></h2>
</section>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_atx_style_headings(self):
        md_text = '''\
# Heading 1
## Heading 2
### Heading 3
'''
        expected = '''\
<section id="section-heading-1">
<h1 id="title_2">Heading 1<a class="anchor" href="#title_2"></a></h1>
</section>
<section id="section-heading-2">
<h2 id="title_2-2">Heading 2<a class="anchor" href="#title_2-2"></a></h2>
</section>
<section id="section-heading-3">
<h3 id="title_2-2-2">Heading 3<a class="anchor" href="#title_2-2-2"></a></h3>
</section>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_setext_style_headings(self):
        md_text = '''\
Heading 1
=========

Heading 2
---------

### Heading 3
'''
        expected = '''\
<section id="section-heading-1">
<h1 id="title_2">Heading 1<a class="anchor" href="#title_2"></a></h1>
</section>
<section id="section-heading-2">
<h2 id="title_2-2">Heading 2<a class="anchor" href="#title_2-2"></a></h2>
</section>
<section id="section-heading-3">
<h3 id="title_2-2-2">Heading 3<a class="anchor" href="#title_2-2-2"></a></h3>
</section>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

if __name__ == '__main__':
    unittest.main()
