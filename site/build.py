#!/usr/bin/env python3
"""Build the self-contained lab pages that GitHub Pages serves.

One markdown source produces one page per variant (see VARIANTS). Each page
inlines marked.min.js and that variant's markdown into one file with no
runtime fetches. Edit the markdown, run this, commit every output.

Variant tags: untagged markdown goes into every variant. Wrap only the parts
that differ, with each marker on its own line (indenting is fine):

  <!-- variant:vm -->
  ...VM-only content...
  <!-- /variant -->
  <!-- variant:gsi,other -->
  ...content for several variants...
  <!-- /variant -->

Usage:
  python3 site/build.py           # build once
  python3 site/build.py --watch   # rebuild automatically whenever a source
                                   # file changes (Ctrl-C to stop)
"""

import re
import sys
import time
import pathlib

here = pathlib.Path(__file__).parent  # site/
root = here.parent  # gh-pages repo root

md_path = here / "Gemini World 3 QwikLab 2.0.md"
tpl_path = here / "index.html"
marked_path = here / "marked.min.js"

# Variant name -> output path. To add a variant, add a line here and tag the
# markdown where it differs.
VARIANTS = {
    "vm": root / "index.html",  # main page served by GitHub Pages
    "gsi": root / "gsi.html",  # the GSI team pulls this from the repo
}

# The files whose changes should trigger a rebuild in --watch mode.
SOURCES = [md_path, tpl_path, marked_path]

OPEN_RE = re.compile(r"^\s*<!--\s*variant:\s*([\w\s,-]+?)\s*-->\s*$")
CLOSE_RE = re.compile(r"^\s*<!--\s*/variant\s*-->\s*$")
ANY_MARKER_RE = re.compile(r"<!--\s*/?variant")


class BuildError(Exception):
    pass


def filter_variant(md, variant):
    """Return the markdown for one variant, with all variant markers removed."""
    out = []
    block = None  # variant names of the open block, or None outside a block
    open_line = 0
    for n, line in enumerate(md.splitlines(keepends=True), 1):
        where = f"{md_path.name}:{n}"
        m = OPEN_RE.match(line)
        if m:
            if block is not None:
                raise BuildError(
                    f"{where}: nested variant block (opened at line {open_line})"
                )
            block = {v.strip() for v in m.group(1).split(",") if v.strip()}
            unknown = block - VARIANTS.keys()
            if unknown:
                raise BuildError(
                    f"{where}: unknown variant {', '.join(sorted(unknown))} "
                    f"(known: {', '.join(VARIANTS)})"
                )
            open_line = n
        elif CLOSE_RE.match(line):
            if block is None:
                raise BuildError(f"{where}: <!-- /variant --> with no open block")
            block = None
        elif ANY_MARKER_RE.search(line):
            raise BuildError(
                f"{where}: malformed variant marker (must be on its own line)"
            )
        elif block is None or variant in block:
            out.append(line)
    if block is not None:
        raise BuildError(f"{md_path.name}:{open_line}: variant block never closed")
    return "".join(out)


def render(tpl, marked_js, md):
    """Inline marked.js and the markdown into the HTML template."""
    # Prevent the markdown from prematurely closing the inline <script> tag.
    md_safe = md.replace("</script>", "<\\/script>")

    # Inline marked.js (replace the external <script src>).
    assert '<script src="marked.min.js"></script>' in tpl, "marked script tag not found"
    html = tpl.replace(
        '<script src="marked.min.js"></script>',
        "<script>\n" + marked_js + "\n</script>",
    )

    # Inject the markdown into the inline placeholder.
    placeholder = '<script type="text/markdown" id="md-inline"></script>'
    assert placeholder in html, "md-inline placeholder not found"
    return html.replace(
        placeholder,
        '<script type="text/markdown" id="md-inline">\n' + md_safe + "\n</script>",
    )


def build():
    """Write every variant's page. Returns [(path, size), ...]."""
    tpl = tpl_path.read_text()
    marked_js = marked_path.read_text()
    md = md_path.read_text()

    # Filter every variant before writing anything, so a bad marker leaves
    # all outputs untouched.
    pages = {
        out: render(tpl, marked_js, filter_variant(md, name))
        for name, out in VARIANTS.items()
    }
    for out, html in pages.items():
        out.write_text(html)
    return [(out, len(html)) for out, html in pages.items()]


def report(results, prefix=""):
    for out, size in results:
        print(f"{prefix}Wrote {out.relative_to(root)} ({size:,} bytes)")


def watch(interval=0.5):
    """Rebuild whenever a source file's mtime changes. Ctrl-C to stop."""

    def snapshot():
        return {p: p.stat().st_mtime for p in SOURCES if p.exists()}

    try:
        report(build())
    except BuildError as e:
        print(f"build error: {e}")
    print(f"Watching for changes in {here}/ … (Ctrl-C to stop)")
    last = snapshot()
    try:
        while True:
            time.sleep(interval)
            now = snapshot()
            if now != last:
                last = now
                try:
                    report(build(), prefix=f"[{time.strftime('%H:%M:%S')}] ")
                except Exception as e:  # keep watching even if a build fails
                    print(f"build error: {e}")
    except KeyboardInterrupt:
        print("\nStopped watching.")


if __name__ == "__main__":
    if "--watch" in sys.argv[1:]:
        watch()
    else:
        try:
            report(build())
        except BuildError as e:
            sys.exit(f"build error: {e}")
