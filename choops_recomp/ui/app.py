"""Assets-folder desktop editor. GUI/CLI share the same Xbox backend."""
import argparse
import json
import os
from pathlib import Path
import traceback
from PySide6.QtCore import Qt,QAbstractListModel,QAbstractTableModel,QModelIndex,QObject,QRunnable,QThreadPool,Signal,QSortFilterProxyModel,QTimer
from PySide6.QtGui import QAction,QImage,QPixmap,QKeySequence
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QTabWidget,QPushButton,QLabel,QListView,QLineEdit,QFileDialog,QMessageBox,QTableView,QComboBox,QInputDialog,QColorDialog,QCheckBox,QPlainTextEdit,QAbstractItemView,QDialog,QDialogButtonBox,QTableWidget,QTableWidgetItem,QScrollArea,QGridLayout,QStyledItemDelegate
from ..workspace import Workspace
from .. import dds,audio,scene
from ..roster import Roster,STRINGS
from ..player_fields import FIELDS,RATINGS


class Signals(QObject):
    result=Signal(object);error=Signal(str);progress=Signal(int,int,str)


class Work(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.signals=Signals()
    def run(self):
        try:self.signals.result.emit(self.fn(self.signals.progress.emit))
        except Exception as exc:self.signals.error.emit(str(exc))


class LibraryModel(QAbstractListModel):
    def __init__(self,items=None):super().__init__();self.items=items or []
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.items)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role==Qt.ItemDataRole.DisplayRole:return self.items[index.row()].label
    def set_items(self,items):self.beginResetModel();self.items=items;self.endResetModel()


class RosterModel(QAbstractTableModel):
    error=Signal(str)
    def __init__(self,document,table):super().__init__();self.doc=document;self.table=table;self.columns=[];self.reset(table)
    def reset(self,table):
        self.beginResetModel();self.table=table;self.columns=['index',*STRINGS.get(table,{})]
        if table=='players':self.columns+=['jersey_number','height_inches','position_code']
        if table=='uniforms':self.columns+=['owner','asset','variant','shape','unlock']
        self.endResetModel()
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.doc.rows[self.table])
    def columnCount(self,parent=QModelIndex()):return len(self.columns)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):return str(self.doc.rows[self.table][index.row()].get(self.columns[index.column()],''))
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return self.columns[section].replace('_',' ').title() if orientation==Qt.Orientation.Horizontal else str(section)
    def flags(self,index):
        flags=super().flags(index)
        if index.column()>0 and not (self.table=='uniforms' and self.columns[index.column()] not in ('asset','shape')):flags|=Qt.ItemFlag.ItemIsEditable
        return flags
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole:return False
        try:
            field=self.columns[index.column()]
            if field in STRINGS.get(self.table,{}):self.doc.set_string(self.table,index.row(),field,str(value))
            elif self.table=='uniforms':self.doc.set_uniform(index.row(),field,int(value))
            else:self.doc.set_player(index.row(),field,int(value))
            self.dataChanged.emit(index,index);return True
        except Exception as exc:self.error.emit(str(exc));return False


class PlayerDetailsModel(QAbstractTableModel):
    error=Signal(str)
    def __init__(self,document,index,ratings=False):
        super().__init__();self.doc=document;self.index=index;self.ratings=ratings;self.fields=RATINGS if ratings else list(FIELDS.values())
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.fields)
    def columnCount(self,parent=QModelIndex()):return 2
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):return None
        spec=self.fields[index.row()]
        if index.column()==0:return spec['name']
        player=self.doc.rows['players'][self.index]
        value=player['ratings'][index.row()] if self.ratings else player[spec['key']]
        if role==Qt.ItemDataRole.DisplayRole and spec.get('choices'):return spec['choices'].get(str(value),f'Unknown stored code {value}')
        return value
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal:return ('Xbox field','Value')[section]
    def flags(self,index):return super().flags(index)|(Qt.ItemFlag.ItemIsEditable if index.column()==1 else Qt.ItemFlag.NoItemFlags)
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole or index.column()!=1:return False
        try:
            if self.ratings:self.doc.set_rating(self.index,index.row(),float(value))
            else:self.doc.set_player(self.index,self.fields[index.row()]['key'],int(value))
            self.dataChanged.emit(index,index);return True
        except (ValueError,TypeError) as exc:self.error.emit(str(exc));return False


