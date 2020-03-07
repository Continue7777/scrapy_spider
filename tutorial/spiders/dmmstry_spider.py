import scrapy
import pandas as pd
from bs4 import BeautifulSoup
import os
import json
import requests
import re
from datetime import datetime
from datetime import timedelta


def get_date(days=0):
    date = datetime.now() - timedelta(days=days)
    return datetime.strftime(date, '%B %-d,%Y') 

def log_print(s,debug=True):
    if debug:
        print s

def clean_str(s):
    return s.replace("\n","").strip()


class DmmstrySpider(scrapy.Spider):
    name = "dmmstry"
    abs_path = os.getcwd() + '/spiders/'
    url_used_file = 'url_used.csv'

    cookies = {
        '_ga': 'GA1.2.1328724326.1583206558',
        '_fbp': 'fb.1.1583209030738.1211827902',
        '_gid': 'GA1.2.1156183927.1583326665',
        '_gat': '1',
        'csrftoken': '6QzLjbiv6stfpAr6ARCsY8Mz0K583k5eDsLQWOQRVn3JBsnR1C4SAPslFRwmP2IF',
        'sessionid': '56kl38n7q71g3rbz5n67565c9efijgzg',
        'device_session': 'eyJwYXNzY29kZSI6MTA0NDB9:1jARcz:dZHzn009WiSSkdrL7sUSU6cslbw',
        '_gat_pageTracker': '1',
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
            'Referer': 'https://dmmspy.com/v2/dynamic-grid?search_mode=',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
    
    def start_requests(self):
        url_df = pd.read_csv(self.abs_path + self.url_used_file,header=None,names=['url'])
        key_word_df = pd.read_csv(self.abs_path +"key_word.csv",sep='\t')
        key_word_list = set(key_word_df['key_word'].tolist())
        all_page_num = 85
        used_urls = url_df['url'].tolist()
        urls = []
        
        post_time = get_date(30 * 6) + " - " + get_date(0)
        post_time = post_time.replace(" ","+").replace(',','%2C')
        
        key_word_list = ['tumbler cup']
        for key_word in key_word_list:
            for page_num in range(1,all_page_num):
                key_word_web = "+".join(key_word.split(" "))
                url = "http://dmmspy.com/v2/dynamic-grid?page="+str(page_num)+"&search_mode=&q=" + key_word_web + "&likes=&comments=&post_time=" + post_time + "&sort="    
                self.headers['Referer'] = url
                if url in used_urls:
                    continue
                urls.append(url)
                yield scrapy.Request(url=url,headers=self.headers,cookies=self.cookies, callback=self.parse)
             
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
    
    
#     def parse_facebook(self,div_caption):
#         try:      
#             response = requests.get("http://dmmspy.com/" + div_caption.a['href'])
#             facebook_url = re.findall("https://www.facebook.com/\w*",response.text)[0]
#             response_facebook = requests.get(facebook_url)
#             return response_facebook.url
#         except AttributeError  as e:
#             return ""

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
        platform = self.parse_platform(div_caption.parent)
        owner_name = self.parse_owner_name(div_caption)
        domain = self.parse_domain(div_caption)
        link = self.parse_link(div_caption)
        pixelId = self.parse_pixelId(div_caption)
        facebook_url = self.parse_facebook(div_caption)
        like_num = self.parse_like_num(div_caption.parent)
        share_num = self.parse_share_num(div_caption.parent)
        commnet_num = self.parse_comment_num(div_caption.parent)
        return platform,owner_name,domain,link,pixelId,facebook_url,like_num,share_num,commnet_num

    def parse_one_page(self,content):
        platform_list = []
        owner_name_list = []
        domain_list = []
        link_list = []
        pixelId_list = []
        facebook_url_list = []
        like_num_list = []
        share_num_list = []
        comment_num_list = []
        
        soup = BeautifulSoup(content)
        div_captions = soup.find_all(name='div',class_="caption")
        if len(div_captions) > 0:
            for div_caption in div_captions:
                platform,owner_name,domain,link,pixelId,facebook_url,like_num,share_num,comment_num = self.parse_info(div_caption)
                platform_list.append(platform)
                owner_name_list.append(owner_name)
                domain_list.append(domain)
                link_list.append(link)
                pixelId_list.append(pixelId)
                facebook_url_list.append(facebook_url)
                like_num_list.append(like_num)
                share_num_list.append(share_num)
                comment_num_list.append(comment_num)
        res_df = pd.DataFrame(data={"platform":platform_list,"owner_name":owner_name_list,"domain":domain_list,"link":link_list,"pixelId":pixelId_list,"facebook_url":facebook_url_list,'like_num':like_num_list,"share_num":share_num_list,"comment_num":comment_num_list},columns=['platform','domain','owner_name','link','pixelId','facebook_url','like_num','share_num','comment_num'])
        return res_df

    def parse(self, response):
        res_df = self.parse_one_page(response.text)
        print "!!!!!!!!!!!!!",len(res_df)
        res_df.to_csv(self.abs_path + "result_detail.csv",mode='a',index=False,header=False)
        with open(self.abs_path + self.url_used_file, 'a') as f:
            f.write(response.request.url + '\n')
        