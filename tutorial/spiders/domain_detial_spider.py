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

script = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(0.5))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""

class DomainDetailSpider(scrapy.Spider):
    name = 'domain_detail'
#     handle_httpstatus_list = [301,302,403,404,500]

    custom_settings = {
        'SPLASH_URL': 'http://172.31.115.244:8050',
        'CONCURRENT_REQUESTS ':300,
        'RETRY_ENABLED' : True,
        'DOWNLOAD_TIMEOUT' : 50,
        'DOWNLOADER_MIDDLEWARES' : {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            },
        'SPIDER_MIDDLEWARES' : {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
            }
    }
     
    product_file = "/root/code/scrapy_project/tutorial/spiders/result/product_detail"
    domain_file = "/root/code/scrapy_project/tutorial/spiders/result/domain_detail.csv"
    domain_f = open(domain_file,'a')
#     owner_file = "owner_detail.csv"
    
    def get_emails(self,s):
        emails = set(re.findall(r'[0-9a-zA-Z_]{0,50}@[0-9a-zA-Z]{1,30}\.[0-9a-zA-Z]{1,13}',s))
        avail_emails = []
        for email in emails:
            flag = True
            for key in  ['your','example','jpg','jpeg','png'] :
                if key in email.lower():
                    flag = False
            if flag:avail_emails.append(email)
        return avail_emails
    
    def start_requests(self):
        # get_dmmspy_domain
        df = pd.read_csv(self.product_file,sep=',',names=['platform','owner_name','domain','link','pixelId','facebook_url','like_num','share_num','comment_num'])
        domain_list = set(df['domain'].to_list())
        # test
#         domain_list = ['blackbirdkidsclothing.co.uk']
        
#         owner_name_df = df.drop_duplicates(['owner_name'])
#         for owner_name,facebook_url in zip(owner_name_df['owner_name'],owner_name_df['facebook_url']):
#             yield scrapy.Request(facebook_url,callback=self.parse_owner_name,meta = {"owner_name":owner_name})
        
#         for domain in domain_list:
#             yield scrapy.Request("https://"+ domain,callback=self.parse_domain_availble,meta={"domain":domain})
        for domain in domain_list:     
            yield SplashRequest("https://"+ domain, self.parse_email,meta={"domain":domain,"url":domain},errback=self.errback,
                            endpoint='execute',
                            args={
                                'wait': 0.1,
                                'lua_source': script
                            }
            )
    
    
    def errback(self,failure):
        domain = failure.request.meta['domain']
        url = failure.request.meta['url']
        
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
            
        self.domain_f.write("\t".join([domain,url,str(code)]) + '\n')
                            
    def parse_email(self, response):
        domain = response.meta['domain']
        url = response.meta['url']
#         inspect_response(response, self)
        emails = self.get_emails(response.text)
        self.domain_f.write("\t".join([domain,url,str(response.status),",".join(emails)]) + '\n')
        
        linkExr = LinkExtractor(allow='contact')
        links = linkExr.extract_links(response)
        for link in links[:3]:
            yield SplashRequest(link.url, self.parse_email,meta={"domain":domain,"url":link.url},errback=self.errback,
                    args={
                        'wait': 0.1,
                    }
                )
               
#     def parse_domain_page_concact(self, response):
#         domain = response.meta['domain']
#         emails = response.meta['emails']
#         if response.status == 200:
#             cur_emails = self.get_emails(response.text)
#             emails = cur_emails + emails      
#         yield scrapy.Request("https://" + domain + "/contact-us",callback=self.parse_domain_concact,meta = {"domain":domain,"emails":emails})
    
#     def parse_domain_concact(self, response):
#         domain = response.meta['domain']
#         emails = response.meta['emails']
#         if response.status == 200:
#             cur_emails = self.get_emails(response.text)
#             emails = cur_emails + emails      
#         with open(self.abs_path + self.domain_file, 'a') as f:
#             f.write(domain + "\t" + "True" + "\t" + ",".join(set(emails)) + '\n')
            
        
#     def parse_owner_name(self, response):
#         owner_name = response.meta["owner_name"]
#         print "-----------------------",owner_name,response.url
#         if response.status == 200 or response.status == 301:
#             emails = self.get_emails(response.text)
#             emails = ",".join(emails)
#             with open(self.abs_path + self.owner_file, 'a') as f:
#                 f.write(owner_name + "\t" + response.url + "\t" + emails + '\n') 
#         else:
#             with open(self.abs_path + self.owner_file, 'a') as f:
#                 f.write(owner_name + "\t" + "False" + "\t" + '\n') 
        