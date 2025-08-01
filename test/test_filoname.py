from par.filoname import get_filename_parts

test_cases = {
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
    "1.Norms's Bio.md.txt": {'title': "Norms's Bio", 'sort': '1.', 'exts': 'md.txt'},
    '10.Windhoek 🇳🇦 🡒 Vic Falls (Fly).md.txt': {'title': 'Windhoek 🇳🇦 🡒 Vic Falls (Fly)', 'sort': '10.', 'exts': 'md.txt'},
    'Tomb_22 - $20,000.jpg': {'title': 'Tomb_22 - $20,000', 'exts': 'jpg'},
    '#menu,.content,#body,pre.ttf': {'title': '#menu,.content,#body,pre', 'exts': 'ttf'},
    ' Liz (Tu) Rite.card.yaml': {'title': 'Liz (Tu) Rite', 'exts': 'card.yaml'},
    '#body {background-size=cover}.svg': {'title': '#body', 'exts': 'svg', 'meta': {'background-size': 'cover'}},
    '91.Dr. Paul J. Garcia.jpg': {'title': 'Dr. Paul J. Garcia', 'sort': '91.', 'exts': 'jpg'},
    '_. Company [pages]/': {'title': 'Company', 'sort': '_.', 'group': 'pages'},
    '_. Last item {cool=false}.dj.html': {'title': 'Last item','sort': '_.', 'meta': {'cool': 'false'},'exts': 'dj.html'}
}

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

total_issues = 0
for filename, expected in test_cases.items():
    parts = get_filename_parts(filename)
    mismatches = []
    for attr, exp_val in expected.items():
        actual_val = getattr(parts, attr)
        if actual_val != exp_val:
            mismatches.append(f"{termfont.fg_orange}{attr:6}{termfont.endc}: got {termfont.fg_red}{actual_val!r}{termfont.endc}, expected {termfont.fg_green}{exp_val!r}{termfont.endc}")
    if mismatches:
        print(f'{termfont.ef_dim}Filename{termfont.endc}: "{termfont.ef_bold}{filename}{termfont.endc}"')
        for mismatch in mismatches:
            print(mismatch)
        print(f"{' '*10} {'-'*10} {' '*10}")
        total_issues = total_issues + len(mismatches)

print(f"{termfont.fg_blue}Total issues found: {total_issues}{termfont.endc}")