"""Regression checks for the shipped capability catalogue and its Osiris consumers."""
from collections import defaultdict
from pathlib import Path
import re


GOALS, = (Path(__file__).resolve().parents[1] / "mod" / "Mods").glob("*/Story/RawFiles/Goals")
CATALOG = "DB_BTAI_Catalog"
SCAN = "PROC_BTAI_ScanCapabilities"
PREPARED = "DB_BTAI_PreparedCapability"
EXAMPLES = {
    "Target_HealingWord": "healing",
    "Target_HoldPerson": "control",
    "Target_Bless": "support",
    "Projectile_Fireball": "damage",
    "Shout_ActionSurge": "support",
}


def parse_call(line):
    """Read one Osiris call, retaining its argument literals and variables."""
    match = re.fullmatch(r"(NOT )?(\w+)\((.*)\);?", line)
    assert match, f"Expected an Osiris call, found {line!r}"
    arguments = tuple(re.sub(r"^\(\w+\)", "", arg.strip())
                      for arg in match[3].split(",")) if match[3] else ()
    return match[1] is not None, match[2], arguments


def sections(path):
    source = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
    init = source.split("INITSECTION", 1)[1].split("KBSECTION", 1)[0].strip()
    kb = source.split("KBSECTION", 1)[1].split("EXITSECTION", 1)[0]
    return init, kb


def read_rules(path):
    _, kb = sections(path)
    rules = []
    chunks = re.split(r"^(IF|PROC|QRY)\s*$", kb, flags=re.M)
    for kind, block in zip(chunks[1::2], chunks[2::2]):
        when, then = re.split(r"^THEN\s*$", block, maxsplit=1, flags=re.M)
        conditions = [line.strip() for line in when.splitlines() if line.strip() and line.strip() != "AND"]
        actions = [line.strip() for line in then.splitlines() if line.strip()]
        rules.append((kind, conditions, actions))
    return rules


def catalogue():
    init, kb = sections(GOALS / "BTAI_CapabilityCatalog.txt")
    assert not kb.strip(), "The catalogue must only seed facts"
    rows = []
    for line in init.splitlines():
        row = re.fullmatch(r'DB_BTAI_Catalog\("([A-Za-z_0-9]+)",\s*"([a-z]+)"\);', line.strip())
        assert row, f"Invalid catalogue fact {line!r}"
        rows.append(row.groups())
    entries = dict(rows)
    assert len(entries) == len(rows), "An ability has duplicate or conflicting catalogue facts"
    assert set(entries.values()) == {"damage", "control", "healing", "support", "utility"}
    for ability, category in EXAMPLES.items():
        assert entries.get(ability) == category, f"{ability} should be {category}"
    return entries


def reachable(rules, root):
    """Follow both THEN procedures and query calls in condition blocks."""
    calls = defaultdict(set)
    for _, conditions, actions in rules:
        owner = parse_call(conditions[0])[1]
        for line in conditions[1:] + actions:
            match = re.match(r"(?:NOT )?(\w+)\(", line)
            if match:
                calls[owner].add(match[1])
    found = set()
    pending = [root]
    while pending:
        name = pending.pop()
        if name not in found:
            found.add(name)
            pending.extend(calls[name] - found)
    return found


def word(token):
    if token.startswith('"'):
        return token[1:-1]
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    if re.fullmatch(r"-?\d+\.\d+", token):
        return float(token)
    return token


def bind(terms, values, context):
    """Unify variables, constants and anonymous wildcards in one fact."""
    result = context.copy()
    for term, value in zip(terms, values, strict=True):
        if term == "_":
            continue
        if term.startswith("_") and term not in result:
            result[term] = value
        elif result.get(term, word(term)) != value:
            return None
    return result


