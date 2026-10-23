---
name: svg-render-layer
description: Render one named Inkscape SVG layer as a standalone SVG beside existing renders, preserving the page and artwork while excluding template layers.
---

# SVG layer rendering

Use when a user wants one SVG layer rendered or exported as a standalone SVG, especially into a project's rendered-assets directory.

## Ground rules

- Preserve the source SVG. Write the standalone render to the requested output location or beside matching renders.
- Match the source page dimensions and viewBox. Follow a sibling rendered SVG's root metadata and structure when one exists.
- Include only the requested layer in the output. Remove other layers instead of relying on `display:none`; Finder and browsers can expose hidden template artwork.
- Make the selected layer itself visible in the standalone output. Inkscape template layers may have `style="display:none"`; set the layer to `display:inline` so browsers and SVG renderers show its artwork.
- Expand the selected layer's `<use>` clones recursively into standalone shapes. Preserve each clone's transform, position, style, label, and stacking order. Set the rendered clone visible when its template instance is hidden.
- Keep every referenced shape's own transform and style when expanding it. Abort on missing or cyclic references; do not silently drop artwork.
- Update the output title, root document ID, Sodipodi document name, and Inkscape current layer to match the selected layer and output filename. Preserve other page settings from the source or sibling render.

## Workflow

1. Read the source SVG and inspect sibling rendered SVGs. Identify the requested layer by its Inkscape label and ID; check the layer's own visibility, child visibility, and the full set of clone references.
2. Build the output as a standalone SVG with the selected layer only. Recursively replace `<use>` elements with grouped copies of their targets, keeping clone attributes on the wrapper and applying nonzero `x`/`y` as a translation. Keep the referenced objects' transforms nested so SVG transform order is preserved.
3. Ensure the selected layer has `display:inline` and its artwork is visible, including clones whose source-layer visibility flags were hidden. Do not include raster originals, generic template artwork, or other certification layers.
4. Parse the output as XML. Confirm the page dimensions match the source, exactly one visible layer remains, all clones were expanded, and the title, root ID, Sodipodi document name, and Inkscape current layer match the selected layer/output filename.
5. Render the output with an SVG renderer or open it in a browser and inspect it. Check that the rasterized result is not fully transparent, then look for missing shield/background shapes, stray template marks, wrong color, or misplaced text. Compare with the sibling render at the same scale. If visual verification is unavailable, say so.
