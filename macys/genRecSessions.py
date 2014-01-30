#!/usr/local/bin/python

import sqlite3
import csv

# params
db_fname = 'macys.db'
out_fname = 'recSessions.csv'

selectRecommendsStmt = 'SELECT Id1, Id2 FROM Recommends ORDER BY Id1'

def main():
    with open(out_fname, 'w') as csvOut:
        writer = csv.writer(csvOut)
        db_conn = sqlite3.connect(db_fname)
        with db_conn:
            db_curs = db_conn.cursor()
            db_curs.execute(selectRecommendsStmt)
            id1 = None
            session = []
            for row in db_curs.fetchall():
                if row[0] == id1:
                    session.append(row[1])
                else:
                    if id1:
                        writer.writerow(session)
                    id1 = row[0]
                    session = [id1]
            # Don't forget last session.
            writer.writerow(session)

if __name__ == '__main__':
    main()
