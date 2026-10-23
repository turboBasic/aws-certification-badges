---
name: svg-deduplicate-object
description: Deduplicate repeated labeled SVG objects by retaining a user-selected instance and replacing the others with linked uses while preserving document order and rendering.
---

# SVG object deduplication

Use when a user wants repeated SVG objects (often Inkscape-labeled paths) consolidated into one source object with references at the duplicates' existing positions.

- Work only in the SVG file the user identifies. Preserve every object's position in the document tree and its z-order; replace duplicates in place rather than moving or regrouping them.
- Before editing, enumerate every matching object with its SVG document-order index, ID, label, geometry, and transforms. Also determine its visible position. For letters or words forming text, interpret “first”, “second”, “last”, and similar ordinals in rendered reading order (normally left to right, then top to bottom), because SVG document order may be reversed or otherwise differ. For other graphics, use SVG document order unless the user specifies another sequence. State the mapping from the user's ordinal to the object ID before editing when the two orders differ; ask only if the intended sequence still cannot be determined.
- Keep the user-selected object as the sole geometry source. Replace each other geometry element in place with an SVG `<use>` element that keeps its original `id` and label, references the unique object's ID, and preserves necessary style or transform attributes.
- A `<use>` copies the source geometry in its original coordinate system; it does not automatically occupy the duplicate's former location. Compare rendered geometry and calculate the translation (or transform) needed to place each use where its replaced object was. Account for transforms already on the source and duplicate.
- Match the SVG version and existing conventions for links. For SVG 1.1 documents, declare `xmlns:xlink="http://www.w3.org/1999/xlink"` on the root if absent and use `xlink:href="#id"`. For SVG 2 documents, use `href="#id"` unless the document or target editor requires the XLink form. Do not add both attributes without a compatibility reason.
- Preserve object labels and IDs so editor workflows and other references remain usable. Check that IDs are unique and each reference resolves to the intended source.
- Render the edited SVG with an available renderer and visually check that linked objects appear in the same locations and order, with the same visible appearance. Parse the SVG to catch malformed XML. If a renderer is unavailable, verify the references and transforms and report that visual rendering was not checked.

When the user specifies instances one at a time, apply only that instruction and wait for the next. If a linked object does not render as expected, inspect the actual rendered image and coordinate systems before changing the reference format; the link syntax may be correct while its geometry is positioned elsewhere.
