# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 13:40:01 2018

@author: vwzheng
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt    
import os
os.chdir('D:/Downloads/vivienne/ML/Classification_UW')

#Load Amazon dataset
products = pd.read_csv('amazon_baby.csv')

#Perform text cleaning
products['review_clean'] = products['review'].str.replace('[^\w\s]','') 
#fill in N/A's in the review column
products = products.fillna({'review':''})  

#Extract Sentiments
#ignore all reviews with rating = 3, as they tend to have a neutral sentiment
products = products[products['rating'] != 3]

#Assign reviews with a rating of 4 or higher to be positive reviews, while 
#the ones with rating of 2 or lower are negative
products['sentiment'] = products['rating'].apply(lambda rating: 
                                                 +1 if rating > 3 else -1)
    
#Split into training and test sets    
train_idx = pd.read_json('module-9-assignment-train-idx.json')
test_idx = pd.read_json('module-9-assignment-test-idx.json')
train_data = products.iloc[train_idx.iloc[:,0].values]
test_data = products.iloc[test_idx.iloc[:,0].values]    

os.chdir('D:/Downloads/vivienne/ML/Classification_UW/Wk6_Precision&Recall')    

#Build the word count vector for each review
from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(token_pattern=r'\b\w+\b')
#Use this token pattern to keep single-letter words
#First, learn vocabulary from the training data and assign columns to words
#Then convert the training data into a sparse matrix
train_data = train_data.fillna({'review_clean':''})
train_matrix = vectorizer.fit_transform(train_data['review_clean'])
#Second, convert the test data into a sparse matrix, using the same 
#word-column mapping
test_data = test_data.fillna({'review_clean':''})
test_matrix = vectorizer.transform(test_data['review_clean'])

#Train a sentiment classifier with logistic regression
from sklearn.linear_model import LogisticRegression
model = LogisticRegression()
model.fit(train_matrix, train_data['sentiment'])
model.classes_

#Model Evaluation
#Accuracy
from sklearn.metrics import accuracy_score
accuracy = accuracy_score(y_true=test_data['sentiment'].as_matrix(), 
                          y_pred=model.predict(test_matrix))
print("Test Accuracy: %s" % accuracy)

#Baseline: Majority class prediction
baseline = len(test_data[test_data['sentiment'] == 1])/len(test_data)
print("Baseline accuracy (majority class classifier): %s" % baseline)
#Using accuracy as the evaluation metric, logistic regression model was 
#better than the baseline (majority class classifier)

#Confusion Matrix
from sklearn.metrics import confusion_matrix
cmat = confusion_matrix(y_true=test_data['sentiment'].as_matrix(),
                        y_pred=model.predict(test_matrix),
                        labels=model.classes_)    
#use the same order of class as the LR model.
print(' target_label | predicted_label | count ')
print('--------------+-----------------+-------')
#Print out the confusion matrix.
#Consult appropriate manuals.
for i, target_label in enumerate(model.classes_):
    for j, predicted_label in enumerate(model.classes_):
        print('{0:^13} | {1:^15} | {2:5d}'.format(target_label, 
                                                  predicted_label, 
                                                  cmat[i,j]))
'''
 target_label | predicted_label | count 
--------------+-----------------+-------
     -1       |       -1        |  3788
     -1       |        1        |  1453 
      1       |       -1        |   803
      1       |        1        | 27292
'''
#1453 predicted values in the test set are false positives   

#Compute the cost of mistakes
FP = cmat[0,1]     
FN = cmat[1,0]
cost = 100*FP + 1*FN

#Precision and Recall
from sklearn.metrics import precision_score
precision = precision_score(y_true=test_data['sentiment'].as_matrix(), 
                            y_pred=model.predict(test_matrix))
#precision = TP/(TP+FP)
print("Precision on test data: %s" % precision)
#fraction of false positives
FP_percent = 1 - precision 
#0.0505479213776
#wanted to reduce this fraction of false positives to be below 3.5%, 
#we would: increase threshold for predicting the positive class y_hat = 1

from sklearn.metrics import recall_score
recall = recall_score(y_true=test_data['sentiment'].as_matrix(),
                      y_pred=model.predict(test_matrix))
#recall = TP/(TP+FN)
print("Recall on test data: %s" % recall)
#0.971418401851
#fraction of the positive reviews in the test_set were correctly predicted 
#as positive by the classifier
#the recall value for a classifier that predicts +1 for all data points in 
#the test_data is 1

#Precision-recall tradeoff
#Vary the threshold
#False positives are costly, so be more conservative about making positive 
#predictions. To achieve this, choose a higher threshold 
def apply_threshold(probabilities, threshold):
    #+1 if >= threshold and -1 otherwise.
    result = np.ones(len(probabilities))
    result[probabilities < threshold] = -1
    
    return result

#compute the class probability
probabilities = model.predict_proba(test_matrix)[:,1]
predictions_with_default_threshold = apply_threshold(probabilities, 0.5)
pos_pred_default = sum(predictions_with_default_threshold == 1) #28745
predictions_with_high_threshold = apply_threshold(probabilities, 0.9)
pos_pred_high = sum(predictions_with_high_threshold == 1) #25061
#the number of positive predicted reviews decrease as the threshold increased
#from 0.5 to 0.9

