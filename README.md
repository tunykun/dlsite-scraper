Code that grabs data from a product on dlsite. I made this to get sales and other data from the site without having to manually go through each page and write stuff down. dlsite_example.py shows all 3 ways that I inteded to use the code. The code itself definitely isn't the greatest because this is the first thing I've written in python, but everything works.


Be sure to:
  1. install all the proper modules. Selenium, Beautiful Soup, etc.
  2. have chrome driver installed.


4-22-2020:
Removed JSON as a savetype because I kept running into memory issues.
Made an attempt at multithreading(?) I think. It's faster than collecting one page at a time. That's for sure. Strong-ish CPU and ~16 GB of ram is recommended. Can lower the MAX_WORKERS global variable to 1 if you don't want to give multithreading a go.
