#!/usr/bin/env python

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import pickle
import os
import sys

def getParser():
    parser = OptionParser()
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--dictfname', dest='dictfname',
        default='data/tokens.dict',
        help='Dictionary that maps itemids to tokens.', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of items per topic to print.', metavar='NUM')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] <lda.pickle> <itemId>'
    parser = getParser()
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return
    items = args[1:]

    # get dictionary
    dictionary = corpora.Dictionary.load_from_text(options.dictfname)

    # load lda model
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # print item's topic mixture
    doc_bow = [(dictionary.token2id[item], 1) for item in items]
    print 'doc_bow =', doc_bow
    print model[doc_bow]

if __name__ == '__main__':
    main()
