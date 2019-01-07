#!BPY

"""
Name: 'MD3 (.md3)'
Blender: 243
Group: 'Import'
Tooltip: 'Import from Quake3 file format. (.md3)'
"""

__author__ = "PhaethonH, Bob Holcomb, Robert (Tr3B) Beckebans, f0rqu3"
__url__ = ("http://tremx.sourceforge.net")
__version__ = "0.7 2007-07-20"

__bpydoc__ = """\
This script imports a Quake 3 file (MD3), textures, 
and animations into Blender for editing. Loader is based on MD3 loader
from www.gametutorials.com-Thanks DigiBen! and the
md3 blender loader by PhaethonH <phaethon@linux.ucla.edu>
Updated by f0rqu3
thanks to Tr3B - xreal.sourceforge.net

Supported:<br>
	Surfaces, Materials, Animations, Tag rotations

Missing:<br>
    None

Known issues:<br>
    None

Notes:<br>
    TODO
"""

import md3
from md3 import *

import md3_shared
from md3_shared import *

log = Logger("md3_import_log")

def Import(fileName):
	#log starts here
	log.start = Blender.sys.time()
	log.info("Starting ...")
	
	log.info("Importing MD3 model: %s", fileName)
	
	pathName = StripGamePath(StripModel(fileName))
	log.info("Shader path name: %s", pathName)
	
	modelName = StripExtension(StripPath(fileName))
	log.info("Model name: %s", modelName)
	
	# read the file in
	file = open(fileName,"rb")
	md3 = md3Object()
	md3.Load(file, log)
	md3.Dump(log)
	file.close()
	
	scene = Blender.Scene.GetCurrent()
	
	for k in xrange(md3.numSurfaces):
	
		surface = md3.surfaces[k]
		
		# create a new mesh
		mesh = Blender.Mesh.New(surface.name)
		
		# mesh has vertex uv :/
		mesh.vertexUV = True
		
		# create the verts
		mesh.verts.extend( [surface.verts[i].xyz for i in xrange(surface.numVerts)] )
		
		#set vertex normal and uv
		for i in xrange(len(mesh.verts)):
			mesh.verts[i].no=Blender.Mathutils.Vector( surface.verts[i].normal )
			mesh.verts[i].uvco=Blender.Mathutils.Vector(surface.uv[i].u, surface.uv[i].v)
		
		# create the faces
		mesh.faces.extend( [surface.triangles[i].indexes for i in xrange(surface.numTriangles)] )
		
		# vertex uv to face uv
		mesh.faceUV=True
		for f in mesh.faces:
			f.uv = [v.uvco for v in f.verts]
			f.smooth=1
		
		# create materials for surface
		for i in xrange(surface.numShaders):
			
			# create new material if necessary
			matName = StripExtension(StripPath(surface.shaders[i].name))
			if matName == "" :
				matName = surface.name + "_mat"
			
			try:
				mat = Blender.Material.Get(matName)
			except NameError:
				log.info("Creating new material: %s", matName)
				mat = Blender.Material.New(matName)
				# create new texture
				texture = Blender.Texture.New(matName)
				texture.setType('Image')
				# try .tga by default
				#imageName = StripExtension(GAMEDIR + surface.shaders[i].name) + '.tga'
				imageName = StripExtension(pathName+matName)
				#print imageName
				try:
					image = Blender.Image.Load(imageName)
					texture.image = image
				except IOError:
					try:
						imageName = StripExtension(imageName) + '.png'
						image = Blender.Image.Load(imageName)
						texture.image = image
					except IOError:
						try:
							imageName = StripExtension(imageName) + '.jpg'
							image = Blender.Image.Load(imageName)
							texture.image = image
						except IOError:
							log.warning("Unable to load image for %s", surface.name)
					
				# texture to material
				mat.setTexture(0, texture, Blender.Texture.TexCo.UV, Blender.Texture.MapTo.COL)
	
			# append material to the mesh's list of materials
			mesh.materials+=[mat]
			#mesh.update()

		# add object
		meshObject= Blender.Object.New('Mesh',surface.name)
		meshObject.link(mesh)
		scene.objects.link(meshObject)
		
		if surface.numFrames > 1 :
			# animate the verts through keyframe animation
			for i in xrange(surface.numFrames):
				
				# update the vertices
				for j in xrange(surface.numVerts):
					xyz=Blender.Mathutils.Vector(surface.verts[(i * surface.numVerts) + j].xyz)
					normal=Blender.Mathutils.Vector(surface.verts[(i * surface.numVerts) + j].normal)
					mesh.verts[j].no = normal
					mesh.verts[j].co = xyz
					
				meshObject.insertShapeKey()

			meshKey = mesh.key
			meshKey.ipo = Blender.Ipo.New('Key', surface.name + "_ipo")
			
			index = 1
			for curveName in meshKey.ipo.curveConsts :
				#print curveName
				meshKey.ipo.addCurve(curveName)
				meshKey.ipo[curveName].interpolation=Blender.IpoCurve.InterpTypes.CONST
				meshKey.ipo[curveName].addBezier((0,0))
				meshKey.ipo[curveName].addBezier((index,1))
				meshKey.ipo[curveName].addBezier((index+1,0))
				index+=1
		
		# select all and remove doubles
		#mesh.sel=1
		#mesh.remDoubles(0.0)
	
	# create tags
	for i in xrange(md3.numTags):
		tag = md3.tags[i]
		# this should be an Empty object
		blenderTag = Blender.Object.New("Empty", tag.name);
		scene.objects.link(blenderTag)
		blenderTag.setLocation(tag.origin)
		
		if md3.numFrames > 1 :
			# set ipo
			ipo = Blender.Ipo.New('Object', tag.name + "_ipo")
			locX = ipo.addCurve('LocX')
			locY = ipo.addCurve('LocY')
			locZ = ipo.addCurve('LocZ')
			rotX = ipo.addCurve('RotX')
			rotY = ipo.addCurve('RotY')
			rotZ = ipo.addCurve('RotZ')
			locX.interpolation=Blender.IpoCurve.InterpTypes.CONST
			locY.interpolation=Blender.IpoCurve.InterpTypes.CONST
			locZ.interpolation=Blender.IpoCurve.InterpTypes.CONST
			rotX.interpolation=Blender.IpoCurve.InterpTypes.CONST
			rotY.interpolation=Blender.IpoCurve.InterpTypes.CONST
			rotZ.interpolation=Blender.IpoCurve.InterpTypes.CONST
			#set ipo for tag
			blenderTag.setIpo(ipo)
			
			for j in xrange(md3.numFrames):
				tag = md3.tags[j * md3.numTags + i]
				
				# Note: Quake3 uses left-hand geometry
				forward = [tag.axis[0], tag.axis[1], tag.axis[2]]
				left = [tag.axis[3], tag.axis[4], tag.axis[5]]
				up = [tag.axis[6], tag.axis[7], tag.axis[8]]
				
				rotation = Blender.Mathutils.Matrix(forward, left, up)
				rot_Euler=rotation.toEuler()
				
				locX.addBezier((j+1,tag.origin[0]))
				locY.addBezier((j+1,tag.origin[1]))
				locZ.addBezier((j+1,tag.origin[2]))
				#blender: 100 degrees -> 10 units in IPO -> BLARGH
				rotX.addBezier((j+1,rot_Euler.x/10))
				rotY.addBezier((j+1,rot_Euler.y/10))
				rotZ.addBezier((j+1,rot_Euler.z/10))


def FileSelectorCallback(fileName):
	Import(fileName)
	
	BlenderGui(log)

Blender.Window.FileSelector(FileSelectorCallback, 'Import Quake3 MD3', Blender.sys.makename(ext='.md3'))