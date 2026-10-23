---
name: svg-deduplicate-object
description: Deduplicate repeated labeled SVG objects by retaining a user-selected instance and replacing the others with linked uses while preserving document order and rendering.
---

# SVG object deduplication

Use when a user wants repeated SVG objects (often Inkscape-labeled paths) consolidated into one source object with references at the duplicates' existing positions.

## Ground rules

- Work only in the SVG file the user identifies. Preserve each object's document-tree position and z-order; replace duplicates in place rather than moving or regrouping them.
- Treat labels as case-sensitive when identifying matching objects.
- Keep the user-selected object as the sole geometry source. Each replacement `<use>` keeps the replaced object's `id` and label, points to the source ID, and retains necessary style or transform attributes.
- Preserve labels and IDs for editor workflows and other references. Keep IDs unique and ensure every reference resolves to the intended source.
- Use SVG 1.1. If the document declares another version or no version, set the root `version` to `1.1`. Add `xmlns:xlink="http://www.w3.org/1999/xlink"` to the root if needed and use `xlink:href="#id"`. Do not add an unprefixed `href` without a compatibility reason.

## Workflow

1. Before editing, enumerate every matching object with its SVG document-order index, ID, label, geometry, and transforms.
2. Determine each object's visible position. For letters or words forming text, interpret “first”, “second”, “last”, and similar ordinals in rendered reading order (normally left to right, then top to bottom), since document order may differ. For other graphics, use document order unless the user specifies another sequence. If the orders differ, state the mapping from the user's ordinal to the object ID before editing; ask only if the intended sequence still cannot be determined.
3. A `<use>` copies source geometry in its original coordinate system; it does not automatically occupy the duplicate's former location. Compare rendered geometry and calculate the translation or transform needed to restore that position, accounting for transforms on both source and duplicate.
4. Parse the edited SVG to catch malformed XML. Render it with `rsvg-convert` (for example, `rsvg-convert -o /tmp/<name>.png <file.svg>`) and visually check that linked objects keep the same locations, order, and visible appearance. If `rsvg-convert` is unavailable, verify references and transforms, and report that visual rendering was not checked.
5. When the user specifies instances one at a time, apply only that instruction and wait for the next. If a linked object does not render as expected, inspect the rendered image and coordinate systems before changing the reference format; the link syntax may be correct while its geometry is positioned elsewhere.
