#!/usr/local/bin/python

import sqlite3
from Product import Product

class Factory(object):
    """Generates Product objects from various retailer databases.
    """

    def __init__(self):
        self.retailers = {}

    def registerRetailer(self, db_conn, name):
        self.retailers[name] = db_conn

    def getRetailer(self, name):
        return self.retailers[name]

    def getProduct(self, retailer, productId):
        if retailer not in self.retailers:
            raise ValueError('Unrecognized retailer.')
        return Product(self.retailers[retailer], productId, retailer=retailer)


##########################
# ROUGH UNIT TEST
##########################

# params
db_name = 'macys/macys.db'

def main():
    db_conn = sqlite3.connect(db_name)
    factory = Factory()
    retailer = 'Macys'
    factory.registerRetailer(db_conn, retailer)
    product = factory.getProduct(retailer, 827236)
    product.printProduct()
    print '====== Outgoing Edges ======'
    for productId in product.outgoing:
        p = factory.getProduct(product.retailer, productId)
        p.printProduct()
    print '############################'
    print '====== Incoming Edges ======'
    for productId in product.incoming:
        p = factory.getProduct(product.retailer, productId)
        p.printProduct()
    print '############################'

if __name__ == '__main__':
    main()
