from dlsite_scraper import dlsite_scraper

# Example 1: Scrap all results from a circle or search page. Have to manually get the page yourself. Be sure dlsite results are
# in tile format rather than list format in order to find the results.

crawler = dlsite_scraper()
url = 'https://www.dlsite.com/maniax/circle/profile/=/language/jp/sex_category%5B0%5D/male/keyword_maker_name/RG24350/order%5B0%5D/release_d/per_page/100/hd/1/page/1#works'
filename = 'momoirotest' # The path where the file will be saved. Here it will be saved to data/momoirotest.json
save_type = 'json' # can save as csv or json
crawler.save_multiple_from_url(url, name_of_file = filename, filetype_passed = save_type)



# Example 2: Manually getting specific pieces of information.

crawler.load_url('https://www.dlsite.com/maniax/work/=/product_id/RJ284644.html', single_url = True)
price = crawler.get_price()
sales = crawler.get_sales()
print(f"Sold {sales} at {price} JPY")



# Example 3: Search for results without manually getting a URL. Just add search terms to the search list.

search_list = ['ロり', 'NTR', 'ASMR']
filename = "custom_search"
save_type = "csv"
crawler.save_multiple_from_search(search_list, file_name = "custom search", filetype_passed = save_type)
