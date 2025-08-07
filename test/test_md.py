import sys
sys.path.insert(0, '..')


# 'Legacy' features, some of which will be brought back
# from par.md import parseHtml
# from par.semantic_ext import blocks as semantic_blocks
# from par.bootstrap_ext import blocks as bootstrap_blocks

# def test_semantic_alert():
#     r"""
#     >>> text = '''
#     ... {% alert %}
#     ... This is a test.
#     ... {% endalert %}
#     ... '''
#     >>> print(parseHtml(text, '%(body)s', block_callback=semantic_blocks))
#     <BLANKLINE>
#     <div class="ui  message">
#     <p>This is a test.</p>
#     <BLANKLINE>
#     </div>
#     """

# def test_semantic_tabs():
#     r"""
#     >>> text = '''
#     ... {% tabs %}
#     ... -- name --
#     ... * a
#     ... * b
#     ... -- name --
#     ... 1. c
#     ... 1. d
#     ... {% endtabs %}
#     ... '''
#     >>> print(parseHtml(text, '%(body)s', block_callback=semantic_blocks))
#     <BLANKLINE>
#     <div class="ui tabular filter menu">
#     <a class=" class="active"item" data-tab="tab_item_1_1">name</a>
#     <a class="item" data-tab="tab_item_1_2">name</a>
#     </div>
#     <div class="tab-content">
#     <div class="ui divided inbox selection list active tab" data-tab="tab_item_1_1">
#     <BLANKLINE>
#     <ul>
#     <li>a</li>
#     <li>b</li>
#     </ul>
#     <BLANKLINE>
#     </div>
#     <div class="ui divided inbox selection list tab" data-tab="tab_item_1_2">
#     <BLANKLINE>
#     <ol>
#     <li>c</li>
#     <li>d</li>
#     </ol>
#     <BLANKLINE>
#     </div>
#     </div>
#     </div>
#     """

# def test_block_1():
#     r"""
#     >>> text = '''
#     ... {% tabs %}
#     ... -- index.html --
#     ... ```    
#     ... This is hello
#     ... ```
#     ... -- hello.html --
#     ... ```
#     ... This is hello
#     ... ```
#     ... {% endtabs %}
#     ... '''
#     >>> from par.bootstrap_ext import blocks
#     >>> print(parseHtml(text, '%(body)s', block_callback=blocks))
#     <BLANKLINE>
#     <div class="tabbable">
#     <ul class="nav nav-tabs">
#     <li class="active"><a href="#tab_item_1_1" data-toggle="tab">index.html</a></li>
#     <li><a href="#tab_item_1_2" data-toggle="tab">hello.html</a></li>
#     </ul>
#     <div class="tab-content">
#     <div class="tab-pane active" id="tab_item_1_1">
#     <BLANKLINE>
#     <pre><code>This is hello</code></pre>
#     <BLANKLINE>
#     </div>
#     <div class="tab-pane" id="tab_item_1_2">
#     <BLANKLINE>
#     <pre><code>This is hello</code></pre>
#     <BLANKLINE>
#     </div>
#     </div>
#     </div>
#     """
    
# def test_block_2():
#     r"""
#     >>> text = '''
#     ... {%alert class=info, close%}
#     ...     This is an alert.
#     ... {%endalert%}'''
#     >>> from par.bootstrap_ext import blocks
#     >>> print(parseHtml(text, '%(body)s', block_callback=blocks))
#     <BLANKLINE>
#     <div class="alert alert-info">
#     <button class="close" data-dismiss="alert">&times;</button>
#     <p>This is an alert.</p>
#     <BLANKLINE>
#     </div>
#     """

