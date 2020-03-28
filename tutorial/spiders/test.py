import scrapy
import pandas as pd
from bs4 import BeautifulSoup
import os
import json
import requests
import re
from datetime import datetime
from datetime import timedelta
import collections
from scrapy.shell import inspect_response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

import sys 

reload(sys) 
sys.setdefaultencoding('utf8') 

def get_date(days=0):
    date = datetime.now() - timedelta(days=days)
    return datetime.strftime(date, '%B %-d, %Y') 

def log_print(s,debug=True):
    if debug:
        print s

def clean_str(s):
    return s.replace("\n","").strip()


class DmmstrySpider(scrapy.Spider):
    name = "test"
    
  
    def start_requests(self):
        yield scrapy.Request("http://www.baidu.com")
             
   
    def func(self,i):
        return scrapy.Request("https://www.qq.com"+str(i),dont_filter=True)
    
    def parse_1(self,c):
        if len(c) > 0:
            for i in range(10):
                yield self.func(i)
    
    
    def parse(self,response):
        print "xxxxxxxxxxxx"
        return self.parse_1(response.text)
  
        




#     def parse_domain_check(self, response):
#         domain = response.meta['domain']
#         self.domain_check_f.write("\t".join([domain,str(response.status)]) + '\n')

#     def domain_check_errback(self,failure):
#         domain = failure.request.meta['domain']
#         url = failure.request.meta['url']
        
#         if failure.check(HttpError):
#             # these exceptions come from HttpError spider middleware
#             # you can get the non-200 response
#             response = failure.value.response
#             code = response.status

#         elif failure.check(DNSLookupError):
#             # this is the original request
#             code = "DNS"

#         elif failure.check(TimeoutError, TCPTimedOutError):
#             code = "TimeOut"
#         else:
#             code = "Error"
            
#         self.domain_check_f.write("\t".join([domain,url,str(code)]) + '\n')