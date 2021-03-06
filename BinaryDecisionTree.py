# -*- coding: utf-8 -*-
"""
Created on Wed Nov 21 16:33:19 2018

@author: vwzheng
"""

import pandas as pd
import numpy as np
import os
os.chdir('D:/Downloads/vivienne/ML/Classification_UW')

#Load the Lending Club dataset
data = pd.read_csv('lending-club-data.csv')
loans = data

#reassign the labels to have +1 for a safe loan, and -1 for a risky/bad loan
loans['safe_loans'] = loans['bad_loans'].apply(lambda x : +1 if x==0 else -1)
loans = loans.drop('bad_loans', axis = 1)

#consider these four features
features = ['grade',            #grade of the loan
            'term',             #the term of the loan
            'home_ownership',   #home_ownership status: own, mortgage or rent
            'emp_length',       #number of years of employment
           ]
target = 'safe_loans'

#Extract these feature columns from the dataset, 
#and discard the rest of the feature columns
loans = loans[features + [target]]
loans.info()
loans.describe(include='all')
loans.grade.unique()
loans.term.unique()
loans.home_ownership.unique()
loans.emp_length.unique()
loans = loans.fillna('n/a')

#Apply one-hot encoding to loans
categorical_variables = []
for feat_name, feat_type in zip(loans.columns, loans.dtypes):
    if feat_type == object:
        categorical_variables.append(feat_name)

for feature in categorical_variables:
    loans_one_hot_encoded = pd.get_dummies(loans[feature],prefix=feature)
    #loans = pd.concat([loans, loans_one_hot_encoded],axis=1)
    loans = loans.drop(feature, axis=1)
    for col in loans_one_hot_encoded.columns:
        loans[col] = loans_one_hot_encoded[col]

#Split data into training and validation by loading JSON files for indices
train_idx = pd.read_json('module-5-assignment-2-train-idx.json')
test_idx = pd.read_json('module-5-assignment-2-test-idx.json')
train_data = loans.iloc[train_idx.iloc[:,0].values]
test_data = loans.iloc[test_idx.iloc[:,0].values]

#Decision tree implementation
#Function to count number of mistakes while predicting majority class
def intermediate_node_num_mistakes(labels_in_node):
    # Corner case: If labels_in_node is empty, return 0
    if len(labels_in_node) == 0:
        return 0    
    # Count the number of 1's (safe loans)
    loans_safe = sum(labels_in_node == 1)   
    # Count the number of -1's (risky loans)
    loans_risky = sum(labels_in_node == -1)                
    # Return the number of mistakes that the majority classifier makes.
    return min(loans_safe, loans_risky)    
    
    
# Test case 1
example_labels = np.array([-1, -1, 1, 1, 1])
if intermediate_node_num_mistakes(example_labels) == 2:
    print ('Test passed!')
else:
    print ('Test 1 failed... try again!')

# Test case 2
example_labels = np.array([-1, -1, 1, 1, 1, 1, 1])
if intermediate_node_num_mistakes(example_labels) == 2:
    print ('Test passed!')
else:
    print ('Test 2 failed... try again!')
    
# Test case 3
example_labels = np.array([-1, -1, -1, -1, -1, 1, 1])
if intermediate_node_num_mistakes(example_labels) == 2:
    print ('Test passed!')
else:
    print ('Test 3 failed... try again!')    
    
#Function to pick best feature to split on    
def best_splitting_feature(data, features, target):

    best_feature = None # Keep track of the best feature 
    best_error = 10     # Keep track of the best error so far 
    #Since error is always <= 1, 
    #we should intialize it with something larger than 1.

    #Convert to float to make sure error gets computed correctly.
    num_data_points = float(len(data))  
    
    #Loop through each feature to consider splitting on that feature
    for feature in features:
        
        #left split will have all data points where the feature value is 0
        left_split = data[data[feature] == 0]
        
        #right split will have all data points where the feature value is 1
        right_split = data[data[feature] == 1]
            
        #Calculate the number of misclassified examples in the left split.
        left_mistakes = intermediate_node_num_mistakes(left_split[target])            

        #Calculate the number of misclassified examples in the right split.
        right_mistakes = intermediate_node_num_mistakes(right_split[target])
            
        #Compute the classification error of this split.
        #Error = (# of left mistakes+# of right mistakes)/(# of data points)
        error = (left_mistakes+right_mistakes)/num_data_points

        #If this is the best error we have found so far, 
        #store the feature as best_feature and the error as best_error
        if error < best_error:
            best_feature = feature
            best_error = error
    
    return best_feature # Return the best feature we found    
    
#Build the tree    
#Create a leaf node given a set of target values    
def create_leaf(target_values):    
    # Create a leaf node
    leaf = {'splitting_feature' : None,
            'left' : None,
            'right' : None,
            'is_leaf': True}
   
    # Count the number of data points that are +1 and -1 in this node.
    num_ones = len(target_values[target_values == +1])
    num_minus_ones = len(target_values[target_values == -1])    

    #For the leaf node, set the prediction to be the majority class.
    #Store the predicted class (1 or -1) in leaf['prediction']
    if num_ones > num_minus_ones:
        leaf['prediction'] = 1
    else:
        leaf['prediction'] = -1         

    # Return the leaf node
    return leaf 

