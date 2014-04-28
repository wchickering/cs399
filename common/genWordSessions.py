#!/usr/bin/env python

"""
Generates session information based on category listings.
"""

from optparse import OptionParser
import csv
import logging
import random
import sqlite3

# params
MIN_SESSION_SIZE = 2
MAX_SESSION_SIZE = 200

selectItemsStmt = 'SELECT Id FROM Products WHERE Description LIKE ? COLLATE NOCASE'

def getParser():
    parser = OptionParser()
    parser.add_option('-d', '--database', dest='db_fname', default='data/macys.db',
        help='sqlite3 database file.', metavar='FILE')
    parser.add_option('-f', '--file', dest='filename', default='data/words.txt',
        help=('Input file containing unique words from item descriptions, '
              'one per line.'), metavar='FILE')
    parser.add_option('-o', '--output', dest='outfilename', default='data/wordSessions.csv',
        help='Output CSV file containing <item, item, item, ...> on each line.',
        metavar='OUT_FILE')
    return parser
    
def randomPop(data):
	if data != []:
		pos = random.randrange( len(data) )
		elem = data[pos]
		data[pos] = data[-1]
		del data[-1]
		return elem
	else:
		return None

def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # Initialize random number generator
    random.seed()

    # Connect to db
    db_conn = sqlite3.connect(options.db_fname)
    with db_conn:
        cursor = db_conn.cursor()
        logging.info('Reading data from %s' % options.filename)
        with open(options.filename, 'r') as fileIn:
            logging.info('Writing sessions to %s' % options.outfilename)
            with open(options.outfilename, 'a') as csvOut:
                writer = csv.writer(csvOut)
                items = None
                for word in fileIn:
                    word_arg = '%'+word.strip()+'%'
                    print 'word_arg = %s' % word_arg
                    cursor.execute(selectItemsStmt, (word_arg,))
                    itemids = [row[0] for row in cursor.fetchall()]
                    if len(itemids) >= MIN_SESSION_SIZE and\
                       len(itemids) <= MAX_SESSION_SIZE:
                        logging.info('Creating session.')
                        writer.writerow(itemids)
                    else:
                        logging.warning('Skipping session due to length: %d' %\
                                        len(itemids))

if __name__ == '__main__':
    main()
