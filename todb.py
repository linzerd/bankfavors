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


# Insert Biz to DB
def insert_biz(jsonfile):
    db = MySQLdb.connect(host="127.0.0.1",user="root",passwd="123@Abc",db="kayohui")
    db.set_character_set("utf8")
    cur = db.cursor()
    cur.execute('set names utf8')

    files = {'BankOfChina.json':1, 'ZhaoShang.json':5, 'GuangFa.json':10, 'JianShe.json': 3}

    new_biz = "insert into favor_store(name, content, addr, city, city_id, bank_id, circle, category, phone, pic, photos, zip, url, begin_time, lat, lng, status, followers, biz_type, price, ctime) values ('{name}', '{content}', '{addr}', '{city}', '{city_id}', '{bank_id}', '{circle}', '{category}', '{phone}', '{pic}', '{photos}', '{zip}', '{rel_url}', '{begin_time}', '{lat}', '{lng}', '{status}', '{followers}', '{biz_type}', '{prize}', '{ctime}');"

    if not files.has_key(jsonfile):
        print 'no json ' + jsonfile
        return

    cur_bank = files[jsonfile]
    fn = jsonfile
    print fn
    s = open(fn, 'r').read()
    items = json.loads(s)  

    count = 0
    for row in items:
        t = str(datetime.datetime.now())[:19]
        name = row['name']
        if not row['content'].has_key('tel'):
            #print 'no tel', row['url']
            row['content']['tel'] = 0
        if not row['content'].has_key('dicount'):
            continue
        if not row['content'].has_key('address'):
            print 'no address:', row['url']
            row['content']['address'] = ''
        #insert Biz to DB
        v = {
            'name': row['name'],
            'content': db.escape_string(row['content']['dicount']), 
            'addr': db.escape_string(row['content']['address']), 
            'city': row['content']['city'], 
            'city_id': 0, 
            'bank_id': cur_bank, 
            'circle': '', 
            'category': '', 
            'phone': row['content']['tel'], 
            'pic': '', 
            'photos': '', 
            'zip': '0', 
            'rel_url': row['url'], 
            'begin_time': '1900-1-1', 
            'lat': row['content']['location'][0], 
            'lng': row['content']['location'][1], 
            'status': 1,
            'followers': 0,
            'biz_type': 1,
            'prize': 0,
            'ctime': t,
        } 
        biz_sql = new_biz.format(**v)
        count = count + 1
        cur.execute(biz_sql)
        print biz_sql
    print count
    db.close()
     
                    

#insert brand into db
def insert_brand(jsonfile):
    db = MySQLdb.connect(host="127.0.0.1",user="root",passwd="123@Abc",db="kayohui")
    db.set_character_set("utf8")
    cur = db.cursor()
    cur.execute('set names utf8')

    new_brand = "insert into store_band(name, `desc`, found_time, from_area, phone_no, web_site, ctime, category, nav_type, logo, photos, weight, logo_m) values ('{name}', '{desc}' , '{found_time}', '{from_area}', '{phone_no}', '{web_site}', '{ctime}', '{category}', '{nav_type}', '{logo}', '{photos}', '{weight}', '{logo_m}')"

    new_favor = "insert into store_favor(name, brand_id, bank_id, fav_type, content, discount, begin_time, end_time, rule_type, rule_value, time_rule, rel_url, ctime) value  ('{name}', {brand_id}, {bank_id}, {fav_type}, '{content}', {discount}, '{begin_time}', '{end_time}', {rule_type}, {rule_value}, '{time_rule}', '{rel_url}', '{ctime}')"


    files = {'ZhaoShang.json':5, 'GuangFa.json':10, 'JianShe.json': 3}
    
    if not files.has_key(jsonfile):
        print 'no json ' + jsonfile
        return
    brands = {}
    favors = {}
    cur_bank = files[jsonfile]
    fn = jsonfile
    print fn
    s = open(fn, 'r').read()
    items = json.loads(s)  

    for row in items:
        t = str(datetime.datetime.now())[:19]
        name = row['name']
        brand = ''
        if name.find(u'(') > -1:
            brand = name.split(u'(')[0]
        if name.find(u'（') > -1:
            brand = name.split(u'（')[0]
        if brand != '':
            if not brands.has_key(brand):
                print brand
                brand_query_sql = "select id from store_band where name = '%s'" % db.escape_string(brand.encode('utf-8'))
                cur.execute(brand_query_sql)
                rs = cur.fetchone() 
                if rs:
                    brands[brand] = int(rs[0])
                    #print brand, int(rs[0])
                else:
                    #insert Brand and get the Brand_id
                    v = {
                        'name': db.escape_string(brand.encode('utf-8')),
                        'desc': db.escape_string(brand.encode('utf-8')),
                        'found_time': 0,
                        'from_area': 0, 
                        'phone_no': 0,
                        'web_site': '', 
                        'ctime': t, 
                        'category': 1,
                        'nav_type': 1, 
                        'logo': '',
                        'photos': '',
                        'weight': 0,
                        'logo_m': '',
                    }
                    brand_insert_sql = new_brand.format(**v)
                    # print brand_insert_sql
                    cur.execute(brand_insert_sql)
                    brands[brand] = cur.lastrowid

                #insert Favor to DB
                #TODO: if the favor already insert
                discount = 0
                if row['content'].has_key('fav'):
                    mc = re.compile(u'([0-9]\.?[0-9]?)折')
                    ret = mc.search(row['content']['fav'])
                    if ret:
                        discount = int(float(ret.group(1)) * 10)

                mc = re.compile(u'([0-9]+年[0-9]+月[0-9]+日)')
                ret = mc.search(row['content']['fav_time'])
                start = 0
                if not ret:
                    end = 0
                else:
                    #start = ret.group(1)
                    end = ret.group()
                name = row['content'][u'fav']
                if len(name) > 50:
                    name = u'优惠商家,刷卡享优惠'
                    
                #print start, end
                v = {
                    'name': db.escape_string(name.encode('utf-8')),
                    'brand_id': brands[brand],
                    'bank_id': cur_bank, 
                    'fav_type': 0,
                    'content': db.escape_string(row['content']['fav'].encode('utf-8')),
                    'discount': discount,
                    'begin_time': start,
                    'end_time': end,
                    'rule_type': 0,
                    'rule_value': 0,
                    'time_rule': '',
                    'rel_url': row['url'],
                    'ctime': t,
                }
                favor_insert_sql = new_favor.format(**v)
                print favor_insert_sql
                cur.execute(favor_insert_sql)

    print 'Brands: ' + str(len(brands))
    print 'Total item: ' + str(len(items))
    db.close()


