# coding: utf-8
import os, sys
import json,time
import datetime
import MySQLdb
from pymongo import Connection
from pymongo.objectid import ObjectId
import re
import urllib, urlparse
from pylibcurl import Curl, const, lib, CurlError
from fetion import fetion

reload(sys) 
sys.setdefaultencoding('utf8') 


def getlocation(addr):
    address = addr.replace(u'内','').split('(')[0];
    address = address.split(u'（')[0];
    address = urllib.quote(addr.encode('utf-8'))
    url = "http://maps.google.cn/maps/geo?q="+address+"&output=csv&oe=utf8&sensor=false"
    #print url
    s = urllib.urlopen(url).read()
    #print s
    try:
        retcode, ac, lat, lng = s.split(',')
        if retcode == '200':
            return float(lat), float(lng)
    except:
        fetion('fetch error!' + addr)
        pass
    return 0, 0 



def getlocation_old(addr):
    address = urllib.quote(addr.encode('utf-8'))
    url = "http://maps.google.cn/maps/geo?q="+address+"&output=csv&oe=utf8&sensor=false"
    print url
    s = urllib.urlopen(url).read()
    print s
    try:
        retcode, ac, lat, lng = s.split(',')
        if retcode == '200':
            return lat, lng 
    except:
        pass
    return 0, 0 

BANKS = [u'中国银行', u'中国工商银行', u'中国建设银行', u'中国农业银行', u'招商银行',
         u'中信银行', u'民生银行', u'交通银行', u'北京银行']

def formatdate(s):
    s = s.strip().replace('/','-').replace(u'.','-').replace(u'－', '-').replace(u'年','-')
    s = s.replace(u'月','-').replace(u'日','')
    # print s

    if s.count('-') != 2:
        print 'date error'
        return ''
    return '%s 23:59:59' % s.strip()

def update_location():
    batch_num = 100
    # Mongodb Connect
    con = Connection('127.0.0.1')
    db = con.kyh
    favors = db.favor

    #last_row_id = ObjectId(‘....’);
    last_row_id = None
    print 'start'
    fetion('start location query')
    counter = 0
    while True:
        counter = counter + 1
        print batch_num * counter, last_row_id
        if last_row_id == None:
            rows = favors.find({'bank': 5}).sort('_id',-1).limit(batch_num)
        else:
            rows = favors.find({'_id':{'$lt': last_row_id }, 'bank': 5}).sort('_id',-1).limit(batch_num)
        for t in rows:
            last_row_id = ObjectId(t['_id'])
            if not t.has_key('location'):
                location = getlocation(t['address'])
                if location[0] > 0:
                    t['location'] = location
                    favors.update({'_id': last_row_id}, t)
                    print '[update]', t['name'], t['location']
                else:
                    print t['address']
                time.sleep(1)
                #print t['name'], location
            else:
                print '[ignore]', t['name'], t['location']
                
        if rows.count(True) < batch_num:
            break 
    print 'finished'
    fetion('location query finished!')
    return


#################
if __name__ == '__main__':
    #if sys.argv[1] in globals():
    #    globals()[sys.argv[1]]()
    #else:
    #insert_brand(sys.argv[1])
    update_location()

