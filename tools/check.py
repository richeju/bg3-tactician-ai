"""Check the references that connect the ring, its commands and their translations."""
from pathlib import Path
import re
from xml.etree import ElementTree as ET

MOD = Path(__file__).resolve().parents[1] / "mod"
META_PATH, = (MOD / "Mods").glob("*/meta.lsx")
PUBLIC = MOD / "Public" / META_PATH.parent.name
STATS = PUBLIC / "Stats" / "Generated" / "Data"


def attribute(node, name):
    return node.find(f"attribute[@id='{name}']").attrib["value"]


def stat_entries(text):
    # Split on entry boundaries so a tooltip or a different spell cannot satisfy a check.
    parts = re.split(r'^new entry "(\w+)"$', text, flags=re.M)
    return {
        name: dict(re.findall(r'^data "(\w+)" "([^"]*)"$', body, re.M))
        for name, body in zip(parts[1::2], parts[2::2])
    }


def check():
    # A missing reference can silently leave the camp chest or spellbook empty.
    meta = ET.parse(META_PATH).find(".//node[@id='ModuleInfo']")
    assert attribute(meta, "Folder") == PUBLIC.name == f"TacticianAI_{attribute(meta, 'UUID')}"
    assert (META_PATH.parent / "GUI" / "metadata.lsx").is_file()
    ring_file, = (PUBLIC / "RootTemplates").glob("*.lsx")
    ring = ET.parse(ring_file).find(".//node[@id='GameObjects']")
    ring_id = attribute(ring, "MapKey")
    reward = ET.parse(PUBLIC / "OneTimeRewards/OneTimeRewards.lsx").find(".//node[@id='OneTimeReward']")
    assert attribute(reward, "ItemTemplateId") == ring_id
    goal = META_PATH.parent / "Story/RawFiles/Goals/BTAI_StartingRing.txt"
    rule = [line.strip() for line in goal.read_text().splitlines() if line.strip()]
    marker = "DB_BTAI_StartingRingGranted(_Avatar)"
    grant = f'TemplateAddTo((ITEMROOT){attribute(ring, "Name")}_{ring_id},_Avatar,1,0);'
    # Use the same post-character-creation hook and parent goal as vanilla GLO_Alchemy.
    assert rule[rule.index("KBSECTION") + 1:rule.index("EXITSECTION")] == [
        "PROC", "PROC_Tutorial_Start()", "AND", "DB_Avatars(_Avatar)",
        "AND", f"NOT {marker}", "THEN", grant, f"{marker};",
    ]
    assert rule[-1] == 'ParentTargetEdge "Start"'
    armor = (STATS / "Armor.txt").read_text()
    assert f'new entry "{attribute(ring, "Stats")}"' in armor
    assert f'data "RootTemplate" "{ring_id}"' in armor
    targets = (STATS / "Spell_Target.txt").read_text()
    shout = (STATS / "Spell_Shout.txt").read_text()
    statuses = (STATS / "Status_BOOST.txt").read_text()
    commands = stat_entries(targets + "\n" + shout)
    assert set(re.findall(r"UnlockSpell\((\w+)\)", armor)) == set(commands)

    companion = commands["Target_BTAI_Delegate"]
    assert companion["SpellProperties"] == "ApplyStatus(BTAI_CONTROLLED,100,-1)"
    assert "not Self()" in companion["TargetConditions"]
    assert "not Tagged('AVATAR')" in companion["TargetConditions"]
    assert commands["Target_BTAI_Recall"]["SpellProperties"] == "RemoveStatus(BTAI_CONTROLLED)"
    effects = stat_entries(statuses)
    assert effects["BTAI_CONTROLLED"]["RemoveEvents"] == "OnCombatEnded"

    solo = commands["Shout_BTAI_DelegateSelf"]
    assert solo["SpellType"] == "Shout" and "CanNotUse" in solo["AIFlags"].split(";")
    assert solo["UseCosts"] == ""
    assert solo["TargetConditions"] == "Self()" and "Combat" in solo["Requirements"].split(";")
    assert re.fullmatch(r"ApplyStatus\((?:SELF,)?BTAI_SELF_CONTROLLED,100,1\)",
                        solo["SpellProperties"].replace(" ", ""))
    solo_status = effects["BTAI_SELF_CONTROLLED"]
    assert {"LoseControl", "LoseControlFriendly"} <= set(solo_status["StatusPropertyFlags"].split(";"))
    assert solo_status["TickType"] == "EndTurn"
    assert {"OnTurn", "OnCombatEnded"} <= set(solo_status["RemoveEvents"].split(";"))

    translated_text = armor + targets + shout + statuses + ring_file.read_text()
    referenced = set(re.findall(r'h[0-9a-fg]{36}', translated_text))
    for locale in ("French", "English"):
        entries = ET.parse(MOD / "Localization" / locale / "TacticianAI.xml").getroot()
        handles = [node.attrib["contentuid"] for node in entries]
        assert len(handles) == len(set(handles)) and set(handles) == referenced, locale
        assert all(node.text and node.text.strip() for node in entries), locale
    print("Verified starting inventory, camp reward, companion and solo commands, status expiry and FR/EN localisation.")


if __name__ == "__main__":
    check()
