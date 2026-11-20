"""School relationship and membership controls backed by checked Xbox writers."""
from PySide6.QtCore import Signal,Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLabel,QListWidget,QPushButton,QDialogButtonBox
from .. import relationships as links


def caption(model,table,index):
    row=model.row(table,index)
    if table=='players':return f"{row['first_name']} {row['last_name']} • #{row['jersey_number']} • {index}"
    return str(row.get('school_name') or row.get('name') or row.get('short_name') or f'{table} {index}')+f' [{index}]'


def picker(model,table,nullable=True):
    combo=QComboBox();combo.setEditable(True);combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    if nullable:combo.addItem('Unassigned',None)
    for row in model.rows[table]:combo.addItem(caption(model,table,row['index']),row['index'])
    combo.completer().setFilterMode(Qt.MatchFlag.MatchContains);return combo


def selected(combo):
    index=combo.currentIndex()
    if index<0 or combo.currentText()!=combo.itemText(index):raise ValueError('Select a matching entry from the list before applying changes')
    return combo.currentData()


class RelationshipsDialog(QDialog):
    changed=Signal()
    def __init__(self,parent,model,team=0):
        super().__init__(parent);self.model=model;self.setWindowTitle('Xbox school relationships');self.resize(1050,850);layout=QVBoxLayout(self)
        self.school=picker(model,'teams',False);layout.addWidget(self.school);self.summary=QLabel();self.summary.setWordWrap(True);layout.addWidget(self.summary)
        form=QFormLayout();self.links={}
        for name,(offset,table,bias) in links.REFERENCES.items():self.links[name]=picker(model,table);form.addRow(name.replace('_',' ').title(),self.links[name])
        layout.addLayout(form);apply=QPushButton('Apply relationship changes');apply.clicked.connect(self.assign);layout.addWidget(apply)
        self.members=QListWidget();layout.addWidget(self.members,1);row=QHBoxLayout()
        for title,callback in [('Move up',lambda:self.reorder(-1)),('Move down',lambda:self.reorder(1)),('Unassign selected player',self.remove)]:button=QPushButton(title);button.clicked.connect(callback);row.addWidget(button)
        layout.addLayout(row);self.player=picker(model,'players',False);layout.addWidget(self.player);transfer=QPushButton('Transfer selected player into this school');transfer.clicked.connect(self.transfer);layout.addWidget(transfer)
        layout.addWidget(QLabel('Changes are undoable in memory. Use Save roster in the main window to write the loose ROST file.'))
        close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.rejected.connect(self.reject);layout.addWidget(close);self.school.currentIndexChanged.connect(self.reload);self.school.setCurrentIndex(self.school.findData(team));self.reload()
    def reload(self):
        try:
            team=selected(self.school);self.state=links.catalog(self.model);current=self.state['teams'][team]
            for name,combo in self.links.items():combo.setCurrentIndex(combo.findData(current[name]))
            self.members.clear()
            for player in current['players']:self.members.addItem(caption(self.model,'players',player))
            conf=current['conference'];names=[] if conf is None else [self.model.rows['teams'][i]['short_name'] for i in self.state['conferences'][conf]]
            self.summary.setText(f"{len(current['players'])}/18 player slots • Conference members: "+', '.join(names))
        except (ValueError,KeyError,TypeError) as exc:self.parent().error(str(exc))
    def perform(self,operation):
        try:operation();self.reload();self.changed.emit()
        except (ValueError,OSError) as exc:self.parent().error(str(exc))
    def assign(self):
        def operation():
            team=selected(self.school);values={name:selected(combo) for name,combo in self.links.items()}
            with self.model.transaction():
                for name,value in values.items():
                    if links.team_links(self.model,team)[name]!=value:links.assign(self.model,team,name,value)
        self.perform(operation)
    def transfer(self):self.perform(lambda:links.move_player(self.model,selected(self.player),selected(self.school)))
    def remove(self):
        def operation():
            row=self.members.currentRow();team=selected(self.school)
            if row>=0:links.move_player(self.model,self.state['teams'][team]['players'][row],None)
        self.perform(operation)
    def reorder(self,delta):
        def operation():
            row=self.members.currentRow();team=selected(self.school);values=self.state['teams'][team]['players'];destination=row+delta
            if 0<=row<len(values) and 0<=destination<len(values):links.reorder_player(self.model,team,values[row],destination)
        row=self.members.currentRow();self.perform(operation);self.members.setCurrentRow(max(0,row+delta))
