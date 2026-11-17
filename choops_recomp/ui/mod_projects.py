"""Compact project area; existing editors operate on independent bank copies."""
import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QPlainTextEdit,QFileDialog,QInputDialog,QComboBox,QDialog,QDialogButtonBox,QCheckBox

from ..mod_project import ModProject,read_json
from .artwork_drop import ArtworkDrop


class ModProjects(QWidget):
    def __init__(self, studio):
        super().__init__();self.studio=studio;self.project=None;self.settings=QSettings("CHoops", "Recomp Studio")
        layout=QVBoxLayout(self)
        label=QLabel('Copy an existing bank into a project, drop artwork onto its texture preview, then export the mod folder. Installed assets are read-only.');label.setWordWrap(True);layout.addWidget(label)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Create Mod…',self.create),('Open Project or Mod Folder…',self.open),('Combine with Mod Folder…',self.combine),('Separate Content…',self.separate),('Set Mods Folder…',self.choose_mods),('Save metadata',self.save)]:
            button=QPushButton(title);button.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(button)
        self.location=QLabel('No project open');self.location.setWordWrap(True);layout.addWidget(self.location)
        self.description=QLineEdit();self.description.setPlaceholderText('Mod description');layout.addWidget(self.description)
        advanced = QCheckBox('Show advanced mod metadata')
        layout.addWidget(advanced)
        self.metadata=QPlainTextEdit();self.metadata.setMaximumHeight(200);layout.addWidget(self.metadata)
        self.metadata.hide()
        advanced.toggled.connect(self.metadata.setVisible)
        row=QHBoxLayout();layout.addLayout(row);self.banks=QComboBox();row.addWidget(self.banks,1)
        for title,fn in [('Add source bank copy',self.add_bank),('Edit project copies',self.edit),('Compare selected texture',self.compare)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(b)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Build one-image court…',self.court),('Build or replace uniform…',self.alternate),('Review differences',self.review),('Export Mod Folder…',self.export)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(b)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Attach native roster + header…',self.roster),('Attach prepared uniform bank…',self.uniform),('Attach external DLL…',self.extension)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.invoke(f));row.addWidget(b)
        self.report=QPlainTextEdit();self.report.setReadOnly(True);layout.addWidget(self.report,1)

    def invoke(self, fn):
        try:fn()
        except Exception as exc:self.studio.error(str(exc))

    def require(self):
        if self.project is None:raise ValueError('Create or open a mod project first')
        return self.project

    def choose_mods(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose the recomp Mods folder', self.settings.value('mods', ''))
        if folder:
            self.settings.setValue('mods', folder)

    def installation(self, assets=None):
        if assets is None:
            remembered = self.settings.value('assets', '')
            assets = Path(remembered) if remembered else None
        if not assets or not (Path(assets).parent/'assets.json').is_file():
            assets = QFileDialog.getExistingDirectory(self, 'Installed Xbox assets folder')
            if not assets:
                return None
        for candidate in (self.settings.value('runtime', ''), *Path(assets).parents):
            if candidate and (Path(candidate)/'tools/chmod.ps1').is_file():
                runtime = Path(candidate)
                break
        else:
            runtime = QFileDialog.getExistingDirectory(self, 'Recomp runtime folder')
            if not runtime:
                return None
        self.settings.setValue('assets', str(assets))
        self.settings.setValue('runtime', str(runtime))
        if not self.settings.value('mods', '') and (Path(runtime)/'mods').is_dir():
            self.settings.setValue('mods', str(Path(runtime)/'mods'))
        return assets, runtime

    def new_location(self):
        destination, _ = QFileDialog.getSaveFileName(self, 'New project directory')
        return destination

    def new_identity(self, default_name=''):
        values = []
        for label, default in (('Mod ID (author.mod-name)', ''), ('Mod name', default_name), ('Author', '')):
            value, ok = QInputDialog.getText(self, 'New Mod', label, text=default)
            if not ok:
                return None
            values.append(value)
        return values

    def create(self):
        if not self.studio.maybe_save():
            return
        installation = self.installation()
        if not installation:
            return
        destination = self.new_location()
        identity = self.new_identity() if destination else None
        if identity:
            self.studio.run_job(lambda _: ModProject.create(destination, *installation, *identity), self.opened)

    def open(self):
        if not self.studio.maybe_save():
            return
        path = QFileDialog.getExistingDirectory(self, 'Open project or installed mod folder', self.settings.value('mods', ''))
        if not path:
            return
        folder = Path(path)
        if (folder/'project.json').is_file():
            installation = self.installation(Path(read_json(folder/'project.json')['source'])/'assets')
            if installation:
                self.opened(ModProject(folder, installation[1]))
        elif (folder/'mod.json').is_file():
            installation = self.installation()
            destination = self.new_location() if installation else None
            if destination:
                self.studio.run_job(lambda _: ModProject.import_folders(destination, *installation, [folder]), self.opened)
        else:
            raise ValueError('Select a folder containing project.json or mod.json')

    def opened(self, project):
        self.project = project
        self.refresh()
        self.activate()

    def combine(self):
        project = self.require()
        if not self.studio.maybe_save():
            return
        folder = QFileDialog.getExistingDirectory(self, 'Select another mod folder containing mod.json', self.settings.value('mods', ''))
        if folder:
            self.compose(project, extra=Path(folder))

    def separate(self):
        project = self.require()
        if self.studio.maybe_save():
            self.compose(project, split=True)

    def compose(self, project, *, extra=None, split=False):
        self.save()
        destination = self.new_location()
        identity = self.new_identity(project.state['manifest']['name']) if destination else None
        if not identity:
            return
        if split:
            # Review the generated manifest so newly authored banks are included.
            self.studio.run_job(lambda _: self.split_groups(project), lambda groups:
                                self.select_group(project, destination, identity, groups))
        else:
            self.compose_job(project, destination, identity, extra=extra)

    @staticmethod
    def split_groups(project):
        with tempfile.TemporaryDirectory(dir=project.root, prefix='.catalog-') as temp:
            return project.content_groups(project.build(Path(temp)))

    def select_group(self, project, destination, identity, groups):
        if not groups:
            return
        group, ok = QInputDialog.getItem(self, 'Separate content', 'Bank or content to put in the new project', groups, editable=False)
        if ok:
            self.compose_job(project, destination, identity, groups={group})

    def compose_job(self, project, destination, identity, *, extra=None, groups=None):
        def process(_):
            with tempfile.TemporaryDirectory(dir=project.root, prefix='.compose-') as temp:
                stage = Path(temp)
                project.build(stage)
                folders = [stage] + ([extra] if extra else [])
                return ModProject.import_folders(destination, project.source/'assets', project.contract.root,
                                                 folders, identity=identity, groups=groups)
        self.studio.run_job(process, self.opened)

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

    def artwork_field(self, layout, label, suffixes=None):
        row = QHBoxLayout()
        drop = ArtworkDrop(label, suffixes=suffixes)
        drop.setWordWrap(True)
        field = QLineEdit()
        field.setReadOnly(True)
        field.setPlaceholderText('Drop artwork on the label or browse')
        drop.dropped.connect(field.setText)
        browse = QPushButton('Browse…')
        def choose():
            pattern = 'DDS (*.dds)' if suffixes == {'.dds'} else 'Artwork (*.dds *.png *.jpg *.jpeg *.tga *.bmp)'
            file, _ = QFileDialog.getOpenFileName(self, label, filter=pattern)
            if file:
                field.setText(file)
        browse.clicked.connect(choose)
        for widget in (drop, field, browse):
            row.addWidget(widget)
        layout.addLayout(row)
        return field

    def author_dialog(self, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(740, 180)
        return dialog, QVBoxLayout(dialog)

    def save_bar(self, dialog, layout):
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

    def court(self):
        project = self.require()
        dialog, layout = self.author_dialog('One-image court')
        layout.addWidget(QLabel('Use the UGA artwork layout, 2048×1024 BC1/DXT1, with all 12 mip levels.'))
        court = QLineEdit()
        court.setPlaceholderText('Court ID, e.g. s272. Blank uses the artwork folder ID.')
        layout.addWidget(court)
        art = self.artwork_field(layout, 'Full court DDS', {'.dds'})
        self.save_bar(dialog, layout)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if not art.text():
            raise ValueError('Choose the full-court DDS')
        target = court.text().strip().casefold() or Path(art.text()).parent.name.casefold()
        artwork = art.text()
        self.studio.run_job(lambda _:project.stage_full_court(target, artwork),
                            lambda result:self.feature_saved(project, f'Saved {result} court to the project.'))

    def alternate(self):
        project = self.require()
        from ..roster import Roster
        # The English master provides the same team indices used by the native template.
        folder = project.source / 'assets/roster_english.iff'
        paths = [*folder.glob('*.rost/roster.dat'), *folder.glob('*.rost/block0.dat')]
        if len(paths) != 1:
            raise ValueError('The installed Xbox English roster template is missing or ambiguous')
        model = Roster(paths[0].read_bytes())
        dialog, layout = self.author_dialog('Build or replace uniform')
        team = QComboBox()
        team.setEditable(True)
        team.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for row in sorted(model.rows['teams'], key=lambda row:(row['school_name'] or row['short_name']).casefold()):
            team.addItem(row['school_name'] or row['short_name'], row['index'])
        layout.addWidget(team)
        variant = QComboBox()
        variant.addItems(['Home — UH', 'Away — UA', 'X — Alternate 1', 'Y — Alternate 2', 'Z — Alternate 3'])
        layout.addWidget(variant)
        jersey = self.artwork_field(layout, 'World jersey artwork')
        shorts = self.artwork_field(layout, 'World shorts artwork')
        selection = self.artwork_field(layout, 'Selection jersey (optional)')
        numbers = self.artwork_field(layout, 'World numbers (optional)')
        selection_numbers = self.artwork_field(layout, 'Selection numbers (optional)')
        lettering = self.artwork_field(layout, 'Surname sheet (optional)')
        logo = self.artwork_field(layout, 'World logo (optional)')
        neck = QComboBox()
        neck.addItem('Use Home neckline', None)
        for index, label in enumerate(('U', 'V', 'V triangle', 'Triangle', 'Wishbone')):
            neck.addItem(label, index)
        layout.addWidget(neck)
        from .. import uniforms
        routes = {(row['owner'], row['variant']): row for row in uniforms.rows(model)}

        def current_route():
            index = team.findText(team.currentText())
            if index < 0:
                return None, None
            owner = uniforms.owner(model, team.itemData(index))
            routed = routes.get((owner, variant.currentIndex()))
            template = routed or (routes.get((owner, 0)) if variant.currentIndex() >= 2 else None)
            return routed, template

        def update_neck(*_):
            routed, template = current_route()
            neck.setEnabled(routed is None and template is not None)
            if not neck.isEnabled():
                neck.setCurrentIndex(0)
            neck.setItemText(0, 'Keep stock neckline' if routed is not None else 'Use Home neckline')

        team.currentTextChanged.connect(update_neck)
        variant.currentIndexChanged.connect(update_neck)
        update_neck()
        if not self.studio.offscreen:
            self.add_alternate_preview(dialog, layout, project, team, variant, neck, jersey, shorts, current_route)
        bumps = QCheckBox('Generate jersey and shorts bump and material maps')
        bumps.setChecked(True)
        layout.addWidget(bumps)
        self.save_bar(dialog, layout)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        team_index = team.findText(team.currentText())
        if team_index < 0:
            raise ValueError('Choose a team')
        index, slot = team.itemData(team_index), variant.currentIndex()
        inputs = jersey.text() or None, shorts.text() or None, selection.text() or None
        options = dict(numbers=numbers.text() or None, selection_numbers=selection_numbers.text() or None,
                       lettering=lettering.text() or None, logo=logo.text() or None,
                       generate_bumps=bumps.isChecked(), neck_shape=neck.currentData())
        self.studio.run_job(lambda _:project.stage_uniform(index, slot, *inputs, **options),
                            lambda names:self.feature_saved(project, 'Saved ' + ' and '.join(names) + ' to the project.'))

    def add_alternate_preview(self, dialog, layout, project, team, variant, neck, jersey, shorts, current_route):
        from PySide6.QtCore import QTimer
        from .. import uniform_preview
        from ..workspace import Workspace
        from .scene_view import SceneView

        view = SceneView()
        view.setMinimumHeight(300)
        layout.addWidget(view, 1)
        generation = 0
        pending = False
        workspace = None
        timer = QTimer(dialog)
        timer.setSingleShot(True)
        timer.setInterval(180)

        def schedule(*_):
            nonlocal generation
            generation += 1
            timer.start()

        def render():
            nonlocal pending
            artwork = {'jersey': jersey.text(), 'shorts': shorts.text()}
            if pending or not any(artwork.values()) or not dialog.isVisible():
                return
            _, row = current_route()
            if row is None:
                return
            shape = neck.currentData()
            current = generation
            pending = True

            def decode(_):
                nonlocal workspace
                try:
                    if workspace is None:
                        workspace = Workspace(project.source / 'assets')
                    return uniform_preview.preview(workspace, row, shape, artwork=artwork), None
                except (ValueError, OSError) as exc:
                    return None, str(exc)

            def finished(result):
                nonlocal pending
                pending = False
                if not dialog.isVisible():
                    return
                if generation != current:
                    timer.start()
                    return
                scene, error = result
                if error:
                    view.setToolTip(error)
                else:
                    view.setToolTip('')
                    view.set_scene(scene['meshes'], scene['images'])

            self.studio.run_job(decode, finished)

        timer.timeout.connect(render)
        for field in (jersey, shorts):
            field.textChanged.connect(schedule)
        team.currentTextChanged.connect(schedule)
        variant.currentIndexChanged.connect(schedule)
        neck.currentIndexChanged.connect(schedule)
        dialog.resize(820, 720)

    def feature_saved(self, project, message):
        if self.project is project:
            self.refresh()
            self.report.setPlainText(message + ' Export Mod Folder to use it.')

    def review(self):
        p=self.require();self.report.setPlainText(json.dumps(dict(changes=p.review(),roster=p.state['manifest'].get('roster'),uniforms=p.state['manifest'].get('uniforms'),extensions=p.state['manifest'].get('extensions')),indent=2))

    def export(self, roster_only=False):
        p=self.require()
        if not self.studio.maybe_save():return
        self.save()
        manifest = p.state['manifest']
        default = Path(self.settings.value('mods', '') or p.root.parent)/manifest['id']
        if default.exists():
            default = default.with_name(default.name+'-'+manifest['version'])
        output, _ = QFileDialog.getSaveFileName(self, 'Export new mod folder', str(default))
        if not output:
            return
        dependencies=[]
        if p.state['manifest'].get('dependencies'):
            paths,ok=QInputDialog.getMultiLineText(self,'Validation dependencies','Installed dependency version directories, one per line')
            if not ok:return
            dependencies=[Path(s.strip()) for s in paths.splitlines() if s.strip()]
        self.report.setPlainText('Validating package with the runtime…')
        self.studio.run_job(lambda progress:p.export_folder(output,dependencies,roster_only=roster_only),lambda manifest:self.report.setPlainText('Exported '+output+'\nRuntime metadata/source contracts accepted. DDS shared-owner checks still run during launcher preparation.\nNot in-game verified. Install and enable through the runtime launcher.'))
