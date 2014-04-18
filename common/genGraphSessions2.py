#!/usr/bin/env python

from optparse import OptionParser
from collections import deque
import pickle
import csv
import sqlite3
import os
import sys

# db_params
selectCategoryItemStmt =\
   ('SELECT Id '
    'FROM Categories '
    'WHERE Category = :Category ')

def getParser():
    parser = OptionParser()
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-g', '--graph', dest='graphfilename',
        default='data/recDirectedGraph.pickle',
        help='Name of picked directed graph.', metavar='FILE')
    parser.add_option('-o', '--output', dest='outfilename',
        default='data/recGraphSessions.csv', help='Name of output csv file.',
        metavar='FILE')
    parser.add_option('-l', type='int', dest='l', default=1,
        help='Max distance in graph from source.', metavar='NUM')
    parser.add_option('--category', dest='category', default=None,
        help='Category to confine start of random walks.', metavar='CAT')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def limitedBFS(graph, source, l):
    assert(l > 0)
    visited = []
    q = deque()
    q.appendleft((source, 0))
    while q:
        (n, d) = q.pop()
        visited.append(n)
        if d < l:
            for neighbor in graph[n][0]:
                q.appendleft((neighbor, d+1))
    return visited

def main():
    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # connect to db if confined to category
    if options.category is not None:
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
    else:
        db_curs = None

    # load recommendation graph
    graph = loadGraph(options.graphfilename)

    # generate and write sessions
    with open(options.outfilename, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        if db_curs is not None and options.category is not None:
            db_curs.execute(selectCategoryItemStmt, (options.category,))
            for row in db_curs.fetchall():
                item = int(row[0])
                if item in graph:
                    session = limitedBFS(graph, item, options.l)
                    writer.writerow(session)
        else:
            for item in graph:
                session = limitedBFS(graph, item, options.l)
                writer.writerow(session)
        
if __name__ == '__main__':
    main()
