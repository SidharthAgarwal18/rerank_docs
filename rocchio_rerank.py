import sys
import os
from bs4 import BeautifulSoup
import re
import csv
import json
import math

def readTop100(top100_filename):
	file = open(top100_filename,"r")
	top100_dictionary = {}

	file_string = file.read()
	lines = re.split('\n',file_string)

	queryNum = 0
	for line in lines:
		terms = re.split(' ',line)

		if(len(terms)<6):
			continue

		if(terms[3]=='1'):
			queryNum+=1
			top100_dictionary[queryNum] = []

		top100_dictionary[queryNum].append(terms[2])

	return top100_dictionary

def readQueryFile(query_filename):
	file = open(query_filename,"r")
	file_string = file.read()
	file_string = file_string[:(len(file_string)-10)]

	while(file_string[0]!='>'):
		file_string = file_string[1:]
	file_string = file_string[1:]

	topics_list = re.split('</topic>',file_string)

	query_dictionary = {}
	queryNum = 1

	for topic in topics_list:
		if '<' not in topic or '>' not in topic:
			continue
		xmlQuery = BeautifulSoup(topic,'xml')
		field = xmlQuery.find_all('query',limit = 1)[0].get_text()
		query_dictionary[queryNum] = field
		queryNum += 1

	return query_dictionary

def readStringFreq(file_string,IDFS):
	words = re.split(' |,|>|<|=|/|-|0|1|2|3|4|5|6|7|8|9|\\.|\n|:|;|"|\'|`|{{|}}|[|]|\)|\(',file_string)

	for term in words:
		term = term.lower()
		if term not in IDFS:
			IDFS[term] = 1
		else:
			IDFS[term]+=1
	return IDFS

def readCollection(collection_dir,LIMIT=1000):

	IDFS = {}

	with open(os.path.join(collection_dir,'metadata.csv')) as inputF:

	    reader = csv.DictReader(inputF)
	    limit = LIMIT

	    for row in reader:
	    
	        title = row['title']
	        readStringFreq(title,IDFS)

	        abstract = row['abstract']
	        readStringFreq(abstract,IDFS)

	        authors = row['authors'].split('; ')
	        for author in authors:
	        	readStringFreq(author,IDFS)

	        if row['pmc_json_files']:
	            for json_path in row['pmc_json_files'].split('; '):
	                with open(os.path.join(collection_dir,json_path)) as f_json:
	                    full_text_dict = json.load(f_json)
	                    
	                    for paragraph_dict in full_text_dict['body_text']:
	                        readStringFreq(paragraph_dict['text'],IDFS)

	        if row['pdf_json_files']:
	            for json_path in row['pdf_json_files'].split('; '):
	                with open(os.path.join(collection_dir,json_path)) as f_json:
	                    full_text_dict = json.load(f_json)
	                    
	                    for paragraph_dict in full_text_dict['body_text']:
	                        readStringFreq(paragraph_dict['text'],IDFS)
	        limit -= 1
	        print(limit)
	        if(limit<0):
	        	break

	    totalN = 0
	    for freq in IDFS.values():
	    	totalN += freq
	    for key in IDFS.keys():
	    	IDFS[key] = math.log((1+(totalN/IDFS[key])),2)

	    return IDFS

def fillTFS(queryDocuments,collection_dir):
	documentTFS = {}

	with open(os.path.join(collection_dir,'metadata.csv')) as inputF:
	    reader = csv.DictReader(inputF)

	    for row in reader:
	    	if row['cord_uid'] in queryDocuments:

	    		if row['cord_uid'] not in documentTFS.keys():
	    			documentTFS[row['cord_uid']] = {}

	    		title = row['title']
	    		readStringFreq(title,documentTFS)

	    		abstract = row['abstract']
	    		readStringFreq(abstract,documentTFS)

	    		authors = row['authors'].split('; ')
	    		for author in authors:
	    			readStringFreq(author,documentTFS)

	    		if row['pmc_json_files']:
	    		    for json_path in row['pmc_json_files'].split('; '):
	    		        with open(os.path.join(collection_dir,json_path)) as f_json:
	    		            full_text_dict = json.load(f_json)
	    		            
	    		            for paragraph_dict in full_text_dict['body_text']:
	    		                readStringFreq(paragraph_dict['text'],documentTFS)

	    		if row['pdf_json_files']:
	    		    for json_path in row['pdf_json_files'].split('; '):
	    		        with open(os.path.join(collection_dir,json_path)) as f_json:
	    		            full_text_dict = json.load(f_json)
	    		            
	    		            for paragraph_dict in full_text_dict['body_text']:
	    		                readStringFreq(paragraph_dict['text'],documentTFS)

def addDictionaries(dict1,dict2):
	newDict = {}

	for key in dict1.keys():
		newDict[key] = dict1[key]

	for key in dict2.keys():
		if key not in newDict.keys():
			newDict[key] = dict2[key]
		else:
			newDict[key] += dict2[key]

	return newDict



if __name__=='__main__':

	num_arguments = len(sys.argv)
	query_filename = sys.argv[1]
	top100_filename = sys.argv[2]
	collection_dir = sys.argv[3]
	output_filename = sys.argv[4]

	query_dictionary = readQueryFile(query_filename)
	top100_dictionary = readTop100(top100_filename)
	IDFS = readCollection(collection_dir)

	queryDocuments = []
	for top100 in top100_dictionary:
		queryDocuments += top100

	documentTFS = fillTFS(queryDocuments,collection_dir)