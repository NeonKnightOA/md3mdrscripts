#!BPY

"""
Name: 'MD3 (.md3)'
Blender: 243
Group: 'Export'
Tooltip: 'Export to Quake3 file format. (.md3)'
"""

__author__ = "PhaethonH, Bob Holcomb, Damien McGinnes, Robert (Tr3B) Beckebans, f0rqu3"
__url__ = ("http://tremx.sourceforge.net")
__version__ = "0.7 2007-07-20"

__bpydoc__ = """\
This script exports a Quake3 file (MD3).
Updated by f0rqu3
thanks to Tr3B - xreal.sourceforge.net

Supported:<br>
    Surfaces, Materials and Tags.

Missing:<br>
    None.

Known issues:<br>
    None.

Notes:<br>
    TODO
"""

import Blender

import BPyMesh

import md3
from md3 import *

import md3_shared
from md3_shared import *

log = Logger("md3_export_log")

def ApplyTransform(vert, matrix):
	return vert * matrix


def UpdateFrameBounds(v, f):
	for i in xrange(3):
		f.mins[i] = min(v[i], f.mins[i])
	for i in xrange(3):
		f.maxs[i] = max(v[i], f.maxs[i])


def UpdateFrameRadius(f):
	f.radius = RadiusFromBounds(f.mins, f.maxs)


def ProcessSurface(scene, blenderObject, md3, pathName, modelName):
	# because md3 doesnt suppoort faceUVs like blender, we need to duplicate
	# any vertex that has multiple uv coords

	vertDict = {}
	indexDict = {} # maps a vertex index to the revised index after duplicating to account for uv
	vertList = [] # list of vertices ordered by revised index
	numVerts = 0
	uvList = [] # list of tex coords ordered by revised index
	faceList = [] # list of faces (they index into vertList)
	numFaces = 0

	scene.makeCurrent()
	Blender.Set("curframe", 1)
	Blender.Window.Redraw()

	# get the object (not just name) and the Mesh, not NMesh
	mesh = Blender.Mesh.New()
	mesh.getFromObject(blenderObject)
	matrix = blenderObject.getMatrix('worldspace')

	surf = md3Surface()
	surf.numFrames = md3.numFrames
	surf.name = blenderObject.getName()
	surf.ident = MD3_IDENT
	
	# create shader for surface
	surf.shaders.append(md3Shader())
	surf.numShaders += 1
	surf.shaders[0].index = 0
	
	log.info("Materials: %s", mesh.materials)
	# :P
	if not mesh.materials:
		surf.shaders[0].name = pathName + blenderObject.name
	else:
		surf.shaders[0].name = pathName + mesh.materials[0].name

	# process each face in the mesh
	for face in mesh.faces:
		if mesh.faceUV == True:
			face_uv = face.uv
		tris_in_this_face = []  #to handle quads and up...
		
		# this makes a list of indices for each tri in this face. a quad will be [[0,1,1],[0,2,3]]
		for vi in xrange(1, len(face)-1):
			tris_in_this_face.append([0, vi, vi + 1])
		
		# loop across each tri in the face, then each vertex in the tri
		for this_tri in tris_in_this_face:
			numFaces += 1
			tri = md3Triangle()
			tri_ind = 0
			for i in this_tri:
				# get the vertex index, coords and uv coords
				index = face.v[i].index
				v = face.v[i].co
				if mesh.faceUV == True:
					uv = tuple(face_uv[i])
				elif mesh.vertexUV:
					uv = (face.v[i].uvco[0], face.v[i].uvco[1])
				else:
					uv = (0.0, 0.0) # handle case with no tex coords	

				
				if vertDict.has_key((index, uv)):
					# if we've seen this exact vertex before, simply add it
					# to the tris list of vertex indices
					tri.indexes[tri_ind] = vertDict[(index, uv)]
				else:
					# havent seen this tri before 
					# (or its uv coord is different, so we need to duplicate it)
					
					vertDict[(index, uv)] = numVerts
					
					# put the uv coord into the list
					# (uv coord are directly related to each vertex)
					tex = md3TexCoord()
					tex.u = uv[0]
					tex.v = uv[1]
					uvList.append(tex)

					tri.indexes[tri_ind] = numVerts

					# now because we have created a new index, 
					# we need a way to link it to the index that
					# blender returns for NMVert.index
					if indexDict.has_key(index):
						# already there - each of the entries against 
						# this key represents  the same vertex with a
						# different uv value
						ilist = indexDict[index]
						ilist.append(numVerts)
						indexDict[index] = ilist
					else:
						# this is a new one
						indexDict[index] = [numVerts]

					numVerts += 1
				tri_ind +=1
			faceList.append(tri)

	# we're done with faces and uv coords
	surf.uv.extend(uvList)

	surf.triangles.extend(faceList)

	surf.numTriangles = len(faceList)
	surf.numVerts = numVerts

	# now vertices are stored as frames -
	# all vertices for frame 1, all vertices for frame 2...., all vertices for frame n
	# so we need to iterate across blender's frames, and copy out each vertex
	for	frameNum in xrange(1, md3.numFrames + 1):
		Blender.Set("curframe", frameNum)
		Blender.Window.Redraw()

		m = Blender.Mesh.New()
		m.getFromObject(blenderObject)
		old_verts = m.verts[:] #backup vertices
		m.transform(matrix, recalc_normals=True)

		vlist = [0] * numVerts
		for vertex in m.verts:
			try:
				vindices = indexDict[vertex.index]
			except:
				log.warning("Found a vertex in %s that is not part of a face", blenderObject.name)
				continue

			vTx = vertex.co
			nTx = vertex.no
			UpdateFrameBounds(vTx, md3.frames[frameNum - 1])
			vert = md3Vert()
			#vert.xyz = vertex.co[0:3]
			#vert.normal = vert.Encode(vertex.no[0:3])
			vert.xyz = vTx[0:3]
			vert.normal = nTx[0:3]
			for ind in vindices:  # apply the position to all the duplicated vertices
				vlist[ind] = vert

		UpdateFrameRadius(md3.frames[frameNum - 1])

		surf.verts.extend(vlist)
		m.verts = old_verts  #restore vertices

	surf.Dump(log)
	md3.surfaces.append(surf)
	md3.numSurfaces += 1


