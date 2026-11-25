"""Pack an already compiled BG3 module into a single-part v18 diagnostic archive."""
import argparse
import ctypes
import hashlib
import os
import struct
from ctypes.util import find_library
from pathlib import Path
from tempfile import TemporaryDirectory

from bg3forge.pak import PakReader

HEADER = struct.Struct("<4sIQIBB16sH")
ENTRY = struct.Struct("<256sIHBBII")


def load_compressor():
    library = os.environ.get("BG3_LZ4_LIBRARY") or find_library("lz4") or "/opt/homebrew/opt/lz4/lib/liblz4.dylib"
    lz4 = ctypes.CDLL(library)
    lz4.LZ4_compressBound.argtypes = [ctypes.c_int]
    lz4.LZ4_compressBound.restype = ctypes.c_int
    lz4.LZ4_compress_HC.argtypes = [
        ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int
    ]
    lz4.LZ4_compress_HC.restype = ctypes.c_int
    return lz4


def compress(lz4, data):
    if len(data) > 0x7E000000:
        raise ValueError("Input exceeds the LZ4 block size limit")
    buffer = ctypes.create_string_buffer(lz4.LZ4_compressBound(len(data)))
    length = lz4.LZ4_compress_HC(data, buffer, len(data), len(buffer), 12)
    if length <= 0:
        raise ValueError("LZ4 compression failed")
    return buffer.raw[:length]


def pack(source, destination):
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("Output must be outside the staging directory")
    files = {file.relative_to(source).as_posix(): file.read_bytes()
             for file in source.rglob("*") if file.is_file()
             and not any(part.startswith(".") for part in file.relative_to(source).parts)}
    manifests = [name for name in files if name.startswith("Mods/") and name.endswith("/meta.lsx")]
    if len(manifests) != 1:
        raise ValueError("Staging directory must contain exactly one Mods/<module>/meta.lsx")
    lz4 = load_compressor()
    ordered = sorted(files, key=lambda name: (name != manifests[0], name))
    entries = {}
    archive_hash = hashlib.md5()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as scratch:
        result = Path(scratch) / destination.name
        with result.open("wb") as stream:
            stream.write(bytes(HEADER.size))
            for name in ordered:
                data = files[name]
                archive_hash.update(data)
                raw_name = name.encode("utf-8")
                if len(raw_name) >= 256:
                    raise ValueError(f"Package entry path too long: {name}")
                offset = stream.tell()
                compressed = compress(lz4, data)
                entries[name] = ENTRY.pack(raw_name, offset & 0xffffffff, offset >> 32,
                                           0, 0x42, len(compressed), len(data))
                stream.write(compressed)
                stream.write(b"\xad" * (-(stream.tell() - HEADER.size) % 64))
            index_offset = stream.tell()
            table = compress(lz4, b"".join(entries[name] for name in sorted(entries)))
            stream.write(struct.pack("<II", len(entries), len(table)))
            stream.write(table)
            # LSLib's v18 opt-in hash increments each byte of the payload digest.
            digest = bytes((value + 1) % 256 for value in archive_hash.digest())
            stream.seek(0)
            stream.write(HEADER.pack(b"LSPK", 18, index_offset, 8 + len(table), 2, 0, digest, 1))
        with PakReader(result) as reader:
            if set(reader.names()) != set(files) or len(reader.entries) != len(files):
                raise ValueError("Archive entry index differs from source")
            for name, data in files.items():
                if reader.read(name) != data:
                    raise ValueError(f"Archive verification failed: {name}")
        result.replace(destination)
    print(f"{destination}: verified {len(files)} file(s), SHA256 {hashlib.sha256(destination.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    pack(arguments.source, arguments.destination)
