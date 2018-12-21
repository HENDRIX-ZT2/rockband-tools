import bpy
import os
from struct import unpack_from, iter_unpack


def create_ob(ob_name, ob_data):
	ob = bpy.data.objects.new(ob_name, ob_data)
	bpy.context.scene.objects.link(ob)
	bpy.context.scene.objects.active = ob
	return ob
	
	
def mesh_from_data(name, verts, faces, wireframe = True):
	me = bpy.data.meshes.new(name)
	me.from_pydata(verts, [], faces)
	me.update()
	ob = create_ob(name, me)
	if wireframe:
		ob.draw_type = 'WIRE'
	return ob, me
	
def create_material(ob, matname, matdir):
	print("MATERIAL:", matname)
	#only create the material if we haven't already created it, then just grab it
	if matname not in bpy.data.materials:
		mat = bpy.data.materials.new(matname)
	else: mat = bpy.data.materials[matname]
	
	filepath = os.path.join(matdir,matname)
	if os.path.exists(filepath):
		with open(filepath, 'rb') as f:
			datastream = f.read()
		
		name_len  = unpack_from(">I", datastream, 105)[0]
		if name_len:
			texture = datastream[109:109+name_len].decode("utf-8")
			print(texture)
			if texture not in bpy.data.textures:
				tex = bpy.data.textures.new(texture, type = 'IMAGE')
				try:
					img = bpy.data.images.load(material.find_recursive(texture))
				except:
					print("Could not find image "+texture+", generating blank image!")
					img = bpy.data.images.new(texture,1,1)
				tex.image = img
			else: tex = bpy.data.textures[texture]
			#now create the slot in the material for the texture
			mtex = mat.texture_slots.add()
			mtex.texture = tex
			mtex.texture_coords = 'UV'
			mtex.use_map_color_diffuse = True
			mtex.use_map_density = True
	#now finally set all the textures we have in the mesh
	me = ob.data
	me.materials.append(mat)
	#reversed so the last is shown
	for mtex in reversed(mat.texture_slots):
		if mtex:
			try:
				uv_i = int(mtex.uv_layer)
				for texface in me.uv_textures[uv_i].data:
					texface.image = mtex.texture.image
			except:
				print("No matching UV layer for Texture!")
	#and for rendering, make sure each poly is assigned to the material
	for f in me.polygons:
		f.material_index = 0
		
def load(operator, context, filepath = ""):
	#big endian
	
	dirname, basename = os.path.split(filepath)
	mat_dir = os.path.join(os.path.dirname(dirname), "Mat")
	
	#when no object exists, or when we are in edit mode when script is run
	try: bpy.ops.object.mode_set(mode='OBJECT')
	except: pass
	print("/nImporting",basename)
	with open(filepath, 'rb') as f:
		datastream = f.read()
	
	a, b  = unpack_from(">II", datastream, 0)
	c  = unpack_from(">I", datastream, 17)[0]
	floats  = unpack_from(">16f", datastream, 21)
	print(floats)
	
	pos = 126
	n1_len  = unpack_from(">I", datastream, pos)[0]
	n1 = datastream[pos+4:pos+4+n1_len]
	pos += 4+ n1_len
	#unread data here
	pos+=25
	mat_name_len  = unpack_from(">I", datastream, pos)[0]
	mat_name = datastream[pos+4:pos+4+mat_name_len].decode("utf-8")
	pos += 4+ mat_name_len
	n3_len  = unpack_from(">I", datastream, pos)[0]
	n3 = datastream[pos+4:pos+4+n3_len]
	pos += 4+ n3_len+1
	print(n1,mat_name,n3)
	d,e, v_num  = unpack_from(">III", datastream, pos)
	pos += 12
	
	print(d,e, v_num)
	# vertlist = list(iter_unpack("3f", datastream[pos : pos+12*v_num]))
	vertlist = []
	uvs =[]
	normals = []
	colors = []
	for x in range(v_num):
		#print(datastream[pos:pos+73])
		
		#1,1,1,1, possibly RGBA?
		uk, x,y,z, n_x,n_y,n_z, r,g,b,a, u,v  = unpack_from(">B 3f 3f 4f 2f", datastream, pos)
		vertlist.append( (x,y,z) )
		normals.append( (n_x,n_y,n_z) )
		colors.append( (r,g,b) )
		uvs.append((u,v))
		#always 0,1,2,3
		d,e,f,g  = unpack_from(">HHHH", datastream, pos+49)
		#not a normal or vertex color, but also spherical in -1 ~ 1 range
		h, i, j, k  = unpack_from(">4f", datastream, pos+57)
		
		pos+=72
	#0 pad byte
	pos+=1
	tri_num  = unpack_from(">I", datastream, pos)[0]
	pos+=4
	trilist = list(iter_unpack(">3H", datastream[pos : pos+6*tri_num]))
	
	
	ob, me = mesh_from_data("test", vertlist, trilist, False)

	me.uv_textures.new("0")
	me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [uvs[l.vertex_index] for l in me.loops] for uv in (pair[0], 1-pair[1])])
	create_material(ob, mat_name, mat_dir)
	
	me.vertex_colors.new("RGB")
	me.vertex_colors[-1].data.foreach_set("color", [c for col in [colors[l.vertex_index] for l in me.loops] for c in col])
	
	me.use_auto_smooth = True
	me.normals_split_custom_set_from_vertices(normals)
load("", "", filepath = "C:/Users/arnfi/Desktop/Mesh/redd51.1.mesh")
load("", "", filepath = "C:/Users/arnfi/Desktop/Mesh/redd51.mesh")