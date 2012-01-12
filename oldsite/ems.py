#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
from PIL import Image

img = Image.open('1.gif')
img = img.convert("RGB")

pixdata = img.load()

for y in xrange(img.size[1]):
    for x in xrange(img.size[0]):
		cpixel = pixdata[x, y]
		bw_value = int(round(sum(cpixel) / float(len(cpixel))))
		if bw_value > 50:
			pixdata[x, y] = (255, 255, 255)

img.save("2.tif", "GIF")


POST /qcgzOutQueryNewAction.do HTTP/1.1
Host: www.ems.com.cn
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/534.52.7 (KHTML, like Gecko) Version/5.1.2 Safari/534.52.7
Content-Length: 126
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Origin: http://www.ems.com.cn
Content-Type: application/x-www-form-urlencoded
Referer: http://www.ems.com.cn/qcgzOutQueryNewAction.do?reqCode=gotoSearch
Accept-Language: en-us
Accept-Encoding: gzip, deflate
Cookie: JSESSIONID=TjZP9KyTyNdSwv4xxmSyvP1xCZJ1Mt1jvstnTfKwhQ71vby2QlDC!-1970652013
Connection: keep-alive

reqCode=browseBASE&myEmsbarCode=1542751394228&mailNum=EP056253765CS&optijiaot.x=15&optijiaot.y=10&AA8F454E0FEA9546D22315D=RLHB
"""

import urllib2
import cookielib
from PIL import ImageFile
import tempfile
import os
import subprocess
import urllib
import string
import sys
from lxml.html import parse
import re
from StringIO import StringIO

def transformCaptchaImage(image):
	img = image.convert("RGB")
	pixdata = img.load()
	
	for y in xrange(img.size[1]):
	    for x in xrange(img.size[0]):
			cpixel = pixdata[x, y]
			bw_value = int(round(sum(cpixel) / float(len(cpixel))))
			if bw_value > 60 :
				pixdata[x, y] = (255, 255, 255)
			
	return img

def findmyEmsbarCode(page):
	myEmsbarCode_pos = page.find("myEmsbarCode")
	if myEmsbarCode_pos == -1:
		print "Failed to locate myEmsbarCode"
		sys.exit(1)
	result = re.search(r"value=\"([0-9]*?)\"", page[myEmsbarCode_pos:myEmsbarCode_pos+50])
	myEmsbarCode = result.group(1)
	print "Found myEmsbarCode = %d" % int(myEmsbarCode)
	return int(myEmsbarCode)

def extractTracking(page):
	root = parse(StringIO(page)).getroot()
	tracking_boundry = root.cssselect("td .border-track-batch")[0]
	brief_result = tracking_boundry.cssselect("td .txt-main")[0].text_content().strip()
	print brief_result
	
	records = []
	record_htmls = tracking_boundry.cssselect("tr[align=center]")
	for record_html in record_htmls:
		columns = record_html.cssselect("td[align=center]")
		if len(columns) != 3:
			print "Unexpected: '%s'" % record_html.tostring(root, pretty_print=True)
			continue
		timestamp = columns[0].text_content().strip()
		location = columns[1].text_content().strip()
		status = columns[2].text_content().strip()
		print "%s\t%s\t%s" % (timestamp, location, status)
		records.append((timestamp, location, status))
	
	return records

def main():
	track_code = "EP056253765CS"
	if len(sys.argv) == 2: track_code = sys.argv[1]
	# track_code = "TX000543523US"
	
	cj = cookielib.LWPCookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)
	
	request_page = urllib2.urlopen('http://www.ems.com.cn/qcgzOutQueryNewAction.do?reqCode=gotoSearch').read()
	
	captcha_image = urllib2.urlopen('http://www.ems.com.cn/servlet/ImageCaptchaServlet').read()
	parser = ImageFile.Parser()
	parser.feed(captcha_image)
	image = parser.close()
		
	image_path = tempfile.mktemp()
	transformCaptchaImage(image).save(image_path, "tiff")
	
	decaptcha_path = tempfile.mktemp()
	print "Executing \"tesseract %s %s\"" % (image_path, decaptcha_path)
	p = subprocess.Popen("tesseract %s %s" % (image_path, decaptcha_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
	p.communicate()
	decaptcha_file = open(decaptcha_path + ".txt", "r")
	decaptcha = decaptcha_file.read().strip()
	decaptcha_file.close()
	
	print "Found captcha %s" % decaptcha
	decaptcha = string.replace(decaptcha, " ", "")
	decaptcha = string.replace(decaptcha, "?", "P")
	decaptcha = string.replace(decaptcha, "\/", "V")
	decaptcha = string.replace(decaptcha, "/", "I")
	decaptcha = string.replace(decaptcha, "\\", "I")
	decaptcha = string.replace(decaptcha, "1", "I")
	decaptcha = string.replace(decaptcha, "0", "O")
	decaptcha = string.replace(decaptcha, "5", "S")
	print "Processed captcha %s" % decaptcha
	if len(decaptcha) != 4: 
		print "Captcha length mismatches! "
		os.system("open " + image_path)
		sys.exit(1)
	
	form = {
		"reqCode" : "browseBASE",
		"myEmsbarCode" : findmyEmsbarCode(request_page),
		"mailNum" : track_code,
		"optijiaot.x" : "15",
		"optijiaot.y" : "10",
		"AA8F454E0FEA9546D22315D" : decaptcha,
	}
	print form
	
	request = urllib2.Request("http://www.ems.com.cn/qcgzOutQueryNewAction.do", urllib.urlencode(form))
	track_page = urllib2.urlopen(request).read()
	extractTracking(track_page)
	
	# try:
	#  		extractTracking(track_page)
	# except: 
	# 	os.system("open " + image_path)
	
main()