# def test_block_1():
#     r"""
#     >>> text = '''
#     ... {% tabs %}
#     ... -- index.html --
#     ... ```    
#     ... This is hello
#     ... ```
#     ... -- hello.html --
#     ... ```
#     ... This is hello
#     ... ```
#     ... {% endtabs %}
#     ... '''
#     >>> from par.bootstrap_ext import blocks
#     >>> print (parseHtml(text, '%(body)s', block_callback=blocks))
#     <BLANKLINE>
#     <div class="tabbable">
#     <ul class="nav nav-tabs">
#     <li class="active"><a href="#tab_item_1_1" data-toggle="tab">index.html</a></li>
#     <li><a href="#tab_item_1_2" data-toggle="tab">hello.html</a></li>
#     </ul>
#     <div class="tab-content">
#     <div class="tab-pane active" id="tab_item_1_1">
#     <BLANKLINE>
#     <pre><code>This is hello</code></pre>
#     <BLANKLINE>
#     </div>
#     <div class="tab-pane" id="tab_item_1_2">
#     <BLANKLINE>
#     <pre><code>This is hello</code></pre>
#     <BLANKLINE>
#     </div>
#     </div>
#     </div>
#     """
    
# def test_block_2():
#     r"""
#     >>> text = '''
#     ... {%alert class=info, close%}
#     ...     This is an alert.
#     ... {%endalert%}'''
#     >>> from par.bootstrap_ext import blocks
#     >>> print (parseHtml(text, '%(body)s', block_callback=blocks))
#     <BLANKLINE>
#     <div class="alert alert-info">
#     <button class="close" data-dismiss="alert">&times;</button>
#     <p>This is an alert.</p>
#     <BLANKLINE>
#     """

from par.md import parseHtml

def test_symbol():
    r"""
    >>> text = '''
    ... This is **a** symbol **test**.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <strong>a</strong> symbol <strong>test</strong>.</p>
    <BLANKLINE>
    """

def test_list_1():
    r"""
    >>> text = '''
    ... * a
    ... * b
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li>a</li>
    <li>b</li>
    </ul>
    <BLANKLINE>
    """
    
def test_list_2():
    r"""
    >>> text = '''
    ... 1. a
    ... 2. b
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li>a</li>
    <li>b</li>
    </ol>
    <BLANKLINE>
    
    """
    
def test_list_3():
    r"""
    >>> text = '''
    ... * a
    ... * b
    ... 
    ... * c
    ... * d
    ... 
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li>a</li>
    <li>b</li>
    <li>c</li>
    <li>d</li>
    </ul>
    <BLANKLINE>
    """
    
def test_list_4():
    r"""
    >>> text = '''
    ... * a
    ...     * b
    ...     * c
    ... * d
    ...     * e
    ... 
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    </ul>
    <BLANKLINE>
    """

def test_dl_1():
    r"""
    >>> text = '''
    ... a --
    ...     abc
    ...
    ... b --
    ...     cde
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>a</dt>
    <dd><p>abc</p>
    </dd>
    <dt>b</dt>
    <dd><p>cde</p>
    </dd>
    </dl>
    """

def test_dl_2():
    r"""
    >>> text = '''
    ... a_ --
    ...     abc
    ... 
    ... **b** --
    ...     * li
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>a_</dt>
    <dd><p>abc</p>
    </dd>
    <dt><strong>b</strong></dt>
    <dd><ul>
    <li>li</li>
    </ul>
    </dd>
    </dl>
    """

def test_dl_3():
    r"""
    >>> text = '''
    ... a
    ... :   abc
    ... 
    ... **b**
    ... :   * li
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    """

def test_dl_4():
    r"""
    >>> text = '''
    ... a --
    ...     abc
    ...
    ...     ```
    ...     code
    ...     ```
    ... 
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>a</dt>
    <dd><p>abc</p>
    <pre><code>code</code></pre>
    </dd>
    </dl>
    """

def test_dl_5():
    r"""
    >>> text = '''
    ... a
    ... :   abc
    ...
    ...     ```
    ...     code
    ...     ```
    ... 
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>a</dt>
    <dd><p>abc</p>
    <pre><code>code</code></pre>
    </dd>
    </dl>
    """

