#!/usr/bin/env python

import sqlite3

class SessionTranslator(object):
   """Translates sets of tokens into either sets of item descriptions or
   sparse category histograms.
   """

   selectCatStmt = 'SELECT Category FROM Categories WHERE Id = :Id'
   selectDescStmt = 'SELECT Description FROM Products WHERE Id = :Id'

   def __init__(self, db_fname):
       """Constructs SessionTranslator, which connects to sqlite3 db."""
       db_conn = sqlite3.connect(db_fname)
       self.cursor = db_conn.cursor()

   def sessionToDesc(self, session):
       """Takes a list of itemsids and returns a list of item descriptions."""
       descriptions = []
       for itemid in session:
           self.cursor.execute(self.selectDescStmt, (itemid,))
           descriptions.append(self.cursor.fetchone()[0])
       return descriptions

   def sessionToCats(self, session):
       """Takes a list of itemids and returns a dictionary of category
       populations.
       """
       cats = {}
       for itemid in session:
           self.cursor.execute(self.selectCatStmt, (itemid,))
           for row in self.cursor.fetchall():
               cat = row[0]
               if cat in cats:
                   cats[cat] += 1
               else:
                   cats[cat] = 1
       return cats

def main():
    """A simple, sanity-checking test."""
    print 'Constructing SessionTranslator (and hence, connecting to db). . .'
    translator = SessionTranslator('data/macys.db')
    #session = [960598,666644,632709,551024,932073,960606,824431,914853,1093859,1053814]
    #session = [1166763, 921078, 1166761, 773981, 1051953, 1166794, 703127,
    #           1200097, 1166379, 1242549]
    session = [1093859, 632709, 932073, 824431, 551024, 666644, 960598, 1053814,
               960606, 914853]
    print 'session =', session
    print 'Translating to category populations. . .'
    cats = translator.sessionToCats(session)
    print cats
    print 'Translating to item descriptions. . .'
    descriptions = translator.sessionToDesc(session)
    print descriptions

if __name__ == '__main__':
    main()
