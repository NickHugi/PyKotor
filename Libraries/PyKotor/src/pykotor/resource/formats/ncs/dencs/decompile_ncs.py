from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData
    from pykotor.resource.formats.ncs.dencs.decoder import Decoder


def decompile_ncs(file_path: str | io.BufferedIOBase, actions: ActionsData) -> str | None:
    data = None
    setdest = None
    dotypes = None
    ast = None
    nodedata = None
    subdata = None
    subs = None
    sub = None
    mainsub = None
    flatten = None
    doglobs = None
    cleanpass = None
    mainpass = None
    destroytree = None
    if actions is None:
        print("null action!")
        return None
    try:
        from pykotor.resource.formats.ncs.dencs.utils.file_script_data import FileScriptData  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.io_ncs import read_ncs  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.ncs_to_ast_converter import convert_ncs_to_ast  # pyright: ignore[reportMissingImports]
        data = FileScriptData()
        
        # Use existing io_ncs to read NCS file
        ncs = read_ncs(file_path)
        
        # Convert NCSInstruction[] directly to AST (skips Decoder -> Lexer -> Parser)
        ast = convert_ncs_to_ast(ncs)
        from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData
        nodedata = NodeAnalysisData()
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData
        subdata = SubroutineAnalysisData(nodedata)
        from pykotor.resource.formats.ncs.dencs.utils.set_positions import SetPositions
        ast.apply(SetPositions(nodedata))
        from pykotor.resource.formats.ncs.dencs.utils.set_destinations import SetDestinations
        setdest = SetDestinations(ast, nodedata, subdata)
        ast.apply(setdest)
        from pykotor.resource.formats.ncs.dencs.utils.set_dead_code import SetDeadCode
        ast.apply(SetDeadCode(nodedata, subdata, setdest.get_origins()))
        setdest.done()
        setdest = None
        subdata.split_off_subroutines(ast)
        ast = None
        mainsub = subdata.get_main_sub()
        from pykotor.resource.formats.ncs.dencs.utils.flatten_sub import FlattenSub
        flatten = FlattenSub(mainsub, nodedata)
        mainsub.apply(flatten)
        subs = subdata.get_subroutines()
        while subs.has_next():
            sub = subs.next()
            flatten.set_sub(sub)
            sub.apply(flatten)
        flatten.done()
        flatten = None
        doglobs = None
        sub = subdata.get_globals_sub()
        if sub is not None:
            from pykotor.resource.formats.ncs.dencs.do_global_vars import DoGlobalVars
            doglobs = DoGlobalVars(nodedata, subdata)
            sub.apply(doglobs)
            from pykotor.resource.formats.ncs.dencs.scriptutils.cleanup_pass import CleanupPass
            cleanpass = CleanupPass(doglobs.get_script_root(), nodedata, subdata, doglobs.get_state())
            cleanpass.apply()
            subdata.set_global_stack(doglobs.get_stack())
            subdata.global_state(doglobs.get_state())
            cleanpass.done()
        alldone = False
        onedone = True
        for pass_num in range(1, 6):
            if alldone:
                break
            if not onedone and pass_num >= 5:
                break
            subs = subdata.get_subroutines()
            alldone = True
            onedone = False
            while subs.has_next():
                sub = subs.next()
                if not subdata.is_prototyped(nodedata.get_pos(sub), True):
                    from pykotor.resource.formats.ncs.dencs.utils.subroutine_path_finder import SubroutinePathFinder
                    sub.apply(SubroutinePathFinder(subdata.get_state(sub), nodedata, subdata, pass_num))
                    if subdata.is_being_prototyped(nodedata.get_pos(sub)):
                        from pykotor.resource.formats.ncs.dencs.do_types import DoTypes
                        dotypes = DoTypes(subdata.get_state(sub), nodedata, subdata, actions, True)
                        sub.apply(dotypes)
                        dotypes.done()
                        onedone = True
                    else:
                        alldone = False
        if not alldone:
            subdata.print_states()
            raise RuntimeError("Unable to do initial prototype of all subroutines.")
        from pykotor.resource.formats.ncs.dencs.do_types import DoTypes
        dotypes = DoTypes(subdata.get_state(mainsub), nodedata, subdata, actions, False)
        mainsub.apply(dotypes)
        dotypes.assert_stack()
        dotypes.done()
        alldone = (subdata.count_subs_done() == subdata.num_subs())
        onedone = True
        donecount = subdata.count_subs_done()
        loopcount = 0
        while not alldone and onedone and loopcount < 1000:
            alldone = (subdata.count_subs_done() == subdata.num_subs())
            onedone = (onedone or subdata.count_subs_done() > donecount)
            donecount = subdata.count_subs_done()
            loopcount += 1
            onedone = False
            subs = subdata.get_subroutines()
            while subs.has_next():
                sub = subs.next()
                dotypes = DoTypes(subdata.get_state(sub), nodedata, subdata, actions, False)
                sub.apply(dotypes)
                dotypes.done()
            dotypes = DoTypes(subdata.get_state(mainsub), nodedata, subdata, actions, False)
            mainsub.apply(dotypes)
            dotypes.done()
        if not alldone:
            print("Unable to do final prototype of all subroutines.")
            return None
        dotypes = None
        nodedata.clear_proto_data()
        subs = subdata.get_subroutines()
        from pykotor.resource.formats.ncs.dencs.main_pass import MainPass
        while subs.has_next():
            sub = subs.next()
            mainpass = MainPass(subdata.get_state(sub), nodedata, subdata, actions)
            sub.apply(mainpass)
            cleanpass = CleanupPass(mainpass.get_script_root(), nodedata, subdata, mainpass.get_state())
            cleanpass.apply()
            data.add_sub(mainpass.get_state())
            mainpass.done()
            cleanpass.done()
        mainpass = MainPass(subdata.get_state(mainsub), nodedata, subdata, actions)
        mainsub.apply(mainpass)
        mainpass.assert_stack()
        cleanpass = CleanupPass(mainpass.get_script_root(), nodedata, subdata, mainpass.get_state())
        cleanpass.apply()
        mainpass.get_state().is_main(True)
        data.add_sub(mainpass.get_state())
        mainpass.done()
        cleanpass.done()
        data.subdata(subdata)
        if doglobs is not None:
            cleanpass = CleanupPass(doglobs.get_script_root(), nodedata, subdata, doglobs.get_state())
            cleanpass.apply()
            data.globals(doglobs.get_state())
            doglobs.done()
            cleanpass.done()
        subs = subdata.get_subroutines()
        from pykotor.resource.formats.ncs.dencs.utils.destroy_parse_tree import DestroyParseTree
        destroytree = DestroyParseTree()
        while subs.has_next():
            subs.next().apply(destroytree)
        mainsub.apply(destroytree)
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        data = None
        setdest = None
        dotypes = None
        ast = None
        if nodedata is not None:
            nodedata.close()
        nodedata = None
        if subdata is not None:
            subdata.parse_done()
        subdata = None
        subs = None
        sub = None
        mainsub = None
        flatten = None
        doglobs = None
        cleanpass = None
        mainpass = None
        destroytree = None
        import gc
        gc.collect()

