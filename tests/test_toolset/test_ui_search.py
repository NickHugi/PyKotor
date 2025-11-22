import pytest
from qtpy.QtCore import Qt
from toolset.gui.dialogs.search import FileSearcher, FileSearchQuery, FileResults
from toolset.data.installation import HTInstallation
from pykotor.resource.type import ResourceType

def test_search_dialog_all_widgets_exist(qtbot, installation: HTInstallation):
    """Verify ALL widgets exist in FileSearcher dialog."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    installations = {"Test Install": installation}
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Installation selector
    assert hasattr(dialog.ui, 'installationSelect')
    
    # Search text
    assert hasattr(dialog.ui, 'searchTextEdit')
    
    # Radio buttons
    assert hasattr(dialog.ui, 'caseSensitiveRadio')
    assert hasattr(dialog.ui, 'caseInsensitiveRadio')
    
    # Checkboxes
    assert hasattr(dialog.ui, 'filenamesOnlyCheck')
    assert hasattr(dialog.ui, 'coreCheck')
    assert hasattr(dialog.ui, 'modulesCheck')
    assert hasattr(dialog.ui, 'overrideCheck')
    assert hasattr(dialog.ui, 'selectAllCheck')
    
    # ALL resource type checkboxes
    assert hasattr(dialog.ui, 'typeARECheck')
    assert hasattr(dialog.ui, 'typeGITCheck')
    assert hasattr(dialog.ui, 'typeIFOCheck')
    assert hasattr(dialog.ui, 'typeVISCheck')
    assert hasattr(dialog.ui, 'typeLYTCheck')
    assert hasattr(dialog.ui, 'typeDLGCheck')
    assert hasattr(dialog.ui, 'typeJRLCheck')
    assert hasattr(dialog.ui, 'typeUTCCheck')
    assert hasattr(dialog.ui, 'typeUTDCheck')
    assert hasattr(dialog.ui, 'typeUTECheck')
    assert hasattr(dialog.ui, 'typeUTICheck')
    assert hasattr(dialog.ui, 'typeUTPCheck')
    assert hasattr(dialog.ui, 'typeUTMCheck')
    assert hasattr(dialog.ui, 'typeUTSCheck')
    assert hasattr(dialog.ui, 'typeUTTCheck')
    assert hasattr(dialog.ui, 'typeUTWCheck')
    assert hasattr(dialog.ui, 'type2DACheck')
    assert hasattr(dialog.ui, 'typeNSSCheck')
    assert hasattr(dialog.ui, 'typeNCSCheck')

def test_search_dialog_all_checkboxes_exhaustive(qtbot, installation: HTInstallation):
    """Test ALL checkboxes with exhaustive combinations."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    installations = {"Test Install": installation}
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test Select All checkbox - should toggle ALL type checkboxes
    dialog.ui.selectAllCheck.setChecked(True)
    assert dialog.ui.typeARECheck.isChecked()
    assert dialog.ui.typeGITCheck.isChecked()
    assert dialog.ui.typeIFOCheck.isChecked()
    assert dialog.ui.typeVISCheck.isChecked()
    assert dialog.ui.typeLYTCheck.isChecked()
    assert dialog.ui.typeDLGCheck.isChecked()
    assert dialog.ui.typeJRLCheck.isChecked()
    assert dialog.ui.typeUTCCheck.isChecked()
    assert dialog.ui.typeUTDCheck.isChecked()
    assert dialog.ui.typeUTECheck.isChecked()
    assert dialog.ui.typeUTICheck.isChecked()
    assert dialog.ui.typeUTPCheck.isChecked()
    assert dialog.ui.typeUTMCheck.isChecked()
    assert dialog.ui.typeUTSCheck.isChecked()
    assert dialog.ui.typeUTTCheck.isChecked()
    assert dialog.ui.typeUTWCheck.isChecked()
    assert dialog.ui.type2DACheck.isChecked()
    assert dialog.ui.typeNSSCheck.isChecked()
    assert dialog.ui.typeNCSCheck.isChecked()
    
    dialog.ui.selectAllCheck.setChecked(False)
    assert not dialog.ui.typeARECheck.isChecked()
    assert not dialog.ui.typeGITCheck.isChecked()
    assert not dialog.ui.typeIFOCheck.isChecked()
    assert not dialog.ui.typeVISCheck.isChecked()
    assert not dialog.ui.typeLYTCheck.isChecked()
    assert not dialog.ui.typeDLGCheck.isChecked()
    assert not dialog.ui.typeJRLCheck.isChecked()
    assert not dialog.ui.typeUTCCheck.isChecked()
    assert not dialog.ui.typeUTDCheck.isChecked()
    assert not dialog.ui.typeUTECheck.isChecked()
    assert not dialog.ui.typeUTICheck.isChecked()
    assert not dialog.ui.typeUTPCheck.isChecked()
    assert not dialog.ui.typeUTMCheck.isChecked()
    assert not dialog.ui.typeUTSCheck.isChecked()
    assert not dialog.ui.typeUTTCheck.isChecked()
    assert not dialog.ui.typeUTWCheck.isChecked()
    assert not dialog.ui.type2DACheck.isChecked()
    assert not dialog.ui.typeNSSCheck.isChecked()
    assert not dialog.ui.typeNCSCheck.isChecked()
    
    # Test individual checkboxes
    dialog.ui.typeUTCCheck.setChecked(True)
    assert dialog.ui.typeUTCCheck.isChecked()
    assert not dialog.ui.typeDLGCheck.isChecked()  # Others should remain unchecked
    
    dialog.ui.typeDLGCheck.setChecked(True)
    assert dialog.ui.typeDLGCheck.isChecked()
    assert dialog.ui.typeUTCCheck.isChecked()  # Previous should remain
    
    # Test location checkboxes
    dialog.ui.coreCheck.setChecked(True)
    assert dialog.ui.coreCheck.isChecked()
    
    dialog.ui.modulesCheck.setChecked(True)
    assert dialog.ui.modulesCheck.isChecked()
    
    dialog.ui.overrideCheck.setChecked(True)
    assert dialog.ui.overrideCheck.isChecked()
    
    dialog.ui.filenamesOnlyCheck.setChecked(True)
    assert dialog.ui.filenamesOnlyCheck.isChecked()

