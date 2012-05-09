# -*- utf-8 -*-
import urllib
import sys 
print sys.getfilesystemencoding()
print urllib.unquote(u'%E7%BB%B4%E6%A0%BC%E7%94%B5%E8%84%91%E7%BB%8F%E8%90%A5%E9%83%A8%EF%BC%88%E5%88%86%E5%BA%97%E4%B8%80%E3%80%81%E5%88%86%E5%BA%97%E4%BA%8C%EF%BC%89').decode("utf-8").encode(sys.getfilesystemencoding())
