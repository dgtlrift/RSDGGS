# draft-rsdggs-informational-00

`draft-rsdggs-informational-00.xml` is the xml2rfc v3 source of the Internet-Draft and the master copy: edit the draft here, and generate every other format (text, HTML, PDF) from it. The docx draft is retired. Render with [xml2rfc](https://pypi.org/project/xml2rfc/):

```sh
pip install xml2rfc
xml2rfc --text --html draft/draft-rsdggs-informational-00.xml
```

History of this file:

1. The export from the drafting chat session of 2026-06-15, unmodified. It had no tables and no lists.
2. The 4-bit triangle selector change (§4.4, §5, §7, §13.2, §14, §17.2, §18), including the §5.2 table.
3. The tables and lists restored from the last docx draft (`draft-rsdggs-informational-00_10.docx`), copied as they were. The docx repeats the §4.1.3 table; it appears once here. The export had replaced the §16.11 table with a two-column ASCII summary and dropped the section's two closing paragraphs; both are restored.

The two figures (Figure 1, the dodecahedron net, and Figure 2, its reference key) are images. The draft links to them in `images/` (`rsdggs_net_page1.png`, `rsdggs_net_page2.png`) instead of embedding them. Figure 2 is drawn by `images/rsdggs_net_page2.py` (matplotlib); edit the script and re-run it rather than editing the PNG.
