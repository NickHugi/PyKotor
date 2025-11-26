import json
from pathlib import Path

wizard_path = Path('c:/Users/boden/Downloads/wizard.indoor')
wiz2_path = Path('c:/Users/boden/Downloads/wiz2.indoor')

wizard_data = json.loads(wizard_path.read_text())
wiz2_data = json.loads(wiz2_path.read_text())

print('=== KEY DIFFERENCES ===')
print('\nwizard.indoor (broken) Room 1:')
r1 = wizard_data['rooms'][1]
comp1 = r1['component']
print(f'  Component: {comp1}')
print(f'  Has flip_x: {"flip_x" in r1}')
print(f'  Has flip_y: {"flip_y" in r1}')
if 'flip_x' in r1:
    print(f'  flip_x = {r1["flip_x"]} (type: {type(r1["flip_x"]).__name__})')
if 'flip_y' in r1:
    print(f'  flip_y = {r1["flip_y"]} (type: {type(r1["flip_y"]).__name__})')
print(f'  rotation = {r1["rotation"]}')

print('\nwiz2.indoor (working) Room 1:')
r2 = wiz2_data['rooms'][1]
comp2 = r2['component']
print(f'  Component: {comp2}')
print(f'  Has flip_x: {"flip_x" in r2}')
print(f'  Has flip_y: {"flip_y" in r2}')
if 'flip_x' in r2:
    print(f'  flip_x = {r2["flip_x"]} (type: {type(r2["flip_x"]).__name__})')
if 'flip_y' in r2:
    print(f'  flip_y = {r2["flip_y"]} (type: {type(r2["flip_y"]).__name__})')
print(f'  rotation = {r2["rotation"]}')

print('\n=== LOAD SIMULATION ===')
def simulate_load(room_data):
    flip_x = bool(room_data.get('flip_x', False))
    flip_y = bool(room_data.get('flip_y', False))
    return flip_x, flip_y

fx1, fy1 = simulate_load(r1)
fx2, fy2 = simulate_load(r2)
print(f'wizard.indoor loads as: flip_x={fx1}, flip_y={fy1}')
print(f'wiz2.indoor loads as: flip_x={fx2}, flip_y={fy2}')
print(f'\nBoth result in same values? {fx1 == fx2 and fy1 == fy2}')

print('\n=== ROTATION DIFFERENCES ===')
print(f'wizard.indoor rotations: {[r["rotation"] for r in wizard_data["rooms"]]}')
print(f'wiz2.indoor rotations: {[r["rotation"] for r in wiz2_data["rooms"]]}')