def test_dl_6():
    r"""
    >>> text = '''
    ... 1. aaa
    ... 
    ...     defaults --
    ...         test:
    ...     
    ...         ```
    ...         return {}
    ...         ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li><p>aaa</p>
    <dl>
    <dt>defaults</dt>
    <dd><p>test:</p>
    <pre><code>return {}</code></pre>
    </dd>
    </dl></li>
    </ol>
    <BLANKLINE>
    """

def test_dl_7():
    r"""
    >>> text = '''
    ... a --
    ...     abc
    ...
    ...     ```
    ...     code
    ...        abcd
    ...     ```
    ...
    ...     test
    ...
    ... b --c --
    ...     abc
    ...
    ...     ```
    ...     code
    ...        abcd
    ...     ```
    ...
    ...     test
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>a</dt>
    <dd><p>abc</p>
    <pre><code>code
       abcd</code></pre>
    <p>test</p>
    </dd>
    <dt>b --c</dt>
    <dd><p>abc</p>
    <pre><code>code
       abcd</code></pre>
    <p>test</p>
    </dd>
    </dl>
    """

def test_deflist_1():
    r"""
    >>> text = '''
    ... Term
    ... : Definition
    ... 
    ... Another Term
    ... : Its definition
    ... : Can have multiple definitions
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <dl>
    <dt>Term</dt>
    <dd><p>Definition</p>
    </dd>
    <dt>Another Term</dt>
    <dd><p>Its definition</p>
    </dd>
    <dd><p>Can have multiple definitions</p>
    </dd>
    </dl>
    <BLANKLINE>
    """


def test_hr():
    r"""
    >>> text = '''
    ... * * * *
    ... ----
    ... __ __ __
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <hr/>
    <hr/>
    <hr/>
    <BLANKLINE>
    """

def test_url_1():
    r"""
    >>> text = '''
    ... This is [Test][foo] .
    ... 
    ... [foo]: http://example.com/  "Optional Title Here"
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>
    <BLANKLINE>
    """

def test_url_2():
    r"""
    >>> text = '''
    ... This is [Test][foo] .
    ... 
    ... [foo]: http://example.com/  'Optional Title Here'
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>
    <BLANKLINE>
    """

def test_url_3():
    r"""
    >>> text = '''
    ... This is [Test][foo] .
    ... 
    ... [foo]: http://example.com/  (Optional Title Here)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <a href="http://example.com/" title="Optional Title Here">Test</a> .</p>
    <BLANKLINE>
    """

def test_url_4():
    r"""
    >>> text = '''
    ... This is [foo][] .
    ... 
    ... [foo]: http://example.com/  (Optional Title Here)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <a href="http://example.com/" title="Optional Title Here">foo</a> .</p>
    <BLANKLINE>
    """

def test_table():
    r"""
    >>> text = '''
    ... || a || b || c ||
    ... || b || c || d ||
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <table>
    <tr><td>a</td><td>b</td><td>c</td>
    </tr>
    <tr><td>b</td><td>c</td><td>d</td>
    </tr>
    </table>
    <BLANKLINE>
    """

def test_table_0():
    r"""
    >>> text = '''
    ... |aa|bb|                                                                                      
    ... |--|--|                                                                                      
    ... |asd||
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <table>
    <thead>
    <tr><th>aa</th><th>bb</th><th></th></tr>
    </thead>
    <tbody>
    <tr><td>asd</td><td></td></tr>
    </tbody></table>
    <BLANKLINE>
    """

def test_star_rating_invalid():
    r"""
    >>> text = '''
    ... ★★★★ / wombat wontparse
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>★★★★ / wombat wontparse</p>
    <BLANKLINE>
    """

def list_nest_1():
    r"""
    >>> text = '''
    ... *   Abacus
    ...     * answer
    ... *   Bubbles
    ...     1.  bunk
    ...     2.  bupkis
    ...         * BELITTLER
    ...     3. burper
    ... *   Cunning
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ul>
    <li><p>Abacus</p>
    <ul>
    <li>answer</li>
    </ul></li>
    <li><p>Bubbles</p>
    <ol>
    <li>bunk</li>
    <li>bupkis</li>
    <ul>
    <li>BELITTLER</li>
    </ul></li>
    <li>burper</li>
    </ol></li>
    <li><p>Cunning</p></li>
    </ul>
    <BLANKLINE>
    """

