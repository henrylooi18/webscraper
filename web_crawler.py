import requests
from bs4 import BeautifulSoup
import time
import json
import re 


URL = "https://quotes.toscrape.com"
FIRST_PAGE = "/page/1/"
INDEX_FILE = "inverted_index.json"  # WHAT DOES THIS DO?
DELAY = 6  # 6 seconds of politeness window

def parse_tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())  # parse and tokenize each text, removing punctuation and converting to lowercase

def build_index():
    index = {}
    current_page = FIRST_PAGE

    while current_page:
        url = URL + current_page
        print(f"Crawling: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')  # parse the HTML content
        quotes = soup.find_all('div', class_='quote')   # find all quotes on the page

        for quote_div in quotes:
            text = quote_div.select_one('span.text').get_text()  # extract the quote text
            tokens = parse_tokenize(text)  # tokenize the quote text

            for token in tokens:
                if token not in index:
                    index[token] = {}  # create a new dictionary for the token if it doesn't exist
                if url not in index[token]:
                    index[token][url] = 0  # start counting from 0
                index[token][url] += 1  # increment of the frequency of the token in the URL

        # find the next hyperlink
        next_hyperlink = soup.select_one('li.next > a')
        current_page = next_hyperlink['href'] if next_hyperlink else None  # get the next page URL 
        time.sleep(DELAY)  # politeness delay

    with open(INDEX_FILE, 'w') as f:  # write to index file
        json.dump(index, f, indent=2)  # save the index to a JSON file
    print(f"Index saved to {INDEX_FILE}")

if __name__ == "__main__":
    build_index()  # run the index building function
    print("Indexing complete.")