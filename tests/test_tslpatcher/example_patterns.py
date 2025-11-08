"""Example TSLPatcher Patterns - Simple Demonstrations

This file demonstrates key TSLPatcher patterns without requiring
the full test infrastructure. Use this as a learning resource or
quick reference for common modding patterns.
"""

# ============================================================================
# PATTERN 1: Simple 2DA Row Addition
# ============================================================================

PATTERN_ADDROW_BASIC = """
Real-world use case: Adding a new spell to spells.2da

[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=my_new_spell

[my_new_spell]
RowLabel=999
label=FORCE_POWER_MY_SPELL
name=32000
spelldesc=32001
iconresref=ip_myspell
impactscript=my_spell
ExclusiveColumn=label
"""

# ============================================================================
# PATTERN 2: 2DA Row Addition with 2DAMEMORY Storage
# ============================================================================

PATTERN_ADDROW_WITH_MEMORY = """
Real-world use case: Adding a spell and storing its row index for reference

[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=my_new_spell

[my_new_spell]
RowLabel=999
label=FORCE_POWER_MY_SPELL
name=32000
2DAMEMORY1=RowIndex          <-- Stores the row index (999) in token 1
ExclusiveColumn=label
"""

# ============================================================================
# PATTERN 3: GFF File References 2DAMEMORY Token
# ============================================================================

PATTERN_GFF_USES_2DAMEMORY = """
Real-world use case: Granting the new spell to a creature

[GFFList]
File0=p_bastilla.utc

[p_bastilla.utc]
ClassList\\0\\KnownList0\\1\\Spell=2DAMEMORY1    <-- Uses stored row index
"""

# ============================================================================
# PATTERN 4: 2DAMEMORY Cross-Reference Chain
# ============================================================================

PATTERN_2DAMEMORY_CHAIN = """
Real-world use case: Adding a new weapon type (quarterstaff)

Step 1: Add sound to weaponsounds.2da
[weaponsounds.2da]
AddRow0=quarterstaff_sounds

[quarterstaff_sounds]
label=Quarterstaff_Sounds
cloth0=staff_hit1
2DAMEMORY1=RowIndex          <-- Token 1 = weaponsounds row index

Step 2: Add base item that references weapon sound
[baseitems.2da]
AddRow0=quarterstaff_baseitem

[quarterstaff_baseitem]
label=Quarterstaff
weaponmattype=2DAMEMORY1     <-- References weaponsounds row
name=32100
2DAMEMORY2=RowIndex          <-- Token 2 = baseitems row index

Step 3: Item uses the base item
[my_staff.uti]
BaseItem=2DAMEMORY2          <-- References baseitems row
"""

# ============================================================================
# PATTERN 5: TLK Append with StrRef Tokens
# ============================================================================

PATTERN_TLK_APPEND = """
Real-world use case: Adding new dialog text

[TLKList]
StrRef0=0
StrRef1=1
StrRef2=2

Then append.tlk file contains the actual text entries.
The StrRef tokens can be used in 2DA/GFF files:

[spells.2da]
ChangeRow0=modify_spell

[modify_spell]
RowIndex=50
name=StrRef0                 <-- Uses new TLK entry 0
spelldesc=StrRef1            <-- Uses new TLK entry 1
"""

# ============================================================================
# PATTERN 6: TLK Replace for Fixing Typos
# ============================================================================

PATTERN_TLK_REPLACE = """
Real-world use case: Fixing typos in existing dialog

[TLKList]
ReplaceFile0=replace.tlk

[replace.tlk]
12345=0                      <-- Original StrRef 12345 -> Token 0
23456=1                      <-- Original StrRef 23456 -> Token 1

Then replace.tlk file contains the corrected text.
"""

# ============================================================================
# PATTERN 7: GFF All Field Types
# ============================================================================