class SpellbookFixture:
    """Execute the detector's calls against two small simulated character spellbooks."""

    def __init__(self, rules):
        self.rules = defaultdict(list)
        for _, conditions, actions in rules:
            _, name, head = parse_call(conditions[0])
            self.rules[name].append((head, conditions[1:], actions))
        self.facts = defaultdict(set)
        self.known = defaultdict(set)
        self.active = defaultdict(set)
        self.status = defaultdict(set)
        self.in_combat = set()
        self.passives = defaultdict(set)
        self.equipped = {}
        self.weapons = {}
        self.scores = {}

    def rows(self, name, args):
        if name.startswith("DB_"):
            return self.facts[name]
        if name in {"HasSpell", "IsSpellActive", "HasActiveStatus", "HasPassive"}:
            book = {"HasSpell": self.known, "IsSpellActive": self.active,
                    "HasActiveStatus": self.status, "HasPassive": self.passives}[name]
            actor, ability, _ = args
            return [(actor, ability, int(ability in book[actor]))]
        if name == "IsInCombat":
            return [(args[0], int(args[0] in self.in_combat))]
        if name == "GetEquippedItem":
            item = self.equipped.get(args[:2])
            return [(*args[:2], item)] if item else []
        if name == "IsWeapon":
            return [(args[0], int(args[0] in self.weapons))]
        if name == "GetStatString":
            return [(args[0], self.weapons[args[0]])] if args[0] in self.weapons else []
        if name == "GetWeaponScoreForCharacter":
            return [(*args[:2], self.scores[args[:2]])] if args[:2] in self.scores else []
        raise AssertionError(f"Unmodelled detector condition {name}")

    def matching_states(self, initial, conditions):
        states = [initial]
        for line in conditions:
            negated, condition, terms = parse_call(line)
            next_states = []
            for state in states:
                values = tuple(state.get(term, word(term)) for term in terms)
                if condition.startswith("QRY_"):
                    if self.invoke(condition, values) != negated:
                        next_states.append(state)
                    continue
                matches = [result for row in self.rows(condition, values)
                           if (result := bind(terms, row, state)) is not None]
                if not negated:
                    next_states.extend(matches)
                elif not matches:
                    next_states.append(state)
            states = next_states
        return states

    def execute(self, line, state):
        remove, action, terms = parse_call(line)
        if action == "DB_NOOP":
            return
        assert all(not term.startswith("_") or term in state for term in terms), line
        values = tuple(state.get(term, word(term)) for term in terms)
        if action.startswith("PROC_BTAI_"):
            assert self.rules[action], f"Undefined detector procedure {action}"
            self.invoke(action, values)
        else:
            assert action.startswith("DB_BTAI_"), f"Unexpected detector side effect {action}"
            if remove:
                self.facts[action].discard(values)
            else:
                self.facts[action].add(values)

    def invoke(self, name, args):
        matched = False
        for head, conditions, actions in self.rules[name]:
            initial = bind(head, args, {})
            if initial is None:
                continue
            for state in self.matching_states(initial, conditions):
                matched = True
                for line in actions:
                    self.execute(line, state)
        return matched

    def prepared(self, actor):
        return {(spell, category) for owner, spell, category in self.facts[PREPARED] if owner == actor}


