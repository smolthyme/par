import unittest

from par.filoname import get_filename_parts

BASE_TEST_CASES = {
    '^. The first item {cool=yes}.html': {
        'title': 'The first item',
        'sort' : '^.',
        'meta' : {'cool': 'yes'},
        'exts' : 'html' },
    'Hats on Top of Heads.jpg':    {'title': 'Hats on Top of Heads', 'exts': 'jpg'},
    'moved-to-archive':            {'title': 'moved-to-archive', 'sort': None},
    '2000.01.01-HARRY_PARROT.jpg': {'title': 'HARRY_PARROT', 'exts': 'jpg'}, # Shows the date should be ignored 
    '01. Small':     {'title': 'Small', 'sort': '01.'},
    '01. Small.jpg': {'title': 'Small', 'sort': '01.'  , 'exts': 'jpg'},
    '3. Large.jpg':  {'title': 'Large', 'sort': '3.'   , 'exts': 'jpg'},
    '3.0 Large':     {'title': 'Large', 'sort': '3.0'},
    '3.0 Large/':    {'title': 'Large', 'sort': '3.0'},
    '3 Large/':      {'title': 'Large', 'sort': '3'},
    '3. Large':      {'title': 'Large', 'sort': '3.'},
    'small_wall #carousel.jpg': {'title': 'small_wall', 'tags': ['carousel'], 'exts': 'jpg'},
    '001.jpg': {'title': '001', 'exts': 'jpg', 'sort': None},
    '002. Bork.jpg': { 'sort': '002.', 'title': 'Bork', 'exts': 'jpg'},
    '17. Liz Of & Pho - CB.jpg': {'title': 'Liz Of & Pho - CB','sort': '17.', 'exts': 'jpg',},
    "1. Norms's Bio.md.txt": {'title': "Norms's Bio", 'sort': '1.', 'exts': 'md.txt'},
    '10. Windhoek 🇳🇦 🡒 Vic Falls (Fly).md.txt': {'title': 'Windhoek 🇳🇦 🡒 Vic Falls (Fly)', 'sort': '10.', 'exts': 'md.txt'},
    'Tomb_22 - $20,000.jpg': {'title': 'Tomb_22 - $20,000', 'exts': 'jpg'},
    '#menu,.content,#body,pre.ttf': {'title': '#menu,.content,#body,pre', 'exts': 'ttf'},
    ' Liz (Tu) Rite.card.yaml': {'title': 'Liz (Tu) Rite', 'exts': 'card.yaml'},
    '#body {background-size=cover}.svg': {'title': '#body', 'exts': 'svg', 'meta': {'background-size': 'cover'}},
    '91. Dr. Paul J. Garcia.jpg': {'title': 'Dr. Paul J. Garcia', 'sort': '91.', 'exts': 'jpg'},
    '_. Company [pages]/': {'title': 'Company', 'sort': '_.', 'group': 'pages'},
    '_. Last item {cool=false}.dj.html': {'title': 'Last item','sort': '_.', 'meta': {'cool': 'false'},'exts': 'dj.html'}
}


class FileNameParsingTests(unittest.TestCase):
    def test_existing_filename_examples(self):
        for filename, expected in BASE_TEST_CASES.items():
            with self.subTest(filename=filename):
                parts = get_filename_parts(filename)

                for attr, exp_val in expected.items():
                    self.assertEqual(getattr(parts, attr), exp_val)


class FileNameMetaParsingTests(unittest.TestCase):
    def test_meta_value_can_contain_dots(self):
        parts = get_filename_parts('Testi {hero=banner.jpg,hammer=one}.md.txt')

        self.assertEqual(parts.title, 'Testi')
        self.assertEqual(parts.meta, {'hero': 'banner.jpg', 'hammer': 'one'})
        self.assertEqual(parts.exts, 'md.txt')


class FileNameCssSelectorParsingTests(unittest.TestCase):
    def test_selector_style_titles_round_trip_cleanly(self):
        cases = {
            '.hero.svg': {'title': '.hero', 'exts': 'svg'},
            '.hero.banner.svg': {'title': '.hero.banner', 'exts': 'svg'},
            '.hero-banner.is-active.svg': {'title': '.hero-banner.is-active', 'exts': 'svg'},
            '#app.main-shell.svg': {'title': '#app.main-shell', 'exts': 'svg'},
            '.layout .hero-block.svg': {'title': '.layout .hero-block', 'exts': 'svg'},
            '.gallery+.caption.svg': {'title': '.gallery+.caption', 'exts': 'svg'},
            '.hero~.note-card.svg': {'title': '.hero~.note-card', 'exts': 'svg'},
            '.hero {display=flex}.svg': {'title': '.hero', 'meta': {'display': 'flex'}, 'exts': 'svg'},
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                parts = get_filename_parts(filename)

                self.assertEqual(parts.title, expected['title'])
                self.assertEqual(parts.exts, expected['exts'])
                self.assertEqual(parts.meta, expected.get('meta', {}))

    def test_hashtag_tags_still_parse_after_selector_expansion(self):
        parts = get_filename_parts('small_wall #carousel.jpg')

        self.assertEqual(parts.title, 'small_wall')
        self.assertEqual(parts.tags, ['carousel'])
        self.assertEqual(parts.exts, 'jpg')

    def test_ambiguous_bare_word_dotted_names_remain_conservative(self):
        parts = get_filename_parts('main.hero.svg')

        self.assertEqual(parts.title, 'main')
        self.assertEqual(parts.exts, 'hero.svg')
