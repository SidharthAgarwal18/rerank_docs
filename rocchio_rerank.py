import sys
import os
from bs4 import BeautifulSoup
import re
import csv
import json
import math
from operator import itemgetter
import random

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

def readStringFreq(file_string,dictionary):
	words = re.split(' |,|>|<|=|/|-|0|1|2|3|4|5|6|7|8|9|\\.|\n|:|;|"|\'|`|{{|}}|[|]|\)|\(',file_string)

	for term in words:
		term = term.lower()
		if term not in dictionary:
			dictionary[term] = 1
		else:
			dictionary[term]+=1
	return dictionary

def readCollection(collection_dir,queryDocuments,LIMIT,gamma = 0.15):

	IDFS = {}

	with open(os.path.join(collection_dir,'metadata.csv')) as inputF:

	    reader = csv.DictReader(inputF)
	    limit = LIMIT

	    for row in reader:

	        title = row['title']
	        readStringFreq(title,IDFS)

	        coin = random.random()
	        if (row['cord_uid'] in queryDocuments and coin>0.5):
	        	continue

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
	        #print(limit)
	        if(limit<0):
	        	break

	    irrelevantDocs = {}
	    for term in IDFS.keys():
	    	irrelevantDocs[term] = (-1)*gamma*IDFS[term]/LIMIT

	    totalN = 0
	    for freq in IDFS.values():
	    	totalN += freq
	    for key in IDFS.keys():
	    	IDFS[key] = math.log((1+(totalN/IDFS[key])),2)

	    return IDFS,totalN,irrelevantDocs

def fillTFS(queryDocuments,collection_dir):
	documentTFS = {}

	with open(os.path.join(collection_dir,'metadata.csv')) as inputF:
	    reader = csv.DictReader(inputF)

	    for row in reader:
	    	if row['cord_uid'] in queryDocuments:

	    		if row['cord_uid'] not in documentTFS.keys():
	    			documentTFS[row['cord_uid']] = {}

	    		title = row['title']
	    		readStringFreq(title,documentTFS[row['cord_uid']])

	    		abstract = row['abstract']
	    		readStringFreq(abstract,documentTFS[row['cord_uid']])

	    		authors = row['authors'].split('; ')
	    		for author in authors:
	    			readStringFreq(author,documentTFS[row['cord_uid']])

	    		if row['pmc_json_files']:
	    		    for json_path in row['pmc_json_files'].split('; '):
	    		        with open(os.path.join(collection_dir,json_path)) as f_json:
	    		            full_text_dict = json.load(f_json)
	    		            
	    		            for paragraph_dict in full_text_dict['body_text']:
	    		                readStringFreq(paragraph_dict['text'],documentTFS[row['cord_uid']])

	    		if row['pdf_json_files']:
	    		    for json_path in row['pdf_json_files'].split('; '):
	    		        with open(os.path.join(collection_dir,json_path)) as f_json:
	    		            full_text_dict = json.load(f_json)
	    		            
	    		            for paragraph_dict in full_text_dict['body_text']:
	    		                readStringFreq(paragraph_dict['text'],documentTFS[row['cord_uid']])
	return documentTFS

def addDictionaries(dict1,dict2,factor1=1,factor2=1):
	newDict = {}

	for key in dict1.keys():
		newDict[key] = dict1[key]*factor1

	for key in dict2.keys():
		if key not in newDict.keys():
			newDict[key] = dict2[key]*factor2
		else:
			newDict[key] += dict2[key]*factor2

	return newDict

def returnScore(TF_document_dictionary,query,otherQuery,alpha,IDFS,totalN):
	score = 0

	for term in query:
		if term not in otherQuery:
			otherQuery[term] = alpha
		else:
			otherQuery[term] += alpha

	norm1 = 0
	norm2 = 0
	for term in otherQuery:
		idf = math.log((1+(totalN)),2) if term not in IDFS.keys() else IDFS[term]
		tf = TF_document_dictionary[term] if term in TF_document_dictionary.keys() else 0
		norm1 += otherQuery[term]*otherQuery[term]
		norm2 += tf*idf*tf*idf
		score += tf*idf*otherQuery[term]

	return score/(math.sqrt(norm1)*math.sqrt(norm2))

def returnOtherVector(query_dictionary,top100_dictionary,documentTFS,irrelevantDocs,beta):
	otherVector = {}

	for queryNum in query_dictionary:
		tempVector = {}
		for document in top100_dictionary[queryNum]:
			tempVector = addDictionaries(tempVector,documentTFS[document],1,beta*(1/100))
		otherVector[queryNum] = addDictionaries(tempVector,irrelevantDocs)
		#print(len(otherVector[queryNum].keys()))

	return otherVector

def reorderQueries(query_dictionary,otherVector,alpha,top100_dictionary,documentTFS,IDFS,totalN,output_filename):

	file = open(output_filename,"w")

	for queryNum in query_dictionary.keys():
		thisOrderedDocs = []
		for document in top100_dictionary[queryNum]:
			thisScore = returnScore(documentTFS[document],query_dictionary[queryNum],otherVector[queryNum],alpha,IDFS,totalN)
			thisOrderedDocs.append([thisScore,document])
		thisOrderedDocs = sorted(thisOrderedDocs,key=itemgetter(0),reverse = True)
		
		for index,scoreId in enumerate(thisOrderedDocs):
			answerLine = str(queryNum) + " Q0 " + scoreId[1] + " " + str(index) + " " +str(scoreId[0]) + " Sidharth\n"
			file.write(answerLine)
	file.close()

if __name__=='__main__':

	LIMIT = 1000

	alpha = 1
	beta = 0.5
	gamma = 0.15

	num_arguments = len(sys.argv)
	query_filename = sys.argv[1]
	top100_filename = sys.argv[2]
	collection_dir = sys.argv[3]
	output_filename = sys.argv[4]

	query_dictionary = readQueryFile(query_filename)
	top100_dictionary = readTop100(top100_filename)
	queryDocuments = []
	for top100 in top100_dictionary.values():
		queryDocuments += top100

	IDFS,totalN,irrelevantDocs = readCollection(collection_dir,queryDocuments,LIMIT,gamma)

	documentTFS = fillTFS(queryDocuments,collection_dir)	

	otherVector_dict = returnOtherVector(query_dictionary,top100_dictionary,documentTFS,irrelevantDocs,beta)

	reorderQueries(query_dictionary,otherVector_dict,alpha,top100_dictionary,documentTFS,IDFS,totalN,output_filename)