"""Generate the Osiris capability catalogue from the installed base game's stats."""

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

from bg3forge.pak import PakReader


ROOT = Path(__file__).resolve().parents[1]
GOAL = next((ROOT / "mod/Mods").glob("*/Story/RawFiles/Goals")) / "BTAI_CapabilityCatalog.txt"
STEAM = Path.home() / "Library/Application Support/Steam/steamapps/common/Baldurs Gate 3"
# Normal campaign modules in dependency order. Honour-specific overrides depend on the ruleset.
PACKAGES = (("Shared", ("Shared", "SharedDev")), ("Gustav", ("Gustav", "GustavDev")),
            ("GustavX", ("GustavX",)))
# Universal or equipment-granted actions that do not need a class spell list.
COMMON_ACTIONS = (
    "Target_MainHandAttack", "Target_OffhandAttack", "Target_UnarmedAttack",
    "Projectile_MainHandAttack", "Projectile_OffhandAttack", "Projectile_HamstringShot",
    "Projectile_PiercingShot", "Target_Topple", "Target_CripplingStrike", "Target_PommelStrike",
    "Zone_Cleave", "Target_Shove", "Target_Help", "Shout_Dash", "Shout_Disengage",
    "Shout_Hide", "Shout_Rage",
)
FIELDS = {
    "AIFlags", "Boosts", "OnApplyFunctors", "OriginSpellProperties", "Requirements", "RootSpellID",
    "SpellFail", "SpellFlags", "SpellProperties", "SpellSuccess",
    "StatusGroups", "TargetConditions", "TooltipDamageList", "TooltipStatusApply", "VerbalIntent",
}
ENTRY = re.compile(r'^new entry "([^"]+)"$')
DATA = re.compile(r'^data "(\w+)" "(.*)"$')
PARENT = re.compile(r'^using "([^"]+)"$')
STATUS = re.compile(r'\bApplyStatus\(\s*(?:(?:SELF|SOURCE|TARGET)\s*,\s*)?([A-Z][A-Z0-9_]+)\s*,')
CONTROL_GROUPS = {
    "SG_Blinded", "SG_Charmed", "SG_Frightened", "SG_Incapacitated", "SG_Paralyzed",
    "SG_Prone", "SG_Restrained", "SG_Silenced", "SG_Stunned", "SG_Unconscious",
}


@dataclass
class Entry:
    parent: str = ""
    data: dict = field(default_factory=dict)


def read_stats(payload, entries):
    record = None
    for line in payload.decode("utf-8-sig").splitlines():
        if match := ENTRY.fullmatch(line):
            record = Entry()
            entries[match[1]].append(record)
        elif record is not None:
            if match := PARENT.fullmatch(line):
                record.parent = match[1]
            elif (match := DATA.fullmatch(line)) and match[1] in FIELDS:
                record.data[match[1]] = match[2]


def read_spell_lists(payload, spell_lists):
    for node in ElementTree.fromstring(payload).iterfind('.//node[@id="SpellList"]'):
        attrs = {attr.get("id"): attr.get("value") for attr in node.findall("attribute")}
        if "Spells" in attrs:
            spell_lists[attrs["UUID"]] = {spell for spell in attrs["Spells"].split(";") if spell}


def load(game_data):
    entries = defaultdict(list)
    spell_lists = {}
    for package, modules in PACKAGES:
        with PakReader(game_data / f"{package}.pak") as pak:
            names = sorted(pak.names())
            for module in modules:
                spell_list = f"Public/{module}/Lists/SpellLists.lsx"
                if spell_list in names:
                    read_spell_lists(pak.read(spell_list), spell_lists)
                for name in names:
                    if re.fullmatch(rf"Public/{module}/Stats/Generated/Data/(?:Spell|Status)_[^/]+\.txt", name):
                        read_stats(pak.read(name), entries)
    if not spell_lists:
        raise ValueError("No player spell lists found in game packages")
    return entries, set(COMMON_ACTIONS).union(*spell_lists.values())


def resolver(entries):
    @lru_cache(maxsize=None)
    def resolve(name, index=None):
        records = entries[name]
        if index is None:
            index = len(records) - 1
        if index < 0:
            raise ValueError(f"Unresolved stats parent {name}")
        entry = records[index]
        if entry.parent == name:
            # A same-name override inherits the previous module's version.
            inherited = resolve(name, index - 1)
        elif entry.parent:
            inherited = resolve(entry.parent)
        else:
            inherited = {}
        # An explicit empty field clears its inherited value.
        return {**inherited, **entry.data}

    return resolve


