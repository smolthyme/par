from par.filoname import get_filename_parts

test_filenames = [
    '3. Large',
    '3. Large.jpg',
    '3.0 Large',
    '3.0 Large/',
    '3 Large/',
    '01. Small',
    '01. Small.jpg',
    '2000.01.01-HARRY_HASA_PARROT.jpg',
    'moved-to-archive',
    'Hats on Top of Heads.jpg'
]

for filename in test_filenames:
    parts = get_filename_parts(filename)
    print(f"Filename: {filename}")
    print(f"Title: {parts.title}")
    print(f"Sort Order: {parts.sort}")
    print(f"Tags: {parts.tags}")
    print(f"Group: {parts.group}")
    print(f"Meta: {parts.meta}")
    print(f"Extensions: {parts.exts}")
    print("-" * 40)