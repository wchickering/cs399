#!/usr/local/bin/python

"""
Create and save an undirected graph from Recommends relations.
"""
import sqlite3
import pickle
from optparse import OptionParser

selectRecommendsStmt = 'SELECT Id1, Id2 FROM Recommends'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='sqlite3 database file containing Recommends table.', metavar='FILE')
    parser.add_option('-o', '--output', dest='outfilename', default='recGraph.pickle',
        help='Output pickle file containing recommendation graph.', metavar='OUT_FILE')
    return parser

def makeGraph(db_curs):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    db_curs.execute(selectRecommendsStmt)
    for row in db_curs.fetchall():
        id1 = row[0]
        id2 = row[1]
        if id1 not in graph:
            node_cnt += 1
            graph[id1] = set([id2,])
        elif id2 not in graph[id1]:
            graph[id1].add(id2)
        if id2 not in graph:
            node_cnt += 1
            graph[id2] = set([id1,])
        elif id1 not in graph[id2]:
            graph[id2].add(id1)
        edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] -d database'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if not options.dbname:
        parser.error('Database required')

    db_conn = sqlite3.connect(options.dbname)
    with db_conn:
        db_curs = db_conn.cursor()
        graph = makeGraph(db_curs)
        pickle.dump(graph, open(options.outfilename, 'w'))

if __name__ == '__main__':
    main()
