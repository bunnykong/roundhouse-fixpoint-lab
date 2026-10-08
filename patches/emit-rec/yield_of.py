#!/usr/bin/env python3
"""Print the template output inside real-blog's layout: the bytes between
'<main ...>\\n      ' and '\\n    </main>' (layout line 28 is '      <%= yield %>')."""
import sys
b = open(sys.argv[1], 'rb').read()
start = b.find(b'<main class="container mx-auto mt-28 px-5 flex flex-col">\n      ')
end = b.rfind(b'\n    </main>')
if start < 0 or end < 0:
    sys.exit("no layout yield region")
start += len(b'<main class="container mx-auto mt-28 px-5 flex flex-col">\n      ')
sys.stdout.buffer.write(b[start:end])
