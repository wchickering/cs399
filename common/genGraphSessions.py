#!/usr/bin/env python

from RoundRobinBFS_directed import roundRobinBFS
from CleanSources import cleanSources

from optparse import OptionParser
from collections import deque
import pickle
import csv
import random
import sqlite3
import os
import sys

# local modules
from Graph_util import loadGraph

# db_params
selectRandomItemStmt =\
   ('SELECT Id '
    'FROM Categories '
    'WHERE Category = :Category '
    'ORDER BY random() LIMIT 1')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname', default=None,
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-o', '--output', dest='outfilename',
        default='data/recGraphSessions.csv', help='Name of output csv file.',
        metavar='FILE')
    parser.add_option('--seed', type='int', dest='seed', default=0,
        help='Seed for random number generator.', metavar='NUM')
    parser.add_option('-p', type='float', dest='p', default=0.05,
        help='Probability of terminating session after each trial.',
        metavar='FLOAT')
    parser.add_option('-n', '--num', type='int', dest='num', default=1000,
        help='Number of sessions to generate.', metavar='NUM')
    parser.add_option('--category', dest='category', default=None,
        help='Category to confine start of random walks.', metavar='CAT')
    return parser

def genSession(graph, p, db_curs=None, category=None):
    session = []
    sources = deque()

    # randomly choose a starting point on the graph
    if db_curs is not None and category is not None:
        while True:
            db_curs.execute(selectRandomItemStmt, (category,))
            item = int(db_curs.fetchone()[0])
            if item in graph:
                break
    else:
        item = random.choice(graph.keys())
    session.append(item)
    sources.appendleft(item)

    # begin traversing graph
    while True:
        if random.random() < p:
            break
        sources = cleanSources(graph, sources, session)
        if not sources:
            break
        # randomly choose a source
        s = [random.choice(sources)]
        items = roundRobinBFS(graph, s, session, 1)
        session += items
        for item in items:
            sources.appendleft(item)

    return session

def main():
    # Parse options
    usage = 'Usage: %prog [options] graph.pickle'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    graphfname = args[0]
    if not os.path.isfile(graphfname):
        parser.error('Cannot find %s' % graphfname)

    # load recommendation graph
    graph = loadGraph(graphfname)

    # seed rng
    random.seed(options.seed)

    # connect to db if confined to category
    if options.category is not None:
        if options.dbname is None:
            parser.error('Must provide --database if --category provided')
        db_conn = sqlite3.connect(options.dbname)
        db_curs = db_conn.cursor()
    else:
        db_curs = None

    # generate and write sessions
    with open(options.outfilename, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(options.num):
            session = genSession(graph, options.p, db_curs=db_curs,
                                 category=options.category)
            writer.writerow(session)
        
if __name__ == '__main__':
    main()
