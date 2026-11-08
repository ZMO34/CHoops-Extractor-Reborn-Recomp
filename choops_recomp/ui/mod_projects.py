"""Compact project area; existing editors operate on independent bank copies."""
import json
from pathlib import Path

from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QPlainTextEdit,QFileDialog,QInputDialog,QComboBox,QDialog

from ..mod_project import ModProject,read_json


class ModProjects(QWidget):
    def __init__(self, studio):
        super().__init__();self.studio=studio;self.project=None
        layout=QVBoxLayout(self)
        label=QLabel('Create a private mod project, add source banks, then edit their copies in the existing tabs.\nExport validates against the selected runtime. Direct editing remains available through File → Open assets folder.');label.setWordWrap(True);layout.addWidget(label)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Create Mod…',self.create),('Open Project…',self.open),('Save metadata',self.save)]:
            button=QPushButton(title);button.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(button)
        self.location=QLabel('No project open');self.location.setWordWrap(True);layout.addWidget(self.location)
        self.description=QLineEdit();self.description.setPlaceholderText('Author description (project-only; canonical mod.json has no description field)');layout.addWidget(self.description)
        layout.addWidget(QLabel('Project manifest metadata: version, exact dependencies, compatibility, update_source. Generated content/assets are refreshed on export.'))
        self.metadata=QPlainTextEdit();self.metadata.setMaximumHeight(200);layout.addWidget(self.metadata)
        row=QHBoxLayout();layout.addLayout(row);self.banks=QComboBox();row.addWidget(self.banks,1)
        for title,fn in [('Add source bank copy',self.add_bank),('Edit project copies',self.edit),('Compare selected texture',self.compare)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(b)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Attach native roster + header…',self.roster),('Attach uniform bank…',self.uniform),('Attach compiled DLL…',self.extension),('Review differences',self.review),('Export .chmod…',self.export)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(b)
        warning=QLabel('Hooks/Code: only player.weight.read / ABI 1 is exposed. DLLs execute with full user access when enabled by the launcher. Studio never loads them.\nRoster: actual Roster.ROS + its own header only. No loose-ROST conversion or existing Legacy migration.\nSCNE: source-compatible cloth positions only. Scorebug, menu and Legacy hooks remain unsupported.');warning.setWordWrap(True);layout.addWidget(warning)
        self.report=QPlainTextEdit();self.report.setReadOnly(True);layout.addWidget(self.report,1)

    def invoke(self, fn):
        try:fn()
        except Exception as exc:self.studio.error(str(exc))

    def require(self):
        if self.project is None:raise ValueError('Create or open a mod project first')
        return self.project

    def create(self):
        if not self.studio.maybe_save():return
        assets=QFileDialog.getExistingDirectory(self,'Read-only installed Xbox assets folder')
        if not assets:return
        runtime=QFileDialog.getExistingDirectory(self,'Runtime root containing tools/chmod.ps1 and docs/formats')
        if not runtime:return
        destination,_=QFileDialog.getSaveFileName(self,'New project directory (must not exist)')
        if not destination:return
        values=[]
        for label in ('Mod ID (author.mod-name)','Mod name','Author'):
            value,ok=QInputDialog.getText(self,'Create Mod',label)
            if not ok:return
            values.append(value)
        self.project=ModProject.create(destination,assets,runtime,*values);self.refresh();self.activate()

    def open(self):
        if not self.studio.maybe_save():return
        path=QFileDialog.getExistingDirectory(self,'Open mod project directory')
        if path:self.project=ModProject(path);self.refresh();self.activate()

    def activate(self):
        self.studio.cancel_index();self.studio.workspace_generation+=1
        self.studio.loaded(self.require().workspace())

    def refresh(self):
        p=self.require();self.location.setText('Project: '+str(p.root)+'\nRead-only source: '+str(p.source));self.description.setText(p.state['description']);self.metadata.setPlainText(json.dumps(p.state['manifest'],indent=2));self.banks.clear()
        for entry in read_json(p.source/'assets.json',32*1024*1024)['entries']:
            bank=Path(entry['folder']).name
            if bank not in p.state['banks']:self.banks.addItem(bank)

    def save(self):
        p=self.require();m=json.loads(self.metadata.toPlainText())
        from jsonschema import Draft202012Validator
        from ..mod_project import DATA
        schema=read_json(DATA/'chmod.schema.json')
        # Full content validation occurs once changed resources are generated.
        for field in ('id','name','author','version','requires','dependencies','incompatible','update_source'):
            if field in m:Draft202012Validator(dict(schema['properties'][field],**{'$defs':schema['$defs']})).validate(m[field])
        p.state['manifest']=m;p.state['description']=self.description.text();p.save();self.report.setPlainText('Project metadata saved. Changes to resource editors require their Save action.')

    def add_bank(self):
        p=self.require();bank=self.banks.currentText()
        if bank:p.add_bank(bank);self.refresh()

    def edit(self):
        p=self.require()
        if self.studio.maybe_save():self.studio.open_assets(p.edit/'assets',loader=p.workspace);self.studio.tabs.setCurrentIndex(0)

    def roster(self):
        p=self.require();payload,_=QFileDialog.getOpenFileName(self,'Compatible native Roster.ROS',filter='Native roster (*.ROS)')
        if not payload:return
        header,_=QFileDialog.getOpenFileName(self,'That roster’s original aggregate header',filter='Header (*.header)')
        if header:p.attach_roster(payload,header);self.refresh()

    def compare(self):
        p=self.require();selected=self.studio.current_texture
        if not selected:raise ValueError('Select a texture in the Textures tab first')
        resource,payload,path=selected
        if resource.workspace.root!=p.edit:raise ValueError('Open project copies before comparing')
        from .. import dds
        from ..mod_project import safe
        from PySide6.QtGui import QImage,QPixmap
        from PySide6.QtCore import Qt
        relative=path.relative_to(p.edit).as_posix();original=safe(p.source,relative).read_bytes()
        dialog=QDialog(self);dialog.setWindowTitle('Source / replacement — '+resource.key);layout=QHBoxLayout(dialog)
        for title,data in [('Original source',original),('Project replacement',path.read_bytes() if path.exists() else payload)]:
            image=dds.image(data).convert('RGBA');qimage=QImage(image.tobytes(),image.width,image.height,QImage.Format.Format_RGBA8888).copy();column=QVBoxLayout();column.addWidget(QLabel(title));label=QLabel();label.setPixmap(QPixmap.fromImage(qimage).scaled(480,480,Qt.AspectRatioMode.KeepAspectRatio));column.addWidget(label);layout.addLayout(column)
        dialog.exec()

    def extension(self):
        p=self.require();path,_=QFileDialog.getOpenFileName(self,'Compiled Windows x64 DLL for player.weight.read / ABI 1',filter='DLL (*.dll)')
        if path:p.attach_extension(path);self.refresh()

    def uniform(self):
        p=self.require();folder=QFileDialog.getExistingDirectory(self,'Authored uniform bank; add world and selection separately')
        if not folder:return
        value,ok=QInputDialog.getText(self,'Source binding','Original template bank hash (decimal or 0x hexadecimal)')
        if ok:p.attach_uniform(folder,int(value,0));self.refresh()

    def review(self):
        p=self.require();self.report.setPlainText(json.dumps(dict(changes=p.review(),roster=p.state['manifest'].get('roster'),uniforms=p.state['manifest'].get('uniforms'),extensions=p.state['manifest'].get('extensions')),indent=2))

    def export(self):
        p=self.require()
        if not self.studio.maybe_save():return
        self.save()
        output,_=QFileDialog.getSaveFileName(self,'Export new package outside project and installation',filter='CHMOD package (*.chmod)')
        if not output:return
        dependencies=[]
        if p.state['manifest'].get('dependencies'):
            paths,ok=QInputDialog.getMultiLineText(self,'Validation dependencies','Installed dependency version directories, one per line')
            if not ok:return
            dependencies=[Path(s.strip()) for s in paths.splitlines() if s.strip()]
        self.report.setPlainText('Validating package with the runtime…')
        self.studio.run_job(lambda progress:p.export(output,dependencies),lambda manifest:self.report.setPlainText('Exported '+output+'\nRuntime metadata/source contracts accepted. DDS shared-owner checks still run during launcher preparation.\nNot in-game verified. Install and enable through the runtime launcher.'))