def test_pre_1():
    r"""
    >>> text = '''
    ... ```lang=python,id=test
    ... a
    ... b
    ... c
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre id="test"><code class="language-python">a
    b
    c</code></pre>
    <BLANKLINE>
    """
    
def test_pre_2():
    r"""
    >>> text = '''
    ... ```python
    ... a
    ... b
    ... c
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre><code class="language-python">a
    b
    c</code></pre>
    <BLANKLINE>
    """

def test_pre_3():
    r"""
    >>> text = '''
    ... ```id=test
    ... a
    ... b
    ... c
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre id="test"><code>a
    b
    c</code></pre>
    <BLANKLINE>
    """

def test_pre_4():
    r"""
    >>> text = '''
    ... ```
    ... a
    ... b
    ... c
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre><code>a
    b
    c</code></pre>
    <BLANKLINE>
    """

def test_pre5():
    r"""
    >>> text = '''
    ... ~~~~~~
    ... asfadsf
    ... ~~~~~~
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre><code>asfadsf</code></pre>
    <BLANKLINE>
    """
    
def test_pre_6():
    r"""
    >>> text = '''
    ... ```class=linenums
    ... a
    ... b
    ... c
    ... ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <pre class="linenums"><code>a
    b
    c</code></pre>
    <BLANKLINE>
    """

def test_footnote():
    r"""
    >>> text = '''
    ... That's some text with a footnote.[^1]
    ... 
    ... [^1]: **aaaa**
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>That's some text with a footnote.<sup id="fnref-1"><a class="footnote-rel inner" href="#fn-1">1</a></sup></p>
    <div class="footnotes"><ol>
    <li id="fn-1">
    <p><strong>aaaa</strong></p>
    <BLANKLINE>
    <a class="footnote-backref inner" href="#fnref-1">↩</a>
    </li>
    </ol></div>
    """

def test_attr_1():
    r"""
    >>> text = '''
    ... test  {#test}
    ... ====
    ... 
    ... ## hello ## {#hello}
    ... 
    ... ### subject ### {#subject}
    ... ### subject {#subject}
    ... 
    ... [link to anchor](#anchor)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    </section>
    """

def test_bold():
    r"""
    >>> text = '''
    ... This is **bold** text.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <strong>bold</strong> text.</p>
    <BLANKLINE>
    """

def test_italic():
    r"""
    >>> text = '''
    ... This is *italic* text.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <em>italic</em> text.</p>
    <BLANKLINE>
    """

def test_bold_and_italic():
    r"""
    >>> text = '''
    ... This is ***bold and italic*** text.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <strong><em>bold and italic</em></strong> text.</p>
    <BLANKLINE>
    """

def test_inline_code():
    r"""
    >>> text = '''
    ... This is `inline code`.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <code>inline code</code>.</p>
    <BLANKLINE>
    """

def test_bold_and_code():
    r"""
    >>> text = '''
    ... This is **bold** and `code`.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <strong>bold</strong> and <code>code</code>.</p>
    <BLANKLINE>
    """

def test_combined_formatting():
    r"""
    >>> text = '''
    ... This is **bold**, *italic*, and `code` in one sentence.
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p>This is <strong>bold</strong>, <em>italic</em>, and <code>code</code> in one sentence.</p>
    <BLANKLINE>
    """

def test_attr_2():
    r"""
    >>> text = '''
    ... ## hello ## {#hello}
    ... ## hello ## {.hello}
    ... ## hello  {#hello}
    ... ## hello  {.hello}
    ... ## hello  {.hello #title .class}
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    </section>
    """

