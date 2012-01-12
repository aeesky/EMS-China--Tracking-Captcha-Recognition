#!/usr/bin/python

import tempfile
import subprocess
import os
import sys

import Image
import ImageOps
import PIL
import ImageEnhance

# from p1 import polarize, clear_noise

"""
Notes:

1. No processing, number rate is 94/99 (almost can be assumed they are all correct)
2. autocontrast -> brighten(2.0) -> grayscale -> invert -> pixel * 15 -> invert  =>  99/99

"""

# input_files = ["1-1.jpg", ]
input_files = filter(lambda name: name.endswith(".jpg"), os.listdir("."))
print input_files

def run_tesseract(path):
	image_path = path
	decaptcha_path = tempfile.mktemp(dir="/tmp/mem/ems/")
	
	command = "tesseract %s %s -psm 7 nobatch digits" % (image_path, decaptcha_path)
	print "Executing " + command
	
	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
	p.communicate()
	
	decaptcha_file = open(decaptcha_path + ".txt", "r")
	decaptcha = decaptcha_file.read().strip()
	decaptcha_file.close()
	
	print "tesseract returned '%s'" % decaptcha
	return decaptcha

def brighten(image, factor):
	enh = ImageEnhance.Brightness(image)
	return enh.enhance(factor)

def contrast(image, factor):
	enh = ImageEnhance.Contrast(image)
	return enh.enhance(factor)

def clear_noise(image, max_color, min_adjacent_dots, replacement):
	pixdata = image.load()
	for y in xrange(1, image.size[1] - 1):
   		for x in xrange(1, image.size[0] - 1):
	   		counter = 0
	   		if pixdata[x - 1,y - 1] < max_color:
		   		counter += 1
	   		if pixdata[x + 1,y - 1] < max_color:
		   		counter += 1
	   		if pixdata[x,y - 1] < max_color:
		   		counter += 1
	   		if pixdata[x - 1,y + 1] < max_color:
		   		counter += 1
	   		if pixdata[x + 1,y + 1] < max_color:
		   		counter += 1
	   		if pixdata[x,y + 1] < max_color:
		   		counter += 1
	   		if pixdata[x - 1,y] < max_color:
		   		counter += 1
	   		if pixdata[x + 1,y] < max_color:
		   		counter += 1
		   	
		   	if not counter > min_adjacent_dots:
			   	pixdata[x, y] = replacement
	return image

def post_process(result):
	result = filter(lambda x: x.isdigit(), result)
	return result

if __name__ == "__main__":
	results = []
	for file in input_files:
		
		# path = file
		im = Image.open(file)
		im = ImageOps.autocontrast(im)
		im = ImageOps.autocontrast(im)
		im = ImageOps.autocontrast(im)
		im = ImageOps.autocontrast(im)
		im = brighten(im, 2.1)
		im = ImageOps.grayscale(im)
		im = ImageOps.invert(im)
		im = im.point(lambda i: 250 if i > 1 else i)
		im = ImageOps.invert(im)
		im = clear_noise(im, 254, 1, 255)
		# im = im.convert("L")
		# im = polarize(im, 250)
		# im = clear_noise(im, 4, 1)
		# im = contrast(im, 2.0)
		path = tempfile.mktemp(dir="/tmp/mem/ems/")+".png"
		
		im.save(path, "png")
		
		result = run_tesseract(path)
		result = post_process(result)
		results.append(result)
		
		try:
			n = int(result)
			if len(result) != 6: raise Exception
		except:
			print "Image<'%s'> = '%s' ? " % (file, result),
			line = sys.stdin.readline()
			if line.strip():	
				im.show()
				line = sys.stdin.readline()
	
	num = 0
	six_digit = 0
	for r in results:
		try:
			n = int(r)
			num += 1
			if len(r) == 6:
				six_digit += 1
		except:
			pass
	print "Number rate %d/%d" % (num, len(results))
	print "6-digit rate %d/%d" % (six_digit, len(results))