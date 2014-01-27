#!/usr/local/bin/python

from optparse import OptionParser
import csv
import logging
import random

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def getParser():
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='filename', default='categories.csv',
        help='Input CSV file containing <category, productId> on each line.',
        metavar='FILE')
    parser.add_option('-o', '--output', dest='outfilename', default='trainSessions.csv',
        help='Output CSV file containing <productId, productId, productId, ...> on each line.',
        metavar='OUT_FILE')
    parser.add_option('-s', '--session-size', dest='session_size', type="int", default=100,
        help='Max number of products per session.', metavar='SIZE')
    parser.add_option('--num-sessions-factor', dest='num_sessions_factor', type="int",
        default=10, help='NUM_SESSIONS(category) = NUM_PRODUCTS(category)/FACTOR',
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

def generateSessions(category, productIds, session_size,
                     num_sessions_factor, writer):
    logging.info('=============================================')
    logging.info('Generating sessions for %s' % category)
    num_products = len(productIds)
    logging.info('len_products = %d' % num_products)
    num_sessions = 1 + int(num_products/num_sessions_factor)
    logging.info('num_sessions = %d' % num_sessions)
    _session_size = int(min(num_products, session_size))
    logging.info('session_size = %d' % _session_size)

    for i in range(num_sessions):
        copyIds = list(productIds)
        sessionIds = []
        for j in range(_session_size):
            sessionIds.append(randomPop(copyIds));
        writer.writerow(sessionIds)


def main():
    parser = getParser()
    (options, args) = parser.parse_args()
    random.seed()
    logging.info('Reading data from %s' % options.filename)
    with open(options.filename, 'r') as csvIn:
        reader = csv.reader(csvIn)
        logging.info('Writing sessions to %s' % options.outfilename)
        with open(options.outfilename, 'w') as csvOut:
            writer = csv.writer(csvOut)
            category = None
            productIds = None
            for row in reader:
                if row[0] == category:
                    productIds.append(row[1])
                else:
                    if productIds is not None:
                        generateSessions(category,
                                         productIds,
                                         options.session_size,
                                         options.num_sessions_factor,
                                         writer)
                    category = row[0]
                    productIds = [row[1]]
            # Don't forget last category
            if productIds is not None:
                generateSessions(category,
                                 productIds,
                                 options.session_size,
                                 options.num_sessions_factor,
                                 writer)

if __name__ == '__main__':
    main()
