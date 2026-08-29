"""Fix non-ASCII characters in Python scripts for Windows cp1252 compatibility."""
import pathlib
import re

files_to_fix = [
    "processing/exposure/build_habitation_baseline.py",
]

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

for rel_path in files_to_fix:
    fpath = PROJECT_ROOT / rel_path
    if not fpath.exists():
        print(f"SKIP (not found): {rel_path}")
        continue
    content = fpath.read_text(encoding="utf-8")
    # Replace known typographic characters with ASCII equivalents
    replacements = {
        "\u2014": "--",   # em dash
        "\u2013": "-",    # en dash
        "\u2192": "->",   # right arrow
        "\u2190": "<-",   # left arrow
        "\u2194": "<->",  # bidirectional arrow
        "\u2026": "...",  # ellipsis
        "\u2019": "'",    # right single quote
        "\u2018": "'",    # left single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2714": "[OK]", # checkmark
        "\u274c": "[X]",  # X mark
        "\u21d2": "=>",   # double right arrow
        "\u21d4": "<=>",  # double bidirectional arrow
        "\u2194": "<->",  # bidirectional arrow
        "\u2196": "<->",  # nw arrow
        "\u00e9": "e",    # e with accent
        "\u2192": "->",   # right arrow again
        "\u2194": "<->",
        "\u00ab": "<<",
        "\u00bb": ">>",
    }
    for char, replacement in replacements.items():
        content = content.replace(char, replacement)
    # Remove any remaining non-ASCII with ?
    content = re.sub(r'[^\x00-\x7F]', '?', content)
    fpath.write_text(content, encoding="utf-8")
    print(f"Fixed: {rel_path}")

print("Done.")
