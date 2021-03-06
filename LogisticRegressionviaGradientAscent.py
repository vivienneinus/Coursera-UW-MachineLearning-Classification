# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 09:52:01 2018

@author: vwzheng
"""

import pandas as pd
import numpy as np
import os
os.chdir('D:/Downloads/vivienne/ML/Classification_UW')

#Load Amazon dataset
products = pd.read_csv('amazon_baby_subset.csv')
#Explore dataset
products.info()
products.describe()
products.describe(include=['object'])

#List the name of the first 10 products 
products['name'].head(10)
#Count positive reviews and negative reviews
count_pos = sum(products['sentiment'] == 1) #26579
count_neg = sum(products['sentiment'] == -1) #26493

#Apply text cleaning on the review data
#Load json file for important_words list
#important_words = pd.read_json('important_words.json') #dataframe
import json
with open('important_words.json') as important_words_file:    
    important_words = json.load(important_words_file)

#Remove punctuation
products = products.fillna({'review': ''}) #fill in N/A's in the review col
def remove_punctuation(text):
    import string
    tr = str.maketrans("", "", string.punctuation)
    return text.translate(tr)
products['review_clean'] = products['review'].apply(remove_punctuation) 

#df['review_clean'] = df['review'].str.replace('[^\w\s]','') #same above

#Compute word counts for important_words
for word in important_words:
    products[word] = products['review_clean'].apply(lambda s : 
                                                    s.split().count(word))
#Updated dataframe        
products.head(1)        
        
#Count reviews containing "perfect" from important_words    
#count_perfect = sum(products['perfect'] > 0) #same below
products['contains_perfect'] = products['perfect'].apply(lambda x: 1 if x >=1
                                                         else 0)  
count_perfect = sum(products['contains_perfect'])

#Convert data frame to multi-dimensional array
def get_numpy_data(dataframe, features, label):
    dataframe['constant'] = 1
    features = ['constant'] + features
    features_frame = dataframe[features]
    feature_matrix = features_frame.as_matrix()
    label_sarray = dataframe[label]
    label_array = label_sarray.as_matrix()
    return (feature_matrix, label_array)

features_matrix, sentiment = get_numpy_data(products, important_words,
                                            'sentiment')

count_features = features_matrix.shape[1]
print(sentiment)

#Estimate conditional probability with link function
'''
produces probablistic estimate for P(y_i = +1 | x_i, w).
estimate ranges between 0 and 1.
'''
def predict_probability(feature_matrix, coefficients):
    # Take dot product of feature_matrix and coefficients  
    # YOUR CODE HERE
    score = np.dot(feature_matrix, coefficients)
    
    # Compute P(y_i = +1 | x_i, w) using the link function
    # YOUR CODE HERE
    predictions = 1./(1+np.exp(-score))
    
    # return predictions
    return predictions

#Compute derivative of log likelihood with respect to a single coefficient
def feature_derivative(errors, feature):     
    # Compute the dot product of errors and feature
    derivative = np.dot(errors, feature)
        # Return the derivative
    return derivative

#Write a function compute_log_likelihood that implements the equation
def compute_log_likelihood(feature_matrix, sentiment, coefficients):
    indicator = (sentiment==+1)
    scores = np.dot(feature_matrix, coefficients)
    lp = np.sum((indicator-1)*scores - np.log(1. + np.exp(-scores)))
    return lp    

#Take gradient steps
def logistic_regression(feature_matrix, sentiment, initial_coefficients, 
                        step_size, max_iter):
    #make sure it's a numpy array
    coefficients = np.array(initial_coefficients) 
    lplist = []
    for itr in range(max_iter):
        # Predict P(y_i = +1|x_1,w) using your predict_probability() function
        # YOUR CODE HERE
        predictions = predict_probability(feature_matrix, coefficients)

        # Compute indicator value for (y_i = +1)
        indicator = (sentiment==+1)

        # Compute the errors as indicator - predictions
        errors = indicator - predictions

        for j in range(len(coefficients)): # loop over each coefficient
            # Recall that feature_matrix[:,j] is the feature column 
            #associated with coefficients[j]
            # compute the derivative for coefficients[j]. Save it in a 
            #variable called derivative
            # YOUR CODE HERE
            derivative = feature_derivative(errors, feature_matrix[:,j])

            # add the step size times the derivative to the current 
            #coefficient
            # YOUR CODE HERE
            coefficients[j] += step_size*derivative

        # Checking whether log likelihood is increasing
        if itr <= 15 or (itr <= 100 and itr % 10 == 0) or (itr <= 1000 and 
                                                           itr % 100 == 0) \
        or (itr <= 10000 and itr % 1000 == 0) or itr % 10000 == 0:
            lp = compute_log_likelihood(feature_matrix, sentiment, 
                                        coefficients)
            lplist.append(lp)
            print('iteration %*d: log likelihood of observed labels = %.8f'%\
                  (int(np.ceil(np.log10(max_iter))), itr, lp))
    
    import matplotlib.pyplot as plt
    x= [i for i in range(len(lplist))]
    plt.plot(x,lplist,'ro')
    plt.show()    
    
    return coefficients    

#Save the coefficients
coefficients = logistic_regression(features_matrix, sentiment, np.zeros(194),
                                   1e-7, 301)

#Predict sentiments
scores = pd.DataFrame(np.dot(features_matrix, coefficients))
class_predictions = scores.iloc[:,0].apply(lambda x: 1 if x > 0 else -1)
count_pred_pos = sum(class_predictions > 0)

#Measure accuracy
accuracy = sum(class_predictions == sentiment)/len(sentiment)

#Which words contribute most to positive & negative sentiments
coefficients_wo_intercept = list(coefficients[1:]) # exclude intercept
#(word, coefficient_value)
word_coefficient_tuples = [(word, coefficient) for word, 
                           coefficient in zip(important_words, coefficients)]
#sorted in coefficient_value descending
word_coefficient_tuples = sorted(word_coefficient_tuples, key=lambda x:x[1],
                                 reverse=True)
#10 "most positive" words
first_10 = word_coefficient_tuples[:10]

#10 "most negative" words
last_10 = word_coefficient_tuples[-10:]
