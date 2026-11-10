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
    result=Signal(object);error=Signal(str);progress=Signal(int,int,str);cancelled=Signal()


class OperationCancelled(Exception):pass


class Work(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.signals=Signals();self.cancelled=False
    def run(self):
        def progress(n,total,text):
            if self.cancelled:raise OperationCancelled()
            self.signals.progress.emit(n,total,text)
        try:
            result=self.fn(progress)
            if self.cancelled:raise OperationCancelled()
            self.signals.result.emit(result)
        except OperationCancelled:self.signals.cancelled.emit()
        except Exception as exc:
            if self.cancelled:self.signals.cancelled.emit()
            else:self.signals.error.emit(str(exc))


class LibraryModel(QAbstractListModel):
    def __init__(self,items=None):super().__init__();self.items=items or []
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.items)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role==Qt.ItemDataRole.DisplayRole:return self.items[index.row()].label
    def set_items(self,items):self.beginResetModel();self.items=items;self.endResetModel()


class RosterModel(QAbstractTableModel):
    error=Signal(str)
    def __init__(self,document,table):
        super().__init__();self.doc=document;self.table=table;self.columns=[];self.schools={}
        if table=='players':
            from ..relationships import catalog
            try:
                state=catalog(document);self.schools={player:' / '.join(document.rows['teams'][i]['short_name'] for i in owners) for player,owners in state['schools'].items()}
            except ValueError:pass
        self.reset(table)
    def reset(self,table):
        self.beginResetModel();self.table=table;self.columns=['index',*STRINGS.get(table,{})]
        if table=='players':self.columns+=['school','class_code','jersey_number','height_inches','position_code']
        if table=='uniforms':self.columns+=['owner','asset','variant','shape','unlock']
        if table=='conferences':
            from ..conference_history import FIELDS as HISTORY
            self.columns+=list(HISTORY)
        self.endResetModel()
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.doc.rows[self.table])
    def columnCount(self,parent=QModelIndex()):return len(self.columns)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and self.columns[index.column()]=='school' and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole,Qt.ItemDataRole.UserRole):return self.schools.get(index.row(),'Unassigned')
        if index.isValid() and self.columns[index.column()]=='class_code' and role==Qt.ItemDataRole.DisplayRole:
            value=self.doc.rows[self.table][index.row()]['class_code'];return FIELDS['class_code']['choices'].get(str(value),f'Unknown {value}')
        if index.isValid() and role==Qt.ItemDataRole.UserRole:return self.doc.rows[self.table][index.row()].get(self.columns[index.column()],'')
        if index.isValid() and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):return str(self.doc.rows[self.table][index.row()].get(self.columns[index.column()],''))
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return self.columns[section].replace('_',' ').title() if orientation==Qt.Orientation.Horizontal else str(section)
    def flags(self,index):
        flags=super().flags(index)
        if index.column()>0 and self.table!='uniforms' and self.columns[index.column()] not in ('school','class_code'):flags|=Qt.ItemFlag.ItemIsEditable
        return flags
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole:return False
        try:
            field=self.columns[index.column()]
            if field in STRINGS.get(self.table,{}):self.doc.set_string(self.table,index.row(),field,str(value))
            elif self.table=='conferences':
                from ..conference_history import set_value
                set_value(self.doc,index.row(),field,int(value))
            elif self.table=='uniforms':self.doc.set_uniform(index.row(),field,int(value))
            else:self.doc.set_player(index.row(),field,int(value))
            self.dataChanged.emit(index,index);return True
        except Exception as exc:self.error.emit(str(exc));return False


class PlayerDetailsModel(QAbstractTableModel):
    error=Signal(str)
    def __init__(self,document,index,ratings=False,category=None):
        super().__init__();self.doc=document;self.player_index=index;self.ratings=ratings;self.fields=RATINGS if ratings else list(FIELDS.values())
        if not ratings and category is not None:
            eligibility={'class_code','scholarship_code','redshirt_code','redshirt_used_code'}
            self.fields=[f for f in self.fields if (f['key'] in eligibility if category=='eligibility' else f.get('group')=='footwear' if category=='footwear' else f['key'] not in eligibility and f.get('group')!='footwear')]
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.fields)
    def columnCount(self,parent=QModelIndex()):return 2
    def choices(self,row):
        spec=self.fields[row]
        if spec.get('group')=='footwear':
            from ..footwear import choices
            return choices(spec['key'],self.doc.rows['players'][self.player_index])
        return spec.get('choices',{})
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):return None
        spec=self.fields[index.row()]
        if index.column()==0:return spec['name']
        player=self.doc.rows['players'][self.player_index]
        value=player['ratings'][index.row()] if self.ratings else player[spec['key']]
        choices=self.choices(index.row())
        if role==Qt.ItemDataRole.DisplayRole and choices:return choices.get(str(value),f'Unknown stored code {value}')
        return value
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal:return ('Xbox field','Value')[section]
    def flags(self,index):return super().flags(index)|(Qt.ItemFlag.ItemIsEditable if index.column()==1 else Qt.ItemFlag.NoItemFlags)
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole or index.column()!=1:return False
        try:
            if self.ratings:self.doc.set_rating(self.player_index,index.row(),float(value))
            else:self.doc.set_player(self.player_index,self.fields[index.row()]['key'],int(value))
            self.dataChanged.emit(self.index(0,1),self.index(self.rowCount()-1,1));return True
        except (ValueError,TypeError) as exc:self.error.emit(str(exc));return False


