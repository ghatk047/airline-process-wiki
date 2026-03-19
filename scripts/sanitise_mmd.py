#!/usr/bin/env python3
"""
sanitise_mmd.py — Clean Mermaid .mmd files before passing to mmdc.
Removes characters that cause Mermaid parse errors:
  - Apostrophes inside node labels
  - Unescaped quotes inside brackets/braces
  - Ampersands (replace with 'and')
  - Newlines inside node labels

Usage: python3 sanitise_mmd.py path/to/file.mmd
"""
import sys, re

path = sys.argv[1]
with open(path) as f:
    content = f.read()

original = content

def clean_label(text):
    text = text.replace("'", "")
    text = text.replace('"', "")
    text = text.replace('&', 'and')
    text = text.replace('\n', ' ')
    return text

# Clean square bracket labels [ ... ]
content = re.sub(
    r'\[([^\[\]]*)\]',
    lambda m: '[' + clean_label(m.group(1)) + ']',
    content
)

# Clean curly brace labels { ... } (decision diamonds)
content = re.sub(
    r'\{([^\{\}]*)\}',
    lambda m: '{' + clean_label(m.group(1)) + '}',
    content
)

# Clean round bracket labels ( ... ) (start/end ovals)
content = re.sub(
    r'\(([^\(\)]*)\)',
    lambda m: '(' + clean_label(m.group(1)) + ')',
    content
)

with open(path, 'w') as f:
    f.write(content)

if content != original:
    print(f"  Sanitised: {path}")
else:
    print(f"  Clean (no changes): {path}")
