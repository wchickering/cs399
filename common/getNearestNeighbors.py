#!/usr/bin/env python

"""
Displays the N nearest neighbors of a particular item within an LDA/LSI model.
"""

from optparse import OptionParser
import pickle
import os
import sys
import numpy as np

# local modules
from KNNSearchEngine import KNNSearchEngine
from SessionTranslator import SessionTranslator
import LDA_util as lda
import LSI_util as lsi

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--ldafile', dest='ldafile', default=None,
        help='Pickled LDA model.', metavar='FILE')
    parser.add_option('--lsifile', dest='lsifile', default=None,
        help='NPZ file of SVD products.', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of nearest neighbors to display.', metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <--ldafile=FILE | --lsifile=FILE> item'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    item = int(args[0])
    if options.ldafile is None and options.lsifile is None:
        parser.error(('Must provide either an LDA (--ldafile) or LSI '
                      '(--lsifile) model.'))

    # load model
    if options.ldafile is not None:
        # process LDA model
        if not os.path.isfile(options.ldafile):
            parser.error('Cannot find %s' % options.ldafile)
        print >> sys.stderr, 'Load LDA model from %s. . .' % options.ldafile
        with open(options.ldafile, 'r') as f:
            ldamodel = pickle.load(f)
        dictionary = {}
        for i, item in ldamodel.id2word.items():
            dictionary[i] = int(item)
        data = lda.getTopicGivenItemProbs(ldamodel).transpose()
    else:
        # process LSI model
        if not os.path.isfile(options.lsifile):
            parser.error('Cannot find %s' % options.lsifile)
        print >> sys.stderr, 'Load LSI model from %s. . .' % options.lsifile
        npzfile = np.load(options.lsifile)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        items = npzfile['dictionary']
        dictionary = {}
        for i in range(len(items)):
            dictionary[i] = int(items[i])
        data = lsi.getTermConcepts(u, s).transpose()

    # build search engine
    searchEngine = KNNSearchEngine(data, dictionary)

    # get translator
    if options.dbname is not None:
        translator = SessionTranslator(options.dbname)
    else:
        translator = None

    # get neighbors
    distances, neighbors =\
        searchEngine.kneighborsByName([item], n_neighbors=options.topn)

    # display top N destinations
    name = None
    if translator is not None:
        description = translator.sessionToDesc([item])[0]
        name = '(%d) %s' % (item, description)
    if name is None:
        name = '%d' % item
    print 'nghbr: dist for %s (top %d)' % (name, options.topn)
    for i in range(len(neighbors[0])):
        neighbor = int(neighbors[0][i])
        distance = distances[0][i]
        name = None
        if translator is not None:
            description = translator.sessionToDesc([neighbor])[0]
            name = '(%d) %s' % (neighbor, description)
        if name is None:
            name = '%d' % neighbor
        print '%s: %.2e' % (name, distance)

if __name__ == '__main__':
    main()
