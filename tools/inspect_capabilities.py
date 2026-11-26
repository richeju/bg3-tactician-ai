"""Show the detector snapshot stored in a BG3 save. Opens the .lsv read-only."""

import argparse
import json
import sys
from pathlib import Path

# Each saved Osiris fact starts with the actor's GUID string.
DATABASES = {
    "DB_BTAI_Scanned": ("scanned", ()),
    "DB_BTAI_OwnedCapability": ("owned_spells", ("spell", "category")),
    "DB_BTAI_PreparedCapability": ("prepared_spells", ("spell", "category")),
    "DB_BTAI_KnownPassive": ("known_passives", ("passive",)),
    "DB_BTAI_WeaponScore": ("weapon_scores", ("slot", "stat_id", "score")),
}


def summarize(facts):
    actors = {}
    available = []
    for database, (field, columns) in DATABASES.items():
        if database not in facts:
            continue
        available.append(database)
        for row in facts[database]:
            if len(row) != len(columns) + 1 or not all(cell["is_valid"] for cell in row):
                raise ValueError(f"Unexpected row in {database}")
            actor_id, *values = (cell["value"] for cell in row)
            if not isinstance(actor_id, str) or not actor_id:
                raise ValueError(f"Missing actor identifier in {database}")
            if actor_id not in actors:
                actors[actor_id] = {
                    "scanned": False, "owned_spells": [], "prepared_spells": [],
                    "known_passives": [], "weapon_scores": [],
                }
            if columns:
                actors[actor_id][field].append(dict(zip(columns, values, strict=True)))
            else:
                actors[actor_id][field] = True
    for actor in actors.values():
        for field, columns in DATABASES.values():
            if columns:
                actor[field].sort(key=lambda entry: tuple(entry[key] for key in columns))
    if not available:
        status = "detector_absent"
    elif not actors:
        status = "no_saved_actors"
    else:
        status = "snapshot"
    return {"status": status, "available_databases": available, "actors": dict(sorted(actors.items()))}


def read_snapshot(path):
    from bg3parser.lspk import extract_frames
    from bg3parser.osiris import read_story

    try:
        frames = extract_frames(str(path))
    except OSError:
        raise
    except Exception as exc:
        # The backend uses struct, compression and format-specific exceptions.
        raise ValueError(f"Invalid or unsupported save archive ({exc})") from exc
    if "StorySave.bin" not in frames:
        raise ValueError("Missing StorySave.bin in the save")
    story = read_story(frames)
    if story is None:
        raise ValueError("The parser could not decode the saved Osiris story")
    version, facts, _ = story
    return {"osiris_version": f"{version >> 8}.{version & 255}", **summarize(facts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, help="Path to an existing .lsv file")
    args = parser.parse_args()
    try:
        snapshot = read_snapshot(args.save)
    except ImportError as exc:
        parser.exit(2, f"Install the optional save inspector dependency from the README. {exc}\n")
    except (OSError, ValueError, KeyError, IndexError) as exc:
        parser.exit(1, f"Could not inspect {args.save.name}: {exc}\n")
    json.dump(snapshot, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
