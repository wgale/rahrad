from __future__ import division
import math
import csv
import numpy as np
import matplotlib.pyplot as plt
from sklearn import neighbors, svm
from sklearn.metrics import roc_curve, auc
from sklearn.cross_validation import train_test_split
import gensim
import time
import datetime
import os
import pickle
import search
import preprocess
import rnn

REPORT_FILES = ['nlp_data/CleanedBrainsFull.csv','nlp_data/CleanedCTPAFull.csv','nlp_data/CleanedPlainabFull.csv','nlp_data/CleanedPvabFull.csv']
REPORT_FILES_BRAINS = ['nlp_data/CleanedBrainsFull.csv']
REPORT_FILES_CTPA = ['nlp_data/CleanedCTPAFull.csv']
REPORT_FILES_PLAINAB = ['nlp_data/CleanedPlainabFull.csv']
REPORT_FILES_PVAB = ['nlp_data/CleanedPvabFull.csv']

REPORT_FILES_LABELLED = ['nlp_data/CleanedBrainsLabelled.csv','nlp_data/CleanedCTPALabelled.csv','nlp_data/CleanedPlainabLabelled.csv','nlp_data/CleanedPvabLabelled.csv']
REPORT_FILES_LABELLED_BRAINS = ['nlp_data/CleanedBrainsLabelled.csv']
REPORT_FILES_LABELLED_CTPA = ['nlp_data/CleanedCTPALabelled.csv']
REPORT_FILES_LABELLED_PLAINAB = ['nlp_data/CleanedPlainabLabelled.csv']
REPORT_FILES_LABELLED_PVAB = ['nlp_data/CleanedPvabLabelled.csv']

DIAGNOSES = ['Brains','CTPA','Plainab','Pvab']

# performs cross-validation and generates precision-recall curve
# used to compare the accuracy of the searching mechanism of the four models
# input is a string of a filename containing a list of searchTerms to use in the testing
# saves output to files in the directory "./precision_recall/"
def precisionRecall(testFile):
	models = ["bow","tfidf","lsi","lda","doc2vec","rnn"]
	# Create the output directory
	directory = "precision_recall/" + datetime.datetime.now().strftime('%m_%d_%H_%M') +"/"
	if not os.path.exists(directory):
		os.makedirs(directory)
	tests = []
	with open(testFile,'rb') as file:
		reader = csv.reader(file)
		for row in reader:
			tests.append(row)
	file.close()

	thres = [0.01,0.02,0.03,0.04,0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]

	numReports = [preprocess.getNumReports(REPORT_FILES[:1]), preprocess.getNumReports(REPORT_FILES[:2]), preprocess.getNumReports(REPORT_FILES[:3]),preprocess.getNumReports()]
	numResults = preprocess.getNumReports()
	for searchTerm in tests:
		print(searchTerm)
		plt.figure(searchTerm[0])
		plt.xlabel("Recall")
		plt.ylabel("Precision")
		plt.title(searchTerm[0])
		with open(directory + searchTerm[0] + ".csv",'w') as writeFile:
			writer = csv.writer(writeFile)

			for model in models:
				writer.writerow([model])
				precision = []
				recall = []

				allReports = search.search(model,numResults,searchTerm[0])
				for i in range(len(thres)):
					truePositive = 0
					retrieved = 0 # retreieved = truePositive + falsePositive
					relevant = 0 # relevant = truePositive + falseNegative

					similarReports = [report for report in allReports if report[1] > thres[i]]

					for reportIdx in similarReports:
						if reportIdx[0] < numReports[0]: # prediction: brains
							if (searchTerm[1] == "Brains"): # actual: brains
								truePositive = truePositive + 1
							# print "brains"
						elif reportIdx[0] < numReports[1]:
							if (searchTerm[1] == "CTPA"):
								truePositive = truePositive + 1
							# print "ctpa"
						elif reportIdx[0] < numReports[2]:
							if (searchTerm[1] == "Plainab"):
								truePositive = truePositive + 1
							# print "plainab"
						elif reportIdx[0] < numReports[3]:
							if (searchTerm[1] == "Pvab"):
								truePositive = truePositive + 1
							# print "pvab"
						else:
							print "error"
					retrieved = retrieved + len(similarReports)
					relevant = relevant + preprocess.getNumReports(["nlp_data/Cleaned" + searchTerm[1] + "Full.csv"])

					precision.append((truePositive/retrieved) if retrieved else 0)
					recall.append((truePositive/relevant) if relevant else 0)
					writer.writerow([precision[i-1],recall[i-1]])

				writer.writerow("")

				# plot the data point
				plt.plot(recall,precision,label=model)

		writeFile.close()
		plt.legend(loc='lower right')
		fileName = directory + searchTerm[0]
		plt.savefig(fileName)
	# Shows all graphs after generation, these are also saved to a file
	# plt.show()



