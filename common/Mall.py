#!/usr/bin/env python

import sqlite3
from Product import Product

class Mall(object):
    """
    A specialized object-relational mapper for interfacing with
    retailer-specific databases. This class provides a place to localize all SQL
    specific to retailer databases.
    """

    def __init__(self):
        self.retailers = {}

    def registerRetailer(self, db_name, name):
        db_conn = sqlite3.connect(db_name)
        self._initDatabase(db_conn)
        self.retailers[name] = db_conn

    def getRetailer(self, name):
        return self.retailers[name]

    def getProduct(self, retailer, productId):
        if retailer not in self.retailers:
            raise ValueError('Unrecognized retailer.')
        return Product(self.retailers[retailer], productId, retailer=retailer)

    def _initDatabase(self, db_conn):
        """
        Create any database entities (e.g. tables, indexes, etc.) that do not
        already exit.
        """
        createProductsTableStmt =\
            ('CREATE TABLE IF NOT EXISTS Products(Id INT PRIMARY KEY, '
             'Url TEXT, ImgFile TEXT, Description TEXT, ShortDescription TEXT, '
             'LongDescription TEXT, Bullets TEXT, Prices TEXT, Available INT, '
             'Time TIMESTAMP, HaveRecs INT)')
        createCategoriesTableStmt =\
            ('CREATE TABLE IF NOT EXISTS Categories(Id INT, '
             'ParentCategory TEXT, Category TEXT, PRIMARY KEY (Id, '
             'ParentCategory, Category), FOREIGN KEY(Id) REFERENCES '
             'Products(Id))')
        createRecommendsTableStmt =\
            ('CREATE TABLE IF NOT EXISTS Recommends(Id1 INT, Id2 INT, '
             'PRIMARY KEY (Id1, Id2), FOREIGN KEY(Id1) REFERENCES '
             'Products(Id), FOREIGN KEY(Id2) REFERENCES Products(Id))')
        db_curs = db_conn.cursor()
        db_curs.execute(createProductsTableStmt)
        db_curs.execute(createCategoriesTableStmt)
        db_curs.execute(createRecommendsTableStmt)

##########################
# ROUGH UNIT TEST
##########################

# params
db_name = 'macys/macys.db'

def main():
    mall = Mall()
    retailer = 'macys'
    mall.registerRetailer(db_name, retailer)
    product = mall.getProduct(retailer, 827236)
    product.printProduct()
    print '====== Outgoing Edges ======'
    for productId in product.outgoing:
        p = mall.getProduct(product.retailer, productId)
        p.printProduct()
    print '############################'
    print '====== Incoming Edges ======'
    for productId in product.incoming:
        p = mall.getProduct(product.retailer, productId)
        p.printProduct()
    print '############################'

if __name__ == '__main__':
    main()
