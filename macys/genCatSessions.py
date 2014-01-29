#!/usr/local/bin/python

"""
Generates session information based on category listings.
"""

from optparse import OptionParser
import csv
import logging
import random

def getParser():
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='filename', default='categories.csv',
        help='Input CSV file containing <category, item> on each line.',
        metavar='FILE')
    parser.add_option('-o', '--output', dest='outfilename', default='trainSessions.csv',
        help='Output CSV file containing <item, item, item, ...> on each line.',
        metavar='OUT_FILE')
    parser.add_option('-s', '--session-size', dest='session_size', type="int", default=100,
        help='Max number of items per session.', metavar='SIZE')
    parser.add_option('--num-sessions-factor', dest='num_sessions_factor', type="int",
        default=10, help='NUM_SESSIONS(category) = NUM_ITEMS(category)/FACTOR',
        metavar='FACTOR')
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

def generateSessions(category, items, session_size,
                     num_sessions_factor, writer):
    logging.info('=============================================')
    logging.info('Generating sessions for %s' % category)
    num_items = len(items)
    logging.info('num_items = %d' % num_items)
    num_sessions = 1 + int(num_items/num_sessions_factor)
    logging.info('num_sessions = %d' % num_sessions)
    _session_size = int(min(num_items, session_size))
    logging.info('session_size = %d' % _session_size)

    for i in range(num_sessions):
        items_copy = list(items)
        sessionIds = []
        for j in range(_session_size):
            sessionIds.append(randomPop(items_copy));
        writer.writerow(sessionIds)


def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Parse options
    parser = getParser()
    (options, args) = parser.parse_args()

    # Initialize random number generator
    random.seed()

    logging.info('Reading data from %s' % options.filename)
    with open(options.filename, 'r') as csvIn:
        reader = csv.reader(csvIn)
        logging.info('Writing sessions to %s' % options.outfilename)
        with open(options.outfilename, 'a') as csvOut:
            writer = csv.writer(csvOut)
            category = None
            items = None
            for row in reader:
                if row[0] == category:
                    items.append(row[1])
                else:
                    if items is not None:
                        generateSessions(category,
                                         items,
                                         options.session_size,
                                         options.num_sessions_factor,
                                         writer)
                    category = row[0]
                    items = [row[1]]
            # Don't forget last category. TODO: Fix this.
            if items is not None:
                generateSessions(category,
                                 items,
                                 options.session_size,
                                 options.num_sessions_factor,
                                 writer)

if __name__ == '__main__':
    main()
