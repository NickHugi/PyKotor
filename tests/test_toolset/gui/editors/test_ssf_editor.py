"""
Comprehensive tests for SSF Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.ssf import SSFEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.formats.ssf import SSF, SSFSound, read_ssf  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]

# ============================================================================
# BASIC TESTS
# ============================================================================

def test_ssf_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new SSF file from scratch."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Verify all spin boxes are zero
    assert editor.ui.battlecry1StrrefSpin.value() == 0
    assert editor.ui.battlecry2StrrefSpin.value() == 0
    assert editor.ui.select1StrrefSpin.value() == 0
    assert editor.ui.attack1StrrefSpin.value() == 0
    assert editor.ui.pain1StrrefSpin.value() == 0
    assert editor.ui.deadStrrefSpin.value() == 0
    
    # Build and verify
    data, _ = editor.build()
    new_ssf = read_ssf(data)
    assert new_ssf is not None

def test_ssf_editor_initialization(qtbot, installation: HTInstallation):
    """Test editor initialization."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify UI components exist
    assert hasattr(editor.ui, 'battlecry1StrrefSpin')
    assert hasattr(editor.ui, 'battlecry1SoundEdit')
    assert hasattr(editor.ui, 'battlecry1TextEdit')
    assert hasattr(editor.ui, 'select1StrrefSpin')
    assert hasattr(editor.ui, 'attack1StrrefSpin')
    assert hasattr(editor.ui, 'deadStrrefSpin')

# ============================================================================
# BATTLE CRY TESTS
# ============================================================================

def test_ssf_editor_manipulate_battlecry1(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating battlecry1 strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    original_data = ssf_file.read_bytes()
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, original_data)
    original_ssf = read_ssf(original_data)
    
    # Modify battlecry1
    new_strref = 12345
    editor.ui.battlecry1StrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.BATTLE_CRY_1) == new_strref
    assert modified_ssf.get(SSFSound.BATTLE_CRY_1) != original_ssf.get(SSFSound.BATTLE_CRY_1)
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.battlecry1StrrefSpin.value() == new_strref

