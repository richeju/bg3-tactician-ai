"""Run the shipped crowd-control rules against simulated native BG3 query results."""

from check_capabilities import GOALS, PREPARED, SpellbookFixture, parse_call, read_rules, sections, word


CASTER = "caster"
ENEMY = "enemy"
HOLD = "Target_HoldPerson"
DELEGATED = "BTAI_CONTROLLED"
CONTROL = "BTAI_CONTROL_TACTICS"
RESCUE = "BTAI_RESCUE_TACTICS"
EFFECTS = {
    HOLD: ("HOLD_PERSON", "SG_Paralyzed"), "Target_HoldMonster": ("HOLD_MONSTER", "SG_Paralyzed"),
    "Target_Blindness": ("BLINDNESS", "SG_Blinded"),
}


class CombatFixture(SpellbookFixture):
    def rows(self, name, args):
        if name in self.facts:
            return self.facts[name]
        if name == "IntegerProduct":
            left, right, _ = args
            return [(left, right, left * right)]
        return super().rows(name, args)

    def execute(self, line, state):
        _, action, terms = parse_call(line)
        if action in {"ApplyStatus", "RemoveStatus"}:
            actor, effect = (state.get(term, word(term)) for term in terms[:2])
            if action == "ApplyStatus":
                self.status[actor].add(effect)
            else:
                self.status[actor].discard(effect)
            return
        super().execute(line, state)

    def check_turn(self, expected, label):
        self.invoke("TurnStarted", (CASTER,))
        assert (CONTROL in self.status[CASTER]) == expected, label


def combat_fixture(spell=HOLD, slot=2):
    paths = [GOALS / name for name in ("BTAI_AdaptiveCombat.txt", "BTAI_ControlTactics.txt",
                                       "BTAI_RescueTactics.txt", "BTAI_RangedTactics.txt")]
    game = CombatFixture(rule for path in paths for rule in read_rules(path))
    for path in paths:
        init, _ = sections(path)
        for line in filter(str.strip, init.splitlines()):
            _, name, args = parse_call(line.strip())
            game.facts[name].add(tuple(map(word, args)))
    game.in_combat.update((CASTER, ENEMY))
    game.status[CASTER].add(DELEGATED)
    game.active[CASTER].add(spell)
    game.facts[PREPARED].add((CASTER, spell, "control"))
    game.facts["GetActionResourceValuePersonal"].update({
        (CASTER, "ActionPoint", 0, 1.0), (CASTER, "SpellSlot", slot, 1.0),
    })
    # BG3 performs spell-specific targeting. Supply the single returned target as a native fact.
    game.facts["CanCastSpellOnEnemyInSameCombat"].add((CASTER, spell, ENEMY))
    game.facts["CombatGetGuidFor"].update({(CASTER, "fight"), (ENEMY, "fight")})
    game.facts["GetDistanceTo"].add((CASTER, ENEMY, 18.0))
    game.facts["HasLineOfSight"].add((CASTER, ENEMY, 1))
    effect, group = EFFECTS[spell]
    game.facts["IsImmuneToStatus"].add((ENEMY, effect, CASTER, 0))
    game.facts["IsImmuneToStatusGroup"].add((ENEMY, group, CASTER, 0))
    game.facts["HasActiveStatusWithGroup"].update({
        (CASTER, "SG_Incapacitated", 0), (ENEMY, "SG_Incapacitated", 0),
        (ENEMY, group, 0),
    })
    game.facts["IsDead"].update({(CASTER, 0), (ENEMY, 0)})
    game.facts["DB_PartyMembers"].add((CASTER,))
    game.facts["GetHitpoints"].add((CASTER, 30))
    game.facts["GetMaxHitpoints"].add((CASTER, 30))
    return game


