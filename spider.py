# -*- coding: utf-8 -*-
import os, sys
import re, copy
import json, time
import urllib, urlparse
from pylibcurl import Curl, const, lib, CurlError
from pymongo import Connection
import ctypes
import cStringIO
from fetion import fetion

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
            return lat, lng 
    except:
        fetion('fetch error!' + addr)
        pass
    return 0, 0 

class Spider:
    def __init__(self, url=''):
        self.url = url
        #self.cateurl = cateurl

        self.content_type_re = re.compile(r'Content-Type:[ ]*text/html;[ ]*charset=([a-zA-Z0-9\-]+)')
        self.charset = 'utf-8'
        self.filename = ''
        self.refresh_location_key = u'address'

    def run(self):
        pass 

    def getwebdata(self, url):
        headbuf = cStringIO.StringIO()
        bodybuf = cStringIO.StringIO()
 
        curl = Curl(headerfunction=headbuf.write, writefunction=bodybuf.write)
        curl.url = url
        curl.httpget = 1 
        curl.perform()
        curl.close() 

        headdata = headbuf.getvalue() 
    
        ret = self.content_type_re.search(headdata)
        if ret:
            charset = ret.groups()[0].lower()
            if charset == 'gb2312' or charset == 'gbk':
                charset = 'gbk'
            return unicode(bodybuf.getvalue(), charset, 'ignore')
        else:
            return unicode(bodybuf.getvalue(), self.charset)

    def postwebdata(self, url, data):
        headbuf = cStringIO.StringIO()
        bodybuf = cStringIO.StringIO()
        
        #print 'post size:', len(urllib.urlencode(data))
        curl = Curl(headerfunction=headbuf.write, writefunction=bodybuf.write)
        curl.url = url
        curl.post = 1 
        curl.autoreferer = 1
        
        cookie_file = 'cookie.txt'
        curl.cookiefile = cookie_file
        curl.cookiejar  = cookie_file

        curl.postfields = urllib.urlencode(data)
        curl.perform()
        curl.close() 

        headdata = headbuf.getvalue() 
    
        ret = self.content_type_re.search(headdata)
        if ret:
            charset = ret.groups()[0].lower()
            if charset == 'gb2312' or charset == 'gbk':
                charset = 'gbk'
            return unicode(bodybuf.getvalue(), charset, 'ignore')
        else:
            return unicode(bodybuf.getvalue(), self.charset)

    def get_content_url(self, data):
        result = []
        rets = self.content_url_re.findall(data)
        return rets

    def get_content(self, data):
        result = {}
        for mc in self.content_re:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                result[mc[0]] = re.sub('<[/]?a[^>]*>', '', s).strip()

        return result         

    def get_logo(self, data):
        ret = self.logo_re.search(data)
        if ret:
            return ret.groups()[0]
        return ''

    def get_pages(self, data):
        ret = self.page_re.search(data)
        if not ret:
            return 0
        return int(ret.groups()[0])


    def refresh_content(self, name=None):
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)

        for row in result:
            if name and name != row['name']:
                continue
            url  = row['url']  
            print '====== %s:%s ======' % (row['name'], url)
            data = self.getwebdata(url)
            rets = self.get_content(data)
            for k,v in rets.iteritems():
                print k, v
            
            if row['content'].has_key('location'):
                rets['location'] = row['content']['location']
            if rets:
                row['content'] = rets

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

    def refresh_location(self, name=None):
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)
        error_data = []

        for row in result:
            content = row['content']
            if name and name != content['name']:
                continue
            if len(row['content']) < 3 or not content.has_key('address'):
                print 'no address!!!:', row
                error_data.append(row['url'])
                result.remove(row)
                continue
            if row.has_key('city'):
                address = row['city'] + content[self.refresh_location_key]
            else:
                address = content[self.refresh_location_key]
            print content['name'], address
            content['location'] = getlocation(address)
            time.sleep(2)
            row['name'] = content['name']

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

        f = open(self.filename + '_miss', 'w')
        f.write(json.dumps(error_data))
        f.close()

        fetion('location query finished.')

    def refresh_logo(self, name=None):
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)

        for row in result:
            if name and name != row['name']:
                continue
            content = row['content']
            print row['name'], row['url']
            data = self.getwebdata(row['url'])
            logo = self.get_logo(data)
            if logo:
                logo = self.url_complete(row['url'], logo)
            print logo
            row['logo'] = logo

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

    def url_complete(self, requrl, url):
        if url.startswith(('http://', 'https://')):
            return
        if url[0] == '/':
            x = urlparse.urlparse(requrl)
            return '%s://%s%s' % (x.scheme, x.netloc, url)
        return os.path.dirname(requrl) + '/' + url

