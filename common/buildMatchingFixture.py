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

# db params
selectProductIdsStmt = 'SELECT Id FROM Products'
selectProductStmt = 'SELECT Url, Description FROM Products WHERE Id = :Id'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--shortname', dest='shortname', default=None,
        help='Short name for company.', metavar='NAME')
    parser.add_option('--longname', dest='longname', default=None,
        help='Long name for company.', metavar='NAME')
    parser.add_option('--company_id', type='int', dest='company_id', default=1,
        help='Company primary key.', metavar='NUM')
    parser.add_option('--graph', dest='graph', default=None,
        help=('Limit products in fixture to those in the provided undirected '
              'or directed graph.'), metavar='FILE')
    return parser

def loadGraph(fname):
    with open(fname, 'r') as f:
        graph = pickle.load(f)
    return graph

def main():
    # Parse options
    usage = 'Usage: %prog [options] database'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    dbname = args[0]
    if not os.path.isfile(dbname):
        parser.error('Cannot find %s' % dbname)
    if options.graph is not None:
        if not os.path.isfile(options.graph):
            parser.error('Cannot find %s' % options.graph)
        graph = loadGraph(options.graph)
    else:
        graph = None

    print >> sys.stderr, 'Connecting to %s. . .' % dbname
    db_conn = sqlite3.connect(dbname)

    # get company name
    if options.shortname is not None:
        shortname = options.shortname
    else:
        shortname = os.path.splitext(os.path.basename(dbname))[0]
    if options.longname is not None:
        longname = options.longname
    else:
        longname = shortname

    # get company items
    if graph is not None:
        # confine items to those present in graph
        items = graph.keys()
    else:
        # include all items in db
        db_curs = db_conn.cursor()
        db_curs.execute(selectProductIdsStmt)
        items = [int(row[0]) for row in db_curs.fetchall()]

    # generate data
    print >> sys.stderr, 'Generating data. . .'
    data = []
    record = {}
    record['pk'] = options.company_id
    record['model'] = 'polls.company'
    fields = {}
    fields['shortname'] = shortname
    fields['longname'] = longname
    record['fields'] = fields
    data.append(record)
    db_curs = db_conn.cursor()
    pk = 1
    for item_id in items:
        db_curs.execute(selectProductStmt, (item_id,))
        row = db_curs.fetchone()
        if not row:
            print >> sys.stderr, 'WARNING: %d not found in db' % item_id
            continue
        url = row[0]
        description = row[1]
        record = {}
        record['pk'] = pk
        record['model'] = 'polls.product'
        fields = {}
        fields['company'] = options.company_id
        fields['item_id'] = item_id
        fields['url'] = url
        fields['description'] = description
        record['fields'] = fields
        data.append(record)
        pk += 1

    # dump data
    print >> sys.stderr, 'Dumping data. . .'
    print json.dumps(data)

if __name__ == '__main__':
    main()