PATTERN_GFF_FIELD_TYPES = """
Real-world use case: Modifying various creature properties

[creature.utc]
Str=20                       <-- Byte field
Dex=18                       <-- Byte field
Appearance_Type=999          <-- Int32 field
Tag=my_creature              <-- String field
TemplateResRef=my_creature   <-- ResRef field
FirstName=<locstring_sect>   <-- LocalizedString (uses subsection)

[locstring_sect]
FieldType=ExoLocString
Label=FirstName
StrRef=32000
lang0=My Creature Name       <-- English male
lang2=My Creature Name       <-- English female
"""

# ============================================================================
# PATTERN 8: GFF Nested Struct Modification
# ============================================================================

PATTERN_GFF_NESTED = """
Real-world use case: Modifying items in creature inventory

[creature.utc]
ItemList\\0\\InventoryRes=g_i_melee01    <-- Modify first item

List syntax: ItemList\\0\\ references first item in list
Struct syntax: InventoryRes is field in that struct
"""

# ============================================================================
# PATTERN 9: GFF AddField for New Content
# ============================================================================

PATTERN_GFF_ADDFIELD = """
Real-world use case: Adding custom script field to door

[GFFList]
File0=door.utd

[door.utd]
AddField0=custom_script_field

[custom_script_field]
FieldType=ResRef
Label=CustomScript
Value=my_script
Path=                        <-- Empty path = root level
"""

# ============================================================================
# PATTERN 10: GFF AddStructToList for List Entries
# ============================================================================

PATTERN_GFF_ADDSTRUCT = """
Real-world use case: Adding a new feat to creature

[creature.utc]
AddField0=add_new_feat

[add_new_feat]
FieldType=Struct
Label=
Path=FeatList               <-- Add to FeatList
TypeId=0                    <-- Struct type ID
AddField0=feat_field        <-- Nested field in new struct

[feat_field]
FieldType=Word
Label=Feat
Value=123
Path=                       <-- Relative to parent struct
"""

# ============================================================================
# PATTERN 11: SSF Sound Modifications
# ============================================================================

PATTERN_SSF_BASIC = """
Real-world use case: Custom character voice set

[SSFList]
File0=character.ssf

[character.ssf]
Battlecry 1=StrRef0         <-- Uses new TLK entry
Selected 1=StrRef1
Attack 1=StrRef2
Pain 1=StrRef3
"""

# ============================================================================
# PATTERN 12: ChangeRow with Multiple Columns
# ============================================================================

PATTERN_CHANGEROW_MULTI = """
Real-world use case: Rebalancing a feat

[2DAList]
Table0=feat.2da

[feat.2da]
ChangeRow0=modify_power_attack

[modify_power_attack]
RowIndex=20
name=32200                  <-- New name StrRef
description=32201           <-- New description
minattackbonus=2            <-- Changed requirement
attackmod=-3                <-- Changed attack penalty
damagemod=5                 <-- Changed damage bonus
"""

# ============================================================================
# PATTERN 13: AddColumn for New 2DA Column
# ============================================================================

PATTERN_ADDCOLUMN = """
Real-world use case: Adding custom property column to items

[baseitems.2da]
AddColumn0=custom_property

[custom_property]
ColumnLabel=customproperty
DefaultValue=0              <-- Default for all existing rows
I10=special_value           <-- Special value for row 10
L999=another_value          <-- Value for row with label "999"
2DAMEMORY5=I10              <-- Store row 10's value in token 5
"""

# ============================================================================
# PATTERN 14: InstallList for Additional Files
# ============================================================================

PATTERN_INSTALLLIST = """
Real-world use case: Installing textures, models, scripts

[InstallList]
install_folder0=Override
install_folder1=modules\\danm13.mod

[install_folder0]
File0=my_texture.tga
File1=my_model.mdl
File2=my_model.mdx
Replace0=k_inc_generic.ncs  <-- Replace existing file

[install_folder1]
File0=danm13.mod            <-- Install entire module
"""

