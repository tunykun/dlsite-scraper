import requests
import csv
import json
import datetime
from bs4 import BeautifulSoup as bs
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from currency_converter import CurrencyConverter
import concurrent.futures
import traceback


class dlsite_scraper:
	"""
	A program that scrapes dlsite for information and saves it to a JSON or CSV file.
	"""
	
	def __init__(self):
		"""Initializes our webdriver."""
		self.reload_counter = 0	
		self.max_reloads = 2 # +1 is what we actual have, so 3 reloads total
		# was running out of memory, so now I restart the driver once the page has
		# been reloaded MAX_MEM_COUNT times.
		self.MAX_MEM_COUNT = 35
		self.mem_count = 0 # the current # of reloads


		options = Options()
		chrome_prefs = {}
		# This makes it so images aren't downloaded
		options.experimental_options["prefs"] = chrome_prefs
		chrome_prefs["profile.default_content_settings"] = {"images": 2}
		chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
		self.options = options;
		self.driver = webdriver.Chrome(options=options)
		self.driver.set_page_load_timeout(10)

	def load_url(self, full_url, single_url = False):
		"""Pass a dlsite url to load it via the webdriver"""
		self.url = full_url
		url	= full_url
		try:
			self.driver.get(url)
			source_code = self.driver.execute_script("return document.documentElement.outerHTML")
		except:
			print("Error loading url")
			#traceback.print_exc()
			self._reload_driver()
			self.load_url(self.url)
		else:
			self.soup = bs(source_code,features="lxml")
			if (single_url == True):
				self.driver.quit()

	def _reload_driver(self):
		print("Restarting driver")
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
			self._track_memory()
			self.load_url(self.url)
			self.driver.find_element_by_id("search_button").send_keys(Keys.F5)
			print(f"we reloaded for {self.url}")
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
			self.driver.quit()
			return num_searches_found
	

	def get_seller_name(self):
		for link in self.soup.findAll('span', {'class':'maker_name'}):
			try:
				for l in link.findAll('a',):
					name = l.string
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
				return rating


	def get_sale_date(self):
		for link in self.soup.findAll('table',{'id':'work_outline'}):
			try:
				data = link.findAll('a',)[0].string
			except:
				print("Error getting release date")
			else:
				return data

	def get_genres(self):
		list_of_genres = []
		for link in self.soup.findAll('div',{'class':'main_genre'}):
			try:
				for l in link.findAll('a',):
					list_of_genres.append(l.string) 
			except:
				print("Error getting genres")
				pass
			else:
				return list_of_genres

	def get_name(self):
		for link in self.soup.findAll('a',{'itemprop':'url'}):
			try:
				name = link.contents[0] 
			except:
				print("Error getting name")
			else:
				return name

	def get_sales(self):
		result_set = self.soup.findAll('dl', {'class':'work_dl purchase'})
		if(result_set == []):
			self._reload_page()
			if (self.reload_counter <= self.max_reloads):
				return self.get_sales()
			else: 
				self.reload_counter = 0
				return 0
		for link in result_set: 
			try:
				res2 = link.findAll('dd' , {'class' : 'count'})
			
				for r in res2:
					sales = r.string.replace(',','')
			except:
				print("Error getting sales")
			else:
				self.reload_counter = 0
				return sales

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
				print("Error getting price")
			else:
				return price

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

	def data_as_list(self):
		"""Puts all data from a url into a list"""
		all_values = []
		all_values.append(self.get_name())
		all_values.append(self.url)
		all_values.append(self.get_seller_name())
		all_values.append(self.get_price())
		all_values.append(self.get_sales())
		all_values.append(self.get_sale_date())
		all_values.append(self.get_rating())
		all_values.append(self.get_genres())
		return all_values

	def data_as_dict(self):
		"""Puts all data from a url into a dictionary"""
		dict_return = {}
		dict_return['name'] = self.get_name()
		dict_return['url'] = self.url
		dict_return['seller_name'] = self.get_seller_name()
		dict_return['price'] = self.get_price()
		dict_return['sales'] = self.get_sales()
		dict_return['sale_date'] = self.get_sale_date()
		dict_return['rating'] = self.get_rating()
		dict_return['genre'] = self.get_genres()

		return dict_return

	def create_data_dict(self, listval):
		"""Creates a dictionary entry from a value called listval and appends data that is not already given"""
		self.load_url(listval)
		data_dict = self.data_as_dict()

		rj_start_ind = listval.find("RJ")
		if(rj_start_ind == -1):
			rj_start_ind = listval.find("VJ")
		rj_html_ind = listval.find(".html")
		rj_substring = listval[rj_start_ind:rj_html_ind]
		data_dict['code'] = rj_substring
		recording_time = datetime.datetime.now()
		formatted_time = recording_time.strftime("%Y-%m-%d")

		data_dict['recording_time'] = formatted_time
		return data_dict

	def save_as_json(self, filename):
		fname = f"{filename}.json"
		list_of_works = self.get_multiple_from_page()


		# create list to be saved. We need this to be create data dict
		list_of_works_as_dict = {}
		dict_counter = 0
		for l in list_of_works:
			print (f'progress = {list_of_works.index(l) + 1} / {len(list_of_works)}')
			list_of_works_as_dict[dict_counter] = self.create_data_dict(l)
			self._track_memory()
			dict_counter += 1

		with open(fname, 'w', newline='', encoding='utf-16') as f:
			json.dump(list_of_works_as_dict, f)
		self.driver.quit()

	def _find_next_page(self, current_page):
		page_info = []
		for link in self.soup.findAll('td', {'class':'page_no'}):
			for l in link.findAll('a',{'data-value' : str(current_page+1)}):
				print(l)
				print('---')
				d_val = None
				if (l.get('data-value') != None):
					d_val = int(l.get('data-value'))
		
				if ( d_val > int(current_page)):
					page_info.append(l.get('href'))
					page_info.append(int(l.string))
					return page_info
			return [1,1] 
		return [1,1]
		

	def get_multiple_from_page(self):
		count = 0
		list_of_works = []
		current_page = 1

		page_info = self._find_next_page(current_page)

		while(current_page <= page_info[1]):
			for link in self.soup.findAll('div', {'class':'multiline_truncate'}):
				for l in link.findAll('a',):
					hrefl = l.get('href')
					list_of_works.append(hrefl)
				count += 1
			current_page += 1
			if(page_info[0] == 1):
				current_page += 1
			else:
				self.load_url(page_info[0])
			new_page_info = self._find_next_page(current_page)
			if (new_page_info[0] != 1):
				page_info = new_page_info

		print(f"found {count} items")	
		return list_of_works
		
	def save_multiple_from_search(self, keywords, file_name="untitled", filetype_passed='json'):
		self.get_total_search_res(keywords)
		self.save_data_multiple(filename = file_name, filetype=filetype_passed)

	def save_multiple_from_url(self, url, name_of_file = "untitlted", filetype_passed='json'):
		self.load_url(url)
		self.save_data_multiple(filename=name_of_file, filetype=filetype_passed)

	def create_data_list(self,listval):
		self.load_url(listval)
		data_list = self.data_as_list()
		rj_start_ind = listval.find("RJ")
		if(rj_start_ind == -1):
			rj_start_ind = listval.find("VJ")
		rj_html_ind = listval.find(".html")
		rj_substring = listval[rj_start_ind:rj_html_ind]
		data_list.append(rj_substring)
		recording_time = datetime.datetime.now()
		formatted_time = recording_time.strftime("%Y-%m-%d")

		data_list.append(formatted_time)
		return(data_list)

	def save_as_csv(self, filename):
		fname = f"{filename}.csv"
		list_of_works = self.get_multiple_from_page()

		list_of_works_as_lists = []
		for l in list_of_works:
			print (f'progress = {list_of_works.index(l) + 1 } / {len(list_of_works)}')
			list_of_works_as_lists.append(self.create_data_list(l))
			self._track_memory()

		with open(fname, 'w', newline='', encoding='utf-16') as f:
			writer = csv.writer(f)
			headersf = ['name','url','seller name', 'price','sales','release date','rating','genres','code','data recording date']
			writer.writerow(headersf)
			for r in list_of_works_as_lists:
					writer.writerow(r)
		self.driver.quit()

	def save_data_multiple(self, filetype="csv", filename="untitled"):
		if(filetype == "csv"):
			self.save_as_csv(filename)
		elif(filetype == 'json'):
			self.save_as_json(filename)