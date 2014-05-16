#!/usr/bin/env python

"""
Creates a JSON "fixture" (serialized data for upload) for the django
matching app.
"""

from optparse import OptionParser
import os
import sys
import sqlite3
import pickle
import json
import numpy as np

# import local modules
import LSI_util as lsi

# db params
selectProductIdsStmt =\
    ('SELECT Id '
     'FROM Products')
selectProductStmt =\
    ('SELECT Url, Description '
     'FROM Products '
     'WHERE Id = :Id')
selectProductCategoriesStmt =\
    ('SELECT ParentCategory, Category '
     'FROM Categories '
     'WHERE Id = :Id')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    return parser

def getLSIModels(files):
    matrices = []
    dictionaries = []
    for svdfile in files:
        if not os.path.isfile(svdfile):
            parser.error('Cannot find %s' % svdfile)
        print >> sys.stderr, 'Loading LSI model from %s. . .' % svdfile
        npzfile = np.load(svdfile)
        u = npzfile['u']
        s = npzfile['s']
        v = npzfile['v']
        items = npzfile['dictionary']
        dictionary = {}
        for i in range(len(items)):
            dictionary[int(items[i])] = i
        matrices.append(lsi.getTermConcepts(u, s))
        dictionaries.append(dictionary)
    return matrices, dictionaries

def genRecord(pk, model, **kwargs):
    record = {}
    record['pk'] = pk
    record['model'] = model
    record['fields'] = kwargs
    return record

def genData(item_lists, db_conn, matrices, dictionaries):
    # initialize PKs
    company_id = 0
    concept_id = 0
    category_id = 0
    product_id = 0
    productcategory_id = 0
    productconcept_id = 0
    data = []
    for idx in range(len(item_lists)):
        items = item_lists[idx]
        dictionary = dictionaries[idx]
        matrix = matrices[idx]
        # generate company record
        company_id += 1
        shortname = 'company%d' % company_id
        data.append(genRecord(company_id, 'polls.company', shortname=shortname,
                              longname=shortname))
        concept_id_dict = {}
        for concept in range(matrix.shape[0]):
            # generate concept record
            concept_id += 1
            concept_id_dict[concept] = concept_id
            data.append(genRecord(concept_id, 'polls.concept',
                                  company=company_id,
                                  name='concept%d' % concept))
        # precompute company's category data
        db_curs = db_conn.cursor()
        categories = set()
        product_categories = {}
        for item_id in items:
            product_categories[item_id] = []
            db_curs.execute(selectProductCategoriesStmt, (item_id,))
            for row in db_curs.fetchall():
                category = '%s/%s' % (row[0], row[1])
                categories.add(category)
                product_categories[item_id].append(category)
        category_id_dict = {}
        for category in categories:
            # generate category record
            category_id += 1
            category_id_dict[category] = category_id
            data.append(genRecord(category_id, 'polls.category',
                                  company=company_id, description=category))
        for item_id in items:
            db_curs.execute(selectProductStmt, (item_id,))
            row = db_curs.fetchone()
            if not row:
                print >> sys.stderr, 'WARNING: %d not found in db' % item_id
                continue
            url = row[0]
            description = row[1]
            # generate product record
            product_id += 1
            data.append(genRecord(product_id, 'polls.product',
                                  company=company_id, item_id=item_id, url=url,
                                  description=description))
            for category in product_categories[item_id]:
                # generate productcategory record
                productcategory_id += 1
                data.append(genRecord(productcategory_id,
                                      'polls.productcategory',
                                      product=product_id,
                                      category=category_id_dict[category]))
            for concept in range(matrix.shape[0]):
                # generate productconcept record
                productconcept_id += 1
                value = matrix[concept][dictionary[item_id]]
                data.append(genRecord(productconcept_id, 'polls.productconcept',
                                      product=product_id,
                                      concept=concept_id_dict[concept],
                                      value=value))
    return data

def main():
    # Parse options
    usage = 'Usage: %prog [options] database [svd1.npz] [svd2.npz] [...]'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error('Wrong number of arguments')
    dbname = args[0]
    if not os.path.isfile(dbname):
        parser.error('Cannot find %s' % dbname)

    if len(args) > 1:
        # read LSI models
        matrices, dictionaries = getLSIModels(args[1:])
 
    # connect to db 
    print >> sys.stderr, 'Connecting to %s. . .' % dbname
    db_conn = sqlite3.connect(dbname)

    # get company items
    item_lists = []
    if dictionaries:
        for dictionary in dictionaries:
            item_lists.append(dictionary.keys())
    else:
        # include all items in db within single company
        db_curs = db_conn.cursor()
        db_curs.execute(selectProductIdsStmt)
        item_lists.append([int(row[0]) for row in db_curs.fetchall()])

    # generate data
    print >> sys.stderr, 'Generating data. . .'
    data = genData(item_lists, db_conn, matrices, dictionaries)

    # dump data
    print >> sys.stderr, 'Dumping data. . .'
    print json.dumps(data)

if __name__ == '__main__':
    main()