def check_capabilities():
    entries = catalogue()
    paths = list(GOALS.glob("*.txt"))
    rules = [rule for path in paths for rule in read_rules(path)]
    clear = "PROC_BTAI_ClearCapabilities"
    detector = reachable(rules, SCAN) | reachable(rules, clear)
    detector.add("PROC_BTAI_RefreshEnabledCapabilities")
    # Follow every possible call from TurnStarted, including queries in tactical rules.
    costly = {SCAN, CATALOG, "DB_BTAI_PassiveCandidate", "PROC_BTAI_ScanPassives"}
    assert not (reachable(rules, "TurnStarted") & costly), "TurnStarted reaches a full catalogue scan"
    # Run only snapshot handlers; the native combat scorer is a separate subsystem.
    relevant = []
    for path in (GOALS / "BTAI_CapabilityDetection.txt", GOALS / "BTAI_PassiveDetection.txt"):
        for _, _, actions in read_rules(path):
            for line in actions:
                _, action, _ = parse_call(line)
                assert action == "DB_NOOP" or action.startswith(("PROC_BTAI_", "DB_BTAI_")), line
    for kind, conditions, actions in rules:
        if kind == "IF":
            actions = [line for line in actions if parse_call(line)[1] in detector]
            if actions:
                relevant.append((kind, conditions, actions))
        elif parse_call(conditions[0])[1] in detector:
            relevant.append((kind, conditions, actions))
    game = SpellbookFixture(relevant)
    for path in paths:
        init, _ = sections(path)
        for line in filter(str.strip, init.splitlines()):
            _, name, args = parse_call(line.strip())
            if name in {CATALOG, "DB_BTAI_PassiveCandidate", "DB_BTAI_WeaponSlot"}:
                game.facts[name].add(tuple(map(word, args)))

    actor, other = "actor", "other"
    enabled, controlled = "BTAI_ENABLED", "BTAI_CONTROLLED"
    heal, hold, bless, fire, surge = EXAMPLES
    archery, martial = "FightingStyle_Archery", "MartialArts_UnarmedDamage"
    assert {(archery,), (martial,)} <= game.facts["DB_BTAI_PassiveCandidate"]
    game.facts["DB_PartyMembers"].update({(actor,), (other,)})
    game.known[actor].update((heal, hold, surge))
    # An unowned ability must be ignored even if a native active-bit probe returns true.
    game.active[actor].update((heal, fire))
    game.passives[actor].add(archery)
    game.known[other].update((bless, fire))
    game.active[other].add(fire)
    slot = "Ranged Main Weapon"
    game.weapons.update({"first-bow": "WPN_TestBow", "better-bow": "WPN_TestBowPlus"})
    game.scores.update({("first-bow", actor): 7.0, ("better-bow", actor): 12.0})
    game.equipped[actor, slot] = "first-bow"

    def snapshot(character):
        return {db: {row for row in game.facts[db] if row[0] == character}
                for db in (PREPARED, "DB_BTAI_OwnedCapability", "DB_BTAI_KnownPassive",
                           "DB_BTAI_WeaponScore", "DB_BTAI_Scanned")}

    def event(name, *args):
        game.invoke(name, args)

    def toggle_on(character):
        game.status[character].add(enabled)
        event("StatusApplied", character, enabled, character, 1)

    # Nondelegated actors stay untracked through ordinary equipment and level changes.
    event("StatusApplied", actor, "BLESS", actor, 1)
    event("Equipped", "first-bow", actor)
    event("LeveledUp", actor)
    assert not any(snapshot(actor).values())
    toggle_on(actor)
    assert game.prepared(actor) == {(heal, "healing")}
    assert game.facts["DB_BTAI_OwnedCapability"] == {
        (actor, spell, entries[spell]) for spell in (heal, hold, surge)}
    assert snapshot(actor)["DB_BTAI_KnownPassive"] == {(actor, archery)}
    assert snapshot(actor)["DB_BTAI_WeaponScore"] == {(actor, slot, "WPN_TestBow", 7.0)}
    assert snapshot(actor)["DB_BTAI_Scanned"] == {(actor,)}
    toggle_on(other)
    assert game.prepared(other) == {(fire, "damage")}
    game.known[other].add(heal)
    game.active[other].add(heal)
    event("LearnedSpell", other, heal)
    assert game.prepared(other) == {(fire, "damage"), (heal, "healing")}
    other_before = snapshot(other)

    # Combat entry picks up manual preparation changes, even without a learned-spell event.
    game.active[actor] = {hold}
    game.in_combat.add(actor)
    game.status[actor].add(controlled)
    event("StatusApplied", actor, controlled, actor, 2)
    assert game.prepared(actor) == {(hold, "control")}

    # A respec removes old ownership, preparation and passive rows on the same character.
    game.known[actor] = {surge, bless}
    game.active[actor] = {bless}
    game.passives[actor] = {martial}
    event("RespecCompleted", actor)
    assert game.prepared(actor) == {(bless, "support")}
    assert snapshot(actor)["DB_BTAI_OwnedCapability"] == {
        (actor, spell, entries[spell]) for spell in (surge, bless)}
    assert snapshot(actor)["DB_BTAI_KnownPassive"] == {(actor, martial)}

    game.equipped[actor, slot] = "better-bow"
    event("Equipped", "better-bow", actor)
    assert snapshot(actor)["DB_BTAI_WeaponScore"] == {(actor, slot, "WPN_TestBowPlus", 12.0)}
    del game.equipped[actor, slot]
    event("Unequipped", "better-bow", actor)
    assert not snapshot(actor)["DB_BTAI_WeaponScore"]
    game.equipped[actor, slot] = "nonweapon"
    event("Equipped", "nonweapon", actor)
    assert not snapshot(actor)["DB_BTAI_WeaponScore"]

    game.status[actor].discard(enabled)
    event("StatusRemoved", actor, enabled, actor, 3)
    assert not any(snapshot(actor).values()), "OFF must clear every actor-scoped row"
    event("LearnedSpell", actor, fire)
    event("LevelGameplayStarted", "WLD_Main_A", 1)
    assert not any(snapshot(actor).values()), "Ordinary events must not track an OFF actor"
    # Reconcile saved rows when a load delivers no status-applied/removed event.
    game.facts["DB_BTAI_Scanned"].add((actor,))
    game.facts[PREPARED].add((actor, hold, "control"))
    game.facts[PREPARED].discard((other, fire, "damage"))
    event("LevelGameplayStarted", "WLD_Main_A", 1)
    assert not any(snapshot(actor).values())

    assert snapshot(other) == other_before, "A refresh or OFF altered a second character's snapshot"
    event("StatusRemoved", other, controlled, other, 4)
    assert snapshot(other) == other_before, "Ending combat must preserve an enabled actor's snapshot"

    # Legacy saves can carry temporary AI control without the persistent enabled status.
    event("StatusApplied", actor, controlled, actor, 5)
    assert snapshot(actor)["DB_BTAI_Scanned"] == {(actor,)}
    game.status[actor].discard(controlled)
    event("StatusRemoved", actor, controlled, actor, 5)
    assert not any(snapshot(actor).values()), "Removing legacy temporary control must clean its snapshot"
    passives = len(game.facts["DB_BTAI_PassiveCandidate"])
    print(f"Verified {len(entries)} capability records, {passives} passive candidates and actor weapon scores.")


if __name__ == "__main__":
    check_capabilities()
