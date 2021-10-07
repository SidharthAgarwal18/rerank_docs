import sys
import re
import math
import random

def returnRelevance(relevantRankings_filename):
	queryDocRelevance = {}
	queryNum = 1

	file = open(relevantRankings_filename,"r")
	file_string = file.read()
	lines = re.split('\n',file_string)

	for line in lines:
		terms = re.split(' ',line)
		if(len(terms)<4):
			continue
		queryDocRelevance[(int(terms[0]),terms[2])] = int(terms[3])

	return queryDocRelevance

def returnRanking(output_filename):
	queryResults = {}

	file = open(output_filename,"r")
	file_string = file.read()
	lines = re.split('\n',file_string)

	for line in lines:
		terms = re.split(' ',line)
		if len(terms)<4:
			continue
		if terms[3]=='1':
			queryResults[int(terms[0])] = []
		queryResults[int(terms[0])].append(terms[2])
	return queryResults

def returnDCG(vector):
	score = 0
	rank = 1

	for term in vector:
		factor = math.log(1+rank,2)
		rank += 1
		score += int(pow(2,term)-1)/factor

	return score

def returnRelRankingDCG(queryResults,queryDocRelevance):

	total_score = 0
	countValid = 0

	for queryNum in queryResults.keys():
		ranks = []
		
		for doc in queryResults[queryNum]:

			if (queryNum,doc) not in queryDocRelevance.keys():
				ranks.append(0)
			else:
				ranks.append(queryDocRelevance[(queryNum,doc)])

		#random.shuffle(ranks)
		dcg = returnDCG(ranks)

		ranks = sorted(ranks,reverse = True)
		ndcg = returnDCG(ranks)
		
		if ndcg!=0:
			countValid += 1
			total_score += dcg/ndcg		

	return total_score/countValid

def returnMAPScore(queryResults,queryDocRelevance):

	total_score = 0

	for queryNum in queryResults.keys():

		total_doc_yet = 0
		total_relevant = 0
		this_score = 0
		
		for doc in queryResults[queryNum]:

			total_doc_yet += 1
			if (queryNum,doc) in queryDocRelevance.keys():
				this_relevance = queryDocRelevance[(queryNum,doc)]
				if this_relevance>0:
					total_relevant += 1
					total_score += total_relevant/total_doc_yet

		total_score += this_score/total_doc_yet

	return total_score/len(queryResults.keys())

if __name__=='__main__':
	relevantRankings_filename = "t40-qrels.txt"
	output_filename = sys.argv[1]

	queryDocRelevance = returnRelevance(relevantRankings_filename)
	queryResults = returnRanking(output_filename)

	DCGScore = returnRelRankingDCG(queryResults,queryDocRelevance)
	print("The NDCG Score is : "+ str(DCGScore))

	MAPScore = returnMAPScore(queryResults,queryDocRelevance)
	print("The MAP Score is : "+ str(MAPScore))
