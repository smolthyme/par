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
<li>a
<ul>
<li>b</li>
<li>c</li>
</ul></li>
<li>d
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
<li>bupkis
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
<li>abc
<pre><code>code</code></pre></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_ordered_list_with_indented_code(self):
        md_text = '''\
1. abc

        code
        more code
'''
        expected = '''\
<ol>
<li>abc
<pre><code>code
more code</code></pre></li>
</ol>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_ordered_list_with_language_code_blocks(self):
        md_text = '''\
1. Python example:
    ```python
    def greet(name):
        print(f"Hello, {name}!")
    greet("World")
    ```

2. JavaScript example:
    ```javascript
    function add(a, b) {
        return a + b;
    }
    console.log(add(2, 3));
    ```

3. Bash example:
    ```bash
    echo "Hello from Bash!"
    ```
''';       expected = '''\
<ol>
<li>Python example:
<pre><code class="language-python">def greet(name):
    print(f"Hello, {name}!")
greet("World")</code></pre></li>
<li>JavaScript example:
<pre><code class="language-javascript">function add(a, b) {
    return a + b;
}
console.log(add(2, 3));</code></pre></li>
<li>Bash example:
<pre><code class="language-bash">echo "Hello from Bash!"</code></pre></li>
</ol>'''
        self.maxDiff = None
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
</dd>
<dd><pre><code>return {}</code></pre>
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
* [ ] a
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
<li><input type="checkbox" checked></input>b
<ul>
<li><input type="radio" checked></input>c</li>
<li><input type="radio"></input>d</li>
</ul></li>
<li><input type="checkbox"></input>a
<ul>
<li><input type="checkbox" checked></input>b</li>
<li><input type="radio" checked></input>c</li>
<li><input type="radio"></input>d</li>
</ul></li>
</ul>'''
        self.maxDiff = None
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

[^1]: Cats **aaaa**
'''
        expected = '''\
<p>That's some text with a footnote.<sup id="fnref-1"><a class="footnote-rel inner" href="#fn-1">1</a></sup></p>
<div class="footnotes"><ol>
<li id="fn-1">
<p>Cats <strong>aaaa</strong></p>

<a class="footnote-backref inner" href="#fnref-1">↩</a>
</li>
</ol></div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


    def test_image_as_link(self):
        md_text = '''\
[![Alt text](https://example.com/image.png)](https://example.com/target)
[![](https://example.com/image.png)](https://example.com/target)
'''
        expected = '''\
<p><a href="https://example.com/target"><img alt="Alt text" src="https://example.com/image.png">Alt text</img></a></p>
<p><a href="https://example.com/target"><img src="https://example.com/image.png"></a></p>'''
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


