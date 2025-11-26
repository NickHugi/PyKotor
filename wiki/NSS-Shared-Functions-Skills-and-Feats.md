# Skills and Feats

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="gethasfeat"></a>

## `GetHasFeat(nFeat, oCreature)` - Routine 285

- `285. GetHasFeat`
- Determine whether oCreature has nFeat, and nFeat is useable.
- - nFeat: FEAT_*
- - oCreature

- `nFeat`: int
- `oCreature`: object

<a id="gethasskill"></a>

## `GetHasSkill(nSkill, oCreature)` - Routine 286

- `286. GetHasSkill`
- Determine whether oCreature has nSkill, and nSkill is useable.
- - nSkill: SKILL_*
- - oCreature

- `nSkill`: int
- `oCreature`: object

<a id="getlastcombatfeatused"></a>

## `GetLastCombatFeatUsed(oAttacker)` - Routine 724

- `724. GetLastCombatFeatUsed`
- Returns the last feat used (as a feat number that indexes the Feats.2da) by the given object

- `oAttacker`: object

<a id="getmetamagicfeat"></a>

## `GetMetaMagicFeat()` - Routine 105

- `105. GetMetaMagicFeat`
- Get the metamagic type (METAMAGIC_*) of the last spell cast by the caller
- - Return value if the caster is not a valid object: -1

<a id="getskillrank"></a>

## `GetSkillRank(nSkill, oTarget)` - Routine 315

- `315. GetSkillRank`
- Get the number of ranks that oTarget has in nSkill.
- - nSkill: SKILL_*
- - oTarget
- - Returns -1 if oTarget doesn't have nSkill.
- - Returns 0 if nSkill is untrained.

- `nSkill`: int
- `oTarget`: object

<a id="talentfeat"></a>

## `TalentFeat(nFeat)` - Routine 302

- `302. TalentFeat`
- Create a Feat Talent.
- - nFeat: FEAT_*

- `nFeat`: int

<a id="talentskill"></a>

## `TalentSkill(nSkill)` - Routine 303

- `303. TalentSkill`
- Create a Skill Talent.
- - nSkill: SKILL_*

- `nSkill`: int

