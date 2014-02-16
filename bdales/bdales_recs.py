#!/usr/local/bin/python

import multiprocessing as mp
import time
import urllib2
from bs4 import BeautifulSoup
import sqlite3
import sys
import selenium
from selenium import webdriver

# params
numWorkers = 4
productUrlTemplate = 'http://www1.bloomingdales.com/shop/product/?ID=%d'
loadTimeout = 30

# db params
db_fname = 'bdales.db'
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
    driver.set_page_load_timeout(loadTimeout)
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


def worker(master_pipe, worker_pipe):
    master_pipe.close()

    # connect to db
    db_conn = sqlite3.connect(db_fname)
    with db_conn:
        db_curs = db_conn.cursor()

        driver = getWebDriver()

        insertCnt = 0
        while True:
            try:
                productId = worker_pipe.recv()
                insertCnt += getRecommends(driver, productId, db_curs)
                db_conn.commit()
            except EOFError:
                break

        driver.quit()

    #print 'Inserted %d new recommendations.' % insertCnt

    worker_pipe.close()
        

def master(pipes):
    # close worker ends of pipes
    for w in range(numWorkers):
        pipes[w][1].close()

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
            pipes[workerIdx][0].send(productId)
            iter += 1

    # close master ends of pipes
    for w in range(numWorkers):
        pipes[w][0].close()


def main():
    # create pipes
    pipes = []
    for w in range(numWorkers):
        master_pipe, worker_pipe = mp.Pipe()
        pipes.append((master_pipe, worker_pipe))

    # create worker processes
    workers = []
    for w in range(numWorkers):
        w = mp.Process(target=worker, args=(pipes[w][0], pipes[w][1]))
        workers.append(w)

    # start worker processes
    for w in range(numWorkers):
        workers[w].start()

    # delegate work
    master(pipes)


if __name__ == '__main__':
    main()
