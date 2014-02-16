#!/usr/local/bin/python

import sys
import os
from optparse import OptionParser
from selenium import webdriver
from ghost import Ghost

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-o', '--output', dest='outfilename', default=None,
        help='Output file.', metavar='OUT_FILE')
    return parser

def main():
    # Parse options
    usage = 'Usage: %prog [options] url'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    url = args[0]
    if options.outfilename:
        assert(os.path.isfile(options.outfilename))
        outfile = open(options.outfilename, 'w')
    else:
        outfile = sys.stdout

    # Attempt to open url
    profile = webdriver.FirefoxProfile();
    profile.set_preference('permissions.default.image', 2);
    driver = webdriver.Firefox(firefox_profile=profile);
    driver.get(url)
    content = driver.page_source.encode('utf-8')
    driver.close()

    outfile.write(content)
    outfile.close()

if __name__ == '__main__':
    main()
