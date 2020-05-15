import requests
import csv
import json
import datetime
import time
from bs4 import BeautifulSoup as bs
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from currency_converter import CurrencyConverter
import concurrent.futures
import traceback
import psutil
import objgraph
import inspect

import concurrent.futures
import gc

class dlsite_scraper:
	"""
	A program that scrapes dlsite for information and saves it to a JSON or CSV file.
	"""
	
	def __init__(self):
		self.start_time = time.time()
		"""Initializes our webdriver."""
		self.reload_counter = 0	
		self.max_reloads = 2 # +1 is what we actual have, so 3 reloads total
		# was running out of memory, so now I restart the driver once the page has
		# been reloaded MAX_MEM_COUNT times.
		self.MAX_MEM_COUNT = 50
		self.mem_count = 0 # the current # of reloads

		# was running out of ram so I used this.
		# lower this # if you're running out of memory
		self.MAX_STORAGE_VAL = 1000 

		# default 5
		# for multithreading?
		# set to 1 if you want to scrape 1 page at a time.
		self.MAX_WORKERS = 5

		# headless mode is like 2-3x slower, but it allows me to use the pc. Probably a decent trade off?
		options = webdriver.ChromeOptions()
		# options.headless = True
		# options.add_argument('--disable-gpu')
		chrome_prefs = {}


		# This makes it so images aren't downloaded		
		options.experimental_options["prefs"] = chrome_prefs
		chrome_prefs["profile.default_content_settings"] = {"images": 2}
		chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
		self.options = options;
		self.driver = webdriver.Chrome(options=self.options)
		self.bVoiceWorks = False;
		
		#self.driver.set_page_load_timeout(10)

	def load_url(self, full_url):
		"""Pass a dlsite url to load it via the webdriver"""
		self._track_memory()
		self.url = full_url
		url	= full_url
		try:
			self.driver.get(url)

			source_code = self.driver.execute_script("return document.documentElement.outerHTML")
		except:
			print(self.url)
			print("Error loading url")
			traceback.print_exc()
			self._reload_driver()
			self.load_url(self.url)
		else:
			self.soup = bs(source_code,features="lxml")

	def _reload_driver(self):
		##print("Restarting driver")
		self.driver.quit()
		self.mem_count = 0
		self.driver = webdriver.Chrome(options = self.options)

	
	def _track_memory(self):
		"""Tracks how many pages are loaded and restarts the webdriver once MAX_MEM_COUNT pages have been loaded"""
		self.mem_count += 1
		if(self.mem_count >= self.MAX_MEM_COUNT):
			self._reload_driver()

	def _reload_page(self):
		if (self.reload_counter <= self.max_reloads):
			self.load_url(self.url)
			try:
				self.driver.find_element_by_id("search_button").send_keys(Keys.F5)
			except:
				self._reload_driver()
				self._reload_page()
			##print(f"\twe reloaded for {self.url}")
			self.reload_counter += 1

	def _make_keyword_string(self, list_keys):
		"""Combine list_keys into a single string"""
		conc_string = ''
		for key in list_keys:
			key_w_plus = key + '+'
			conc_string += key_w_plus
		conc_string = conc_string[0:len(conc_string) - 1]
		return conc_string

	def get_total_search_res(self, keylist):
		"""Find # of search results based on a list of keywords"""
		keywords_string = self._make_keyword_string(keylist)
		items_per_page = 100
		url = f"https://www.dlsite.com/maniax/fsr/=/language/jp/sex_category%5B0%5D/male/keyword/{keywords_string}/order%5B0%5D/trend/per_page/{items_per_page}/from/fs.header"
		self.load_url(url)
		
		num_searches_found = 0

		try:
			resultSet = self.soup.findAll('div',{'class':'page_total'})[0].findAll('strong')
			num_searches_found = resultSet[0].string
		except:
			print("Error retrieving search results")
		else:
			return num_searches_found
	

	def get_seller_name(self):
		results = self.soup.findAll('span', {'class':'maker_name'})
		while(results ==[]):
			self._reload_page()
			results = self.soup.findAll('span', {'class':'maker_name'})
		for link in results:
			try:
				for l in link.findAll('a',):
					name = str(l.string)
			except:
				print("Error getting seller name")
			else:
				return name

	
	def get_rating(self):
		
		result_set = self.soup.findAll('span',{'class':'average_count'})
		if(result_set == []):
			self._reload_page()
			if (self.reload_counter <= self.max_reloads):
				return self.get_rating()
			else:
				self.reload_counter = 0
				return 0
		for link in result_set:
			try:
				rating = link.string
				if(rating == None):
					rating = 0
			except:
				print("Error getting rating")
			else:
				self.reload_counter = 0				
				return float(rating)


	def get_sale_date(self):
		for link in self.soup.findAll('table',{'id':'work_outline'}):
			try:
				data = link.findAll('a',)[0].string
			except:
				print("Error getting release date")
			else:
				return str(data)

	def get_genres(self):
		genre_string = ''
		for link in self.soup.findAll('div',{'class':'main_genre'}):
			try:
				for l in link.findAll('a',):
					genre_string += f'{str(l.string)} '
			except:
				print("Error getting genres")
				pass
			else:
				return genre_string

	def get_maker_code(self):
		results = self.soup.findAll('span', {"class":"maker_name"})
		for link in results:
			ahref = link.findAll('a',)
			for l in ahref:
				try:
					code = l.get('href')
					code = str(code)
					code_start_ind = code.index('G')
					code_end_ind = code.index('.html')
					maker_code = code[int(code_start_ind) - 1 : int(code_end_ind)]
				except:
					print("error getting maker code")
					traceback.print_exc()
				else:
					return maker_code

	def get_name(self):
		results = self.soup.findAll('a',{'itemprop':'url'})
		while(results == []):
			self._reload_page()
			results = self.soup.findAll('a',{'itemprop':'url'})	
		for link in results:
			try:
				name = link.contents[0] 
			except:
				print("Error getting name")
			else:
				return str(name)

	def get_sales(self):
		result_set = self.soup.findAll('dd', {'class':'point'})
		if(result_set == []):
			self._reload_page()
			if (self.reload_counter <= self.max_reloads):
				return self.get_sales()
			else: 
				self.reload_counter = 0
				return 0
		for link in result_set: 
			try:
				sales = link.string.replace(',','')
			except:
				print("Error getting sales")
			else:
				self.reload_counter = 0
				return int(sales)

	def get_total_earnings_jp(self):
		return self.get_sales() * self.get_price()

	def get_total_earnings_us(self):
		c = CurrencyConverter()
		convertedVal = c.convert(self.get_sales() * self.get_price(), "JPY", "USD")
		return convertedVal

	def get_price(self):
		result_set = self.soup.findAll('span',{'class':'price'})
		for link in result_set: 
			try:
				price = int(link.contents[0].replace(',','')) 
			except:
				if (self.reload_counter <= self.max_reloads):
					self._reload_page()
					return self.get_price()
				else: 
					self.reload_counter = 0
					return 0
			else:
				return int(price)


	def print_all_data(self):
		print(f"Name: {self.get_name()}")
		print("---")
		print(f"Code: {self.url}")
		print("---")
		print(f"Seller: {self.get_seller_name()}")
		print("---")
		print(f"price: {self.get_price()}")
		print("---")
		print(f"Sales: {self.get_sales()}")
		print("---")
		print(f"Release date: {self.get_sale_date()}")
		print("---")
		print(f"Rating: {self.get_rating()}")
		print("---")
		print(f"List of genres: {self.get_genres()}")


	def _find_all_pages(self):
		b_one_page = True
		for link in self.soup.findAll('td', {'class':'page_no'}):
		    for l in link.findAll('a'):
		        
		        if(l.contents[0] == '最後へ'):
		            b_one_page = False
		            last_page_url = l.get('href')
		            
		            ex_url = last_page_url
		            pg_str = '/page/'
		            page_index = ex_url.find(pg_str)
		            ex_url = ex_url[:page_index + len(pg_str)]
		            last_url_ind = last_page_url[page_index + len(pg_str):].replace('#works','')
		if(b_one_page == False):
		    all_pages = []
		    for v in range(1,int(last_url_ind) + 1):
		        all_pages.append(ex_url + str(v))
		    return all_pages

		return [self.url]

	def _get_all_works_a_page(self, url, list_of_scrapers):
		scraper_ind = -1

		while(scraper_ind == -1):
			for scraper in list_of_scrapers:
				if(scraper[1] == False):
					scraper_ind = list_of_scrapers.index(scraper)
					scraper[1] = True
					all_works = []
					scraper[0].load_url(url)
					for link in scraper[0].soup.findAll('div', {'class':'multiline_truncate'}):
						for l in link.findAll('a',):
							hrefl = l.get('href')
							all_works.append(hrefl)
					break;
		
		list_of_scrapers[scraper_ind][0].soup.decompose()
		list_of_scrapers[scraper_ind][1] = False
		return all_works
		
	def get_all_works_from_pages(self, list_of_scrapers):
		list_of_works = []
		all_pages = self._find_all_pages()  

		with concurrent.futures.ThreadPoolExecutor(max_workers = self.MAX_WORKERS) as ex:
			results = [ex.submit(self._get_all_works_a_page,l, list_of_scrapers) for l in all_pages]

			for k in concurrent.futures.as_completed(results):
				list_of_works += k.result()

		return list_of_works
		
	
	
	def data_as_list(self):
		"""Puts all data from a url into a list"""
		all_values = []
		all_values.append(self.get_name())
		all_values.append(self.get_seller_name())
		all_values.append(self.get_price())
		all_values.append(self.get_sales())
		if(self.bVoiceWorks == True):
			all_values.append(self.getCVs())
		all_values.append(self.get_sale_date())
		all_values.append(all_values[-1][5:7])
		all_values.append(all_values[-2][:4])
		all_values.append(self.get_rating())
		all_values.append(self.get_genres())
		rj_start_ind = self.url.find("J")
		rj_html_ind = self.url.find(".html")
		rj_substring = self.url[rj_start_ind-1:rj_html_ind]
		all_values.append(rj_substring)
		all_values.append(self.get_maker_code())
		return all_values

	def create_data_list(self,listval):
		self.load_url(listval)
		data_list = self.data_as_list()
		
		
		recording_time = datetime.datetime.now()
		formatted_time = recording_time.strftime("%Y-%m-%d")
		data_list.append(formatted_time)
		return(data_list)


	def _rename_later(self, l, list_of_works, list_of_scrapers):
		scraper_ind = -1

		while(scraper_ind == -1):
			for scraper in list_of_scrapers:
				if(scraper[1] == False):
					scraper_ind = list_of_scrapers.index(scraper)
					scraper[1] = True
					k = scraper[0].create_data_list(l)
					break;
		
		list_of_scrapers[scraper_ind][0].soup.decompose()
		list_of_scrapers[scraper_ind][1] = False
		return k

	def save_as_csv(self, filename):
		fname = f"{filename}.csv"
		list_of_scrapers = []
		with concurrent.futures.ThreadPoolExecutor(max_workers = self.MAX_WORKERS) as ex:
			results = [ex.submit(dlsite_scraper) for l in range(0,self.MAX_WORKERS)]

			for k in concurrent.futures.as_completed(results):
				list_of_scrapers.append([k.result(), False])

		list_of_works = self.get_all_works_from_pages(list_of_scrapers)

		with open(fname, 'w', newline='', encoding= 'utf-8') as f:
			writer = csv.writer(f)
			
			if(self.bVoiceWorks == True):
				headersf = ['name','seller name', 'price','sales','CVs', 'release date','release month', 'release year', 'rating','genres', 'code', 'maker code','data recording date']
			else:
				headersf = ['name','seller name', 'price','sales','release date','release month', 'release year', 'rating','genres', 'code', 'maker code','data recording date']
			writer.writerow(headersf)


		with open(fname, 'a', newline='', encoding= 'utf-8') as f:
			writer = csv.writer(f)
			self.driver.quit()
			with concurrent.futures.ThreadPoolExecutor(max_workers = self.MAX_WORKERS) as ex:
				results = [ex.submit(self._rename_later,l, list_of_works, list_of_scrapers) for l in list_of_works]

				for k in concurrent.futures.as_completed(results):
					writer.writerow(k.result())
					results.remove(k)
		print(time.time() - self.start_time)

	def save_data_multiple(self, filetype="csv", filename="untitled"):
		if(filetype == "csv"):
			self.save_as_csv(filename)
			
	def save_multiple_from_search(self, keywords, file_name="untitled", filetype_passed='csv'):
		self.get_total_search_res(keywords)
		self.save_data_multiple(filename = file_name, filetype=filetype_passed)

	def save_multiple_from_url(self, url, name_of_file = "untitlted", filetype_passed='csv'):
		self.load_url(url)
		self.save_data_multiple(filename=name_of_file, filetype=filetype_passed)