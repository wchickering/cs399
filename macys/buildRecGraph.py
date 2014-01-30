#!/usr/local/bin/python

"""
Create and save an undirected graph from Recommends relations.
"""
import sqlite3
import pickle

# params
db_fname = 'macys.db'
save_fname = 'recGraph.pickle'

selectRecommendsStmt = 'SELECT Id1, Id2 FROM Recommends'

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
            edge_cnt += 1
            graph[id1] = set([id2,])
        elif id2 not in graph[id1]:
            edge_cnt += 1
            graph[id1].add(id2)
        if id2 not in graph:
            node_cnt += 1
            graph[id2] = set([id1,])
        elif id1 not in graph[id2]:
            edge_cnt += 1
            graph[id2].add(id1)
    assert(edge_cnt % 2 == 0)
    edge_cnt = edge_cnt/2
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
