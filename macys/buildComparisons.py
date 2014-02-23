#!/usr/local/bin/python

"""
Creates images of all pairs of items, side-by-side, for a particular category.
"""

import logging
import sqlite3
import os
from optparse import OptionParser
from ImageConcat import concatImageFiles

#params
selectProductsStmt = 'SELECT Id FROM Categories WHERE Category = :Category'
imageFileNameTemplate = 'images/%d.jpg'
compareImageFileNameTemplates = 'comparisons/%d_%d.jpg'

def getParser():
    parser = OptionParser()
    parser.add_option('-d', '--database', dest='dbname', default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-c', '--category', dest='category', default='Skirts',
        help='Category from which to generate item pairs.', metavar='CATEGORY')
    return parser

def buildComparison(itemA, itemB):
    infileA = imageFileNameTemplate % itemA
    infileB = imageFileNameTemplate % itemB
    if not os.path.isfile(infileA) or not os.path.isfile(infileB):
        logging.warning('Item image not found.')
        return 0
    outfile = compareImageFileNameTemplates % (itemA, itemB)
    concatImageFiles([infileA, infileB], outfile)
    return 1

def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # Connect to db
    logging.info('Connecting to database...')
    db_conn = sqlite3.connect(options.dbname)
    with db_conn:
        db_curs = db_conn.cursor()
        db_curs.execute(selectProductsStmt, (options.category,))
        # Read itemids into memory
        itemids = [row[0] for row in db_curs.fetchall()]
        for i in range(len(itemids)-1):
            for j in range(i+1, len(itemids)):
                buildComparison(itemids[i], itemids[j])

if __name__ == '__main__':
    main()
