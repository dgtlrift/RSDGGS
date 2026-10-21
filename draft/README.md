# draft-hanley-rsdggs-01

`draft-hanley-rsdggs-01.xml` is the xml2rfc v3 source of the Internet-Draft and the master copy: edit the draft here, and generate every other format (text, HTML, PDF) from it. The pre-draft docx is retired. Build the renderings with:

```sh
draft/build.sh
```

It validates the XML against the RFCXML schema ([`rfc7991bis.rnc`](https://github.com/ietf-tools/RFCXML)) and runs [svgcheck](https://github.com/ietf-tools/svgcheck). It then writes `draft-hanley-rsdggs-01.txt` and `.html` with [xml2rfc](https://github.com/ietf-tools/xml2rfc), and `.docx` with LibreOffice from the HTML (`docx.py` cleans up the conversion). The tools are pinned in `build.sh` and installed into `draft/.tools` on first run; it needs Python 3, Java and LibreOffice. The renderings are committed for convenience; rebuild them whenever the XML changes, and never edit them by hand.

The draft's `<date>` gives only the year, so each build is dated the day it runs, as an Internet-Draft submission is.

History of this file. RSDGGS was in a pre-draft phase until this file: the June export and the docx were working documents, nothing was submitted to the IETF, and `draft-rsdggs-informational-00` was a working title rather than an Internet-Draft name. `draft-hanley-rsdggs-00` is the first version prepared for submission.

1. The pre-draft XML export from the drafting chat session of 2026-06-15, unmodified. It had no tables and no lists.
2. The 4-bit triangle selector change (sections 4.4, 5, 7, 13.2, 14, 17.2 and 18), including the section 5.2 table.
3. The tables and lists restored from the last pre-draft docx (`draft-rsdggs-informational-00_10.docx`), copied as they were. The docx repeats the section 4.1.3 table; it appears once here. The export had replaced the section 16.11 table with a two-column ASCII summary and dropped the section's two closing paragraphs; both are restored.
4. Renamed from the working title to `draft-hanley-rsdggs-00`, following the `draft-<surname>-<topic>` convention for individual drafts.
5. `draft-hanley-rsdggs-00` was posted to the IETF on 2026-10-20 ([datatracker](https://datatracker.ietf.org/doc/draft-hanley-rsdggs/)), before the idnits fixes (PR #10) and the corrected Face 2 orientation in the CN101923801B comparison (PR #11) reached main. A posted revision cannot be replaced, so the file was renamed to `draft-hanley-rsdggs-01`, the next revision to submit.

## Figures

The draft carries the dodecahedron net as Figure 5. It is inline SVG in an `<artset>`, with a short ASCII-art note for the text rendering, because plain text cannot show a drawing. The RFC SVG profile (RFC 7996) allows black and white only, with no raster images, gradients, patterns or clipping. So `images/rsdggs_bw.py` draws a black-and-white version, with the ISM bands as hatching, writes it to `images/bw/rsdggs_net_page1_bw.svg` and copies it into the XML between the `rsdggs_bw.py: begin/end` comments. Re-run the script rather than editing the SVG in the XML.

The net's reference key (band legend, face table, folding instructions and band quick reference) is not embedded. Everything on it is already in the draft as text and tables (sections 4.6.1 to 4.6.3 and 9), which work in every rendering. The draft links to the full-colour net and key, and to the black-and-white and per-face versions, in this repository.

Those links name the revision's tag (`blob/draft-hanley-rsdggs-01/...`), not a branch, so a posted revision keeps pointing at the files it was written against; `build.sh` fails on any other link into this repository. When a revision is submitted, tag the commit whose XML is uploaded with the draft name and push the tag (`git tag draft-hanley-rsdggs-01 && git push origin draft-hanley-rsdggs-01`); the links do not resolve until then. For the next revision, rename the files, `docName`, `seriesInfo` and the links together.

The colour net and key are drawn by `images/rsdggs_net_page1.py` and `images/rsdggs_net_page2.py` (matplotlib), which write the PNG and an all-vector SVG; edit a script and re-run it rather than editing the output. The key's labels take the draft name from `docName`, so re-running the scripts after a rename updates them. `images/rsdggs_faces.py` draws the twelve faces one per page (`images/faces/rsdggs_face_00.svg` to `_11.svg`) for building a larger model; each edge is labelled with its face and triangle, and each glue tab names the edge it goes under. The net scripts read the face geometry from `src/constants.rs` and needs `numpy` and `shapely`; it downloads Natural Earth 5.1.2 country outlines once into `images/.cache/`.