def classify(spell, entries, resolve):
    intent = spell.get("VerbalIntent")
    effects = ";".join(spell.get(key, "") for key in (
        "SpellProperties", "OriginSpellProperties", "SpellSuccess", "SpellFail"
    ))
    tooltip = spell.get("TooltipDamageList", "")
    status_refs = effects + ";" + spell.get("TooltipStatusApply", "")
    statuses = [resolve(name) for name in sorted(set(STATUS.findall(status_refs))) if name in entries]
    groups = {group for status in statuses for group in status.get("StatusGroups", "").split(";")}
    boosts = ";".join(status.get("Boosts", "") for status in statuses)
    # Native intent distinguishes a hostile drain from a heal, or a stun from its weapon damage.
    if intent == "Damage":
        return "damage"
    if intent in {"Control", "Debuff"}:
        return "control"
    if "DealDamage(" in effects and intent != "Buff":
        return "damage"
    if "RemoveStatus(" in effects and "IF(IsDowned()):RegainHitPoints(1)" in effects:
        return "support"  # Help grants one hit point only to get a downed target back up.
    if re.search(r"\b(?:RegainHitPoints|Resurrect|Stabilize)\(", effects) or "RegainHitPoints(" in tooltip:
        return "healing"
    if groups & CONTROL_GROUPS or "OriginToEntity,Aggressive)" in effects:
        return "control"
    if intent == "Buff" or re.search(r"\b(?:AC|TemporaryHP|IncreaseMaxHP|DownedStatus|ActionResource|RollBonus)\(", boosts):
        return "support"
    if "DealDamage(" in tooltip:
        return "damage"
    if intent == "Healing":
        # Restoration spells and other effects that cure conditions without restoring HP.
        return "support"
    if any("RegainHitPoints(" in status.get("OnApplyFunctors", "") for status in statuses):
        return "healing"
    return "utility"


def catalogue(game_data):
    entries, candidates = load(game_data)
    resolve = resolver(entries)
    rows = {}
    for name in sorted(candidates):
        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise ValueError(f"Invalid spell identifier: {name!r}")
        # The shared lists also contain a few narrative NPC and passive unlock helpers.
        if "_NPC" in name or "_GOB_" in name or name.endswith("_Unlock"):
            continue
        if name not in entries:
            raise ValueError(f"Missing player ability {name} in stats")
        spell = resolve(name)
        if (spell.get("RootSpellID") and re.search(r"_\d+$", name)
                or "CanNotUse" in spell.get("AIFlags", "").split(";")
                or "!Combat" in spell.get("Requirements", "").split(";")
                or "ShortRest()" in spell.get("SpellProperties", "")):
            continue
        rows[name] = classify(spell, entries, resolve)
    return rows


def render(rows):
    return "\n".join([
        "Version 1", "SubGoalCombiner SGC_AND", "INITSECTION",
        "// Generated by tools/generate_capabilities.py from the base game.",
        *(f'DB_BTAI_Catalog("{name}","{category}");' for name, category in rows.items()),
        "KBSECTION", "EXITSECTION", "ENDEXITSECTION", 'ParentTargetEdge "Start"', "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-data", type=Path, help="BG3 Data directory containing Shared.pak")
    parser.add_argument("--check", action="store_true", help="Check the committed goal without writing it")
    args = parser.parse_args()
    game_data = args.game_data or next(STEAM.glob("*.app/Contents/Data"), None)
    if game_data is None or not (game_data / "Shared.pak").is_file():
        parser.error("pass --game-data with the path to the installed game's Data directory")
    rows = catalogue(game_data)
    goal = render(rows)
    if args.check:
        if not GOAL.is_file() or GOAL.read_bytes() != goal.encode("utf-8"):
            raise SystemExit("Capability catalogue is out of date")
    else:
        GOAL.write_bytes(goal.encode("utf-8"))
    counts = ", ".join(f"{key}={count}" for key, count in sorted(Counter(rows.values()).items()))
    print(f"{len(rows)} capabilities ({counts})")


if __name__ == "__main__":
    main()
