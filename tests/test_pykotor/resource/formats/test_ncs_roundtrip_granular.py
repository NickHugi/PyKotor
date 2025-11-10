from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

pytest.importorskip("ply", reason="ply is required for NSS compilation tests")

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_auto import (
    bytes_ncs,
    compile_nss,
    decompile_ncs,
    read_ncs,
)
from pykotor.resource.formats.ncs.ncs_data import NCS


TESTS_ROOT = Path(__file__).resolve().parents[4]


def _canonical_bytes(ncs: NCS) -> bytes:
    """Return canonical byte representation for easy equality checks."""
    return bytes(bytes_ncs(ncs))


def _assert_bidirectional_roundtrip(
    source: str,
    game: Game,
    *,
    library_lookup: list[Path] | None = None,
) -> str:
    """
    Compile source to NCS, decompile it back, and ensure both NSS->NCS->NSS and
    NCS->NSS->NCS cycles are stable for the given game context.
    """
    compiled = compile_nss(source, game, library_lookup=library_lookup)
    decompiled = decompile_ncs(compiled, game)

    # NSS -> NCS -> NSS -> NCS
    recompiled = compile_nss(decompiled, game, library_lookup=library_lookup)
    assert _canonical_bytes(compiled) == _canonical_bytes(
        recompiled
    ), "Recompiled bytecode diverged from initial compile"

    # NCS -> NSS -> NCS using freshly parsed binary payload
    binary_blob = _canonical_bytes(compiled)
    reloaded = read_ncs(binary_blob)
    ncs_from_binary = compile_nss(
        decompile_ncs(reloaded, game),
        game,
        library_lookup=library_lookup,
    )
    assert _canonical_bytes(reloaded) == _canonical_bytes(
        ncs_from_binary
    ), "Roundtrip from binary payload not stable"

    return decompiled


def _dedent(script: str) -> str:
    return textwrap.dedent(script).strip() + "\n"


def _assert_substrings(source: str, substrings: list[str]) -> None:
    for snippet in substrings:
        assert (
            snippet in source
        ), f"Expected snippet '{snippet}' to be present in decompiled script:\n{source}"


