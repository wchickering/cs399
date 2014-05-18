#!/usr/bin/env python

"""
Creates a JSON "fixture" (serialized data for upload) for the django
matching/tourneys app.
"""

from optparse import OptionParser
import os
import sys
import sqlite3
import json
import numpy as np

# import local modules
import LSI_util as lsi

# db params
selectProductStmt =\
    ('SELECT Url, Description '
     'FROM Products '
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
            dictionary[str(items[i])] = i
        matrices.append(lsi.getTermConcepts(u, s))
        dictionaries.append(dictionary)
    return matrices, dictionaries

def genRecord(pk, model, **kwargs):
    record = {}
    record['pk'] = pk
    record['model'] = model
    record['fields'] = kwargs
    return record

def genData(mediadir, item_lists, db_conn, matrices, dictionaries):
    db_curs = db_conn.cursor()
    # initialize PKs
    league_id = 0
    attribute_id = 0
    player_id = 0
    playerattribute_id = 0
    data = []
    for idx in range(len(item_lists)):
        items = item_lists[idx]
        dictionary = dictionaries[idx]
        matrix = matrices[idx]
        # generate league record
        league_id += 1
        name = 'league%d' % league_id
        data.append(genRecord(league_id, 'tourneys.league', name=name,
                              description=name, mediadir=mediadir))
        attribute_id_dict = {}
        for attribute in range(matrix.shape[0]):
            # generate attribute record
            attribute_id += 1
            attribute_id_dict[attribute] = attribute_id
            data.append(genRecord(attribute_id, 'tourneys.attribute',
                                  league=league_id,
                                  name='league%d_attribute%d' %\
                                  (league_id, attribute)))
        for item_id in items:
            db_curs.execute(selectProductStmt, (item_id,))
            row = db_curs.fetchone()
            if not row:
                print >> sys.stderr, 'WARNING: %d not found in db' % item_id
                continue
            url = row[0]
            description = row[1]
            # generate player record
            player_id += 1
            image = os.path.join(mediadir, '%s.jpg' % item_id)
            data.append(genRecord(player_id, 'tourneys.player',
                                  league=league_id, code=item_id,
                                  description=description, image=image))
            for attribute in range(matrix.shape[0]):
                # generate playerattribute record
                playerattribute_id += 1
                value = matrix[attribute][dictionary[item_id]]
                data.append(genRecord(playerattribute_id,
                                      'tourneys.playerattribute',
                                      player=player_id,
                                      attribute=attribute_id_dict[attribute],
                                      value=value))
    return data

def main():
    # Parse options
    usage = 'Usage: %prog [options] database svd1.npz svd2.npz'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 3:
        parser.error('Wrong number of arguments')
    dbname = args[0]
    if not os.path.isfile(dbname):
        parser.error('Cannot find %s' % dbname)

    # derive mediadir from dbname
    mediadir = os.path.splitext(os.path.basename(dbname))[0]
    print >> sys.stderr, 'mediadir = %s' % mediadir

    # connect to db 
    print >> sys.stderr, 'Connecting to %s. . .' % dbname
    db_conn = sqlite3.connect(dbname)

    # read LSI models
    matrices, dictionaries = getLSIModels(args[1:])
 
    # get league items
    item_lists = []
    for dictionary in dictionaries:
        item_lists.append(dictionary.keys())

    # generate data
    print >> sys.stderr, 'Generating data. . .'
    data = genData(mediadir, item_lists, db_conn, matrices, dictionaries)

    # dump data
    print >> sys.stderr, 'Dumping data. . .'
    print json.dumps(data)

if __name__ == '__main__':
    main()
