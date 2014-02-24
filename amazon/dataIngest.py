#!/usr/local/bin/python

"""
Import SNAP Amazon reviews data found at:
http://snap.stanford.edu/data/web-Amazon-links.html
into sqlite3 database.
"""

import os
import sys
from optparse import OptionParser
import sqlite3

# db params
createProductsTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Products(ProductId TEXT PRIMARY KEY, Title TEXT, '
     ' Price TEXT)')
createCategoriesTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Categories(ProductId TEXT, Category TEXT, '
     'PRIMARY KEY (ProductId, Category), FOREIGN KEY(ProductId) REFERENCES '
     'Products(ProductId))')
createUsersTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Users(UserId TEXT PRIMARY KEY, '
     'ProfileName TEXT)')
createReviewsTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Reviews(ProductId TEXT, UserId TEXT, '
     'Helpfulness TEXT, Score REAL, Time INT, Summary TEXT, Text TEXT, '
     'PRIMARY KEY (ProductId, UserId), FOREIGN KEY(ProductId) REFERENCES '
     'Products(ProductId), FOREIGN KEY(UserId) REFERENCES Users(UserId))')
selectProductStmt = 'SELECT * FROM Products WHERE ProductId = :ProductId'
insertProductStmt =\
    ('INSERT INTO Products (ProductId, Title, Price, StoreId) VALUES '
     '(:ProductId, :Title, :Price)')
selectCategoryStmt =\
    ('SELECT * FROM Categories WHERE ProductId = :ProductId AND '
     'Category = :Category')
insertCategoryStmt =\
    ('INSERT INTO Categories (ProductId, Category) VALUES (:ProductId, '
     ':Category)')
selectUserStmt = 'SELECT * FROM Users WHERE UserId = :UserId'
insertUserStmt =\
    'INSERT INTO Users (UserId, ProfileName) VALUES (:UserId, :ProfileName)'
selectReviewStmt =\
    'SELECT * FROM Reviews WHERE ProductId = :ProductId AND UserId = :UserId'
insertReviewStmt =\
    ('INSERT INTO Reviews (ProductId, UserId, Helpfulness, Score, Time, '
     'Summary, Text) VALUES (:ProductId, :UserId, :Helpfulness, :Score, '
     ':Time, :Summary, :Text)')

# global counters
products_inserted = 0
categories_inserted = 0
users_inserted = 0
reviews_inserted = 0

class ProductReview(object):
    def __init__(self):
        self.productId = None
        self.title = None
        self.price = None
        self.userId = None
        self.profileName = None
        self.helpfulness = None
        self.score = None
        self.time = None
        self.summary = None
        self.text = None

    def setAttr(self, attribute, value):
        if attribute == 'productId':
            self.productId = value
        elif attribute == 'title':
            self.title = value
        elif attribute == 'price':
            self.price = value
        elif attribute == 'userId':
            self.userId = value
        elif attribute == 'profileName':
            self.profileName = value
        elif attribute == 'helpfulness':
            self.helpfulness = value
        elif attribute == 'score':
            self.score = float(value)
        elif attribute == 'time':
            self.time = int(value)
        elif attribute == 'summary':
            self.summary = value
        elif attribute == 'text':
            self.text = value
        else:
            raise ValueError('Unrecognized attribute: %s' % attribute)

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='db_fname', default='data/amazon.db',
        help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-c', '--category', dest='category', default=None,
        help='Category of products in datafile.', metavar='FILE')
    return parser

def importProductReview(db_curs, category, pr):
    global products_inserted
    global categories_inserted
    global users_inserted
    global reviews_inserted
    # ignore reviews by 'unknown' users
    if pr.userId == 'unknown':
        return
    # insert product if not already in db
    db_curs.execute(selectProductStmt, (pr.productId,))
    if not db_curs.fetchone():
        db_curs.execute(insertProductStmt, (pr.productId, pr.title, pr.price))
        products_inserted += 1
    # insert category if not already in db
    db_curs.execute(selectCategoryStmt, (pr.productId, category))
    if not db_curs.fetchone():
        db_curs.execute(insertCategoryStmt, (pr.productId, category))
        categories_inserted += 1
    # insert user if not already in db
    db_curs.execute(selectUserStmt, (pr.userId,))
    if not db_curs.fetchone():
        db_curs.execute(insertUserStmt, (pr.userId, pr.profileName))
        users_inserted += 1
    # insert review if not already in db
    db_curs.execute(selectReviewStmt, (pr.productId, pr.userId))
    if not db_curs.fetchone():
        db_curs.execute(insertReviewStmt, (pr.productId, pr.userId,
            pr.helpfulness, pr.score, pr.time, pr.summary, pr.text))
        reviews_inserted += 1

def printCounts():
    global products_inserted
    global categories_inserted
    global users_inserted
    global reviews_inserted
    print 'Inserted %d products' % products_inserted
    print 'Inserted %d categories' % categories_inserted
    print 'Inserted %d users' % users_inserted
    print 'Inserted %d reviews' % reviews_inserted

def main():
    # Parse options
    usage = 'Usage: %prog [options] <datafile>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    inputfilename = args[0]
    if not os.path.isfile(inputfilename):
        print >> sys.stderr, 'Cannot find: %s' % inputfilename
        return

    # determine category
    if options.category:
        category = options.category
    else:
        category = os.path.basename(inputfilename).split('.')[0]
    print 'Category: %s' % category

    # connect to db
    print 'Connecting to %s. . .' % options.db_fname
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create Products table if not already exists
        db_curs.execute(createProductsTableStmt)
        # create Categories table if not already exists
        db_curs.execute(createCategoriesTableStmt)
        # create Users table if not already exists
        db_curs.execute(createUsersTableStmt)
        # create Reviews table id not already exists
        db_curs.execute(createReviewsTableStmt)

        with open(inputfilename, 'r') as inputfile:
            maxReviews = sys.maxint
            review_cnt = 0
            pr = ProductReview()
            for line in inputfile:
                tokens = line.split('/', 1)
                try:
                    tokens = tokens[1].split(' ', 1)
                except IndexError:
                    continue
                attribute = tokens[0].split(':')[0]
                value = tokens[1].rstrip()
                pr.setAttr(attribute, value)
                if attribute == 'text':
                    importProductReview(db_curs, category, pr)
                    review_cnt += 1
                    if review_cnt >= maxReviews:
                        break
                    pr = ProductReview()
    # print insertion counts
    printCounts()

if __name__ == '__main__':
    main()
