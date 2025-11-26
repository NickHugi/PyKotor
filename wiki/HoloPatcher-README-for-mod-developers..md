_This page explains how to create a mod with HoloPatcher. If you are an end user you may be looking for [How to Use HoloPatcher](https://github.com/NickHugi/PyKotor/wiki/Installing-Mods-with-HoloPatcher)_

## Creating a HoloPatcher mod

HoloPatcher is a rewrite of TSLPatcher written in Python, utilizing the PyKotor library. Everything is backwards compatible with TSLPatcher. For this reason I suggest you first read [TSLPatcher's readme, really.](https://github.com/NickHugi/PyKotor/wiki/TSLPatcher's-Official-Readme)

## HoloPatcher changes & New Features

### TLK replacements

- This is not recommended under most scenarios. You usually want to append a new entry and update your DLGs to point to it using StrRef in the ini. However for projects like the k1cp and mods that fix grammatical/spelling mistakes, this may be useful.

The basic syntax is:

```ini
[TLKList]
ReplaceFile0=tlk_modifications_file.tlk

[tlk_modifications_file.tlk]
StrRef0=2
```

This will replace StrRef0 in dialog.tlk with StrRef2 from `tlk_modifications_file.tlk`.

[See our tests](https://github.com/NickHugi/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/tests/test_tslpatcher/test_reader.py#L463) for more examples.
Don't use the 'ignore' syntax or the 'range' syntax, these won't be documented or supported until further notice.

### HACKList (Editing NCS directly)

This is a TSLPatcher feature that was [not documented in the TSLPatcher readme.](https://github.com/NickHugi/PyKotor/wiki/TSLPatcher's-Official-Readme). We can only guess why this is. The only known uses we know about are [Stoffe's HLFP mod](https://deadlystream.com/files/file/832-high-level-force-powers/) and some starwarsknights/lucasforums archives on waybackmachine pointing to files that are unavailable.

Due to this feature being highly undocumented and only one known usage, our implementation might not match exactly. If you happen to find an old TSLPatcher mod that produces different HACKList results than HoloPatcher, [please report them here](https://github.com/NickHugi/PyKotor/issues/24)

In continuation, HoloPatcher's [HACKList] will use the following syntax:

```ini
[HACKList]
File0=script_to_modify.NCS

[script_to_modify.ncs]
20=StrRef5
40=2DAMEMORY10
60=65535
```

This will:

- Modify offset dec 20 (hex 0x14) of `script_to_modify.ncs` and overwrite that offset with the value of StrRef5.
- Modify offset dec 40 (hex 0x28) of `script_to_modify.ncs` and overwrite that offset with the value of 2DAMEMORY10.
- Modify offset dec 60 (hex 0x3C) of `script_to_modify.ncs` and overwrite that offset with the value of dec 65535 (hex 0xFFFF) i.e. the maximum possible value.
In summary, HACKList writes unsigned WORDs (sized at two bytes) to offsets in the NCS specified by the ini.

### For more information on HoloPatcher's implementation, please see the following links

#### [pykotor.tslpatcher.reader](https://github.com/NickHugi/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/Libraries/PyKotor/src/pykotor/tslpatcher/reader.py#L697)

#### [pykotor.tslpatcher.mods.ncs](https://github.com/NickHugi/PyKotor/blob/92f5fb81a7b9642085c67b7b48ddd50f2df4378d/Libraries/PyKotor/src/pykotor/tslpatcher/mods/ncs.py)
