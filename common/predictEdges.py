#!/usr/bin/env python

"""
Predicts the edges across two LDA/LSI model.
"""
from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

# local modules
from Util import loadPickle, getAndCheckFilename, loadModel
from Prediction_util import makeEdges, filterByPopularity
from KNNSearchEngine import KNNSearchEngine
from sklearn.preprocessing import normalize

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-k', type='int', dest='k', default=2,
        help='Number of predicted edges per node.', metavar='NUM')
    parser.add_option('--both', action='store_true', dest='both', default=False,
        help=('Predict k edges for each node in each graph connecting to a '
              'node in the other graph.'))
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--popdict', dest='popdict', default=None,
        help='Picked popularity dictionary.', metavar='FILE')
    parser.add_option('--min-pop', type='int', dest='minPop',
        default=0, help='Minimum popularity to be included in search engine.',
        metavar='NUM')
    parser.add_option('--weight', action='store_true', dest='weight',
        default=False,
        help='Weight KNN search engine results using popDictionary.')
    parser.add_option('--sphere', action='store_true', dest='sphere',
        default=False,
        help='Project items in latent spaces onto surface of sphere.')
    parser.add_option('--topn', type='int', dest='topn', default=None,
        help=('Number of nearest neighbors in latent space to consider before '
              'applying popularity weighting.'), metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicMap.pickle modelfile1 modelfile2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 

    topic_map_filename = getAndCheckFilename(args[0])
    model1_filename = getAndCheckFilename(args[1])
    model2_filename = getAndCheckFilename(args[2])

    # get popularity dictionary
    if options.popdict:
        print 'Loading popularity dictionary from %s. . .' % options.popdict
        popDictionary = loadPickle(options.popdict)
    else:
        popDictionary = None

    # load topic map
    print 'Loading topic map from %s. . .' % topic_map_filename
    topic_map = loadPickle(topic_map_filename)

    # load models
    print 'Loading model1 from %s. . .' % model1_filename
    data1, dictionary1 = loadModel(model1_filename)
    print 'Loading model2 from %s. . .' % model2_filename
    data2, dictionary2 = loadModel(model2_filename)

    if popDictionary is not None and options.minPop > 0:
        # filter items in target space by popularity
        print 'Filtering target space such that popularity >= %d. . .' %\
              options.minPop
        data2, dictionary2 = filterByPopularity(data2, dictionary2,
                                                popDictionary, options.minPop)
        print 'Filtered target space with %d items.' % data2.shape[0]

    # transform each model to other's space
    print 'Transforming topic spaces. . .'
    transformed_data1 = np.dot(data1, np.array(topic_map).transpose())
    if options.both:
        transformed_data2 = np.dot(data2, np.array(topic_map))

    if options.sphere:
        # place all items in latent space on surface of sphere
        transformed_data1 = normalize(transformed_data1, 'l2', axis=1)
        data2 = normalize(data2, 'l2', axis=1)
        if options.both:
            transformed_data2 = normalize(transformed_data2, 'l2', axis=1)
            data1 = normalize(data1, 'l2', axis=1)

    # create search engines
    print 'Creating KNN search engines. . .'
    searchEngine2 = KNNSearchEngine(data2, dictionary2)
    if options.both:
        searchEngine1 = KNNSearchEngine(data1, dictionary1)

    # search for neighbors of model1 items within model2
    print 'Predicting edges. . .'
    distances1, neighbors1 = searchEngine2.kneighbors(
        transformed_data1,
        options.k,
        weights=popDictionary if options.weight else None,
        topn=options.topn
    )
    if options.both:
        distances2, neighbors2 = searchEngine1.kneighbors(
            transformed_data2,
            options.k,
            weights=popDictionary if options.weight else None,
            topn=options.topn
        )

    # translate neighbors into edge predictions
    predicted_edges = makeEdges(neighbors1, dictionary1)
    if options.both:
        predicted_edges += makeEdges(neighbors2, dictionary2)
        # remove duplicates
        predicted_edges = [(min(n1, n2), max(n1, n2)) for\
                           (n1, n2) in predicted_edges]
        predicted_edges = list(set(predicted_edges))

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
