"""Roster filtering that retains source row identity for every edit/action."""
from PySide6.QtCore import QSortFilterProxyModel,Qt


class RosterFilter(QSortFilterProxyModel):
    def __init__(self,document,table,parent=None):
        super().__init__(parent);self.document=document;self.table=table;self.allowed=None;self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive);self.setFilterKeyColumn(-1);self.setDynamicSortFilter(True)
    def school(self,index):
        self.allowed=None
        if index is not None:
            from ..relationships import catalog
            from ..uniforms import owner,rows
            state=catalog(self.document)
            if index==-1:
                self.allowed=set(range(len(self.document.rows['players'])))-set(state['schools']) if self.table=='players' else set()
            else:
                team=state['teams'][index]
                if self.table=='players':self.allowed=set(team['players'])
                elif self.table=='teams':self.allowed={index}
                elif self.table=='coaches':self.allowed={team[k] for k in ('coach','assistant1','assistant2') if team[k] is not None}
                elif self.table=='arenas':self.allowed={team['arena']} if team['arena'] is not None else set()
                elif self.table=='conferences':self.allowed={team['conference']} if team['conference'] is not None else set()
                elif self.table=='uniforms':self.allowed={r['index'] for r in rows(self.document) if r['owner']==owner(self.document,index)}
        self.invalidate()
    def filterAcceptsRow(self,row,parent):return (self.allowed is None or row in self.allowed) and super().filterAcceptsRow(row,parent)
