from MagicWardrobe import MagicWardrobe
import web

db = web.database(dbn='sqlite', db='data/macys.db')
sessionId = 1
wardrobe = MagicWardrobe()
wardrobe.initSession(sessionId)

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()
# Sample usage (in auctionbase.py):
#
# t = sqlitedb.transaction()
# try:
#     sqlitedb.query('[FIRST QUERY STATEMENT]')
#     sqlitedb.query('[SECOND QUERY STATEMENT]')
# except:
#     t.rollback()
#     raise
# else:
#     t.commit()
#
# check out http://webpy.org/cookbook/transactions for examples
def getProductID():
    query_string = 'select min(Id) as x from Products'
    results = query(query_string)
    return results[0].x

def getProduct(productId):
    query_string = 'select Id, Url, ImgFile, Description, Prices from Products where Id = $productId'
    results = query(query_string, {'productId': productId})
    return results[0]

def getNextProduct(productId, liked):
    productId = int(productId)
    if productId == 0:
        productId = 1184526 # Magic productId for testing
    likes = []
    dislikes = []
    if liked == 'disliked':
        dislikes.append(int(productId))
    else:
        likes.append(int(productId))
    wardrobe.feedback(sessionId, likes, dislikes)
    items = wardrobe.nextItems(sessionId, 1)
    result = getProduct(items[0])
    if liked == 'disliked':
        result.Description += '?'
    elif liked == 'liked':
        result.Description += '!'
    return result

def query(query_string, vars = {}):
    return db.query(query_string, vars)
