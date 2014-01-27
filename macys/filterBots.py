import sqlite3

# params
botsPerParentCategoryFilter = 1
botsPerCategoryFilter = 3

# db params
db_fname = 'macys.db'
createSessionsTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Sessions(sessionId INT, productId INT, '
     'PRIMARY KEY (sessionId, productId))')
selectCategoriesStmt = 'SELECT distinct Category FROM Categories'
selectParentCategoriesStmt = 'SELECT distinct ParentCategory FROM Categories'
insertParentCategoryFilterStmt =\
    ('INSERT INTO Sessions(sessionId, productId) '
     'SELECT :sessionId, Id FROM Categories '
     'WHERE ParentCategory = :ParentCategory GROUP BY Id')
insertCategoryFilterStmt =\
    ('INSERT INTO Sessions(sessionId, productId) '
     'SELECT :sessionId, Id FROM Categories WHERE Category = :Category '
     'GROUP BY Id')

def main():
    # connect to db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()

        # create table if not already exists
        db_curs.execute(createSessionsTableStmt)

        sessionId = 1

        # do parent category filterbots
        db_curs.execute(selectParentCategoriesStmt)
        for row in db_curs.fetchall():
            parentCategory = row[0]
            print 'ParentCategory filterBots for: %s' % parentCategory
            for i in range(botsPerParentCategoryFilter):
                db_curs.execute(insertParentCategoryFilterStmt,\
                                (sessionId, parentCategory))
                print 'sessionId = %d' % sessionId
                sessionId += 1

        # do category filterbots
        db_curs.execute(selectCategoriesStmt)
        for row in db_curs.fetchall():
            category = row[0]
            print 'Category filterBots for: %s' % category
            for i in range(botsPerCategoryFilter):
                db_curs.execute(insertCategoryFilterStmt,\
                                (sessionId, category))
                print 'sessionId = %d' % sessionId
                sessionId += 1

if __name__ == '__main__':
    main()
