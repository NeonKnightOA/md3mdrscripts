# Blender MD3-MDR import/export scripts repository
A repository housing many MD3/MDR import/export scripts for different versions of Blender.

#Sources
* [Blender 2.7 MD3 Export Script @ Duke4.net](https://forums.duke4.net/topic/5358-blender-27-md3-export-script/)
* [Blender md3 import-export tool @ ModDB.com](https://www.moddb.com/games/quake-iii-arena/downloads/blender-md3-import-export-tool)
* [MD3 support for Blender (Repository) @ github\.com/neumond](https://github.com/neumond/blender-md3)

# Other links of interest
* [Description of MD3 format](http://www.icculus.org/homepages/phaethon/q3a/formats/md3format.html)
* [Elite Force MDR format](http://forums.ubergames.net/topic/2299-elite-force-mdr-format/)
* [Dev:Py/Scripts @ BlenderWiki](https://en.blender.org/index.php/Dev:Py/Scripts)

# To-Do
* Create Blender Python scripts for MDR import/export with full feature support, such as compression, tags, and LODs.
  * LOD selection export: LOD meshes shifted into different layers for organization, and object names given an _1 _2 respectively, having the exporter to also select those (if available) and export the selected object/armature along with the LOD mesh objects.
  * Unlike IQM, MDR is weighted bones on a skeleton without hierarchy and rather compressed bone data intended for loads of frames. It also has the ability to have internal LOD meshes in the same file.
* Create proper md3 exporters for later versions
  * They are known for having bounding box and normals issues. The bounding box is important since it's used for the renderer to occlude, and has a habit of doing a smallest bbox. For example, when making a little flare sprite surface on a railgun, when the flare is unseen, the whole gun is unseen. It's also almost impossible to make autosprites2 in them.
  
