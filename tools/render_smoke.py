"""Native OpenGL rendering check using the actual viewer, with no visible window."""
import argparse
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.pop('QT_QPA_PLATFORM',None)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QOpenGLContext,QOffscreenSurface,QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLFramebufferObject,QOpenGLFramebufferObjectFormat
from choops_recomp.ui.scene_view import SceneView
from choops_recomp.workspace import Workspace
from choops_recomp.scene import preview,textures
from choops_recomp.dds import image


def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--resource',default='s000.iff/9');p.add_argument('--arena',type=int);p.add_argument('--arena-mode',default='combined');p.add_argument('--uniform',type=int);p.add_argument('--number',type=int);p.add_argument('--surname',default='');p.add_argument('--yaw',type=float,default=30);p.add_argument('--shoe');p.add_argument('--expect-textured',action='store_true');p.add_argument('--output',required=True);a=p.parse_args()
    app=QApplication([]);fmt=QSurfaceFormat();fmt.setVersion(2,0);fmt.setDepthBufferSize(24)
    context=QOpenGLContext();context.setFormat(fmt)
    if not context.create():raise RuntimeError('Native OpenGL context unavailable')
    surface=QOffscreenSurface();surface.setFormat(context.format());surface.create()
    if not context.makeCurrent(surface):raise RuntimeError('Cannot make native OpenGL current')
    class InvisibleView(SceneView):
        def context(self):return context
        def makeCurrent(self):return context.makeCurrent(surface)
        def doneCurrent(self):context.doneCurrent()
    w=Workspace(a.assets)
    if a.shoe:
        from choops_recomp.shoe_preview import preview as shoe_preview
        result=shoe_preview(w,a.shoe);images=result['images']
    elif a.arena is not None:
        from choops_recomp.arena_preview import preview as arena_preview
        result=arena_preview(w,a.arena,a.arena_mode);images=result['images']
    elif a.uniform is not None:
        from choops_recomp.roster import Roster
        from choops_recomp.uniforms import rows
        from choops_recomp.uniform_preview import preview as uniform_preview
        result=uniform_preview(w,rows(Roster(w.of_type('ROST')[0].blocks()[0]))[a.uniform],number=a.number,surname=a.surname);images=result['images']
    else:
        r=w.resource(a.resource);blocks=r.blocks();result=preview(blocks);images={t['index']:image(t['dds']) for t in textures(blocks) if 'dds' in t}
    view=InvisibleView();view.resize(1000,700);view.initializeGL();view.set_scene(result['meshes'],images);view.yaw=a.yaw
    framebuffer_format=QOpenGLFramebufferObjectFormat();framebuffer_format.setAttachment(QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)
    fbo=QOpenGLFramebufferObject(1000,700,framebuffer_format);fbo.bind();view.gl.glViewport(0,0,1000,700);view.paintGL();view.gl.glFinish()
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    if not fbo.toImage().save(str(output)):raise RuntimeError('Could not save render check image')
    if a.expect_textured:
        from PIL import Image
        with Image.open(output) as rendered:
            if len(rendered.convert('RGB').getcolors(1000000) or [])<=8:raise RuntimeError('Expected multicolor DDS artwork, but render is flat')
    print(f'Native GL rendered {len(result["meshes"])} Xbox meshes with {len(images)} DDS images; no window/game was shown')
    view.cleanup();context.makeCurrent(surface);fbo.release();context.doneCurrent();return 0


if __name__=='__main__':raise SystemExit(main())