def test_link_1():
    r"""
    >>> text = '''
    ... [[Page|Hello world]]
    ... [[Page#title|Hello world]]
    ... [[wiki:Page|Hello world]]
    ... 
    ... [[image:a.png]]
    ... [[image:a.png|right]]
    ... [[image:a.png||250]]
    ... <Page>
    ... <http://localhost:8000>
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p><a href="Page.html">Hello world</a> <a href="Page.html#title">Hello world</a> <a href="Page.html">Hello world</a>
    </p>
    <p><img src="/images/a.png"/> <div class="floatright"><img src="/images/a.png"/></div> <img src="/images/a.png"  width="250px"/> <Page> <a href="http://localhost:8000">http://localhost:8000</a></p>
    <BLANKLINE>
    """
    
def test_link_2():
    r"""
    >>> text = '''
    ... [](http://aaaa.com)
    ... ![](http://aaaa.com)
    ... [](page)
    ... <http://aaaa.com>
    ... [[Page]]
    ... [[#edit]]
    ... [abc][cde]
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p><a href="http://aaaa.com">http://aaaa.com</a> <img src="http://aaaa.com"/>
     <a href="page">page</a> <a href="http://aaaa.com">http://aaaa.com</a> <a href="Page.html">Page</a>
     <a href="#edit">
     <a href="#">abc</a>
    </p>
    <BLANKLINE>
    """
    
def test_table_1():
    r"""
    >>> text = '''
    ... First Header  | Second Header
    ... ------------- | -------------
    ... Content Cell  | Content Cell
    ... Content Cell  | Content Cell
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <table>
    <thead>
    <tr><th>First Header</th><th>Second Header</th></tr>
    </thead>
    <tbody>
    <tr><td>Content Cell</td><td>Content Cell</td></tr>
    <tr><td>Content Cell</td><td>Content Cell</td></tr>
    </tbody></table>
    <BLANKLINE>
    """

def test_table_2():
    r"""
    >>> text = '''
    ... First Header  | Second Header | Third Header
    ... :------------ | ------------: | :----------:
    ... Content Cell  | Content Cell  | Content Cell 
    ... Content Cell  | Content Cell  | Content Cell 
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <table>
    <thead>
    <tr><th>First Header</th><th>Second Header</th><th>Third Header</th></tr>
    </thead>
    <tbody>
    <tr><td align="left">Content Cell</td><td align="right">Content Cell</td><td align="center">Content Cell</td></tr>
    <tr><td align="left">Content Cell</td><td align="right">Content Cell</td><td align="center">Content Cell</td></tr>
    </tbody></table>
    <BLANKLINE>
    """

def test_table_3():
    r"""
    >>> text = '''
    ... | First Header  | Second Header |
    ... | :------------ | ------------: |
    ... | **cell**      | Content Cell  |
    ... | Content Cell  | Content Cell  |
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <table>
    <thead>
    <tr><th>First Header</th><th>Second Header</th></tr>
    </thead>
    <tbody>
    <tr><td align="left"><strong>cell</strong></td><td align="right">Content Cell</td></tr>
    <tr><td align="left">Content Cell</td><td align="right">Content Cell</td></tr>
    </tbody></table>
    <BLANKLINE>
    """

def test_table_4():
    r"""
    >>> text = '''
    ... |aa|bb|
    ... |--|--|
    ... |asd||
    ... '''
    >>> print(parseHtml(text, '%(body)s', tag_class={'table':'table'}))
    <BLANKLINE>
    <table>
    <thead>
    <tr><th>aa</th><th>bb</th></tr>
    </thead>
    <tbody>
    <tr><td>asd</td><td></td></tr>
    </tbody></table>
    <BLANKLINE>
    """

def test_list_pre():
    r"""
    >>> text = '''
    ... 1. abc
    ... 
    ...     ```
    ...     code
    ...     ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li><p>abc</p>
    <pre><code>code</code></pre></li>
    </ol>
    <BLANKLINE>
    """
    
def test_list_pre_1():
    r"""
    >>> text = '''
    ... 1. abc
    ... 
    ...         code
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li><p>abc</p>
    <pre><code>code</code></pre></li>
    </ol>
    <BLANKLINE>
    """
    
