#!/usr/local/bin/python

"""
Create and save an undirected graph from Recommends relations.
"""
import sqlite3
import pickle

# params
db_fname = 'macys.db'
save_fname = 'recDirectedGraph.pickle'

selectRecommendsStmt = 'SELECT Id1, Id2 FROM Recommends'

class Node(object):
    def __init__(self):
        self.inbound = []
        self.outbound = []

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
            graph[id1] = Node()
        graph[id1].outbound.append(id2)
        if id2 not in graph:
            node_cnt += 1
            graph[id2] = Node()
        graph[id2].inbound.append(id1)
        edge_cnt += 1
    print '%d nodes, %d edges' % (node_cnt, edge_cnt)
    return graph

def main():
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        graph = makeGraph(db_curs)
        pickle.dump(graph, open(save_fname, 'w'))

if __name__ == '__main__':
    main()
