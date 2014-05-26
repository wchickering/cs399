#!/usr/bin/env python

import numpy as np
import math

"""
Helper functions for use with gensim LdaModel.
"""
def loadLDAModel(model):
    dictionary = {}
    for i, node in model.id2word.items():
        dictionary[i] = int(node)
    data = getTopicGivenItemProbs(model).transpose()
    return data, dictionary

def getTopicProbs(model):
    return model.alpha/sum(model.alpha)

def getItemGivenTopicProbs(model):
    raw_beta = model.state.get_lambda()
    row_sums = raw_beta.sum(axis=1)
    return raw_beta / row_sums[:,np.newaxis]

def getItemProbs(model):
    return np.transpose(getItemGivenTopicProbs(model)).dot(getTopicProbs(model))

def getTopicGivenItemProbs(model):
    return getItemGivenTopicProbs(model)*getTopicProbs(model)[:,np.newaxis]/\
           getItemProbs(model)

def cosSimTopics(model, topicA, topicB):
    raw_beta = model.state.get_lambda()
    vecA = raw_beta[topicA,:]
    vecB = raw_beta[topicB,:]
    return np.dot(vecA, vecB)/math.sqrt(np.dot(vecA, vecA)*np.dot(vecB, vecB))
