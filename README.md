Code that grabs data from a product on dlsite. I wanted to get sales and stuff from the site without having to manually go through each page and write stuff down, so here this is. dlsite_example.py shows all 3 ways that I inteded to use the code. The code itself definitely isn't the greatest because this is the first thing I've written in python, but everything works.

Make sure you have chrome driver properly installed and in your path.

4-22-2020
Removed JSON as a save type because it was causing all sorts of memory issues. I made an attempt at multithreading. My computer isn't the strongest, but it isn't weak either. Ryzen 5 1600, RX 470, 16 gb RAM. So... If your specs are like mine, everything should run fine from the get go. If not, change the global variable MAX_WORKERS to 1. It's in the __init__.
