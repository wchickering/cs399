#!/usr/bin/env python

"""
Extract subgraph from directed graph consisting of nodes associated with a
category.
"""

from optparse import OptionParser
import pickle
import os
import sys
import sqlite3

# db params
selectCategoryProductsStmt =\
    ('SELECT Id '
     'FROM Categories '
     'WHERE parentCategory = :parentCategory '
     'AND category = :category')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-o', '--output', dest='outfilename',
        default='categoryGraph.pickle',
        help='Output pickle file containing category graph.',
        metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

# assumes graph is self-consistent
def extractSubGraph(graph, selectNodes):
    subgraph = {}
    for node in graph:
        if node in selectNodes:
            subgraph[node] = ([n for n in graph[node][0] if n in selectNodes],\
                              [n for n in graph[node][1] if n in selectNodes])
    return subgraph

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph.pickle parentCategory category'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % graphfname
        return
    parentCategory = args[1]
    category = args[2]

    # connect to db
    print 'Connecting to %s. . .' % options.dbname
    db_conn = sqlite3.connect(options.dbname)
    db_curs = db_conn.cursor()

    # get category items
    db_curs.execute(selectCategoryProductsStmt, (parentCategory, category))
    catItems = set([int(row[0]) for row in db_curs.fetchall()])
    print '%d items found in category: %s, %s' %\
          (len(catItems), parentCategory, category)

    # load graph
    print 'Loading graph from %s. . .' % graphfname
    graph = loadGraph(graphfname)

    # extract graph
    print 'Extracting category graph. . .'
    subgraph = extractSubGraph(graph, catItems)

    # save graph
    print 'Saving category graph to %s. . .' % options.outfilename
    pickle.dump(subgraph, open(options.outfilename, 'w'))

if __name__ == '__main__':
    main()

