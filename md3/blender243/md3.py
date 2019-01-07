import struct, math

MAX_QPATH = 64
MD3_IDENT = "IDP3"
MD3_VERSION = 15
MD3_MAX_TAGS = 16
MD3_MAX_SURFACES = 32
MD3_MAX_FRAMES = 1024
MD3_MAX_SHADERS = 256
MD3_MAX_VERTICES = 4096
MD3_MAX_TRIANGLES = 8192
MD3_XYZ_SCALE = (1.0 / 64.0)
MD3_BLENDER_SCALE = (1.0 / 1.0)

def asciiz(s):
	n = 0
	while( n < MAX_QPATH and ord(s[n]) != 0):
		n = n + 1
	return s[0:n]

# copied from PhaethonH <phaethon@linux.ucla.edu> md3.py
def Decode(lng,lat):
	#lat = (latlng >> 8) & 0xFF;
	#lng = (latlng) & 0xFF;
	lat *= 2*math.pi / 255;
	lng *= 2*math.pi / 255;
	x = math.cos(lat) * math.sin(lng)
	y = math.sin(lat) * math.sin(lng)
	z =                 math.cos(lng)
	retval = [ x, y, z ]
	return retval

# copied from PhaethonH <phaethon@linux.ucla.edu> md3.py
def Encode(normal):
	x, y, z = normal
	
	# normalise
	l = math.sqrt((x*x) + (y*y) + (z*z))
	if l == 0:
		return (0,0)
	x = x/l
	y = y/l
	z = z/l
	
	if (x == 0.0) & (y == 0.0) :
		if z > 0.0:
			return (0,0) # lat = 0, long = 0
		else:
			return (128,0) # lat = 0, long = 128
	
	# Encode a normal vector into a 16-bit latitude-longitude value
	#lng = math.acos(z)
	#lat = math.acos(x / math.sin(lng))
	#retval = ((lat & 0xFF) << 8) | (lng & 0xFF)
	lng = math.acos(z) * 255 / (2 * math.pi)
	lat = math.atan2(y, x) * 255 / (2 * math.pi)
	#retval = ((int(lat) & 0xFF) << 8) | (int(lng) & 0xFF)
	return ( int(lng) & 0xFF , int(lat) & 0xFF )

#this class computes normal on load and save
class md3Vert(object):
	__slots__ = 'xyz', 'normal', 'binaryFormat'
	
	binaryFormat = "<3hBB"
	
	def __init__(self):
		self.xyz = [0, 0, 0]
		self.normal = 0
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)
	
	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.xyz[0] = data[0] * MD3_XYZ_SCALE
		self.xyz[1] = data[1] * MD3_XYZ_SCALE
		self.xyz[2] = data[2] * MD3_XYZ_SCALE
		self.normal = Decode( data[3], data[4] )
		return self
		
	def Save(self, file):
		lnglat = Encode(self.normal)
		file.write(struct.pack(self.binaryFormat, \
			self.xyz[0] / MD3_XYZ_SCALE, \
			self.xyz[1] / MD3_XYZ_SCALE, \
			self.xyz[2] / MD3_XYZ_SCALE, \
			lnglat[0], lnglat[1] \
		))
		#print "aaaa" + repr(lnglat)
		#print "Wrote MD3 Vertex: ", data
	
	def Dump(self):
		log.info("MD3 Vertex")
		log.info("X: %s", self.xyz[0])
		log.info("Y: %s", self.xyz[1])
		log.info("Z: %s", self.xyz[2])
		log.info("Normal: %s", self.normal)
		log.info("")
		
class md3TexCoord(object):
	__slots__ = 'u', 'v', 'binaryFormat'
	
	binaryFormat = "<2f"
	
	def __init__(self):
		self.u = 0.0
		self.v = 0.0
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)

	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		# for some reason quake3 texture maps are upside down, flip that
		self.u = data[0]
		self.v = 1.0 - data[1]
		return self

	def Save(self, file):
		file.write(struct.pack(self.binaryFormat, self.u, 1.0-self.v))
		#print "wrote MD3 texture coordinate structure: ", data

	def Dump(self):
		log.info("MD3 Texture Coordinates")
		log.info("U: %s", self.u)
		log.info("V: %s", self.v)
		log.info("")
		

