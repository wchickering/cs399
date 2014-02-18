#!/usr/local/bin/python

import sqlite3

# params
selectProductStmt =\
    ('SELECT Url, ImgFile, Description, Prices, Available, Time, HaveRecs '
     'FROM Products WHERE Id = :Id')
selectCategoriesStmt =\
     'SELECT ParentCategory, Category FROM Categories WHERE Id = :Id'
selectOutgoingEdgesStmt = 'SELECT Id2 FROM Recommends WHERE Id1 = :Id'
selectIncomingEdgesStmt = 'SELECT Id1 FROM Recommends WHERE Id2 = :Id'

class Product(object):
    """Represents a Product from a retailer database.
    """

    def __init__(self, db_conn, productId, retailer=None):
        self.id = productId
        self.retailer = retailer
        db_curs = db_conn.cursor()
        # Get Product relation
        db_curs.execute(selectProductStmt, {'Id': productId})
        if db_curs.rowcount == 0:
            raise ValueError('productId not found in database')
        row = db_curs.fetchone()
        self.url = row[0]
        self.imgfile = row[1]
        self.description = row[2]
        self.prices = row[3]
        self.available = row[4]
        self.time = row[5]
        self.haverecs = row[6]
        # Get Categories relations
        db_curs.execute(selectCategoriesStmt, {'Id': productId})
        self.categories = [(row[0], row[1]) for row in db_curs.fetchall()]
        # Get outgoing edges
        db_curs.execute(selectOutgoingEdgesStmt, {'Id': productId})
        self.outgoing = [row[0] for row in db_curs.fetchall()]
        # Get incoming edges
        db_curs.execute(selectIncomingEdgesStmt, {'Id': productId})
        self.incoming = [row[0] for row in db_curs.fetchall()]

    def printProduct(self):
        print '  productId = %d' % self.id
        print '   retailer = %s' % self.retailer
        print '        url = %s' % self.url
        print '    imgfile = %s' % self.imgfile
        print 'description = %s' % self.description
        print '     prices = %s' % self.prices
        print '  available = %d' % self.available
        print '       time = %s' % self.time
        print '   haverecs = %d' % self.haverecs
        for cat in self.categories:
            print '  parentCat = %s, cat = %s' % (cat[0], cat[1])
        print ' outgoing = %s' % self.outgoing
        print ' incoming = %s' % self.incoming


##########################
# ROUGH UNIT TEST
##########################

# params
db_name = 'macys/macys.db'

def main():
    db_conn = sqlite3.connect(db_name)
    p = Product(db_conn, 827236, 'macys')
    p.printProduct()

if __name__ == '__main__':
    main()
