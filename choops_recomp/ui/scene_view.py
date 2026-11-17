"""Generic DDS-textured orbit view, adapted from the owner's v1.23 Qt viewer.

Only host drawing/camera code is reused. All resource decoding is Xbox-specific.
"""
from array import array
import math
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QMatrix4x4,QVector3D,QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLBuffer,QOpenGLShader,QOpenGLShaderProgram,QOpenGLTexture,QOpenGLFunctions_2_0
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class SceneView(QOpenGLWidget):
    def __init__(self,parent=None):
        super().__init__(parent);fmt=QSurfaceFormat();fmt.setVersion(2,0);fmt.setDepthBufferSize(24);self.setFormat(fmt)
        self.setMinimumSize(320,300);self.meshes=[];self.images={};self.textures={};self.batches=[];self.vertices=[];self.dirty=True
        self.yaw=30.;self.pitch=28.;self.distance=3.;self.radius=1.;self.center=QVector3D();self.last=None;self.cutaway=True;self.wireframe=False;self.program=None;self.buffer=None;self.error=''
    def set_scene(self,meshes,images):
        self.meshes=meshes;self.images=images;self.vertices=[];self.batches=[]
        for mesh in meshes:
            if self.cutaway and mesh.get('hidden_by_default'):continue
            start=len(self.vertices);self.vertices.extend(mesh['vertices'])
            layer={'floor':1,'paint':2,'centerlogo':3,'lines':4}.get(mesh['name'].rsplit('/',1)[-1].lower(),0)
            for b in mesh['batches']:self.batches.append(dict(b,first=start+b['first'],layer=layer))
        self.fit();self.dirty=True;self.update()
    def fit(self):
        if self.vertices:
            low=[min(v[k] for v in self.vertices) for k in range(3)];high=[max(v[k] for v in self.vertices) for k in range(3)]
            self.center=QVector3D(*[(a+b)/2 for a,b in zip(low,high)]);self.radius=max(math.sqrt(sum((b-a)**2 for a,b in zip(low,high)))/2,.001)
        self.distance=3.;self.update()
    def initializeGL(self):
        self.gl=QOpenGLFunctions_2_0();self.gl.initializeOpenGLFunctions();self.program=QOpenGLShaderProgram(self)
        vertex='''#version 110
attribute vec3 position; attribute vec2 uv; attribute vec4 color; uniform mat4 mvp; varying vec2 texcoord; varying vec4 tint;
void main(){ gl_Position=mvp*vec4(position,1.0); texcoord=uv; tint=color; }'''
        fragment='''#version 110
uniform sampler2D diffuse; uniform bool textured; uniform vec4 materialColor; varying vec2 texcoord; varying vec4 tint;
uniform sampler2D numberMap; uniform sampler2D nameMap; uniform bool useNumber; uniform bool useName; uniform vec4 numberUV; uniform vec4 backNumberUV; uniform vec4 namePlacement; uniform float nameScale;
void main(){vec4 c=textured?texture2D(diffuse,texcoord):vec4(0.72,0.75,0.81,1.0);c*=tint*materialColor;
if(useNumber){vec2 n=texcoord*numberUV.xy+numberUV.zw;if(n.x>=0.0&&n.x<=1.0&&n.y>=0.0&&n.y<=1.0){vec4 g=texture2D(numberMap,n);c.rgb=mix(c.rgb,g.rgb,g.a);}vec2 b=texcoord*backNumberUV.xy+backNumberUV.zw;if(b.x>=0.0&&b.x<=1.0&&b.y>=0.0&&b.y<=1.0){vec4 g=texture2D(numberMap,b);c.rgb=mix(c.rgb,g.rgb,g.a);}}
if(useName){vec2 p=vec2(2.0*(texcoord.x-namePlacement.x),namePlacement.y-texcoord.y);vec2 q=vec2(0.5+atan(p.x,p.y)*0.5/namePlacement.w,1.0+(namePlacement.z-length(p))*nameScale);if(q.x>=0.0&&q.x<=1.0&&q.y>=0.0&&q.y<=1.0){vec4 g=texture2D(nameMap,q);c.rgb=mix(c.rgb,g.rgb,g.a);}}
if(c.a<0.01)discard;gl_FragColor=c;}'''
        if not(self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex,vertex) and self.program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment,fragment) and self.program.link()):self.error=self.program.log();return
        self.buffer=QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer);self.buffer.create();self.dirty=True
        self.context().aboutToBeDestroyed.connect(self.cleanup)
    def cleanup(self):
        self.makeCurrent()
        for texture in self.textures.values():texture.destroy()
        self.textures={}
        if self.buffer:self.buffer.destroy()
        self.doneCurrent()
    def paintGL(self):
        gl=self.gl;gl.glClearColor(.055,.065,.085,1.);gl.glClear(0x4000|0x100)
        if not self.program or not self.program.isLinked() or not self.vertices:return
        if self.dirty:
            self.buffer.bind();data=array('f',(x for v in self.vertices for x in v)).tobytes();self.buffer.allocate(data,len(data));self.buffer.release()
            for texture in self.textures.values():texture.destroy()
            self.textures={}
            for key,image in self.images.items():
                rgba=image.convert('RGBA');raw=rgba.tobytes();q=QImage(raw,rgba.width,rgba.height,rgba.width*4,QImage.Format.Format_RGBA8888).copy()
                texture=QOpenGLTexture(q);texture.setMinificationFilter(QOpenGLTexture.Filter.Linear);texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear);self.textures[key]=texture
            self.dirty=False
        gl.glEnable(0xB71);gl.glDepthFunc(0x203);gl.glDisable(0xB44);gl.glEnable(0xBE2);gl.glBlendFunc(0x302,0x303)
        gl.glPolygonMode(0x408,0x1B01 if self.wireframe else 0x1B02)
        projection=QMatrix4x4();projection.perspective(45.,max(1,self.width())/max(1,self.height()),self.radius*.001,self.radius*200)
        view=QMatrix4x4();a,p=math.radians(self.yaw),math.radians(self.pitch);direction=QVector3D(math.cos(p)*math.sin(a),math.sin(p),math.cos(p)*math.cos(a))
        view.lookAt(self.center+direction*self.radius*self.distance,self.center,QVector3D(0,1,0));self.program.bind();self.program.setUniformValue('mvp',projection*view);gl.glUniform1i(self.program.uniformLocation('diffuse'),0)
        gl.glUniform1i(self.program.uniformLocation('numberMap'),1);gl.glUniform1i(self.program.uniformLocation('nameMap'),2)
        self.buffer.bind()
        for name,offset,size in [('position',0,3),('uv',12,2),('color',20,4)]:
            loc=self.program.attributeLocation(name);self.program.enableAttributeArray(loc);self.program.setAttributeBuffer(loc,0x1406,offset,size,36)
        for batch in self.batches:
            texture=self.textures.get(batch.get('texture_index'));gl.glUniform1i(self.program.uniformLocation('textured'),int(texture is not None))
            from PySide6.QtGui import QVector4D
            self.program.setUniformValue('materialColor',QVector4D(*batch.get('color',(1.,1.,1.,1.))))
            number=self.textures.get(batch.get('number_texture'));surname=self.textures.get(batch.get('name_texture'));gl.glUniform1i(self.program.uniformLocation('useNumber'),int(number is not None));gl.glUniform1i(self.program.uniformLocation('useName'),int(surname is not None))
            for uniform,key,default in [('numberUV','number_uv',(1.,1.,0.,0.)),('backNumberUV','back_number_uv',(1.,1.,0.,0.)),('namePlacement','name_placement',(0.,0.,1.,1.))]:self.program.setUniformValue(uniform,QVector4D(*batch.get(key,default)))
            gl.glUniform1f(self.program.uniformLocation('nameScale'),float(batch.get('name_scale',1.)))
            if number:number.bind(1)
            if surname:surname.bind(2)
            if texture:texture.bind(0)
            if batch['layer']:gl.glEnable(0x8037);gl.glPolygonOffset(-float(batch['layer']),-float(batch['layer']))
            else:gl.glDisable(0x8037)
            gl.glDrawArrays(4,batch['first'],batch['count'])
            if texture:texture.release(0)
            if number:number.release(1)
            if surname:surname.release(2)
        self.buffer.release();self.program.release();gl.glPolygonMode(0x408,0x1B02)
    def mousePressEvent(self,event):self.last=event.position()
    def mouseMoveEvent(self,event):
        if self.last is None:return
        d=event.position()-self.last;self.last=event.position()
        if event.buttons()&Qt.MouseButton.LeftButton:self.yaw+=d.x()*.4;self.pitch=max(-89.,min(89.,self.pitch+d.y()*.4))
        elif event.buttons()&Qt.MouseButton.RightButton:self.center+=QVector3D(-d.x(),d.y(),0)*self.radius*.002*self.distance
        self.update()
    def wheelEvent(self,event):self.distance=max(.01,min(100.,self.distance*math.exp(-event.angleDelta().y()/1200)));self.update()
