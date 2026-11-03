from PySide6.QtWidgets import QMainWindow
from choops_recomp.ui.relationships import RelationshipsDialog
from choops_recomp import relationships
from test_relationships import roster


def test_relationship_dialog_applies_checked_links_and_rejects_unselected_text(qapp):
    class Parent(QMainWindow):
        def error(self,text):self.last_error=text
    parent=Parent();parent.last_error=None;model=roster();dialog=RelationshipsDialog(parent,model)
    combo=dialog.links['coach'];combo.setCurrentIndex(combo.findData(5));dialog.assign()
    assert relationships.team_links(model,0)['coach']==5 and len(model.history)==1
    before=bytes(model.data);combo.setEditText('Not a selected coach');dialog.assign()
    assert bytes(model.data)==before and 'Select a matching entry' in parent.last_error
    dialog.close();parent.close()