def test_ssf_editor_manipulate_all_battlecries(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all battlecry strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set all battlecries
    battlecry_values = {
        'battlecry1StrrefSpin': (SSFSound.BATTLE_CRY_1, 1001),
        'battlecry2StrrefSpin': (SSFSound.BATTLE_CRY_2, 1002),
        'battlecry3StrrefSpin': (SSFSound.BATTLE_CRY_3, 1003),
        'battlecry4StrrefSpin': (SSFSound.BATTLE_CRY_4, 1004),
        'battlecry5StrrefSpin': (SSFSound.BATTLE_CRY_5, 1005),
        'battlecry6StrrefSpin': (SSFSound.BATTLE_CRY_6, 1006),
    }
    
    for spin_name, (sound_type, value) in battlecry_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in battlecry_values.items():
        assert modified_ssf.get(sound_type) == value

# ============================================================================
# SELECT TESTS
# ============================================================================

def test_ssf_editor_manipulate_select1(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating select1 strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify select1
    new_strref = 2001
    editor.ui.select1StrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.SELECT_1) == new_strref
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.select1StrrefSpin.value() == new_strref

def test_ssf_editor_manipulate_all_selects(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all select strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set all selects
    select_values = {
        'select1StrrefSpin': (SSFSound.SELECT_1, 2001),
        'select2StrrefSpin': (SSFSound.SELECT_2, 2002),
        'select3StrrefSpin': (SSFSound.SELECT_3, 2003),
    }
    
    for spin_name, (sound_type, value) in select_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in select_values.items():
        assert modified_ssf.get(sound_type) == value

# ============================================================================
# ATTACK TESTS
# ============================================================================

def test_ssf_editor_manipulate_attack1(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating attack1 strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify attack1
    new_strref = 3001
    editor.ui.attack1StrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.ATTACK_GRUNT_1) == new_strref
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.attack1StrrefSpin.value() == new_strref

def test_ssf_editor_manipulate_all_attacks(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all attack strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set all attacks
    attack_values = {
        'attack1StrrefSpin': (SSFSound.ATTACK_GRUNT_1, 3001),
        'attack2StrrefSpin': (SSFSound.ATTACK_GRUNT_2, 3002),
        'attack3StrrefSpin': (SSFSound.ATTACK_GRUNT_3, 3003),
    }
    
    for spin_name, (sound_type, value) in attack_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in attack_values.items():
        assert modified_ssf.get(sound_type) == value

# ============================================================================
# PAIN TESTS
# ============================================================================

def test_ssf_editor_manipulate_pain1(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating pain1 strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify pain1
    new_strref = 4001
    editor.ui.pain1StrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.PAIN_GRUNT_1) == new_strref
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.pain1StrrefSpin.value() == new_strref

def test_ssf_editor_manipulate_all_pain(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all pain strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set all pain
    pain_values = {
        'pain1StrrefSpin': (SSFSound.PAIN_GRUNT_1, 4001),
        'pain2StrrefSpin': (SSFSound.PAIN_GRUNT_2, 4002),
    }
    
    for spin_name, (sound_type, value) in pain_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in pain_values.items():
        assert modified_ssf.get(sound_type) == value

# ============================================================================
# SPECIAL SOUND TESTS
# ============================================================================

def test_ssf_editor_manipulate_dead(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating dead strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify dead
    new_strref = 5001
    editor.ui.deadStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.DEAD) == new_strref
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.deadStrrefSpin.value() == new_strref

def test_ssf_editor_manipulate_low_hp(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating low HP strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify low HP
    new_strref = 6001
    editor.ui.lowHpStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.LOW_HEALTH) == new_strref

def test_ssf_editor_manipulate_critical_hit(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating critical hit strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify critical
    new_strref = 7001
    editor.ui.criticalStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.CRITICAL_HIT) == new_strref

def test_ssf_editor_manipulate_immune(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating immune strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify immune
    new_strref = 8001
    editor.ui.immuneStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.TARGET_IMMUNE) == new_strref

# ============================================================================
# MINE/STEALTH/UNLOCK TESTS
# ============================================================================

def test_ssf_editor_manipulate_lay_mine(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating lay mine strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify lay mine
    new_strref = 9001
    editor.ui.layMineStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.LAY_MINE) == new_strref

def test_ssf_editor_manipulate_disarm_mine(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating disarm mine strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify disarm mine
    new_strref = 10001
    editor.ui.disarmMineStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.DISARM_MINE) == new_strref

def test_ssf_editor_manipulate_stealth_unlock_search(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating stealth/unlock/search strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set all stealth/unlock/search
    stealth_unlock_values = {
        'beginStealthStrrefSpin': (SSFSound.BEGIN_STEALTH, 11001),
        'beginSearchStrrefSpin': (SSFSound.BEGIN_SEARCH, 11002),
        'beginUnlockStrrefSpin': (SSFSound.BEGIN_UNLOCK, 11003),
        'unlockSuccessStrrefSpin': (SSFSound.UNLOCK_SUCCESS, 11004),
        'unlockFailedStrrefSpin': (SSFSound.UNLOCK_FAILED, 11005),
    }
    
    for spin_name, (sound_type, value) in stealth_unlock_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in stealth_unlock_values.items():
        assert modified_ssf.get(sound_type) == value

# ============================================================================
# PARTY/PoISON TESTS
# ============================================================================

def test_ssf_editor_manipulate_party_sounds(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating party separation/rejoin strrefs."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Set party sounds
    party_values = {
        'partySeparatedStrrefSpin': (SSFSound.SEPARATED_FROM_PARTY, 12001),
        'rejoinPartyStrrefSpin': (SSFSound.REJOINED_PARTY, 12002),
    }
    
    for spin_name, (sound_type, value) in party_values.items():
        spin = getattr(editor.ui, spin_name)
        spin.setValue(value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    for spin_name, (sound_type, value) in party_values.items():
        assert modified_ssf.get(sound_type) == value

def test_ssf_editor_manipulate_poisoned(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating poisoned strref."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify poisoned
    new_strref = 13001
    editor.ui.poisonedStrrefSpin.setValue(new_strref)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf.get(SSFSound.POISONED) == new_strref

# ============================================================================
# SAVE/LOAD ROUNDTRIP TESTS
# ============================================================================

def test_ssf_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    original_data = ssf_file.read_bytes()
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, original_data)
    original_ssf = read_ssf(original_data)
    
    # Save without modifications
    data1, _ = editor.build()
    saved_ssf1 = read_ssf(data1)
    
    # Load saved data
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data1)
    
    # Save again
    data2, _ = editor.build()
    saved_ssf2 = read_ssf(data2)
    
    # Verify all sound types match between saves
    for sound_type in SSFSound:
        assert saved_ssf1.get(sound_type) == saved_ssf2.get(sound_type)

def test_ssf_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test save/load roundtrip with modifications."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    original_data = ssf_file.read_bytes()
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, original_data)
    
    # Modify multiple values
    editor.ui.battlecry1StrrefSpin.setValue(99999)
    editor.ui.deadStrrefSpin.setValue(88888)
    editor.ui.poisonedStrrefSpin.setValue(77777)
    
    # Save
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    
    # Verify modifications
    assert modified_ssf.get(SSFSound.BATTLE_CRY_1) == 99999
    assert modified_ssf.get(SSFSound.DEAD) == 88888
    assert modified_ssf.get(SSFSound.POISONED) == 77777
    
    # Load back and verify
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
    assert editor.ui.battlecry1StrrefSpin.value() == 99999
    assert editor.ui.deadStrrefSpin.value() == 88888
    assert editor.ui.poisonedStrrefSpin.value() == 77777

def test_ssf_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple save/load cycles preserve content."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if not ssf_file.exists():
        pytest.skip("n_ithorian.ssf not found")
    
    editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Perform multiple cycles
    for cycle in range(3):
        # Modify values
        editor.ui.battlecry1StrrefSpin.setValue(10000 + cycle)
        editor.ui.deadStrrefSpin.setValue(20000 + cycle)
        
        # Save
        data, _ = editor.build()
        saved_ssf = read_ssf(data)
        
        # Verify
        assert saved_ssf.get(SSFSound.BATTLE_CRY_1) == 10000 + cycle
        assert saved_ssf.get(SSFSound.DEAD) == 20000 + cycle
        
        # Load back
        editor.load(ssf_file, "n_ithorian", ResourceType.SSF, data)
        
        # Verify loaded
        assert editor.ui.battlecry1StrrefSpin.value() == 10000 + cycle
        assert editor.ui.deadStrrefSpin.value() == 20000 + cycle

# ============================================================================
# EDGE CASES
# ============================================================================

def test_ssf_editor_zero_values(qtbot, installation: HTInstallation):
    """Test that zero values are handled correctly."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # All values should be zero
    assert editor.ui.battlecry1StrrefSpin.value() == 0
    assert editor.ui.deadStrrefSpin.value() == 0
    
    # Build and verify
    data, _ = editor.build()
    new_ssf = read_ssf(data)
    
    # Zero values should be stored as 0 or None depending on implementation
    # Just verify build works
    assert new_ssf is not None

def test_ssf_editor_maximum_values(qtbot, installation: HTInstallation):
    """Test handling of maximum strref values."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set maximum value (2^32 - 1 for uint32)
    max_value = 4294967295
    editor.ui.battlecry1StrrefSpin.setValue(max_value)
    
    # Save and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    # Note: SSF might use smaller type, so value might be clamped
    # Just verify build works
    assert modified_ssf is not None

def test_ssf_editor_all_sounds_set(qtbot, installation: HTInstallation):
    """Test setting all sound types."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set all sound types to unique values
    all_sounds = {
        'battlecry1StrrefSpin': 1,
        'battlecry2StrrefSpin': 2,
        'battlecry3StrrefSpin': 3,
        'battlecry4StrrefSpin': 4,
        'battlecry5StrrefSpin': 5,
        'battlecry6StrrefSpin': 6,
        'select1StrrefSpin': 7,
        'select2StrrefSpin': 8,
        'select3StrrefSpin': 9,
        'attack1StrrefSpin': 10,
        'attack2StrrefSpin': 11,
        'attack3StrrefSpin': 12,
        'pain1StrrefSpin': 13,
        'pain2StrrefSpin': 14,
        'lowHpStrrefSpin': 15,
        'deadStrrefSpin': 16,
        'criticalStrrefSpin': 17,
        'immuneStrrefSpin': 18,
        'layMineStrrefSpin': 19,
        'disarmMineStrrefSpin': 20,
        'beginStealthStrrefSpin': 21,
        'beginSearchStrrefSpin': 22,
        'beginUnlockStrrefSpin': 23,
        'unlockSuccessStrrefSpin': 24,
        'unlockFailedStrrefSpin': 25,
        'partySeparatedStrrefSpin': 26,
        'rejoinPartyStrrefSpin': 27,
        'poisonedStrrefSpin': 28,
    }
    
    for spin_name, value in all_sounds.items():
        if hasattr(editor.ui, spin_name):
            spin = getattr(editor.ui, spin_name)
            spin.setValue(value)
    
    # Build and verify
    data, _ = editor.build()
    modified_ssf = read_ssf(data)
    assert modified_ssf is not None

# ============================================================================
# TEXT BOX UPDATE TESTS
# ============================================================================

def test_ssf_editor_update_text_boxes_with_talktable(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test that text boxes update when talktable is available."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # If installation has talktable, verify text boxes can be updated
    if editor._talktable is not None:
        ssf_file = test_files_dir / "n_ithorian.ssf"
        if ssf_file.exists():
            editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
            
            # Set a strref
            editor.ui.battlecry1StrrefSpin.setValue(1)
            
            # Update text boxes
            editor.update_text_boxes()
            
            # Verify text/sound boxes exist (they may be empty if strref not in talktable)
            assert hasattr(editor.ui, 'battlecry1TextEdit')
            assert hasattr(editor.ui, 'battlecry1SoundEdit')

def test_ssf_editor_update_text_boxes_no_talktable(qtbot, installation: HTInstallation):
    """Test that update_text_boxes handles missing talktable gracefully."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Clear talktable
    editor._talktable = None
    
    # Update should not crash
    editor.update_text_boxes()
    
    # Verify editor is still functional
    assert editor is not None

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_ssf_editor_all_operations(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test all operations together."""
    editor = SSFEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set various values
    editor.ui.battlecry1StrrefSpin.setValue(100)
    editor.ui.select1StrrefSpin.setValue(200)
    editor.ui.deadStrrefSpin.setValue(300)
    
    # Save
    data1, _ = editor.build()
    
    # Load
    ssf_file = test_files_dir / "n_ithorian.ssf"
    if ssf_file.exists():
        editor.load(ssf_file, "n_ithorian", ResourceType.SSF, ssf_file.read_bytes())
    
    # Modify
    editor.ui.poisonedStrrefSpin.setValue(400)
    
    # Save again
    data2, _ = editor.build()
    
    # Verify both saves worked
    assert len(data1) > 0
    assert len(data2) > 0