class PlayerChoiceDelegate(QStyledItemDelegate):
    def createEditor(self,parent,option,index):
        spec=index.model().fields[index.row()]
        if index.column()==1 and spec.get('choices'):
            editor=QComboBox(parent)
            for code,caption in spec['choices'].items():editor.addItem(caption,int(code))
            return editor
        return super().createEditor(parent,option,index)
    def setEditorData(self,editor,index):
        if isinstance(editor,QComboBox):
            value=index.data(Qt.ItemDataRole.EditRole);row=editor.findData(value)
            if row<0:editor.addItem(f'Unknown stored code {value}',value);row=editor.count()-1
            editor.setCurrentIndex(row)
        else:super().setEditorData(editor,index)
    def setModelData(self,editor,model,index):
        if isinstance(editor,QComboBox):model.setData(index,editor.currentData())
        else:super().setModelData(editor,model,index)


class Studio(QMainWindow):
    def __init__(self,offscreen=False):
        super().__init__();self.offscreen=offscreen;self.last_error=None;self.setWindowTitle('CHoops Recomp Studio — Xbox assets');self.resize(1400,900);self.pool=QThreadPool(self);self.jobs=[];self.workspace=None;self.roster=None;self.roster_resource=None;self.scene_resource=None;self.scene_data=None;self.generation=0;self.workspace_generation=0
        self.tabs=QTabWidget();self.setCentralWidget(self.tabs);self.pages={}
        bar=self.menuBar().addMenu('File');open_action=bar.addAction('Open assets folder…');open_action.setShortcut(QKeySequence.StandardKey.Open);open_action.triggered.connect(self.choose_assets)
        save=QAction('Save roster',self);save.setShortcut(QKeySequence.StandardKey.Save);save.triggered.connect(self.save_roster);self.addAction(save)
        for name,kind in [('Models / Courts','SCNE'),('Textures','TXTR'),('Audio','AUDO')]:self.make_library(name,kind)
        model_page=self.pages['SCNE'];self.view=QLabel('3D preview is disabled in offscreen UI checks') if offscreen else __import__('choops_recomp.ui.scene_view',fromlist=['SceneView']).SceneView()
        model_page['layout'].addWidget(self.view,1);model_page['details']=QPlainTextEdit();model_page['details'].setReadOnly(True);model_page['details'].setMaximumHeight(130);model_page['layout'].addWidget(model_page['details'])
        row=QHBoxLayout();fit=QPushButton('Fit camera');fit.clicked.connect(lambda:self.view.fit() if hasattr(self.view,'fit') else None);row.addWidget(fit)
        self.cutaway=QCheckBox('Cutaway');self.cutaway.setChecked(True);self.cutaway.toggled.connect(self.toggle_cutaway);row.addWidget(self.cutaway)
        self.scene_textures=QComboBox();row.addWidget(self.scene_textures,1);export=QPushButton('Export DDS');export.clicked.connect(self.export_scene_dds);row.addWidget(export);replace=QPushButton('Replace DDS…');replace.clicked.connect(self.replace_scene_dds);row.addWidget(replace);model_page['layout'].addLayout(row)
        row=QHBoxLayout();self.uniform_picker=QComboBox();self.uniform_picker.setEditable(True);row.addWidget(self.uniform_picker,1);self.uniform_shape=QComboBox();self.uniform_shape.addItems(['U','V','V triangle','Triangle','Wishbone']);row.addWidget(self.uniform_shape);self.uniform_build=QComboBox();self.uniform_build.addItems(['reg','thin','fat']);row.addWidget(self.uniform_build);self.shorts_build=QComboBox();self.shorts_build.addItems(['reg','thin','fat']);row.addWidget(self.shorts_build);preview=QPushButton('Preview uniform');preview.clicked.connect(self.preview_uniform);row.addWidget(preview);model_page['layout'].addLayout(row)
        row=QHBoxLayout();self.shoe_picker=QComboBox();self.shoe_picker.setEditable(True);row.addWidget(self.shoe_picker,1);preview=QPushButton('Preview shoes');preview.clicked.connect(self.preview_shoes);row.addWidget(preview);model_page['layout'].addLayout(row)
        self.texture_view=QLabel('Select a texture');self.texture_view.setAlignment(Qt.AlignmentFlag.AlignCenter);self.texture_view.setMinimumSize(400,400);self.pages['TXTR']['layout'].addWidget(self.texture_view,1)
        self.texture_details=QLabel();self.pages['TXTR']['layout'].addWidget(self.texture_details)
        row=QHBoxLayout()
        for text,slot in [('Export DDS',self.export_texture),('Replace DDS…',self.replace_texture)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        self.pages['TXTR']['layout'].addLayout(row);self.current_texture=None
        self.audio_details=QPlainTextEdit();self.audio_details.setReadOnly(True);self.pages['AUDO']['layout'].addWidget(self.audio_details)
        self.audio_cover=QLabel();self.audio_cover.setAlignment(Qt.AlignmentFlag.AlignCenter);self.audio_cover.setMaximumHeight(260);self.pages['AUDO']['layout'].addWidget(self.audio_cover);self.audio_cover_resource=None
        row=QHBoxLayout()
        for text,slot in [('Play',self.play_audio),('Stop',self.stop_audio),('Export WAV…',self.export_audio),('Import WAV…',self.import_audio),('Export tab…',self.export_audio_tab)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        self.pages['AUDO']['layout'].addLayout(row);row=QHBoxLayout()
        for text,slot in [('Export cover DDS…',self.export_audio_cover),('Replace cover DDS…',self.replace_audio_cover)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        self.pages['AUDO']['layout'].addLayout(row);self.pages['AUDO']['layout'].addWidget(QLabel('Native WAV keeps original channels, rate and duration. No console codec is required for import.'))
        from ..audio_catalog import CATEGORIES
        self.audio_categories=QTabWidget();self.audio_groups={name:[] for name in CATEGORIES}
        for name in CATEGORIES:self.audio_categories.addTab(QWidget(),name)
        self.audio_categories.setMaximumHeight(42);self.pages['AUDO']['layout'].insertWidget(0,self.audio_categories)
        self.audio_categories.currentChanged.connect(self.change_audio_category)
        self.current_audio=None
        self.audio_player=None;self.audio_preview_directory=None
        roster_page=QWidget();layout=QVBoxLayout(roster_page);row=QHBoxLayout();self.roster_tables=QComboBox();self.roster_tables.currentTextChanged.connect(self.change_table);row.addWidget(self.roster_tables)
        for text,slot in [('Undo',self.undo),('Redo',self.redo),('Channels…',self.edit_rating),('Team palette…',self.edit_palette),('New uniform…',self.add_uniform),('Save roster',self.save_roster)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        layout.addLayout(row);row=QHBoxLayout()
        for text,slot in [('Export CSV…',self.export_csv),('Import / compare…',self.import_csv),('Copy ratings',self.copy_ratings),('Paste ratings to selected',self.paste_ratings)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        layout.addLayout(row);self.roster_view=QTableView();split=QSplitter();split.addWidget(self.roster_view);self.player_tabs=QTabWidget();self.player_properties=QTableView();self.player_ratings=QTableView();self.player_tabs.addTab(self.player_properties,'Player / Appearance');self.player_tabs.addTab(self.player_ratings,'Ratings');split.addWidget(self.player_tabs);layout.addWidget(split);layout.addWidget(QLabel('Xbox profile: 316-byte player rows. Unknown source bits are preserved.'));self.tabs.addTab(roster_page,'Roster')
        self.statusBar().showMessage('Open the recomp game’s assets folder. No game is launched by this editor.')
        self.roster_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.roster_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.copied_ratings=None
        self.player_properties.setItemDelegate(PlayerChoiceDelegate(self.player_properties))
    def make_library(self,title,kind):
        page=QWidget();layout=QVBoxLayout(page);split=QSplitter();layout.addWidget(split);left=QWidget();l=QVBoxLayout(left);search=QLineEdit();search.setPlaceholderText('Search assets…');l.addWidget(search);view=QListView();view.setUniformItemSizes(True);model=LibraryModel();proxy=QSortFilterProxyModel();proxy.setSourceModel(model);proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive);view.setModel(proxy);l.addWidget(view);split.addWidget(left);right=QWidget();detail=QVBoxLayout(right);split.addWidget(right);split.setStretchFactor(1,2)
        search.textChanged.connect(proxy.setFilterFixedString);view.selectionModel().currentChanged.connect(lambda index,old,k=kind:self.select_resource(k,index));self.pages[kind]=dict(model=model,proxy=proxy,view=view,layout=detail);self.tabs.addTab(page,title)
    def run_job(self,fn,callback):
        job=Work(fn);self.jobs.append(job)
        def finished(result):
            try:callback(result)
            except Exception as exc:self.error(str(exc))
            finally:
                if job in self.jobs:self.jobs.remove(job)
        job.signals.result.connect(finished);job.signals.error.connect(lambda text:(self.jobs.remove(job) if job in self.jobs else None,self.error(text)));job.signals.progress.connect(lambda n,total,text:self.statusBar().showMessage(f'{n:,}/{total:,} • {text}'));self.pool.start(job)
    def error(self,text):
        self.last_error=text;self.statusBar().showMessage(text)
        if not self.offscreen:QMessageBox.warning(self,'CHoops Recomp Studio',text)
    def choose_assets(self):
        if not self.maybe_save():return
        path=QFileDialog.getExistingDirectory(self,'Open Xbox recomp assets folder')
        if path:self.open_assets(path)
    def maybe_save(self):
        if not self.roster or bytes(self.roster.data)==self.roster.original:return True
        answer=QMessageBox.question(self,'Unsaved Xbox roster','Save roster edits before continuing?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
        if answer==QMessageBox.StandardButton.Cancel:return False
        if answer==QMessageBox.StandardButton.Save:
            try:self.roster.save(self.roster_resource.component_path())
            except (ValueError,OSError) as exc:self.error(str(exc));return False
        return True
    def closeEvent(self,event):
        if self.jobs:self.statusBar().showMessage('Wait for the active operation to finish before closing');event.ignore();return
        if not self.maybe_save():event.ignore();return
        self.stop_audio()
        if self.audio_player:
            from PySide6.QtCore import QUrl
            self.audio_player.setSource(QUrl())
        if self.audio_preview_directory:self.audio_preview_directory.cleanup()
        event.accept()
    def open_assets(self,path):
        self.workspace_generation+=1;generation=self.workspace_generation;self.statusBar().showMessage('Reading Xbox assets…')
        self.run_job(lambda progress:Workspace(path,progress),lambda result:self.loaded(result) if generation==self.workspace_generation else None)
    def loaded(self,workspace):
        self.audio_cover_resource=None;self.audio_cover.clear()
        self.stop_audio();self.generation+=1;self.current_texture=None;self.current_audio=None;self.scene_resource=None;self.scene_data=None;self.roster=None;self.roster_resource=None;self.roster_view.setModel(None);self.player_properties.setModel(None);self.player_ratings.setModel(None);self.scene_textures.clear();self.uniform_picker.clear();self.roster_tables.clear();self.audio_details.clear();self.texture_view.clear();self.texture_details.clear()
        if hasattr(self.view,'set_scene'):self.view.set_scene([],{})
        self.workspace=workspace
        from ..shoe_preview import available
        self.shoe_picker.clear();self.shoe_picker.addItems(available(workspace));self.shoe_picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        for kind,page in self.pages.items():page['model'].set_items(workspace.of_type(kind))
        from ..audio_catalog import group
        self.audio_groups=group(workspace.of_type('AUDO'));self.change_audio_category(self.audio_categories.currentIndex())
        rosters=workspace.of_type('ROST')
        if rosters:
            self.roster_resource=rosters[0];self.roster=Roster(self.roster_resource.blocks()[0]);self.roster_tables.clear();self.roster_tables.addItems(list(self.roster.rows));self.change_table(self.roster_tables.currentText())
            from ..uniforms import rows,name
            self.uniform_picker.clear()
            import struct
            owners={}
            for team in self.roster.rows['teams']:
                owner=struct.unpack_from('>H',self.roster.data,team['offset']+0x190)[0];owners.setdefault(owner,[]).append(team['short_name'])
            for uniform in rows(self.roster):
                caption=' / '.join(dict.fromkeys(owners.get(uniform['owner'],[f"Owner {uniform['owner']}"])))
                self.uniform_picker.addItem(f"{caption} • {name(uniform['asset'],uniform['variant'])}",uniform['index'])
            self.uniform_picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.statusBar().showMessage(f"Xbox • {len(workspace.banks):,} banks • {len(workspace.resources):,} resources • edit directly, then restart the recomp")
    def change_table(self,table):
        if self.roster and table in self.roster.rows:
            model=RosterModel(self.roster,table);self.roster_model=model;model.error.connect(self.error);self.roster_view.setModel(model);self.roster_view.resizeColumnsToContents()
            self.roster_view.selectionModel().currentRowChanged.connect(self.change_player);self.player_tabs.setVisible(table=='players')
    def change_player(self,index,previous):
        if self.roster_tables.currentText()!='players' or not index.isValid():return
        self.property_model=PlayerDetailsModel(self.roster,index.row());self.rating_model=PlayerDetailsModel(self.roster,index.row(),True)
        for view,model in ((self.player_properties,self.property_model),(self.player_ratings,self.rating_model)):
            model.error.connect(self.error);view.setModel(model);view.resizeColumnsToContents()
    def change_audio_category(self,index):
        from ..audio_catalog import CATEGORIES
        if not 0<=index<len(CATEGORIES):return
        self.current_audio=None;self.audio_cover_resource=None;self.audio_cover.clear();self.audio_details.clear();self.pages['AUDO']['model'].set_items(self.audio_groups[CATEGORIES[index]])
    def selected(self,kind,index):
        page=self.pages[kind];source=page['proxy'].mapToSource(index)
        return page['model'].items[source.row()] if source.isValid() else None
    def select_resource(self,kind,index):
        r=self.selected(kind,index)
        if not r:return
        if kind=='SCNE':
            self.generation+=1;generation=self.generation;self.statusBar().showMessage('Decoding Xbox scene…')
            def decode(progress):
                blocks=r.blocks();result=scene.preview(blocks)
                try:result['textures']=scene.textures(blocks)
                except ValueError:result['textures']=[]
                result['resource']=r;result['generation']=generation;return result
            self.run_job(decode,self.show_scene)
        elif kind=='TXTR':
            try:
                blocks=r.blocks();payload=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);path=r.folder/'texture.dds'
                if path.exists():payload=path.read_bytes()
                self.current_texture=(r,payload,path);self.show_image(payload);self.texture_details.setText(r.label+' • '+str(dds.info(payload)))
            except ValueError as exc:self.texture_details.setText(str(exc));self.current_texture=None
        elif kind=='AUDO':
            try:self.current_audio=r;self.audio_details.setPlainText(r.label+'\n'+json.dumps(audio.info(r.blocks()),indent=2))
            except ValueError as exc:self.current_audio=None;self.audio_details.setPlainText(str(exc))
            self.show_audio_cover()
    def show_scene(self,result):
        if result['generation']!=self.generation:return
        self.scene_data=result;self.scene_resource=result['resource'];self.scene_textures.clear();images=dict(result.get('images',{}))
        for t in result['textures']:
            if 'dds' not in t:continue
            path=self.scene_resource.folder/f"texture_{t['index']:04d}.dds";payload=path.read_bytes() if path.exists() else t['dds'];images[t['index']]=dds.image(payload);self.scene_textures.addItem(f"Texture {t['index']} • {t['id']:08x}",t['index'])
        if hasattr(self.view,'set_scene'):self.view.set_scene(result['meshes'],images)
        self.pages['SCNE']['details'].setPlainText(f"{len(result['meshes'])}/{result['declared_parts']} mesh parts • {sum(len(m['vertices'])//3 for m in result['meshes']):,} triangles\n"+'\n'.join(result['warnings']))
        self.statusBar().showMessage('Xbox scene ready')
    def preview_uniform(self):
        if not self.workspace or not self.roster:return
        from ..uniforms import rows
        from ..uniform_preview import preview
        index=self.uniform_picker.currentData()
        if index is None:return
        row=rows(self.roster)[index];shape=self.uniform_shape.currentIndex();build=self.uniform_build.currentText();shorts=self.shorts_build.currentText();workspace=self.workspace
        self.generation+=1;generation=self.generation
        def decode(progress):
            result=preview(workspace,row,shape,build,shorts);result['generation']=generation;return result
        self.run_job(decode,self.show_scene)
    def preview_shoes(self):
        if not self.workspace:return
        from ..shoe_preview import preview
        filename=self.shoe_picker.currentText();workspace=self.workspace;self.generation+=1;generation=self.generation
        def decode(progress):
            result=preview(workspace,filename);result['generation']=generation;return result
        self.run_job(decode,self.show_scene)
    def toggle_cutaway(self,checked):
        if hasattr(self.view,'set_scene'):self.view.cutaway=checked;self.view.set_scene(self.view.meshes,self.view.images)
    def show_image(self,payload):
        image=dds.image(payload);data=image.tobytes();q=QImage(data,image.width,image.height,image.width*4,QImage.Format.Format_RGBA8888).copy();self.texture_view.setPixmap(QPixmap.fromImage(q).scaled(700,600,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def show_audio_cover(self):
        self.audio_cover_resource=None;self.audio_cover.clear()
        if not self.current_audio:return
        try:
            from ..audio_catalog import cover_resource
            resource,shared=cover_resource(self.current_audio)
            if resource is None:self.audio_cover.setText('No jukebox artwork binding for this audio bank');return
            blocks=resource.blocks();path=resource.folder/'texture.dds';payload=path.read_bytes() if path.is_file() else dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);image=dds.image(payload);raw=image.tobytes();q=QImage(raw,image.width,image.height,image.width*4,QImage.Format.Format_RGBA8888).copy()
            self.audio_cover.setPixmap(QPixmap.fromImage(q).scaled(240,240,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));self.audio_cover.setToolTip(f'Xbox artwork shared by {shared} track(s)');self.audio_cover_resource=resource
        except ValueError as exc:self.audio_cover.setText('Cover preview: '+str(exc))
    def export_audio_cover(self):
        resource=self.audio_cover_resource
        if resource is None:return
        path,_=QFileDialog.getSaveFileName(self,'Export Xbox cover DDS','','DDS (*.dds)')
        if path:
            blocks=resource.blocks();current=resource.folder/'texture.dds';Path(path).write_bytes(current.read_bytes() if current.is_file() else dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None))
    def replace_audio_cover(self):
        resource=self.audio_cover_resource
        if resource is None:return
        path,_=QFileDialog.getOpenFileName(self,'Replace Xbox cover artwork','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
        if not path:return
        try:
            if self.workspace is not resource.workspace:raise ValueError('Source folder changed while selecting artwork')
            from ..edits import save_texture,artwork_payload
            blocks=resource.blocks();baseline=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);payload=artwork_payload(path,baseline)
            save_texture(resource,payload);self.show_audio_cover();self.statusBar().showMessage('Shared Xbox cover DDS saved directly to its resource folder')
        except ValueError as exc:self.error(str(exc))
    def export_texture(self):
        if not self.current_texture:return
        path,_=QFileDialog.getSaveFileName(self,'Export DDS','','DDS (*.dds)')
        if path:Path(path).write_bytes(self.current_texture[1])
    def replace_texture(self):
        if not self.current_texture:return
        r,old,target=self.current_texture
        path,_=QFileDialog.getOpenFileName(self,'Replace texture artwork','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
        if not path:return
        try:
            if self.workspace is not r.workspace:raise ValueError('Source folder changed while selecting artwork')
            from ..edits import save_texture,artwork_payload
            target=save_texture(r,artwork_payload(path,old));self.current_texture=(r,target.read_bytes(),target);self.show_image(target.read_bytes());self.statusBar().showMessage('DDS saved directly to assets. Restart the recomp to apply.')
        except ValueError as exc:self.error(str(exc))
    def scene_texture(self):
        if not self.scene_data:return None
        index=self.scene_textures.currentData();return next((t for t in self.scene_data['textures'] if t['index']==index),None)
    def export_scene_dds(self):
        t=self.scene_texture()
        if not t:return
        path,_=QFileDialog.getSaveFileName(self,'Export embedded Xbox DDS','','DDS (*.dds)')
        current=self.scene_resource.folder/f"texture_{t['index']:04d}.dds"
        if path:Path(path).write_bytes(current.read_bytes() if current.is_file() else t['dds'])
    def replace_scene_dds(self):
        t=self.scene_texture()
        if not t:return
        resource=self.scene_resource;generation=self.generation
        path,_=QFileDialog.getOpenFileName(self,'Replace scene artwork','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
        if not path:return
        try:
            if self.workspace is not resource.workspace or generation!=self.generation:raise ValueError('Source scene changed while selecting artwork')
            from ..edits import save_scene_texture,artwork_payload
            save_scene_texture(resource,t['index'],artwork_payload(path,t['dds']));self.show_scene(self.scene_data);self.statusBar().showMessage('Scene DDS saved. Restart the updated recomp to apply.')
        except ValueError as exc:self.error(str(exc))
    def export_audio(self):
        if not self.current_audio:return
        path,_=QFileDialog.getSaveFileName(self,'Export Xbox audio as WAV','','WAV (*.wav)')
        resource=self.current_audio
        if path:self.run_job(lambda progress:audio.export_wav(resource,path),lambda result:self.statusBar().showMessage('WAV export complete'))
    def export_audio_tab(self):
        if not self.workspace:return
        from ..audio_catalog import CATEGORIES
        resources=list(self.audio_groups[CATEGORIES[self.audio_categories.currentIndex()]])
        if not resources:return
        path,_=QFileDialog.getSaveFileName(self,'New audio export folder','audio-export')
        if path:self.run_job(lambda progress:audio.export_batch(resources,path,progress),lambda result:self.statusBar().showMessage(f'Exported {len(result)} WAV files and Xbox import manifest'))
    def stop_audio(self):
        if self.audio_player:self.audio_player.stop()
    def play_audio(self):
        if not self.current_audio:return
        resource=self.current_audio
        import tempfile
        if self.audio_preview_directory is None:self.audio_preview_directory=tempfile.TemporaryDirectory(prefix='choops-preview-')
        import uuid
        target=Path(self.audio_preview_directory.name)/(uuid.uuid4().hex+'.wav')
        def play(result):
            from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
            from PySide6.QtCore import QUrl
            if self.audio_player is None:
                self.audio_player=QMediaPlayer(self);self.audio_output=QAudioOutput(self);self.audio_player.setAudioOutput(self.audio_output)
                self.audio_player.errorOccurred.connect(lambda error,text:self.error(text))
            self.audio_player.setSource(QUrl.fromLocalFile(str(target)));self.audio_player.play()
        self.run_job(lambda progress:audio.export_wav(resource,target),play)
    def import_audio(self):
        if not self.current_audio:return
        path,_=QFileDialog.getOpenFileName(self,'Import native PCM WAV','','WAV (*.wav)')
        if path:
            try:
                from ..edits import save_audio
                save_audio(self.current_audio,path);self.statusBar().showMessage('WAV saved directly to assets. Restart the updated recomp to apply.')
            except ValueError as exc:self.error(str(exc))
    def undo(self):
        if self.roster:self.roster.undo();self.change_table(self.roster_tables.currentText())
    def export_csv(self):
        if not self.roster:return
        path,_=QFileDialog.getSaveFileName(self,'Export Xbox roster CSV','','CSV (*.csv)')
        if path:
            try:
                from ..roster_csv import export
                export(self.roster,self.roster_tables.currentText(),path);self.statusBar().showMessage('CSV and Xbox source-identity metadata exported')
            except (ValueError,OSError) as exc:self.error(str(exc))
    def import_csv(self):
        if not self.roster:return
        path,_=QFileDialog.getOpenFileName(self,'Compare Xbox roster CSV','','CSV (*.csv)')
        if not path:return
        try:
            from ..roster_csv import review,apply
            changes=review(self.roster,path)
            if not changes:self.statusBar().showMessage('CSV contains no changes');return
            dialog=QDialog(self);dialog.setWindowTitle('Review Xbox roster changes');dialog.resize(900,600);layout=QVBoxLayout(dialog)
            choices={};pane=QWidget();grid=QGridLayout(pane);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(pane);scroll.setMaximumHeight(180);layout.addWidget(scroll)
            for n,field in enumerate(sorted({c['field'] for c in changes})):
                check=QCheckBox(field);check.setChecked(True);choices[field]=check;grid.addWidget(check,n//3,n%3)
            table=QTableWidget(len(changes),4);table.setHorizontalHeaderLabels(['Row','Field','Before','After']);table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            for i,change in enumerate(changes):
                for j,value in enumerate((change['index'],change['field'],change['before'],change['after'])):table.setItem(i,j,QTableWidgetItem(str(value)))
            layout.addWidget(table);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                selected={field for field,check in choices.items() if check.isChecked()};apply(self.roster,changes,selected);self.change_table(self.roster_tables.currentText());self.statusBar().showMessage('Selected CSV fields applied; Save roster to write changes')
        except (ValueError,OSError,KeyError) as exc:self.error(str(exc))
    def copy_ratings(self):
        if self.roster and self.roster_tables.currentText()=='players' and self.roster_view.currentIndex().isValid():self.copied_ratings=list(self.roster.rows['players'][self.roster_view.currentIndex().row()]['ratings']);self.statusBar().showMessage('Copied all 30 Xbox ratings')
    def paste_ratings(self):
        if not self.roster or self.roster_tables.currentText()!='players' or self.copied_ratings is None:return
        try:
            with self.roster.transaction():
                for index in self.roster_view.selectionModel().selectedRows():
                    for channel,value in enumerate(self.copied_ratings):
                        if value<RATINGS[channel]['minimum']:raise ValueError('Copied ratings contain a preserved sentinel below the Xbox menu range')
                        self.roster.set_rating(index.row(),channel,value)
            self.change_table('players');self.statusBar().showMessage('Ratings pasted as one undoable edit; Save roster to write changes')
        except ValueError as exc:self.error(str(exc))
    def add_uniform(self):
        if not self.roster or self.roster_tables.currentText()!='teams':return
        team=self.roster_view.currentIndex().row()
        if team<0:return
        variant,ok=QInputDialog.getItem(self,'New Xbox uniform','Alternate slot',['Alternate 1','Alternate 2','Alternate 3'],0,False)
        if not ok:return
        asset,ok=QInputDialog.getInt(self,'New Xbox uniform','Unused uniform asset ID',900,0,1023)
        if not ok:return
        answer=QMessageBox.question(self,'Create uniform folders','Create independent world/selection folders and save the current roster edits?')
        if answer!=QMessageBox.StandardButton.Yes:return
        try:
            from ..uniforms import create
            result=create(self.workspace,self.roster,self.roster_resource,team,int(variant[-1])+1,asset)
            self.statusBar().showMessage('Created '+', '.join(result['folders']));self.open_assets(self.workspace.assets)
        except (ValueError,OSError) as exc:self.error(str(exc))
    def redo(self):
        if self.roster:self.roster.redo();self.change_table(self.roster_tables.currentText())
    def save_roster(self):
        if not self.roster:return
        try:self.roster.save(self.roster_resource.component_path());self.statusBar().showMessage('Xbox roster saved. Restart the updated recomp to apply.')
        except ValueError as exc:self.error(str(exc))
    def edit_rating(self):
        if not self.roster or self.roster_tables.currentText()!='players':return
        index=self.roster_view.currentIndex().row()
        if index<0:return
        channel,ok=QInputDialog.getInt(self,'Stored rating channel','Xbox channel (semantic captions pending)',1,1,30)
        if not ok:return
        value,ok=QInputDialog.getDouble(self,'Stored rating value','Value (stored ×100)',self.roster.rows['players'][index]['ratings'][channel-1],0,99,2)
        if ok:self.roster.set_rating(index,channel-1,value)
    def edit_palette(self):
        if not self.roster or self.roster_tables.currentText()!='teams':return
        index=self.roster_view.currentIndex().row()
        if index<0:return
        slot,ok=QInputDialog.getInt(self,'Team palette','Xbox RGBA slot',0,0,30)
        if not ok:return
        from PySide6.QtGui import QColor
        value=self.roster.rows['teams'][index]['palette'][slot];c=QColor(*bytes.fromhex(value));chosen=QColorDialog.getColor(c,self,'Edit RGBA palette slot',QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if chosen.isValid():self.roster.set_palette(index,slot,bytes((chosen.red(),chosen.green(),chosen.blue(),chosen.alpha())))


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--assets');parser.add_argument('--smoke',action='store_true');parser.add_argument('--report');args=parser.parse_args(argv)
    app=QApplication.instance() or QApplication([]);app.setStyle('Fusion');window=Studio(offscreen=os.environ.get('QT_QPA_PLATFORM')=='offscreen');window.show()
    if args.assets:window.open_assets(args.assets)
    if args.smoke:
        def finish():
            if window.jobs:QTimer.singleShot(100,finish);return
            report=dict(window_title=window.windowTitle(),tabs=[window.tabs.tabText(i) for i in range(window.tabs.count())],workspace=window.workspace.report() if window.workspace else None,error=window.last_error)
            if args.report:Path(args.report).write_text(json.dumps(report,indent=2))
            window.close();app.exit(1 if window.last_error else 0)
        QTimer.singleShot(250,finish)
    return app.exec()
