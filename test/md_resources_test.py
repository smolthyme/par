import unittest

from par.md import parseHtmlDebug


class TestDebugResourcesBasics(unittest.TestCase):
    def test_empty_document_returns_plain_empty_resource_dict(self):
        html, resources = parseHtmlDebug("")

        self.assertEqual(html, "")
        self.assertIsInstance(resources, dict)
        self.assertEqual(
            resources,
            {
                "links_ext": [],
                "links_int": [],
                "images": [],
                "videos": [],
                "audios": [],
                "toc": [],
                "footnotes": [],
                "ids": {},
                "link_refs": {},
                "image_refs": {},
            },
        )

    def test_basic_links_and_images_are_tracked(self):
        html, resources = parseHtmlDebug(
            "Visit https://example.com ![logo](logo.png), and [[Home]]."
        )

        self.assertIn('<a href="https://example.com">', html)
        self.assertIn('<img alt="logo" src="images/logo.png"/>', html)
        self.assertEqual(resources["links_ext"], ["https://example.com"])
        self.assertEqual(resources["links_int"], ["home.html"])
        self.assertEqual(resources["images"], ["logo.png"])
        self.assertEqual(resources["videos"], [])
        self.assertEqual(resources["audios"], [])

    def test_media_and_reference_metadata_are_plain_dict_values(self):
        html, resources = parseHtmlDebug(
            "[Guide][docs] and ![Icon][asset]\n\n"
            '[docs]: https://example.com/docs "Docs"\n'
            "[asset]: icon.svg\n"
        )

        self.assertIn('title="Docs"', html)
        self.assertIn('src="images/icon.svg"', html)
        self.assertEqual(resources["links_ext"], ["https://example.com/docs"])
        self.assertEqual(resources["images"], ["icon.svg"])
        expected_refs = {
            "docs": {"url": "https://example.com/docs", "title": "Docs"},
            "asset": {"url": "icon.svg", "title": None},
        }
        self.assertEqual(resources["link_refs"], expected_refs)
        self.assertEqual(resources["image_refs"], expected_refs)


class TestDebugResourcesComplexDocuments(unittest.TestCase):
    def test_article_tracks_toc_references_media_and_footnotes(self):
        markdown = '''\\
.. toc::

# Launch guide

Read the [full guide][guide] or visit https://example.com/support.

![Product image](product.png)

## Video walkthrough

![](walkthrough.mp4) and ![](https://youtu.be/iNiImDNtLpQ)

The result is documented here.[^note]

[guide]: https://example.com/guide "Launch guide"
[^note]: The guide includes **setup** details.
'''
        html, resources = parseHtmlDebug(markdown)

        self.assertIn('<section class="toc">', html)
        self.assertIn('id="title_1"', html)
        self.assertIn('id="title_1-1"', html)
        self.assertIn('https://example.com/guide', html)
        self.assertIn('walkthrough.mp4', html)
        self.assertIn('fn-note', html)
        self.assertEqual(set(resources["links_ext"]), {
            "https://example.com/guide",
            "https://example.com/support.",
        })
        self.assertEqual(resources["links_int"], [])
        self.assertEqual(resources["images"], ["product.png"])
        self.assertEqual(resources["videos"], [
            "walkthrough.mp4",
            "https://youtu.be/iNiImDNtLpQ",
        ])
        self.assertEqual(resources["audios"], [])
        self.assertEqual(resources["toc"], [
            (1, "title_1", "Launch guide"),
            (2, "title_1-1", "Video walkthrough"),
        ])
        self.assertEqual(resources["footnotes"], [
            {"name": "note", "text": "<p>The guide includes <strong>setup</strong> details.</p>"}
        ])
        self.assertEqual(resources["link_refs"]["guide"], {
            "url": "https://example.com/guide",
            "title": "Launch guide",
        })

    def test_product_page_tracks_nested_card_and_mixed_media(self):
        markdown = '''\\
# Product overview

[|## Featured product

![Product](hero.jpg){.hero}

[[Product details|Read more]]
|]{#featured .highlight}

||| {.benefits}
Fast delivery with [tracking](https://example.com/track).

[[image:badge.svg|right]]

||| 
Audio preview: ![](preview.ogg)
'''
        html, resources = parseHtmlDebug(markdown)

        self.assertIn('<div class="card highlight" id="featured">', html)
        self.assertIn('<h2 id="title_1">Featured product', html)
        self.assertIn('href="product-details.html"', html)
        self.assertIn('class="collection-horiz benefits"', html)
        self.assertEqual(set(resources["links_ext"]), {"https://example.com/track"})
        self.assertEqual(resources["links_int"], ["product-details.html"])
        self.assertEqual(resources["images"], ["hero.jpg", "badge.svg"])
        self.assertEqual(resources["videos"], [])
        self.assertEqual(resources["audios"], ["preview.ogg"])
        self.assertEqual(resources["toc"], [(1, "title_1", "Product overview")])
        self.assertEqual(resources["ids"], {1: 2, 2: 1})

    def test_interactive_form_tracks_links_and_attachments_without_pollution(self):
        markdown = '''\\
## Contact support

[&> /api/contact
[Name: >___*]
[Email >@___*]
[Attachment: >!+___]
((Send|>https://example.com/thanks))
]

For urgent issues, see [status][status-page] or listen to ![](notice.mp3).

[status-page]: https://status.example.com "System status"
'''
        html, resources = parseHtmlDebug(markdown)

        self.assertIn('<form action="/api/contact" method="post">', html)
        self.assertIn('name="name" required', html)
        self.assertIn('name="email" required type="email"', html)
        self.assertIn('formaction="https://example.com/thanks"', html)
        self.assertIn('src="images/notice.mp3"', html)
        self.assertEqual(resources["links_ext"], ["https://status.example.com"])
        self.assertEqual(resources["links_int"], [])
        self.assertEqual(resources["images"], [])
        self.assertEqual(resources["videos"], [])
        self.assertEqual(resources["audios"], ["notice.mp3"])
        self.assertEqual(resources["toc"], [(2, "title_0-1", "Contact support")])
        self.assertEqual(resources["footnotes"], [])
        self.assertEqual(resources["link_refs"]["status-page"], {
            "url": "https://status.example.com",
            "title": "System status",
        })


if __name__ == "__main__":
    unittest.main()
