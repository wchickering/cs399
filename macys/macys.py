#!/usr/local/bin/python

import urllib
import urllib2
from bs4 import BeautifulSoup, NavigableString
import sqlite3
import json
import re
import unicodedata
import math
import sys
import os
import time

# params
categories_fname = 'categories.json'
imageFileTemplate = 'images/%d.jpg'
metaUrlTemplate = 'http://www1.macys.com/catalog/category/facetedmeta?sortBy=NAME&productsPerPage=%d&pageIndex=%d&parentCategoryId=%d&categoryId=%d'
productsUrlTemplate = 'http://www1.macys.com/shop/catalog/product/thumbnail/1?edge=hybrid&limit=none&suppressColorSwatches=false&categoryId=%d&ids=%s'
productsPerPage = 100
pauseTime = 0.2 # number of second to pause between HTTP requests.

# db params
db_fname = 'macys.db'
createProductsTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Products(Id INT PRIMARY KEY, Url TEXT, '
     'ImgFile TEXT, Description TEXT, Prices TEXT, Available INT, '
     'Time TIMESTAMP, HaveRecs INT)')
createCategoriesTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Categories(Id INT, ParentCategory TEXT, '
     'Category TEXT, PRIMARY KEY (Id, ParentCategory, Category), '
     'FOREIGN KEY(Id) REFERENCES Products(Id))')
updateAllProductsStmt = 'UPDATE Products SET Available = 0'
updateProductStmt = 'UPDATE Products SET Available = 1 WHERE Id = ?'
selectCategoryStmt =\
    ('SELECT * FROM Categories WHERE Id = :Id AND '
     'ParentCategory = :ParentCategory AND Category = :Category')
insertProductStmt =\
    ('INSERT INTO Products(Id, Url, ImgFile, Description, Prices, Available, '
     'HaveRecs, Time) VALUES (:Id, :Url, :ImgFile, :Description, :Prices, 1, '
     '0, CURRENT_TIMESTAMP)')
insertCategoryStmt =\
    ('INSERT INTO Categories(Id, ParentCategory, Category) '
     'VALUES (:Id, :ParentCategory, :Category)')

def normalizeStr(s):
    decodedStr = s.decode("utf8")
    u = unicode(decodedStr)
    return unicodedata.normalize('NFKD', u).encode('ascii','ignore')

# TODO: FIX THIS, IF IT'S USEFUL
def stripTags(tag):
    s = ''
    for c in tag.contents:
        if not isinstance(c, NavigableString):
            c = stripTags(c)
        if c:
            s += normalizeStr(c)
        print 's =', s
    tag.replaceWith(s)

def processProduct(productTag, parentCategoryName, categoryName, db_curs):
    try:
        # parse productTag
        try:
            product_id = int(productTag['id'])
        except ValueError:
            print >> sys.stderr, 'WARNING: Failed to parse product_id'
            return 0
        print 'product_id = %d' % product_id
        imgTag = productTag.find('img')
        imgSrc = imgTag['src']
        print 'imgSrc = %s' % imgSrc
        img_fname = imageFileTemplate % product_id
        print 'img_fname = %s' % img_fname
        # retrieve and save image
        if not os.path.isfile(img_fname):
            try:
                urllib.urlretrieve(imgSrc, img_fname)
            except:
                print >> sys.stderr, 'WARNING: Failed to retrieve product image'
        shortDescriptionTag = productTag.find('div', {'class' : 'shortDescription'})
        productUrl = shortDescriptionTag.find('a')['href']
        print 'productUrl = %s' % productUrl
        # remove "NEW!" from description
        newTag = shortDescriptionTag.find('span', text=re.compile("^NEW!"))
        if newTag:
            newTag.extract()
        shortDescription = \
            normalizeStr(shortDescriptionTag.find('a').renderContents().strip())
        print 'shortDesciption = %s' % shortDescription
        priceTag = productTag.find('div', {'class' : 'prices'})
        prices = []
        for tag in priceTag.findAll('span'):
            prices.append(normalizeStr(tag.renderContents()))
        print 'prices = %s' % prices
        # insert product into db
        db_curs.execute(insertProductStmt,\
            {'Id': product_id, 'Url': productUrl, 'ImgFile': img_fname,\
             'Description': shortDescription, 'Prices': str(prices)})
        # insert category into db
        db_curs.execute(insertCategoryStmt,\
            {'Id': product_id, 'ParentCategory': parentCategoryName,\
             'Category': categoryName})
        return db_curs.rowcount
    except:
        print >> sys.stderr, 'WARNING: Failed to parse HTML.'
        return 0

