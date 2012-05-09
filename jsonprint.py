# coding: utf-8
import os, sys
import json

def myprint(filename, name=''):
    f = open(filename, 'r')
    x = json.load(f)
    
    #wf = open(filename + '.out', 'w')
    wf = sys.stdout
    for item in x:
        if name and name != item['name']:
            continue
        wf.write('====== name:%s ======\n'  % item['name'].encode('utf-8'))
        wf.write('url: %s\n' % item['url'].encode('utf-8'))
        if not item['content'].has_key(u'礼品编号') and not item['content'].has_key('gno'):
            wf.write('!!!!! not found: 礼品编号\n')
        for k,v in item['content'].iteritems():
            if filename == 'ZhaoShang.json' and k == 'chain':
                wf.write('%s\t%d\n' % (k.encode('utf-8'), len(v)))
                continue
            if k != 'location':
                wf.write('%s\t%s\n' % (k.encode('utf-8'), v.encode('utf-8')))
            else:
                wf.write('%s\t%s\n' % (k.encode('utf-8'), str(v)))
    wf.write('size: %d' % len(x))
    f.close()
    wf.close()

def main():
    try:
        name = unicode(sys.argv[2], 'utf-8')
    except:
        name = ''
    myprint(sys.argv[1], name)

main()

