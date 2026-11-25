"""Compile the project and assemble its verified BG3 v18 package."""

from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from pack_candidate import pack
from bg3forge.parsers.localization import LocaEntry, parse_loca, write_loca
from bg3forge.parsers.lsf import parse_lsf, write_lsf
from bg3forge.parsers.lsx import load_lsx


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mod"
OUTPUT = ROOT / "dist" / "TacticianAI.pak"


def package_entry(path):
    name = path.relative_to(SOURCE)
    if name.parts[0] == "Localization" and path.suffix == ".xml":
        records = [
            LocaEntry(node.attrib["contentuid"], int(node.attrib["version"]), node.text or "")
            for node in ElementTree.parse(path).getroot().findall("content")
        ]
        data = write_loca(records)
        if parse_loca(data) != records:
            raise ValueError(f"Localisation round-trip mismatch in {name}")
        return name.with_suffix(".loca"), data
    if path.parent.name in ("RootTemplates", "GUI") and path.suffix == ".lsx":
        template = load_lsx(path)
        if path.parent.name == "RootTemplates":
            # LSLib's LSF layout differs from bg3forge's. Keep our reference
            # output and validate it against its editable LSX on every build.
            data = (ROOT / "compiled" / path.with_suffix(".lsf").name).read_bytes()
        else:
            data = write_lsf(template, version=7)
        if parse_lsf(data) != template:
            raise ValueError(f"LSF differs from the source for {name}; recompile the edited LSX")
        return name.with_suffix(".lsf"), data
    text = path.read_text(encoding="utf-8")
    if name.parts[0] == "Public":
        # The original release used the Windows LSLib checkout's CRLF text.
        text = text.replace("\n", "\r\n")
    return name, text.encode("utf-8")


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=OUTPUT.parent) as work:
        stage = Path(work)
        for path in sorted(SOURCE.rglob("*")):
            if path.is_file() and not any(part.startswith(".") for part in path.relative_to(SOURCE).parts):
                name, data = package_entry(path)
                target = stage / name
                if target.exists():
                    raise ValueError(f"Duplicate archive path {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        pack(stage, OUTPUT)


if __name__ == "__main__":
    main()
