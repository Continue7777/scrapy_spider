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
    name = "dmmstry_product"
    domain_checked_list = []
    key_page_used_file = '/root/code/scrapy_project/tutorial/spiders/data_config/key_page_used.csv'
    key_word_file = '/root/code/scrapy_project/tutorial/spiders/data_config/key_word.csv'
    product_detail_file = '/root/code/scrapy_project/tutorial/spiders/result/product_detail.csv'
    domain_check_file = '/root/code/scrapy_project/tutorial/spiders/result/domain_check.csv'

    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS':1
    }
        
    cookies = {
        '_ga': 'GA1.2.1328724326.1583206558',
        '_fbp': 'fb.1.1583209030738.1211827902',
        '_gid': 'GA1.2.476530775.1585119060',
        '_gat_pageTracker': '1',
        'csrftoken': 'reB7KccErmEYHqIS4irtaNPrhdV3cDSm8SpEAGVzHl9g0LdX3AGLPgfRED7Kolpr',
        'sessionid': 'arbr8h3fvwlheqse7n8cy9j42eqs4v4i',
        'device_session': 'eyJwYXNzY29kZSI6NDM4NjV9:1jH01G:Rj3-zb8norX5bRqogQO7IQ2FOvU',
    }


    headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
            'Sec-Fetch-Dest': 'document',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Referer': 'https://dmmspy.com/v2/dynamic-grid',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
    product_f = open(product_detail_file, 'a')
    domain_check_f = open(domain_check_file, 'a')
    key_page_used_f = open(key_page_used_file,'a')
    
    def start_requests(self):
        # get used_url
        key_page_used = []
        if os.path.isfile(self.key_page_used_file):
            key_page_df = pd.read_csv(self.key_page_used_file,names=['key'])
            key_page_used = set(key_page_df['key'].tolist())

        # get search key_word
        key_word_df = pd.read_csv(self.key_word_file,sep='\t')
        key_word_list = set(key_word_df['key_word'].tolist())
        #  key_word_list = ['tumbler cup'] # single test
        
        # set search page_num
        all_page_num = 85
    
        # search key
        search_replace = "+" 
        
        # get last 6 months
        post_time = get_date(30 * 6) + " - " + get_date(0)
        post_time = post_time.replace(" ",search_replace).replace(',','%2C')
              
        for key_word in key_word_list:
            for page_num in range(1,all_page_num):
                key_page = key_word+"\t"+str(page_num)
                if key_page in key_page_used:
                    print key_word,page_num,'used!!!'
                    continue
                key_word_web = search_replace.join(key_word.split(" "))
                url = "http://dmmspy.com/v2/dynamic-grid?page="+str(page_num)+"&search_mode=&q=" + key_word_web + "&likes=&comments=&post_time=" + post_time + "&sort="    
                yield scrapy.Request(url=url,headers=self.headers,cookies=self.cookies, callback=self.parse,meta={"key_page":key_page})
             
    def parse_owner_name(self,div_caption):
        try:
            owner_name = div_caption.find(name='div',attrs={"class":"owner-name"}).a.string
            return clean_str(owner_name)
        except AttributeError  as e:
            return ""
    
    def parse_domain(self,div_caption):
        try:
            domain = div_caption.find(name='div',attrs={"title":"Domain"}).a.string
            return clean_str(domain)
        except AttributeError  as e:
            return ""

    def parse_link(self,div_caption):
        try:
            return div_caption.find(name='a',attrs={"class":"linked-link"}).string
        except AttributeError  as e:
            return ""    

    def parse_pixelId(self,div_caption):
        try:
            return div_caption.find(name='a',attrs={"class":"pixel_id_tag"}).string
        except AttributeError  as e:
            return ""
    
    def parse_facebook(self,div_caption):
        try:      
            return "http://dmmspy.com/" + div_caption.a['href']
        except AttributeError  as e:
            return ""
    
    def parse_platform(self,div_caption):
        try:
            return div_caption.find(name='div',attrs={"class":"platform-bar"}).img['title']
        except AttributeError  as e:
            return ""
    
    def parse_like_num(self,div_caption):
        try:
            return clean_str(div_caption.find(name='span',attrs={"title":"Num of likes"}).contents[-1])
        except AttributeError  as e:
            return '0'
        
    def parse_share_num(self,div_caption):
        try:
            return clean_str(div_caption.find(name='span',attrs={"title":"Num of shares"}).contents[2])
        except AttributeError  as e:
            return '0'   

    def parse_comment_num(self,div_caption):
        try:
            return clean_str(div_caption.find(name='span',attrs={"title":"Num of comments"}).contents[2])
        except AttributeError  as e:
            return '0' 

     
    def parse_info(self,div_caption):
        res_dict = collections.OrderedDict()
        res_dict["platform"] = self.parse_platform(div_caption.parent)
        res_dict["owner_name"] = self.parse_owner_name(div_caption)
        res_dict["domain"] = self.parse_domain(div_caption)
        res_dict["link"] = self.parse_link(div_caption)
        res_dict["pixelId"] = self.parse_pixelId(div_caption)
        res_dict["facebook_url"] = self.parse_facebook(div_caption)
        res_dict["like_num"] = self.parse_like_num(div_caption.parent)
        res_dict["share_num"] = self.parse_share_num(div_caption.parent)
        res_dict["commnet_num"] = self.parse_comment_num(div_caption.parent)
        res_str = ",".join(res_dict.values())
        
        self.product_f.write(res_str + '\n')
        
    def parse_one_page(self,content,key_page):
        soup = BeautifulSoup(content)
        div_captions = soup.find_all(name='div',class_="caption")
        print("!!!!one_page_len:",len(div_captions))
        if len(div_captions) > 0:
            for div_caption in div_captions:
                self.parse_info(div_caption)
            self.key_page_used_f.write(key_page + '\n')
            print("!!!!key_page_add:",key_page)
    
    def parse(self, response):
        self.parse_one_page(response.text,response.meta["key_page"])

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