#!/usr/bin/env python

from gensim import corpora
from gensim.models import ldamodel
from optparse import OptionParser
import pickle
import os
import sys

from SessionTranslator import SessionTranslator

# params
imgsrcTemplate = 'images/%s.jpg'

def getParser(usage=None):
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--database', dest='dbname',
        default='data/macys.db',
        help='Name of Sqlite3 product database.', metavar='DBNAME')
    parser.add_option('--dictfname', dest='dictfname',
        default='data/tokens.dict',
        help='Dictionary that maps itemids to tokens.', metavar='FILE')
    parser.add_option('-n', '--topn', type='int', dest='topn', default=10,
        help='Number of items per topic to print.', metavar='NUM')
    return parser

def getItemTopics(dictionary, model, item):
    mixture = [0]*model.num_topics
    for topic in range(model.num_topics):
        item_dist = model.show_topic(topic, topn=len(dictionary))
        mixture[topic] = [kvp[0] for kvp in item_dist if kvp[1] == item][0]
    total = sum([x for x in mixture])
    return [(ind, x/total) for ind, x in enumerate(mixture)]

def genHtml(dictionary, model, translator, topn):
    print '<html lang="en" debug="true">'
    print '<head><title>Display LDA Topics</title></head>'
    print '<body>'
    # print top N items from each topic
    for topic in range(model.num_topics):
        item_dist = model.show_topic(topic, topn=topn)
        print '<hr><div><b>Topic: %d</b>' % topic
        items = [pair[1] for pair in item_dist]
        descriptions = translator.sessionToDesc(items)
        for i in range(len(items)):
            imgsrc = imgsrcTemplate % items[i]
            print '<div><table><tr><td><img src="%s"></td>' % imgsrc
            doc_bow = [(dictionary.token2id[items[i]], 1)]
            #mixture = model[doc_bow]
            mixture = getItemTopics(dictionary, model, items[i])
            print >> sys.stderr, 'DBG: mixture =', mixture
            print '<td><table>'
            for component in mixture:
                print '<tr><td>%d, %.3f</td></tr>' %\
                      (component[0], component[1])
            print '<tr><td>(%s) %s</td></tr>' % (items[i], descriptions[i])
            print '</table></td></tr></table></div>' 
        print '</div>'
    print '</body></html>'

def main():
    # Parse options
    usage = 'Usage: %prog [options] <lda.pickle>'
    parser = getParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('Wrong number of arguments')
    modelfname = args[0]
    if not os.path.isfile(modelfname):
        print >> sys.stderr, 'Cannot find %s' % modelfname
        return

    # get dictionary
    dictionary = corpora.Dictionary.load_from_text(options.dictfname)

    # load lda model
    with open(modelfname, 'r') as f:
        model = pickle.load(f)

    # get translator
    translator = SessionTranslator(options.dbname)

    # generate html document
    genHtml(dictionary, model, translator, options.topn)

if __name__ == '__main__':
    main()
