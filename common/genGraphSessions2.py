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

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
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
    usage = 'Usage: %prog [options] graph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        print >> sys.stderr, 'ERROR: Cannot find %s' % graphfname
        return

    # load recommendation graph
    graph = loadGraph(graphfname)

    # connect to db if confined to category
    if options.category is not None:
        if options.dbname is None:
            print >> sys.stderr,\
                'ERROR: Must provide --database if --category provided'
            return
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
    else:
        db_curs = None

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
