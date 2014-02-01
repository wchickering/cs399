import web

db = web.database(dbn='sqlite', db='macys.db')
db2 = web.database(dbn='sqlite', db='auctionbase.db')

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

def getNextProduct(productId):
    query_string = 'select min(Id) as Id, Url, ImgFile, Description, Prices from Products where Id > $productId'
    results = query(query_string, {'productId': productId})
    return results[0]

def getProductPrice(productId):
    query_string = 'select Prices from Products where Id = $productId'
    results = query(query_string, {'productId': productId})
    return results[0].Prices

def getProductUrl(productId):
    query_string = 'select Url from Products where Id = $productId'
    results = query(query_string, {'productId': productId})
    return results[0].Url

# returns the current time from your database
def getTime():
    query_string = 'select now from Time'
    results = query(query_string)
    # alternatively: return results[0]['now']
    return results[0].now 

# Updates the current time. If given time violates a constraint,
# an exception will be thrown.
def setTime(selected_time):
    query_string = 'update Time set now = $newTime'
    query(query_string, {'newTime': selected_time})

def getUserByUsername(username):
    query_string = 'select * from User where username = $username'
    results = query(query_string, {'username': username})
    for r in results:
        return r
    return None

def getCategories():
    query_string = 'select * from Category'
    return query(query_string)

def getCategoryNameById(category_id):
    query_string = 'select categoryName from Category where categoryID = $categoryID'
    results = query(query_string, {'categoryID': category_id})
    return results[0].categoryName

# returns a single item specified by the Item's ID in the database
def getAuctionById(item_id):
    query_string = 'select * from auction_view where itemID = $itemID'
    results = query(query_string, {'itemID': item_id})
    for r in results:
        return r
    return None

def getHighBidByItemId(item_id):
    query_string = 'select * from high_bid_view where itemID = $itemID'
    results = query(query_string, {'itemID': item_id})
    for r in results:
        return r
    return None

def createBid(item_id, user_id, amount):
    now = getTime()
    query_string = ('insert into Bid (itemID, userID, time, amount) '
                    'values ($itemID, $userID, $time, $amount)')
    query(query_string, {'itemID': item_id, 'userID': user_id, 'time': now, 'amount': amount})

def getBidsByItemId(item_id):
    query_string = ('select Bid.*, User.* from Bid natural join User, Time '
                    'where itemID = $itemID and time <= Time.now order by time desc')
    return query(query_string, {'itemID': item_id})

def getAuctions(**filters):

#category_id=None, status=None,
#                min_currently=None, max_currently=None,
#                min_started=None, max_started=None,
#                min_ends=None, max_ends=None):
    query_string = ('select distinct auction_view.* '
                    'from ItemCategory natural join Category, '
                    'auction_view '
                    'where auction_view.itemID = ItemCategory.itemID ')
    vars = {}
    # categoryID
    if 'category_id' in filters:
        query_string += 'and categoryID = $categoryID '
        vars['categoryID'] = filters['category_id']
    # status
    if 'status' in filters:
        status = filters['status']
        if status == 'Pending':
            query_string += 'and status = "Pending" '
        elif status == 'Open':
            query_string += 'and status = "Open" '
        elif status == 'Closed':
            query_string += 'and status = "Closed" '
        elif status:
            raise ValueError('Invalid status value: %s' % status)
    # currently
    if 'min_currently' in filters:
        query_string += 'and currently >= $min_currently '
        vars['min_currently'] = filters['min_currently']
    if 'max_currently' in filters:
        query_string += 'and currently <= $max_currently '
        vars['max_currently'] = filters['max_currently']
    # started
    if 'min_started' in filters:
        query_string += 'and started >= $min_started '
        vars['min_started'] = filters['min_started']
    if 'max_started' in filters:
        query_string += 'and started <= $max_started '
        vars['max_started'] = filters['max_started']
    # ends
    if 'min_ends' in filters:
        query_string += 'and ends >= $min_ends '
        vars['min_ends'] = filters['min_ends']
    if 'max_ends' in filters:
        query_string += 'and ends <= $max_ends '
        vars['max_ends'] = filters['max_ends']
    query_string += 'order by ends'
    return query(query_string, vars)

# helper method to determine whether query result is empty
# Sample use:
# query_result = sqlitedb.query('select currenttime from Time')
# if (sqlitedb.isResultEmpty(query_result)):
#   print 'No results found'
# else:
#   .....
#
# NOTE: this will consume the first row in the table of results,
# which means that data will no longer be available to you.
# You must re-query in order to retrieve the full table of results
def isResultEmpty(result):
    try:
        result[0]
        return False
    except:
        return True

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}):
    return db.query(query_string, vars)

#####################END HELPER METHODS#####################

#TODO: additional methods to interact with your database,
# e.g. to update the current time
