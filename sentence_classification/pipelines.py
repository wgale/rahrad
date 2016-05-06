from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.pipeline import Pipeline
# from sklearn.neural_network import MLPClassifier

from sklearn import svm

# Defines different combinations of feature extraction and classification in pipelines for easy use.

##########################
#### Model Parameters ####
##########################

countVectorizerParams = {}
tfidfVectorizerParams = {}
truncatedSVDParams = {"n_components": 10, "random_state": 42}
randomForestParams = {'n_estimators': 500, 'min_samples_leaf': 3}
SVCParams = {"probability": True}

#######################
#### Random Forest ####
#######################

# CountVectorizer -> LSI -> RandomForest
def get_count_lsi_randomforest():
    vectorizer = CountVectorizer(**countVectorizerParams)
    svd = TruncatedSVD(**truncatedSVDParams)
    classifier = RandomForestClassifier(**randomForestParams)

    return Pipeline([('vectorizer', vectorizer), ('lsi', svd), ('classifier', classifier)])


# TFIDFVectorizer -> LSI -> RandomForest
def get_tfidf_lsi_randomforest():
    vectorizer = TfidfVectorizer(**tfidfVectorizerParams)
    svd = TruncatedSVD(**truncatedSVDParams)
    classifier = RandomForestClassifier(**randomForestParams)

    return Pipeline([('vectorizer', vectorizer), ('lsi', svd), ('classifier', classifier)])

#############
#### SVM ####
#############

# CountVectorizer -> LSI -> SVM
def get_count_lsi_SVM():
    vectorizer = CountVectorizer(**countVectorizerParams)
    svd = TruncatedSVD(**truncatedSVDParams)
    classifier = svm.SVC(**SVCParams)

    return Pipeline([('vectorizer', vectorizer), ('lsi', svd), ('classifier', classifier)])


# TFIDFVectorizer -> LSI -> SVM
def get_tfidf_lsi_SVM():
    vectorizer = TfidfVectorizer(**tfidfVectorizerParams)
    svd = TruncatedSVD(**truncatedSVDParams)
    classifier = svm.SVC(**SVCParams)

    return Pipeline([('vectorizer', vectorizer), ('lsi', svd), ('classifier', classifier)])
