#!/usr/bin/env python3
"""Prepare 14 legacy-reference cleanups on a staging fork, not upstream."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

LEGACY = "dss2020_hydraulic_load_current"
CURRENT = "hydraulic_load_current"
qgs = Path("project/teksi_wastewater.qgs")
ui = Path("plugin/teksi_wastewater/processing_provider/swmm_import_results.py")
docs = Path("docs/en/tww_swmm/Import-Results.rst")

original = qgs.read_text(encoding="utf-8")
root = ET.fromstring(original)
legacy_count = 0
for layer in root.findall(".//projectlayers/maplayer"):
    for parent in layer.iter():
        if parent.tag not in {"editable", "labelOnTop", "reuseLastValue"}:
            continue
        fields = [e for e in parent if e.tag == "field"]
        for obsolete in [e for e in fields if e.get("name") == LEGACY]:
            match = [e for e in fields if e.get("name") == CURRENT]
            assert len(match) == 1, "Missing or ambiguous replacement for old field"
            old_attrs = {k: v for k, v in obsolete.attrib.items() if k != "name"}
            new_attrs = {k: v for k, v in match[0].attrib.items() if k != "name"}
            assert old_attrs == new_attrs, "Removing conflicting settings is unsafe"
            legacy_count += 1
assert legacy_count == 12, f"Expected 12 redundant QGIS settings, got {legacy_count}"
lines = original.splitlines(keepends=True)
new_lines = []
removed = 0
for line in lines:
    if LEGACY in line and re.search(r"<field\b[^>]*\bname=[\"']" + LEGACY + r"[\"']", line):
        removed += 1
    else:
        new_lines.append(line)
assert removed == 12
updated_qgs = "".join(new_lines)
ET.fromstring(updated_qgs)
assert LEGACY not in updated_qgs
qgs.write_text(updated_qgs, encoding="utf-8")

for path in (ui, docs):
    before = path.read_text(encoding="utf-8")
    assert before.count(LEGACY) == 1, f"Unexpected references in {path}"
    path.write_text(before.replace(LEGACY, CURRENT), encoding="utf-8")
    assert LEGACY not in path.read_text(encoding="utf-8")

assert LEGACY not in qgs.read_text(encoding="utf-8")
print("PASS: Removed 12 redundant QGIS references and corrected UI + docs (14 total)")