# tests the model at classifying reports as either positive or negative based on diagnosis
# uses a MmCorpus file
def labelClassification():
	corpus = gensim.corpora.MmCorpus('./model_files/reports_lsi.mm')
	#convert the corpus to a numpy matrix, take the transpose and convert it to a list
	corpusList = [list(x) for x in zip(*gensim.matutils.corpus2dense(corpus,corpus.num_terms,dtype=np.float64))]
	# corpusList = [list(x) for x in np.asarray(corpus)[:,:,1]]
	reports = preprocess.getReports()

	numFolds = 5 # number of folds for cross validation
	# Create the output directory
	directory = "label_classification/" + datetime.datetime.now().strftime('%m_%d_%H_%M') +"/"
	if not os.path.exists(directory):
		os.makedirs(directory)
	with open(directory+"labelClassification.csv",'w') as writeFile:
		writer = csv.writer(writeFile)
		writer.writerow(["score","output label","expected label","report"])

		for j in range(len(REPORT_FILES_LABELLED)):
			writer.writerow("")
			writer.writerow("")
			writer.writerow([DIAGNOSES[j]])

			# initialise figure and plot
			name = DIAGNOSES[j] + " ROC"
			plt.figure(name)
			plt.xlabel("False Positive")
			plt.ylabel("True Positive")
			plt.title(DIAGNOSES[j] + " ROC")

			# fetch corpus and labels
			labelledCorpus = []
			# print(range(getNumReports(REPORT_FILES[:j]),getNumReports(REPORT_FILES[:j])+getNumReports([REPORT_FILES_LABELLED[j]])))
			# The labeled data is at the start of the data set
			# Get the ids in the corpus of these first labeled examples for each class
			for i in range(preprocess.getNumReports(REPORT_FILES[:j]),preprocess.getNumReports(REPORT_FILES[:j])+preprocess.getNumReports([REPORT_FILES_LABELLED[j]])):
				labelledCorpus.append((corpusList[i]))
			labels = np.asarray(preprocess.getData([REPORT_FILES_LABELLED[j]]))[:,2]
			############### THIS CODE BLOCK REMOVES THE NUMBER OF NEGATIVE LABELS TO EQUALISE THE DISTRIBUTION OF CLASS LABELS. TO BE REMOVED IN FUTURE.
			count = 0
			deletes = []
			for x in range(len(labels)):
				if (labels[x] == "negative"):
					count = count + 1
					deletes.append(x)
				if (count == (len(labels)-(list(labels).count("positive"))*2)):
					break
			labelledCorpus = np.delete(labelledCorpus,deletes,axis=0)
			labels = np.delete(labels,deletes)
			##################

			numData = len(labels) # size of the labelled data set
			dataPerFold = int(math.ceil(numData/numFolds))


			for n in range(0,numFolds):
				# split training and test data
				train_labelledCorpus,test_labelledCorpus,train_labels,test_labels = train_test_split(labelledCorpus,labels,test_size=0.13)

				# build classifier
				classifier = svm.SVC(kernel='linear').fit(train_labelledCorpus,train_labels)
				# classifier = svm.LinearSVC(C=1.0).fit(train_labelledCorpus,train_labels)
				# classifier = neighbors.KNeighborsClassifier(n_neighbors=3).fit(train_labelledCorpus,train_labels)

				# compute output label and corresponding score
				output_test = classifier.predict(test_labelledCorpus)
				output_train = classifier.predict(train_labelledCorpus)
				output_scores_test = classifier.decision_function(test_labelledCorpus)
				output_scores_train = classifier.decision_function(train_labelledCorpus)

				# sort scores and labels in order
				sortList = list(zip(output_scores_test,output_test,test_labels,test_labelledCorpus))
				sortList.sort()
				output_scores_test,output_test,test_labels,test_labelledCorpus = zip(*sortList)

				if n ==0:
					all_test_labels = test_labels
					all_output_scores_test = output_scores_test
					all_train_labels = tuple(train_labels)
					all_output_scores_train = tuple(output_scores_train)
				else:
					all_test_labels = all_test_labels + test_labels
					all_output_scores_test = all_output_scores_test + output_scores_test
					all_train_labels = all_train_labels + tuple(train_labels)
					all_output_scores_train = all_output_scores_train+ tuple(output_scores_train)
				# save result to file
				for r in range(len(test_labels)):
					reportIdx = corpusList.index(list(test_labelledCorpus[r]))
					writer.writerow("")
					writer.writerow([output_scores_test[r],output_test[r],test_labels[r]])
					writer.writerow([reports[reportIdx]])
			# generate the roc curve
			fp_test,tp_test,_ = roc_curve(all_test_labels,all_output_scores_test,pos_label="positive")
			fp_train,tp_train,_ = roc_curve(all_train_labels,all_output_scores_train,pos_label="positive")

			# Calculate the area under the curves
			area_test = auc(fp_test, tp_test)
			area_train = auc(fp_train, tp_train)
			# Plot the average ROC curves
			plt.plot(fp_test,tp_test,'b',label='test(area = %0.2f)' % area_test)
			plt.plot(fp_train,tp_train,'r',label='train(area = %0.2f)' % area_train)
			plt.legend(loc='lower right')
			plt.savefig(directory+name)
	writeFile.close()
	# 			# build roc curve and plot
	# 			fp_test,tp_test,_ = roc_curve(test_labels,output_scores_test,pos_label="positive")
	# 			fp_train,tp_train,_ = roc_curve(train_labels,output_scores_train,pos_label="positive")
	# 			area_test = auc(fp_test, tp_test)
	# 			area_train = auc(fp_train, tp_train)
	#
	# 			plt.plot(fp_test,tp_test,'b',label='test(area = %0.2f)' % area_test if n == 0 else "")
	# 			plt.plot(fp_train,tp_train,'r',label='train(area = %0.2f)' % area_train if n == 0 else "")
	# 			plt.legend(loc='lower right')
	# 			plt.savefig(directory+name)
	#
	#
	# 			# save result to file
	# 			for r in range(len(test_labels)):
	# 				reportIdx = corpusList.index(list(test_labelledCorpus[r]))
	# 				writer.writerow("")
	# 				writer.writerow([output_scores_test[r],output_test[r],test_labels[r]])
	# 				writer.writerow([reports[reportIdx]])
	# 	# plt.show()
	# writeFile.close()

