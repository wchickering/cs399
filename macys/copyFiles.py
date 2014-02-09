#!/usr/local/bin/python

"""
Copies files between directories.
"""

import logging
import sys
import os
import shutil
from optparse import OptionParser

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-m', '--max-num', type='int', dest='max_num', default=sys.maxint,
        help='Maximum number of files to copy.', metavar='MAX-NUM')
    return parser

def main():
    # Setup logging
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # Parse options
    usage = 'Usage: %prog [options] from-dir to-dir'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error('Wrong number of arguments')
    from_dir = args[0]
    to_dir = args[1]
    assert(options.max_num > 0)

    # Copy files
    num_copied = 0
    for filename in os.listdir(from_dir):
        src_path = os.path.join(from_dir, filename)
        dest_path = os.path.join(to_dir, filename)
        
        if not os.path.isfile(dest_path):
            print 'Copying %s' % filename
            shutil.copyfile(src_path, dest_path)
            num_copied += 1
        if num_copied >= options.max_num:
            break
    print '%d files copied.' % num_copied

if __name__ == '__main__':
    main()