# ============================================================================
# PATTERN 15: High() Function for Auto-Incrementing
# ============================================================================

PATTERN_HIGH_FUNCTION = """
Real-world use case: Adding row with highest priority

[2DAList]
Table0=effecticon.2da

[effecticon.2da]
AddRow0=my_effect_icon

[my_effect_icon]
label=MY_EFFECT
iconresref=ip_myeffect
priority=High(priority)     <-- Automatically uses highest priority + 1
2DAMEMORY1=RowIndex
ExclusiveColumn=label
"""

# ============================================================================
# Real-World Complete Example: Bastila Has Battle Meditation
# ============================================================================

REAL_WORLD_BASTILA_BATTLE_MEDITATION = """
This is the actual pattern from the "Bastila Has Battle Meditation" mod.

[TLKList]
StrRef0=0

[2DAList]
Table0=spells.2da
Table1=visualeffects.2da
Table2=effecticon.2da

[GFFList]
File0=p_bastilla.utc
File1=p_bastilla001.utc
File2=p_bastilla002.utc

[spells.2da]
AddRow0=Battle_Meditation

[Battle_Meditation]
label=FORCE_POWER_BATTLE_MEDITATION_PC
name=32079
spelldesc=StrRef0
forcepoints=35
iconresref=ip_battlemed02
impactscript=fp_bmed
forcefriendly=high()
2DAMEMORY1=RowIndex         <-- Store spell row index
ExclusiveColumn=label

[visualeffects.2da]
AddRow2=BattleMed_PC_Animation

[BattleMed_PC_Animation]
label=VFX_IMP_BATTLE_MED_II
imp_root_m_node=v_BMedit2_imp
soundimpact=v_imp_heal
2DAMEMORY2=RowIndex         <-- Store VFX row index
ExclusiveColumn=label

[effecticon.2da]
AddRow0=Bmed_EffectIcon

[Bmed_EffectIcon]
label=FORCE_POWER_BATTLE_MEDITATION_PC
iconresref=ip_battlemed02
priority=high()
2DAMEMORY4=RowIndex         <-- Store effect icon row index
ExclusiveColumn=label

[p_bastilla.utc]
ClassList\\0\\KnownList0\\1\\Spell=2DAMEMORY1    <-- Grant spell to Bastila

[p_bastilla001.utc]
ClassList\\0\\KnownList0\\1\\Spell=2DAMEMORY1    <-- Grant to all Bastila variants

[p_bastilla002.utc]
ClassList\\0\\KnownList0\\1\\Spell=2DAMEMORY1
"""

# ============================================================================
# Real-World Complete Example: dm_qrts Quarterstaff
# ============================================================================

REAL_WORLD_DM_QRTS_QUARTERSTAFF = """
This is the actual pattern from the "DeadMan's quarterstaffs" mod.

[2DAList]
Table0=weaponsounds.2da
Table1=baseitems.2da

[GFFList]
File0=propqs02.uti
File1=w_melee_26.uti

[weaponsounds.2da]
AddRow0=weaponsounds_row_dm_electrostaff_0

[weaponsounds_row_dm_electrostaff_0]
label=DM_Electrostaff
cloth0=dm_estf_hits1
leather0=dm_estf_hits1
armor0=dm_estf_hith1
metal0=dm_estf_hitmtl1
parry0=dm_estf_par1
swingshort0=dm_estf_sw1
ExclusiveColumn=label
2DAMEMORY1=RowIndex         <-- Store weaponsounds row

[baseitems.2da]
AddRow0=baseitems_row_dm_electrostaff_0

[baseitems_row_dm_electrostaff_0]
label=DM_ElectroStaff
equipableslots=0x00010
defaultmodel=w_Qtrstaff_001
weaponwield=3
weapontype=1
weaponmattype=2DAMEMORY1    <-- Reference weaponsounds row
powereditem=1
2DAMEMORY2=RowIndex         <-- Store baseitems row
ExclusiveColumn=label

[propqs02.uti]
!ReplaceFile=1
BaseItem=2DAMEMORY2         <-- Reference baseitems row

[w_melee_26.uti]
BaseItem=2DAMEMORY2         <-- Reference baseitems row
!ReplaceFile=1
"""