class md3Triangle(object):
	__slots__ = 'indexes', 'binaryFormat'
	
	binaryFormat = "<3i"
	
	def __init__(self):
		self.indexes = [ 0, 0, 0 ]
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)

	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.indexes[0] = data[0]
		self.indexes[1] = data[2] # reverse
		self.indexes[2] = data[1] # reverse
		return self

	def Save(self, file):
		file.write(struct.pack(self.binaryFormat, \
			self.indexes[0], \
			self.indexes[2], \
			self.indexes[1] \
		))
		#print "wrote MD3 face structure: ",data

	def Dump(self, log):
		log.info("MD3 Triangle")
		log.info("Indices: %s", self.indexes)
		log.info("")


class md3Shader(object):
	__slots__ = 'name', 'index', 'binaryFormat'
	
	binaryFormat = "<%dsi" % MAX_QPATH
	
	def __init__(self):
		self.name = ""
		self.index = 0
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)

	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.name = asciiz(data[0])
		self.index = data[1]
		return self

	def Save(self, file):
		file.write(struct.pack(self.binaryFormat, self.name, self.index))
		#print "wrote MD3 shader structure: ",data

	def Dump(self, log):
		log.info("MD3 Shader")
		log.info("Name: %s", self.name)
		log.info("Index: %s", self.index)
		log.info("")


class md3Surface(object):
	__slots__ = \
		'ident', 'name', 'flags', 'numFrames', 'numShaders', 'numVerts', 'numTriangles', \
		'ofsTriangles', 'ofsShaders', 'ofsUV', 'ofsVerts', 'ofsEnd', 'shaders', 'triangles', 'uv', \
		'verts', 'binaryFormat'
	
	binaryFormat = "<4s%ds10i" % MAX_QPATH  # 1 int, name, then 10 ints
	
	def __init__(self):
		self.ident = ""
		self.name = ""
		self.flags = 0
		self.numFrames = 0
		self.numShaders = 0
		self.numVerts = 0
		self.numTriangles = 0
		self.ofsTriangles = 0
		self.ofsShaders = 0
		self.ofsUV = 0
		self.ofsVerts = 0
		self.ofsEnd = 0
		self.shaders = []
		self.triangles = []
		self.uv = []
		self.verts = []
		
	def GetSize(self):
		sz = struct.calcsize(self.binaryFormat)
		self.ofsTriangles = sz
		for t in self.triangles:
			sz += t.GetSize()
		self.ofsShaders = sz
		for s in self.shaders:
			sz += s.GetSize()
		self.ofsUV = sz
		for u in self.uv:
			sz += u.GetSize()
		self.ofsVerts = sz
		for v in self.verts:
			sz += v.GetSize()
		self.ofsEnd = sz
		return self.ofsEnd
		
	def Load(self, file, log):
		# where are we in the file (for calculating real offsets)
		ofsBegin = file.tell()
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.ident = data[0]
		self.name = asciiz(data[1])
		self.flags = data[2]
		self.numFrames = data[3]
		self.numShaders = data[4]
		self.numVerts = data[5]
		self.numTriangles = data[6]
		self.ofsTriangles = data[7]
		self.ofsShaders = data[8]
		self.ofsUV = data[9]
		self.ofsVerts = data[10]
		self.ofsEnd = data[11]
		
		# load the tri info
		file.seek(ofsBegin + self.ofsTriangles, 0)
		for i in xrange(self.numTriangles):
			self.triangles.append(md3Triangle())
			self.triangles[i].Load(file)
			#self.triangles[i].Dump(log)
		
		# load the shader info
		file.seek(ofsBegin + self.ofsShaders, 0)
		for i in xrange(self.numShaders):
			self.shaders.append(md3Shader())
			self.shaders[i].Load(file)
			#self.shaders[i].Dump(log)
			
		# load the uv info
		file.seek(ofsBegin + self.ofsUV, 0)
		for i in xrange(self.numVerts):
			self.uv.append(md3TexCoord())
			self.uv[i].Load(file)
			#self.uv[i].Dump(log)
			
		# load the verts info
		file.seek(ofsBegin + self.ofsVerts, 0)
		for i in xrange(self.numFrames):
			for j in xrange(self.numVerts):
				self.verts.append(md3Vert())
				#i*self.numVerts+j=where in the surface vertex list the vert position for this frame is
				self.verts[(i * self.numVerts) + j].Load(file)
				#self.verts[j].Dump(log)
			
		# go to the end of this structure
		file.seek(ofsBegin+self.ofsEnd, 0)
			
		return self
	
	def Save(self, file):
		self.GetSize()
		file.write(struct.pack(self.binaryFormat, \
			self.ident, \
			self.name, \
			self.flags, \
			self.numFrames, \
			self.numShaders, \
			self.numVerts, \
			self.numTriangles, \
			self.ofsTriangles, \
			self.ofsShaders, \
			self.ofsUV, \
			self.ofsVerts, \
			self.ofsEnd \
		))

		# write the tri data
		for t in self.triangles:
			t.Save(file)

		# save the shader coordinates
		for s in self.shaders:
			s.Save(file)

		# save the uv info
		for u in self.uv:
			u.Save(file)

		# save the verts
		for v in self.verts:
			v.Save(file)

	def Dump(self, log):
		log.info("MD3 Surface")
		log.info("Ident: %s", self.ident)
		log.info("Name: %s", self.name)
		log.info("Flags: %s", self.flags)
		log.info("Number of Frames: %s", self.numFrames)
		log.info("Number of Shaders: %s", self.numShaders)
		log.info("Number of Verts: %s", self.numVerts)
		log.info("Number of Triangles: %s", self.numTriangles)
		log.info("Offset to Triangles: %s", self.ofsTriangles)
		log.info("Offset to Shaders: %s", self.ofsShaders)
		log.info("Offset to UV: %s", self.ofsUV)
		log.info("Offset to Verts: %s", self.ofsVerts)
		log.info("Offset to end: %s", self.ofsEnd)
		log.info("")
		

