#!/usr/bin/env python

"""
Create and save an undirected graph from Recommends relations.
"""

from optparse import OptionParser
import os
import sys
import sqlite3

# local modules
from Graph_util import saveGraph, getComponentLists, extractNodes

# db params
selectRecommendsStmt =\
    ('SELECT Id1, Id2 '
     'FROM Recommends')
selectCategoryRecommendsStmt =\
    ('SELECT R.Id1, R.Id2 '
     'FROM Recommends as R, '
     'Categories as C1, '
     'Categories as C2 '
     'WHERE C1.Id = R.Id1 '
     'AND C2.Id = R.Id2 '
     'AND C2.ParentCategory = C1.ParentCategory '
     'AND C2.Category = C1.Category '
     'AND C1.ParentCategory = :ParentCategory1 '
     'AND C1.Category = :Category1')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--savefile', dest='savefile', default='recGraph.pickle',
        help='Save file for pickled recommendation graph.', metavar='FILE')
    parser.add_option('--directed', action='store_true', dest='directed',
        default=False, help='Create a directed graph.')
    parser.add_option('--parent-category', dest='parentCategory', default=None,
        help='Confine graph to parent category.', metavar='PARCAT')
    parser.add_option('--category', dest='category', default=None,
        help='Confine graph to category.', metavar='CAT')
    parser.add_option('--min-component-size', type='int',
        dest='minComponentSize', default=5, help='Minimum component size.',
        metavar='NUM')
    return parser

def makeGraph(db_conn, parentCategory=None, category=None, directed=True):
    graph = {}
    node_cnt = 0
    edge_cnt = 0
    db_curs = db_conn.cursor()
    if parentCategory is not None and category is not None:
        db_curs.execute(selectCategoryRecommendsStmt,
                        (parentCategory, category))
    else:
        db_curs.execute(selectRecommendsStmt)
    for row in db_curs.fetchall():
        id1 = row[0]
        id2 = row[1]
        if id1 not in graph:
            node_cnt += 1
            graph[id1] = ([],[])
        if id2 not in graph[id1][0]:
            graph[id1][0].append(id2)
        if not directed and id2 not in graph[id1][1]:
            graph[id1][1].append(id2)
        if id2 not in graph:
            node_cnt += 1
            graph[id2] = ([],[])
        if id1 not in graph[id2][1]:
            graph[id2][1].append(id1)
        if not directed and id1 not in graph[id2][0]:
            graph[id2][0].append(id1)
        edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] database'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    dbname = args[0]
    if not os.path.isfile(dbname):
        parser.error('Cannot find %s' % dbname)

    print 'Connecting to %s. . .' % dbname
    db_conn = sqlite3.connect(dbname)

    # make graph
    print 'Making graph. . .'
    graph = makeGraph(db_conn, directed=options.directed,
                      parentCategory=options.parentCategory,
                      category=options.category)

    # Remove any components below minComponentSize
    component_lists = getComponentLists(graph)
    for component in component_lists:
        if len(component) < options.minComponentSize:
            extractNodes(graph, component)

    # save graph
    print 'Saving graph to %s. . .' % options.savefile
    saveGraph(graph, options.savefile)

if __name__ == '__main__':
    main()