def decision_tree_create(data, features, target, current_depth = 0, 
                         max_depth = 10):
    remaining_features = features[:] # Make a copy of the features.
    
    target_values = data[target]
    print("----------------------------------------------------------------")
    print("Subtree, depth = %s (%s data points)."%(current_depth, 
                                                   len(target_values)))
    

    #Stopping condition 1
    #Check if there are mistakes at current node.
    if intermediate_node_num_mistakes(target_values) == 0:   
        print("Stopping condition 1 reached.")     
        #If not mistakes at current node, make current node a leaf node
        return create_leaf(target_values)
        
    #Stopping condition 2 
    #Check if there are remaining features to consider splitting on
    if remaining_features == []:
        print("Stopping condition 2 reached.")    
        #If there are no remaining features to consider, 
        #make current node a leaf node
        return create_leaf(target_values)    
    
    #Additional stopping condition (limit tree depth)
    if current_depth >= max_depth:
        print("Reached maximum depth. Stopping for now.")
        #If the max tree depth has been reached, 
        #make current node a leaf node
        return create_leaf(target_values)

    #Find the best splitting feature
    splitting_feature = best_splitting_feature(data, features, target)

    # Split on the best feature that we found. 
    left_split = data[data[splitting_feature] == 0]
    right_split = data[data[splitting_feature] == 1]
    remaining_features.remove(splitting_feature)
    print("Split on feature %s. (%s, %s)" % (splitting_feature, 
          len(left_split), len(right_split)))
    
    # Create a leaf node if the split is "perfect"
    if len(left_split) == len(data):
        print("Creating leaf node.")
        return create_leaf(left_split[target])
    if len(right_split) == len(data):
        print("Creating leaf node.")
        return create_leaf(right_split[target])

        
    #Repeat (recurse) on left and right subtrees
    left_tree = decision_tree_create(left_split, remaining_features, 
                                     target, current_depth + 1, max_depth)        

    right_tree = decision_tree_create(right_split, remaining_features, 
                                      target, current_depth + 1, max_depth)

    return {'is_leaf'          : False, 
            'prediction'       : None,
            'splitting_feature': splitting_feature,
            'left'             : left_tree, 
            'right'            : right_tree}

#Build the tree on training
feature_ls = list(train_data.drop(target, axis=1).columns)
my_decision_tree = decision_tree_create(train_data, feature_ls, target,
                                        current_depth = 0, max_depth = 6)    
    
#Make predictions with a decision tree    
def classify(tree, x, annotate = False):
    # if the node is a leaf node.
    if tree['is_leaf']:
        if annotate:
             print("At leaf, predicting %s" % tree['prediction'])
        return tree['prediction']
    else:
        # split on feature.
        split_feature_value = x[tree['splitting_feature']]
        if annotate:
             print("Split on %s = %s" % (tree['splitting_feature'], 
                                         split_feature_value))
        if split_feature_value == 0:
            return classify(tree['left'], x, annotate)
        else:
            return classify(tree['right'], x, annotate)    
        
print (test_data.iloc[0])
print ('Predicted class: %s ' % classify(my_decision_tree, 
                                         test_data.iloc[0]))

classify(my_decision_tree, test_data.iloc[0], annotate=True)        

'''
What was the feature that my_decision_tree first split on while making the 
prediction for test_data[0]? term_ 36 months

What was the first feature that lead to a right split of test_data[0]?
grade_D #print(my_decision_tree) first very right stump is grade_D

What was the last feature split on before reaching a leaf node for 
test_data[0]? grade_D
'''

#Evaluate your decision tree
def evaluate_classification_error(tree, data):
    # Apply the classify(tree, x) to each row in your data
    prediction = data.apply(lambda x: classify(tree, x), axis = 1)
    
    #calculate the classification error and return it
    return sum(prediction.values != data[target])*1./len(data)

evaluate_classification_error(my_decision_tree, test_data)

#Print out a decision stump
def print_stump(tree, name = 'root'):
    #split_name is 'term. 36 months' for root node
    split_name = tree['splitting_feature'] 
    if split_name is None:
        print("(leaf, label: %s)" % tree['prediction'])
        return None
    split_feature, split_value = split_name.split('_', 1)
    print('                       %s' % name)
    print('         |---------------|----------------|')
    print('         |                                |')
    print('         |                                |')
    print('         |                                |')
    print('  [{0} == 0]               [{0} == 1]    '.format(split_name))
    print('         |                                |')
    print('         |                                |')
    print('         |                                |')
    print('    (%s)                         (%s)' \
        % (('leaf, label: ' + str(tree['left']['prediction']) 
            if tree['left']['is_leaf'] else 'subtree'),
           ('leaf, label: ' + str(tree['right']['prediction']) 
            if tree['right']['is_leaf'] else 'subtree')))

#print the root of my_decision_tree
print_stump(my_decision_tree)    
    
#Explore the intermediate left subtree
#print out the left subtree
print_stump(my_decision_tree['left'], my_decision_tree['splitting_feature'])
#print out the left subtree of the left subtree of the root
print_stump(my_decision_tree['left']['left'], 
            my_decision_tree['left']['splitting_feature'])
#print out the right subtree
print_stump(my_decision_tree['right'], my_decision_tree['splitting_feature'])
#print out the right subtree of the right subtree of the root
print_stump(my_decision_tree['right']['right'], 
            my_decision_tree['right']['splitting_feature'])
'''
What is the path of the first 3 feature splits considered along the 
left-most branch of my_decision_tree? term_36 months, grade_A, grade_B

What is the path of the first 3 feature splits considered along the 
right-most branch of my_decision_tree? term_36 months, grade_D, leaf -1

'''