def check_control():
    game = combat_fixture()
    # The native selector can return NULL for a spell with no eligible enemy in this fight.
    # Replace one query result at a time and verify an already-active preference disappears.
    blockers = [
        ("CanCastSpellOnEnemyInSameCombat", (CASTER, HOLD), ENEMY, "NULL_00000000-0000-0000-0000-000000000000"),
        ("GetActionResourceValuePersonal", (CASTER, "ActionPoint", 0), 1.0, 0.0),
        ("GetActionResourceValuePersonal", (CASTER, "SpellSlot", 2), 1.0, 0.0),
        ("GetDistanceTo", (CASTER, ENEMY), 18.0, 18.01),
        ("HasLineOfSight", (CASTER, ENEMY), 1, 0),
        ("IsImmuneToStatus", (ENEMY, "HOLD_PERSON", CASTER), 0, 1),
        ("IsImmuneToStatusGroup", (ENEMY, "SG_Paralyzed", CASTER), 0, 1),
        ("HasActiveStatusWithGroup", (ENEMY, "SG_Incapacitated"), 0, 1),
        ("HasActiveStatusWithGroup", (ENEMY, "SG_Paralyzed"), 0, 1),
        ("HasActiveStatusWithGroup", (CASTER, "SG_Incapacitated"), 0, 1),
        ("IsDead", (ENEMY,), 0, 1),
        ("IsDead", (CASTER,), 0, 1),
    ]
    for query, args, allowed, blocked in blockers:
        game.check_turn(True, ("eligible target", query))
        rows = game.facts[query]
        rows.remove((*args, allowed))
        rows.add((*args, blocked))
        game.check_turn(False, (query, args, blocked))
        rows.remove((*args, blocked))
        rows.add((*args, allowed))
    for actor, status in [(ENEMY, "DOWNED"), (CASTER, "DOWNED"), (CASTER, "SILENCED")]:
        game.status[actor].add(status)
        game.check_turn(False, (actor, status))
        game.status[actor].remove(status)
    game.facts[PREPARED] = {(ENEMY, HOLD, "control")}
    game.check_turn(False, "only another character prepared Hold Person")
    game.facts[PREPARED].add((CASTER, HOLD, "control"))
    game.active[CASTER].remove(HOLD)
    game.check_turn(False, "stale prepared snapshot")
    game.active[CASTER].add(HOLD)
    game.check_turn(True, "prepared again")
    game.status[CASTER].remove(DELEGATED)
    game.invoke("StatusRemoved", (CASTER, DELEGATED, CASTER, 3))
    game.check_turn(False, "delegation off")

    for spell, slot, expected in [
        ("Target_Blindness", 2, True),
        ("Target_HoldMonster", 4, False),
        ("Target_HoldMonster", 5, True),
    ]:
        game = combat_fixture(spell, slot)
        game.check_turn(expected, (spell, slot))

    game = combat_fixture("Target_Blindness")
    game.active[CASTER].add(HOLD)
    game.facts[PREPARED].add((CASTER, HOLD, "control"))
    game.facts["CanCastSpellOnEnemyInSameCombat"].add((CASTER, HOLD, ENEMY))
    game.facts["IsImmuneToStatus"].add((ENEMY, "HOLD_PERSON", CASTER, 1))
    game.facts["HasActiveStatusWithGroup"].add((ENEMY, "SG_Paralyzed", 0))
    game.check_turn(True, "Blindness still qualifies when the target resists Hold Person")

    game = combat_fixture()
    game.facts["GetActionResourceValuePersonal"].remove((CASTER, "SpellSlot", 2, 1.0))
    game.facts["GetActionResourceValuePersonal"].add((CASTER, "WarlockSpellSlot", 3, 1.0))
    game.check_turn(True, "higher-level pact slot")

    # A critical caster with a viable healing spell must still receive the higher-priority rescue profile.
    game.facts["GetHitpoints"] = {(CASTER, 10)}
    game.facts["IsTagged"].update({
        (CASTER, "UNDEAD_33c625aa-6982-4c27-904f-e47029a9b140", 0),
        (CASTER, "CONSTRUCT_22e5209c-eaeb-40dc-b6ef-a371794110c2", 0),
    })
    game.active[CASTER].add("Target_CureWounds")
    game.facts[PREPARED].add((CASTER, "Target_CureWounds", "healing"))
    game.check_turn(True, "control available during emergency")
    assert RESCUE in game.status[CASTER]
    game.facts["GetHitpoints"] = {(CASTER, 30)}
    game.check_turn(True, "control after emergency")
    assert RESCUE not in game.status[CASTER]
    print("Verified crowd-control opportunities, resource and target filters, rescue coexistence and cleanup.")


if __name__ == "__main__":
    check_control()