class PlayerChoiceDelegate(QStyledItemDelegate):
    def createEditor(self,parent,option,index):
        spec=index.model().fields[index.row()]
        choices=index.model().choices(index.row())
        if index.column()==1 and choices:
            editor=QComboBox(parent)
            for code,caption in choices.items():editor.addItem(caption,int(code))
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
        bar=self.menuBar().addMenu('File');open_action=bar.addAction('Open assets folder…');open_action.setShortcut(QKeySequence.StandardKey.Open);open_action.triggered.connect(self.choose_assets);self.cancel_loading=bar.addAction('Cancel loading');self.cancel_loading.setEnabled(False);self.cancel_loading.triggered.connect(self.cancel_index)
        save=QAction('Save roster',self);save.setShortcut(QKeySequence.StandardKey.Save);save.triggered.connect(self.save_roster);self.addAction(save)
        for name,kind in [('Models / Courts','SCNE'),('Textures','TXTR'),('Audio','AUDO')]:self.make_library(name,kind)
        model_page=self.pages['SCNE'];self.view=QLabel('3D preview is disabled in offscreen UI checks') if offscreen else __import__('choops_recomp.ui.scene_view',fromlist=['SceneView']).SceneView()
        model_page['layout'].addWidget(self.view,1);model_page['details']=QPlainTextEdit();model_page['details'].setReadOnly(True);model_page['details'].setMaximumHeight(130);model_page['layout'].addWidget(model_page['details'])
        row=QHBoxLayout();fit=QPushButton('Fit camera');fit.clicked.connect(lambda:self.view.fit() if hasattr(self.view,'fit') else None);row.addWidget(fit)
        for text,slot in [('Export cloth OBJ…',self.export_cloth_obj),('Import cloth positions…',self.import_cloth_obj)]:button=QPushButton(text);button.clicked.connect(slot);row.addWidget(button)
        self.cutaway=QCheckBox('Cutaway');self.cutaway.setChecked(True);self.cutaway.toggled.connect(self.toggle_cutaway);row.addWidget(self.cutaway)
        self.scene_textures=QComboBox();row.addWidget(self.scene_textures,1);export=QPushButton('Export DDS');export.clicked.connect(self.export_scene_dds);row.addWidget(export);replace=QPushButton('Replace DDS…');replace.clicked.connect(self.replace_scene_dds);row.addWidget(replace);model_page['layout'].addLayout(row)
        row=QHBoxLayout();self.uniform_picker=QComboBox();self.uniform_picker.setEditable(True);row.addWidget(self.uniform_picker,1);self.uniform_shape=QComboBox();self.uniform_shape.addItems(['U','V','V triangle','Triangle','Wishbone']);row.addWidget(self.uniform_shape);self.uniform_build=QComboBox();self.uniform_build.addItems(['reg','thin','fat']);row.addWidget(self.uniform_build);self.shorts_build=QComboBox();self.shorts_build.addItems(['reg','thin','fat']);row.addWidget(self.shorts_build);preview=QPushButton('Preview uniform');preview.clicked.connect(self.preview_uniform);row.addWidget(preview);model_page['layout'].addLayout(row)
        self.uniform_picker.currentIndexChanged.connect(self.select_uniform_shape)
        row=QHBoxLayout();self.arena_picker=QComboBox();self.arena_picker.setEditable(True);self.arena_picker.setInsertPolicy(QComboBox.InsertPolicy.NoInsert);row.addWidget(self.arena_picker,1);self.arena_mode=QComboBox();self.arena_mode.addItems(['combined','arena','floor']);row.addWidget(self.arena_mode);button=QPushButton('Preview stadium');button.clicked.connect(self.preview_arena);row.addWidget(button);model_page['layout'].addLayout(row)
        row=QHBoxLayout();self.shoe_picker=QComboBox();self.shoe_picker.setEditable(True);row.addWidget(self.shoe_picker,1);preview=QPushButton('Preview shoes');preview.clicked.connect(self.preview_shoes);row.addWidget(preview);model_page['layout'].addLayout(row)
        self.texture_view=QLabel('Select a texture');self.texture_view.setAlignment(Qt.AlignmentFlag.AlignCenter);self.texture_view.setMinimumSize(400,400);self.pages['TXTR']['layout'].addWidget(self.texture_view,1)
        self.texture_details=QLabel();self.pages['TXTR']['layout'].addWidget(self.texture_details)
        self.texture_face=QComboBox();self.texture_face.addItem('Face 0');self.texture_face.setEnabled(False);self.texture_face.currentIndexChanged.connect(self.show_current_texture_face);self.pages['TXTR']['layout'].addWidget(self.texture_face)
        row=QHBoxLayout()
        for text,slot in [('Export artwork',self.export_texture),('Replace artwork…',self.replace_texture)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        self.pages['TXTR']['layout'].addLayout(row);self.current_texture=None;self.current_font=None
        self.audio_details=QPlainTextEdit();self.audio_details.setReadOnly(True);self.pages['AUDO']['layout'].addWidget(self.audio_details)
        self.audio_cover=QLabel();self.audio_cover.setAlignment(Qt.AlignmentFlag.AlignCenter);self.audio_cover.setMaximumHeight(260);self.pages['AUDO']['layout'].addWidget(self.audio_cover);self.audio_cover_resource=None
        row=QHBoxLayout()
        for text,slot in [('Play',self.play_audio),('Stop',self.stop_audio),('Export WAV…',self.export_audio),('Import WAV…',self.import_audio),('Export tab…',self.export_audio_tab),('Import folder…',self.import_audio_folder)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
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
        for text,slot in [('Undo',self.undo),('Redo',self.redo),('School relationships…',self.edit_relationships),('Uniform editor…',self.edit_uniforms),('Channels…',self.edit_rating),('Team palette…',self.edit_palette),('New uniform…',self.add_uniform),('Save roster',self.save_roster)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        layout.addLayout(row);row=QHBoxLayout()
        for text,slot in [('Export CSV…',self.export_csv),('Import / compare…',self.import_csv),('Copy ratings',self.copy_ratings),('Paste ratings to selected',self.paste_ratings),('Preview player shoes…',self.preview_player_shoes)]:b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        layout.addLayout(row);row=QHBoxLayout();self.roster_search=QLineEdit();self.roster_search.setPlaceholderText('Search roster fields…');row.addWidget(self.roster_search,1);self.roster_school=QComboBox();self.roster_school.addItem('All schools',None);row.addWidget(self.roster_school);self.roster_count=QLabel();row.addWidget(self.roster_count);layout.addLayout(row);self.roster_search.textChanged.connect(self.filter_roster);self.roster_school.currentIndexChanged.connect(self.filter_roster)
        self.roster_view=QTableView();split=QSplitter();split.addWidget(self.roster_view);self.player_tabs=QTabWidget();self.player_properties=QTableView();self.player_ratings=QTableView();self.player_eligibility=QTableView();self.player_footwear=QTableView();self.player_tabs.addTab(self.player_eligibility,'Eligibility');self.player_tabs.addTab(self.player_properties,'Appearance / Motion');self.player_tabs.addTab(self.player_footwear,'Footwear');self.player_tabs.addTab(self.player_ratings,'Ratings');split.addWidget(self.player_tabs);layout.addWidget(split);self.player_summary=QLabel();self.player_summary.setTextFormat(Qt.TextFormat.PlainText);layout.addWidget(self.player_summary);layout.addWidget(QLabel('Xbox profile: 316-byte player rows. Unknown source bits are preserved.'));self.tabs.addTab(roster_page,'Roster')
        self.statusBar().showMessage('Open the recomp game’s assets folder. No game is launched by this editor.')
        from .mod_projects import ModProjects
        self.mod_projects=ModProjects(self);self.tabs.addTab(self.mod_projects,'Mods / Mod Projects')
        self.roster_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.roster_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.copied_ratings=None
        self.player_properties.setItemDelegate(PlayerChoiceDelegate(self.player_properties))
        self.player_eligibility.setItemDelegate(PlayerChoiceDelegate(self.player_eligibility));self.player_footwear.setItemDelegate(PlayerChoiceDelegate(self.player_footwear))
    def make_library(self,title,kind):
        page=QWidget();layout=QVBoxLayout(page);split=QSplitter();layout.addWidget(split);left=QWidget();l=QVBoxLayout(left);search=QLineEdit();search.setPlaceholderText('Search assets…');l.addWidget(search);view=QListView();view.setUniformItemSizes(True);model=LibraryModel();proxy=QSortFilterProxyModel();proxy.setSourceModel(model);proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive);view.setModel(proxy);l.addWidget(view);split.addWidget(left);right=QWidget();detail=QVBoxLayout(right);split.addWidget(right);split.setStretchFactor(1,2)
        search.textChanged.connect(proxy.setFilterFixedString);view.selectionModel().currentChanged.connect(lambda index,old,k=kind:self.select_resource(k,index));self.pages[kind]=dict(model=model,proxy=proxy,view=view,layout=detail);self.tabs.addTab(page,title)
        inspect=QPushButton('Inspect resource files…');inspect.clicked.connect(lambda checked=False,k=kind:self.inspect_resource(k));l.addWidget(inspect)
    def inspect_resource(self,kind):
        resource=self.selected(kind,self.pages[kind]['view'].currentIndex())
        if resource is None:return
        from ..inspection import components,page,hex_text
        try:
            entries=components(resource);dialog=QDialog(self);dialog.setWindowTitle('Inspect '+resource.label);dialog.resize(1000,650);layout=QVBoxLayout(dialog)
            layout.addWidget(QLabel(f'{resource.key} • {resource.kind} • record CRC {resource.record["id"]:08x} • read only'))
            picker=QComboBox()
            for entry in entries:picker.addItem(f'Component {entry["index"]}: {entry["size"]:,} bytes • {entry["encoding"]}')
            layout.addWidget(picker);row=QHBoxLayout();offset=QLineEdit('0');offset.setPlaceholderText('Hexadecimal component offset');row.addWidget(offset);read=QPushButton('Read 4 KiB');row.addWidget(read);layout.addLayout(row)
            location=QLabel();location.setWordWrap(True);layout.addWidget(location);view=QPlainTextEdit();view.setReadOnly(True);view.setStyleSheet('font-family: Consolas, monospace');layout.addWidget(view)
            def refresh():
                try:
                    index=picker.currentIndex();start=int(offset.text(),16);entry=entries[index];data=page(resource,index,start);location.setText(str(entry['path'] or 'Empty component'));view.setPlainText(hex_text(data,start))
                except (ValueError,OSError,IndexError) as exc:view.setPlainText(str(exc))
            read.clicked.connect(refresh);picker.currentIndexChanged.connect(lambda _:refresh());refresh();dialog.exec()
        except (ValueError,OSError) as exc:self.error(str(exc))
    def run_job(self,fn,callback):
        job=Work(fn);self.jobs.append(job)
        def finished(result):
            try:callback(result)
            except Exception as exc:self.error(str(exc))
            finally:
                if job in self.jobs:self.jobs.remove(job)
        def cancelled():
            if job in self.jobs:self.jobs.remove(job)
            if job is getattr(self,'index_job',None):self.cancel_loading.setEnabled(False);self.statusBar().showMessage('Loading cancelled; previous workspace retained')
        job.signals.cancelled.connect(cancelled);job.signals.result.connect(finished);job.signals.error.connect(lambda text:(self.jobs.remove(job) if job in self.jobs else None,self.cancel_loading.setEnabled(False) if job is getattr(self,'index_job',None) else None,self.error(text)));job.signals.progress.connect(lambda n,total,text:self.statusBar().showMessage(f'{n:,}/{total:,} • {text}'));self.pool.start(job);return job
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
    def open_assets(self,path,loader=None):
        project=getattr(getattr(self,'mod_projects',None),'project',None)
        if loader is None and project and Path(path).resolve()==project.edit/'assets':loader=project.workspace
        self.cancel_index();self.cancel_loading.setEnabled(True)
        self.workspace_generation+=1;generation=self.workspace_generation;self.statusBar().showMessage('Reading Xbox assets…')
        self.index_job=self.run_job(lambda progress:(loader or Workspace)(path,progress),lambda result:self.loaded(result) if generation==self.workspace_generation else None)
    def cancel_index(self):
        job=getattr(self,'index_job',None)
        if job in self.jobs:job.cancelled=True
    def loaded(self,workspace):
        self.cancel_loading.setEnabled(False)
        self.player_eligibility.setModel(None);self.player_footwear.setModel(None);self.player_summary.clear()
        self.current_font=None
        self.audio_cover_resource=None;self.audio_cover.clear()
        self.stop_audio();self.generation+=1;self.current_texture=None;self.current_audio=None;self.scene_resource=None;self.scene_data=None;self.roster=None;self.roster_resource=None;self.roster_view.setModel(None);self.player_properties.setModel(None);self.player_ratings.setModel(None);self.scene_textures.clear();self.uniform_picker.clear();self.roster_tables.clear();self.audio_details.clear();self.texture_view.clear();self.texture_details.clear()
        if hasattr(self.view,'set_scene'):self.view.set_scene([],{})
        self.workspace=workspace
        from ..arena_preview import available as available_arenas
        self.arena_picker.clear()
        for asset in available_arenas(workspace):self.arena_picker.addItem(f'Stadium {asset:03d}',asset)
        self.arena_picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        from ..shoe_preview import available
        self.shoe_picker.clear();self.shoe_picker.addItems(available(workspace));self.shoe_picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        for kind,page in self.pages.items():page['model'].set_items(workspace.of_type(kind))
        from ..audio_catalog import group
        self.audio_groups=group(workspace.of_type('AUDO'));self.change_audio_category(self.audio_categories.currentIndex())
        rosters=workspace.of_type('ROST')
        if rosters:
            self.roster_search.clear();self.roster_school.blockSignals(True);self.roster_school.clear();self.roster_school.addItem('All schools',None);self.roster_school.addItem('Unassigned players',-1)
            self.roster_resource=rosters[0];self.roster=Roster(self.roster_resource.blocks()[0]);self.roster_tables.clear();self.roster_tables.addItems(list(self.roster.rows));self.change_table(self.roster_tables.currentText())
            for team in self.roster.rows['teams']:self.roster_school.addItem(team['school_name'] or team['short_name'],team['index'])
            self.roster_school.blockSignals(False)
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
        project=getattr(getattr(self,'mod_projects',None),'project',None)
        mode='private mod project copies • export through Mods' if project and workspace.root==project.edit else 'direct editing • restart the recomp'
        self.statusBar().showMessage(f"Xbox • {len(workspace.banks):,} banks • {len(workspace.resources):,} resources • {mode}")
    def change_table(self,table):
        if self.roster and table in self.roster.rows:
            from .roster_filter import RosterFilter
            previous_proxy=getattr(self,'roster_proxy',None);previous_model=getattr(self,'roster_model',None)
            model=RosterModel(self.roster,table);self.roster_model=model;model.error.connect(self.error);self.roster_proxy=RosterFilter(self.roster,table,self);self.roster_proxy.setSourceModel(model);self.roster_proxy.setSortRole(Qt.ItemDataRole.UserRole);self.roster_view.setModel(self.roster_proxy);self.roster_view.setSortingEnabled(True);self.roster_view.resizeColumnsToContents()
            self.roster_view.selectionModel().currentRowChanged.connect(self.change_player);self.player_tabs.setVisible(table=='players')
            for signal in (self.roster_proxy.rowsInserted,self.roster_proxy.rowsRemoved,self.roster_proxy.layoutChanged):signal.connect(self.update_roster_count)
            self.filter_roster()
            if previous_proxy is not None:previous_proxy.deleteLater()
            if previous_model is not None:previous_model.deleteLater()
    def update_roster_count(self,*args):
        if self.roster is not None and hasattr(self,'roster_proxy'):self.roster_count.setText(f'{self.roster_proxy.rowCount():,} / {self.roster_model.rowCount():,}')
    def roster_row(self,index=None):
        index=self.roster_view.currentIndex() if index is None else index
        return self.roster_proxy.mapToSource(index).row() if index.isValid() else -1
    def filter_roster(self,*args):
        if self.roster is None or not hasattr(self,'roster_proxy'):return
        try:
            self.roster_proxy.school(self.roster_school.currentData());self.roster_proxy.setFilterFixedString(self.roster_search.text());self.roster_count.setText(f'{self.roster_proxy.rowCount():,} / {self.roster_model.rowCount():,}')
            if not self.roster_view.currentIndex().isValid():self.clear_player_details()
        except ValueError as exc:self.error(str(exc))
    def clear_player_details(self):
        for view in (self.player_properties,self.player_ratings,self.player_eligibility,self.player_footwear):view.setModel(None)
        self.player_summary.clear()
    def change_player(self,index,previous):
        if self.roster_tables.currentText()!='players' or not index.isValid():self.clear_player_details();return
        player=self.roster_row(index);self.property_model=PlayerDetailsModel(self.roster,player,category='appearance');self.rating_model=PlayerDetailsModel(self.roster,player,True);self.eligibility_model=PlayerDetailsModel(self.roster,player,category='eligibility');self.footwear_model=PlayerDetailsModel(self.roster,player,category='footwear')
        for view,model in ((self.player_properties,self.property_model),(self.player_ratings,self.rating_model),(self.player_eligibility,self.eligibility_model),(self.player_footwear,self.footwear_model)):
            model.error.connect(self.error);model.dataChanged.connect(lambda *args,source=player:self.refresh_player_summary(source));view.setModel(model);view.resizeColumnsToContents()
        self.refresh_player_summary(player)
    def refresh_player_summary(self,player):
        if self.roster is None:return
        if hasattr(self,'roster_model') and self.roster_model.table=='players':self.roster_model.dataChanged.emit(self.roster_model.index(player,0),self.roster_model.index(player,self.roster_model.columnCount()-1))
        row=self.roster.rows['players'][player];self.player_summary.setText(f"{row['first_name']} {row['last_name']} • #{row['jersey_number']} • source player {player} • "+FIELDS['class_code']['choices'].get(str(row['class_code']),'Unknown class'))
    def selected_school(self):
        if self.roster_tables.currentText()=='teams' and self.roster_view.currentIndex().isValid():return self.roster_row()
        if self.roster_tables.currentText()=='players' and self.roster_view.currentIndex().isValid():
            from ..relationships import catalog
            owners=catalog(self.roster)['schools'].get(self.roster_row(),[])
            if len(owners)==1:return owners[0]
        if self.roster_school.currentData() is not None and self.roster_school.currentData()>=0:return self.roster_school.currentData()
        return 0
    def edit_relationships(self):
        if self.roster is None:return
        from .relationships import RelationshipsDialog
        try:
            dialog=RelationshipsDialog(self,self.roster,self.selected_school());dialog.changed.connect(self.roster_changed);dialog.exec()
        except (ValueError,OSError) as exc:self.error(str(exc))
    def edit_uniforms(self):
        if self.roster is None or self.workspace is None:return
        from .uniform_editor import UniformEditor
        try:
            dialog=UniformEditor(self,self.roster,self.workspace,self.selected_school());dialog.changed.connect(self.roster_changed);dialog.exec()
        except (ValueError,OSError) as exc:self.error(str(exc))
    def roster_changed(self):
        self.change_table(self.roster_tables.currentText())
        if self.roster is None:return
        from ..uniforms import rows,owner,name
        previous=self.uniform_picker.currentText();self.uniform_picker.blockSignals(True);self.uniform_picker.clear();owners={}
        for team in self.roster.rows['teams']:owners.setdefault(owner(self.roster,team['index']),[]).append(team['short_name'])
        for uniform in rows(self.roster):
            caption=' / '.join(dict.fromkeys(owners.get(uniform['owner'],[f"Owner {uniform['owner']}"])))
            self.uniform_picker.addItem(f"{caption} • {name(uniform['asset'],uniform['variant'])}",uniform['index'])
        match=self.uniform_picker.findText(previous)
        if match>=0:self.uniform_picker.setCurrentIndex(match)
        self.uniform_picker.blockSignals(False)
        self.select_uniform_shape()
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
            self.current_font=None
            try:
                blocks=r.blocks()
                import zlib
                if len(blocks[0])>=12 and blocks[0][8:12]==bytes.fromhex('24820002'):
                    from ..uniform_fonts import atlas
                    image=atlas(blocks);self.current_font=r;self.current_texture=None;self.texture_face.setEnabled(False);self.show_pil_image(image);self.texture_details.setText(r.label+f' • Xbox indexed font {image.width}×{image.height} • export/import PNG');return
                payload=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);path=r.folder/'texture.dds'
                descriptor=dds.info(payload)
                if 'raw_format' not in descriptor and not descriptor.get('direct_component') and path.exists():payload=path.read_bytes()
                self.current_texture=(r,payload,path);self.texture_face.blockSignals(True);self.texture_face.clear()
                for face in range(descriptor.get('faces',1)):self.texture_face.addItem(f'Face {face}')
                self.texture_face.setEnabled(descriptor.get('faces',1)>1);self.texture_face.blockSignals(False);self.show_current_texture_face();self.texture_details.setText(r.label+' • '+str(descriptor))
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
            source=t.get('source_resource',self.scene_resource);local=t.get('source_index',t['index']);path=source.folder/f"texture_{local:04d}.dds";descriptor=dds.info(t['dds']);payload=path.read_bytes() if path.exists() and 'raw_format' not in descriptor and not descriptor.get('direct_component') else t['dds'];images[t['index']]=dds.image(payload);self.scene_textures.addItem(f"{t.get('role','Scene')} texture {local} • {t['id']:08x}",t['index'])
        if hasattr(self.view,'set_scene'):self.view.set_scene(result['meshes'],images)
        self.pages['SCNE']['details'].setPlainText(f"{len(result['meshes'])}/{result['declared_parts']} mesh parts • {sum(len(m['vertices'])//3 for m in result['meshes']):,} triangles\n"+'\n'.join(result['warnings']))
        self.statusBar().showMessage('Xbox scene ready')
    def select_uniform_shape(self):
        if self.roster is None:return
        from ..uniforms import rows
        index=self.uniform_picker.currentData();uniforms=rows(self.roster)
        if isinstance(index,int) and 0<=index<len(uniforms):self.uniform_shape.setCurrentIndex(uniforms[index]['shape'])
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
    def preview_player_shoes(self):
        if self.roster is None or self.roster_tables.currentText()!='players' or self.roster_row()<0:return
        variant,ok=QInputDialog.getItem(self,'Player shoe artwork','Uniform',['Home','Away'],0,False)
        if not ok:return
        try:
            from ..footwear import texture
            filename=texture(self.roster.rows['players'][self.roster_row()],variant=='Away');index=self.shoe_picker.findText(filename)
            if index<0:raise ValueError('Assigned Xbox shoe artwork is missing: '+filename)
            self.shoe_picker.setCurrentIndex(index);self.preview_shoes();self.tabs.setCurrentIndex(0)
        except ValueError as exc:self.error(str(exc))
    def preview_arena(self):
        if self.workspace is None:return
        from .relationships import selected
        from ..arena_preview import preview
        try:asset=selected(self.arena_picker)
        except ValueError as exc:self.error(str(exc));return
        workspace=self.workspace;mode=self.arena_mode.currentText();self.generation+=1;generation=self.generation
        def decode(progress):
            result=preview(workspace,asset,mode);result['generation']=generation;return result
        self.run_job(decode,self.show_scene)
    def toggle_cutaway(self,checked):
        if hasattr(self.view,'set_scene'):self.view.cutaway=checked;self.view.set_scene(self.view.meshes,self.view.images)
    def show_image(self,payload):
        self.show_pil_image(dds.image(payload))
    def show_current_texture_face(self,*args):
        if self.current_texture is None:return
        payload=self.current_texture[1];descriptor=dds.info(payload)
        if 'raw_format' in descriptor:
            from ..raw_texture import image_from_dds
            self.show_pil_image(image_from_dds(payload,max(0,self.texture_face.currentIndex())))
        else:self.show_image(payload)
    def show_pil_image(self,image):
        image=image.convert('RGBA');data=image.tobytes();q=QImage(data,image.width,image.height,image.width*4,QImage.Format.Format_RGBA8888).copy();self.texture_view.setPixmap(QPixmap.fromImage(q).scaled(700,600,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
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
        if self.current_font is not None:
            from ..uniform_fonts import atlas
            resource=self.current_font;path,_=QFileDialog.getSaveFileName(self,'Export Xbox indexed font','','PNG (*.png)')
            if path:atlas(resource.blocks()).save(path)
            return
        if not self.current_texture:return
        resource,payload,target=self.current_texture;descriptor=dds.info(payload);path,_=QFileDialog.getSaveFileName(self,'Export texture artwork','','DDS (*.dds);;PNG face (*.png)')
        if path:
            if Path(path).suffix.casefold()=='.png':
                from ..raw_texture import image_from_dds
                (image_from_dds(payload,max(0,self.texture_face.currentIndex())) if 'raw_format' in descriptor else dds.image(payload)).save(path)
            else:Path(path).write_bytes(payload)
    def replace_texture(self):
        if self.current_font is not None:
            resource=self.current_font;path,_=QFileDialog.getOpenFileName(self,'Save Xbox indexed font artwork','','Artwork (*.png *.dds *.tga *.bmp)')
            if path:
                try:
                    if self.workspace is not resource.workspace:raise ValueError('Source folder changed while selecting artwork')
                    from ..uniform_fonts import save_atlas,atlas
                    save_atlas(resource,path);self.show_pil_image(atlas(resource.blocks()));self.statusBar().showMessage('Indexed font saved directly to its component. Restart the recomp to apply.')
                except (ValueError,OSError) as exc:self.error(str(exc))
            return
        if not self.current_texture:return
        r,old,target=self.current_texture
        path,_=QFileDialog.getOpenFileName(self,'Replace texture artwork','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
        if not path:return
        try:
            if self.workspace is not r.workspace:raise ValueError('Source folder changed while selecting artwork')
            from ..edits import save_texture,artwork_payload
            if 'raw_format' in dds.info(old) or dds.info(old).get('direct_component'):
                from ..raw_texture import from_image
                payload=Path(path).read_bytes() if Path(path).suffix.casefold()=='.dds' else from_image(path,old,max(0,self.texture_face.currentIndex())) if 'raw_format' in dds.info(old) else dds.from_image(path,old,False);save_texture(r,payload);blocks=r.blocks();fresh=dds.xbox_dds(blocks[0],blocks[1] if len(blocks)>1 else None);self.current_texture=(r,fresh,target);self.show_current_texture_face();self.statusBar().showMessage('Texture saved to its loose component; no asset bank rebuilt. Restart the recomp to apply.')
            else:
                target=save_texture(r,artwork_payload(path,old));self.current_texture=(r,target.read_bytes(),target);self.show_image(target.read_bytes());self.statusBar().showMessage('DDS saved directly to assets. Restart the recomp to apply.')
        except ValueError as exc:self.error(str(exc))
    def scene_texture(self):
        if not self.scene_data:return None
        index=self.scene_textures.currentData();return next((t for t in self.scene_data['textures'] if t['index']==index),None)
    def export_cloth_obj(self):
        resource=self.selected('SCNE',self.pages['SCNE']['view'].currentIndex())
        if resource is None:return
        path,_=QFileDialog.getSaveFileName(self,'Export selected Xbox cloth in model space','','OBJ (*.obj)')
        if path:
            from ..geometry import export_obj
            self.run_job(lambda progress:export_obj(resource,path),lambda result:self.statusBar().showMessage('Exported cloth OBJ and source-bound companion. Preserve vertex order and topology.'))
    def import_cloth_obj(self):
        resource=self.selected('SCNE',self.pages['SCNE']['view'].currentIndex())
        if resource is None:return
        path,_=QFileDialog.getOpenFileName(self,'Import source-bound Xbox cloth positions','','OBJ (*.obj)')
        if not path or self.workspace is not resource.workspace:return
        answer=QMessageBox.question(self,'Save shared cloth positions',f'Save model-space positions to {resource.label}? Every uniform using this cloth resource shares these edits.',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Cancel)
        if answer!=QMessageBox.StandardButton.Save:return
        from ..geometry import import_obj
        def finished(count):
            self.statusBar().showMessage(f'Saved {count} cloth positions directly to the component. Restart the recomp to apply.')
            if self.workspace is resource.workspace:self.select_resource('SCNE',self.pages['SCNE']['view'].currentIndex())
        self.run_job(lambda progress:import_obj(resource,path),finished)
    def export_scene_dds(self):
        t=self.scene_texture()
        if not t:return
        path,_=QFileDialog.getSaveFileName(self,'Export embedded Xbox DDS','','DDS (*.dds)')
        resource=t.get('source_resource',self.scene_resource);local=t.get('source_index',t['index']);current=resource.folder/f"texture_{local:04d}.dds"
        descriptor=dds.info(t['dds'])
        if path:Path(path).write_bytes(current.read_bytes() if current.is_file() and 'raw_format' not in descriptor and not descriptor.get('direct_component') else t['dds'])
    def replace_scene_dds(self):
        t=self.scene_texture()
        if not t:return
        resource=t.get('source_resource',self.scene_resource);local=t.get('source_index',t['index']);generation=self.generation
        path,_=QFileDialog.getOpenFileName(self,'Replace scene artwork','','Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)')
        if not path:return
        try:
            if self.workspace is not resource.workspace or generation!=self.generation:raise ValueError('Source scene changed while selecting artwork')
            from ..edits import save_scene_texture,artwork_payload
            save_scene_texture(resource,local,artwork_payload(path,t['dds']));fresh=scene.textures(resource.blocks())
            if self.scene_data.get('sources'):
                by_index={item['index']:item for item in fresh}
                for item in self.scene_data['textures']:
                    if item.get('source_resource') is resource:item['dds']=by_index[item['source_index']]['dds']
            else:self.scene_data['textures']=fresh
            self.show_scene(self.scene_data);self.statusBar().showMessage('Scene artwork saved. Restart the updated recomp to apply.')
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
    def import_audio_folder(self):
        workspace=self.workspace
        if workspace is None:return
        folder=QFileDialog.getExistingDirectory(self,'Review exported Xbox WAV folder')
        if not folder:return
        def review(rows):
            if self.workspace is not workspace:return
            if not rows:self.statusBar().showMessage('No WAV files changed from this export');return
            dialog=QDialog(self);dialog.setWindowTitle('Review Xbox WAV replacements');dialog.resize(760,550);layout=QVBoxLayout(dialog);layout.addWidget(QLabel(f'{len(rows)} changed tracks. Select replacements to save directly to their resource folders.'))
            scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();choices_layout=QVBoxLayout(content);choices=[]
            for row in rows:
                checkbox=QCheckBox(row['label']);checkbox.setChecked(True);checkbox.setToolTip(row['resource']);choices_layout.addWidget(checkbox);choices.append((row,checkbox))
            scroll.setWidget(content);layout.addWidget(scroll);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()==QDialog.DialogCode.Accepted and self.workspace is workspace:
                selected=[row for row,checkbox in choices if checkbox.isChecked()]
                self.run_job(lambda progress:audio.apply_batch(workspace,folder,selected,progress),lambda count:self.statusBar().showMessage(f'Saved {count} native WAV replacements. Restart the recomp to apply.'))
        self.run_job(lambda progress:audio.review_batch(workspace,folder),review)
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
        if self.roster:self.roster.undo();self.roster_changed()
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
        if self.roster and self.roster_tables.currentText()=='players' and self.roster_view.currentIndex().isValid():self.copied_ratings=list(self.roster.rows['players'][self.roster_row()]['ratings']);self.statusBar().showMessage('Copied all 30 Xbox ratings')
    def paste_ratings(self):
        if not self.roster or self.roster_tables.currentText()!='players' or self.copied_ratings is None:return
        try:
            with self.roster.transaction():
                for index in self.roster_view.selectionModel().selectedRows():
                    for channel,value in enumerate(self.copied_ratings):
                        if value<RATINGS[channel]['minimum']:raise ValueError('Copied ratings contain a preserved sentinel below the Xbox menu range')
                        self.roster.set_rating(self.roster_row(index),channel,value)
            self.change_table('players');self.statusBar().showMessage('Ratings pasted as one undoable edit; Save roster to write changes')
        except ValueError as exc:self.error(str(exc))
    def add_uniform(self):
        if not self.roster or self.roster_tables.currentText()!='teams':return
        team=self.roster_row()
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
        if self.roster:self.roster.redo();self.roster_changed()
    def save_roster(self):
        if not self.roster:return
        try:self.roster.save(self.roster_resource.component_path());self.statusBar().showMessage('Xbox roster saved. Restart the updated recomp to apply.')
        except ValueError as exc:self.error(str(exc))
    def edit_rating(self):
        if not self.roster or self.roster_tables.currentText()!='players':return
        index=self.roster_row()
        if index<0:return
        channel,ok=QInputDialog.getInt(self,'Stored rating channel','Xbox channel (semantic captions pending)',1,1,30)
        if not ok:return
        value,ok=QInputDialog.getDouble(self,'Stored rating value','Value (stored ×100)',self.roster.rows['players'][index]['ratings'][channel-1],0,99,2)
        if ok:self.roster.set_rating(index,channel-1,value)
    def edit_palette(self):
        if not self.roster or self.roster_tables.currentText()!='teams':return
        index=self.roster_row()
        if index<0:return
        slot,ok=QInputDialog.getInt(self,'Team palette','Xbox RGBA slot',0,0,30)
        if not ok:return
        from PySide6.QtGui import QColor
        value=self.roster.rows['teams'][index]['palette'][slot];c=QColor(*bytes.fromhex(value));chosen=QColorDialog.getColor(c,self,'Edit RGBA palette slot',QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if chosen.isValid():self.roster.set_palette(index,slot,bytes((chosen.red(),chosen.green(),chosen.blue(),chosen.alpha())))


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--assets');parser.add_argument('--smoke',action='store_true');parser.add_argument('--smoke-dialogs',action='store_true');parser.add_argument('--report');args=parser.parse_args(argv)
    if args.smoke_dialogs and (not args.smoke or not args.assets or os.environ.get('QT_QPA_PLATFORM')!='offscreen'):parser.error('--smoke-dialogs requires --smoke, --assets and QT_QPA_PLATFORM=offscreen')
    app=QApplication.instance() or QApplication([]);app.setStyle('Fusion');window=Studio(offscreen=os.environ.get('QT_QPA_PLATFORM')=='offscreen');window.show()
    if args.assets:window.open_assets(args.assets)
    if args.smoke:
        def finish():
            if window.jobs:QTimer.singleShot(100,finish);return
            report=dict(window_title=window.windowTitle(),tabs=[window.tabs.tabText(i) for i in range(window.tabs.count())],workspace=window.workspace.report() if window.workspace else None,error=window.last_error)
            if args.smoke_dialogs and not window.last_error:
                try:
                    from .relationships import RelationshipsDialog
                    from .uniform_editor import UniformEditor
                    relationships=RelationshipsDialog(window,window.roster);uniforms=UniformEditor(window,window.roster,window.workspace)
                    report['relationships']=dict(fields=len(relationships.links),members=relationships.members.count());report['uniform_editor']=dict(routes=uniforms.routes.count(),artwork=uniforms.art.count(),players=uniforms.player.count())
                    from ..uniform_fonts import atlas
                    font=next(uniforms.art.itemData(i) for i in range(uniforms.art.count()) if uniforms.is_font(uniforms.art.itemData(i)));image=atlas(font.blocks());report['font_atlas']=list(image.size)
                    relationships.close();uniforms.close()
                except Exception as exc:window.last_error=str(exc)
                report['error']=window.last_error
            if args.report:Path(args.report).write_text(json.dumps(report,indent=2))
            window.close();app.exit(1 if window.last_error else 0)
        QTimer.singleShot(250,finish)
    return app.exec()
