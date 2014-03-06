#!/usr/local/bin/python

"""
Make csv containing product pairs for which we have the most information about
their similarity as per user-item collaborative filtering.
"""

from optparse import OptionParser
import sqlite3
import os
import csv

# params
outputFileTemplate = '%s.csv'

# db params
createSimilaritiesNumUsersIndexStmt =\
    ('CREATE INDEX IF NOT EXISTS Similarities_NumUsers_Idx ON '
     'Similarities(NumUsers)')
createStoreProductsProductIdIndexStmt =\
    ('CREATE INDEX IF NOT EXISTS StoreProducts_ProductId_Idx ON '
     'StoreProducts(ProductId)')
selectSimilaritiesStmt =\
    ('SELECT ProductId1, ProductId2, CosineSim, NumUsers '
     'FROM Similarities '
     'ORDER BY NumUsers DESC')
selectStoreProductsStmt =\
    'SELECT StoreId FROM StoreProducts WHERE ProductId = :ProductId'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-o', '--output-dir', dest='outputDir', default='output',
        help='Output directory.', metavar='DIR')
    parser.add_option('-l', '--limit', dest='limit', type='int', default=100,
        help='Limit to the number of edges made.', metavar='NUM')
    parser.add_option('-s', '--storeId', dest='storeId', type='int', default=1,
        help='StoreId from which to select edges.', metavar='ID')
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
        # create indexes if not already exists
        db_curs.execute(createSimilaritiesNumUsersIndexStmt)
        db_curs.execute(createStoreProductsProductIdIndexStmt)

    outputFileName = os.path.join(options.outputDir,
        outputFileTemplate % os.path.splitext(os.path.basename(__file__))[0])
    print 'Writing to %s . . .' % outputFileName
    with open(outputFileName, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        # fetch top similarity records
        num_writes = 0
        db_curs = db_conn.cursor()
        db_curs.execute(selectSimilaritiesStmt)
        for row in db_curs.fetchall():
            productId1 = row[0]
            productId2 = row[1]
            cosineSim = row[2]
            numUsers = row[3]
            # skip edges where both products are not in our store
            db_curs1 = db_conn.cursor()
            db_curs1.execute(selectStoreProductsStmt, (productId1,))
            if options.storeId not in [row[0] for row in db_curs1.fetchall()]:
                continue
            db_curs1.execute(selectStoreProductsStmt, (productId2,))
            if options.storeId not in [row[0] for row in db_curs1.fetchall()]:
                continue
            # output edge
            writer.writerow([productId1, productId2, cosineSim, numUsers])
            num_writes += 1
            if num_writes >= options.limit:
                break

if __name__ == '__main__':
    main()