# tests the model at classifying reports as either positive or negative based on diagnosis
# Uses D2V model
def labelClassificationD2V():

	model = gensim.models.Doc2Vec.load("./model_files/reports.doc2vec_model")

	reports = preprocess.getReports()
	processedReports = preprocess.getProcessedReports()

	numFolds = 5 # number of folds for cross validation
	directory = "label_classification/" + datetime.datetime.now().strftime('%m_%d_%H_%M') +"/"
	if not os.path.exists(directory):
		os.makedirs(directory)
	with open(directory+"labelClassification.csv",'w') as writeFile:
		writer = csv.writer(writeFile)
		writer.writerow(["score","output label","expected label","report"])

		for j in range(len(REPORT_FILES_LABELLED)):
			writer.writerow("")
			writer.writerow("")
			writer.writerow([DIAGNOSES[j]])

			# initialise figure and plot
			name = DIAGNOSES[j] + " ROC"
			plt.figure(name)
			plt.xlabel("False Positive")
			plt.ylabel("True Positive")
			plt.title(DIAGNOSES[j] + " ROC")

			# fetch corpus and labels
			labelledReports = []
			labelledCorpus = list()
			# The labeled data is at the start of the data set
			# Get the ids in the corpus of these first labeled examples for each class
			for i in range(preprocess.getNumReports(REPORT_FILES[:j]),preprocess.getNumReports(REPORT_FILES[:j])+preprocess.getNumReports([REPORT_FILES_LABELLED[j]])):
				labelledReports.append(reports[i])
				labelledCorpus.append(model.infer_vector(processedReports[i]))
			labels = np.asarray(preprocess.getData([REPORT_FILES_LABELLED[j]]))[:,2]
			corpusList = [list(x) for x in labelledCorpus]
			############### THIS CODE BLOCK REMOVES THE NUMBER OF NEGATIVE LABELS TO EQUALISE THE DISTRIBUTION OF CLASS LABELS. TO BE REMOVED IN FUTURE.
			count = 0
			deletes = []
			for x in range(len(labels)):
				if (labels[x] == "negative"):
					count = count + 1
					deletes.append(x)
				if (count == (len(labels)-(list(labels).count("positive"))*2)):
					break
			labelledCorpus = np.delete(labelledCorpus,deletes,axis=0)
			labels = np.delete(labels,deletes)
			##################

			numData = len(labels) # size of the labelled data set
			dataPerFold = int(math.ceil(numData/numFolds))


			for n in range(0,numFolds):
				# split training and test data
				train_labelledCorpus,test_labelledCorpus,train_labels,test_labels = train_test_split(labelledCorpus,labels,test_size=0.13)

				# build classifier
				classifier = svm.SVC(kernel='linear').fit(train_labelledCorpus,train_labels)

				# compute output label and corresponding score
				output_test = classifier.predict(test_labelledCorpus)
				output_train = classifier.predict(train_labelledCorpus)
				output_scores_test = classifier.decision_function(test_labelledCorpus)
				output_scores_train = classifier.decision_function(train_labelledCorpus)

				# sort scores and labels in order
				sortList = list(zip(output_scores_test,output_test,test_labels,test_labelledCorpus))
				sortList.sort()
				output_scores_test,output_test,test_labels,test_labelledCorpus = zip(*sortList)

				# build roc curve and plot
				fp_test,tp_test,_ = roc_curve(test_labels,output_scores_test,pos_label="positive")
				fp_train,tp_train,_ = roc_curve(train_labels,output_scores_train,pos_label="positive")

				plt.plot(fp_test,tp_test,'r',label="train" if n == 0 else "")
				plt.plot(fp_train,tp_train,'b',label="test" if n == 0 else "")
				plt.legend(loc='lower right')
				plt.savefig(directory+name)

				# save result to file
				for r in range(len(test_labels)):
					reportIdx = corpusList.index(list(test_labelledCorpus[r]))
					writer.writerow("")
					writer.writerow([output_scores_test[r],output_test[r],test_labels[r]])
					writer.writerow([labelledReports[reportIdx]])
		# plt.show()
	writeFile.close()

