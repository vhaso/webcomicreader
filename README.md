# webcomicreader
A python 3.8/tk program that loads webcomics via http and bookmarks your page

## Functionality
Webcomics that have been publishing for a few years, have considerable backlogs. For (new) readers it can be tedious to keep track of their progress in a webcomic, because web browser don't allow for easy bookmarking of the last page that was read. The webcomicreader saves/loads the readers progress on closing/opening the program.
The webcomicreader is run from the command line with a settings_file argument:
    python webcomicreader.py <settings_file>

## The settings-file
Setting up a webcomic requires entering some html-selectors into a settings-file that allow the reader to scrape the web-site for the page-images, and writing an initial save-file. An example for the [XKCD](xkcd.com) webcomic is included. A settings file must contain the following elements:
* **page_type** is the type of the page for webcomics that are loaded via http us `online`
* **next_selector/prev_selector** are the selectors for the anchor elements with links to the next_previous page
* **the img_selector** is the selector for the page-image img element
* **save_file** is the relative path from the program's directory to the save_file
* **href_format** is the format that the next/previous hrefs are written in (currently `relative`, `absolute` or `full`)
* **src_format** is the format that the image src is written in (currently `no_schema` or `full`)
