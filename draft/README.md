# draft-rsdggs-informational-00

`draft-rsdggs-informational-00.xml` is the xml2rfc v3 source of the Internet-Draft and the master copy: edit the draft here, and generate every other format (text, HTML, PDF) from it. The docx draft is retired. Build the renderings with:

```sh
draft/build.sh
```

It validates the XML against the RFCXML schema ([`rfc7991bis.rnc`](https://github.com/ietf-tools/RFCXML)) and runs [svgcheck](https://github.com/ietf-tools/svgcheck). It then writes `draft-rsdggs-informational-00.txt` and `.html` with [xml2rfc](https://github.com/ietf-tools/xml2rfc), and `.docx` with LibreOffice from the HTML (`docx.py` cleans up the conversion). The tools are pinned in `build.sh` and installed into `draft/.tools` on first run; it needs Python 3, Java and LibreOffice. The renderings are committed for convenience; rebuild them whenever the XML changes, and never edit them by hand.

The draft's `<date>` gives only the year, so each build is dated the day it runs, as an Internet-Draft submission is.

History of this file:

1. The export from the drafting chat session of 2026-06-15, unmodified. It had no tables and no lists.
2. The 4-bit triangle selector change (§4.4, §5, §7, §13.2, §14, §17.2, §18), including the §5.2 table.
3. The tables and lists restored from the last docx draft (`draft-rsdggs-informational-00_10.docx`), copied as they were. The docx repeats the §4.1.3 table; it appears once here. The export had replaced the §16.11 table with a two-column ASCII summary and dropped the section's two closing paragraphs; both are restored.

The two figures (Figure 1, the dodecahedron net, and Figure 2, its reference key) are images. The draft links to them in `images/` (`rsdggs_net_page1.png`, `rsdggs_net_page2.png`) instead of embedding them. Both are drawn by scripts next to them, `images/rsdggs_net_page1.py` and `images/rsdggs_net_page2.py` (matplotlib); edit a script and re-run it rather than editing the PNG. Figure 1 reads the face geometry from `src/constants.rs` and needs `numpy` and `shapely`; it downloads Natural Earth 5.1.2 country outlines once into `images/.cache/`.
