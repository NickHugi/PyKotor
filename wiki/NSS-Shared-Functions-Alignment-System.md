# Alignment System

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="adjustalignment"></a>

## `AdjustAlignment(oSubject, nAlignment, nShift)` - Routine 201

- `201. AdjustAlignment`
- Adjust the alignment of oSubject.
- - oSubject
- - nAlignment:
- -> ALIGNMENT_LIGHT_SIDE/ALIGNMENT_DARK_SIDE: oSubject's
- alignment will be shifted in the direction specified

- `oSubject`: object
- `nAlignment`: int
- `nShift`: int

<a id="getalignmentgoodevil"></a>

## `GetAlignmentGoodEvil(oCreature)` - Routine 127

- `127. GetAlignmentGoodEvil`
- Return an ALIGNMENT_* constant to represent oCreature's good/evil alignment
- - Return value if oCreature is not a valid creature: -1

- `oCreature`: object

<a id="getfactionaveragegoodevilalignment"></a>

## `GetFactionAverageGoodEvilAlignment(oFactionMember)` - Routine 187

- `187. GetFactionAverageGoodEvilAlignment`
- Get an integer between 0 and 100 (inclusive) that represents the average
- good/evil alignment of oFactionMember's faction.
- - Return value on error: -1

- `oFactionMember`: object

<a id="versusalignmenteffect"></a>

## `VersusAlignmentEffect(eEffect, nLawChaos, nGoodEvil)` - Routine 355

- `355. VersusAlignmentEffect`
- Set eEffect to be versus a specific alignment.
- - eEffect
- - nLawChaos: ALIGNMENT_LAWFUL/ALIGNMENT_CHAOTIC/ALIGNMENT_ALL
- - nGoodEvil: ALIGNMENT_GOOD/ALIGNMENT_EVIL/ALIGNMENT_ALL

- `eEffect`: effect
- `nLawChaos`: int (default: `0`)
- `nGoodEvil`: int (default: `0`)