#Explore the associated precision and recall as the threshold varies
#Threshold = 0.5
precision_with_default_threshold = precision_score(
                                   y_true=test_data['sentiment'].as_matrix(),
                                   y_pred=predictions_with_default_threshold)

recall_with_default_threshold = recall_score(
                                y_true=test_data['sentiment'].as_matrix(), 
                                y_pred=predictions_with_default_threshold)

print("Precision (threshold = 0.5): %s" % precision_with_default_threshold)
print("Recall (threshold = 0.5)   : %s" % recall_with_default_threshold)

#Threshold = 0.9
precision_with_high_threshold = precision_score(
                                y_true=test_data['sentiment'].as_matrix(), 
                                y_pred=predictions_with_high_threshold)

recall_with_high_threshold = recall_score(
                             y_true=test_data['sentiment'].as_matrix(), 
                             y_pred=predictions_with_high_threshold)

print("Precision (threshold = 0.9): %s" % precision_with_high_threshold)
print("Recall (threshold = 0.9)   : %s" % recall_with_high_threshold)
#the precision increases with a higher threshold
#the recall decreases with a higher threshold

#Precision-recall curve
threshold_values = np.linspace(0.5, 1, num=100)
print(threshold_values)

precision_all = []
recall_all = []
probabilities = model.predict_proba(test_matrix)[:,1]
for threshold in threshold_values:
    predictions = apply_threshold(probabilities, threshold)
    precision = precision_score(y_true=test_data['sentiment'].as_matrix(), 
                                y_pred=predictions)
    recall = recall_score(y_true=test_data['sentiment'].as_matrix(), 
                          y_pred=predictions)
    precision_all.append(precision)
    recall_all.append(recall)

#plot the precision-recall curve to visualize the precision-recall tradeoff 
def plot_pr_curve(precision, recall, title):
    plt.rcParams['figure.figsize'] = 7, 5
    plt.locator_params(axis = 'x', nbins = 5)
    plt.plot(precision, recall, 'b-', linewidth=4.0, color = '#B0017F')
    plt.title(title)
    plt.xlabel('Precision')
    plt.ylabel('Recall')
    plt.rcParams.update({'font.size': 16})
    
plot_pr_curve(precision_all, recall_all, 'Precision recall curve (all)')  
plt.savefig('precision_recall.png')
#Among all the threshold values tried, the smallest threshold value that 
#achieves a precision of 96.5% or better is: 0.70707071
print(np.array(threshold_values)[np.array(precision_all) >= 0.965]) #all
print(threshold_values[np.array(precision_all) >= 0.965].min()) #.707

#Using threshold = 0.98, the number of false negatives:
predictions_with_98_threshold = apply_threshold(probabilities, 0.98)
FN_98 = sum((predictions_with_98_threshold == -1)&
            (test_data['sentiment'] == 1)) #8247
cmat_98 = confusion_matrix(y_true=test_data['sentiment'].as_matrix(),
                           y_pred=predictions_with_98_threshold,
                           labels=model.classes_)    
#use the same order of class as the LR model.
print(' target_label | predicted_label | count ')
print('--------------+-----------------+-------')
#Print out the confusion matrix.
#Consult appropriate manuals.
for i, target_label in enumerate(model.classes_):
    for j, predicted_label in enumerate(model.classes_):
        print('{0:^13} | {1:^15} | {2:5d}'.format(target_label, 
                                                  predicted_label, 
                                                  cmat_98[i,j]))
'''
 target_label | predicted_label | count 
--------------+-----------------+-------
     -1       |       -1        |  5050
     -1       |        1        |   191  #FP
      1       |       -1        |  8247  #FN
      1       |        1        | 19848  #TP
'''
        
#Evaluate specific search terms
#Precision-Recall on all baby related items
baby_reviews = test_data[test_data['name'].apply(lambda x: 
                                                 'baby' in str(x).lower())]
baby_matrix = vectorizer.transform(baby_reviews['review_clean'])
probabilities_baby = model.predict_proba(baby_matrix)[:,1]    
#threshold_values = np.linspace(0.5, 1, num=100)
precision_baby = []
recall_baby = []
for threshold in threshold_values: 
    #Make predictions. Use the `apply_threshold` function 
    predictions = apply_threshold(probabilities_baby, threshold)
    #Calculate the precision
    precision = precision_score(y_true=baby_reviews['sentiment'].as_matrix(),
                                y_pred=predictions)
    
    recall = recall_score(y_true=baby_reviews['sentiment'].as_matrix(), 
                          y_pred=predictions)
    #Append the precision and recall scores.
    precision_baby.append(precision)
    recall_baby.append(recall)

#Among all the threshold values tried, the smallest threshold value that 
#achieves a precision of 96.5% or better for the reviews in baby_reviews is:
#0.727272727273
print(threshold_values[np.array(precision_baby) >= 0.965].min()) #0.727
#this threshold value is larger than the threshold used for the entire 
#dataset to achieve the same specified precision of 96.5%    
plot_pr_curve(precision_baby, recall_baby, 'Precision recall curve (Baby)')  
plt.savefig('precision_recall_baby.png')