#!/usr/local/bin/python

import multiprocessing as mp
import Queue
import eventlet
from eventlet.timeout import Timeout
import time
import urllib2
from bs4 import BeautifulSoup
import sqlite3
import sys
import selenium
from selenium import webdriver

# params
numWorkers = 6
productUrlTemplate = 'http://www1.bloomingdales.com/shop/product/?ID=%d'
workerTimeout = 30
webDriverTimeout = 30
workerQueueSize = 10

# db params
db_fname = 'data/bdales.db'
createRecommendsTableStmt =\
    ('CREATE TABLE IF NOT EXISTS Recommends(Id1 INT, Id2 INT, '
     'PRIMARY KEY (Id1, Id2), FOREIGN KEY(Id1) REFERENCES Products(Id), '
     'FOREIGN KEY(Id2) REFERENCES Products(Id))')
selectRecommendStmt = 'SELECT * FROM Recommends WHERE Id1 = :Id1 AND Id2 = :Id2'
insertRecommendStmt = 'INSERT INTO Recommends(Id1, Id2) VALUES (:Id1, :Id2)'
selectProductsStmt =\
     'SELECT Id FROM Products WHERE Available = 1 AND HaveRecs = 0'
selectProductStmt = 'SELECT * FROM Products WHERE Id = :Id'
updateProductStmt = 'UPDATE Products SET HaveRecs = 1 WHERE Id = :Id'


def getWebDriver():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('permissions.default.image', 2)
    driver = webdriver.Firefox(firefox_profile=profile)
    # TODO: Verify that these timeouts are optimal.
    driver.implicitly_wait(webDriverTimeout)
    driver.set_page_load_timeout(webDriverTimeout)
    driver.set_script_timeout(webDriverTimeout)
    return driver


def processRecommend(id1, productTag, db_curs):
    # process productTag
    try:
        id2 = int(productTag['id'])
    except ValueError:
        print >> sys.stderr, 'WARNING: Failed to parse productId.'
        return 0
    # check for pre-existing recommendation
    db_curs.execute(selectRecommendStmt, (id1, id2))
    if db_curs.fetchone():
        return 0
    # check db for product
    #print 'Id2 = %d' % id2
    db_curs.execute(selectProductStmt, (id2,))
    if not db_curs.fetchone():
        #print >> sys.stderr, 'WARNING: Product not in DB.'
        return 0
    # insert new recommendation
    db_curs.execute(insertRecommendStmt, (id1, id2))
    return 1


def getRecommends(driver, productId, db_curs):
    #print 'productId = %d' % productId
    insertCnt = 0
    productUrl = productUrlTemplate % productId
    try:
        # fetch html
        #print 'Opening url: %s' % productUrl
        driver.get(productUrl)
        html = driver.page_source
        soup = BeautifulSoup(html)
        for productTag in\
            soup.findAll('div', {'class': 'productThumbnail showQuickView'}):
            insertCnt +=\
                processRecommend(productId, productTag, db_curs)
        if insertCnt == 0:
            #print 'No recommends found.'
            pass
        db_curs.execute(updateProductStmt, (productId,))
    except selenium.common.exceptions.TimeoutException:
        #print >> sys.stderr,\
        #    'WARNING: Timed out waiting for page load.'
        pass
    return insertCnt


def worker(driver, q):
    # connect to db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()

        insertCnt = 0
        # TODO: Need a terminal condition here.
        while True:
            productId = q.get()
            # TODO: Verify that the next line is useful.
            driver.switch_to_window(driver.current_window_handle)
            insertCnt += getRecommends(driver, productId, db_curs)
            db_conn.commit()

    #print 'Inserted %d new recommendations.' % insertCnt


def master(drivers, queues, workers):
    # connect to db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()
        # create table if not already exists
        db_curs.execute(createRecommendsTableStmt)
        # get item ids
        db_curs.execute(selectProductsStmt)

        # parsel out work
        iter=0
        for row in db_curs.fetchall():
            productId = row[0]
            workerIdx = iter % numWorkers
            while True:
                try:
                    print 'Sending productId %d to worker %d' % (productId, workerIdx)
                    queues[workerIdx].put(productId, timeout=workerTimeout)
                    break
                except Queue.Full:
                    # replace worker
                    print 'WARNING: Replacing worker %d' % workerIdx
                    workers[workerIdx].terminate()
                    timeout = Timeout(10)
                    with Timeout(10) as timeout:
                        drivers[workerIdx].quit()
                    drivers[workerIdx] = getWebDriver()
                    workers[workerIdx] = mp.Process(target=worker,\
                            args=(drivers[workerIdx], queues[workerIdx]))
                    workers[workerIdx].start()
                    time.sleep(2) # a couple of seconds to start 
            iter += 1

    # close queues
    for w in range(numWorkers):
        queues[w].close()


def main():
    # create webdrivers
    drivers = []
    for w in range(numWorkers):
        drivers.append(getWebDriver())

    # create queues
    queues = []
    for w in range(numWorkers):
        queues.append(mp.Queue(workerQueueSize))

    # create worker processes
    workers = []
    for w in range(numWorkers):
        workers.append(mp.Process(target=worker, args=(drivers[w], queues[w])))

    # start worker processes
    for w in range(numWorkers):
        workers[w].start()

    # delegate work
    master(drivers, queues, workers)


if __name__ == '__main__':
    main()
