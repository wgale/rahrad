from __future__ import division
import pickle
import csv
import re
from nltk.corpus import stopwords
from nltk import stem
import nltk
import gensim
import xml.etree.ElementTree as ET

# global variables, loaded during first call to text preprocessing
# set of stop words
stop = set()
# specialist dictionary
medical = dict()

# runs the preprocessing procedure to the supplied text
# input is string of text to be processed
# output is the same string processed
# set minimal to true for minimal text preprocessing
def textPreprocess(text,minimal=False):
	#load set of stop words
	global stop
	if not stop:
		negations = set(('no', 'nor','against','don', 'not'))
		stop = set(stopwords.words("english")) - negations
	#load dictionary of specialist lexicon
	global medical
	if not medical:
		file = open('../dictionary_files/medical.pkl', 'r')
		medical = pickle.load(file)
		file.close()

	if not minimal:
		text = re.sub("[^a-zA-Z\-]"," ",text) # remove non-letters, except for hyphens
		text = text.lower() # convert to lower-case
		text = text.split() # tokenise string
		text = [word for word in text if len(word) > 1] # remove all single-letter words
		# remove stop words
		text = [word for word in text if not word in stop]
	else:
		# Alterative Minimal processing, lowercase and keep punctuation
		text = text.lower()
		# Split on non alphanumeric and non hyphen characters and keep delimiter
		text = re.split("([^\w\-]+)||\b", text)
		# Delete whitespace tokens
		text = [word.replace(' ','') for word in text]
		text = filter(None, text)

	#look up variable length sequences of words in medical dictionary, stem them if not present
	numTokens = 5 #phrases up to 5 words long
	while numTokens > 0:
		processedText=[]
		start=0
		#Check each phrase of n tokens while there are sufficient tokens after
		while start < (len(text) - numTokens):
			phrase=text[start]
			nextToken=1
			while nextToken < numTokens:
				#add the next tokens to the current one
				phrase = phrase+" "+text[start+nextToken]
				nextToken += 1
			if phrase in medical:
				#convert tokens to one token from specialist
				processedText.append(medical[phrase])
				# skip the next tokens
				start += (numTokens)
			elif numTokens == 1:
				#individual tokens, stem them if not in specialist and keep
				processedText.append(stem.snowball.EnglishStemmer().stem(phrase))
				start += 1
			else:
				#token not part of phrase, keep
				processedText.append(text[start])
				start += 1
		#Keep remaining tokens without enough tokens after them
		while start < len(text):
			processedText.append(text[start])
			start += 1
		text = processedText
		numTokens -= 1

	# word stemming (list of word stemmers: http://www.nltk.org/api/nltk.stem.html)
	# text = [stem.snowball.EnglishStemmer().stem(word) for word in text]
	# text = [stem.PorterStemmer().stem(word) for word in text]

	return(text)

# retrieves all fields of all cases, including raw report amongst other fields
# input must be an ARRAY of fileNames. By default, fetches from all case in directory.
# output is a multi-dimensional array containing this data
def getData(fileNames):
	data = []

	for fileName in fileNames:
		with open(fileName,'rb') as file:
			file.readline() # skip header line
			reader = csv.reader(file)
			for row in reader:
				data.append(row)

	return data

# retrieves a list of all reports in its raw unprocessed state
# input must be an ARRAY of fileNames. By default, fetches all reports in directory.
# output is an array containing the reports
def getReports(fileType):
	reports = []
	fileName = "Cleaned" + fileType + "Full.csv"

	with open(fileName,'rb') as file:
		file.readline() # skip header line
		reader = csv.reader(file)
		for row in reader:
			reports.append(row[1])

	return reports

# retrieves all reports that have been preprocessed corresponding to the given diagnoses
# input must be an ARRAY of string specifying the diagnoses to fetched. By default, fetches all reports from all diagnoses.
# output is an array containing the processed reports
def getProcessedReports(fileType):
	reports = []

	file = open('../model_files/reports_list_' + fileType, 'r')
	reports = reports + pickle.load(file)
	file.close()

	return reports

# determine the total number of case reports in the given files
# input must be an array of fileNames. By default, fetches the total number of case reports in the directory.
# output is the sum of number of case reports
def getNumReports(fileNames):
	data = getData(fileNames)
	return len(data)

# fetches the raw reports, preprocesses them, then saves them as report files
# input must be an array of fileNames to preprocess. By default, preprocesses all reports in directory.
def preprocessReports(fileType): 

	reports = getReports(fileType)
	#reports = getSentences([fileNames[j]])
	print("report loading finished")
	print "preprocessing reports..."

	j = 10

	for i in xrange(len(reports)):
		if (i / len(reports) * 100) > j and j < 100:
			print str(j) + "%... "
			j = j + 10
		reports[i] = textPreprocess(reports[i])
	print("preprocessing finished")

	file = open('../model_files/reports_list_' + fileType, 'w')
	pickle.dump(reports, file)
	file.close()

	print("reports saved")

# runs the processing procedure on the supplied SPECIALIST and radlex lexicon xml files
# maps all the phrases in the specialist and radlex lexicons to their bases
# input is LEXICON.xml and radlex_xml.xml in dictionary_files folder
# output is a dictionary stored in ./dictionary_files/medical.pkl
def buildMedDict():
	medDict = dict()
	dictTree = ET.parse('dictionary_files/radlex_xml_synonyms.xml')
	root = dictTree.getroot()
	print("Loaded radlex")
	for lexRecord in root.findall('lexRecord'):
		mapping = lexRecord.find('base').text.lower()
		for word in lexRecord.findall('inflVars'):
			medDict[word.text.lower()] = mapping
	print("Added radlex")

	dictTree = ET.parse('dictionary_files/LEXICON.xml')
	root = dictTree.getroot()
	print("Loaded SPECIALIST")
	for lexRecord in root.findall('lexRecord'):
		mapping = lexRecord.find('base').text.lower()
		for word in lexRecord.findall('inflVars'):
			medDict[word.text.lower()] = mapping
		for word in lexRecord.findall('acronyms'):
			medDict[word.text.lower()] = mapping
	print("Added Specialist")
	file = open('./dictionary_files/medical.pkl', 'w')
	pickle.dump(medDict, file)
	file.close()
	print("done")
	print(medDict["aneurysm of ascending aorta"])

# get all the derivations of each word in the search term, and generates a new search term based on these derivations (only if they exist in the dictionary)
# input is the search term to use
# output is a new search term that contains all of the derivations
def getDerivations(searchTerm):
	dictionary = gensim.corpora.Dictionary.load('../model_files/reports.dict')
	newSearchTerm = []
	for word in searchTerm:
		for i in range(len(word)):
			if i == 0:
				if word in dictionary.values():
					newSearchTerm.append(word)
			else:
				if word[:-i] in dictionary.values():
					newSearchTerm.append(word[:-i])
	return newSearchTerm
