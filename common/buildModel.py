#!/usr/bin/env python

"""
Construct and save LDA model using Radim Rehurek's gensim module.
"""

from gensim import corpora, models, similarities
from gensim.models import ldamodel
from optparse import OptionParser
import logging
import pickle
import csv

def getParser():
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='filename',
        default='data/trainSessions.csv',
        help=('CSV file containing training data. Each line consists of tokens '
              'liked in a single session.'), metavar='FILE')
    parser.add_option('-d', '--dict-fname-in', dest='dict_fname_in',
        default='data/tokens.csv',
        help='File containing all tokens in the vocabulary.', metavar='FILE')
    parser.add_option('--dict-fname-out', dest='dict_fname_out',
        default='data/tokens.dict',
        help='Save file for dictionary that maps itemids to tokens.',
        metavar='FILE')
    parser.add_option('-l', '--lda-file', dest='lda_filename',
        default='data/lda.pickle', help='Save file for LDA model.',
        metavar='FILE')
    parser.add_option('-t', '--num-topics', dest='num_topics', type='int',
        default=100, help='Number of topics in LDA model.', metavar='NUM')
    parser.add_option('-p', '--passes', dest='passes', type='int', default=1,
        help='Number of passes for training LDA model.', metavar='NUM')
    parser.add_option('--alpha', dest='alpha', default='symmetric',
        help='Alpha param for gensim.LdaModel().', metavar='VAL')
    return parser

def buildDictionary(fname_in, fname_out):
    logging.info('Building dictionary from %s.' % fname_in)
    with open(fname_in) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
        dictionary = corpora.Dictionary(records)
        logging.info('Saving dictionary to %s.' % fname_out)
        dictionary.save_as_text(fname_out)
    return dictionary
            
def getCorpus(dictionary, filename):
    logging.info('Building training corpus from %s.' % filename)
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    return [dictionary.doc2bow(record) for record in records]

def buildLDA(dictionary, corpus, num_topics, passes, alpha):
    lda = ldamodel.LdaModel(corpus=corpus,
                            num_topics=num_topics,
                            id2word=dictionary,
                            chunksize=100,
                            passes=passes,
                            update_every=1,
                            alpha=alpha,
                            eta=None,
                            decay=0.5,
                            eval_every=10)
    return lda

def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                        level=logging.INFO)

    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # Construct dictionary
    dictionary = buildDictionary(options.dict_fname_in, options.dict_fname_out)

    # Construct corpus
    corpus = getCorpus(dictionary, options.filename)

    # Construct LDA Model
    lda = buildLDA(dictionary, corpus, options.num_topics, options.passes,
                   options.alpha)
    logging.info('Saving LDA model to %s.' % options.lda_filename)
    pickle.dump(lda, open(options.lda_filename, 'w'))

if __name__ == '__main__':
    main()
