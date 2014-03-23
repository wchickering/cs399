#!/usr/local/bin/python

"""
Partitions Products in sqlite3 database by assigning StoreId values
based upon given paramaters.
"""

from optparse import OptionParser
import sqlite3
import random 

# db params
dropStoresTableStmt = 'DROP TABLE IF EXISTS Stores'
dropStoreProductsTableStmt = 'DROP TABLE IF EXISTS StoreProducts'
createStoresTableStmt =\
    'CREATE TABLE Stores(StoreId INT PRIMARY KEY, Name TEXT)'
createStoreProductsTableStmt =\
    ('CREATE TABLE StoreProducts(StoreId INT, ProductId INT, PRIMARY '
     'KEY(StoreId, ProductId), '
     'FOREIGN KEY(StoreId) REFERENCES Stores(StoreId), '
     'FOREIGN KEY(ProductId) REFERENCES Products(ProductId))')
insertStoreStmt = 'INSERT INTO Stores (StoreId) VALUES (:StoreId)'
selectProductsStmt = 'SELECT ProductId FROM Products'
insertStoreProductStmt =\
    ('INSERT INTO StoreProducts (StoreId, ProductId) '
     'VALUES (:StoreId, :ProductId)')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname',
        default='data/amazon.db', help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-n', '--numStores', dest='numStores', type='int',
        default=2, help='Number of StoreId values.', metavar='NUM')
    parser.add_option('-r', '--ratios', dest='ratios', default='1:1',
        help=('Ratios of products per store. For example, "2:1" indicates that '
              'store 1 has a product catalog that is twice the size of store '
              '2\'s.'), metavar='RATIOS')
    parser.add_option('-o', '--overlap', dest='overlap', type='float',
        default=0.0, help='Fraction of products in multiple stores.',
        metavar='OVERLAP')
    return parser

def getRanges(ratios):
    fractions = [float(r)/sum(ratios) for r in ratios]
    last = 0.0
    ranges = []
    for i in range(len(fractions)):
        ranges.append(last + fractions[i])
        last += fractions[i]
    return ranges

def getRandomId(ranges):
    r = random.random()
    for i in range(len(ranges)):
        if ranges[i] >= r:
            return i+1
    raise ValueError('invalid ranges')

def main():
    # Parse options
    usage = 'Usage: %prog [options]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if options.numStores <= 0:
        parser.error('Number of StoreIds must be positive.')
    try:
        ratios = [int(r) for r in options.ratios.split(':')]
    except:
        parser.error('Invalid ratios string.')
    if len(ratios) != options.numStores:
        parser.error('Number of StoreIds and ratios must be equal.')
    if options.overlap < 0.0:
        parser.error('Overlap cannot be negative.')

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # drop Stores table
        db_curs.execute(dropStoresTableStmt)
        # drop StoreProducts table
        db_curs.execute(dropStoreProductsTableStmt)
        # create Stores table 
        db_curs.execute(createStoresTableStmt)
        # create StoreProducts table 
        db_curs.execute(createStoreProductsTableStmt)

        # insert Stores relations
        for i in range(options.numStores):
            db_curs.execute(insertStoreStmt, (i+1,))

        # choose StoreProducts
        ranges = getRanges(ratios)
        db_curs.execute(selectProductsStmt)
        for row in db_curs.fetchall():
            productId = row[0]
            storeId = getRandomId(ranges)
            db_curs2 = db_conn.cursor()
            db_curs2.execute(insertStoreProductStmt, (storeId, productId))
            stores = [storeId]
            while len(stores) < options.numStores:
                if random.random() > options.overlap:
                    break
                else:
                    while True:
                        storeId = getRandomId(ranges)
                        if storeId not in stores:
                            stores.append(storeId)
                            break
                    db_curs2.execute(insertStoreProductStmt,
                                     (storeId, productId))

if __name__ == '__main__':
    main()