def Export(fileName):
	if(fileName.find('.md3', -4) <= 0):
		fileName += '.md3'
	
	pathName = StripGamePath(StripModel(fileName))
	
	# ask for a new shader path
	text = Blender.Draw.Create(pathName)
	block = [ ("",text , 0, MAX_QPATH, "Ex: models/players/human_base/") ]
	retval = Blender.Draw.PupBlock("Shader Path :", block)
	#changed
	if retval: pathName = text.val
	
	#log starts here
	log.start = Blender.sys.time()
	log.info("Starting ...")
	
	log.info("Exporting MD3 format to: %s", fileName)
	
	log.info("Shader path name: %s", pathName)
	
	modelName = StripExtension(StripPath(fileName))
	log.info("Model name: %s", modelName)
	
	md3 = md3Object()
	md3.ident = MD3_IDENT
	md3.version = MD3_VERSION

	tagList = []
	
	# get the scene
	scene = Blender.Scene.GetCurrent()
	context = scene.getRenderingContext()

	scene.makeCurrent()
	md3.numFrames = Blender.Get("curframe")
	Blender.Set("curframe", 1)

	# create a bunch of blank frames, they'll be filled in by 'ProcessSurface'
	for i in xrange(1, md3.numFrames + 1):
		frame = md3Frame()
		frame.name = "frame_" + str(i)
		md3.frames.append(frame)

	# export all selected objects
	objlist = Blender.Object.GetSelected()

	# process each object for the export
	for obj in objlist:
		# check if it's a mesh object
		if obj.getType() == "Mesh":
			log.info("Processing surface: %s", obj.name)
			if len(md3.surfaces) == MD3_MAX_SURFACES:
				log.warning("Hit md3 limit (%i) for number of surfaces, skipping ...", MD3_MAX_SURFACES, obj.getName())
			else:
				ProcessSurface(scene, obj, md3, pathName, modelName)
		elif obj.getType() == "Empty":   # for tags, we just put em in a list so we can process them all together
			if obj.name[0:4] == "tag_":
				log.info("Processing tag: %s", obj.name)
				tagList.append(obj)
				md3.numTags += 1
		else:
			log.info("Skipping object: %s", obj.name)

	
	# work out the transforms for the tags for each frame of the export
	for i in xrange(1, md3.numFrames + 1):
		
		# needed to update IPO's value, but probably not the best way for that...
		scene.makeCurrent()
		Blender.Set("curframe", i)
		Blender.Window.Redraw()
		for tag in tagList:
			t = md3Tag()
			matrix = tag.getMatrix('worldspace')
			t.origin[0] = matrix[3][0]
			t.origin[1] = matrix[3][1]
			t.origin[2] = matrix[3][2]
				
			t.axis[0] = matrix[0][0]
			t.axis[1] = matrix[0][1]
			t.axis[2] = matrix[0][2]
				
			t.axis[3] = matrix[1][0]
			t.axis[4] = matrix[1][1]
			t.axis[5] = matrix[1][2]
				
			t.axis[6] = matrix[2][0]
			t.axis[7] = matrix[2][1]
			t.axis[8] = matrix[2][2]
			t.name = tag.name
			#t.Dump(log)
			md3.tags.append(t)

	# export!
	file = open(fileName, "wb")
	md3.Save(file)
	file.close()
	md3.Dump(log)

def FileSelectorCallback(fileName):
	Export(fileName)
	
	BlenderGui(log)

Blender.Window.FileSelector(FileSelectorCallback, "Export Quake3 MD3", Blender.sys.makename(ext='.md3'))