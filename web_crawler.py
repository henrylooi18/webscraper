import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import re 



URL = "https://quotes.toscrape.com"
FIRST_PAGE = "/"
INDEX_FILE = "inverted_index.json"  # index file to store the inverted index
DELAY = 6  # 6 seconds of politeness window

def parse_tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())  # parse and tokenize each text, removing punctuation and converting to lowercase


def extract_next_page(soup, url):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        joined_url = urljoin(url, link)  # join the base URL with the relative link

        if urlparse(joined_url).netloc == urlparse(url).netloc:  # only crawl in the same domain 
            links.add(joined_url)
    return links


def build_index():
    index = {}
    next_visit = {URL + '/'}
    visited = set()
    
    while next_visit:
        current_url = next_visit.pop()
        if current_url in visited:
            continue
        print(f"Crawling: {current_url}")
        visited.add(current_url)

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')  # parse the HTML content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {current_url}: {e}")
            continue

        all_text = soup.get_text(separator=' ', strip=True)  # get all text from the page
        tokens = parse_tokenize(all_text)

        # indexing the tokens
        for token in tokens:
            if token not in index:
                index[token] = {}  # create a new dictionary for the token if it doesn't exist
            if current_url not in index[token]:
                index[token][current_url] = 0  # start counting from 0
            index[token][current_url] += 1  # increment of the frequency of the token in the URL

        internal_links = extract_next_page(soup, current_url)  # extract internal links from the page
        next_visit.update(internal_links)  # add new links to the set of links to visit

        #time.sleep(DELAY)  # politeness delay

    with open(INDEX_FILE, 'w') as f:  # write to index file
        json.dump(index, f, indent=2)  # save the index to a JSON file
    print(f"Index saved to {INDEX_FILE}")

   
'''
def load_index(filename="inverted_index.json"):
    with open(filename, 'r') as readfile:  # open file in read mode
        index = json.load(readfile)    # load index from JSON file into a dictionary
    return index  


def print_inverted_index(index, word):
    if word in index:
        for url, count in index[word].items():
            print(f"Word: '{word}'\nURL: {url}\nFrequency: {count}")
    else:
        print(f"Word '{word}' not found in the index.")
'''
   
if __name__ == "__main__":
    build_index()  # run the index building function
    print("Indexing complete.")
