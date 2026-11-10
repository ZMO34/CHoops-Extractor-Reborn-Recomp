"""Direct Xbox uniform routing, artwork, glyphs and authored model preview."""
import zlib
from pathlib import Path
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLabel,QPushButton,QSpinBox,QLineEdit,QCheckBox,QSplitter,QWidget,QFileDialog,QMessageBox,QDialogButtonBox,QTableWidget,QTableWidgetItem,QInputDialog
from .. import uniforms,uniform_preview,uniform_fonts,dds,edits
from .relationships import picker,caption,selected


class UniformEditor(QDialog):
    changed=Signal()
    def __init__(self,parent,model,workspace,team=0):
        super().__init__(parent);self.model=model;self.workspace=workspace;self.preview_generation=0;self.setWindowTitle('Xbox uniform editor');self.resize(1350,950);layout=QVBoxLayout(self);split=QSplitter();layout.addWidget(split);controls=QWidget();left=QVBoxLayout(controls);split.addWidget(controls);right=QWidget();preview_layout=QVBoxLayout(right);split.addWidget(right);split.setStretchFactor(1,2)
        self.school=picker(model,'teams',False);left.addWidget(self.school);self.shared=QLabel();self.shared.setWordWrap(True);left.addWidget(self.shared);self.routes=QComboBox();left.addWidget(self.routes);form=QFormLayout();self.asset=QSpinBox();self.asset.setRange(0,1023);form.addRow('Artwork asset ID',self.asset);self.shape=QComboBox();self.shape.addItems(['U','V','V triangle','Triangle','Wishbone']);form.addRow('Neckline',self.shape);self.variant=QComboBox();self.variant.addItems(uniforms.VARIANTS);form.addRow('Slot',self.variant);self.unlock=QSpinBox();self.unlock.setRange(0,127);form.addRow('Unlock code (0 = available)',self.unlock);left.addLayout(form)
        for title,callback in [('Apply routing to roster',self.apply),('Make school routing independent',self.detach),('Clone selected artwork privately…',self.clone),('Create independent alternate folders…',self.create)]:b=QPushButton(title);b.clicked.connect(callback);left.addWidget(b)
        self.availability={};row=QHBoxLayout()
        for slot in (2,3,4):
            checkbox=QCheckBox('Alt '+str(slot-1));checkbox.clicked.connect(lambda checked,slot=slot:self.set_available(slot,checked));self.availability[slot]=checkbox;row.addWidget(checkbox)
        left.addLayout(row)
        self.art=QComboBox();left.addWidget(self.art)
        for title,callback in [('Export selected artwork…',self.export_art),('Save replacement artwork…',self.import_art),('Edit selected font metrics…',self.edit_metrics)]:b=QPushButton(title);b.clicked.connect(callback);left.addWidget(b)
        hint=QLabel('Routing edits stay in memory until Save roster. Artwork and glyph Save actions write their own loose resource files.');hint.setWordWrap(True);left.addWidget(hint);left.addStretch();controls.setMaximumWidth(480)
        self.view=QLabel('3D disabled during offscreen checks') if parent.offscreen else __import__('choops_recomp.ui.scene_view',fromlist=['SceneView']).SceneView();preview_layout.addWidget(self.view,1);self.details=QLabel();self.details.setWordWrap(True);preview_layout.addWidget(self.details)
        self.player=QComboBox();preview_layout.addWidget(self.player);row=QHBoxLayout();self.number=QSpinBox();self.number.setRange(0,100);self.number.setToolTip('100 previews 00');self.surname=QLineEdit();self.show_number=QCheckBox('Number');self.show_number.setChecked(True);self.show_name=QCheckBox('Surname');self.show_name.setChecked(True)
        for widget in (self.show_number,self.number,self.show_name,self.surname):row.addWidget(widget)
        preview_layout.addLayout(row);row=QHBoxLayout();self.build=QComboBox();self.build.addItems(['reg','thin','fat']);self.shorts=QComboBox();self.shorts.addItems(['reg','thin','fat']);row.addWidget(QLabel('Top build'));row.addWidget(self.build);row.addWidget(QLabel('Shorts build'));row.addWidget(self.shorts)
        for text,callback in [('Refresh preview',self.preview),('Front',lambda:self.angle(0)),('Back',lambda:self.angle(180))]:b=QPushButton(text);b.clicked.connect(callback);row.addWidget(b)
        preview_layout.addLayout(row);close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.rejected.connect(self.reject);layout.addWidget(close)
        self.school.currentIndexChanged.connect(self.reload);self.routes.currentIndexChanged.connect(self.route);self.player.currentIndexChanged.connect(self.choose_player);self.school.setCurrentIndex(self.school.findData(team));self.reload()
    def perform(self,fn):
        try:return fn()
        except (ValueError,OSError,KeyError,StopIteration) as exc:self.parent().error(str(exc))
    def reload(self):
        self.perform(self._reload)
    def _reload(self):
        team=selected(self.school);value=uniforms.owner(self.model,team);shared=uniforms.owners(self.model,value);self.shared.setText('Routing owner '+str(value)+' • Shared by: '+', '.join(self.model.rows['teams'][i]['short_name'] for i in shared));self.routes.blockSignals(True);self.routes.clear()
        for row in uniforms.rows(self.model):
            if row['owner']==value:self.routes.addItem(uniforms.VARIANTS[row['variant']]+' • '+uniforms.name(row['asset'],row['variant']),row['index'])
        active={r['variant'] for r in uniforms.rows(self.model) if r['owner']==value};dormant={r['variant'] for r in uniforms.disabled(self.model) if r['owner']==value}
        for slot,checkbox in self.availability.items():checkbox.setChecked(slot in active);checkbox.setEnabled(slot in active or slot in dormant);checkbox.setToolTip('Keep or restore this alternate assignment' if slot in active or slot in dormant else 'Create this alternate first')
        self.routes.blockSignals(False);self.player.blockSignals(True);self.player.clear()
        from ..relationships import members
        for index in members(self.model,'teams',team):self.player.addItem(caption(self.model,'players',index),index)
        self.player.blockSignals(False);self.choose_player();self.route()
    def choose_player(self):
        index=self.player.currentData()
        if index is not None:row=self.model.row('players',index);self.number.setValue(row['jersey_number']);self.surname.setText(row['last_name'])
    def route(self):
        index=self.routes.currentData();self.art.clear()
        if index is None:return
        row=uniforms.rows(self.model)[index];self.asset.setValue(row['asset']);self.shape.setCurrentIndex(row['shape']);self.variant.setCurrentIndex(row['variant']);self.unlock.setValue(row['unlock']);filename=uniforms.name(row['asset'],row['variant']);bank=zlib.crc32(filename.upper().encode('ascii'))&0xffffffff
        labels={zlib.crc32(n.encode())&0xffffffff:n for n in ('unifregion','unif','shortregion','short','names','jersey_numbers')}
        for resource in self.workspace.of_type('TXTR'):
            if resource.entry['hash']==bank:self.art.addItem(labels.get(resource.record['id'],resource.label),resource)
        users=[r for r in uniforms.rows(self.model) if r['asset']==row['asset'] and r['variant']==row['variant']]
        self.details.setText(f'Artwork routing used by {len(users)} uniform row(s). Private routing does not copy shared artwork; use Clone selected artwork privately for independent textures.')
        if not self.parent().offscreen:self.preview()
    def apply(self):
        def operation():
            selected(self.school)
            uniforms.edit(self.model,self.workspace,self.routes.currentData(),asset=self.asset.value(),shape=self.shape.currentIndex(),variant=self.variant.currentIndex(),unlock=self.unlock.value());self.changed.emit();self.reload();self.preview()
        self.perform(operation)
    def detach(self):
        self.perform(lambda:uniforms.detach(self.model,selected(self.school)));self.changed.emit();self.reload()
    def set_available(self,slot,enabled):
        self.perform(lambda:uniforms.set_available(self.model,self.workspace,uniforms.owner(self.model,selected(self.school)),slot,enabled));self.changed.emit();self.reload()
    def create(self):
        def operation():
            owner=uniforms.owner(self.model,selected(self.school));occupied={r['variant'] for r in uniforms.rows(self.model)+uniforms.disabled(self.model) if r['owner']==owner};available=[i for i in (2,3,4) if i not in occupied]
            if not available:raise ValueError('All three alternate slots are already assigned')
            label,ok=QInputDialog.getItem(self,'Create alternate','Slot',[uniforms.VARIANTS[i] for i in available],0,False)
            if not ok:return
            asset,ok=QInputDialog.getInt(self,'Create alternate','Unused Xbox artwork ID',900,0,1023)
            if not ok:return
            if QMessageBox.question(self,'Save new uniform','Create independent artwork folders and save current roster changes?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Save:return
            uniforms.create(self.workspace,self.model,self.parent().roster_resource,selected(self.school),uniforms.VARIANTS.index(label),asset);self.parent().open_assets(self.workspace.assets);self.accept()
        self.perform(operation)
    def clone(self):
        def operation():
            index=self.routes.currentData()
            if index is None:return
            asset,ok=QInputDialog.getInt(self,'Clone uniform artwork','Unused Xbox artwork ID',900,0,1023)
            if not ok:return
            if QMessageBox.question(self,'Save private artwork','Clone this slot into independent world/selection folders and save current roster changes?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Save:return
            uniforms.clone_artwork(self.workspace,self.model,self.parent().roster_resource,selected(self.school),index,asset);self.parent().open_assets(self.workspace.assets);self.accept()
        self.perform(operation)
    def preview(self):
        try:selected(self.school)
        except ValueError as exc:self.parent().error(str(exc));return
        index=self.routes.currentData()
        if index is None:return
        row=uniforms.rows(self.model)[index];shape=self.shape.currentIndex();number=self.number.value() if self.show_number.isChecked() else None;surname=self.surname.text() if self.show_name.isChecked() else '';build=self.build.currentText();shorts=self.shorts.currentText();self.preview_generation+=1;generation=self.preview_generation
        def decode(progress):return uniform_preview.preview(self.workspace,row,shape,build,shorts,number,surname)
        def finished(result):
            if generation!=self.preview_generation or not self.isVisible():return
            if hasattr(self.view,'set_scene'):self.view.set_scene(result['meshes'],result['images'])
            self.details.setText('\n'.join(result['warnings']))
        self.parent().run_job(decode,finished)
    def angle(self,yaw):
        if hasattr(self.view,'yaw'):self.view.yaw=yaw;self.view.pitch=5;self.view.update()
    def is_font(self,r):return r.record['id'] in (zlib.crc32(b'names')&0xffffffff,zlib.crc32(b'jersey_numbers')&0xffffffff)
    def export_art(self):
        def operation():
            r=self.art.currentData()
            if r is None:return
            font=self.is_font(r);path,_=QFileDialog.getSaveFileName(self,'Export uniform artwork','','PNG (*.png)' if font else 'DDS (*.dds)')
            if not path:return
            if Path(path).exists():raise ValueError('Choose a new artwork destination')
            if font:uniform_fonts.atlas(r.blocks()).save(path)
            else:
                blocks=r.blocks();current=r.folder/'texture.dds';Path(path).write_bytes(current.read_bytes() if current.is_file() else dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None))
        self.perform(operation)
    def import_art(self):
        def operation():
            selected(self.school)
            r=self.art.currentData()
            if r is None:return
            path,_=QFileDialog.getOpenFileName(self,'Save uniform artwork replacement','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
            if not path:return
            if self.is_font(r):uniform_fonts.save_atlas(r,path)
            else:
                blocks=r.blocks();baseline=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);edits.save_texture(r,edits.artwork_payload(path,baseline))
            self.preview()
        self.perform(operation)
    def edit_metrics(self):
        def operation():
            selected(self.school)
            atlas=self.art.currentData()
            if atlas is None or not self.is_font(atlas):raise ValueError('Select names or jersey_numbers artwork first')
            role='names' if atlas.record['id']==zlib.crc32(b'names')&0xffffffff else 'numbers';filename=uniforms.name(uniforms.rows(self.model)[self.routes.currentData()]['asset'],uniforms.rows(self.model)[self.routes.currentData()]['variant']);target=uniform_fonts.resource(self.workspace,filename,role,0x68b693b2);width=uniform_fonts.layout(atlas.blocks())[0];values=uniform_fonts.metrics(target.blocks(),width,28 if role=='names' else 10)
            dialog=QDialog(self);dialog.setWindowTitle('Xbox glyph metrics');layout=QVBoxLayout(dialog);table=QTableWidget(len(values),2);table.setHorizontalHeaderLabels(['Atlas X','Width']);table.setVerticalHeaderLabels(list("'-ABCDEFGHIJKLMNOPQRSTUVWXYZ") if role=='names' else list('0123456789'))
            for i,pair in enumerate(values):
                for j,value in enumerate(pair):table.setItem(i,j,QTableWidgetItem(str(value)))
            layout.addWidget(table);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()==QDialog.DialogCode.Accepted:uniform_fonts.save_metrics(target,atlas,[[int(table.item(i,j).text()) for j in range(2)] for i in range(len(values))]);self.preview()
        self.perform(operation)