# ============================================================================
# Pattern Summary Table
# ============================================================================

PATTERN_SUMMARY = """
+------------------+----------------------------------+------------------------+
| Pattern          | Use Case                         | Key Feature            |
+------------------+----------------------------------+------------------------+
| AddRow Basic     | Add new 2DA row                  | ExclusiveColumn        |
| AddRow + Memory  | Add row with reference           | 2DAMEMORY#=RowIndex    |
| GFF + 2DAMEMORY  | Link GFF to 2DA row              | Field=2DAMEMORY#       |
| Memory Chain     | Multi-file 2DA references        | Token cascading        |
| TLK Append       | New dialog text                  | StrRef# tokens         |
| TLK Replace      | Fix existing text                | ReplaceFile            |
| GFF Fields       | Modify GFF properties            | Path\\Field=Value      |
| GFF Nested       | Nested struct modification       | Path\\Struct\\Field    |
| GFF AddField     | Add new GFF field                | AddField# section      |
| GFF AddStruct    | Add list entry                   | AddField + TypeId      |
| SSF              | Character voice                  | Sound=StrRef#          |
| ChangeRow Multi  | Rebalance row                    | Multiple columns       |
| AddColumn        | New 2DA column                   | I#, L#, DefaultValue   |
| InstallList      | Copy files                       | File#, Replace#        |
| High()           | Auto-increment values            | High(column)           |
+------------------+----------------------------------+------------------------+
"""

if __name__ == "__main__":
    print("TSLPatcher Pattern Examples")
    print("=" * 80)
    print("\nThis file contains example patterns for common TSLPatcher scenarios.")
    print("Import the pattern strings in your code or use as reference documentation.")
    print("\nAvailable patterns:")
    
    patterns = [
        ("PATTERN_ADDROW_BASIC", "Simple 2DA row addition"),
        ("PATTERN_ADDROW_WITH_MEMORY", "AddRow with 2DAMEMORY storage"),
        ("PATTERN_GFF_USES_2DAMEMORY", "GFF references 2DA via token"),
        ("PATTERN_2DAMEMORY_CHAIN", "Chained 2DAMEMORY references"),
        ("PATTERN_TLK_APPEND", "TLK append mode"),
        ("PATTERN_TLK_REPLACE", "TLK replace mode"),
        ("PATTERN_GFF_FIELD_TYPES", "All GFF field types"),
        ("PATTERN_GFF_NESTED", "Nested struct modification"),
        ("PATTERN_GFF_ADDFIELD", "Adding new GFF field"),
        ("PATTERN_GFF_ADDSTRUCT", "Adding struct to list"),
        ("PATTERN_SSF_BASIC", "SSF sound modifications"),
        ("PATTERN_CHANGEROW_MULTI", "ChangeRow multiple columns"),
        ("PATTERN_ADDCOLUMN", "Adding 2DA column"),
        ("PATTERN_INSTALLLIST", "File installation"),
        ("PATTERN_HIGH_FUNCTION", "High() function usage"),
        ("REAL_WORLD_BASTILA_BATTLE_MEDITATION", "Complete: Bastila spell mod"),
        ("REAL_WORLD_DM_QRTS_QUARTERSTAFF", "Complete: Quarterstaff weapon mod"),
    ]
    
    for i, (name, description) in enumerate(patterns, 1):
        print(f"{i:2}. {description:45} -> {name}")
    
    print("\nExample usage:")
    print("  from example_patterns import PATTERN_ADDROW_WITH_MEMORY")
    print("  print(PATTERN_ADDROW_WITH_MEMORY)")
    
    print("\nSee test_diff_comprehensive.py for executable tests of these patterns.")

