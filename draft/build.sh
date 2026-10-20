#!/bin/sh
# Validate the draft, then write the .txt, .html and .docx renderings next to the XML.
#
#   draft/build.sh
#
# Tools, pinned (installed once into draft/.tools):
#   xml2rfc   v3.34.1   https://github.com/ietf-tools/xml2rfc    text and HTML
#   svgcheck  v0.12.0   https://github.com/ietf-tools/svgcheck   SVG profile check
#   RFCXML    02dd494   https://github.com/ietf-tools/RFCXML     rfc7991bis.rnc schema
#   jing      20181222  https://github.com/relaxng/jing-trang    RELAX NG validator (Java)
#   LibreOffice         HTML to .docx; the IETF tools do not write .docx
set -eu
cd "$(dirname "$0")"

name=draft-hanley-rsdggs-00
tools=.tools
rfcxml=02dd49434445ca0498a13baf904109478251bdd7
mkdir -p "$tools"

if [ ! -x "$tools/venv/bin/xml2rfc" ]; then
    python3 -m venv "$tools/venv"
    "$tools/venv/bin/pip" install -q \
        "git+https://github.com/ietf-tools/xml2rfc.git@v3.34.1" \
        "git+https://github.com/ietf-tools/svgcheck.git@v0.12.0"
fi
rnc="$tools/rfc7991bis.rnc"
if [ ! -f "$rnc" ]; then
    # rfc7991bis.rnc includes SVG-1.2-RFC.rnc.
    for f in rfc7991bis.rnc SVG-1.2-RFC.rnc; do
        curl -sSfL -o "$tools/$f" "https://raw.githubusercontent.com/ietf-tools/RFCXML/$rfcxml/$f"
    done
    (cd "$tools" && sha256sum -c -) <<EOF
9e82263d8e7450a75553ad9219b9f27e6de72399de61f31a5172a9f2db3dd8d2  rfc7991bis.rnc
d83cb019ff0ad725308e717115b63931dcdfe1e85087d3134a676f90191b044c  SVG-1.2-RFC.rnc
EOF
fi
jing="$tools/jing-20181222/bin/jing.jar"
if [ ! -f "$jing" ]; then
    curl -sSfL -o "$tools/jing.zip" \
        https://github.com/relaxng/jing-trang/releases/download/V20181222/jing-20181222.zip
    echo "87075cb8e94439d7d7fb7752c246074e1cebf52dff45176d02190b18bd4d462d  $tools/jing.zip" | sha256sum -c -
    unzip -q -o "$tools/jing.zip" -d "$tools"
fi

echo "== RFCXML schema (rfc7991bis.rnc)"
java -jar "$jing" -c "$rnc" "$name.xml"
echo "   valid"
echo "== svgcheck"
"$tools/venv/bin/svgcheck" "$name.xml"
# The black-and-white figures in images/bw are meant to be RFC-ready too.
for f in ../images/bw/*.svg ../images/bw/faces/*.svg; do
    "$tools/venv/bin/svgcheck" -N "$f" >/dev/null 2>&1 || { echo "$f: not RFC 7996 SVG" >&2; exit 1; }
done
echo "   images/bw: $(ls ../images/bw/*.svg ../images/bw/faces/*.svg | wc -l) files conform"
echo "== xml2rfc"
"$tools/venv/bin/xml2rfc" --text --html "$name.xml"

echo "== docx (LibreOffice)"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
"$tools/venv/bin/python" docx.py prep "$name.html" "$work/$name.html"
# Load the HTML as a Writer document. The default (Writer/Web) import can loop forever
# laying out this draft; a 4-line change to the boilerplate was enough to trigger it.
soffice --headless --norestore -env:UserInstallation="file://$work/profile" \
    --infilter="HTML (StarWriter)" \
    --convert-to "docx:MS Word 2007 XML" --outdir "$work" "$work/$name.html" >/dev/null
"$tools/venv/bin/python" docx.py fix "$work/$name.docx"
mv "$work/$name.docx" "$name.docx"
chmod 644 "$name.docx"
echo "   $name.docx"
