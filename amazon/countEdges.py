#!/usr/local/bin/python

"""
Counts the edges with non-zero weight in an otherwise complete
weighted product graph constructed via user-item collaborative filtering.
"""

from optparse import OptionParser
import sqlite3
import math
import sys

# db params
selectProductsStmt = 'SELECT ProductId FROM Products ORDER BY ProductId'
selectUserScoresStmt =\
    ('SELECT UserId, Score FROM Reviews WHERE ProductId = :ProductId '
     'ORDER BY UserId')
selectOtherProductsStmt =\
    ('SELECT ProductId FROM Products WHERE ProductId > :ProductId '
     'ORDER BY ProductId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='data/amazon.db',
        help='sqlite3 database file.', metavar='FILE')
    return parser

def cosSim(scoresA, scoresB):
    """Compute Cosine similarity of sparse vectors in O(n),
       where n is the max nonzero elements of the two vectors.
    """
    innerProd = 0
    varA = 0
    varB = 0
    i = 0
    j = 0
    while i < len(scoresA) and j < len(scoresB):
        if scoresA[i][0] < scoresB[j][0]:
            varA += scoresA[i][1]**2
            i += 1
        elif scoresA[i][0] > scoresB[j][0]:
            varB += scoresB[j][1]**2
            j += 1
        else:
            innerProd += scoresA[i][1]*scoresB[j][1]
            varA += scoresA[i][1]**2
            varB += scoresB[j][1]**2
            i += 1
            j += 1
    if innerProd == 0:
        return 0
    else:
        score = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        return score

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        num_edges = 0
        updateEvery = 10000000
        count = 0
        db_curs1 = db_conn.cursor()
        db_curs1.execute(selectProductsStmt)
        for row1 in db_curs1.fetchall():
            idA = row1[0]
            db_curs2 = db_conn.cursor()
            db_curs2.execute(selectUserScoresStmt, (idA,))
            scoresA = [(row[0], row[1]) for row in db_curs2.fetchall()]
            db_curs2.execute(selectOtherProductsStmt, (idA,))
            for row2 in db_curs2.fetchall():
               idB = row2[0]
               db_curs3 = db_conn.cursor()
               db_curs3.execute(selectUserScoresStmt, (idB,))
               scoresB = [(row[0], row[1]) for row in db_curs3.fetchall()]
               similarity = cosSim(scoresA, scoresB)
               count += 1
               if similarity > 0:
                   num_edges += 1
               if count % updateEvery == 0:
                   print 'count =', count
    print 'Number of Edges = %d' % num_edges

if __name__ == '__main__':
    main()
