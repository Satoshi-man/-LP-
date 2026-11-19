"""Build redesign preview pages from the original LP HTML.

Only the KV block is replaced and a style block is added; questions, form
fields and scripts are copied as-is. Preview-only changes: <base> so the
original assets load, GTM removed, CSRF tokens blanked, form submission blocked.
"""
import re, sys, pathlib

SRC_DIR, OUT_DIR = pathlib.Path(sys.argv[1]), pathlib.Path(__file__).parent
HERE = OUT_DIR / 'src'
FONT = '<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap" rel="stylesheet">'
GUARD = """<script>/* PREVIEW ONLY: 送信を止める */
HTMLFormElement.prototype.submit = function () { alert('プレビューのため送信されません'); };
document.addEventListener('submit', function (e) { e.preventDefault(); alert('プレビューのため送信されません'); }, true);
</script>"""

for key in ['f01', 'f04']:
    html = (SRC_DIR / key / 'index.html').read_text(encoding='utf-8')
    kv_re = re.compile(r'[ \t]*<div class="kv-section">\s*<img[^>]*class="kv-img"[^>]*>\s*</div>\n', re.S)
    assert len(kv_re.findall(html)) == 1, key
    style = '<style>\n' + (HERE / f'{key}_theme.css').read_text() + (HERE / 'base.css').read_text() + '</style>'
    out = kv_re.sub(lambda m: (HERE / f'{key}_kv.html').read_text(), html)
    out = out.replace('</head>', f'  {FONT}\n  <!-- REDESIGN: style -->\n  {style}\n  </head>', 1)
    # preview-only
    out = re.sub(r'<!-- Google Tag Manager -->.*?<!-- End Google Tag Manager -->', '', out, flags=re.S)
    out = re.sub(r'<!-- Google Tag Manager \(noscript\) -->.*?<!-- End Google Tag Manager \(noscript\) -->', '', out, flags=re.S)
    out = re.sub(r'(name="csrf-token" content=")[^"]*', r'\1', out)
    out = re.sub(r'(name="authenticity_token" value=")[^"]*', r'\1', out)
    out = out.replace('<head>', '<head>\n    <base href="https://furinisharyo-madoguchi.com/">\n    ' + GUARD, 1)
    (OUT_DIR / f'{key}-preview.html').write_text(out, encoding='utf-8')

    # verify: everything from the first diagnosis block to </html> is unchanged
    def tail(s):
        s = re.sub(r'(name="authenticity_token" value=")[^"]*', r'\1', s)
        return s[s.index('<div class="diagnosis-section">'):]
    assert tail(html) == tail(out), f'{key}: questions/logic changed'
    print(key, 'ok: questions, fields and scripts unchanged')
