"""Check the references that connect the ring, its commands and their translations."""
from pathlib import Path
import re
from xml.etree import ElementTree as ET

MOD = Path(__file__).resolve().parents[1] / "mod"
PUBLIC = MOD / "Public" / "TacticianAI"
STATS = PUBLIC / "Stats" / "Generated" / "Data"


def attribute(node, name):
    return node.find(f"attribute[@id='{name}']").attrib["value"]


def check():
    # A missing reference can silently leave the camp chest or spellbook empty.
    meta = ET.parse(MOD / "Mods/TacticianAI/meta.lsx").find(".//node[@id='ModuleInfo']")
    assert attribute(meta, "Folder") == PUBLIC.name
    ring_file, = (PUBLIC / "RootTemplates").glob("*.lsx")
    ring = ET.parse(ring_file).find(".//node[@id='GameObjects']")
    ring_id = attribute(ring, "MapKey")
    reward = ET.parse(PUBLIC / "OneTimeRewards/OneTimeRewards.lsx").find(".//node[@id='OneTimeReward']")
    assert attribute(reward, "ItemTemplateId") == ring_id
    armor = (STATS / "Armor.txt").read_text()
    assert f'new entry "{attribute(ring, "Stats")}"' in armor
    assert f'data "RootTemplate" "{ring_id}"' in armor
    spells = (STATS / "Spell_Target.txt").read_text()
    assert set(re.findall(r"UnlockSpell\((\w+)\)", armor)) == set(re.findall(r'^new entry "(\w+)"', spells, re.M))
    status = re.search(r'^new entry "(\w+)"', (STATS / "Status_BOOST.txt").read_text(), re.M)[1]
    assert f'ApplyStatus({status},100,-1)' in spells and f'RemoveStatus({status})' in spells
    referenced = set(re.findall(r'h[0-9a-fg]{36}', armor + spells + (STATS / "Status_BOOST.txt").read_text() + ring_file.read_text()))
    for locale in ("French", "English"):
        entries = ET.parse(MOD / "Localization" / locale / "TacticianAI.xml").getroot()
        handles = [node.attrib["contentuid"] for node in entries]
        assert len(handles) == len(set(handles)) and set(handles) == referenced, locale
        assert all(node.text and node.text.strip() for node in entries), locale
    print("Verified camp reward, ring, spells, status and FR/EN localisation.")


if __name__ == "__main__":
    check()
