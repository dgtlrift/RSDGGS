"""Help LibreOffice turn the xml2rfc HTML into a usable .docx.

    python draft/docx.py prep IN.html OUT.html   # before LibreOffice
    python draft/docx.py fix FILE.docx           # after LibreOffice, in place

The IETF tools do not write .docx. LibreOffice converts the HTML well, except for:

- inline SVG figures, which `prep` turns into embedded images;
- the parts that only make sense in a browser or in print (pilcrow paragraph links,
  the running page header and footer, the "top" link), which `prep` removes;
- tables, which come out narrow and without borders. LibreOffice hangs on this document
  if the HTML tables carry width or border attributes, so `fix` sets full width and
  borders in the .docx itself.
"""

import base64
import shutil
import sys
import tempfile
import zipfile

from lxml import etree, html

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
               "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders",
               "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]


def w(tag):
    return f"{{{W}}}{tag}"


def prep(src, dst):
    doc = html.parse(src).getroot()
    for xpath in ('//a[@class="pilcrow"]', '//table[@class="ears"]', '//*[@class="toplink"]',
                  "//script"):
        for el in doc.xpath(xpath):
            el.drop_tree()
    # LibreOffice skips inline SVG, and links (does not embed) an image file; it does
    # embed an image given as a data: URI.
    for svg in doc.xpath('//*[local-name()="svg"]'):
        for el in svg.iter():                 # the HTML parser lowercased these
            for attr in ("viewBox", "baseProfile"):
                if attr.lower() in el.attrib:
                    el.set(attr, el.attrib.pop(attr.lower()))
        data = base64.b64encode(etree.tostring(svg)).decode()
        _, _, w, h = (float(v) for v in svg.get("viewBox").split())
        img = etree.Element("img", src="data:image/svg+xml;base64," + data,
                            width="576", height=str(round(576 * h / w)))  # 6 in wide
        img.tail = svg.tail
        svg.getparent().replace(svg, img)
    etree.ElementTree(doc).write(dst, method="html", encoding="utf-8")


def fix_tables(root):
    sect = root.find(f".//{w('sectPr')}")
    size, margins = sect.find(w("pgSz")), sect.find(w("pgMar"))
    text_width = (int(size.get(w("w"))) - int(margins.get(w("left")))
                  - int(margins.get(w("right"))))
    for tbl in root.iter(w("tbl")):
        tpr = tbl.find(w("tblPr"))
        if tpr is None:
            tpr = etree.Element(w("tblPr"))
            tbl.insert(0, tpr)
        for old in tpr.findall(w("tblW")) + tpr.findall(w("tblBorders")) + \
                tpr.findall(w("jc")) + tpr.findall(w("tblInd")):
            tpr.remove(old)
        etree.SubElement(tpr, w("tblW"), {w("w"): "5000", w("type"): "pct"})
        borders = etree.SubElement(tpr, w("tblBorders"))
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            etree.SubElement(borders, w(side), {w("val"): "single", w("sz"): "4",
                                                w("space"): "0", w("color"): "999999"})
        # Scale the column grid to the text width, keeping the column proportions.
        cols = tbl.findall(f"{w('tblGrid')}/{w('gridCol')}")
        total = sum(int(c.get(w("w"), "0")) for c in cols)
        if total:
            for c in cols:
                c.set(w("w"), str(int(c.get(w("w"))) * text_width // total))
        for tcw in tbl.iter(w("tcW")):
            tcw.getparent().remove(tcw)
        # Word rejects tblPr children that are out of schema order.
        tpr[:] = sorted(tpr, key=lambda el: TBLPR_ORDER.index(etree.QName(el).localname)
                        if etree.QName(el).localname in TBLPR_ORDER else len(TBLPR_ORDER))


def fix(path):
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        out = tmp.name
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = etree.fromstring(data)
                fix_tables(root)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                                      standalone=True)
            zout.writestr(item, data)
    shutil.move(out, path)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"prep": prep, "fix": fix}[cmd](*args)
