#!/usr/bin/env python

"""
Execute runExperiment.sh multiple times with various options and arguments.
"""

from optparse import OptionParser
import os
import sys
import sqlite3
from subprocess import call

# local moduls
from Util import getAndCheckFilename

# params
command = '../common/runExperiment.sh'

# db params
createProcessedCategoriesTableStmt =\
    ('CREATE TABLE IF NOT EXISTS ProcessedCategories(ParentCategory TEXT, '
     'Category TEXT, Processed INT, PRIMARY KEY (ParentCategory, Category))')
createBadCategoriesTableStmt =\
    ('CREATE TABLE IF NOT EXISTS BadCategories(ParentCategory TEXT, '
     'Category TEXT, PRIMARY KEY (ParentCategory, Category))')
selectProcessedCategoriesCountStmt =\
    ('SELECT COUNT(*) '
     'FROM ProcessedCategories')
insertProcessedCategoriesStmt =\
    ('INSERT INTO ProcessedCategories(ParentCategory, Category, Processed) '
     'SELECT ParentCategory, Category, 0 '
     'FROM Categories '
     'GROUP BY ParentCategory, Category')
selectProcessedCategoriesStmt =\
    ('SELECT PC.ParentCategory, PC.Category '
     'FROM ProcessedCategories AS PC '
     'WHERE PC.Processed = 0 '
     'AND NOT EXISTS '
     '(SELECT * '
     ' FROM BadCategories '
     ' WHERE ParentCategory = PC.ParentCategory '
     ' AND Category = PC.Category)')
updateProcessedCategoryStmt =\
    ('UPDATE ProcessedCategories '
     'SET Processed = 1 '
     'WHERE ParentCategory = :ParentCategory '
     'AND Category = :Category')

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('--options', dest='options', default=None,
        help='Space-separated options for runExperiment.sh.', metavar='STR')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] database sequence'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    dbname = getAndCheckFilename(args[0])
    try:
        sequence = int(args[1])
    except ValueError:
        parser.error('Invalid sequence number')
        sys.exit(-1)

    # connect to db
    db_conn = sqlite3.connect(dbname)
    db_curs = db_conn.cursor()

    # create ProcessedCategories table if not already exists
    db_curs.execute(createProcessedCategoriesTableStmt)
    db_conn.commit()

    # create BadCategories table if not already exists
    db_curs.execute(createBadCategoriesTableStmt)
    db_conn.commit()

    # insert ProcessedCategories if none exist
    db_curs.execute(selectProcessedCategoriesCountStmt)
    count = int(db_curs.fetchone()[0])
    if count == 0:
        print 'Creating ProcessedCategories records. . .'
        db_curs.execute(insertProcessedCategoriesStmt)
        db_conn.commit()

    # prepare command options
    if options.options is not None:
        cmdOptions = options.options.split()
    else:
        cmdOptions = []

    if sequence == 1:
        # execute for every category
        print 'Executing runExperiment.sh for every category. . .'
        db_curs.execute(selectProcessedCategoriesStmt)
        for parentCategory, category in db_curs.fetchall():
            args = [command] + cmdOptions + [parentCategory, category]
            print '>>> %s' % ' '.join(args)
            returncode = call(args)
            if returncode != 0:
                print >> sys.stderr, 'WARNING: runExperiment.sh failed.'
            db_curs2 = db_conn.cursor()
            db_curs2.execute(updateProcessedCategoryStmt,
                             (parentCategory, category))
            db_conn.commit()
    else:
        print >> sys.stderr, 'Unrecognized sequence: %d' % sequence

if __name__ == '__main__':
    main()
