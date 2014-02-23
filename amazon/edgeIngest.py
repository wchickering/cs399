#!/usr/local/bin/python

"""
Import edges from csv into sqlite3 database.
Edges in file assumed to be all those with nonzero
similarity as per user-item collaborative filtering.
"""

from optparse import OptionParser
import sqlite3
import os
import math

# db params
commitInterval = 1000
createSimilaritiesTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Similarities(ProductId1 INT, ProductId2 INT, '
     'CosineSim REAL, ExtJaccard REAL, NumUsers INT, PRIMARY KEY(ProductId1, '
     'ProductId2), FOREIGN KEY(ProductId1) REFERENCES Products(ProductId), '
     'FOREIGN KEY(ProductId2) REFERENCES Products(ProductId))')
selectReviewsStmt =\
    ('SELECT UserId, Score FROM Reviews WHERE ProductId = :ProductId '
     'ORDER BY UserId')
selectSimilarityStmt =\
    ('SELECT * FROM Similarities WHERE ProductId1 = :ProductId1 AND '
     'ProductId2 = :ProductId2')
insertSimilarityStmt =\
    ('INSERT INTO Similarities (ProductId1, ProductId2, CosineSim, '
     'ExtJaccard, NumReviews) VALUES (:ProductId1, :ProductId2, :CosineSim, '
     ':ExtJaccard, :NumUsers)')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='amazon.db',
        help='sqlite3 database file.', metavar='FILE')
    return parser

def calcSim(scoresA, scoresB):
    """Compute Cosine similarity of sparse vectors in O(n),
       where n is the max nonzero elements of the two vectors.
    """
    count = 0
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
            count += 1
            innerProd += scoresA[i][1]*scoresB[j][1]
            varA += scoresA[i][1]**2
            varB += scoresB[j][1]**2
            i += 1
            j += 1
    if innerProd == 0:
        return (0, 0, count)
    else:
        cosineSim = innerProd/(math.sqrt(varA)*math.sqrt(varB))
        extJaccard = innerProd/(varA + varB - innerProd)
        return (cosineSim, extJaccard, count)

def main():
    # Parse options
    usage = 'Usage: %prog [options] <csvfile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create Similarities table if not already exists
        db_curs.execute(createSimilaritiesTableStmt)

        with open(inputfilename, 'r') as inputfile:
            num_inserts = 0
            for line in inputfile:
                tokens = line.split(',')
                productId1 = tokens[0].strip()
                productId2 = tokens[1].strip()
                db_curs.execute(selectSimilarityStmt, (productId1, productId2))
                if not db_curs.fetchone():
                    db_curs.execute(selectReviewsStmt, (productId1,))
                    scores1 = [(row[0], row[1]) for row in db_curs.fetchall()]
                    db_curs.execute(selectReviewsStmt, (productId2,))
                    scores2 = [(row[0], row[1]) for row in db_curs.fetchall()]
                    cosineSim, extJaccard, numUsers = calcSim(scores1, scores2)
                    if cosineSim == 0:
                        print 'WARNING: Zero cosineSim encountered.'
                    if extJaccard == 0:
                        print 'WARNING: Zero extJaccard encountered.'
                    db_curs.execute(insertSimilarityStmt,
                                    (productId1, productId2, cosineSim,
                                     extJaccard, numUsers))
                    num_inserts += 1
                    if num_inserts % commitInterval == 0:
                        db_conn.commit()
    print '%d Similarities inserted.' % num_inserts

if __name__ == '__main__':
    main()