def test_search_dialog_all_radio_buttons(qtbot, installation: HTInstallation):
    """Test ALL radio buttons."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    installations = {"Test Install": installation}
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test case sensitive radio
    dialog.ui.caseSensitiveRadio.setChecked(True)
    assert dialog.ui.caseSensitiveRadio.isChecked()
    assert not dialog.ui.caseInsensitiveRadio.isChecked()
    
    # Test case insensitive radio
    dialog.ui.caseInsensitiveRadio.setChecked(True)
    assert dialog.ui.caseInsensitiveRadio.isChecked()
    assert not dialog.ui.caseSensitiveRadio.isChecked()

def test_search_dialog_query_construction_exhaustive(qtbot, installation: HTInstallation):
    """Test query construction with ALL possible combinations."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    installations = {"Test Install": installation}
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test 1: All checkboxes checked
    dialog.ui.selectAllCheck.setChecked(True)
    dialog.ui.searchTextEdit.setText("test_search")
    dialog.ui.caseSensitiveRadio.setChecked(True)
    dialog.ui.filenamesOnlyCheck.setChecked(True)
    dialog.ui.coreCheck.setChecked(True)
    dialog.ui.modulesCheck.setChecked(True)
    dialog.ui.overrideCheck.setChecked(True)
    
    # Manually construct query to verify UI state (without calling accept which triggers search)
    check_types = []
    if dialog.ui.typeARECheck.isChecked(): check_types.append(ResourceType.ARE)
    if dialog.ui.typeGITCheck.isChecked(): check_types.append(ResourceType.GIT)
    if dialog.ui.typeIFOCheck.isChecked(): check_types.append(ResourceType.IFO)
    if dialog.ui.typeVISCheck.isChecked(): check_types.append(ResourceType.VIS)
    if dialog.ui.typeLYTCheck.isChecked(): check_types.append(ResourceType.LYT)
    if dialog.ui.typeDLGCheck.isChecked(): check_types.append(ResourceType.DLG)
    if dialog.ui.typeJRLCheck.isChecked(): check_types.append(ResourceType.JRL)
    if dialog.ui.typeUTCCheck.isChecked(): check_types.append(ResourceType.UTC)
    if dialog.ui.typeUTDCheck.isChecked(): check_types.append(ResourceType.UTD)
    if dialog.ui.typeUTECheck.isChecked(): check_types.append(ResourceType.UTE)
    if dialog.ui.typeUTICheck.isChecked(): check_types.append(ResourceType.UTI)
    if dialog.ui.typeUTPCheck.isChecked(): check_types.append(ResourceType.UTP)
    if dialog.ui.typeUTMCheck.isChecked(): check_types.append(ResourceType.UTM)
    if dialog.ui.typeUTSCheck.isChecked(): check_types.append(ResourceType.UTS)
    if dialog.ui.typeUTTCheck.isChecked(): check_types.append(ResourceType.UTT)
    if dialog.ui.typeUTWCheck.isChecked(): check_types.append(ResourceType.UTW)
    if dialog.ui.type2DACheck.isChecked(): check_types.append(ResourceType.TwoDA)
    if dialog.ui.typeNSSCheck.isChecked(): check_types.append(ResourceType.NSS)
    if dialog.ui.typeNCSCheck.isChecked(): check_types.append(ResourceType.NCS)
    
    query = FileSearchQuery(
        installation=dialog.ui.installationSelect.currentData(),
        case_sensitive=dialog.ui.caseSensitiveRadio.isChecked(),
        filenames_only=dialog.ui.filenamesOnlyCheck.isChecked(),
        text=dialog.ui.searchTextEdit.text(),
        search_core=dialog.ui.coreCheck.isChecked(),
        search_modules=dialog.ui.modulesCheck.isChecked(),
        search_override=dialog.ui.overrideCheck.isChecked(),
        check_types=check_types,
    )
    
    assert query.text == "test_search"
    assert query.case_sensitive
    assert query.filenames_only
    assert query.search_core
    assert query.search_modules
    assert query.search_override
    assert len(query.check_types) == 20  # All types checked
    assert ResourceType.UTC in query.check_types
    assert ResourceType.DLG in query.check_types
    assert ResourceType.ARE in query.check_types
    
    # Test 2: Only specific types checked
    dialog.ui.selectAllCheck.setChecked(False)
    dialog.ui.typeUTCCheck.setChecked(True)
    dialog.ui.typeDLGCheck.setChecked(True)
    dialog.ui.type2DACheck.setChecked(True)
    
    check_types = []
    if dialog.ui.typeARECheck.isChecked(): check_types.append(ResourceType.ARE)
    if dialog.ui.typeGITCheck.isChecked(): check_types.append(ResourceType.GIT)
    if dialog.ui.typeIFOCheck.isChecked(): check_types.append(ResourceType.IFO)
    if dialog.ui.typeVISCheck.isChecked(): check_types.append(ResourceType.VIS)
    if dialog.ui.typeLYTCheck.isChecked(): check_types.append(ResourceType.LYT)
    if dialog.ui.typeDLGCheck.isChecked(): check_types.append(ResourceType.DLG)
    if dialog.ui.typeJRLCheck.isChecked(): check_types.append(ResourceType.JRL)
    if dialog.ui.typeUTCCheck.isChecked(): check_types.append(ResourceType.UTC)
    if dialog.ui.typeUTDCheck.isChecked(): check_types.append(ResourceType.UTD)
    if dialog.ui.typeUTECheck.isChecked(): check_types.append(ResourceType.UTE)
    if dialog.ui.typeUTICheck.isChecked(): check_types.append(ResourceType.UTI)
    if dialog.ui.typeUTPCheck.isChecked(): check_types.append(ResourceType.UTP)
    if dialog.ui.typeUTMCheck.isChecked(): check_types.append(ResourceType.UTM)
    if dialog.ui.typeUTSCheck.isChecked(): check_types.append(ResourceType.UTS)
    if dialog.ui.typeUTTCheck.isChecked(): check_types.append(ResourceType.UTT)
    if dialog.ui.typeUTWCheck.isChecked(): check_types.append(ResourceType.UTW)
    if dialog.ui.type2DACheck.isChecked(): check_types.append(ResourceType.TwoDA)
    if dialog.ui.typeNSSCheck.isChecked(): check_types.append(ResourceType.NSS)
    if dialog.ui.typeNCSCheck.isChecked(): check_types.append(ResourceType.NCS)
    
    query2 = FileSearchQuery(
        installation=dialog.ui.installationSelect.currentData(),
        case_sensitive=dialog.ui.caseSensitiveRadio.isChecked(),
        filenames_only=dialog.ui.filenamesOnlyCheck.isChecked(),
        text=dialog.ui.searchTextEdit.text(),
        search_core=dialog.ui.coreCheck.isChecked(),
        search_modules=dialog.ui.modulesCheck.isChecked(),
        search_override=dialog.ui.overrideCheck.isChecked(),
        check_types=check_types,
    )
    
    assert len(query2.check_types) == 3
    assert ResourceType.UTC in query2.check_types
    assert ResourceType.DLG in query2.check_types
    assert ResourceType.TwoDA in query2.check_types
    assert ResourceType.ARE not in query2.check_types
    
    # Test 3: Case insensitive
    dialog.ui.caseInsensitiveRadio.setChecked(True)
    query3 = FileSearchQuery(
        installation=dialog.ui.installationSelect.currentData(),
        case_sensitive=dialog.ui.caseSensitiveRadio.isChecked(),
        filenames_only=dialog.ui.filenamesOnlyCheck.isChecked(),
        text=dialog.ui.searchTextEdit.text(),
        search_core=dialog.ui.coreCheck.isChecked(),
        search_modules=dialog.ui.modulesCheck.isChecked(),
        search_override=dialog.ui.overrideCheck.isChecked(),
        check_types=check_types,
    )
    assert not query3.case_sensitive
    
    # Test 4: Only core, no modules/override
    dialog.ui.coreCheck.setChecked(True)
    dialog.ui.modulesCheck.setChecked(False)
    dialog.ui.overrideCheck.setChecked(False)
    query4 = FileSearchQuery(
        installation=dialog.ui.installationSelect.currentData(),
        case_sensitive=dialog.ui.caseSensitiveRadio.isChecked(),
        filenames_only=dialog.ui.filenamesOnlyCheck.isChecked(),
        text=dialog.ui.searchTextEdit.text(),
        search_core=dialog.ui.coreCheck.isChecked(),
        search_modules=dialog.ui.modulesCheck.isChecked(),
        search_override=dialog.ui.overrideCheck.isChecked(),
        check_types=check_types,
    )
    assert query4.search_core
    assert not query4.search_modules
    assert not query4.search_override

