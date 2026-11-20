from PySide6.QtCore import Qt
from choops_recomp.ui.app import RosterModel
from choops_recomp.ui.roster_filter import RosterFilter
from test_relationships import roster


def test_sorted_school_filter_preserves_edit_identity(qapp):
    model=roster();source=RosterModel(model,'players');proxy=RosterFilter(model,'players');proxy.setSourceModel(source);proxy.setSortRole(Qt.ItemDataRole.UserRole);proxy.school(0);proxy.sort(0,Qt.SortOrder.DescendingOrder)
    assert proxy.rowCount()==2 and proxy.mapToSource(proxy.index(0,0)).row()==1
    column=source.columns.index('jersey_number');assert proxy.setData(proxy.index(0,column),'42')
    assert model.rows['players'][1]['jersey_number']==42 and model.rows['players'][0]['jersey_number']==0
    proxy.school(1);assert proxy.rowCount()==1 and proxy.mapToSource(proxy.index(0,0)).row()==2


def test_search_and_unassigned_filters_combine_without_mutating_source(qapp):
    model=roster();model.set_string('players',3,'last_name','FindMe');before=bytes(model.data);source=RosterModel(model,'players');proxy=RosterFilter(model,'players');proxy.setSourceModel(source);proxy.school(-1)
    assert proxy.rowCount()==2;proxy.setFilterFixedString('findme');assert proxy.rowCount()==1 and proxy.mapToSource(proxy.index(0,0)).row()==3
    proxy.school(0);assert proxy.rowCount()==0;assert bytes(model.data)==before
