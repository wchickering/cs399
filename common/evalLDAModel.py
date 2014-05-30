#!/usr/bin/env python

from optparse import OptionParser
import csv
import pickle
import os
import sys

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def getCorpus(model, filename):
    with open(filename) as csvIn:
        reader = csv.reader(csvIn)
        records = [record for record in reader]
    return [model.id2word.doc2bow(record) for record in records]

def main():
    # Parse options
    usage = 'Usage: %prog [options] lda.pickle testdocs'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return
    testfname = args[1]
    if not os.path.isfile(testfname):
        print >> sys.stderr, 'Cannot find %s' % testfname
        return

    # load lda model
    print 'Loading LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get test corpus
    print 'Loading test corpus. . .'
    corpus = getCorpus(model, testfname)

    # print lower bound on perplexity
    print 'Perplexity lower bound (model.bound()):', model.bound(corpus)
    print 'Per word perplexity bound (model.log_perplexity()):',\
          model.log_perplexity(corpus)

if __name__ == '__main__':
    main()

