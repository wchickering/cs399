#!/usr/bin/env python

"""
Download any/all missing product images from macys.com.
"""

import urllib
import urllib2
from bs4 import BeautifulSoup, NavigableString
import json
import re
import unicodedata
import math
import sys
import os
import time
import signal

# params
categories_fname = 'categories.json'
imageFileTemplate = 'images/%d.jpg'
metaUrlTemplate = 'http://www1.macys.com/catalog/category/facetedmeta?sortBy=NAME&productsPerPage=%d&pageIndex=%d&parentCategoryId=%d&categoryId=%d'
productsUrlTemplate = 'http://www1.macys.com/shop/catalog/product/thumbnail/1?edge=hybrid&limit=none&suppressColorSwatches=false&categoryId=%d&ids=%s'
productsPerPage = 100
pauseTime = 0.2 # number of second to pause between HTTP requests.
urlretrieveTimeout = 20

def normalizeStr(s):
    decodedStr = s.decode("utf8")
    u = unicode(decodedStr)
    return unicodedata.normalize('NFKD', u).encode('ascii','ignore')

def getProductImage(productTag, parentCategoryName, categoryName):
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
            def timeout_handler(signum, frame):
                print >> sys.stderr, 'WARNING: Timeout occurred.'
                raise TimeoutError
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(urlretrieveTimeout)
            try:
                urllib.urlretrieve(imgSrc, img_fname)
                signal.alarm(0) # disable alarm
            except TimeoutError:
                print >> sys.stderr, 'WARNING: Image retrieval timed out.'
                return 0
            except:
                print >> sys.stderr, 'WARNING: Failed to retrieve product image'
                return 0
        return 1
    except:
        print >> sys.stderr, 'WARNING: Failed to parse HTML.'
        return 0

def processCategory(category):
    parentCategoryName = str(category['parentCategoryName'])
    parentCategoryId = int(category['parentCategoryId'])
    categoryName = str(category['categoryName'])
    categoryId = int(category['categoryId'])
    print 'parentCategoryName =', parentCategoryName
    print '  parentCategoryId =', parentCategoryId
    print '      categoryName =', categoryName
    print '        categoryId =', categoryId

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
            if len(productIds) > 0:
                # retrieve product images and data
                productList = ','.join(map(lambda x:'%d_%d' % (categoryId, x),\
                                           productIds))
                print 'productList =', productList
                url = productsUrlTemplate % (categoryId, productList)
                print 'Opening Url: %s' % url
                html = urllib2.urlopen(url).read()
                soup = BeautifulSoup(html)
                for productTag in\
                    soup.findAll('div', {'class': 'productThumbnail'}):
                    # Pause for a moment to be "polite"
                    time.sleep(pauseTime)
                    cnt = getProductImage(productTag, parentCategoryName,
                                          categoryName)
                    pageInsertCnt += cnt
                    insertCnt += cnt

                print 'Acquired %d out of %d products' %\
                      (pageInsertCnt, len(productIds))

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
    # Get categories
    with open(categories_fname) as f:
        categories_json = f.readlines()

    # Insert/Update each category
    insertCnt = 0
    for category_json in categories_json:
        category = json.loads(category_json.rstrip())
        insertCnt += processCategory(category)

if __name__ == '__main__':
    main()