class md3Tag(object):
	__slots__ = 'name', 'origin', 'axis', 'binaryFormat'
	
	binaryFormat="<%ds3f9f" % MAX_QPATH
	
	def __init__(self):
		self.name = ""
		self.origin = [0, 0, 0]
		self.axis = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)
		
	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.name = asciiz(data[0])
		self.origin[0] = data[1]
		self.origin[1] = data[2]
		self.origin[2] = data[3]
		self.axis[0] = data[4]
		self.axis[1] = data[5]
		self.axis[2] = data[6]
		self.axis[3] = data[7]
		self.axis[4] = data[8]
		self.axis[5] = data[9]
		self.axis[6] = data[10]
		self.axis[7] = data[11]
		self.axis[8] = data[12]
		return self
		
	def Save(self, file):
		file.write(struct.pack(self.binaryFormat, \
			self.name, \
			float(self.origin[0]), \
			float(self.origin[1]), \
			float(self.origin[2]), \
			float(self.axis[0]), \
			float(self.axis[1]), \
			float(self.axis[2]), \
			float(self.axis[3]), \
			float(self.axis[4]), \
			float(self.axis[5]), \
			float(self.axis[6]), \
			float(self.axis[7]), \
			float(self.axis[8]) \
		))
		#print "wrote MD3 Tag structure: ",data
		
	def Dump(self, log):
		log.info("MD3 Tag")
		log.info("Name: %s", self.name)
		log.info("Origin: %s", self.origin)
		log.info("Axis: %s", self.axis)
		log.info("")
	
class md3Frame(object):
	__slots__ = 'mins', 'maxs', 'localOrigin', 'radius', 'name', 'binaryFormat'
	
	binaryFormat="<3f3f3ff16s"
	
	def __init__(self):
		self.mins = [0, 0, 0]
		self.maxs = [0, 0, 0]
		self.localOrigin = [0, 0, 0]
		self.radius = 0.0
		self.name = ""
		
	def GetSize(self):
		return struct.calcsize(self.binaryFormat)

	def Load(self, file):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)
		self.mins[0] = data[0]
		self.mins[1] = data[1]
		self.mins[2] = data[2]
		self.maxs[0] = data[3]
		self.maxs[1] = data[4]
		self.maxs[2] = data[5]
		self.localOrigin[0] = data[6]
		self.localOrigin[1] = data[7]
		self.localOrigin[2] = data[8]
		self.radius = data[9]
		self.name = asciiz(data[10])
		return self

	def Save(self, file):
		file.write(struct.pack(self.binaryFormat, \
			self.mins[0], \
			self.mins[1], \
			self.mins[2], \
			self.maxs[0], \
			self.maxs[1], \
			self.maxs[2], \
			self.localOrigin[0], \
			self.localOrigin[1], \
			self.localOrigin[2], \
			self.radius, \
			self.name \
		))
		#print "wrote MD3 frame structure: ",data

	def Dump(self, log):
		log.info("MD3 Frame")
		log.info("Min Bounds: %s", self.mins)
		log.info("Max Bounds: %s", self.maxs)
		log.info("Local Origin: %s", self.localOrigin)
		log.info("Radius: %s", self.radius)
		log.info("Name: %s", self.name)
		log.info("")

