#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import json
import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import cgi
import time
import pprint

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        '/auctionsearch', 'auction_search',
        '/auctionlist', 'auction_list',
        '/auctiondetails', 'auction_details',
        '/auctiondetails', 'auction_details',
        '/leftorright', 'left_or_right',
        # first parameter => URL, second parameter => class name
        )

count = 0

class left_or_right:
   def GET(self):
       #nextID = sqlitedb.getNextProductID()
       productId = sqlitedb.getProductID()
       price = sqlitedb.getProductPrice(productId)
       template_params = {}
       template_params['productId'] = productId
       template_params['price'] = price
       return render_template('index.html', **template_params)

   def POST(self):
       post_params = web.input()
       productId = post_params['productId']
       #product = sqlitedb.getProduct(productId)
       product = sqlitedb.getNextProduct(productId)
       json_obj = json.dumps(product)
       return json_obj

class curr_time:
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class select_time:
    def GET(self):
        # get current time
        current_time = sqlitedb.getTime()
        t = time.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        return render_template('select_time.html', time = t)

    def POST(self):
        
        template_params = {}

        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)

        try:
            t = time.strptime(selected_time, "%Y-%m-%d %H:%M:%S")
            template_params['time'] = t
        except Exception as e:
            template_params['error'] = 'Invalid Time: %s' % cgi.escape(selected_time)
        else:
            template_params['message'] = '(Selected time was: %s.)' % selected_time

            t = sqlitedb.transaction()
            try:
                sqlitedb.setTime(selected_time)
            except Exception as e:
                template_params['error'] = str(e)
                t.rollback()
            else:
                t.commit()

        return render_template('select_time.html', **template_params)

class auction_search:
    def GET(self):
        categories = sqlitedb.getCategories()
        return render_template('auction_search.html', categories = categories)

class auction_list:
    def GET(self):
        print >> sys.stderr, dir(web)
        print >> sys.stderr, 'DBG: web.input() = %s' % web.input()
        get_params = web.input()
        template_params = {}
        filters = {}

        # status 
        if 'status' in get_params and get_params['status'] != 'All':
            filters['status'] = get_params['status']
            template_params['message'] = '%s Auctions' % filters['status']
        else:
            template_params['message'] = 'All Auctions'

        # category
        if 'category_id' in get_params and int(get_params['category_id']) >= 0:
            filters['category_id'] = get_params['category_id']
            categoryName = sqlitedb.getCategoryNameById(filters['category_id'])
            template_params['message'] += ' within <b>%s</b>' % cgi.escape(categoryName)

        # min currently
        if 'min_currently' in get_params and get_params['min_currently']:
            try:
                min_currently = float(get_params['min_currently'])
            except:
                template_params['error'] = \
                    "Invalid Min Price: %s" % cgi.escape(get_params['min_currently'])
            else:
                filters['min_currently'] = min_currently
                template_params['message'] += '<br>currently more than $%.2f' % min_currently

        # max currently
        if 'max_currently' in get_params and get_params['max_currently']:
            try:
                max_currently = float(get_params['max_currently'])
            except:
                template_params['error'] = \
                    "Invalid Max Price: %s" % cgi.escape(get_params['max_currently'])
            else:
                filters['max_currently'] = max_currently
                template_params['message'] += '<br>currently less than $%.2f' % max_currently

        # min started datetime
        if 'apply_min_started' in get_params and \
           get_params['apply_min_started'] == 'true':
            min_started_MM = get_params['min_started_MM']
            min_started_dd = get_params['min_started_dd']
            min_started_yyyy = get_params['min_started_yyyy']
            min_started_HH = get_params['min_started_HH']
            min_started_mm = get_params['min_started_mm']
            min_started_ss = get_params['min_started_ss'];
            filters['min_started'] = '%s-%s-%s %s:%s:%s' % \
                (min_started_yyyy, min_started_MM, min_started_dd,
                 min_started_HH, min_started_mm, min_started_ss)
            template_params['message'] += '<br> started after %s' % filters['min_started']
            
        # max started datetime
        if 'apply_max_started' in get_params and \
           get_params['apply_max_started'] == 'true':
            max_started_MM = get_params['max_started_MM']
            max_started_dd = get_params['max_started_dd']
            max_started_yyyy = get_params['max_started_yyyy']
            max_started_HH = get_params['max_started_HH']
            max_started_mm = get_params['max_started_mm']
            max_started_ss = get_params['max_started_ss'];
            filters['max_started'] = '%s-%s-%s %s:%s:%s' % \
                (max_started_yyyy, max_started_MM, max_started_dd,
                 max_started_HH, max_started_mm, max_started_ss)
            template_params['message'] += '<br> started before %s' % filters['max_started']

        # min ends datetime
        if 'apply_min_ends' in get_params and \
           get_params['apply_min_ends'] == 'true':
            min_ends_MM = get_params['min_ends_MM']
            min_ends_dd = get_params['min_ends_dd']
            min_ends_yyyy = get_params['min_ends_yyyy']
            min_ends_HH = get_params['min_ends_HH']
            min_ends_mm = get_params['min_ends_mm']
            min_ends_ss = get_params['min_ends_ss'];
            filters['min_ends'] = '%s-%s-%s %s:%s:%s' % \
                (min_ends_yyyy, min_ends_MM, min_ends_dd,
                 min_ends_HH, min_ends_mm, min_ends_ss)
            template_params['message'] += '<br> ends after %s' % filters['min_ends']
            
        # max ends datetime
        if 'apply_max_ends' in get_params and \
           get_params['apply_max_ends'] == 'true':
            max_ends_MM = get_params['max_ends_MM']
            max_ends_dd = get_params['max_ends_dd']
            max_ends_yyyy = get_params['max_ends_yyyy']
            max_ends_HH = get_params['max_ends_HH']
            max_ends_mm = get_params['max_ends_mm']
            max_ends_ss = get_params['max_ends_ss'];
            filters['max_ends'] = '%s-%s-%s %s:%s:%s' % \
                (max_ends_yyyy, max_ends_MM, max_ends_dd,
                 max_ends_HH, max_ends_mm, max_ends_ss)
            template_params['message'] += '<br> ends before %s' % filters['max_ends']

        template_params['auctions'] = sqlitedb.getAuctions(**filters)
       
        return render_template('auction_list.html', **template_params)

    def POST(self):
        return self.GET()

class auction_details:
    def GET(self, template_params=None):
        if not template_params:
            template_params = {}
        get_params = web.input()
        item_id = get_params['item_id']
        sqlitedb.transaction()
        try:
            auction = sqlitedb.getAuctionById(item_id)
            if not auction:
                raise ValueError('Auction not found.')
            else:
                template_params['auction'] = auction
            template_params['bids'] = sqlitedb.getBidsByItemId(item_id)
            template_params['high_bid'] = sqlitedb.getHighBidByItemId(item_id)
        except Exception as e:
            template_params['error'] = str(e)
        return render_template('auction_details.html', **template_params)

    def POST(self):
        template_params = {}
        t = sqlitedb.transaction()
        try:
            get_params = web.input()
            item_id = get_params['item_id']
            username = get_params['username']
            amount = float(get_params['amount'])
            user = sqlitedb.getUserByUsername(username)
            if not user:
                template_params['error'] = "Invalid username: " + cgi.escape(username)
            elif not isinstance(amount, float) or amount < 0:
                template_params['error'] = "Invalid amount: " + cgi.escape(amount)
            else:
                sqlitedb.createBid(item_id, user.userID, amount)
        except Exception as e:
            t.rollback()
            template_params['error'] = str(e)
        else:
            t.commit()

        return self.GET(template_params)

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
