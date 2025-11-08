from __future__ import annotations

import os
import traceback
import unittest

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, decompile_ncs
from pathlib import Path


class TestNcsRoundtrip(unittest.TestCase):
    DEFAULT_SAMPLE_SIZE = 10
    SAMPLE_LIMIT = int(os.environ.get("PYKOTOR_NCS_ROUNDTRIP_SAMPLE", DEFAULT_SAMPLE_SIZE))
    _ROUNDTRIP_CASES: list[tuple[Game, Path, list[Path]]] | None = None

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.vanilla_root = cls.root / "Vanilla_KOTOR_Script_Source"
        cls.roundtrip_cases = cls._initialize_roundtrip_cases()

    def test_nss_roundtrip(self):
        if not self.roundtrip_cases:
            self.skipTest("Vanilla_KOTOR_Script_Source submodule not available or no scripts collected")

        for game, script_path, library_lookup in self.roundtrip_cases:
            with self.subTest(f"{game.name}_{script_path.relative_to(self.vanilla_root)}"):
                source = script_path.read_text(encoding="windows-1252", errors="ignore")
                original_ncs = compile_nss(source, game, library_lookup=library_lookup)

                decompiled_source = decompile_ncs(original_ncs, game)
                roundtrip_ncs = compile_nss(decompiled_source, game, library_lookup=library_lookup)
                roundtrip_source = decompile_ncs(roundtrip_ncs, game)
                roundtrip_ncs_second = compile_nss(roundtrip_source, game, library_lookup=library_lookup)

                self.assertEqual(
                    roundtrip_ncs,
                    roundtrip_ncs_second,
                    f"Roundtrip compilation not stable for {script_path}",
                )


    @classmethod
    def _iter_scripts(cls, root: Path) -> list[Path]:
        return sorted(root.rglob("*.nss"))

    @classmethod
    def _collect_sample(cls, game: Game, roots: list[Path], library_lookup: list[Path]) -> list[Path]:
        sample: list[Path] = []
        for directory in roots:
            for script in cls._iter_scripts(directory):
                if script in sample:
                    print(f"Skipping duplicate script {script} for game {game}")
                    continue
                try:
                    source = script.read_text(encoding="windows-1252", errors="ignore")
                except FileNotFoundError:
                    print(f"Skipping missing script {script} for game {game}")
                    continue

                # Skip scripts that rely on external includes for now
                if "#include" in source:
                    print(f"Skipping script {script} for game {game} due to include directive")
                    continue

                try:
                    compile_nss(source, game, library_lookup=library_lookup)
                except Exception:
                    print(f"Compilation failed for script {script} for game {game}")
                    print(f"{traceback.format_exc()}\n")
                    continue

                sample.append(script)
                if cls.SAMPLE_LIMIT and len(sample) >= cls.SAMPLE_LIMIT:
                    print(
                        f"Reached sample limit {cls.SAMPLE_LIMIT} for game {game} with directory {directory}",
                    )
                    return sample
        return sample

    @classmethod
    def _game_config(cls) -> dict[Game, dict[str, list[Path]]]:
        return {
            Game.K1: {
                "roots": [
                    cls.vanilla_root / "K1" / "Modules",
                    cls.vanilla_root / "K1" / "Rims",
                    cls.vanilla_root / "K1" / "Data" / "scripts.bif",
                ],
                "lookup": [
                    (cls.vanilla_root / "K1" / "Modules").resolve(),
                    (cls.vanilla_root / "K1" / "Rims").resolve(),
                    (cls.vanilla_root / "K1" / "Data" / "scripts.bif").resolve(),
                ],
            },
            Game.K2: {
                "roots": [
                    cls.vanilla_root / "TSL" / "Vanilla" / "Modules",
                    cls.vanilla_root / "TSL" / "Vanilla" / "Data" / "Scripts",
                ],
                "lookup": [
                    (cls.vanilla_root / "TSL" / "Vanilla" / "Modules").resolve(),
                    (cls.vanilla_root / "TSL" / "Vanilla" / "Data" / "Scripts").resolve(),
                    (cls.vanilla_root / "TSL" / "TSLRCM" / "Override").resolve(),
                ],
            },
        }

    @classmethod
    def _initialize_roundtrip_cases(cls) -> list[tuple[Game, Path, list[Path]]]:
        if cls._ROUNDTRIP_CASES is not None:
            print(f"Roundtrip cases already initialized with {len(cls._ROUNDTRIP_CASES)} entries")
            return cls._ROUNDTRIP_CASES

        roundtrip_cases: list[tuple[Game, Path, list[Path]]] = []
        if not cls.vanilla_root.exists():
            print(f"Skipping sample collection because VANILLA_ROOT {cls.vanilla_root} does not exist")
            cls._ROUNDTRIP_CASES = roundtrip_cases
            return roundtrip_cases

        print("Collecting sample scripts from Vanilla_KOTOR_Script_Source...")
        for game, config in cls._game_config().items():
            print(f"Collecting sample scripts for {game.name}...")
            roots = [path for path in config["roots"] if path.exists() and path.is_dir()]
            lookup = [path for path in config["lookup"] if path.exists()]
            print(f"Roots: {roots}")
            print(f"Lookup: {lookup}")
            if not roots or not lookup:
                print(f"No roots or lookup found for {game.name}, skipping...")
                continue
            sample = cls._collect_sample(game, roots, lookup)
            roundtrip_cases.extend(
                (game, script, lookup) for script in sample
            )

        cls._ROUNDTRIP_CASES = roundtrip_cases
        return roundtrip_cases
