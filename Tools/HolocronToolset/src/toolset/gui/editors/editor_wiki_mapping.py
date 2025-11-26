"""Mapping of editors to their wiki documentation files."""

# Editor class name -> wiki markdown filename
EDITOR_WIKI_MAP: dict[str, str] = {
    "AREEditor": "GFF-File-Format.md",  # ARE section in GFF doc
    "BWMEditor": "BWM-File-Format.md",
    "DLGEditor": "GFF-File-Format.md",  # DLG section in GFF doc
    "ERFEditor": "ERF-File-Format.md",
    "GFFEditor": "GFF-File-Format.md",
    "GITEditor": "GFF-File-Format.md",  # GIT section in GFF doc
    "IFOEditor": "GFF-File-Format.md",  # IFO section in GFF doc
    "JRLEditor": "GFF-File-Format.md",  # JRL section in GFF doc
    "LTREditor": "LTR-File-Format.md",
    "LYTEditor": "LYT-File-Format.md",
    "LIPEditor": "LIP-File-Format.md",
    "MDLEditor": "MDL-MDX-File-Format.md",
    "NSSEditor": "NSS-File-Format.md",
    "NSEditor": "NCS-File-Format.md",  # NCS compiled from NSS
    "PTHEditor": "GFF-File-Format.md",  # PTH section in GFF doc
    "SAVEditor": "GFF-File-Format.md",  # SAV uses GFF format
    "SSFEditor": "SSF-File-Format.md",
    "TLKEditor": "TLK-File-Format.md",
    "TPCEditor": "TPC-File-Format.md",
    "TXTEditor": None,  # Plain text, no specific format
    "TwoDAEditor": "2DA-File-Format.md",
    "UTCEditor": "GFF-File-Format.md",  # UTC section in GFF doc
    "UTDEditor": "GFF-File-Format.md",  # UTD section in GFF doc
    "UTEEditor": "GFF-File-Format.md",  # UTE section in GFF doc
    "UTIEditor": "GFF-File-Format.md",  # UTI section in GFF doc
    "UTMEditor": "GFF-File-Format.md",  # UTM section in GFF doc
    "UTPEditor": "GFF-File-Format.md",  # UTP section in GFF doc
    "UTSEditor": "GFF-File-Format.md",  # UTS section in GFF doc
    "UTTEditor": "GFF-File-Format.md",  # UTT section in GFF doc
    "UTWEditor": "GFF-File-Format.md",  # UTW section in GFF doc
    "SaveGameEditor": "GFF-File-Format.md",  # Save game uses GFF
    "MetadataEditor": "GFF-File-Format.md",  # Metadata uses GFF
}

