import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
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


# ===== build index function =====
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


# ===== load index function =====
def load_index(filename="inverted_index.json"):
    with open(filename, 'r') as readfile:  # open file in read mode
        index = json.load(readfile)    # load index from JSON file into a dictionary
    return index  


# ===== print inverted index function =====
def print_inverted_index(index, word):
    if word in index:
        for url, count in index[word].items():
            print(f"\nWord: '{word}'\nURL: {url}\nFrequency: {count}")
    else:
        print(f"Word '{word}' not found in the index.")


# ===== find words function =====
def find_words(index, words):
    words_tokens = parse_tokenize(words)  # tokenize the input words
    total_urls = defaultdict(lambda: {"match_type": 0, "frequency": 0, "words_found": {}}) # match type: 2=exact, 1=all, 0=partial 

    # collect number of apperances of each word in the URLs
    word_url = []
    for word in words_tokens:
        if word in index:
            word_url.append(set(index[word].keys()))  # get the URLs for the word
        else:
            word_url.append(set())  # if the word is not in the index, add an empty set

    all_match = set.intersection(*word_url) if word_url else set()  # find the intersection of all sets (exact match)
    partial_match = set.union(*word_url) if word_url else set()  # partial match URLs
  
    for url in partial_match:
        total_frequency = 0
        words_found = {}

        for word in words_tokens:
            frequency = index.get(word, {}).get(url, 0)  # get the frequency of the word in the URL
            if frequency > 0: 
                words_found[word] = frequency  # add the word and its frequency to the dictionary
                total_frequency += frequency  # sum the frequencies

        match_type = 0  # default match type is 0 (partial match)

        try:
            response = requests.get(url)  # check if the URL is reachable
            page_text = response.text.lower()
            if words.lower() in page_text:  # check if the word is in the page text
                match_type = 2
            elif url in all_match:
                match_type = 1    
        except:
            continue     

        total_urls[url]["match_type"] = match_type  # set the match type for the URL
        total_urls[url]["frequency"] = total_frequency  # set the frequency for the URL
        total_urls[url]["words_found"] = words_found  # update the words found for the URL

    ranking = sorted(total_urls.items(), key=lambda x: (-x[1]["match_type"], -x[1]["frequency"]))  # sort the URLs by match type and frequency
    return ranking
    

def command_loop():
    index = load_index()  # load the index from the file
    while True:
        print("\nCommands: 'print <words>' || 'find <word>' || 'exit'")
        word = input("Enter command: ").strip().lower()
        if word == 'exit':
            break
        elif word.startswith("print "):
            _, word = word.split(maxsplit=1)  # split the command and the word
            print_inverted_index(index, word)
        elif word.startswith("find "):
            _, words = word.split(maxsplit=1)  # split the command and the words
            results = find_words(index, words)
            if results:
                for url, data in results:
                    print(f"\nURL: {url}")
                    print(f"Match Type: {data['match_type']} (2=Exact, 1=All, 0=Partial)")
                    print(f"Total Frequency: {data['frequency']}")
                    print("Words Found:")
                    for word, freq in data["words_found"].items():
                        print(f"'{word}': {freq}")
            else: 
                print("No results found.")
        else:
            print("Unknown command. Use 'print <words>' to see the page ranking of the words  || 'find <word>' to see the index for a word || 'exit' to quit.")

   
if __name__ == "__main__":
    command_loop()  # start the command loop
