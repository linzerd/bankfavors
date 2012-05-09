# coding: utf-8
import os, sys
import json,time
import datetime
import MySQLdb
import re
import urllib, urlparse
from pylibcurl import Curl, const, lib, CurlError

reload(sys) 
sys.setdefaultencoding('utf8') 

def getlocation(addr):
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


def format(filename):
    fr = open(filename, 'r')
    s = fr.read()
    items = json.loads(s)  
    details = []
    not_found = []
    for row in items:
        if not row['content'].has_key('address'):
            row['content']['address'] = ''
            print row['name']

        address = row['content']['address']
        if '(' in address:
            temp = address.split('(')
            address = temp[len(temp) - 2]
            print address
        if u'（' in address:
            temp = address.split('（')
            address = temp[len(temp) - 2]
            print address
        location = getlocation(address)
        row['content']['location'] = location

        if location == (0,0):
            add = {}
            add['name'] = row['name']
            add['address'] = row['content']['address']
            not_found.append(add)
            print address, row['content']['address']

            # time.sleep(1)
        details.append(row)
    fr.close()

    fw = open(filename + '_notfound', 'w')
    fw.write(json.dumps(not_found)) 
    fw.close()

    fw = open(filename + '_location', 'w')
    fw.write(json.dumps(details)) 
    fw.close()

def view(filename):
    fr = open(filename, 'r')
    s = fr.read()
    items = json.loads(s)  
    for row in items:
        print row['name'], row['address']
    print len(items)

if __name__ == '__main__':
    format(sys.argv[1])
    #view(sys.argv[1])

