#!/usr/local/bin/python

"""
Generates a CSV file for use in setting up an Amazon.com Mechanical Turk Job.
"""

import sqlite3
import os
import csv
import logging
import random
from optparse import OptionParser

# params
selectDescriptionStmt = 'SELECT Description FROM Products WHERE Id = :Id'
imageUrlTemplate = 'https://dl.dropboxusercontent.com/u/49846997/ComparingSkirts/%s'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--db-name', dest='db_name', default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('-o', '--output', dest='outfilename', default='data/turkjob.csv',
        help='Output CSV file.', metavar='OUT_FILE')
    return parser

def writeHeaderRecord(writer):
    writer.writerow(['item1', 'item2', 'description1', 'description2', 'imageUrl'])
   
def writeTaskRecord(writer, db_curs, filename):
    basename = filename.split('.')[0]
    items = basename.split('_')
    assert(len(items) == 2)
    # Retrieve item description A from db
    db_curs.execute(selectDescriptionStmt, (items[0],))
    row = db_curs.fetchone()
    if not row:
        logging.warning('Failed to retrieve Id: %d from database.'\
                        % items[0])
        return 0
    descs = [row[0]]
    # Retrieve item description B from db
    db_curs.execute(selectDescriptionStmt, (items[1],))
    row = db_curs.fetchone()
    if not row:
        logging.warning('Failed to retrieve Id: %d from database.'\
                        % items[1])
        return 0
    descs.append(row[0])
    imageUrl = imageUrlTemplate % filename
    # Write turk job task record
    writer.writerow([items[0], items[1], descs[0], descs[1], imageUrl])
    return 1

def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Parse options
    usage = 'Usage: %prog [options] comparisons_dir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    directory = args[0]
    assert(os.path.isdir(directory))

    # Initialize random number generator
    random.seed()

    # Connect to db
    logging.info('Connecting to database...')
    db_conn = sqlite3.connect(options.db_name)
    with db_conn:
        db_curs = db_conn.cursor()

        # Open CSV file for writing
        with open(options.outfilename, 'w') as csvOut:
            writer = csv.writer(csvOut)
            # Read all filenames into memory
            filenames = [f for f in os.listdir(directory)]
            # Shuffle filenames in place
            random.shuffle(filenames)
            # Write header record
            writeHeaderRecord(writer)
            num_tasks = 0
            for filename in filenames:
                num_tasks += writeTaskRecord(writer, db_curs, filename)
    print '%d tasks written.' % num_tasks

if __name__ == '__main__':
    main()
