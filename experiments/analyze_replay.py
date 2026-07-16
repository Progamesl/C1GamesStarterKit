#!/usr/bin/env python3
"""Summarize a Terminal newline-delimited JSON replay.

The first non-empty line of a replay is normally the game configuration.  The
remaining lines are turn-start (turnInfo[0] == 0), action-frame (== 1), and
end-game (== 2) records.  This tool intentionally reads the unit definitions
from the replay instead of assuming a particular season's unit names or costs.

Examples:
    python3 experiments/analyze_replay.py match.replay
    python3 experiments/analyze_replay.py match.replay --json > summary.json
    python3 experiments/analyze_replay.py match.replay --compact
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


Number = float
Location = Tuple[int, int]


def _round(value: Number, digits: int = 3) -> Number:
    rounded = round(float(value), digits)
    return int(rounded) if rounded.is_integer() else rounded


def _loc(raw: Sequence[Any]) -> Location:
    return int(raw[0]), int(raw[1])


def _loc_list(location: Location) -> List[int]:
    return [location[0], location[1]]


def _sorted_counter(counter: Counter) -> Dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _stats(record: Dict[str, Any], player: int) -> Optional[Dict[str, Number]]:
    raw = record.get(f"p{player}Stats")
    if not raw or len(raw) < 3:
        return None
    return {
        "health": _round(raw[0]),
        "SP": _round(raw[1]),
        "MP": _round(raw[2]),
        "time_ms": _round(raw[3]) if len(raw) > 3 else 0,
    }


@dataclass
class UnitDefinition:
    index: int
    shorthand: str
    display: str
    category: Optional[int]
    cost_sp: Number
    cost_mp: Number
    upgrade_cost_sp: Number
    upgrade_cost_mp: Number
    start_health: Number
    attack_range: Number
    upgrade_attack_range: Number

    @property
    def stationary(self) -> bool:
        return self.category == 0

    @property
    def mobile(self) -> bool:
        return self.category == 1

    @property
    def role(self) -> str:
        lowered = f"{self.display} {self.shorthand}".lower()
        if self.category == 0:
            return "structure"
        if self.category == 1:
            return "mobile"
        if "remove" in lowered or self.shorthand.upper() == "RM":
            return "remove"
        if "upgrade" in lowered or self.shorthand.upper() == "UP":
            return "upgrade"
        return "meta"


@dataclass
class UnitIdentity:
    owner: int
    type_index: int
    location: Location


@dataclass
class Wave:
    turn: int
    owner: int
    type_index: int
    origin: Location
    unit_ids: List[str] = field(default_factory=list)
    breaches: List[Location] = field(default_factory=list)
    deaths: int = 0
    self_destruct_or_removed: int = 0
    shield_events: int = 0
    shield_amount: Number = 0
    attacks_mobile: int = 0
    attacks_structure: int = 0
    structure_damage: Number = 0
    structures_destroyed: Counter = field(default_factory=Counter)
    path_by_id: Dict[str, List[Location]] = field(default_factory=lambda: defaultdict(list))

    @property
    def count(self) -> int:
        return len(self.unit_ids)


@dataclass
class TurnAccumulator:
    turn: int
    start_record: Optional[Dict[str, Any]] = None
    action_records: List[Dict[str, Any]] = field(default_factory=list)
    end_record: Optional[Dict[str, Any]] = None
    structures_built: Dict[int, Counter] = field(
        default_factory=lambda: {1: Counter(), 2: Counter()}
    )
    build_locations: Dict[int, Dict[str, List[Location]]] = field(
        default_factory=lambda: {
            1: defaultdict(list),
            2: defaultdict(list),
        }
    )
    upgrades: Dict[int, Counter] = field(
        default_factory=lambda: {1: Counter(), 2: Counter()}
    )
    upgrade_locations: Dict[int, List[Location]] = field(
        default_factory=lambda: {1: [], 2: []}
    )
    removals: Dict[int, Counter] = field(
        default_factory=lambda: {1: Counter(), 2: Counter()}
    )
    removal_locations: Dict[int, List[Location]] = field(
        default_factory=lambda: {1: [], 2: []}
    )
    structure_damage: Dict[int, Number] = field(
        default_factory=lambda: {1: 0, 2: 0}
    )
    damaged_structures: Dict[int, Dict[str, Dict[str, Any]]] = field(
        default_factory=lambda: {1: {}, 2: {}}
    )
    structure_deaths: Dict[int, Counter] = field(
        default_factory=lambda: {1: Counter(), 2: Counter()}
    )
    structure_death_details: Dict[int, List[Dict[str, Any]]] = field(
        default_factory=lambda: {1: [], 2: []}
    )
    breaches: Dict[int, List[Dict[str, Any]]] = field(
        default_factory=lambda: {1: [], 2: []}
    )
    shield_events: Dict[int, int] = field(
        default_factory=lambda: {1: 0, 2: 0}
    )
    shield_amount: Dict[int, Number] = field(
        default_factory=lambda: {1: 0, 2: 0}
    )
    event_counts: Counter = field(default_factory=Counter)
    waves: Dict[Tuple[int, int, Location], Wave] = field(default_factory=dict)
    wave_by_unit_id: Dict[str, Wave] = field(default_factory=dict)


class ReplayAnalyzer:
    def __init__(self, path: str):
        self.path = path
        self.config: Dict[str, Any] = {}
        self.records: List[Dict[str, Any]] = []
        self.parse_warnings: List[str] = []
        self.units: List[UnitDefinition] = []
        self.identities: Dict[str, UnitIdentity] = {}
        self.turns: Dict[int, TurnAccumulator] = {}
        self.end_record: Optional[Dict[str, Any]] = None

    def load(self) -> None:
        with open(self.path, encoding="utf-8") as replay_file:
            for line_number, raw_line in enumerate(replay_file, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{self.path}:{line_number}: invalid JSON: {exc}"
                    ) from exc
                if not isinstance(record, dict):
                    self.parse_warnings.append(
                        f"line {line_number}: ignored non-object JSON value"
                    )
                    continue
                if "turnInfo" not in record:
                    if not self.config and "unitInformation" in record:
                        self.config = record
                    else:
                        self.parse_warnings.append(
                            f"line {line_number}: ignored object without turnInfo"
                        )
                    continue
                record["_line_number"] = line_number
                self.records.append(record)

        if not self.config:
            raise ValueError("replay has no configuration record")
        if not self.records:
            raise ValueError("replay has no state records")
        self._load_unit_definitions()

    def _load_unit_definitions(self) -> None:
        self.units = []
        for index, raw in enumerate(self.config.get("unitInformation", [])):
            upgrade = raw.get("upgrade") or {}
            base_sp = raw.get("cost1", 0)
            base_mp = raw.get("cost2", 0)
            self.units.append(
                UnitDefinition(
                    index=index,
                    shorthand=str(raw.get("shorthand", index)),
                    display=str(raw.get("display", raw.get("shorthand", index))),
                    category=raw.get("unitCategory"),
                    cost_sp=base_sp,
                    cost_mp=base_mp,
                    upgrade_cost_sp=upgrade.get("cost1", base_sp),
                    upgrade_cost_mp=upgrade.get("cost2", base_mp),
                    start_health=raw.get("startHealth", 0),
                    attack_range=raw.get("attackRange", 0),
                    upgrade_attack_range=upgrade.get(
                        "attackRange", raw.get("attackRange", 0)
                    ),
                )
            )

    def unit(self, type_index: int) -> UnitDefinition:
        if 0 <= type_index < len(self.units):
            return self.units[type_index]
        return UnitDefinition(
            index=type_index,
            shorthand=f"type_{type_index}",
            display=f"type_{type_index}",
            category=None,
            cost_sp=0,
            cost_mp=0,
            upgrade_cost_sp=0,
            upgrade_cost_mp=0,
            start_health=0,
            attack_range=0,
            upgrade_attack_range=0,
        )

    def analyze(self) -> Dict[str, Any]:
        self._index_unit_identities()
        self._group_records()
        self._process_events()

        turn_summaries = [
            self._summarize_turn(self.turns[turn])
            for turn in sorted(self.turns)
        ]
        waves = [
            wave
            for turn in sorted(self.turns)
            for wave in sorted(
                self.turns[turn].waves.values(),
                key=lambda item: (item.owner, item.type_index, item.origin),
            )
        ]
        summary = {
            "schema_version": 1,
            "replay": os.path.abspath(self.path),
            "line_count": max(
                (record["_line_number"] for record in self.records), default=0
            ),
            "config": self._config_summary(),
            "result": self._result_summary(),
            "aggregate": self._aggregate_summary(turn_summaries, waves),
            "waves": [self._wave_summary(wave) for wave in waves],
            "turns": turn_summaries,
            "warnings": self.parse_warnings,
        }
        return summary

    def _index_unit_identities(self) -> None:
        # Snapshots are the most reliable type source, including the new unit id
        # assigned when a structure is upgraded.
        for record in self.records:
            for owner in (1, 2):
                groups = record.get(f"p{owner}Units", [])
                for type_index, group in enumerate(groups):
                    unit_def = self.unit(type_index)
                    if unit_def.role in {"remove", "upgrade"}:
                        continue
                    for raw_unit in group:
                        if len(raw_unit) < 4:
                            continue
                        self.identities[str(raw_unit[3])] = UnitIdentity(
                            owner=owner,
                            type_index=type_index,
                            location=_loc(raw_unit),
                        )

        # A mobile can spawn and disappear before a useful snapshot in malformed
        # or abbreviated replays, so fill any remaining identities from events.
        for record in self.records:
            for spawn in record.get("events", {}).get("spawn", []):
                if len(spawn) < 4:
                    continue
                location, type_index, unit_id, owner = (
                    _loc(spawn[0]),
                    int(spawn[1]),
                    str(spawn[2]),
                    int(spawn[3]),
                )
                if self.unit(type_index).role in {"structure", "mobile"}:
                    self.identities.setdefault(
                        unit_id,
                        UnitIdentity(owner, type_index, location),
                    )

    def _group_records(self) -> None:
        for record in self.records:
            turn_info = record.get("turnInfo", [])
            if len(turn_info) < 2:
                self.parse_warnings.append(
                    f"line {record['_line_number']}: short turnInfo"
                )
                continue
            phase, turn = int(turn_info[0]), int(turn_info[1])
            accumulator = self.turns.setdefault(turn, TurnAccumulator(turn))
            if phase == 0:
                accumulator.start_record = record
            elif phase == 1:
                accumulator.action_records.append(record)
            elif phase == 2:
                accumulator.end_record = record
                self.end_record = record
            else:
                self.parse_warnings.append(
                    f"line {record['_line_number']}: unknown phase {phase}"
                )

    def _process_events(self) -> None:
        for turn in sorted(self.turns):
            accumulator = self.turns[turn]
            for record in accumulator.action_records:
                events = record.get("events") or {}
                for event_name, values in events.items():
                    accumulator.event_counts[event_name] += len(values or [])
                self._process_spawns(accumulator, events.get("spawn", []))
                self._process_moves(accumulator, events.get("move", []))
                self._process_shields(accumulator, events.get("shield", []))
                attack_sources = self._process_attacks(
                    accumulator, events.get("attack", [])
                )
                self._process_damage(
                    accumulator, events.get("damage", []), attack_sources
                )
                self._process_deaths(
                    accumulator, events.get("death", []), attack_sources
                )
                self._process_breaches(accumulator, events.get("breach", []))

    def _structure_type_at(
        self, record: Dict[str, Any], owner: int, location: Location
    ) -> Optional[int]:
        groups = record.get(f"p{owner}Units", [])
        for type_index, group in enumerate(groups):
            if not self.unit(type_index).stationary:
                continue
            if any(_loc(raw_unit) == location for raw_unit in group):
                return type_index
        identity_matches = [
            identity.type_index
            for identity in self.identities.values()
            if identity.owner == owner and identity.location == location
            and self.unit(identity.type_index).stationary
        ]
        return identity_matches[-1] if identity_matches else None

    def _process_spawns(
        self, accumulator: TurnAccumulator, spawns: Iterable[Sequence[Any]]
    ) -> None:
        first_record = (
            accumulator.action_records[0]
            if accumulator.action_records
            else accumulator.start_record or {}
        )
        for spawn in spawns:
            if len(spawn) < 4:
                continue
            location, type_index, unit_id, owner = (
                _loc(spawn[0]),
                int(spawn[1]),
                str(spawn[2]),
                int(spawn[3]),
            )
            unit_def = self.unit(type_index)
            if owner not in (1, 2):
                continue
            if unit_def.role == "structure":
                accumulator.structures_built[owner][unit_def.shorthand] += 1
                accumulator.build_locations[owner][unit_def.shorthand].append(
                    location
                )
            elif unit_def.role == "mobile":
                key = (owner, type_index, location)
                wave = accumulator.waves.setdefault(
                    key, Wave(accumulator.turn, owner, type_index, location)
                )
                wave.unit_ids.append(unit_id)
                accumulator.wave_by_unit_id[unit_id] = wave
                wave.path_by_id[unit_id].append(location)
            elif unit_def.role == "upgrade":
                target_type = self._structure_type_at(
                    first_record, owner, location
                )
                shorthand = (
                    self.unit(target_type).shorthand
                    if target_type is not None
                    else "unknown"
                )
                accumulator.upgrades[owner][shorthand] += 1
                accumulator.upgrade_locations[owner].append(location)
            elif unit_def.role == "remove":
                target_type = self._structure_type_at(
                    accumulator.start_record or first_record, owner, location
                )
                shorthand = (
                    self.unit(target_type).shorthand
                    if target_type is not None
                    else "unknown"
                )
                accumulator.removals[owner][shorthand] += 1
                accumulator.removal_locations[owner].append(location)

    def _process_moves(
        self, accumulator: TurnAccumulator, moves: Iterable[Sequence[Any]]
    ) -> None:
        for move in moves:
            if len(move) < 6:
                continue
            destination = _loc(move[1])
            unit_id = str(move[4])
            wave = accumulator.wave_by_unit_id.get(unit_id)
            if wave is not None:
                path = wave.path_by_id[unit_id]
                if not path or path[-1] != destination:
                    path.append(destination)

    def _process_shields(
        self, accumulator: TurnAccumulator, shields: Iterable[Sequence[Any]]
    ) -> None:
        for shield in shields:
            if len(shield) < 7:
                continue
            amount, target_id, owner = shield[2], str(shield[5]), int(shield[6])
            if owner not in (1, 2):
                continue
            accumulator.shield_events[owner] += 1
            accumulator.shield_amount[owner] += float(amount)
            wave = accumulator.wave_by_unit_id.get(target_id)
            if wave is not None:
                wave.shield_events += 1
                wave.shield_amount += float(amount)

    def _process_attacks(
        self, accumulator: TurnAccumulator, attacks: Iterable[Sequence[Any]]
    ) -> Dict[str, Dict[str, Any]]:
        sources: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"queue": deque(), "last": None}
        )
        for attack in attacks:
            if len(attack) < 7:
                continue
            target_type = int(attack[2])
            source_id, target_id = str(attack[4]), str(attack[5])
            sources[target_id]["queue"].append(source_id)
            sources[target_id]["last"] = source_id
            wave = accumulator.wave_by_unit_id.get(source_id)
            if wave is None:
                continue
            target_def = self.unit(target_type)
            if target_def.stationary:
                wave.attacks_structure += 1
            elif target_def.mobile:
                wave.attacks_mobile += 1
        return sources

    def _process_damage(
        self,
        accumulator: TurnAccumulator,
        damages: Iterable[Sequence[Any]],
        attack_sources: Dict[str, Dict[str, Any]],
    ) -> None:
        for damage in damages:
            if len(damage) < 5:
                continue
            location, amount, target_id, owner = (
                _loc(damage[0]),
                float(damage[1]),
                str(damage[3]),
                int(damage[4]),
            )
            identity = self.identities.get(target_id)
            if owner not in (1, 2) or identity is None:
                continue
            target_def = self.unit(identity.type_index)
            if not target_def.stationary:
                continue
            accumulator.structure_damage[owner] += amount
            detail = accumulator.damaged_structures[owner].setdefault(
                target_id,
                {
                    "id": target_id,
                    "type": target_def.shorthand,
                    "location": _loc_list(location),
                    "damage": 0,
                },
            )
            detail["damage"] = _round(detail["damage"] + amount)
            # Attack and damage events are emitted in matching order for normal
            # attacks.  Pair by target id so simultaneous attackers are not all
            # credited with every damage event.  Self-destruct/melee damage has
            # no matching attack event and therefore remains unattributed.
            source_queue = attack_sources.get(target_id, {}).get("queue")
            source_id = source_queue.popleft() if source_queue else None
            wave = accumulator.wave_by_unit_id.get(source_id)
            if wave is not None:
                wave.structure_damage += amount

    def _process_deaths(
        self,
        accumulator: TurnAccumulator,
        deaths: Iterable[Sequence[Any]],
        attack_sources: Dict[str, Dict[str, Any]],
    ) -> None:
        for death in deaths:
            if len(death) < 5:
                continue
            location, type_index, unit_id, owner, special = (
                _loc(death[0]),
                int(death[1]),
                str(death[2]),
                int(death[3]),
                bool(death[4]),
            )
            unit_def = self.unit(type_index)
            if owner not in (1, 2):
                continue
            if unit_def.stationary:
                accumulator.structure_deaths[owner][unit_def.shorthand] += 1
                accumulator.structure_death_details[owner].append(
                    {
                        "id": unit_id,
                        "type": unit_def.shorthand,
                        "location": _loc_list(location),
                        # The replay schema does not name this boolean.  It is
                        # true for completed removals in known engine output,
                        # but may also cover self-destruction in other configs.
                        "special_death_flag": special,
                    }
                )
                source_id = attack_sources.get(unit_id, {}).get("last")
                wave = accumulator.wave_by_unit_id.get(source_id)
                if wave is not None:
                    wave.structures_destroyed[unit_def.shorthand] += 1
            elif unit_def.mobile:
                wave = accumulator.wave_by_unit_id.get(unit_id)
                if wave is not None:
                    wave.deaths += 1
                    if special:
                        wave.self_destruct_or_removed += 1

    def _process_breaches(
        self, accumulator: TurnAccumulator, breaches: Iterable[Sequence[Any]]
    ) -> None:
        for breach in breaches:
            if len(breach) < 5:
                continue
            location, damage, type_index, unit_id, owner = (
                _loc(breach[0]),
                float(breach[1]),
                int(breach[2]),
                str(breach[3]),
                int(breach[4]),
            )
            if owner not in (1, 2):
                continue
            accumulator.breaches[owner].append(
                {
                    "location": _loc_list(location),
                    "damage": _round(damage),
                    "type": self.unit(type_index).shorthand,
                    "id": unit_id,
                }
            )
            wave = accumulator.wave_by_unit_id.get(unit_id)
            if wave is not None:
                wave.breaches.append(location)

    def _snapshot(
        self, record: Optional[Dict[str, Any]], owner: int
    ) -> Dict[str, Any]:
        if not record:
            return {
                "counts": {},
                "upgraded": 0,
                "pending_removal": 0,
                "damaged": [],
                "locations": {},
            }
        groups = record.get(f"p{owner}Units", [])
        upgraded_ids = set()
        pending_ids = set()
        for type_index, group in enumerate(groups):
            role = self.unit(type_index).role
            if role == "upgrade":
                upgraded_ids.update(str(unit[3]) for unit in group if len(unit) > 3)
            elif role == "remove":
                pending_ids.update(str(unit[3]) for unit in group if len(unit) > 3)

        counts = Counter()
        locations: Dict[str, List[List[int]]] = defaultdict(list)
        damaged = []
        for type_index, group in enumerate(groups):
            unit_def = self.unit(type_index)
            if not unit_def.stationary:
                continue
            counts[unit_def.shorthand] += len(group)
            for raw_unit in group:
                location = _loc(raw_unit)
                locations[unit_def.shorthand].append(_loc_list(location))
                if len(raw_unit) < 4:
                    continue
                unit_id, health = str(raw_unit[3]), float(raw_unit[2])
                upgraded = unit_id in upgraded_ids
                expected_health = unit_def.start_health
                if upgraded:
                    expected_health = (
                        self.config["unitInformation"][type_index]
                        .get("upgrade", {})
                        .get("startHealth", expected_health)
                    )
                if health + 1e-9 < float(expected_health):
                    damaged.append(
                        {
                            "id": unit_id,
                            "type": unit_def.shorthand,
                            "location": _loc_list(location),
                            "health": _round(health),
                            "max_health": _round(expected_health),
                        }
                    )
        return {
            "counts": _sorted_counter(counts),
            "upgraded": len(upgraded_ids),
            "pending_removal": len(pending_ids),
            "damaged": sorted(
                damaged, key=lambda item: (item["type"], item["location"])
            ),
            "locations": {
                key: sorted(value) for key, value in sorted(locations.items())
            },
        }

    def _resource_spend(
        self, accumulator: TurnAccumulator, owner: int
    ) -> Dict[str, Number]:
        sp = 0.0
        mp = 0.0
        for shorthand, count in accumulator.structures_built[owner].items():
            unit_def = next(
                (unit for unit in self.units if unit.shorthand == shorthand),
                None,
            )
            if unit_def:
                sp += float(unit_def.cost_sp) * count
                mp += float(unit_def.cost_mp) * count
        for wave in accumulator.waves.values():
            if wave.owner != owner:
                continue
            unit_def = self.unit(wave.type_index)
            sp += float(unit_def.cost_sp) * wave.count
            mp += float(unit_def.cost_mp) * wave.count
        for shorthand, count in accumulator.upgrades[owner].items():
            unit_def = next(
                (unit for unit in self.units if unit.shorthand == shorthand),
                None,
            )
            if unit_def:
                sp += float(unit_def.upgrade_cost_sp) * count
                mp += float(unit_def.upgrade_cost_mp) * count
        return {"SP": _round(sp), "MP": _round(mp)}

    def _summarize_turn(self, accumulator: TurnAccumulator) -> Dict[str, Any]:
        action_first = (
            accumulator.action_records[0]
            if accumulator.action_records
            else accumulator.end_record
        )
        action_last = (
            accumulator.action_records[-1]
            if accumulator.action_records
            else accumulator.end_record
        )
        result: Dict[str, Any] = {
            "turn": accumulator.turn,
            "frames": len(accumulator.action_records),
            "event_counts": _sorted_counter(accumulator.event_counts),
            "players": {},
        }
        for owner in (1, 2):
            breaches = accumulator.breaches[owner]
            result["players"][f"P{owner}"] = {
                "start": _stats(accumulator.start_record or action_first or {}, owner),
                "post_action": _stats(action_first or {}, owner),
                "end": _stats(action_last or {}, owner),
                "estimated_spend": self._resource_spend(accumulator, owner),
                "structures_start": self._snapshot(
                    accumulator.start_record, owner
                ),
                "structures_end": self._snapshot(action_last, owner),
                "structures_built": _sorted_counter(
                    accumulator.structures_built[owner]
                ),
                "build_locations": {
                    key: [_loc_list(location) for location in value]
                    for key, value in sorted(
                        accumulator.build_locations[owner].items()
                    )
                },
                "upgrades": _sorted_counter(accumulator.upgrades[owner]),
                "upgrade_locations": [
                    _loc_list(location)
                    for location in accumulator.upgrade_locations[owner]
                ],
                "removals_marked": _sorted_counter(
                    accumulator.removals[owner]
                ),
                "removal_locations": [
                    _loc_list(location)
                    for location in accumulator.removal_locations[owner]
                ],
                "structure_damage_taken": _round(
                    accumulator.structure_damage[owner]
                ),
                "damaged_structure_events": sorted(
                    accumulator.damaged_structures[owner].values(),
                    key=lambda item: (item["type"], item["location"], item["id"]),
                ),
                "structure_deaths": _sorted_counter(
                    accumulator.structure_deaths[owner]
                ),
                "structure_death_details": accumulator.structure_death_details[
                    owner
                ],
                "breach_count": len(breaches),
                "breach_damage_dealt": _round(
                    sum(float(item["damage"]) for item in breaches)
                ),
                "breaches": breaches,
                "shield_events": accumulator.shield_events[owner],
                "shield_amount": _round(accumulator.shield_amount[owner]),
            }
        return result

    def _wave_summary(self, wave: Wave) -> Dict[str, Any]:
        paths = list(wave.path_by_id.values())
        representative_path = max(paths, key=len) if paths else []
        return {
            "turn": wave.turn,
            "owner": f"P{wave.owner}",
            "type": self.unit(wave.type_index).shorthand,
            "display": self.unit(wave.type_index).display,
            "origin": _loc_list(wave.origin),
            "count": wave.count,
            "MP_spent": _round(
                wave.count * float(self.unit(wave.type_index).cost_mp)
            ),
            "breach_count": len(wave.breaches),
            "breach_locations": [
                _loc_list(location) for location in wave.breaches
            ],
            "deaths": wave.deaths,
            "special_death_flag_count": wave.self_destruct_or_removed,
            "shield_events": wave.shield_events,
            "shield_amount": _round(wave.shield_amount),
            "attacks_mobile": wave.attacks_mobile,
            "attacks_structure": wave.attacks_structure,
            "attributed_structure_damage": _round(wave.structure_damage),
            "attributed_structures_destroyed": _sorted_counter(
                wave.structures_destroyed
            ),
            "representative_path": [
                _loc_list(location) for location in representative_path
            ],
        }

    def _config_summary(self) -> Dict[str, Any]:
        resources = self.config.get("resources", {})
        return {
            "season_compatibility": {
                "P1": self.config.get("seasonCompatibilityModeP1"),
                "P2": self.config.get("seasonCompatibilityModeP2"),
            },
            "starting_health": resources.get("startingHP"),
            "starting_SP": resources.get("startingCores"),
            "starting_MP": resources.get("startingBits"),
            "SP_per_round": resources.get("coresPerRound"),
            "MP_per_round": resources.get("bitsPerRound"),
            "MP_decay_per_round": resources.get("bitDecayPerRound"),
            "units": [
                {
                    "index": unit.index,
                    "shorthand": unit.shorthand,
                    "display": unit.display,
                    "role": unit.role,
                    "cost_SP": unit.cost_sp,
                    "cost_MP": unit.cost_mp,
                    "upgrade_cost_SP": unit.upgrade_cost_sp,
                    "upgrade_cost_MP": unit.upgrade_cost_mp,
                }
                for unit in self.units
            ],
        }

    def _result_summary(self) -> Dict[str, Any]:
        final_record = self.end_record or self.records[-1]
        end_stats = final_record.get("endStats") or {}
        winner = end_stats.get("winner")
        p1 = _stats(final_record, 1)
        p2 = _stats(final_record, 2)
        if winner is None and p1 and p2:
            if p1["health"] > p2["health"]:
                winner = 1
            elif p2["health"] > p1["health"]:
                winner = 2
        return {
            "winner": f"P{winner}" if winner in (1, 2) else None,
            "final_turn": int(final_record.get("turnInfo", [0, 0])[1]),
            "final_P1": p1,
            "final_P2": p2,
            "end_stats": end_stats or None,
        }

    def _aggregate_summary(
        self, turns: List[Dict[str, Any]], waves: List[Wave]
    ) -> Dict[str, Any]:
        aggregate: Dict[str, Any] = {"players": {}}
        for owner in (1, 2):
            player_key = f"P{owner}"
            player_turns = [turn["players"][player_key] for turn in turns]
            player_waves = [wave for wave in waves if wave.owner == owner]
            built = Counter()
            upgrades = Counter()
            removals = Counter()
            deaths = Counter()
            for player_turn in player_turns:
                built.update(player_turn["structures_built"])
                upgrades.update(player_turn["upgrades"])
                removals.update(player_turn["removals_marked"])
                deaths.update(player_turn["structure_deaths"])
            aggregate["players"][player_key] = {
                "structure_builds": _sorted_counter(built),
                "upgrades": _sorted_counter(upgrades),
                "removals_marked": _sorted_counter(removals),
                "structure_deaths": _sorted_counter(deaths),
                "structure_damage_taken": _round(
                    sum(
                        float(player_turn["structure_damage_taken"])
                        for player_turn in player_turns
                    )
                ),
                "mobile_units_spawned": sum(wave.count for wave in player_waves),
                "mobile_by_type": _sorted_counter(
                    Counter(
                        {
                            self.unit(type_index).shorthand: sum(
                                wave.count
                                for wave in player_waves
                                if wave.type_index == type_index
                            )
                            for type_index in {
                                wave.type_index for wave in player_waves
                            }
                        }
                    )
                ),
                "mobile_MP_spent_from_events": _round(
                    sum(
                        wave.count
                        * float(self.unit(wave.type_index).cost_mp)
                        for wave in player_waves
                    )
                ),
                "breaches": sum(
                    player_turn["breach_count"] for player_turn in player_turns
                ),
                "breach_damage_dealt": _round(
                    sum(
                        float(player_turn["breach_damage_dealt"])
                        for player_turn in player_turns
                    )
                ),
                "shield_events": sum(
                    player_turn["shield_events"] for player_turn in player_turns
                ),
                "shield_amount": _round(
                    sum(
                        float(player_turn["shield_amount"])
                        for player_turn in player_turns
                    )
                ),
                "max_start_MP": _round(
                    max(
                        (
                            float(player_turn["start"]["MP"])
                            for player_turn in player_turns
                            if player_turn["start"]
                        ),
                        default=0,
                    )
                ),
            }
        return aggregate


def _format_counts(counts: Dict[str, int]) -> str:
    return ",".join(f"{key}:{value}" for key, value in counts.items()) or "-"


def _format_stats(stats: Optional[Dict[str, Number]]) -> str:
    if not stats:
        return "-"
    return "HP={health} SP={SP} MP={MP}".format(**stats)


def _print_text(summary: Dict[str, Any], compact: bool = False) -> None:
    result = summary["result"]
    print(
        f"Replay: {summary['replay']} ({summary['line_count']} lines)\n"
        f"Result: {result['winner'] or 'unknown'} on turn "
        f"{result['final_turn']}; "
        f"P1 {_format_stats(result['final_P1'])}; "
        f"P2 {_format_stats(result['final_P2'])}"
    )
    for player_key in ("P1", "P2"):
        player = summary["aggregate"]["players"][player_key]
        print(
            f"{player_key} aggregate: builds "
            f"{_format_counts(player['structure_builds'])}; upgrades "
            f"{_format_counts(player['upgrades'])}; mobile "
            f"{_format_counts(player['mobile_by_type'])}; "
            f"breaches={player['breaches']}; "
            f"shield={player['shield_events']} events/"
            f"{player['shield_amount']} HP; "
            f"max_start_MP={player['max_start_MP']}"
        )

    print("\nMobile waves:")
    for wave in summary["waves"]:
        breach_locations = Counter(
            tuple(location) for location in wave["breach_locations"]
        )
        breach_text = ",".join(
            f"{list(location)}x{count}"
            for location, count in sorted(breach_locations.items())
        ) or "-"
        print(
            f"  T{wave['turn']:02d} {wave['owner']} "
            f"{wave['type']}x{wave['count']} from {wave['origin']} "
            f"MP={wave['MP_spent']} -> breaches={wave['breach_count']} "
            f"at {breach_text}; structure_damage~"
            f"{wave['attributed_structure_damage']}; "
            f"shield={wave['shield_amount']}"
        )

    if compact:
        return
    print("\nPer-turn actions/resources:")
    for turn in summary["turns"]:
        player_fragments = []
        for player_key in ("P1", "P2"):
            player = turn["players"][player_key]
            actions = []
            if player["structures_built"]:
                actions.append(
                    "build=" + _format_counts(player["structures_built"])
                )
            if player["upgrades"]:
                actions.append("up=" + _format_counts(player["upgrades"]))
            if player["removals_marked"]:
                actions.append(
                    "rm=" + _format_counts(player["removals_marked"])
                )
            if player["structure_deaths"]:
                actions.append(
                    "lost=" + _format_counts(player["structure_deaths"])
                )
            if player["breach_count"]:
                actions.append(
                    f"breach={player['breach_count']}"
                    f"/{player['breach_damage_dealt']}"
                )
            if player["structure_damage_taken"]:
                actions.append(
                    f"struct_dmg={player['structure_damage_taken']}"
                )
            player_fragments.append(
                f"{player_key} {_format_stats(player['start'])} "
                f"spend={player['estimated_spend']['SP']}/"
                f"{player['estimated_spend']['MP']} "
                + (" ".join(actions) if actions else "idle")
            )
        print(f"  T{turn['turn']:02d}: " + " | ".join(player_fragments))

    end_stats = result.get("end_stats")
    if end_stats:
        print("\nAuthoritative endStats:")
        print(json.dumps(end_stats, indent=2, sort_keys=True))
    if summary["warnings"]:
        print("\nWarnings:", file=sys.stderr)
        for warning in summary["warnings"]:
            print(f"  - {warning}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", help="path to a newline-delimited .replay file")
    parser.add_argument(
        "--json", action="store_true", help="emit the complete machine-readable summary"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="text mode: omit the per-turn table and endStats dump",
    )
    args = parser.parse_args(argv)

    analyzer = ReplayAnalyzer(args.replay)
    try:
        analyzer.load()
        summary = analyzer.analyze()
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        _print_text(summary, compact=args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