# tests the model at classifying reports as either positive or negative based on diagnosis
# Uses D2V model
def labelClassificationRNN(learn=True):
	if learn:
		c_vals = [[0.001,0.001,0.001,0.001]]
		c_vals = [[0.005,0.005,0.005,0.005]]
		c_vals.append([0.01,0.01,0.01,0.01])
		c_vals.append([0.05,0.05,0.05,0.05])
		c_vals.append([0.1,0.1,0.1,0.1])
		c_vals.append([0.5,0.5,0.5,0.5])
		c_vals.append([1,1,1,1])
		optimal_c = [[0,0,0,0]]
	else:
		file = open('./model_files/svm_c_values.pkl', 'r')
		c_vals = pickle.load(file)
		optimal_c = c_vals
		file.close()
	reports = preprocess.getReports()
	reportVectors = rnn.loadReportVecs()

	numFolds = 5 # number of folds for cross validation
	directory = "label_classification/" + datetime.datetime.now().strftime('%m_%d_%H_%M') +"/"
	if not os.path.exists(directory):
		os.makedirs(directory)
	with open(directory+"labelClassification.csv",'w') as writeFile:
		writer = csv.writer(writeFile)
		writer.writerow(["score","output label","expected label","report"])

		for j in range(len(REPORT_FILES_LABELLED)):
			writer.writerow("")
			writer.writerow("")
			writer.writerow([DIAGNOSES[j]])
			# fetch corpus and labels
			labelledReports = []
			labelledCorpus = list()
			# The labeled data is at the start of the data set
			# Get the ids in the corpus of these first labeled examples for each class
			for i in range(preprocess.getNumReports(REPORT_FILES[:j]),preprocess.getNumReports(REPORT_FILES[:j])+preprocess.getNumReports([REPORT_FILES_LABELLED[j]])):
				labelledReports.append(reports[i])
				labelledCorpus.append(reportVectors[i][:])
			labels = np.asarray(preprocess.getData([REPORT_FILES_LABELLED[j]]))[:,2]
			corpusList = [list(x) for x in labelledCorpus]
			############### THIS CODE BLOCK REMOVES THE NUMBER OF NEGATIVE LABELS TO EQUALISE THE DISTRIBUTION OF CLASS LABELS. TO BE REMOVED IN FUTURE.
			# count = 0
			# deletes = []
			# for x in range(len(labels)):
			# 	if (labels[x] == "negative"):
			# 		count = count + 1
			# 		deletes.append(x)
			# 	if (count == (len(labels)-(list(labels).count("positive"))*2)):
			# 		break
			# labelledCorpus = np.delete(labelledCorpus,deletes,axis=0)
			# labels = np.delete(labels,deletes)
			##################
			best_area_cv = -1
			for c_value in c_vals:
				for n in range(numFolds):
					# split training and test data
					train_labelledCorpus,test_labelledCorpus,train_labels,test_labels = train_test_split(labelledCorpus,labels,test_size=0.15)
					# Split of the last 20% of training set for cross validation
					cv_labelledCorpus = train_labelledCorpus[int(0.8*len(train_labelledCorpus)):]
					train_labelledCorpus = train_labelledCorpus[:int(0.8*len(train_labelledCorpus))]
					cv_labels = train_labels[int(0.8*len(train_labels)):]
					train_labels = train_labels[:int(0.8*len(train_labels))]
					# build classifier
					classifier = svm.SVC(C=c_value[j],kernel='linear').fit(train_labelledCorpus,train_labels)
					# compute output label and corresponding score
					output_test = classifier.predict(test_labelledCorpus)
					output_cv = classifier.predict(cv_labelledCorpus)
					output_train = classifier.predict(train_labelledCorpus)
					output_scores_test = classifier.decision_function(test_labelledCorpus)
					output_scores_train = classifier.decision_function(train_labelledCorpus)
					output_scores_cv = classifier.decision_function(cv_labelledCorpus)

					if n ==0:
						all_test_labels = tuple(test_labels)
						all_output_scores_test = tuple(output_scores_test)
						all_cv_labels = tuple(cv_labels)
						all_output_scores_cv = tuple(output_scores_cv)
						all_train_labels = tuple(train_labels)
						all_output_scores_train = tuple(output_scores_train)
					else:
						all_test_labels = all_test_labels + tuple(test_labels)
						all_output_scores_test = all_output_scores_test + tuple(output_scores_test)
						all_cv_labels = all_cv_labels + tuple(cv_labels)
						all_output_scores_cv = all_output_scores_cv + tuple(output_scores_cv)
						all_train_labels = all_train_labels + tuple(train_labels)
						all_output_scores_train = all_output_scores_train+ tuple(output_scores_train)
					# save result for fold to file
					for r in range(len(test_labels)):
						reportIdx = corpusList.index(list(test_labelledCorpus[r]))
						writer.writerow("With c value: "+str(c_value[j]))
						writer.writerow([output_scores_test[r],output_test[r],test_labels[r]])
						writer.writerow([labelledReports[reportIdx]])
				# generate the roc curve
				fp_test,tp_test,_ = roc_curve(all_test_labels,all_output_scores_test,pos_label="positive")
				fp_cv,tp_cv,_ = roc_curve(all_cv_labels,all_output_scores_cv,pos_label="positive")
				fp_train,tp_train,_ = roc_curve(all_train_labels,all_output_scores_train,pos_label="positive")

				# Calculate the area under the curves
				area_test = auc(fp_test, tp_test)
				area_cv = auc(fp_cv, tp_cv)
				area_train = auc(fp_train, tp_train)
				# Store c value,tps, fps and aucs if cv auc is new best
				if area_cv > best_area_cv:
					optimal_c[0][j] = c_value[j]
					best_fp_test=fp_test
					best_tp_test=tp_test
					best_fp_cv=fp_cv
					best_tp_cv=tp_cv
					best_fp_train=fp_train
					best_tp_train=tp_train
					best_area_test=area_test
					best_area_cv=area_cv
					best_area_train=area_train
			# initialise and plot the average ROC curves for optimal c value
			name = DIAGNOSES[j] + " ROC"
			plt.figure(name)
			plt.xlabel("False Positive")
			plt.ylabel("True Positive")
			plt.title(DIAGNOSES[j] + " ROC: c value of "+str(optimal_c[0][j]))
			plt.plot(best_fp_test,best_tp_test,'b',label='test(area = %0.2f)' % best_area_test)
			plt.plot(best_fp_cv,best_tp_cv,'g',label='cv(area = %0.2f)' % best_area_cv)
			plt.plot(best_fp_train,best_tp_train,'r',label='train(area = %0.2f)' % best_area_train)
			plt.legend(loc='lower right')
			plt.savefig(directory+name)
	writeFile.close()
	if learn:
		file = open('./model_files/svm_c_values.pkl', 'w')
		pickle.dump(optimal_c,file)
		file.close()
