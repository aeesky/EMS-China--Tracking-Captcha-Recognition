import urllib2
import random

for i in range(100,1000):
	# rand = random.random()
	rand = 1
	print "Fetching #%d with rand %f\r" % (i, rand)
	
	f = open(str(i)+"-"+str(rand)+".jpg", "w")
	content = urllib2.urlopen("http://www.ems.com.cn/emsService/ems/rand").read()
	f.write(content)
	f.close()