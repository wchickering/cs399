#!/usr/local/bin/python

"""
Computes the biases associated with the dataset, each user, and each item and
stores them in the database.
"""

from optparse import OptionParser
import sqlite3

# db params
createGlobalsTableStmt =\
    'CREATE TABLE IF NOT EXISTS Globals(Key TEXT PRIMARY KEY, Value TEXT)'
deleteGlobalStmt = 'DELETE FROM Globals WHERE Key = :Key'
insertGlobalStmt = 'INSERT INTO Globals (Key, Value) VALUES (:Key, :Value)'
selectAvgScoreStmt = 'SELECT avg(Score) FROM Reviews'
dropUserBiasesTableStmt = 'DROP TABLE IF EXISTS UserBiases'
createUserBiasesTableStmt =\
    ('CREATE TABLE UserBiases (UserId TEXT PRIMARY KEY, Bias Real, FOREIGN '
     'KEY(UserId) REFERENCES Users(UserId))')
insertUserBiasesStmt =\
    ('INSERT INTO UserBiases (UserId, Bias) '
     'SELECT UserId, Avg(Score) - :GlobalBias '
     'FROM Users NATURAL JOIN Reviews '
     'GROUP BY UserId')
dropProductBiasesTableStmt = 'DROP TABLE IF EXISTS ProductBiases'
createProductBiasesTableStmt =\
    ('CREATE TABLE ProductBiases (ProductId TEXT PRIMARY KEY, Bias Real, '
     'FOREIGN KEY (ProductId) REFERENCES Products(ProductId))')
insertProductBiasesStmt =\
    ('INSERT INTO ProductBiases (ProductId, Bias) '
     'SELECT ProductId, Avg(Score) - :GlobalBias '
     'FROM Products NATURAL JOIN Reviews '
     'GROUP BY ProductId')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
                      default='data/amazon.db', help='sqlite3 database file.',
                      metavar='FILE')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create Globals table if not already exists
        db_curs.execute(createGlobalsTableStmt)
        # delete any peexisting Bias from Globals table 
        db_curs.execute(deleteGlobalStmt, ('Bias',))
        # compute global bias
        db_curs.execute(selectAvgScoreStmt)
        globalBias = float(db_curs.fetchone()[0])
        print 'Global Bias = %.2f' % globalBias
        # insert global bias into db
        db_curs.execute(insertGlobalStmt, ('Bias', str(globalBias)))
        # drop UserBiases table if exists
        db_curs.execute(dropUserBiasesTableStmt)
        # create UserBiases table
        db_curs.execute(createUserBiasesTableStmt)
        # compute and insert UserBiases
        db_curs.execute(insertUserBiasesStmt, (globalBias,))
        # drop ProductBiases table if exists
        db_curs.execute(dropProductBiasesTableStmt)
        # create ProductBiases table
        db_curs.execute(createProductBiasesTableStmt)
        # compute and insert ProductBiases
        db_curs.execute(insertProductBiasesStmt, (globalBias,))

if __name__ == '__main__':
    main()

