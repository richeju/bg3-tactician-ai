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


def check_tactics(effects, goals):
    archetypes = PUBLIC / "AI/Archetypes"
    lifecycle = (goals / "BTAI_AdaptiveCombat.txt").read_text()
    assert 'StatusApplied((CHARACTER)_Actor,"BTAI_CONTROLLED",_,_)' in lifecycle
    assert 'TurnStarted((CHARACTER)_Actor)\nAND\nHasActiveStatus(_Actor,"BTAI_CONTROLLED",1)' in lifecycle
    cleanup = lifecycle.split('StatusRemoved((CHARACTER)_Actor,"BTAI_CONTROLLED",_,_)')[1]
    profiles = {
        "BTAI_CONTROLLED": ("btai_adaptive", "base", 1),
        "BTAI_RANGED_TACTICS": ("btai_ranged", "btai_adaptive", 2),
        "BTAI_CONTROL_TACTICS": ("btai_control", "btai_adaptive", 3),
        "BTAI_RESCUE_TACTICS": ("btai_rescue", "btai_adaptive", 4),
    }
    for status, (name, parent, priority) in profiles.items():
        assert effects[status]["Boosts"] == f"AiArchetypeOverride({name},{priority})"
        assert effects[status]["RemoveEvents"] == "OnCombatEnded"
        tuning = (archetypes / f"{name}.txt").read_text().splitlines()
        assert tuning[0] == f"USING {parent}"
        if status != "BTAI_CONTROLLED":
            assert f'RemoveStatus(_Actor,"{status}");' in cleanup
    assert not (archetypes / "base.txt").exists()
    control_profile = (archetypes / "btai_control.txt").read_text()
    for key in ("MULTIPLIER_CONTROL_ENEMY_POS", "MODIFIER_CONCENTRATION_REMOVE_SELF"):
        adjustment = re.search(rf"^\+ {key} ([\d.]+)$", control_profile, re.M)
        assert adjustment and float(adjustment[1]) > 0, key
    for goal_name in ("BTAI_RangedTactics", "BTAI_RescueTactics", "BTAI_ControlTactics"):
        goal = (goals / f"{goal_name}.txt").read_text()
        assert "PROC_BTAI_RefreshTactics((CHARACTER)_Actor)" in goal
        assert 'ParentTargetEdge "Start"' in goal
        # Story chooses scoring preferences. The combat engine owns spell use and costs.
        assert "UseSpell(" not in goal and "RequestSetBaseArchetype(" not in goal

    rescue = (goals / "BTAI_RescueTactics.txt").read_text()
    spells = re.findall(r'DB_BTAI_RescueSpell\("([^"]+)",([\d.]+),(\d+),"([^"]+)"\);', rescue)
    assert set(spells) == {
        ("Target_HealingWord", "18.0", "1", "BonusActionPoint"),
        ("Target_CureWounds", "1.5", "1", "ActionPoint"),
        ("Target_Heal", "18.0", "6", "ActionPoint"),
    }
    assert 'DB_BTAI_PreparedCapability(_Actor,_Spell,"healing")' in rescue
    assert "IsSpellActive(_Actor,_Spell,1)" in rescue
    assert "GetActionResourceValuePersonal(_Actor,_Action,0,_Actions)" in rescue
    assert "GetActionResourceValuePersonal(_Actor,_Pool,_Level,_Slots)" in rescue


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
    spell_text = "\n".join(path.read_text() for path in sorted(STATS.glob("Spell_*.txt")))
    commands = stat_entries(spell_text)
    # Keep the existing ID for saved hotbars. No other command should be granted or defined.
    assert list(commands) == ["Target_BTAI_Delegate"]
    assert re.findall(r"UnlockSpell\((\w+)\)", armor) == list(commands)
    toggle = commands["Target_BTAI_Delegate"]
    assert toggle["SpellType"] == "Target" and toggle["MaximumTargets"] == "1"
    assert toggle["TargetRadius"] == "30" and toggle["UseCosts"] == ""
    assert toggle["AIFlags"] == "CanNotUse" and toggle["SpellFlags"] == ""
    assert toggle["SpellProperties"] == "" and toggle["TooltipStatusApply"] == ""
    assert not toggle.get("Requirements") and not toggle.get("RequirementConditions")
    assert toggle["TargetConditions"] == (
        "Character() and (Self() or (Party() and Ally())) and not Summon() and not Dead() and not IsDowned()"
    )

    statuses = (STATS / "Status_BOOST.txt").read_text()
    effects = stat_entries(statuses)
    # A save from 1.0.2.0 may still have either of the two original control statuses.
    states = {"BTAI_ENABLED", "BTAI_CONTROLLED", "BTAI_SELF_CONTROLLED"}
    assert set(toggle["SpellRoll"].split(" and ")) == {f"not HasStatus('{state}')" for state in states}
    assert set(toggle["SpellFail"].split(";")) == {f"RemoveStatus({state})" for state in states}
    assert toggle["SpellSuccess"].split(";") == [
        "ApplyStatus(BTAI_ENABLED,100,-1)", "IF(Combat()):ApplyStatus(BTAI_CONTROLLED,100,-1)"
    ]

    enabled = effects["BTAI_ENABLED"]
    assert enabled["StatusPropertyFlags"] == "IgnoreResting" and not enabled.get("RemoveEvents")
    passives = (STATS / "Passive.txt").read_text()
    auto = stat_entries(passives)[enabled["Passives"]]
    assert auto["Properties"] == "IsHidden" and auto["StatsFunctorContext"] == "OnCombatStarted"
    assert auto["Conditions"] == "not HasStatus('BTAI_CONTROLLED')"
    assert auto["StatsFunctors"] == "ApplyStatus(BTAI_CONTROLLED,100,-1)"
    control = effects["BTAI_CONTROLLED"]
    assert {"LoseControl", "LoseControlFriendly"} <= set(control["StatusPropertyFlags"].split(";"))
    assert control["RemoveEvents"] == "OnCombatEnded"
    assert effects["BTAI_SELF_CONTROLLED"]["RemoveEvents"] == "OnTurn;OnCombatEnded"
    check_tactics(effects, goal.parent)

    translated_text = armor + spell_text + statuses + passives + ring_file.read_text()
    referenced = set(re.findall(r'h[0-9a-fg]{36}', translated_text))
    for locale in ("French", "English"):
        entries = ET.parse(MOD / "Localization" / locale / "TacticianAI.xml").getroot()
        handles = [node.attrib["contentuid"] for node in entries]
        assert len(handles) == len(set(handles)) and set(handles) == referenced, locale
        assert all(node.text and node.text.strip() for node in entries), locale
    print("Verified ring grants, AI toggle, adaptive tactics and FR/EN localisation.")


if __name__ == "__main__":
    from check_capabilities import check_capabilities
    from check_control import check_control

    check()
    check_capabilities()
    check_control()
