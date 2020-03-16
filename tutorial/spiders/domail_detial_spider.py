# -*- coding: utf-8 -*-
import scrapy
import os
import pandas as pd
import re


class DomainDetailSpider(scrapy.Spider):
    name = 'domain_detail'
    handle_httpstatus_list = [301,302,204,206,403,404,500]

    abs_path = os.getcwd() + '/spiders/result/'
    domain_file = "domain_detail.csv"
    owner_file = "owner_detail.csv"
    
    def get_emails(self,s):
        emails = set(re.findall(r'[0-9a-zA-Z_]{0,50}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}',s))
        avail_emails = []
        for email in emails:
            if "your" not in email and "example" not in email:
                avail_emails.append(email)
        return avail_emails
    
    def start_requests(self):
        df = pd.read_csv(self.abs_path + "../result_detail.csv",sep=',',names=['platform','domain','owner_name','link','pixelId','facebook_url','like_num','share_num','comment_num'])

        
        owner_name_df = df.drop_duplicates(['owner_name'])
        for owner_name,facebook_url in zip(owner_name_df['owner_name'],owner_name_df['facebook_url']):
            yield scrapy.Request(facebook_url,callback=self.parse_owner_name,meta = {"owner_name":owner_name})
        
#         for domain in set(df['domain'].to_list()):
#             yield scrapy.Request("https://"+ domain,callback=self.parse_domain_availble,meta={"domain":domain})
            

    
    def parse_domain_availble(self, response):
        domain = response.meta['domain']
        if response.status != 200:
            with open(self.abs_path + self.domain_file, 'a') as f:
                f.write(domain + "\t" + "False" + "\t" + '\n')
        else:
            emails = self.get_emails(response.text)
            yield scrapy.Request("https://" + domain + "/pages/contact-us",callback=self.parse_domain_page_concact,meta = {"domain":domain,"emails":emails})
            
        
    def parse_domain_page_concact(self, response):
        domain = response.meta['domain']
        emails = response.meta['emails']
        if response.status == 200:
            cur_emails = self.get_emails(response.text)
            emails = cur_emails + emails      
        yield scrapy.Request("https://" + domain + "/contact-us",callback=self.parse_domain_concact,meta = {"domain":domain,"emails":emails})
    
    def parse_domain_concact(self, response):
        domain = response.meta['domain']
        emails = response.meta['emails']
        if response.status == 200:
            cur_emails = self.get_emails(response.text)
            emails = cur_emails + emails      
        with open(self.abs_path + self.domain_file, 'a') as f:
            f.write(domain + "\t" + "True" + "\t" + ",".join(set(emails)) + '\n')
            
        
    def parse_owner_name(self, response):
        owner_name = response.meta["owner_name"]
        print "-----------------------",owner_name,response.url
        if response.status == 200 or response.status == 301:
            emails = self.get_emails(response.text)
            emails = ",".join(emails)
            with open(self.abs_path + self.owner_file, 'a') as f:
                f.write(owner_name + "\t" + response.url + "\t" + emails + '\n') 
        else:
            with open(self.abs_path + self.owner_file, 'a') as f:
                f.write(owner_name + "\t" + "False" + "\t" + '\n') 
        