def zhaoshang():
    s = open('ZhaoShang.json', 'r').read()
    x = json.loads(s)
    t = str(datetime.datetime.now())[:19]
    for row in x:
        c = row['content']
        v = {'name':row['name'].encode('utf-8').replace("'", "''"), 
             'addr':c[u'商户地址'].encode('utf-8'), 
             'country':'北京',
             'band':'', 
             'phone':c[u'服务电话'].encode('utf-8'), 
             'photo':'', 'date':t,
             'lat':c['location'][0], 'lng':c['location'][1], 
             'desc':c[u'商户介绍'].encode('utf-8').replace("'", "''")
             }
        sql = sqlfmt.format(**v)
        print sql

def bankofchina():
    s = open('bankofchina.json', 'r').read()
    x = json.loads(s)
    t = str(datetime.datetime.now())[:19]
    for row in x:
        c = row['content']
        v = {'name':row['name'].encode('utf-8').replace("'", "''"), 
             'addr':c[u'商户地址'].encode('utf-8'), 
             'country':'北京',
             'band':'', 
             'phone':c[u'联系电话'].encode('utf-8'), 
             'photo':'', 'date':t,
             'lat':c['location'][0], 'lng':c['location'][1], 
             'desc':"",
             }
        sql = sqlfmt.format(**v)
        print sql


def bankofbeijing():
    s = open('BankOfBeijing.json', 'r').read()
    x = json.loads(s)
    t = str(datetime.datetime.now())[:19]
    for row in x:
        c = row['content']
        v = {'name':row['name'].encode('utf-8').replace("'", "''"), 
             'addr':c[u'商户地址'].encode('utf-8'), 
             'country':'北京',
             'band':'', 
             'phone':c.get(u'联系电话', '').encode('utf-8'), 
             'photo':'', 'date':t,
             'lat':c['location'][0], 'lng':c['location'][1], 
             'desc':c['desc'].encode('utf-8').replace("'", "''")
             }
        sql = sqlfmt.format(**v)
        print sql


def mingsheng():
    s = open('MingSheng.json', 'r').read()
    x = json.loads(s)
    t = str(datetime.datetime.now())[:19]
    for row in x:
        c = row['content']
        v = {'name':row['name'].encode('utf-8').replace("'", "''"), 
             'addr':c[u'联系地址'].encode('utf-8'), 
             'country':'北京',
             'band':'', 
             'phone':c[u'联系方式'].encode('utf-8'), 
             'photo':'', 'date':t,
             'lat':c['location'][0], 'lng':c['location'][1], 
             'desc':c[u'商户简介'].encode('utf-8').replace("'", "''")
             }
        sql = sqlfmt.format(**v)
        print sql


#################
if __name__ == '__main__':
    #if sys.argv[1] in globals():
    #    globals()[sys.argv[1]]()
    #else:
    #insert_brand(sys.argv[1])
    insert_biz(sys.argv[1])

