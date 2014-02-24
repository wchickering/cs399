#!/usr/local/bin/python

"""
Generates and saves a directed weighted graph from Similarities
relations according to given parameters.
"""

from optparse import OptionParser
import operator
import sqlite3
import pickle
import sys

# params
displayInterval = 1000

# db params
selectProductsStmt = 'SELECT ProductId FROM Products ORDER BY ProductId'
selectSimilaritiesStmt =\
    ('SELECT ProductId1, ProductId2, CosineSim, NumUsers '
     'FROM Similarities WHERE '
     'CosineSim >= :MinCosineSim AND '
     'ExtJaccard >= :MinExtJaccard AND '
     'NumUsers >= :MinNumUsers '
     'ORDER BY CosineSim DESC, NumUsers DESC')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='data/amazon.db',
        help='sqlite3 database file.',
        metavar='FILE')
    parser.add_option('-o', '--outfile', dest='outfilename', default='data/graph.pickle',
        help='Output filename for pickled graph.',
        metavar='FILE')
    parser.add_option('-w', '--weight', dest='weight', type='int', default=1,
        help='Indicates whether graph is weighted (1) or unweighted (0).',
        metavar='WEIGHT')
    parser.add_option('-k', '--numEdges', dest='k', type='int', default=sys.maxint,
        help='Maximum number of outgoing edges per node.',
        metavar='K')
    parser.add_option('--minCosineSim', dest='minCosineSim', type='float',
        default=0.0, help='Minimum Cosine Similarity associated with edges.',
        metavar='SIM')
    parser.add_option('--minExtJaccard', dest='minExtJaccard', type='float',
        default=0.0, help='Minimum Extended Jaccard Similarity associated with edges.',
        metavar='SIM')
    parser.add_option('--minNumUsers', dest='minNumUsers', type='int',
        default=0, help='Minimum Number of Users associated with edges.',
        metavar='NUM')
    return parser

def saveGraph(graph, filename):
    pickle.dump(graph, open(filename, 'w'))

def addDirectedEdge(graph, node1, node2, weight):
    if node1 not in graph:
        graph[node1] = {}
    graph[node1][node2] = weight

def truncateEdges(graph, k):
    count = 0
    for node1 in graph:
        count += 1
        node1Edges = graph[node1]
        if len(node1Edges) > k:
            sortedEdges = sorted(node1Edges.iteritems(), key=operator.itemgetter(1), reverse=True)
            del sortedEdges[k:]
            graph[node1] = dict(sortedEdges);
        if count % displayInterval == 0:
            print '%d Edges Processed' % count

def printGraph(graph):
    numLines = 100
    count = 0
    for node1 in graph:
        count += 1
        if count > numLines:
            return
        print 'Node1: ' + node1
        for node2 in graph[node1]:
            print '  Node2: ' + node1 + '  Weight: ' + str(graph[node1][node2])

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs1 = db_conn.cursor()
        graph = {}
        count = 0
        db_curs1.execute(selectSimilaritiesStmt,
                          (options.minCosineSim,
                          options.minExtJaccard,
                          options.minNumUsers))
        for row in db_curs1.fetchall():
            count += 1
            productId1 = row[0]
            productId2 = row[1]
            cosineSim = row[2]
            numUsers = row[3]
            if options.weight:
                weight = cosineSim
            else:
                weight = 1
            addDirectedEdge(graph, productId1, productId2, weight)
            if count % displayInterval == 0:
                print '%d Edges Processed' % count
        print 'Truncating Graph...'
        truncateEdges(graph, options.k)
    print 'Saving Graph...'
    saveGraph(graph, options.outfilename)
    print 'Printing Graph...'
    printGraph(graph)

#        db_curs1.execute(selectProductsStmt)
#        for row in db_curs1.fetchall():
#            productId = row[0]
#            count += 1
#            db_curs2 = db_conn.cursor()
#            db_curs2.execute(selectSimilaritiesStmt,
#                             (productId,
#                              options.minCosineSim,
#                              options.minExtJaccard,
#                              options.minNumUsers))
#            for row in db_curs2.fetchall():
#                productId1 = row[0]
#                productId2 = row[1]
#                cosineSim = row[2]
#                numUsers = row[3]
#                if productId1 == productId:
#                    productIdB = productId2
#                else:
#                    productIdB = productId1
#
#                if options.weight:
#                    weight = cosineSim
#                else:
#                    weight = 1
#                addDirectedEdge(graph, productId, productIdB, weight)
#            if count % displayInterval == 0:
#                print '%d Nodes Processed' % count
#    saveGraph(graph, options.outfilename)

if __name__ == '__main__':
    main()