class TestImageAttributesHTML(unittest.TestCase):
    def test_inline_image_with_class(self):
        md_text = '''![Alt text](image.png){.hero}'''
        expected = '''<p><img alt="Alt text" class="hero" src="images/image.png"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_image_with_id(self):
        md_text = '''![Alt text](image.png){#my-id}'''
        expected = '''<p><img alt="Alt text" id="my-id" src="images/image.png"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_image_with_class_and_id(self):
        md_text = '''![Alt text](image.png){.my-class #my-id}'''
        expected = '''<p><img alt="Alt text" class="my-class" id="my-id" src="images/image.png"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_image_with_multiple_classes(self):
        md_text = '''![Alt text](image.png){.class1 .class2}'''
        expected = '''<p><img alt="Alt text" class="class1 class2" src="images/image.png"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_image_with_title_and_class(self):
        md_text = '''![Alt text](image.png "Image Title"){.styled}'''
        expected = '''<p><img alt="Alt text" class="styled" src="images/image.png" title="Image Title"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_reference_image_with_class(self):
        md_text = '''![Alt][ref]{.my-class}

[ref]: image.png
'''
        expected = '''<p><img alt="Alt" class="my-class" src="images/image.png"></img></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_reference_image_with_class_and_id(self):
        md_text = '''![Alt][ref]{.my-class #img-id}

[ref]: image.png "Ref Title"
'''
        expected = '''<p><img alt="Alt" class="my-class" id="img-id" src="images/image.png" title="Ref Title"></img></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_image_link_with_class(self):
        md_text = '''[![Alt](image.png)](https://example.com){.clickable}'''
        expected = '''<p><a class="clickable" href="https://example.com"><img alt="Alt" src="images/image.png">Alt</img></a></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_image_link_with_class_and_id(self):
        md_text = '''[![Alt](image.png)](https://example.com){.clickable #hero-img}'''
        expected = '''<p><a class="clickable" href="https://example.com" id="hero-img"><img alt="Alt" src="images/image.png">Alt</img></a></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_video_with_class(self):
        md_text = '''![](video.mp4){.video-player}'''
        expected = '''<p><video class="video-player" controls="yesplz" disablePictureInPicture="True" playsinline="True" src="images/video.mp4" type="video/mp4"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_audio_with_class(self):
        md_text = '''![](audio.mp3){.audio-player #main-audio}'''
        expected = '''<p><audio class="audio-player" controls="yesplz" id="main-audio" src="images/audio.mp3" type="audio/mpeg"/></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_youtube_with_class(self):
        md_text = '''![](https://www.youtube.com/watch?v=iNiImDNtLpQ){.yt-player}'''
        expected = '''<p><object class="yt-embed yt-player" data="https://www.youtube.com/embed/iNiImDNtLpQ"></object></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestSideBySideBlocksHTML(unittest.TestCase):
    def test_sidebyside_blocks(self):
        md_text = '''\
|||
Content for the first block.
Second block
Third one
'''
        expected = '''<div class="collection-horiz">
<p>Content for the first block.</p>
<p>Second block</p>
<p>Third one</p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_sidebyside_double_with_adv_imgs(self):
        md_text = '''\
# Our Jam
        
|||
![Exhibitions](exhibition-stand-icon.svg){.icon-lg} Exhibitions
![Tradeshows](partner-handshake-icon.svg){.icon-lg} Tradeshows
![Stand Builds](toolbox-build.svg){.icon-lg} Stand Builds

|||
![Warehousing](warehouse-icon.svg){.icon-lg} Warehousing
![Logistics](delivery-truck-icon.svg){.icon-lg} Logistics
![Site Visits](binoculars-icon.svg){.icon-lg} Site Visits

## Why we're the best

Good stuff all round! Test examples rock!
'''
        expected = '''
<section id="section-our-jam">
<h1 id="title_2">Our Jam<a class="anchor" href="#title_2"></a></h1>
<div class="collection-horiz">
<p><img alt="Exhibitions" class="icon-lg" src="images/exhibition-stand-icon.svg"/> Exhibitions</p>
<p><img alt="Tradeshows" class="icon-lg" src="images/partner-handshake-icon.svg"/> Tradeshows</p>
<p><img alt="Stand Builds" class="icon-lg" src="images/toolbox-build.svg"/> Stand Builds</p>
</div>
<div class="collection-horiz">
<p><img alt="Warehousing" class="icon-lg" src="images/warehouse-icon.svg"/> Warehousing</p>
<p><img alt="Logistics" class="icon-lg" src="images/delivery-truck-icon.svg"/> Logistics</p>
<p><img alt="Site Visits" class="icon-lg" src="images/binoculars-icon.svg"/> Site Visits</p>
</div>
</section>
<section id="section-why-we-re-the-best">
<h2 id="title_2-2">Why we're the best<a class="anchor" href="#title_2-2"></a></h2>
<p>Good stuff all round! Test examples rock!</p>
</section>'''
        self.maxDiff = None
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


    def test_sidebyside_with_class_and_formatting(self):
        md_text = '''\
||| {.custom-class}
**Bold text** in first block.
![Cool background](http://example.com/image.png){.cool-pix}
'''
        expected = '''<div class="collection-horiz custom-class">
<p><strong>Bold text</strong> in first block.</p>
<p><img alt="Cool background" class="cool-pix" src="http://example.com/image.png"/></p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_sidebyside_without_class_but_with_classed_blocks(self):
        md_text = '''\
|||
![A Picture with Class](http://example.com/pic.jpg){.fancy-pic}
![Another Picture with Class](http://example.com/pic.jpg){.fancy-pic}
'''
        expected = '''<div class="collection-horiz">
<p><img alt="A Picture with Class" class="fancy-pic" src="http://example.com/pic.jpg"/></p>
<p><img alt="Another Picture with Class" class="fancy-pic" src="http://example.com/pic.jpg"/></p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

class TestCardsHTML(unittest.TestCase):
    def test_inline_card_simple(self):
        md_text = '''[|A simple card with just text|]'''
        expected = '''<div class="card">
<p>A simple card with just text</p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_card_with_formatting(self):
        md_text = '''[|### Card Header|]'''
        expected = '''<div class="card">
<section id="section-card-header">
<h3 id="title_1">Card Header<a class="anchor" href="#title_1"></a></h3>
</section>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_inline_card_with_link(self):
        md_text = '''[|Check out [this link](https://example.com)|]'''
        expected = '''<div class="card">
<p>Check out <a href="https://example.com">this link</a></p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_multiline_card(self):
        md_text = '''\
[|
## Card Title
Some paragraph text here.
|]
'''
        expected = '''<div class="card">
<section id="section-card-title">
<h2 id="title_1">Card Title<a class="anchor" href="#title_1"></a></h2>
<p>Some paragraph text here.</p>
</section>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_card_with_list(self):
        md_text = '''\
[|
* Item one
* Item two
* Item three
|]
'''
        expected = '''<div class="card">
<ul>
<li>Item one</li>
<li>Item two</li>
<li>Item three</li>
</ul>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_card_with_class(self):
        md_text = '''[|Styled card content|]{.highlight}'''
        expected = '''<div class="card highlight">
<p>Styled card content</p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_card_with_id_and_class(self):
        md_text = '''[|Card with attrs|]{#my-card .special}'''
        expected = '''<div class="card special" id="my-card">
<p>Card with attrs</p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_two_cards_sequential(self):
        md_text = '''\
[|First card|]
[|Second card|]
'''
        expected = '''<div class="card">
<p>First card</p>
</div>

<div class="card">
<p>Second card</p>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_cards_in_sidebyside(self):
        md_text = '''\
|||
[|
## Card One
First card content
|]

|||
[|
## Card Two
Second card content
|]
'''
        expected = '''<div class="collection-horiz">
<div class="card">
<section id="section-card-one">
<h2 id="title_1">Card One<a class="anchor" href="#title_1"></a></h2>
<p>First card content</p>
</section>
</div>
</div>
<div class="collection-horiz">
<div class="card">
<section id="section-card-two">
<h2 id="title_1">Card Two<a class="anchor" href="#title_1"></a></h2>
<p>Second card content</p>
</section>
</div>
</div>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_card_with_image_link(self):
        md_text = '''[|[![Logo](logo.png)](https://example.com)|]'''
        expected = '''<div class="card">
<p><a href="https://example.com"><img alt="Logo" src="images/logo.png">Logo</img></a></p>
</div>'''
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
<li><a href="#title_0-1">First heading</a></li>
<li><a href="#title_0-2">Second heading</a></li>
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

    def test_emdash_in_headings(self):
        md_text = '''\
# Title -- Subtitle
## Another -- Example
'''
        result = parseHtml(md_text).strip()
        self.assertIn('Title — Subtitle', result)
        self.assertIn('Another — Example', result)

class TestButtonsHTML(unittest.TestCase):
    def test_button_as_link(self):
        md_text = "((Go to Example.com|>https://example.com))"
        expected = '<p><form action="https://example.com" method="get"><button type="submit">Go to Example.com</button></form></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_open_new_tab(self):
        md_text = "((Go to Example.com in new tab|>> https://example.com))"
        expected = '<p><form action="https://example.com" method="get" target="_blank"><button type="submit">Go to Example.com in new tab</button></form></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_submit_form_post(self):
        md_text = "((Submit|/submit-this-form-yo))"
        expected = '<p><form action="/submit-this-form-yo" method="post"><button type="submit">Submit</button></form></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_form_attr_button(self):
        md_text = "((Submit|/form-name))"
        expected = '<p><button type="submit" form="form-name">Submit</button></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_js_onclick(self):
        md_text = "((Click Me|$ alert('Button clicked!')))"
        expected = "<p><button type=\"button\" onclick=\"alert('Button clicked!')\">Click Me</button></p>"
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_styled_button_class_on_form(self):
        md_text = "((Styled Button|> https://example.com)){.cssstyle}"
        expected = '<p><form action="https://example.com" method="get" class="cssstyle"><button type="submit">Styled Button</button></form></p>'
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestFormsHTML(unittest.TestCase):
    """Test form block syntax: [&> url ...], [=> url ...], [*= expr ...]"""
    
    def test_form_post_simple(self):
        """[&> /action] creates a POST form"""
        md_text = '''\
[&> /contact-api
Get in contact with us!
]
'''
        expected = '''\
<form action="/contact-api" method="post">
<p>Get in contact with us!</p>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_form_get_simple(self):
        """[=> /action] creates a GET form"""
        md_text = '''\
[=>/search
Search the site
]
'''
        expected = '''\
<form action="/search" method="get">
<p>Search the site</p>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_form_oninput(self):
        """[*= expression ...] creates a form with oninput handler"""
        md_text = '''\
[*= result.value=a.value*2
Double your number
]
'''
        expected = '''\
<form oninput="result.value=a.value*2">
<p>Double your number</p>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_form_with_id_and_class(self):
        """Form with {#id .class} attributes"""
        md_text = '''\
[&> /api
Content here
]{#my-form .styled}
'''
        expected = '''\
<form action="/api" class="styled" id="my-form" method="post">
<p>Content here</p>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_form_post_full_url(self):
        """POST form with full URL"""
        md_text = '''\
[&>https://cool.com/send
Submit data
]
'''
        expected = '''\
<form action="https://cool.com/send" method="post">
<p>Submit data</p>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestInputsHTML(unittest.TestCase):
    """Test input syntax: [Label: >type___*]"""
    
    def test_text_input_required(self):
        """[Name: >___*] creates required text input"""
        md_text = '''[Name: >___*]'''
        expected = '''<p><label>Name: <input name="name" required type="text"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_text_input_optional(self):
        """[Name: >___] creates optional text input"""
        md_text = '''[Name: >___]'''
        expected = '''<p><label>Name: <input name="name" type="text"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_email_input(self):
        """[Email >@___*] creates email input"""
        md_text = '''[Email >@___*]'''
        expected = '''<p><label>Email <input name="email" required type="email"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_tel_input(self):
        """[Phone: >tel___*] creates telephone input"""
        md_text = '''[Phone: >tel___*]'''
        expected = '''<p><label>Phone: <input name="phone" required type="tel"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_number_input(self):
        """[Amount >#___] creates number input"""
        md_text = '''[Amount >#___]'''
        expected = '''<p><label>Amount <input name="amount" type="number"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_file_input(self):
        """[Photo: >!___*] creates file input for images"""
        md_text = '''[Photo: >!___*]'''
        expected = '''<p><label>Photo: <input accept="image/*" name="photo" required type="file"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_file_input_multiple(self):
        """[Photos: >!+___*] creates multiple file input"""
        md_text = '''[Photos: >!+___*]'''
        expected = '''<p><label>Photos: <input accept="image/*" multiple name="photos" required type="file"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_checkbox_input(self):
        """[Urgent? >[]] creates checkbox"""
        md_text = '''[Urgent? >[]]'''
        expected = '''<p><label>Urgent? <input name="urgent" type="checkbox"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_checkbox_checked(self):
        """[Active >[x]] creates checked checkbox"""
        md_text = '''[Active >[x]]'''
        expected = '''<p><label>Active <input checked name="active" type="checkbox"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_textarea(self):
        """[Message: > ______*] creates textarea (6+ underscores)"""
        md_text = '''[Message: > ______*]'''
        expected = '''<p><label>Message: <textarea name="message" required></textarea></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_output_element(self):
        """[Result <___] creates output element"""
        md_text = '''[Result <___]'''
        expected = '''<p><label>Result <output name="result"></output></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_input_with_attributes(self):
        """Input with {name=x type=y} attributes"""
        md_text = '''[Milliliters (ml) >#___]{name=ml type=number min=0 step=any value=100}'''
        expected = '''<p><label>Milliliters (ml) <input min="0" name="ml" step="any" type="number" value="100"/></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_output_with_attributes(self):
        """Output with {name=x .class} attributes"""
        md_text = '''[Ounces (oz) <___]{name=oz .stylish}'''
        expected = '''<p><label>Ounces (oz) <output class="stylish" name="oz"></output></label></p>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


class TestFormsWithInputsHTML(unittest.TestCase):
    """Test forms containing inputs"""

    def test_contact_form(self):
        """Complete contact form example"""
        md_text = '''\
[&> /contact-api
Get in contact with us!
[Name: >___*]
[Phone: >tel___*]
[Urgent? >[]]
[Message: > ______*]
((Send)){type=submit}
]
'''
        expected = '''\
<form action="/contact-api" method="post">
<p>Get in contact with us!</p>
<label>Name: <input name="name" required type="text"/></label>
<label>Phone: <input name="phone" required type="tel"/></label>
<label>Urgent? <input name="urgent" type="checkbox"/></label>
<label>Message: <textarea name="message" required></textarea></label>
<button type="submit">Send</button>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_newsletter_form(self):
        """Newsletter signup form"""
        md_text = '''\
[=>/newslettersignup
[Email >@___*]]
'''
        expected = '''\
<form action="/newslettersignup" method="get">
<label>Email <input name="email" required type="email"/></label>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_converter_form(self):
        """Unit converter with oninput and output"""
        md_text = '''\
[*= oz.value=(+ml.value/29.5735).toFixed(2)
**Milliliter** to **Ounce** conversion
[Milliliters (ml) >#___]{name=ml type=number min=0 step=any value=100}
[Ounces (oz) <___]{name=oz .stylish}
]{#ml2oz .card}
'''
        expected = '''\
<form class="card" id="ml2oz" oninput="oz.value=(+ml.value/29.5735).toFixed(2)">
<p><strong>Milliliter</strong> to <strong>Ounce</strong> conversion</p>
<label>Milliliters (ml) <input min="0" name="ml" step="any" type="number" value="100"/></label>
<label>Ounces (oz) <output class="stylish" name="oz"></output></label>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())

    def test_image_upload_form(self):
        """Image upload form with multiple files"""
        md_text = '''\
[=>https://cool.com/send-a-shot
[Photo: >!+___*]
((Submit))
]
'''
        expected = '''\
<form action="https://cool.com/send-a-shot" method="get">
<label>Photo: <input accept="image/*" multiple name="photo" required type="file"/></label>
<button type="submit">Submit</button>
</form>'''
        self.assertEqual(parseHtml(md_text).strip(), expected.strip())


if __name__ == '__main__':
    unittest.main()