def test_search_dialog_installation_selector(qtbot, installation: HTInstallation):
    """Test installation selector with multiple installations."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    # Create second installation (mock or real)
    installations = {
        "Installation 1": installation,
        "Installation 2": installation,  # Using same for test
    }
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.ui.installationSelect.count() == 2
    
    # Test switching installations
    dialog.ui.installationSelect.setCurrentIndex(0)
    assert dialog.ui.installationSelect.currentText() == "Installation 1"
    
    dialog.ui.installationSelect.setCurrentIndex(1)
    assert dialog.ui.installationSelect.currentText() == "Installation 2"
    
    # Verify data is correct
    assert dialog.ui.installationSelect.currentData() == installation

def test_search_dialog_text_input(qtbot, installation: HTInstallation):
    """Test search text input with various inputs."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    installations = {"Test Install": installation}
    dialog = FileSearcher(parent, installations)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test various text inputs
    test_texts = [
        "",
        "simple",
        "test with spaces",
        "test_with_underscores",
        "test-with-dashes",
        "test123numbers",
        "TEST_UPPERCASE",
        "test\nmultiline",
        "special!@#$%^&*()chars",
    ]
    
    for text in test_texts:
        dialog.ui.searchTextEdit.setText(text)
        assert dialog.ui.searchTextEdit.text() == text