class TestNssNcsRoundtripGranular:
    def test_roundtrip_primitives_and_structural_types(self):
        source = _dedent(
            """
            void main()
            {
                int valueInt = 42;
                float valueFloat = 3.5;
                string valueString = "kotor";
                object valueObject = OBJECT_SELF;
                vector valueVector = Vector(1.0, 2.0, 3.0);
                location valueLocation = Location(valueVector, 180.0);
                effect valueEffect = GetFirstEffect(OBJECT_SELF);
                event valueEvent = EventUserDefined(12);
                talent valueTalent = TalentFeat(FEAT_POWER_ATTACK);

                if (GetIsEffectValid(valueEffect))
                {
                    RemoveEffect(OBJECT_SELF, valueEffect);
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int valueInt = 42;",
                "float valueFloat = 3.5;",
                "string valueString = \"kotor\";",
                "object valueObject = OBJECT_SELF;",
                "vector valueVector = Vector(1.0, 2.0, 3.0);",
                "location valueLocation = Location(valueVector, 180.0);",
                "event valueEvent = EventUserDefined(12);",
                "talent valueTalent = TalentFeat(FEAT_POWER_ATTACK);",
            ],
        )

    def test_roundtrip_arithmetic_operations(self):
        source = _dedent(
            """
            float CalculateAverage(int first, int second, float weight)
            {
                float total = IntToFloat(first + second);
                float average = total / 2.0;
                return (average * weight) - 1.5;
            }

            void main()
            {
                int a = 10;
                int b = 7;
                int sum = a + b;
                int difference = sum - 5;
                int product = difference * 3;
                int quotient = product / 4;
                int remainder = quotient % 2;
                float weighted = CalculateAverage(sum, difference, 4.5);
                float negated = -weighted;
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int sum = a + b;",
                "int difference = sum - 5;",
                "int product = difference * 3;",
                "int quotient = product / 4;",
                "int remainder = quotient % 2;",
                "float negated = -weighted;",
            ],
        )

    def test_roundtrip_bitwise_and_shift_operations(self):
        source = _dedent(
            """
            void main()
            {
                int mask = 0xFF;
                int value = 0x35;
                int andResult = mask & value;
                int orResult = mask | value;
                int xorResult = mask ^ value;
                int leftShift = value << 2;
                int rightShift = mask >> 3;
                int unsignedShift = mask >>> 1;
                int inverted = ~value;
                int combined = (andResult | xorResult) & ~leftShift;
                int logicalMix = (combined != 0) && (xorResult == 0xCA);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int andResult = mask & value;",
                "int orResult = mask | value;",
                "int xorResult = mask ^ value;",
                "int leftShift = value << 2;",
                "int rightShift = mask >> 3;",
                "int unsignedShift = mask >>> 1;",
                "int inverted = ~value;",
            ],
        )

    def test_roundtrip_logical_and_relational_operations(self):
        source = _dedent(
            """
            int Evaluate(int a, int b, int c)
            {
                if ((a > b && b >= c) || (a == c))
                {
                    return 1;
                }
                else if (!(c < a) && (b != 0))
                {
                    return 2;
                }
                return 0;
            }

            void main()
            {
                int flag = Evaluate(5, 3, 4);
                if (flag == 1 || flag == 2)
                {
                    AssignCommand(OBJECT_SELF, PlayAnimation(ANIMATION_LOOPING_GET_UP, 1.0, 0.5));
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "if ((a > b && b >= c) || (a == c))",
                "else if (!(c < a) && (b != 0))",
                "if (flag == 1 || flag == 2)",
            ],
        )

    def test_roundtrip_compound_assignments(self):
        source = _dedent(
            """
            void main()
            {
                int counter = 0;
                counter += 5;
                counter -= 2;
                counter *= 3;
                counter /= 2;
                counter %= 4;

                float distance = 10.0;
                distance += 2.5;
                distance -= 1.5;
                distance *= 1.25;
                distance /= 3.0;

                vector offset = Vector(1.0, 2.0, 3.0);
                offset += Vector(0.5, 0.5, 0.5);
                offset -= Vector(0.5, 1.0, 1.5);
                offset *= 2.0;
                offset /= 4.0;
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "counter += 5;",
                "counter -= 2;",
                "counter *= 3;",
                "counter /= 2;",
                "counter %= 4;",
                "distance += 2.5;",
                "offset += Vector(0.5, 0.5, 0.5);",
                "offset *= 2.0;",
            ],
        )

    def test_roundtrip_increment_and_decrement(self):
        source = _dedent(
            """
            void main()
            {
                int i = 0;
                int first = i++;
                int second = ++i;
                int third = i--;
                int fourth = --i;
                if (first < second && third >= fourth)
                {
                    i += 1;
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int first = i++;",
                "int second = ++i;",
                "int third = i--;",
                "int fourth = --i;",
            ],
        )

    def test_roundtrip_if_else_nesting(self):
        source = _dedent(
            """
            int EvaluateState(int state)
            {
                if (state == 0)
                {
                    return 10;
                }
                else if (state == 1)
                {
                    if (GetIsNight())
                    {
                        return 20;
                    }
                    else
                    {
                        return 30;
                    }
                }
                else
                {
                    return -1;
                }
            }

            void main()
            {
                int result = EvaluateState(1);
                if (result == 20)
                {
                    ActionStartConversation(OBJECT_SELF, "result_20");
                }
                else
                {
                    ActionStartConversation(OBJECT_SELF, "other_result");
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "if (state == 0)",
                "else if (state == 1)",
                "if (GetIsNight())",
                "else",
                "ActionStartConversation(OBJECT_SELF, \"result_20\");",
            ],
        )

    def test_roundtrip_while_for_do_loops(self):
        source = _dedent(
            """
            void main()
            {
                int total = 0;
                int i = 0;
                while (i < 5)
                {
                    total += i;
                    i++;
                }

                for (int j = 0; j < 3; j++)
                {
                    total += j * 2;
                }

                int k = 0;
                do
                {
                    total -= k;
                    k++;
                }
                while (k < 2);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "while (i < 5)",
                "for (int j = 0; j < 3; j++)",
                "do",
                "while (k < 2);",
            ],
        )

    def test_roundtrip_switch_case(self):
        source = _dedent(
            """
            void main()
            {
                int value = GetLocalInt(OBJECT_SELF, "switch");
                switch (value)
                {
                    case 0:
                        SetLocalInt(OBJECT_SELF, "switch", 1);
                        break;
                    case 1:
                    case 2:
                        SetLocalInt(OBJECT_SELF, "switch", 3);
                        break;
                    default:
                        DeleteLocalInt(OBJECT_SELF, "switch");
                        break;
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "switch (value)",
                "case 0:",
                "case 1:",
                "case 2:",
                "default:",
            ],
        )

    def test_roundtrip_struct_usage(self):
        source = _dedent(
            """
            struct CombatStats
            {
                int attack;
                int defense;
                float multiplier;
                string label;
            };

            CombatStats BuildStats(int base)
            {
                CombatStats result;
                result.attack = base + 2;
                result.defense = base * 2;
                result.multiplier = IntToFloat(result.defense) / 3.0;
                result.label = \"stat_\" + IntToString(base);
                return result;
            }

            void main()
            {
                CombatStats stats = BuildStats(5);
                if (stats.attack > stats.defense)
                {
                    stats.label = \"attack_bias\";
                }
                else
                {
                    stats.label = \"defense_bias\";
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "struct CombatStats",
                "result.attack = base + 2;",
                "result.defense = base * 2;",
                "stats.label = \"attack_bias\";",
            ],
        )

    def test_roundtrip_function_definitions_and_returns(self):
        source = _dedent(
            """
            int CountPartyMembers()
            {
                int count = 0;
                object creature = GetFirstFactionMember(OBJECT_SELF, FALSE);
                while (GetIsObjectValid(creature))
                {
                    count++;
                    creature = GetNextFactionMember(OBJECT_SELF, FALSE);
                }
                return count;
            }

            void Announce(int members)
            {
                string message = "members:" + IntToString(members);
                SendMessageToPC(OBJECT_SELF, message);
            }

            void main()
            {
                int members = CountPartyMembers();
                Announce(members);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int CountPartyMembers()",
                "while (GetIsObjectValid(creature))",
                "void Announce(int members)",
                "Announce(members);",
            ],
        )

    def test_roundtrip_action_queue_and_delays(self):
        source = _dedent(
            """
            void ApplyBuff(object target)
            {
                effect buff = EffectAbilityIncrease(ABILITY_STRENGTH, 2);
                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, buff, target, 6.0);
            }

            void main()
            {
                object player = GetFirstPC();
                DelayCommand(1.5, AssignCommand(player, ApplyBuff(player)));
                ClearAllActions();
                ActionDoCommand(AssignCommand(OBJECT_SELF, PlaySound("pc_action")));
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "DelayCommand(1.5, AssignCommand(player, ApplyBuff(player)));",
                "ClearAllActions();",
                "ActionDoCommand(AssignCommand(OBJECT_SELF, PlaySound(\"pc_action\")));",
            ],
        )

    def test_roundtrip_include_resolution(self, tmp_path: Path):
        include_path = tmp_path / "rt_helper.nss"
        include_path.write_text(
            _dedent(
                """
                int HelperFunction(int value)
                {
                    return value * 2;
                }
                """
            ),
            encoding="utf-8",
        )

        source = _dedent(
            """
            #include "rt_helper"

            void main()
            {
                int result = HelperFunction(5);
                SetLocalInt(OBJECT_SELF, "helper", result);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(
            source,
            Game.K1,
            library_lookup=[tmp_path],
        )
        _assert_substrings(
            decompiled,
            [
                "int HelperFunction(int value)",
                "SetLocalInt(OBJECT_SELF, \"helper\", result);",
            ],
        )

    def test_roundtrip_tsl_specific_functionality(self):
        source = _dedent(
            """
            void main()
            {
                object target = GetFirstPC();
                effect penalty = EffectAttackDecrease(2, ATTACK_BONUS_MISC);
                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, penalty, target, 5.0);
                AssignCommand(target, ClearAllActions());
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K2)
        _assert_substrings(
            decompiled,
            [
                "effect penalty = EffectAttackDecrease(2, ATTACK_BONUS_MISC);",
                "ApplyEffectToObject(DURATION_TYPE_TEMPORARY, penalty, target, 5.0);",
            ],
        )


class TestNcsBinaryRoundtripSamples:
    SAMPLE_FILES = [
        ("tests/files/test.ncs", Game.K1),
        ("tests/test_pykotor/test_files/test.ncs", Game.K1),
        ("tests/test_toolset/test_files/90sk99.ncs", Game.K2),
    ]

    @pytest.mark.parametrize(("relative_path", "game"), SAMPLE_FILES)
    def test_binary_roundtrip_samples(self, relative_path: str, game: Game):
        ncs_path = TESTS_ROOT.parent / relative_path
        assert ncs_path.is_file(), f"Sample NCS file '{ncs_path}' is missing"

        original = read_ncs(ncs_path)
        decompiled = decompile_ncs(original, game)
        recompilation = compile_nss(decompiled, game)

        assert _canonical_bytes(original) == _canonical_bytes(
            recompilation
        ), f"Roundtrip failed for {relative_path}"
        assert len(decompiled.strip()) > 0, "Decompiled source should not be empty"