def test_list_pre_2():
    r"""
    >>> text = '''
    ... 1. abc
    ... 
    ...     cde
    ... 
    ...     ```
    ...     code
    ...     ```
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <ol>
    <li><p>abc</p>
    <p>cde</p>
    <pre><code>code</code></pre></li>
    </ol>
    <BLANKLINE>
    """


def test_list_check_radio():
    r"""
    >>> text = '''
    ... * [] a
    ...    * [*] b
    ...     * <*> c
    ...     * < > d
    ... * [] a
    ...     * [*] b
    ...     * <*> c
    ...     * < > d
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    </ul>
    <BLANKLINE>
    """

def test_toc():
    r"""
    >>> text = '''
    ... .. toc::
    ... ## First heading
    ... Something here
    ... ## Second heading
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
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
    </section>
    """

def test_video_direct():
    r"""
    >>> text = '''
    ... ![](cool.mp4)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p><video controls="yesplz" disablePictureInPicture="True" playsinline="True" src="images/cool.mp4" type="video/mp4"/></p>
    <BLANKLINE>
    """

def test_video_youtube():
    r"""
    >>> text = '''
    ... ![](https://www.youtube.com/watch?v=iNiImDNtLpQ)
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <p><object class="yt-embed" data="https://www.youtube.com/embed/iNiImDNtLpQ"></object></p>
    <BLANKLINE>
    """

def test_blockquote():
    r"""
    >>> text = '''
    ... > "I have been using the AquaBoostAG liquefied polymer" -- Mystery Mountain Grove
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <blockquote><p>"I have been using the AquaBoostAG liquefied polymer" — Mystery Mountain Grove</p>
    </blockquote>
    <BLANKLINE>
    """

def test_heading_1():
    r"""
    >>> text = '''
    ... # Heading 1
    ... ## Heading 2
    ... ### Heading 3
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <section id="section-heading-1">
    <h1 id="title_2">Heading 1<a class="anchor" href="#title_2"></a></h1>
    </section>
    <section id="section-heading-2">
    <h2 id="title_2-2">Heading 2<a class="anchor" href="#title_2-2"></a></h2>
    </section>
    <section id="section-heading-3">
    <h3 id="title_2-2-2">Heading 3<a class="anchor" href="#title_2-2-2"></a></h3>
    </section>
    """

def test_heading_2():
    r"""
    >>> text = '''
    ... Heading 1
    ... =========
    ... 
    ... Heading 2
    ... ---------
    ... 
    ... ### Heading 3
    ... '''
    >>> print(parseHtml(text, '%(body)s'))
    <BLANKLINE>
    <section id="section-heading-1">
    <h1 id="title_2">Heading 1<a class="anchor" href="#title_2"></a></h1>
    </section>
    <section id="section-heading-2">
    <h2 id="title_2-2">Heading 2<a class="anchor" href="#title_2-2"></a></h2>
    </section>
    <section id="section-heading-3">
    <h3 id="title_2-2-2">Heading 3<a class="anchor" href="#title_2-2-2"></a></h3>
    </section>
    """

# Cant test easily as it's dynamic... for some odd reason.
# def test_raw_email1():
#     r"""
#     >>> text = '''gorble_clok@spam.com'''
#     >>> print(parseHtml(text, '%(body)s'))
#     <p><a href="&#x6D;ail&#x74;&#x6F;&#x3A;&#x67;orb&#x6C;e&#x5F;c&#x6C;&#x6F;k&#x40;spa&#x6D;.&#x63;o&#x6D;">&#x67;orb&#x6C;&#x65;_&#x63;&#x6C;&#x6F;k@&#x73;pa&#x6D;&#x2E;c&#x6F;m</a></p>
#     """


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

    Args:
        sample (str): Multi-line string for the sample.
        expected (str): Multi-line string for the expected output.
        result (str): Multi-line string for the actual result.
        term_width (int): Width of the terminal.
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

            print(f"Name: {test.name[9:]}")
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