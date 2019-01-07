import math
import Blender

#q_shared
GAMEDIR = './'
MAX_QPATH = 64

# strips the slashes from the back of a string
def StripPath(path):
	for c in xrange(len(path), 0, -1):
		if path[c-1] == "/" or path[c-1] == "\\":
			path = path[c:]
			break
	return path
	
# strips the model from path
def StripModel(path):
	for c in xrange(len(path), 0, -1):
		if path[c-1] == "/" or path[c-1] == "\\":
			path = path[:c]
			break
	return path

# strips file type extension
def StripExtension(name):
	if name.find('.') != -1:
		name = name[:name.find('.')]
	return name
	
# strips gamedir
def StripGamePath(name):
	if name[0:len(GAMEDIR)] == GAMEDIR:
		name = name[len(GAMEDIR):len(name)]
	return name

#q_math
def VectorLength(v):
	return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

def RadiusFromBounds(mins, maxs):
	corner = [0, 0, 0]
	a = 0
	b = 0
	
	for i in range(0, 3):
		a = abs(mins[i])
		b = abs(maxs[i])
		if a > b:
			corner[i] = a
		else:
			corner[i] = b

	return VectorLength(corner)

# our own logger class. it works just the same as a normal logger except
# all info messages get show. 
class Logger:
	def __init__(self, name):
		self.has_warnings = False
		self.has_errors = False
		self.has_critical = False
		self.message = ""
		self.name = name
		self.start = 0
		
		if name not in ( text.getName() for text in Blender.Text.Get() ):
			self.outtext = Blender.Text.New(name)
		else:
			self.outtext = Blender.Text.Get(name)
			self.outtext.clear()
		
		self.outtext.write("\n___START___\n\n")
	
	def log(self, type, msg, *args):
			self.message = type.ljust(10) + ":" + msg % args
			self.outtext.write(self.message+'\n')
			print self.message
	
	def info(self, msg, *args):
		self.log("info", msg, *args)
	
	def warning(self, msg, *args):
		self.log("warning", msg, *args)
		self.has_warnings = True
	
	def error(self, msg, *args):
		self.log("error", msg, *args)
		self.has_errors = True
		
	def critical(self, msg, *args):
		self.log("critical", msg, *args)
		self.has_errors = True
	
class BlenderGui:
	def __init__(self, log):
		text = ["A log has been written to a blender text window.",
			"Change this window type to a text window.", 
			"You will be able to select the file %s." % log.name ]
		
		text+=["Parsed in %i seconds"%(Blender.sys.time() - log.start)]
		
		if log.has_critical:
			text += ["There were critical errors!!!!"]
		elif log.has_errors:
			text += ["There were errors!"]
		elif log.has_warnings:
			text += ["There were warnings"]
		
		text.reverse()
		self.msg = text
		
		Blender.Draw.Register(self.gui, self.event, self.button_event)
		
	def gui(self,):
		quitbutton = Blender.Draw.Button("Exit", 1, 0, 0, 100, 20, "Close Window")
		
		y = 35
		
		for line in self.msg:
			Blender.BGL.glRasterPos2i(10,y)
			Blender.Draw.Text(line)
			y+=15
			
	def event(self,evt, val):
		if evt == Blender.Draw.ESCKEY:
			Blender.Draw.Exit()
			return
	
	def button_event(self,evt):
		if evt == 1:
			Blender.Draw.Exit()
			return