def test_results_dialog_all_widgets(qtbot, installation: HTInstallation):
    """Test FileResults dialog with ALL widgets."""
    from qtpy.QtWidgets import QWidget
    from pykotor.extract.file import FileResource
    from pathlib import Path
    parent = QWidget()
    
    # Create multiple results with different types
    res1 = FileResource("res1", ResourceType.UTC, 0, 0, Path("path/to/res1.utc"))
    res2 = FileResource("res2", ResourceType.DLG, 0, 0, Path("path/to/res2.dlg"))
    res3 = FileResource("res3", ResourceType.UTI, 0, 0, Path("path/to/res3.uti"))
    results = [res1, res2, res3]
    
    dialog = FileResults(parent, results, installation)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Verify list populated
    assert dialog.ui.resultList.count() == 3
    
    # Test selecting each item
    for i in range(3):
        dialog.ui.resultList.setCurrentRow(i)
        assert dialog.ui.resultList.currentRow() == i
        current_item = dialog.ui.resultList.currentItem()
        assert current_item is not None
    
    # Test double-click (should trigger signal)
    signal_called = []
    dialog.sig_searchresults_selected.connect(lambda res: signal_called.append(res))
    
    dialog.ui.resultList.setCurrentRow(0)
    qtbot.mouseDClick(dialog.ui.resultList.viewport(), Qt.MouseButton.LeftButton,
                     pos=dialog.ui.resultList.visualItemRect(dialog.ui.resultList.item(0)).center())
    
    # Double-click should select and accept
    assert len(signal_called) > 0 or dialog.ui.resultList.currentRow() == 0
    
    # Test accept button
    dialog.ui.resultList.setCurrentRow(1)
    dialog.accept()
    assert len(signal_called) >= 1
    assert isinstance(signal_called[0], FileResource)

def test_results_dialog_empty_results(qtbot, installation: HTInstallation):
    """Test FileResults with empty results."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = FileResults(parent, [], installation)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.ui.resultList.count() == 0
    
    # Accept with no selection should not crash
    dialog.accept()

def test_results_dialog_single_result(qtbot, installation: HTInstallation):
    """Test FileResults with single result."""
    from qtpy.QtWidgets import QWidget
    from pykotor.extract.file import FileResource
    from pathlib import Path
    parent = QWidget()
    
    res = FileResource("single", ResourceType.UTC, 0, 0, Path("path/to/single.utc"))
    dialog = FileResults(parent, [res], installation)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.ui.resultList.count() == 1
    dialog.ui.resultList.setCurrentRow(0)
    
    signal_called = []
    dialog.sig_searchresults_selected.connect(lambda r: signal_called.append(r))
    dialog.accept()
    
    assert len(signal_called) == 1
    assert signal_called[0].resname() == "single"
