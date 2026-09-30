# Lab documentation site (`gh-pages`)

This branch holds the **participant-facing lab guide** for Build with Gemini
Track 3 and the script that builds it.

> The `main` branch is different: it's what participants download (the agent
> skills). The docs live here on `gh-pages` only.

## How it works

One markdown file is the source for every version of the guide. `site/build.py`
turns it into self-contained HTML pages, one per **variant**. Each page has the
markdown and the `marked.js` renderer inlined, so it needs no other files
except the images in `images/`.

| Variant | Output | Used by |
|---|---|---|
| `vm` | `index.html` | The main site on GitHub Pages (Qwiklabs remote VM setup) |
| `gsi` | `gsi.html` | The GSI team, who pull it from this repo (no Cloud console setup, no swag) |

```
site/
├── Gemini World 3 QwikLab 2.0.md   ← the source you edit
├── build.py                        ← builds every variant; lists them in VARIANTS
├── index.html                      ← HTML template (styles, nav, rendering)
└── marked.min.js                   ← markdown renderer (vendored)
index.html                          ← built: vm variant   (do NOT hand-edit)
gsi.html                            ← built: gsi variant  (do NOT hand-edit)
images/                             ← screenshots referenced by the markdown
styles/                             ← GM3 color tokens the template's CSS was ported from
```

## Making a change

1. Edit **`site/Gemini World 3 QwikLab 2.0.md`**. Put screenshots in `images/`
   and reference them with relative paths, e.g. `![](images/my-screenshot.png)`.
2. Rebuild every page:
   ```bash
   python3 site/build.py
   ```
   While iterating, use watch mode to rebuild on every save (Ctrl-C to stop):
   ```bash
   python3 site/build.py --watch
   ```
3. Preview by opening the built page (`open index.html` or `open gsi.html`) and
   refreshing after each rebuild.
4. Commit the markdown **and** both built pages, then push:
   ```bash
   git add -A && git commit -m "Update lab docs" && git push origin gh-pages
   ```

Never hand-edit `index.html` or `gsi.html`. They're overwritten on every build.
If you change the look of the page, edit the template `site/index.html` and
rebuild.

## Variants

Text with no tags goes into **every** variant. Wrap only the parts that differ:

```markdown
Shared text that every variant gets.

<!-- variant:vm -->
## Open the Google Cloud console
...VM-only steps...
<!-- /variant -->
<!-- variant:gsi -->
## Open Antigravity 2.0
<!-- /variant -->

More shared text.
```

Rules:

- Each marker goes on its own line.
- Inside a list item, indent the markers to match the item's text (e.g. three
  spaces for a numbered item).
- A block can list several variants: `<!-- variant:vm,gsi -->`.
- Blocks can't be nested.

The build stops with a line number if a marker names an unknown variant, is
malformed, or isn't closed, so a typo can't silently drop content.

### Adding a variant

1. Add a line to `VARIANTS` in `site/build.py`, e.g.
   `"byol": root / "byol.html",`.
2. Tag the markdown wherever the new variant differs.
3. Rebuild and commit the new output.

If a new version would differ from this guide in most sections, give it its own
markdown file instead. Tags work well for a handful of differences; past that
the source becomes hard to read.
