import os
import zlib
from struct import iter_unpack, calcsize, unpack_from
import numpy as np
	
def read_milo(name):
	print("Reading",name)
	with open(name, 'rb') as f:
		datastream = f.read()
		pos = 4
		zlib_start, num_parts, len_uncompressed = unpack_from('=III', datastream, 4)
		len_compressed = unpack_from('='+num_parts*"I", datastream, 16)
		print(len_compressed)
		pos = zlib_start
		outs = []
		for le in len_compressed:
			#using "deflate" compression
			#https://stackoverflow.com/questions/1838699/how-can-i-decompress-a-gzip-stream-with-zlib
			outp =	zlib.decompress(datastream[pos:pos+le], wbits = -zlib.MAX_WBITS)
			if outp:
				with open(str(le)+".hex", 'wb') as out:
					out.write(outp)
				outs.append(outp)
			pos+=le
		output_joined = b"".join(outs)
		decode_part(output_joined)

def read_tex(filename):
	"""encapsulates png_wii files, but with different endianness in header compared to unpacked versions"""
	#http://www.scorehero.com/forum/viewtopic.php?t=20822
			
	with open(filename, 'rb') as f:
		datastream = f.read()
		# try:
		width, height, bpp, path_len = unpack_from('>IIII', datastream, 17)
		fp = datastream[33:33+path_len]
		print(width, height, bpp, path_len, fp)
		pos =33+path_len+9
		unk1, bpp2, num, unk2, width, height, bytes_per_line  = unpack_from('>bbIbHHH', datastream, pos)
		print(unk1, bpp2, num, unk2, width, height, bytes_per_line)
		pos += 13 + 19 #padding
		#start of palette
		if bpp2 == 4:
			pal_size = 16*4
		elif bpp2 == 8:
			pal_size = 256*4
		#RGBA
		pal = list( iter_unpack("4B", datastream[pos:pos+pal_size]) )
		print(pal)
		pos += pal_size
		print(pos)
		pixels = []
		if bpp2 == 4:
			#split into nibbles
			#https://stackoverflow.com/questions/42896154/python-split-byte-into-high-low-nibbles
			for y in range(0, height//2, 4):
				for x in range(0, width, 4):
					for y1 in range(y, y+4):
						for x1 in range(x, x+4):
			# for y in range(height):
				# for i in range(bytes_per_line):
							byte = unpack_from('>B', datastream, pos)[0]
							high, low = byte >> 4, byte & 0x0F
							pixels.append(high)
							pixels.append(low)
							pos+=1
		out = np.zeros((height, width, 4), dtype=np.uint8)
		
		i=0
		for x in range(0, height):
			for y in range(0, width):
				
				r, g, b, a = pal[ pixels[i] ]
				out[x,y] = [r,g,b, a]
				i+=1
		# print(pixels)
		print(pos)
		show_data(out)
		# except:
			# print("error reading",filename)
	#what follows is presumably mipmaps
		
def read_png_wii(filename):
	"""encapsulates png_wii files, but with different endianness in header compared to unpacked versions"""
	#http://www.scorehero.com/forum/viewtopic.php?t=20822
			
	with open(filename, 'rb') as f:
		datastream = f.read()
		TextureHeaderOffset, TexturePaletteHeaderOffset, TexturePaletteOffset = unpack_from('<3I', datastream, 16)
		print("TextureHeaderOffset",TextureHeaderOffset)
		print("TexturePaletteHeaderOffset",TexturePaletteHeaderOffset)
		print("TexturePaletteOffset",TexturePaletteOffset)
		#TextureCount, TextureWidth, TextureHeight, TextureFormat
		# height, width, bpp, path_len = unpack_from('>IIII', datastream, 17)
		# height, width, bpp, path_len = unpack_from('>IIII', datastream, 17)
		TextureFormat = unpack_from('>I', datastream, 3)[0]
		TextureHeight, TextureWidth, LineSize = unpack_from('<HHI', datastream, 7)
		print("TextureFormat",TextureFormat)
		print("TextureHeight",TextureHeight)
		print("TextureWidth",TextureWidth)
		print("LineSize",LineSize)
		if TextureFormat == 3:
			print("IA8")
			
			# var offset = GetTextureOffset(tpl);
			offset=0
			output = np.zeros((height, width, 4), dtype=np.uint8)
			# var output = new UInt32[TextureWidth * TextureHeight];
			inp = 0

			for y in range(0, TextureHeight, 4):
				for x in range(0, TextureWidth, 4):
					for y1 in range(y, y+4):
						for x1 in range(x, x+4):
							byte = unpack_from('>B', datastream, inp)[0]
							high, low = byte >> 4, byte & 0x0F
							pixels.append(high)
							pixels.append(low)
							# var pixelbytes = new byte[2];
							# pixelbytes[1] = tpl[offset + inp * 2]
							# pixelbytes[0] = tpl[offset + inp * 2 + 1]
							# var pixel = BitConverter.ToUInt16(pixelbytes, 0);
							inp+=1

							if y1 >= TextureHeight or x1 >= TextureWidth:
								continue

							r = (pixel >> 8) # &0xff
							g = (pixel >> 8) # &0xff
							b = (pixel >> 8) # &0xff
							a = (pixel >> 0) & 0xff

							rgba = (r << 0) | (g << 8) | (b << 16) | (a << 24)
							output[y1 * TextureWidth + x1] = rgba
			np.reshape(output, (height, width, 4) )
			show_data(output)

def show_data(data):
	from matplotlib import pyplot as plt
	plt.imshow(data, interpolation='nearest')
	plt.show()
		
def decode_part(stream):
	"""takes a deflated stream"""
	#big endian
	#maybe version?
	num = unpack_from('>I', stream, 0)[0]
	pos = 4
	directory_extension_len = unpack_from('>I', stream, pos)[0]
	pos+=4
	directory_extension = stream[pos:pos+directory_extension_len]
	pos+=directory_extension_len
	
	directory_len = unpack_from('>I', stream, pos)[0]
	pos+=4
	directory = stream[pos:pos+directory_len]
	pos+=directory_len
	print(directory_extension, directory)
	
	num_entries, len_files, num_files = unpack_from('>III', stream, pos)
	print(num_entries, len_files, num_files)
	pos +=12
	print(pos)
	names = []
	for i in range(num_entries//2):
		ext_len = unpack_from('>I', stream, pos)[0]
		ext = stream[pos+4:pos+4+ext_len]
		pos +=ext_len+4
		name_len = unpack_from('>I', stream, pos)[0]
		name = stream[pos+4:pos+4+name_len]
		pos +=name_len+4
		names.append( os.path.join(ext,name) )
	
	#TODO note: the header block still contains more data after the file table
	
	sep = b"\xAD\xDE\xAD\xDE"
	files = stream.split(sep)
	print("numfiles",len(files))
	print("numnames",len(names))
	print(names)
	#skip the first file (header) and ignore the last one (empty due to split behavior)
	for filename, f in zip(names, files[1:-1]):
		print(filename,len(f))
		dir = os.path.dirname(filename)
		if not os.path.exists( dir ):
			try:
				os.makedirs( dir )
			except OSError as exc: # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise
		with open(filename, 'wb') as out:
			out.write(f)
		if b".tex" in filename.lower():
			read_tex(filename)
# read_milo("emi_redd_mixer.milo_ps2")
# read_png_wii("C:/Users/arnfi/Desktop/RB milos/Tex/redd51.png_wii")
read_milo("bass_lh_hofner63_pick.milo_wii")