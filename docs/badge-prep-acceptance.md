# Badge preparation acceptance record

Manual acceptance run completed on 2026-10-21 with Pillow and the local CLI. The four supplied
Anthropic badge images were prepared with `--size 1024 --padding 32 --colors 8` into an ignored
scratch directory. Each produced one transparent RGBA PNG and one palette JSON. The PNGs are
centered with preserved proportions; visual comparison found no crop, transparency, or alignment
defect.

## Source provenance and output bounds

The SHA-256 values identify the exact supplied source files used in this pass. Track JSON links
identify the corresponding credential records.

| Credential | Track JSON | Source dimensions | Source SHA-256 | Prepared alpha bounds |
| --- | --- | ---: | --- | --- |
| Claude Certified Associate - Foundations (CCAO-F) | [ccao-f.json](https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/certifications/claude/tracks/ccao-f.json) | 600 × 600 | `98f0afbf7d36c9f802f9b2f164f42f5046ea37a931e705670c24475f4f35711f` | (33, 32)–(990, 992) |
| Claude Certified Architect - Foundations (CCAR-F) | [ccar-f.json](https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/certifications/claude/tracks/ccar-f.json) | 604 × 604 | `bd60b9af0ff88b4fd5a8dd4fdafaa8b38e009ad5fef983e96581f000d9d58587` | (35, 32)–(989, 992) |
| Claude Certified Architect - Professional (CCAR-P) | [ccar-p.json](https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/certifications/claude/tracks/ccar-p.json) | 600 × 600 | `002ff2ee94fdfb3e23508aa665b6fbcabff1e53eaf4455a268929e03e51cd7f0` | (32, 33)–(992, 991) |
| Claude Certified Developer - Foundations (CCDV-F) | [ccdv-f.json](https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/certifications/claude/tracks/ccdv-f.json) | 601 × 601 | `6320fffee5b5252d315bad407f94310e433d2ceaf8427dba440988a972041925` | (34, 32)–(989, 992) |

All prepared PNGs are 1024 × 1024 RGBA. The reported bounds are Pillow's exclusive alpha bounds.
Every output retained transparent pixels outside the badge artwork. The complete four-image CLI
run took about two seconds on the local environment.

## No-overwrite and font-sample checks

Rerunning the same batch into its occupied output directory exited 1 with an overwrite diagnostic.
The directory contained exactly four PNGs and four palette JSON files before and after, and all
eight SHA-256 hashes remained unchanged.

A font sample was exported from the Architect - Foundations source at
`left,top,right,bottom = 55,325,550,450`, scale 2, with `#d97757` behind transparent pixels. The
result was an RGB PNG of 990 × 250; visual comparison with the source confirms it contains the two
lines “Claude Certified / Architect” without clipping or including neighboring text.
