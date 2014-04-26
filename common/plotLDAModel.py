#!/usr/bin/env python

from optparse import OptionParser
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
import sys

import LDA_util as lda

# params
saveFormat = 'jpg'

# db params
selectCategoryProductsStmt =\
   ('SELECT Id '
    'FROM Categories '
    'WHERE Category = :Category ')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--category', dest='category', default=None,
        help='Category to confine start of random walks.', metavar='CAT')
    parser.add_option('--bins', type='int', dest='bins', default=100,
        help='Number of bins in histograms.', metavar='NUM')
    parser.add_option('--savedir', dest='savedir', default=None,
        help='Directory to save figures in.', metavar='DIR')
    parser.add_option('--show', action='store_true', dest='show', default=False,
        help='Show plots.')
    return parser

def plotModel(model, items, numBins, savedir, show=False):
    print >> sys.stderr, 'Plot each topic distribution. . .'
    if items is not None:
        ids = [model.id2word.token2id[str(item)] for item in items\
               if str(item) in model.id2word.token2id]
    else:
        ids = None
    p_topic_given_item = lda.getTopicGivenItemProbs(model)
    first = True
    for topic in range(model.num_topics):
        if first:
            first = False
        else:
            plt.figure()
        if ids is not None:
            probs = [prob for ind, prob in\
                     enumerate(p_topic_given_item[topic,:]) if ind in ids]
        else:
            probs = p_topic_given_item[topic,:]
        print 'topic %d: mean=%f, min=%f, max=%f' %\
              (topic, np.mean(probs), min(probs), max(probs))
        n, bins, patches = plt.hist(probs, numBins)
        plt.savefig(os.path.join(savedir, 'topic%d.%s' % (topic, saveFormat)))
    if show:
        plt.show()

def main():
    # Parse options
    usage = 'Usage: %prog [options] <lda.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % modelfname
        return
    if options.savedir is None:
        savedir = os.getcwd()
    elif os.path.isdir(options.savedir):
        savedir = options.savedir
    else:
        print >> sys.stderr, 'ERROR: Cannot find dir: %s' % options.savedir
        return

    # load lda model
    print >> sys.stderr, 'Load LDA model. . .'
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # connect to db if confined to category
    if options.category is not None:
        if options.dbname is None:
            print >> sys.stderr,\
                'ERROR: Must provide --database if --category provided'
            return
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
        db_curs.execute(selectCategoryProductsStmt, (options.category,))
        items = [row[0] for row in db_curs.fetchall()]
    else:
        items = None

    # generate plots
    plotModel(model, items, options.bins, savedir, options.show)

if __name__ == '__main__':
    main()
