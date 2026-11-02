"""Render roster dialogs on Qt's offscreen platform; never show a desktop window."""
import argparse,os,sys
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QFont
from choops_recomp.ui.app import Studio
from choops_recomp.ui.relationships import RelationshipsDialog
from choops_recomp.ui.uniform_editor import UniformEditor
from choops_recomp.workspace import Workspace
from choops_recomp.roster import Roster


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();output=args.output.resolve();owned=Path(__file__).resolve().parents[1]/'output'
    if output.exists() or not output.is_relative_to(owned):raise ValueError('Choose a new private output under this checkout/output')
    output.mkdir(parents=True);app=QApplication([]);app.setStyle('Fusion')
    # The Windows offscreen plugin has no automatic system font database.
    font=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/segoeui.ttf'
    if font.is_file():
        if QFontDatabase.addApplicationFont(str(font))<0:raise ValueError('Cannot register the system font for UI inspection')
        app.setFont(QFont('Segoe UI',9))
    parent=Studio(offscreen=True);workspace=Workspace(args.assets);model=Roster(workspace.of_type('ROST')[0].blocks()[0]);parent.workspace=workspace;parent.roster=model;parent.roster_resource=workspace.of_type('ROST')[0]
    for kind,name in ((RelationshipsDialog,'relationships'),(UniformEditor,'uniforms')):
        dialog=kind(parent,model,workspace) if kind is UniformEditor else kind(parent,model);dialog.show();app.processEvents()
        if parent.last_error:raise ValueError(parent.last_error)
        if not dialog.grab().save(str(output/(name+'.png'))):raise ValueError('Cannot save dialog render')
        dialog.close()
    parent.close();print('Both dialogs rendered offscreen with no errors; no game/window/input automation')


if __name__=='__main__':main()
