
from mpi4py import MPI
comm = MPI.COMM_WORLD
my_rank = comm.Get_rank()
p = comm.Get_size()


from bs4 import BeautifulSoup
import requests
import pandas as pd 
import numpy as np
import warnings
import time
import re
import pickle
from tqdm import tqdm
import json
pd.set_option('display.max_columns', None)


def url_extraction(url):
        """
        Takes an url of a category in the website allrecipes.com and returns the urls of all the recipes on the page
        """
        data = requests.get(url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('a')
    #  s2 = soup.find_all('a',{'class':'comp card--image-top mntl-card-list-items mntl-document-card mntl-card card card--no-image'})
        urls=[]
        for i in s:
            urls.append(i.get('href'))  
                
        return(urls)
    
    
cat_urls = url_extraction('https://podcasts.apple.com/us/genre/podcasts/id26')
#print("cat_urls",cat_urls)
#cat_urls = cat_urls[27:137]

working_urls = []

for i in cat_urls:
    #print("i",i)
    if "https://podcasts.apple.com/us/genre/podcasts-" in i:
        data = requests.get(i)
        soup = BeautifulSoup(data.content,'html.parser')
        s1 = soup.find_all('div',{'class': 'column first'})[0].find_all('a')
        s2 = soup.find_all('div',{'class': 'column'})[0].find_all('a')
        s3 = soup.find_all('div',{'class': 'column last'})[0].find_all('a')
        s = s1+s2+s3
        urls_within_cat = []
        for ii in s:
            urls_within_cat.append(ii.get('href'))
        working_urls.extend(urls_within_cat)

delta = 100000
#delta = 2 #test
urls = working_urls[my_rank*delta:(my_rank+1)*delta]



    
class Extract():

    def __init__(self,url):
        self.url = url
 
    def get_id(self):
        id_pod = self.url.split('/')[-1]
        return id_pod
    
    
    def get_title(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('span',{'class' : 'product-header__title'})
        if list(s):
            title = s[0].get_text().strip()
            return title
        else:
            return np.nan
    
    def get_studio(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('span',{'class' : 'product-header__identity podcast-header__identity'})
        if list(s):
            studio = s[0].get_text().strip()
            return studio
        else:
            return np.nan
    
    def get_category(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('li',{'class' : 'inline-list__item inline-list__item--bulleted'})
        if list(s):
            category = s[0].get_text().strip()
            return category
        else:
            return np.nan
    
    
    def get_avg_rating_and_volume(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('figcaption',{'class' : 'we-rating-count star-rating__count'})
        if list(s):
            avg_rating = s[0].get_text().split('•')[0].strip()
            ratings_volume = s[0].get_text().split('•')[1].strip() 
            return avg_rating, ratings_volume
        else:
            return np.nan, np.nan
    
    
    def get_episode_count(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('div',{'class' : 'product-artwork__caption small-hide medium-show'})
        if list(s):
            num_episodes = s[0].get_text().strip()  
            return num_episodes
        else:
            return np.nan

    def get_description(self):
        data = requests.get(self.url)
        soup = BeautifulSoup(data.content,'html.parser')
        s = soup.find_all('section',{'class' : 'product-hero-desc__section'})
        if list(s):
            description = s[0].get_text().strip()
            return description
        else:
            return np.nan
    
    
    
    

import time
start = time.time()

podcasts_info =  []

for url in tqdm(urls):
    p = Extract(url)
    podcasts_info.append({
        'id':p.get_id(),
        'name': p.get_title(),
        'url': url,
        'studio': p.get_studio(),
        'category': p.get_category(),
        'episode_count': p.get_episode_count(),
        'avg_rating': p.get_avg_rating_and_volume()[0],
        'total_ratings': p.get_avg_rating_and_volume()[1],
        'description' : p.get_description()
    })
    print(url)
    
end = time.time()
print(end - start)

with open('podcasts.json', 'wt') as f_out:
    json.dump(podcasts_info, f_out, indent=2)