class ZhaoShang (Spider):
    def __init__(self):
        Spider.__init__(self)
    
        self.url = 'http://best.cmbchina.com/QueryResult.aspx?city=%s&class=50&subclass=&ccid=#listTop'
        #self.url = 'http://best.cmbchina.com/Default.aspx?city=0010&class=50'
        self.baseurl = 'http://best.cmbchina.com/'
        #self.cateurl = 'http://best.cmbchina.com/QueryResult.aspx?city=0010&class=50&subclass=%s&ccid=#listTop'
        self.postdata = {'city':'0010', 'class':'50',
                    '__EVENTTARGET':'', 
                    '__EVENTARGUMENT':'',
                    '__VIEWSTATE':'',
                    '__EVENTVALIDATION':'',
                    }
        self.filename = 'ZhaoShang.json'
        self.logo_re = re.compile(u'src="([^"]+)" onerror="this.src=\'images/noimage.gif\'">')
        self.refresh_location_key = u'商户地址'
        self.bank_id = 5
        print '====== ZhaoShang ======'

    def go(self):
        baseurl = 'http://best.cmbchina.com/'
        postdata = copy.copy(self.postdata)

        result = []
        count  = 0
        pagecur = 0

        # Mongodb Connect
        con = Connection()
        db = con.kyh
        favors = db.favor

        #favors.find()

        s = self.getwebdata(self.url)
        cities = self.get_cities(s)
        for city in cities:
            print city[0], city[1]
            fetion(city[1].encode('utf-8'))
            postdata['city'] = city[0]

            pagecur += 1
            print '------ page:%d target:%s ------' % (pagecur,postdata['__EVENTTARGET'])
            if count > 0:
                s = self.postwebdata(self.url % city[0], postdata)
            else:
                s = self.getwebdata(self.url % city[0])
            total = self.get_count(s)
            pages = total / 10 + 1

            print pages
            for i in range(1,pages):
                if i > 1:
                    s = self.postwebdata(self.url % city[0], postdata)
                else:
                    s = self.getwebdata(self.url % city[0])
     
                print 'content_url page:%d' % i

                ret = self.get_content_urls(s)
                print 'found:', len(ret)
                for x in ret:
                    #print c
                    #result.append({'name':x[1].strip(), 'url':baseurl + x[0].strip(), 'content': c})
                    favor = favors.find_one({'url':baseurl + x[0].strip()})
                    #print 'favor:',favor
                    if favor == None:
                        content = self.getwebdata(self.baseurl + x[0].strip())
                        c = self.get_content(content)
                        c['bank'] = self.bank_id
                        c['url'] = baseurl + x[0].strip()
                        favors.insert(c)
                        print 'insert:', x[0].strip(), x[1].strip()
                        time.sleep(1)
                    else:
                        print 'skip:', x[0].strip(), x[1].strip()
                        continue
                
                if not self.get_page_next(s, postdata, i):
                    print 'page end'
                    break

        #f = open(self.filename, 'w')
        #f.write(json.dumps(result))
        #f.close()
        fetion(u'CMB Bank fetch Finished!!!')

    def refresh_content(self, name=None): 
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)

        count = 0
        for row in result:
            if name and name != row['name']:
                continue
            url  = row['url']  
            print '====== %d %s:%s ======' % (count, row['name'], url)
            data = self.getwebdata(url)
            rets = self.get_content(data)
            for k,v in rets.iteritems():
                if k != 'chain':
                    print k, v
                else:
                    print k, len(v)
            if rets:
                row['content'] = rets
            count += 1

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        #f = open(self.filename, 'w')
        #f.write(json.dumps(result))
        #f.close()


    def get_cities(self, data):
        start = u'<div id="CityContent">'
        end = u'<iframe id="IfrShadow"'

        pos1 = data.find(start)
        if pos1 < 0:
            return []
        pos2 = data.find(end, pos1)
        if pos2 < 0:
            return []

        s = data[pos1+len(start):pos2]
        #print s 
        mc = re.compile(u'<a href=\'Default.aspx\?city=([0-9]+)&&class=50\' class="CityItem" cname="特惠商户" oname=\'.*?\' otype="文字链接">(.*)</a>')
        #mc = re.compile(u'<option value="([0-9]+)">--(.*)</option>')
        rets = mc.findall(s)
        #print rets
        
        return rets


    def get_zone(self, data):
        start = u'<option selected="selected" value="">所有地区</option>'
        end = u'</select>'

        pos1 = data.find(start)
        if pos1 < 0:
            return []
        pos2 = data.find(end, pos1)
        if pos2 < 0:
            return []

        s = data[pos1+len(start):pos2]
        #print s
        
        mc = re.compile(u'<option value="([0-9]+)">--(.*)</option>')
        rets = mc.findall(s)
        #print rets
        
        return rets

    def get_content_urls(self, data):
        start = u'<td width="572" background="images/favshop_left_bg2_02.gif">'
        end = u'</tr><tr class="mpager" align="right">'

        pos1 = data.find(start)
        if pos1 < 0:
            return []
        pos2 = data.find(end, pos1)
        if pos2 < 0:
            return []
        s = data[pos1+len(start):pos2]

        mc = re.compile(u'商户名称： <a href="([^"]+)".*?class="redName" target="_blank">(.*?)</a>', re.DOTALL)
        rets = mc.findall(s)
        return rets    

    def get_content(self, data):
        mcs = [
            ('name', re.compile(u'商 户 名 称：</a>.*?</td>.*?<td align="left">(.*?)</td>', re.DOTALL)),
            ('address', re.compile(u'商 户 地 址：</a>.*?</td>.*?<td align="left" valign="top">(.*?)</td>', re.DOTALL)),
            ('tel', re.compile(u'服 务 电 话：</a> </a>.*?</td>.*?<td align="left">.*?<a class="black">.*?([0-9\-]+)', re.DOTALL)),
            ('price', re.compile(u'人 均 消 费：￥([0-9\-]+)', re.DOTALL)),
            ('discount', re.compile(u'持 卡 优 惠：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            ('detail', re.compile(u'优 惠 细 则：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            ('content', re.compile(u'商 户 介 绍：.*?</td>.*?<td class="black" align="left" valign="top">(.*?)</td>', re.DOTALL)),
            ('special', re.compile(u'招 牌 服 务：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            ('card', re.compile(u'刷 卡 消 费：.*?</td>.*?<td class="black" align="left">(.*?)&nbsp;', re.DOTALL)),
            ('parking', re.compile(u'停 车 环 境：(.*?)&nbsp;', re.DOTALL)),
            ('end', re.compile(u'持卡优惠截止日期：.*?([0-9\/]+)', re.DOTALL)),
            ('trans', re.compile(u'公 交 指 南：.*?</td>.*?<td class="black" valign="top" align="left">(.*?)</td>', re.DOTALL)),
            ('logo', re.compile('<img style="cursor: hand" height="130px" border="0" align="middle" width="180px".*?src="([^"]+)" onerror="this\.src=\'images/noimage\.gif\'">', re.DOTALL)),
        ]

        result = {}
        for mc in mcs:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                result[mc[0]] = re.sub('<[/]?a[^>]*>', '', s).strip()

        #chain = self.get_chain(data)
        #result['chain'] = chain 
        return result         

    def get_chain(self, data):
        start = u'其他连锁店'
        end   = u'<td width="572" background="images/favshop_left_bg2_01.gif" height="10">'
        
        pos1 = data.find(start)
        if pos1 < 0:
            return []
        pos2 = data.find(end, pos1)
        if pos2 < 0:
            return []
        s = data[pos1+len(start):pos2]

        mc = re.compile('<a href="([^"]+)".*?class="black">(.*?)</a>', re.DOTALL)
   
        result = []
        rets = mc.findall(s)
        for x in rets:
            #print x[0], x[1]
            result.append([x[0], x[1].strip()])
        return result

    def get_page_info(self, data, postdata):
        items = {'__VIEWSTATE':re.compile(u'id="__VIEWSTATE" value="([^"]+)"'),
                 '__EVENTVALIDATION':re.compile(u'id="__EVENTVALIDATION" value="([^"]+)'),}

        for k,v in items.iteritems():
            ret = v.search(data) 
            if ret:
                postdata[k] = ret.groups()[0]

    def get_count(self, data):
        mc = re.compile(u'特惠商户共有([0-9]+)家')
        ret = mc.search(data)
        if not ret:
            return 0
        return int(ret.groups()[0])


    def get_page_next(self, data, postdata, pagecur):
        self.get_page_info(data, postdata)
        mc = re.compile(u"<a href=\"javascript:__doPostBack\('([a-zA-Z0-9\$]+)',''\)\">([0-9\.]+)</a>")
        pagenext = int(pagecur) + 1
        result = []
        rets = mc.findall(data)
        
        #for x in rets:
        #    print 'page:', x[0], x[1]
      
        if not rets:
            return rets
        page10next = None 
        if rets[0][1] == '...':
            rets = rets[1:]
        if rets[-1][1] == '...':
            page10next = rets[-1]
            rets = rets[:-1] 
        #print 'page10next:', page10next, 'rets:', len(rets)
        for x in rets:
            #print 'check:', int(x[1]), pagenext
            if int(x[1]) == pagenext:
                postdata['__EVENTTARGET'] = x[0]
                return True

        if page10next:
            #print 'page 10 next'
            postdata['__EVENTTARGET'] = page10next[0]
            return True

        return False
        



# Ecitic Bank
class ZhongXin(Spider):
    def __init__(self):
        Spider.__init__(self)
        # https://creditcard.ecitic.com/citiccard/ecitic/work.do?func=queryVendorInf&dom=%3Crequest%3E%3Ctypeinfo%20id=%22queryVendorList%22%20city_id=%22%22%20card_type_id=%22%22%20play_id=%22%22%20trade_id=%22%22%20sub_trade_id=%22%22%20city_business_id=%22%22%20card_level=%22%22%20key=%22%22%20current_page=%221%22%20page_rows=%2220%22/%3E%3C/request%3E 
        self.url = 'https://creditcard.ecitic.com/citiccard/ecitic/work.do?func=queryVendorInf&dom=<request><typeinfo id="queryVendorList" city_id="" card_type_id="" play_id="" trade_id="" sub_trade_id="" city_business_id="" card_level="" key="" current_page="%d" page_rows="20"/></request>'
        #self.url = 'http://best.cmbchina.com/Default.aspx?city=0010&class=50'
        self.baseurl = 'http://best.cmbchina.com/'
        #self.cateurl = 'http://best.cmbchina.com/QueryResult.aspx?city=0010&class=50&subclass=%s&ccid=#listTop'
        self.logo_re = re.compile(u'src="([^"]+)" onerror="this.src=\'images/noimage.gif\'">')
        self.refresh_location_key = u'商户地址'

        print '====== Zhong Xin Bank ======'

    def go(self):
        result = []
        count  = 0
        pagecur = 0
        perpage = 20

        while True:
            time.sleep(1)
            pagecur += 1
            url = (self.url % (pagecur, )).replace(' ', '%20')
            print url
            s = self.getwebdata(url)
            print s
            return
            ret = self.get_content_urls(s)
            print 'found:', len(ret)
            for x in ret:
                #print 'contente url:', x[0].strip(), x[1].strip()
                result.append({'name':x[1].strip(), 'url':baseurl + x[0].strip(), 'content':{}})
            
            if not self.get_page_next(s, postdata, pagecur):
                print 'page end'
                break
            count += 1

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

    def refresh_content(self, name=None): 
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)

        count = 0
        for row in result:
            if name and name != row['name']:
                continue
            url  = row['url']  
            print '====== %d %s:%s ======' % (count, row['name'], url)
            data = self.getwebdata(url)
            rets = self.get_content(data)
            for k,v in rets.iteritems():
                if k != 'chain':
                    print k, v
                else:
                    print k, len(v)
            if rets:
                row['content'] = rets
            count += 1

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

    def get_content(self, data):
        mcs = [
            (u'商户名称', re.compile(u'商 户 名 称：</a>.*?</td>.*?<td align="left">(.*?)</td>', re.DOTALL)),
            (u'商户地址', re.compile(u'商 户 地 址：</a>.*?</td>.*?<td align="left" valign="top">(.*?)</td>', re.DOTALL)),
            (u'服务电话', re.compile(u'服 务 电 话：</a> </a>.*?</td>.*?<td align="left">.*?<a class="black">.*?([0-9\-]+)', re.DOTALL)),
            (u'人均消费', re.compile(u'人 均 消 费：￥([0-9\-]+)', re.DOTALL)),
            (u'持卡优惠', re.compile(u'持 卡 优 惠：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            (u'优惠细则', re.compile(u'优 惠 细 则：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            (u'商户介绍', re.compile(u'商 户 介 绍：.*?</td>.*?<td class="black" align="left" valign="top">(.*?)</td>', re.DOTALL)),
            (u'招牌服务', re.compile(u'招 牌 服 务：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            (u'刷卡消费', re.compile(u'刷 卡 消 费：.*?</td>.*?<td class="black" align="left">(.*?)&nbsp;', re.DOTALL)),
            (u'停车环境', re.compile(u'停 车 环 境：(.*?)&nbsp;', re.DOTALL)),
            (u'持卡优惠截止日期', re.compile(u'持卡优惠截止日期：.*?([0-9\/]+)', re.DOTALL)),
            (u'公交指南', re.compile(u'公 交 指 南：.*?</td>.*?<td class="black" valign="top" align="left">(.*?)</td>', re.DOTALL)),
            (u'logo', re.compile('<img style="cursor: hand" height="130px" border="0" align="middle" width="180px".*?src="([^"]+)" onerror="this\.src=\'images/noimage\.gif\'">', re.DOTALL)),
        ]

        result = {}
        for mc in mcs:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                result[mc[0]] = re.sub('<[/]?a[^>]*>', '', s).strip()

        chain = self.get_chain(data)
        result['chain'] = chain 
        return result         

class BankOfChinaWap (Spider):
    # to be finished
    def __init__(self):
        Spider.__init__(self)
        self.url = 'http://srh.bankofchina.com/search/wap/rwm_l.jsp?curpage=1&provice=-1&city=-1&btype=-1&stype=-1&keyword='
        self.filename = 'BankOfChina.json'
        self.refresh_location_key = u'address'
        self.charset = 'gbk'
        print '======= BankOfChina ======'

    def go(self):
        url  = 'http://srh.bankofchina.com/search/merchant09/merchant_search.jsp'
        postdata = {'SS':'', 'CS':'', 'FL':'1582,1583,1584,1585,1586,1587,1588,1589,1590,1591,1592,1593,1594,1595,1596,1597,1598,1599,1600,1601,1602,1603,1604,1605,1606,1607,1608,1609,1610,1611,1612,1613,1614,1615,1616,1617,1618,1619,1620,1621,1622,1623,1624,1625,1626,1627,1628,1629,1630,1631,1631,1632,1633,1634',
                'ZL':0, 'sword':'', 'cmgsearch':'', 'page':'1'} 
        data = self.postwebdata(url, postdata) 
        #print data
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            print '====== get_content_url:%d ======' % i
            postdata['page'] = str(i)
            try:
                data = self.postwebdata(url, postdata) 
            except:
                fetion('try ' + url + ' exception; page: ' + str(i)) 
                continue
            rets = self.get_content_url(data) 
            
            for x in rets: 
                print '====== get_content:%s %s ======' % x
                data = self.getwebdata(x[0])
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                result.append({'name':x[1], 'url':x[0], 'content':rets})     
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

        return result

    def get_content_url(self, data):
        mc = re.compile(u'<td height="20" valign="top"><a href="([^"]+)" target="_blank">(.*?)</a></td>') 
        result = []
        rets = mc.findall(data)
        return rets

    def get_content(self, data):
        mcs = [
            ('name', re.compile(u'商户名称：</td>.*?<td colspan="3">(.*?)</td>', re.DOTALL)),
            ('type', re.compile(u'商户类别：</td>.*?<td width="161">(.*?)</td>', re.DOTALL)),
            ('address', re.compile(u'商户地址：</td>.*?<td colspan="5">(.*?)</td>', re.DOTALL)),
            ('tel', re.compile(u'联系电话：</td>.*?<td colspan="5">([0-9\-]+)</td>', re.DOTALL)),
            ('city', re.compile(u'所在城市：</td>.*?<td width="141">(.*?)</td>', re.DOTALL)),
            ('begin', re.compile(u'优惠起始日期：([0-9]+年[0-9]+月[0-9]+日)', re.DOTALL)),
            ('end', re.compile(u'优惠截止日期：([0-9]+年[0-9]+月[0-9]+日)', re.DOTALL)),
            ('dicount', re.compile(u'<td width="290" valign="top" class="dashlv"><P>(.*?)</P></td>')),
        ]

        result = {}
        for mc in mcs:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                result[mc[0]] = re.sub('<[/]?a[^>]*>', '', s).strip()

        return result         

    def get_pages(self, data):
        mc = re.compile(u'</font>个商户 第<font color="red"> [0-9]+ / ([0-9]+)</font> 页')
        ret = mc.search(data)
        if not ret:
            return 0
        return int(ret.groups()[0])




class BankOfChina (Spider):
    def __init__(self):
        Spider.__init__(self)
        self.filename = 'BankOfChina.json'
        self.refresh_location_key = u'address'
        self.charset = 'gbk'
        print '======= BankOfChina ======'

    def go(self):
        url  = 'http://srh.bankofchina.com/search/merchant09/merchant_search.jsp'
        postdata = {'SS':'', 'CS':'', 'FL':'1582,1583,1584,1585,1586,1587,1588,1589,1590,1591,1592,1593,1594,1595,1596,1597,1598,1599,1600,1601,1602,1603,1604,1605,1606,1607,1608,1609,1610,1611,1612,1613,1614,1615,1616,1617,1618,1619,1620,1621,1622,1623,1624,1625,1626,1627,1628,1629,1630,1631,1631,1632,1633,1634',
                'ZL':0, 'sword':'', 'cmgsearch':'', 'page':'1'} 
        data = self.postwebdata(url, postdata) 
        #print data
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            print '====== get_content_url:%d ======' % i
            postdata['page'] = str(i)
            try:
                data = self.postwebdata(url, postdata) 
            except:
                fetion('try ' + url + ' exception; page: ' + str(i)) 
                continue
            rets = self.get_content_url(data) 
            
            for x in rets: 
                print '====== get_content:%s %s ======' % x
                data = self.getwebdata(x[0])
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                result.append({'name':x[1], 'url':x[0], 'content':rets})     
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

        return result

    def get_content_url(self, data):
        mc = re.compile(u'<td height="20" valign="top"><a href="([^"]+)" target="_blank">(.*?)</a></td>') 
        result = []
        rets = mc.findall(data)
        return rets

    def get_content(self, data):
        mcs = [
            ('name', re.compile(u'商户名称：</td>.*?<td colspan="3">(.*?)</td>', re.DOTALL)),
            ('type', re.compile(u'商户类别：</td>.*?<td width="161">(.*?)</td>', re.DOTALL)),
            ('address', re.compile(u'商户地址：</td>.*?<td colspan="5">(.*?)</td>', re.DOTALL)),
            ('tel', re.compile(u'联系电话：</td>.*?<td colspan="5">([0-9\-]+)</td>', re.DOTALL)),
            ('city', re.compile(u'所在城市：</td>.*?<td width="141">(.*?)</td>', re.DOTALL)),
            ('begin', re.compile(u'优惠起始日期：([0-9]+年[0-9]+月[0-9]+日)', re.DOTALL)),
            ('end', re.compile(u'优惠截止日期：([0-9]+年[0-9]+月[0-9]+日)', re.DOTALL)),
            ('dicount', re.compile(u'<td width="290" valign="top" class="dashlv"><P>(.*?)</P></td>')),
        ]

        result = {}
        for mc in mcs:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                result[mc[0]] = re.sub('<[/]?a[^>]*>', '', s).strip()

        return result         

    def get_pages(self, data):
        mc = re.compile(u'</font>个商户 第<font color="red"> [0-9]+ / ([0-9]+)</font> 页')
        ret = mc.search(data)
        if not ret:
            return 0
        return int(ret.groups()[0])

class BankOfBeijing (Spider):
    def __init__(self):
        Spider.__init__(self)
        self.charset = 'utf-8'
        self.filename = 'BankOfBeijing.json'
        self.refresh_location_key = u'商户地址'
        self.logo_re = re.compile(u'<img src="([^"]+)" height="154" width="142" border="0" />')
        print '====== BankOfBeijing ======'

    def go(self):
        urlfirst = 'http://www.bankofbeijing.com.cn/creditcard/company_1.html'
        urltpl   = 'http://www.bankofbeijing.com.cn/creditcard/company_1_%d.html'
        urlbase  = 'http://www.bankofbeijing.com.cn'

        data = self.getwebdata(urlfirst)
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            if i == 1:
                url = urlfirst
            else:
                url = urltpl % i
            print '====== get_content_url:%s ======' % url
            data = self.getwebdata(url) 
            rets = self.get_content_url(data) 
            
            for x in rets: 
                contenturl = urlbase + x[0].strip()
                print '====== get_content:%s %s ======' % x
                data = self.getwebdata(contenturl)
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                result.append({'name':x[1].strip(), 'url':contenturl, 'content':rets})     

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

        return result

    def get_content_url(self, data):
        mc = re.compile(u'<span class="f_000_12"><a href="([^"]+)" target="_blank">(.*?)</a></span>') 
        result = []
        rets = mc.findall(data)
        return rets

    def get_content(self, data):
        mcs = [
            (u'商户地址', re.compile(u'(?:地址|地点)：(.*?)<', re.DOTALL)),
            (u'联系电话', re.compile(u'电话[： ]?([0-9\-－]+)', re.DOTALL)),
            (u'优惠截止日期', re.compile(u'(?:时间|日期)：([0-9\.\-]+)', re.DOTALL)),
            #(u'desc', re.compile(u'<span class="f_666_12"><p>(.*?)</p>', re.DOTALL)),
            (u'desc', re.compile(u'<span class="f_666_12"><p[^>]*>(.*?)<(?:hr|/p)', re.DOTALL)),
        ]

        result = {}
        for mc in mcs:
            ret = mc[1].search(data)
            if ret:
                s = ret.groups()[0]
                s = re.sub('<[/]?a[^>]*>', '', s).strip()
                s = re.sub('<[/]?p[^>]*>', '', s).strip()
                result[mc[0]] = s

        return result         

    def get_pages(self, data):
        mc = re.compile(u'<a class="last" href="/creditcard/company_1_([0-9]+).html">末页</a>')
        ret = mc.search(data)
        if not ret:
            return 0
        return int(ret.groups()[0])

class MingSheng (Spider):
    def __init__(self):
        Spider.__init__(self)
        print '====== MingSheng ======'
        #self.url = 'http://creditcard.cmbc.com.cn/Ex-gratiaBusiness/List.aspx?cityid=&categoryid=1&businesstype=&page=%d'
        self.url = 'http://creditcard.cmbc.com.cn/Ex-gratiaBusiness/List.aspx?cityid=1&categoryid=1&businesstype=1&page=%d'

        self.content_url_re = re.compile(u'商户名称：<font style="color:#f38c05;"><a target="_blank"  href=\'([^\']+)\' class="a_name">(.*?)</a>')

        self.page_re = re.compile(u'page=([0-9]+)">尾页')
        #self.refresh_location_key = ''
        self.filename = 'MingSheng.json'
        self.refresh_location_key = u'联系地址'

        self.content_re = [
            (u'分类', re.compile(u'所属分类：<span id="lblMerchantTypeDes">(.*?)</span>')),
            (u'优惠截止日期', re.compile(u'优惠截止日期：.*?<span id="lblEndDate">(.*?)</span>', re.DOTALL)),
            (u'联系方式', re.compile(u'联系方式：</font>.*?([0-9\-]+)', re.DOTALL)),
            (u'联系地址', re.compile(u'联系地址：</font>(.*?)</div>', re.DOTALL)),
            (u'商户简介', re.compile(u'商户简介:.*?<li>(.*?)<li', re.DOTALL)),
            (u'优惠折扣', re.compile(u'优惠折扣:.*?<li>.*?<span id="lblZk">(.*?)</span>', re.DOTALL)),
            ]

        self.logo_re = re.compile(u'<img src="([^"]+)" id="merchantLogo" width="175" height="133" />')

    def go(self):
        urlbase = 'http://creditcard.cmbc.com.cn/Ex-gratiaBusiness/'
        data = self.getwebdata(self.url % 1)
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            url = self.url % i
            print '====== get_content_url:%s ======' % url
            data = self.getwebdata(url) 
            rets = self.get_content_url(data) 
            print 'content urls:', len(rets) 
            for x in rets: 
                contenturl = urlbase + x[0]
                print '====== get_content:%s %s ======' % x
                print 'url:', contenturl
                data = self.getwebdata(contenturl)
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                result.append({'name':x[1], 'url':contenturl, 'content':rets})     

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()


# GuangFa Bank New From Wap
class GuangFaNew (Spider):
    def __init__(self):
        Spider.__init__(self)
        print '====== GuangFa ======'
        # self.url = 'http://card.cgbchina.com.cn/Channel/1113974'
        self.url = 'https://wap.cgbchina.com.cn/commerceQuery.do?comQueryArea=000&comQueryType=000&comQueryName=&turnPageBeginPos=%d&turnPageShowNum=%d&turnPageTotalNum=7698&turnPageSerialNo=5LV637L6EU&%s'
        self.baseurl = 'https://wap.cgbchina.com.cn'
        #self.content_url_re = re.compile(u'商户名称：<font style="color:#f38c05;"><a target="_blank"  href=\'([^\']+)\' class="a_name">(.*?)</a>')
        #/commerceQueryDetail.do?comQueryType=000&amp;comQueryName=&amp;comQueryArea=000&amp;commerceName=%E9%9C%87%E8%81%94%E7%94%B5%E8%84%91%E7%BB%8F%E8%90%A5%E9%83%A8&amp;commerceArea=022&amp;commerceType=006&amp;address=%E4%BD%9B%E5%B1%B1%E5%B8%82%E9%A1%BA%E5%BE%B7%E5%8C%BA%E5%A4%A7%E8%89%AF%E5%87%A4%E5%B1%B1%E4%B8%AD%E8%B7%AF%E9%9D%92%E5%B0%91%E5%B9%B4%E5%AE%AB%E4%B8%9C%E4%BE%A7%E6%AD%A3%E4%B8%9A%E5%95%86%E8%B4%B8%E4%B8%AD%E5%BF%83%E7%AC%AC%E4%B8%89%E5%B1%8223103%E5%8F%B7&amp;phone=0757-22207066&amp;beginTime=2011-01-15&amp;endTime=2012-12-31&amp;privilegeInfo=%E5%88%B7%E5%B9%BF%E5%8F%91%E5%8D%A1%E6%B6%88%E8%B4%B9%E5%8F%AF%E4%BA%AB%E5%8F%97%E7%AC%94%E8%AE%B0%E6%9C%AC%E3%80%81%E7%BB%84%E8%A3%85%E7%94%B5%E8%84%91%E3%80%81%E6%98%BE%E7%A4%BA%E5%99%A8%E3%80%81%E7%94%B5%E8%84%91%E9%85%8D%E4%BB%B68.5%E6%8A%98%E8%B5%B7%EF%BC%8C%E9%80%81%E4%BB%B7%E5%80%BC100%E5%85%83%E7%A4%BC%E5%93%81&amp;turnPageTotalNum=7698&amp;turnPageSerialNo=5LV637L6EU&amp;turnPageBeginPos=1&amp;turnPageShowNum=10&amp;JSESSIONID=00003go05LVHOoUcazTZdM0QQXC:15m2il27v&amp;sid=0.5436242708404943
        self.content_url_re = re.compile(r'<a href="/commerceQueryDetail.do\?([^"]+)">(.*?)</a>', re.DOTALL)

        # 816)" >尾页
        #self.page_re = re.compile(u'&#x5F53;&#x524D;&#x9875;: 1/([0-9]+)')
        # total num
        self.page_re = re.compile('<span>&#x5171;&#x6709;([0-9]+)&#x6761;')

        #self.refresh_location_key = ''
        self.filename = 'GuangFa.json'
        self.refresh_location_key = u'address'

        self.sess_re = re.compile('<form action="(.*?)" ')

        self.logo_re = re.compile(u'<img src="([^"]+)" id="merchantLogo" width="175" height="133" />')

    def get_sessionid(self, data):
        ret = self.sess_re.search(data)
        if not ret:
            return 0
        return ret.groups()[0].replace('&amp;', '&')

    def urldecode(self, url):
        result={}
        url=url.split("?",1)
        if len(url)==2:
            for i in url[1].split("&"):
                i=i.split("=",1)
                if len(i)==2:
                    result[urllib.unquote(i[0])]=urllib.unquote(i[1])
        return result


    def go(self):
        data = self.getwebdata(self.url % (1, 10, ''))
        sessionid_post = self.get_sessionid(data)
        print sessionid_post
        postdata = {next: '&#x8FD4;&#x56DE;'}

        content = self.postwebdata(self.baseurl + sessionid_post, postdata)
        sessionid_post = self.get_sessionid(content)
        sessionid = sessionid_post.split('?')[1]
        print sessionid

        print self.url % (1, 10, sessionid)

        postdata = {
           'comQueryArea': '000',
           'comQueryName': '', 
           'comQueryType': '000',
           'next': '下一步',
           'turnPageBeginPos': '1',
           'turnPageShowNum': '10',
        }
        data = self.postwebdata('https://wap.cgbchina.com.cn/commerceQuery.do?' + sessionid, postdata)
        #print data
        totals = self.get_pages(data)

        result = []
        perpage = 50
        postdata['turnPageShowNum'] = perpage
        for i in range(1, totals / perpage + 1):
            #url = self.url % ( i , 10, sessionid)
            #print '====== get_content_url:%s ======' % url
            postdata['turnPageBeginPos'] = (i - 1) * perpage + 1
            print 'page:', i, ' / beginPos:', postdata['turnPageBeginPos']
            data = self.postwebdata('https://wap.cgbchina.com.cn/commerceQuery.do?' + sessionid, postdata) 
            #print data
            rets = self.get_content_url(data) 
            print 'content urls:', len(rets) 
            result = []
            for x in rets: 
                url = 'https://wap.cgbchina.com.cn/commerceQueryDetail.do?' + x[0]
                #params = self.urldecode(url.replace('&amp;', '&'))
                #t = params['commerceName'].encode('utf-8')
                #print t
                str = x[0].split('&amp;')
                comm = {}
                for t in str:   
                    prop = t.split('=')
                    if prop[0] == u'commerceName':
                        comm['name'] = urllib.unquote(prop[1].encode('ascii'))
                        print comm['name']
                    if prop[0] == u'commerceAddress':
                        comm['address'] = urllib.unquote(prop[1].encode('ascii'))
                    if prop[0] == u'privilegeInfo':
                        comm['discount'] = urllib.unquote(prop[1].encode('ascii'))
                    if prop[0] == u'commerceType':
                        comm['type'] = prop[1].encode('ascii')
                    if prop[0] == u'commerceArea':
                        comm['city'] = prop[1]
                    if prop[0] == u'phone':
                        comm['tel'] = prop[1]
                    if prop[0] == u'beginTime':
                        comm['begin'] = prop[1]
                    if prop[0] == u'endTime':
                        comm['end'] = prop[1]
                #print comm
                result.append(comm)


                #print '====== get_content:%s %s ======' % x
                #data = self.getwebdata(contenturl)
                #rets = self.get_content(data)
                #for k,v in rets.iteritems():
                #    print k, v
                #result.append({'name':x[1], 'url':contenturl, 'content':rets})     
            #return

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()
        fetion('GuangDa Finished!')

# JiaoTong Bank (Bank of Communication)
class JiaoTong (Spider):
    def __init__(self):
        Spider.__init__(self)
        print '====== JiaoTong ======'
        self.url = 'http://creditcard.bankcomm.com/bcms/front/merchant/ajax/searchCn.do'
        self.urlbase = 'http://creditcard.bankcomm.com'
        #self.content_url_re = re.compile(u'商户名称：<font style="color:#f38c05;"><a target="_blank"  href=\'([^\']+)\' class="a_name">(.*?)</a>')
        self.content_url_re = re.compile(u'商户名称：</label><strong><a href="([^"]+)">(.*?)</strong>')

        # 816)" >尾页
        self.page_re = re.compile(u'pageNo:([0-9]+),pageSize:[0-9]+}\)">末页')

        #self.refresh_location_key = ''
        self.refresh_location_key = u'address'
        self.bank_id = 8

        self.content_re = [
            ('name', re.compile(u'<label title=".*?">(.*?)</label>', re.DOTALL)),
            ('address', re.compile(u'商户地址：</dt><dd>(.*?)</dd>', re.DOTALL)),
            ('tel', re.compile(u'服务电话：</dt><dd>(.*?)</dd>', re.DOTALL)),
            #('price', re.compile(u'人 均 消 费：￥([0-9\-]+)', re.DOTALL)),
            #('discount', re.compile(u'([0-9|.]+)折', re.DOTALL)),
            ('detail', re.compile(u'优惠细则：</dt><dd>(.*?)</dd>', re.DOTALL)),
            ('content', re.compile(u'商户介绍：</dt> <dd>(.*?)</dd>', re.DOTALL)),
            ('special', re.compile(u'招 牌 服 务：.*?</td>.*?<td class="black" align="left">(.*?)</td>', re.DOTALL)),
            ('card', re.compile(u'支持卡类：</dt>\r\n<dd>(.*?)</dd>', re.DOTALL)),
            ('parking', re.compile(u'停车环境：</dt><dd>(.*?)</dd>', re.DOTALL)),
            ('end', re.compile(u'优惠截止：</dt><dd>([0-9\/]+)</dd>', re.DOTALL)),
            ('trans', re.compile(u'公交指南：</dt><dd>(.*?)</dd>', re.DOTALL)),
            ('logo', re.compile('<div id="md_plc"><img src="([^"]+)" alt=".*?" width="150" height="110"/>', re.DOTALL)),
            ('category', re.compile(u'<span class="orange">分类：</span>(.*?)<br/>', re.DOTALL)),
            ('city', re.compile(u'cityName:"(.*?)",', re.DOTALL)),
            ]

        self.logo_re = re.compile(u'<img src="([^"]+)" id="merchantLogo" width="175" height="133" />')

    def go(self):
        # Mongodb Connect
        con = Connection()
        db = con.kyh
        favors = db.favor

        postdata = {
            'cityId': 0,
            'cityName': '%E5%85%A8%E5%9B%BD',
            'circleId': 0,
            'catalog': '',
            'cardType': 0,
            'keyWord': '',
            'pageSize': 10,
            'pageNo': 1,
            'orderBy': 0,
            'isPage': 'true',
        }
        
        data = self.postwebdata(self.url, postdata)
        #print data
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages):
            #print '====== get_content_url:%s ======' % url
            print 'page', i
            postdata['pageNo'] = i
            data = self.postwebdata(self.url, postdata) 
            #print data
            rets = self.get_content_url(data) 
            #print rets
            print 'content urls:', len(rets) 
            for x in rets: 
                contenturl = self.urlbase + x[0].strip()
                favor = favors.find_one({'url':contenturl})
                #print 'favor:',favor
                if favor == None:
                    content = self.getwebdata(contenturl)
                    c = self.get_content(content)
                    c['bank'] = self.bank_id
                    c['url'] = contenturl
                    favors.insert(c)
                    print 'insert:', x[0].strip(), x[1].strip()
                    time.sleep(1)
                else:
                    print 'skip:', x[0].strip(), x[1].strip()
                    continue
                #return
                #result.append({'name':x[1], 'url':contenturl, 'content':rets})     

# GuangFa Bank
class GuangFa (Spider):
    def __init__(self):
        Spider.__init__(self)
        print '====== GuangFa ======'
        # self.url = 'http://card.cgbchina.com.cn/Channel/1113974'
        self.category = {
            1113912: '',
            1114675: '',
            1114551: '',
            1114462: '',
            1114400: '',
            1114338: '',
            1114276: '',
            1114187: '',
            1114125: '',
            1114063: '',
            1113974: '',
            1114613: '',
        }
        #self.url = 'http://card.cgbchina.com.cn/jsp/include/CN/card/merchant_querypage.jsp?chanelPath=ROOT_%25E4%25BF%25A1%25E7%2594%25A8%25E5%258D%25A1_%25E7%2589%25B9%25E7%25BA%25A6%25E5%2595%2586%25E6%2588%25B7_%25E5%2595%2586%25E6%2588%25B7%25E5%2588%2597%25E8%25A1%25A8_%25E9%25A4%2590%25E9%25A5%25AE%25E7%25B1%25BB&mCity=&mCondition=%25E8%25AF%25B7%25E8%25BE%2593%25E5%2585%25A5%25E5%2595%2586%25E6%2588%25B7%25E5%2590%258D%25E7%25A7%25B0%25E6%2588%2596%25E5%2585%25B3%25E9%2594%25AE%25E5%25AD%2597&_tp_tt='

        self.url = 'http://card.cgbchina.com.cn/jsp/include/CN/card/merchant_querypage.jsp?chanelPath=ROOT_%25E4%25BF%25A1%25E7%2594%25A8%25E5%258D%25A1_%25E7%2589%25B9%25E7%25BA%25A6%25E5%2595%2586%25E6%2588%25B7_%25E5%2595%2586%25E6%2588%25B7%25E5%2588%2597%25E8%25A1%25A8_%25E9%25A4%2590%25E9%25A5%25AE%25E7%25B1%25BB&mCity=&mCondition=%25E8%25AF%25B7%25E8%25BE%2593%25E5%2585%25A5%25E5%2595%2586%25E6%2588%25B7%25E5%2590%258D%25E7%25A7%25B0%25E6%2588%2596%25E5%2585%25B3%25E9%2594%25AE%25E5%25AD%2597&_tp_tt='
        #self.content_url_re = re.compile(u'商户名称：<font style="color:#f38c05;"><a target="_blank"  href=\'([^\']+)\' class="a_name">(.*?)</a>')
        self.content_url_re = re.compile(u'<a href="([^"]+)"  target="_blank" title="(.*?)" class="title" >')

        # 816)" >尾页
        self.page_re = re.compile(u'([0-9]+)页')

        #self.refresh_location_key = ''
        self.filename = 'GuangFa.json'
        self.refresh_location_key = u'address'

        self.content_re = [
            (u'category', re.compile(u'<span class="orange">分类：</span>(.*?)<br/>', re.DOTALL)),
            (u'fav_time', re.compile(u'<span class="orange">优惠时间：</span>(.*?)<br/>', re.DOTALL)),
            (u'tel', re.compile(u'<span class="orange">电话：</span>.*?([0-9\-]+)', re.DOTALL)),
            (u'city', re.compile(u'<span class="orange">城市：</span>(.*?)<br/>', re.DOTALL)),
            (u'address', re.compile(u'<span class="orange">地址：</span>(.*?)<br/>', re.DOTALL)),
            (u'fav', re.compile(u'</table>\r\n(.*?)\r\n</div>\r\n<div class="longBot"></div>\r\n<!--  内容展示  -->')),
            ]

        self.logo_re = re.compile(u'<img src="([^"]+)" id="merchantLogo" width="175" height="133" />')

    def go(self):
        urlbase = 'http://card.cgbchina.com.cn'

        data = self.getwebdata(self.url)
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            url = self.url + str(i)
            #print '====== get_content_url:%s ======' % url
            print 'page', i
            data = self.getwebdata(url) 
            rets = self.get_content_url(data) 
            print 'content urls:', len(rets) 
            for x in rets: 
                contenturl = urlbase + x[0]
                print '====== get_content:%s %s ======' % x
                print 'url:', contenturl
                data = self.getwebdata(contenturl)
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                result.append({'name':x[1], 'url':contenturl, 'content':rets})     

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()



# China Construction Bank
class JianShe (Spider):
    def __init__(self):
        Spider.__init__(self)
        print '====== Construnction ======'
        # self.url = 'http://card.cgbchina.com.cn/Channel/1113974'
        self.category = {
            1113912: '',
            1114675: '',
            1114551: '',
            1114462: '',
            1114400: '',
            1114338: '',
            1114276: '',
            1114187: '',
            1114125: '',
            1114063: '',
            1113974: '',
            1114613: '',
        }

        self.url = 'http://creditcard.ccb.com/ccapp/doSearch.do?type=bizSearch&s_cityid=&s_catechildid=&s_lifeid=&s_searchKey=&pageNo='
        #(u'<a href="/favorable/20120301_1330580567.html?provinceid=1003&cityid=3" class="more">详情</a>')
        self.content_url_re = re.compile(u'<a href="([^"]+)" class="more">详情</a>')
        #self.content_url_re = re.compile(u'<a href="([^"]+)"  target="_blank" title="(.*?)" class="title" >')

        self.page_re = re.compile('var pagecount = ([0-9]+);')

        #self.refresh_location_key = ''
        self.filename = 'JianShe.json'
        self.refresh_location_key = 'address'

        self.content_re = [
            (u'name', re.compile(u'<h1>([^<]+).*?</h1>.*?<div class="content">', re.DOTALL)),
            (u'stars', re.compile(u'<span class="star-rate" style="width:([0-9]+)%;">', re.DOTALL)),
            (u'fav_time', re.compile(u'截止时间：</dt>.*?<dd>(.*?)&nbsp;</dd>', re.DOTALL)),
            (u'tel', re.compile(u'<dt>商户电话：</dt>.*?<dd>.*?([0-9\-]+).*?</dd>', re.DOTALL)),
            (u'city', re.compile('initGMapByAddress\(\'.*?\',\'(.*?)\'\);', re.DOTALL)),
            #(u'address', re.compile('initGMapByAddress\(\'(.*?)\',\'.*?\'\);', re.DOTALL)),
            (u'address', re.compile(u'<dt>商户地址：</dt><dd>(.*?)&nbsp;</dd>', re.DOTALL)),
            (u'fav', re.compile(u'<dd class="shyh">(.*?)</dd>', re.DOTALL)),
            (u'detail', re.compile(u'<dd class="introduce-info">(.*?)</dd>')),
            ]

        self.logo_re = re.compile(u'<img src="([^"]+)" id="merchantLogo" width="175" height="133" />')

    def go(self):
        urlbase = 'http://creditcard.ccb.com'
        data = self.getwebdata(self.url)
        pages = self.get_pages(data)
        print 'pages:', pages

        result = []
        for i in range(1, pages+1):
            url = self.url + str(i)
            #print '====== get_content_url:%s ======' % url
            data = self.getwebdata(url) 
            rets = self.get_content_url(data) 
            print '************* page:', i, 'content urls:', len(rets), '****************' 
            for x in rets: 
                contenturl = urlbase + x
                print '====== get_content:%s ======' % (x,)
                print 'url:', contenturl
                data = self.getwebdata(contenturl)
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, ':', v
                result.append({'name':x[1], 'url':contenturl, 'content':rets})     

        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()

    def fix_content(self, name=None):
        urlbase = 'http://creditcard.ccb.com'
        f = open(self.filename, 'r')
        s = f.read()
        f.close()

        result = json.loads(s)

        for row in result: 
            if not row['content'].has_key('tel'):
                data = self.getwebdata(row['url'])
                rets = self.get_content(data)
                for k,v in rets.iteritems():
                    print k, v
                if len(rets) < 4: 
                    result.remove(row)
                    print '404 ERROR:', row
                    continue
                if row['content'].has_key('location'):
                    rets['location'] = row['content']['location']
                if rets:
                    row['content'] = rets
            else:
                print row['content']['name']

        os.rename(self.filename, self.filename+'.%d' % int(time.time()))
    
        f = open(self.filename, 'w')
        f.write(json.dumps(result))
        f.close()




def main():
    import pprint
    #x = JiaoTong()
    #x.go()

    #x = ZhaoShang()
    #x.refresh_logo()
    #x.go()
    #x.refresh_content()
    #x.refresh_location()

    #x = BankOfChina()
    #x.go()
    #x.refresh_content()
    #x.refresh_location()
    
    #x = BankOfBeijing()
    #x.refresh_logo()
    #ret = x.go()
    #x.refresh_content()
    #x.refresh_location()

    #x = MingSheng()
    #x.refresh_logo()
    #x.go()
    #x.refresh_location()

    #x = GuangFaNew()
    #x.go()

    #x = JianShe()
    #x.go()
    #x.fix_content()

    #x = ZhongXin()
    #x.go()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'zhaoshang':
            x = ZhaoShang()
        elif sys.argv[1] == 'jiaotong':
            x = JiaoTong()
        else:
            print 'no such bank'   
        x.go()
    else:
        print 'Error: missing args'
    #if sys.argv[1] in globals():
    #    globals()[sys.argv[1]]()
    #else:
 
    #main()
