"""Build and reopen the BG3 package with bg3forge 0.2.0."""

from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from bg3forge.pak import CompressionMethod, PakReader, PakWriter
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
    if path.parent.name == "RootTemplates" and path.suffix == ".lsx":
        template = load_lsx(path)
        data = write_lsf(template, version=7)
        if parse_lsf(data) != template:
            raise ValueError(f"Template round-trip mismatch in {name}")
        return name.with_suffix(".lsf"), data
    return name, path.read_bytes()


def main():
    entries = {}
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file() and not any(p.startswith(".") for p in path.relative_to(SOURCE).parts):
            name, data = package_entry(path)
            if name.as_posix() in entries:
                raise ValueError(f"Duplicate archive path {name}")
            entries[name.as_posix()] = data
    if "Mods/TacticianAI/meta.lsx" not in entries:
        raise ValueError("Missing mod metadata")

    writer = PakWriter(compression=CompressionMethod.ZLIB)
    for name, data in entries.items():
        writer.add(name, data)
    OUTPUT.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=OUTPUT.parent) as work:
        pak = writer.write(Path(work) / OUTPUT.name)
        with PakReader(pak) as archive:
            if set(archive.names()) != set(entries):
                raise ValueError("PAK directory differs from build inputs")
            for name, data in entries.items():
                if archive.read(name) != data:
                    raise ValueError(f"PAK round-trip mismatch in {name}")
        pak.replace(OUTPUT)
    print(f"Built {OUTPUT} ({len(entries)} files)")


if __name__ == "__main__":
    main()
