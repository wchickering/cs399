#!/usr/bin/env python

"""
Predicts the edges across two LDA/LSI model.
"""
from optparse import OptionParser
import pickle
import os
import sys
import numpy as np
from sklearn.preprocessing import normalize

# local modules
from Util import loadPickle, getAndCheckFilename, loadModel
from Prediction_util import makeEdges, filterByPopularity
from KNNSearchEngine import KNNSearchEngine
from TFIDF_SimilarityCache import TFIDF_SimilarityCache

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--edges-per-node', type='float', dest='edgesPerNode',
        default=1.0,
        help='Number of predicted edges per node.', metavar='FLOAT')
    parser.add_option('--symmetric', action='store_true', dest='symmetric',
        default=False,
        help=('Predict k edges for each node in each graph connecting to a '
              'node in the other graph.'))
    parser.add_option('-s', '--savefile', dest='savefile',
        default='predictEdges.pickle', help='Pickle to dump predicted edges.',
        metavar='FILE')
    parser.add_option('--popdict', dest='popdict', default=None,
        help='Pickled popularity dictionary.', metavar='FILE')
    parser.add_option('--min-pop', type='float', dest='minPop',
        default=0.0, help='Minimum popularity to be included in search engine.',
        metavar='FLOAT')
    parser.add_option('--weight-in', action='store_true', dest='weightIn',
        default=False,
        help='Weight KNN search engine results using popDictionary.')
    parser.add_option('--weight-out', action='store_true', dest='weightOut',
        default=False,
        help='Weight choice of outgoing edges using popDictionary.')
    parser.add_option('--sphere', action='store_true', dest='sphere',
        default=False,
        help='Project items in latent spaces onto surface of sphere.')
    parser.add_option('--neighbor-limit', type='int', dest='neighborLimit',
        default=None,
        help=('Number of nearest neighbors in latent space to consider before '
              'applying popularity weighting.'), metavar='NUM')
    parser.add_option('--tau', type='float', dest='tau', default=None,
        help='Coefficiennt for TF-IDF inner product term in KNN search.',
        metavar='FLOAT')
    parser.add_option('--tfidfs', dest='tfidfs', default=None,
        help='Pickled TF-IDF vectors.', metavar='FILE')
    parser.add_option('--short-coeff', type='float', dest='shortCoeff',
        default=0.0,
        help='Coefficient for TF-IDF vectors from short descriptions.')
    parser.add_option('--bigrams-coeff', type='float', dest='bigramsCoeff',
        default=0.0, help='Coefficient for TF-IDF vectors from bigrams.')
    parser.add_option('--hood-coeff', type='float', dest='hoodCoeff',
        default=0.0, help='Coefficient for TF-IDF vectors from neighborhood.')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] topicMap.pickle modelfile1 modelfile2'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments') 

    topicMapFilename = getAndCheckFilename(args[0])
    modelFilename1 = getAndCheckFilename(args[1])
    modelFilename2 = getAndCheckFilename(args[2])

    # load topic map
    print 'Loading topic map from %s. . .' % topicMapFilename
    topicMap = loadPickle(topicMapFilename)

    # load models
    print 'Loading model1 from %s. . .' % modelFilename1
    data1, dictionary1 = loadModel(modelFilename1)
    print 'Loading model2 from %s. . .' % modelFilename2
    data2, dictionary2 = loadModel(modelFilename2)

    if options.popdict:
        # load popularity dictionary
        print 'Loading popularity dictionary from %s. . .' % options.popdict
        popDictionary = loadPickle(options.popdict)
    else:
        popDictionary = None

    if options.tfidfs:
        # load TF-IDF vectors
        print 'Loading TF-IDF vectors from %s. . .' % options.tfidfs
        tfidfs = loadPickle(options.tfidfs)
    else:
        tfidfs = None

    # transform each model to other's space
    print 'Transforming topic spaces. . .'
    transformedData1 = np.dot(data1, topicMap.transpose())
    transformedDictionary1 = dict(dictionary1)
    if options.symmetric:
        transformedData2 = np.dot(data2, topicMap)
        transformedDictionary2 = dict(dictionary2)

    if popDictionary is not None and options.minPop > 0:
        # filter items in target space by popularity
        print 'Filtering target spaces. . .'
        data2, dictionary2 = filterByPopularity(
            data2, dictionary2, popDictionary, options.minPop
        )
        if options.symmetric:
            data1, dictionary1 = filterByPopularity(
                data1, dictionary1, popDictionary, options.minPop
            )

    if options.sphere:
        # place all items in latent space on surface of sphere
        transformedData1 = normalize(transformedData1, 'l2', axis=1)
        data2 = normalize(data2, 'l2', axis=1)
        if options.symmetric:
            transformedData2 = normalize(transformedData2, 'l2', axis=1)
            data1 = normalize(data1, 'l2', axis=1)

    # create search engines
    print 'Creating KNN search engines. . .'
    searchEngine2 = KNNSearchEngine(data2, dictionary2)
    if options.symmetric:
        searchEngine1 = KNNSearchEngine(data1, dictionary1)

    if tfidfs is not None and options.tau is not None:
        # precompute TF-IDF similarities
        print 'Computing item similarities in TF-IDF space. . .'
        simCache2 = TFIDF_SimilarityCache(
            tfidfs,
            shortCoeff=options.shortCoeff,
            bigramsCoeff=options.bigramsCoeff,
            hoodCoeff=options.hoodCoeff,
            useCosine=False
        )
        transformedItems1 =\
            [item for idx, item in sorted(transformedDictionary1.items(),
                                          key=lambda tup: tup[0])]
        items2 =\
            [item for idx, item in sorted(dictionary2.items(),
                                          key=lambda tup: tup[0])]
        simCache2.preComputeSims(transformedItems1, items2)
        if options.symmetric:
            simCache1 = TFIDF_SimilarityCache(
                tfidfs,
                shortCoeff=options.shortCoeff,
                bigramsCoeff=options.bigramsCoeff,
                hoodCoeff=options.hoodCoeff,
                useCosine=False
            )
            transformedItems2 =\
                [item for idx, item in sorted(transformedDictionary2.items(),
                                              key=lambda tup: tup[0])]
            items1 =\
                [item for idx, item in sorted(dictionary1.items(),
                                              key=lambda tup: tup[0])]
            simCache1.preComputeSims(transformedItems2, items1)

    # make predictions
    if popDictionary is not None and options.weightOut:
        # choose outgoing edge nodes based on popularity
        print 'Predicting edges (weighted outgoing). . .'
        totalPredictions = int(transformedData1.shape[1]*options.edgesPerNode)
        if options.symmetric:
            totalPredictions +=\
                int(transformedData2.shape[1]*options.edgesPerNode)
        totalPopularity = 0.0
        for i in range(transformedData1.shape[1]):
            totalPopularity += popDictionary[transformedDictionary1[i]]
        if options.symmetric:
            for i in range(transformedData2.shape[1]):
                totalPopularity += popDictionary[transformedDictionary2[i]]
        neighbors1 = []
        for i in range(transformedData1.shape[0]):
            numPredictions = int(round(
                totalPredictions*popDictionary[transformedDictionary1[i]]/\
                    totalPopularity
            ))
            if numPredictions > 0:
                # create addTerms dictionary
                if tfidfs is not None and options.tau is not None:
                    addTerms = dict(
                        [(dictionary2[idx],
                          options.tau*popDictionary[dictionary2[idx]]*sim)\
                         for (idx, sim) in enumerate(simCache2.sims[i,:])]
                    )
                else:
                    addTerms = None
                # compute edge predictions
                _, n = searchEngine2.kneighbors(
                    transformedData1[i,:],
                    numPredictions,
                    weights=popDictionary if options.weightIn else None,
                    addTerms=addTerms,
                    neighborLimit=options.neighborLimit
                )
                neighbors1.append(n[0])
            else:
                neighbors1.append([]) # place holder
        if options.symmetric:
            neighbors2 = []
            for i in range(transformedData2.shape[0]):
                numPredictions = int(round(
                    totalPredictions*popDictionary[transformedDictionary2[i]]/\
                        totalPopularity
                ))
                if numPredictions > 0:
                    # create addTerms dictionary
                    if tfidfs is not None and options.tau is not None:
                        addTerms = dict(
                            [(dictionary1[idx],
                              options.tau*popDictionary[dictionary1[idx]]*sim)\
                             for (idx, sim) in enumerate(simCache1.sims[i,:])]
                        )
                    else:
                        addTerms = None
                    # compute edge predictions
                    _, n = searchEngine1.kneighbors(
                        transformedData2[i,:],
                        numPredictions,
                        weights=popDictionary if options.weightIn else None,
                        addTerms=addTerms,
                        neighborLimit=options.neighborLimit
                    )
                    neighbors2.append(n[0])
                else:
                    neighbors2.append([]) # place holder
    else:
        # choose outgoing edge nodes uniformly
        print 'Predicting edges (uniform outgoing). . .'
        # TODO: Implement addTerm for uniform outgoing edge prediction
        _, neighbors1 = searchEngine2.kneighbors(
            transformedData1,
            int(options.edgesPerNode),
            weights=popDictionary if options.weightIn else None,
            neighborLimit=options.neighborLimit
        )
        if options.symmetric:
            _, neighbors2 = searchEngine1.kneighbors(
                transformedData2,
                int(options.edgesPerNode),
                weights=popDictionary if options.weightIn else None,
                neighborLimit=options.neighborLimit
            )

    # translate neighbors into edge predictions
    predicted_edges = makeEdges(neighbors1, transformedDictionary1)
    if options.symmetric:
        predicted_edges += makeEdges(neighbors2, transformedDictionary2)
        # remove duplicates
        predicted_edges = [(min(n1, n2), max(n1, n2)) for\
                           (n1, n2) in predicted_edges]
        predicted_edges = list(set(predicted_edges))

    # save results
    print 'Saving results to %s. . .' % options.savefile
    pickle.dump(predicted_edges, open(options.savefile, 'w'))

if __name__ == '__main__':
    main()
