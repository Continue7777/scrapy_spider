# -*- coding: utf-8 -*-
import scrapy
import os
import pandas as pd
from scrapy_splash import SplashRequest
from scrapy.spiders.crawl import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
import re
from scrapy.shell import inspect_response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class DomainDetailSpider(scrapy.Spider):
    name = 'domain_check'

    custom_settings = {
        'CONCURRENT_REQUESTS ':400,
        'RETRY_ENABLED' : True,
        'DOWNLOAD_TIMEOUT' : 20,

    }
    
    check_file = "result/domain_check.csv"
    product_file = "result/product_detail.csv"
    domain_f = open(check_file,mode='a')
    
    def start_requests(self):
        # get_dmmspy_domain
        product_df = pd.read_csv(self.product_file,sep=',',names=['platform','owner_name','domain','link','pixelId','facebook_url','like_num','share_num','comment_num'])
        domain_check_df = pd.read_csv(self.check_file,sep='\t',header=None,names=['domain','code'])
        domain_uesd = set(domain_check_df['domain'].tolist())
        domain_list = set(product_df['domain'].to_list())
    
        for domain in domain_list: 
            if domain not in domain_uesd:
                yield scrapy.Request("https://"+ domain,callback=self.parse,errback = self.domain_check_errback,meta={"domain":domain})
                                
    def parse(self, response):
        domain = response.meta['domain']
#         inspect_response(response, self)
        
        self.domain_f.write("\t".join([domain,str(response.status)]) + '\n')

    def domain_check_errback(self,failure):
        domain = failure.request.meta['domain']
        
        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            code = response.status

        elif failure.check(DNSLookupError):
            # this is the original request
            code = "DNS"

        elif failure.check(TimeoutError, TCPTimedOutError):
            code = "TimeOut"
        else:
            code = "Error"
            
        self.domain_f.write("\t".join([domain,str(code)]) + '\n')