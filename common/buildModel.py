#!/usr/bin/env python

"""
Construct and save LDA model using Radim Rehurek's gensim module.
"""

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import pickle
import csv

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--file', dest='filename', default=None,
        help=('CSV file containing training data. Each line consists of tokens '
              'liked in a single session.'), metavar='FILE')
    parser.add_option('-l', '--lda-file', dest='lda_filename',
        default='lda.pickle', help='Save file for LDA model.',
        metavar='FILE')
    parser.add_option('-t', '--num-topics', dest='num_topics', type='int',
        default=10, help='Number of topics in LDA model.', metavar='NUM')
    parser.add_option('-p', '--passes', dest='passes', type='int', default=1,
        help='Number of passes for training LDA model.', metavar='NUM')
    parser.add_option('--alpha', dest='alpha', default='symmetric',
        help='Alpha param for gensim.LdaModel().', metavar='VAL')
    return parser

def getDictFromDocs(filename):
    termDict = {}
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        for record in reader:
            for term in record:
                termDict[term] = 1
    terms = [[term] for term in termDict.keys()]
    return corpora.Dictionary(terms)
            
def getCorpusFromDocs(filename, dictionary):
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    corpus = [dictionary.doc2bow(record) for record in records]
    return corpus

def buildModel(corpus, dictionary, num_topics, passes, alpha):
    model = ldamodel.LdaModel(corpus=corpus,
                            num_topics=num_topics,
                            id2word=dictionary,
                            chunksize=100,
                            passes=passes,
                            update_every=1,
                            alpha=alpha,
                            eta=None,
                            decay=0.5,
                            eval_every=10)
    return model

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # Build dictionary
    print 'Building dictionary from %s. . .' % options.filename
    dictionary = getDictFromDocs(options.filename)

    # Construct corpus
    print 'Building corpus from %s. . .' % options.filename
    corpus = getCorpusFromDocs(options.filename, dictionary)

    # Train LDA Model
    print 'Training model. . .'
    model = buildModel(corpus, dictionary, options.num_topics, options.passes,
                       options.alpha)

    # Save LDA Model
    print 'Saving model to %s. . .' % options.lda_filename
    pickle.dump(model, open(options.lda_filename, 'w'))

if __name__ == '__main__':
    main()
