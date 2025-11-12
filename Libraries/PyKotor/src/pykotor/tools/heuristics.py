from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.misc import Game

if TYPE_CHECKING:
    import os


def determine_game(
    path: os.PathLike | str,
) -> Game | None:
    """Determines the game based on files and folders.

    Args:
    ----
        path: Path to game directory

    Returns:
    -------
        Game: Game enum or None

    References:
    ----------
        vendor/KOTOR_Registry_Install_Path_Editor (Registry path detection)
        vendor/HoloPatcher.NET/src/HoloPatcher/Utils (Game detection logic)
        Note: File and folder heuristics vary between Steam, GOG, and disc releases

    Processing Logic:
    ----------------
        1. Normalize the path and check for existence of game files
        2. Define checks for each game
        3. Run checks and score games
        4. Return game with highest score or None if scores are equal or all checks fail
    """
    r_path: Path = Path(path)

    def check(x: str) -> bool:
        c_path: Path = r_path.joinpath(x)
        return c_path.exists() is not False

    # Checks for each game
    game1_pc_checks: list[bool] = [
        check("streamwaves"),
        check("swkotor.exe"),
        check("swkotor.ini"),
        check("rims"),
        check("utils"),
        check("32370_install.vdf"),
        check("miles/mssds3d.m3d"),
        check("miles/msssoft.m3d"),
        check("data/party.bif"),
        check("data/player.bif"),
        check("modules/global.mod"),
        check("modules/legal.mod"),
        check("modules/mainmenu.mod"),
    ]

    game1_xbox_checks: list[bool] = [
        check("01_SS_Repair01.ini"),
        check("swpatch.ini"),
        check("dataxbox/_newbif.bif"),
        check("rimsxbox"),
        check("players.erf"),
        check("downloader.xbe"),
        check("rimsxbox/manm28ad_adx.rim"),
        check("rimsxbox/miniglobal.rim"),
        check("rimsxbox/miniglobaldx.rim"),
        check("rimsxbox/STUNT_56a_a.rim"),
        check("rimsxbox/STUNT_56a_adx.rim"),
        check("rimsxbox/STUNT_57_adx.rim"),
        check("rimsxbox/subglobal.rim"),
        check("rimsxbox/subglobaldx.rim"),
        check("rimsxbox/unk_m44ac_adx.rim"),
        check("rimsxbox/M12ab_adx.rim"),
        check("rimsxbox/mainmenu.rim"),
        check("rimsxbox/mainmenudx.rim"),
        check("rimsxbox/manm28ad_adx.rim"),
    ]

    game1_ios_checks: list[bool] = [
        check("override/ios_action_bg.tga"),
        check("override/ios_action_bg2.tga"),
        check("override/ios_action_x.tga"),
        check("override/ios_action_x2.tga"),
        check("override/ios_button_a.tga"),
        check("override/ios_button_x.tga"),
        check("override/ios_button_y.tga"),
        check("override/ios_edit_box.tga"),
        check("override/ios_enemy_plus.tga"),
        check("override/ios_gpad_bg.tga"),
        check("override/ios_gpad_gen.tga"),
        check("override/ios_gpad_gen2.tga"),
        check("override/ios_gpad_help.tga"),
        check("override/ios_gpad_help2.tga"),
        check("override/ios_gpad_map.tga"),
        check("override/ios_gpad_map2.tga"),
        check("override/ios_gpad_save.tga"),
        check("override/ios_gpad_save2.tga"),
        check("override/ios_gpad_solo.tga"),
        check("override/ios_gpad_solo2.tga"),
        check("override/ios_gpad_solox.tga"),
        check("override/ios_gpad_solox2.tga"),
        check("override/ios_gpad_ste.tga"),
        check("override/ios_gpad_ste2.tga"),
        check("override/ios_gpad_ste3.tga"),
        check("override/ios_help.tga"),
        check("override/ios_help2.tga"),
        check("override/ios_help_1.tga"),
        check("KOTOR"),
        check("KOTOR.entitlements"),
        check("kotorios-Info.plist"),
        check("AppIcon29x29.png"),
        check("AppIcon50x50@2x~ipad.png"),
        check("AppIcon50x50~ipad.png"),
    ]

    game1_android_checks: list[bool] = [  # TODO(th3w1zard1): Implement
    ]

    game2_pc_checks: list[bool] = [
        check("streamvoice"),
        check("swkotor2.exe"),
        check("swkotor2.ini"),
        check("LocalVault"),
        check("LocalVault/test.bic"),
        check("LocalVault/testold.bic"),
        check("miles/binkawin.asi"),
        check("miles/mssds3d.flt"),
        check("miles/mssdolby.flt"),
        check("miles/mssogg.asi"),
        check("data/Dialogs.bif"),
    ]

    game2_xbox_checks: list[bool] = [
        check("combat.erf"),
        check("effects.erf"),
        check("footsteps.erf"),
        check("footsteps.rim"),
        check("SWRC"),
        check("weapons.ERF"),
        check("SuperModels/smseta.erf"),
        check("SuperModels/smsetb.erf"),
        check("SuperModels/smsetc.erf"),
        check("SWRC/System/Subtitles_Epilogue.int"),
        check("SWRC/System/Subtitles_YYY_06.int"),
        check("SWRC/System/SWRepublicCommando.int"),
        check("SWRC/System/System.ini"),
        check("SWRC/System/UDebugMenu.u"),
        check("SWRC/System/UnrealEd.int"),
        check("SWRC/System/UnrealEd.u"),
        check("SWRC/System/User.ini"),
        check("SWRC/System/UWeb.int"),
        check("SWRC/System/Window.int"),
        check("SWRC/System/WinDrv.int"),
        check("SWRC/System/Xbox"),
        check("SWRC/System/XboxLive.int"),
        check("SWRC/System/XGame.u"),
        check("SWRC/System/XGameList.int"),
        check("SWRC/System/XGames.int"),
        check("SWRC/System/XInterface.u"),
        check("SWRC/System/XInterfaceMP.u"),
        check("SWRC/System/XMapList.int"),
        check("SWRC/System/XMaps.int"),
        check("SWRC/System/YYY_TitleCard.int"),
        check("SWRC/System/Xbox/Engine.int"),
        check("SWRC/System/Xbox/XboxLive.int"),
        check("SWRC/Textures/GUIContent.utx"),
    ]

    game2_ios_checks: list[bool] = [
        check("override/ios_mfi_deu.tga"),
        check("override/ios_mfi_eng.tga"),
        check("override/ios_mfi_esp.tga"),
        check("override/ios_mfi_fre.tga"),
        check("override/ios_mfi_ita.tga"),
        check("override/ios_self_box_r.tga"),
        check("override/ios_self_expand2.tga"),
        check("override/ipho_forfeit.tga"),
        check("override/ipho_forfeit2.tga"),
        check("override/kotor2logon.tga"),
        check("override/lbl_miscroll_open_f.tga"),
        check("override/lbl_miscroll_open_f2.tga"),
        check("override/ydialog.gui"),
        check("KOTOR II"),
        check("KOTOR2-Icon-20-Apple.png"),
        check("KOTOR2-Icon-29-Apple.png"),
        check("KOTOR2-Icon-40-Apple.png"),
        check("KOTOR2-Icon-58-apple.png"),
        check("KOTOR2-Icon-60-apple.png"),
        check("KOTOR2-Icon-76-apple.png"),
        check("KOTOR2-Icon-80-apple.png"),
        check("KOTOR2_LaunchScreen.storyboardc"),
        check("KOTOR2_LaunchScreen.storyboardc/Info.plist"),
        check("GoogleService-Info.plist"),
    ]

    game2_android_checks: list[bool] = [  # TODO(th3w1zard1): Implement
    ]

    # Determine the game with the most checks passed
    def determine_highest_scoring_game() -> Game | None:
        # Scoring for each game and platform
        scores: dict[Game, int] = {
            Game.K1: sum(game1_pc_checks),
            Game.K2: sum(game2_pc_checks),
            Game.K1_XBOX: sum(game1_xbox_checks),
            Game.K2_XBOX: sum(game2_xbox_checks),
            Game.K1_IOS: sum(game1_ios_checks),
            Game.K2_IOS: sum(game2_ios_checks),
            Game.K1_ANDROID: sum(game1_android_checks),
            Game.K2_ANDROID: sum(game2_android_checks),
        }

        highest_scoring_game: Game | None = None
        highest_score: int = 0

        for game, score in scores.items():
            if score > highest_score:
                highest_score = score
                highest_scoring_game = game

        return highest_scoring_game

    return determine_highest_scoring_game()