def processCategory(category, db_conn):
    parentCategoryName = str(category['parentCategoryName'])
    parentCategoryId = int(category['parentCategoryId'])
    categoryName = str(category['categoryName'])
    categoryId = int(category['categoryId'])
    print 'parentCategoryName =', parentCategoryName
    print '  parentCategoryId =', parentCategoryId
    print '      categoryName =', categoryName
    print '        categoryId =', categoryId

    db_curs = db_conn.cursor()

    insertCnt = 0
    pageIndex = 1
    while True:
        meta_url = metaUrlTemplate %\
            (productsPerPage, pageIndex, parentCategoryId, categoryId)
        try:
            # retrieve meta data
            print 'Opening Url: %s' % meta_url 
            meta_json = urllib2.urlopen(meta_url).read()
            meta = json.loads(unicode(meta_json, "ISO-8859-1"))

            # check for new products
            pageInsertCnt = 0
            productIds = meta['productIds']
            if len(productIds) == 0:
                print 'No products found.'
                break
            newProductIds = []
            for productId in productIds:
                # if already in db, set Available = 1
                db_curs.execute(updateProductStmt, (productId,))
                if db_curs.rowcount == 0:
                    newProductIds.append(productId)
                else:
                    # new category?
                    db_curs.execute(selectCategoryStmt,\
                        {'Id': productId, 'ParentCategory': parentCategoryName,\
                         'Category': categoryName})
                    if not db_curs.fetchone():
                        db_curs.execute(insertCategoryStmt,\
                            (productId, parentCategoryName, categoryName))

            if len(newProductIds) > 0:
                # retrieve product images and data
                productList = ','.join(map(lambda x:'%d_%d' % (categoryId, x),\
                                           newProductIds))
                print 'productList =', productList
                url = productsUrlTemplate % (categoryId, productList)
                print 'Opening Url: %s' % url
                html = urllib2.urlopen(url).read()
                soup = BeautifulSoup(html)
                for productTag in\
                    soup.findAll('div', {'class': 'productThumbnail'}):
                    # Pause for a moment to be "polite"
                    time.sleep(pauseTime)
                    cnt = processProduct(productTag, parentCategoryName,
                                         categoryName, db_curs)
                    pageInsertCnt += cnt
                    insertCnt += cnt

                # commit db transaction
                db_conn.commit()

                print 'Acquired %d out of %d products' % (pageInsertCnt, len(newProductIds))

                # check for terminal condition (i.e. all products read)
                productCount = meta['productCount']
                if pageIndex*productsPerPage >= productCount:
                    break
            pageIndex += 1
        except urllib2.HTTPError as e:
            print >> sys.stderr,\
                'WARNING: HTTPError({0}): {1}'.format(e.errno, e.strerror)
            break
    return insertCnt

def main():
    # connect to db
    print 'Connecting to %s. . .' % db_fname
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create Products table if not already exists
        db_curs.execute(createProductsTableStmt)
        # update Products setting all Available values to 0
        db_curs.execute(updateAllProductsStmt)
        # create Categories table if not already exists
        db_curs.execute(createCategoriesTableStmt)

        # Get categories
        with open(categories_fname) as f:
            categories_json = f.readlines()

        # Insert/Update each category
        insertCnt = 0
        for category_json in categories_json:
            category = json.loads(category_json.rstrip())
            insertCnt += processCategory(category, db_conn)

if __name__ == '__main__':
    main()
