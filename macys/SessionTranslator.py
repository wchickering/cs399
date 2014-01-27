#!/usr/local/bin/python

import sqlite3

class SessionTranslator(object):
   """Translates sets of tokens into either sets of item descriptions or
   sparse category histograms.
   """

   selectCatStmt = 'SELECT Category FROM Categories WHERE Id = :Id'
   selectDescTemplate = 'SELECT Description FROM Products WHERE Id IN (%s)'

   def __init__(self, db_fname):
       """Constructs SessionTranslator, which connects to sqlite3 db."""
       db_conn = sqlite3.connect(db_fname)
       self.cursor = db_conn.cursor()

   def sessionToDesc(self, session):
       """Takes a list of itemsids and returns a list of item descriptions."""
       selectDescStmt = self.selectDescTemplate % ','.join('?'*len(session))
       self.cursor.execute(selectDescStmt, session)
       return [row[0] for row in self.cursor.fetchall()]

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
    translator = SessionTranslator('macys.db')
    session = [960598,666644,632709,551024,932073,960606,824431,914853,1093859,1053814]
    print 'session =', session
    print 'Translating to category populations. . .'
    cats = translator.sessionToCats(session)
    print cats
    print 'Translating to item descriptions. . .'
    descriptions = translator.sessionToDesc(session)
    print descriptions

if __name__ == '__main__':
    main()
