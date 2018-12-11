# -*- coding: utf-8 -*-
"""
Created on Sun Dec  9 14:53:07 2018

@author: Emanuele

Predict TOPIX index
"""

import copy as cp
import numpy as np
import sys

sys.path.append('../../cnn')
sys.path.append('../experiments/data_utils')

import matplotlib.pyplot as plt
import nn as nn
import utils_topix as utils


if __name__ == '__main__':
    
    net_blocks = {'n_inputs': 25, 
                  'layers': [
                          {'type': 'conv', 'activation': 'relu', 'shape': (25, 2), 'stride': 3}, 
                          {'type': 'conv', 'activation': 'relu', 'shape': (25, 2), 'stride': 3}, 
                          {'type': 'conv', 'activation': 'relu', 'shape': (25, 2), 'stride': 3}, 
                          {'type': 'dense', 'activation': 'tanh', 'shape': (None, 35)},                    
                          {'type': 'dense', 'activation': 'tanh', 'shape': (None, 1)}
                          ]
                  }
    
    # create the net    
    net = nn.NN(net_blocks)
    
    # initialize the parameters
    net.init_parameters(['uniform', -1e-4, 1e-4])

    # create the batches from topix dataset
    X_train, Y_train, X_valid, Y_valid, X_test, Y_test = utils.generate_batches(
                                                              filename='data/Topix_index.csv', 
                                                              window=net.n_inputs, mode='validation', 
                                                              non_train_percentage=.3,
                                                              val_rel_percentage=.5)
    
    # normalize the dataset (max-min method)
    X_train = (X_train-np.min(X_train))/(np.max(X_train)-np.min(X_train))
    X_test = (X_test-np.min(X_test))/(np.max(X_test)-np.min(X_test))
    X_valid = (X_valid-np.min(X_valid))/(np.max(X_valid)-np.min(X_valid))
    Y_train = (Y_train-np.min(Y_train))/(np.max(Y_train)-np.min(Y_train))
    Y_test = (Y_test-np.min(Y_test))/(np.max(Y_test)-np.min(Y_test))   
    Y_valid = (Y_valid-np.min(Y_valid))/(np.max(Y_valid)-np.min(Y_valid))    
    
    epochs_train = 10
       
    # train
    for e in range(epochs_train):
        
        print("Training epoch ", e+1)
        
        for (input_, target) in zip(X_test, Y_train):
            
            # format input and prediction
            input_ = input_[np.newaxis,:]
            target = np.array([target])[np.newaxis,:]
                      
            # activate and caluclate derivative for each layer, given the input
            net.activation(input_, accumulate=True)
            net.derivative(None)
                        
            # execute the backpropagation with the input that has been memorized previously
            net.backpropagation(target=target, 
                                loss='L2', 
                                optimizer='sgd', 
                                l_rate=1e-4,
                                update=True)
                        
    # validation: calculate error and estimate its mean and variance
    errors_valid = np.zeros(shape=len(X_valid))
    i = 0
    
    for (input_, target) in zip(X_valid, Y_valid):
        
        
        # format input and prediction
        input_ = input_[np.newaxis,:]
        target = np.array([target])[np.newaxis,:]
        
        net.activation(input_, accumulate=True)
        
#        # backrpop after prediction
#        net.derivative(None)                    
#        net.backpropagation(target=target, 
#                            loss='L2', 
#                            optimizer='sgd', 
#                            l_rate=5e-3,
#                            update=True)
        
        errors_valid[i] = net.output - target
        
        i += 1
    
    mean_valid, var_valid = (errors_valid.mean(), errors_valid.var())
    
    # test   
    p_anomaly_test = np.zeros(shape=len(X_test))
    predictions = np.zeros(shape=len(X_test))
    errors_test = cp.copy(errors_valid)
    i = 0
     
    for (input_, target) in zip(X_test, Y_test):
        
        # format input and prediction
        input_ = input_[np.newaxis,:]
        target = np.array([target])[np.newaxis,:]
        
        net.activation(input_, accumulate=True)
        prediction = net.output
        
#        # backrpop after prediction
#        net.derivative(None)                    
#        net.backpropagation(target=target, 
#                            loss='L2', 
#                            optimizer='sgd', 
#                            l_rate=5e-2,
#                            update=True)
        
        predictions[i] = prediction
        errors_test[i] = utils.gaussian_pdf(errors_test[i], 
                                             mean_valid, 
                                             var_valid)
        anomalies = np.argwhere(errors_test < 1e-1)   
                
        i += 1
        
    # plot results
    fig, ax1 = plt.subplots()

    # plot data series
    ax1.plot(Y_test[:-net.n_inputs+1], 'b', label='index')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('TOPIX')

    # plot predictions
    ax1.plot(predictions, 'r', label='prediction')
    ax1.set_ylabel('Change Point')
    plt.legend(loc='best')
    
    for i in anomalies[:-net.n_inputs+1]:

        plt.axvspan(i, i+1, color='yellow', alpha=0.5, lw=0)

    fig.tight_layout()
    plt.show()
    
    import random; print("\nTen couples of (prediction, target):\n",
                         random.sample(set(zip(predictions, Y_test)), 10))    
    
    print("\nTotal error on ", len(predictions), "points is ", 
          np.linalg.norm(Y_test[:-net.n_inputs+1]-predictions))
    