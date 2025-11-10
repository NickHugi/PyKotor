from pathlib import Path
import re

path = Path('105415.md')
text = path.read_text(encoding='utf-8')
lines = text.splitlines()

idx_keywords = next((i for i, l in enumerate(lines) if l.startswith('Keywords:')), None)
idx_abstract = next((i for i, l in enumerate(lines) if l.startswith('Abstract:')), None)
idx_intro = next((i for i, l in enumerate(lines) if l.startswith('1 INTRODUCTION')), None)

if None in (idx_keywords, idx_abstract, idx_intro):
    raise SystemExit('Required section not found')

keywords_line = lines[idx_keywords]
abstract_lines = lines[idx_abstract:idx_intro]
abstract_paragraph = '\n'.join(
    line.replace('Abstract:', '', 1).strip() if i == 0 else line
    for i, line in enumerate(abstract_lines)
)

header = "# Python and Malware: Developing Stealth and Evasive Malware without Obfuscation\n\n"
header += "<p><em>Vasilios Koutsokostas<sup>1</sup> and Constantinos Patsakis<sup>1,2</sup></em></p>\n\n"
header += (
    "<p><sup>1</sup> Institute of Problem Solving, Department of Informatics, University of Piraeus, Piraeus, Greece<br>\n"
    "<sup>2</sup> Information Management Systems Institute, Athena Research Center, Artemidos 6, Marousi 15125, Greece</p>\n\n"
)
header += f"**{keywords_line.replace('Keywords:', 'Keywords').strip()}**\n\n"
header += "## Abstract\n\n" + abstract_paragraph.strip() + "\n\n"
header += "## Table of Contents\n\n"
header += "- [1 Introduction](#1-introduction)\n"
header += "- [2 Related Work](#2-related-work)\n"
header += "- [3 Python & PyInstaller](#3-python--pyinstaller)\n"
header += "- [4 Conceptual Approach](#4-conceptual-approach)\n"
header += "  - [4.1 Bypassing Static Analysis](#41-bypassing-static-analysis)\n"
header += "  - [4.2 Bypassing Dynamic Analysis](#42-bypassing-dynamic-analysis)\n"
header += "- [5 Experimental Results](#5-experimental-results)\n"
header += "  - [5.1 Static Malware Analysis](#51-static-malware-analysis)\n"
header += "  - [5.2 Dynamic Analysis with Sandboxes](#52-dynamic-analysis-with-sandboxes)\n"
header += "- [6 Discussion](#6-discussion)\n"
header += "- [7 Conclusions](#7-conclusions)\n"
header += "- [Acknowledgements](#acknowledgements)\n"
header += "- [References](#references)\n\n"

remaining_text = '\n'.join(lines[idx_intro:])
content = header + remaining_text

replacements = {
    r'^1 INTRODUCTION': '## 1 Introduction',
    r'^2 RELATED WORK': '## 2 Related Work',
    r'^3 PYTHON & PYINSTALLER': '## 3 Python & PyInstaller',
    r'^4 CONCEPTUAL APPROACH': '## 4 Conceptual Approach',
    r'^4\.1 Bypassing Static Analysis': '### 4.1 Bypassing Static Analysis',
    r'^4\.2 Bypassing Dynamic Analysis': '### 4.2 Bypassing Dynamic Analysis',
    r'^5 EXPERIMENTAL RESULTS': '## 5 Experimental Results',
    r'^5\.1 Static Malware Analysis': '### 5.1 Static Malware Analysis',
    r'^5\.2 Dynamic Analysis with Sandboxes': '### 5.2 Dynamic Analysis with Sandboxes',
    r'^6 DISCUSSION': '## 6 Discussion',
    r'^7 CONCLUSIONS': '## 7 Conclusions',
    r'^ACKNOWLEDGEMENTS': '## Acknowledgements',
    r'^REFERENCES': '## References'
}

for pattern, repl in replacements.items():
    content = re.sub(pattern, repl, content, flags=re.MULTILINE)

content = re.sub(r'(Figure \d+:)', r'<strong>\1</strong>', content)
content = re.sub(r'(Listing 1:)', r'<strong>\1</strong>', content)
content = re.sub(r'(Algorithm 1:)', r'<strong>\1</strong>', content)
content = re.sub(r'(Table \d+:)', r'<strong>\1</strong>', content)

content = re.sub(
    r'<strong>Listing 1:</strong> ([^\n]+)\n((?:.+\n)+?)In what follows',
    lambda m: '<strong>Listing 1:</strong> ' + m.group(1).strip() + '\n\n`powershell\n' + '\n'.join(
        line.strip() for line in m.group(2).strip().splitlines()
    ) + '\n`\n\nIn what follows',
    content,
    flags=re.MULTILINE,
)

content = re.sub(
    r'<strong>Algorithm 1:</strong> Bypassing static analysis\.\n((?:.+\n)+?)### 4\.2',
    lambda m: '<strong>Algorithm 1:</strong> Bypassing static analysis.\n\n<ol>\n' + '\n'.join(
        f'<li>{line.strip()}</li>' for line in m.group(1).strip().split('\n') if line.strip()
    ) + '\n</ol>\n\n### 4.2',
    content,
    flags=re.MULTILINE,
)

content = content.replace('Abstract: ', '')
content = content.replace('\nAbstract:', '\n')

content = re.sub(
    r'<strong>Table 1:</strong> Linker flags for PyInstaller\.\n\nFlag Description\n/BASE:0x00400000 Set base to default Windows PE image\n/BASE\n/DYNAMICBASE:NO Disable dynamic base\n/VERSION:5\.2 Set image version\n/RELEASE Set the checksum of the file',
    '<strong>Table 1:</strong> Linker flags for PyInstaller.\n\n| Flag | Description |\n| --- | --- |\n| /BASE:0x00400000 | Set base to default Windows PE image base |\n| /DYNAMICBASE:NO | Disable dynamic base |\n| /VERSION:5.2 | Set image version |\n| /RELEASE | Set the checksum of the file |',
    content,
    flags=re.MULTILINE,
)

path.write_text(content, encoding='utf-8')
