import re
import shutil
import os
import json
import base64
import os.path as path
import sys
from urlparse import urlparse


def har_parser(filename=None):
	if not path.exists("./parsed-objects/"):
		os.mkdir("./parsed-objects/")
	if not path.exists("./parsed-requests/"):
		os.mkdir("./parsed-requests/")
	requests={}
	objects={}
	for r,sub,files in os.walk(filename):
		for f in files:
			# parsed requests
			for entry in json.load(open(r+"/"+f))["log"]["entries"]:
				hostname="none"
				#this is use for get hostname
				for header in entry["request"]["headers"]:
					if header["name"]=="Host":
						hostname=header["value"]
				#set up request_add
				request_add ={
					"URLs":entry["request"]["url"],
					"HTTP_status_codes":entry["response"]["status"],
					"content_types":entry["response"]["content"]["mimeType"],
					"content_size":entry["response"]["bodySize"],
					"host_name":hostname
				}
	
				requests.setdefault(hostname,[]).append(request_add)
				r_path= str(urlparse(entry["request"]["url"]).path)
				#parse if it is html png or svg
				if r_path.endswith(".html") or r_path.endswith(".png") or r_path.endswith(".svg"):
					objects.setdefault(hostname,[]).append({"path":r_path.split("/")[-1],"data":base64.b64decode(entry["response"]["content"]["text"])})
	#save json file requests
	for key,value in requests.iteritems():
		with open("./parsed-requests/"+key, "w+") as jsonfile:
            		jsonfile.write(json.dumps(value))
	#save json file objectss
	for key,value in objects.iteritems():
		if not path.exists("./parsed-objects/"+key):
			os.makedirs("./parsed-objects/"+key)
		for v in value:
			with open("./parsed-objects/"+key+"/"+v["path"], "w+") as jsonfile_2:
            			jsonfile_2.write(v["data"])

if __name__ == "__main__":
    # Make sure that the gecko drivers are in PATH.
    os.environ["PATH"] = "./:" + os.environ["PATH"]

har_parser(sys.argv[1])
   