class md3Object(object):
	__slots__ = \
		'ident', 'version', 'name', 'flags', 'numFrames', 'numTags', 'numSurfaces', 'numSkins', \
		'ofsFrames', 'ofsTags', 'ofsSurfaces', 'ofsEnd', 'frames', 'tags', 'surfaces', 'binaryFormat'
	
	binaryFormat="<4si%ds9i" % MAX_QPATH  # little-endian (<), 17 integers (17i)
	
	def __init__(self):
		self.ident = ""
		self.version = 0
		self.name = ""
		self.flags = 0
		self.numFrames = 0
		self.numTags = 0
		self.numSurfaces = 0
		self.numSkins = 0
		self.ofsFrames = 0
		self.ofsTags = 0
		self.ofsSurfaces = 0
		self.ofsEnd = 0
		self.frames = []
		self.tags = []
		self.surfaces = []

	def GetSize(self):
		self.ofsFrames = struct.calcsize(self.binaryFormat)
		self.ofsTags = self.ofsFrames
		for f in self.frames:
			self.ofsTags += f.GetSize()
		self.ofsSurfaces += self.ofsTags
		for t in self.tags:
			self.ofsSurfaces += t.GetSize()
		self.ofsEnd = self.ofsSurfaces
		for s in self.surfaces:
			self.ofsEnd += s.GetSize()
		return self.ofsEnd

	def Load(self, file, log):
		tmpData = file.read(struct.calcsize(self.binaryFormat))
		data = struct.unpack(self.binaryFormat, tmpData)

		self.ident = data[0]
		self.version = data[1]

		if(self.ident != "IDP3" or self.version != 15):
			log.error("Not a valid MD3 file")
			log.error("Ident: %s", self.ident)
			log.error("Version: %s", self.version)
			Exit()

		self.name = asciiz(data[2])
		self.flags = data[3]
		self.numFrames = data[4]
		self.numTags = data[5]
		self.numSurfaces = data[6]
		self.numSkins = data[7]
		self.ofsFrames = data[8]
		self.ofsTags = data[9]
		self.ofsSurfaces = data[10]
		self.ofsEnd = data[11]

		# load the frame info
		file.seek(self.ofsFrames, 0)
		for i in xrange(self.numFrames):
			self.frames.append(md3Frame())
			self.frames[i].Load(file)
			#self.frames[i].Dump(log)
		
		# load the tags info
		file.seek(self.ofsTags, 0)
		for i in xrange(self.numFrames):
			for j in xrange(self.numTags):
				tag = md3Tag()
				tag.Load(file)
				#tag.Dump(log)
				self.tags.append(tag)
		
		# load the surface info
		file.seek(self.ofsSurfaces, 0)
		for i in xrange(self.numSurfaces):
			self.surfaces.append(md3Surface())
			self.surfaces[i].Load(file, log)
			self.surfaces[i].Dump(log)
		return self

	def Save(self, file):
		self.GetSize()
		file.write(struct.pack(self.binaryFormat, \
			self.ident, \
			self.version, \
			self.name, \
			self.flags, \
			self.numFrames, \
			self.numTags, \
			self.numSurfaces, \
			self.numSkins, \
			self.ofsFrames, \
			self.ofsTags, \
			self.ofsSurfaces, \
			self.ofsEnd \
		))
		
		for f in self.frames:
			f.Save(file)
			
		for t in self.tags:
			t.Save(file)
			
		for s in self.surfaces:
			s.Save(file)

	def Dump(self, log):
		log.info("Header Information")
		log.info("Ident: %s", self.ident)
		log.info("Version: %s", self.version)
		log.info("Name: %s", self.name)
		log.info("Flags: %s", self.flags)
		log.info("Number of Frames: %s",self.numFrames)
		log.info("Number of Tags: %s", self.numTags)
		log.info("Number of Surfaces: %s", self.numSurfaces)
		log.info("Number of Skins: %s", self.numSkins)
		log.info("Offset Frames: %s", self.ofsFrames)
		log.info("Offset Tags: %s", self.ofsTags)
		log.info("Offset Surfaces: %s", self.ofsSurfaces)
		log.info("Offset end: %s", self.ofsEnd)
		log.info("")
