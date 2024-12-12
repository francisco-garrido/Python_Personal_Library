import requests
from bs4 import BeautifulSoup
import csv
import os
from time import sleep
import re

class GoodreadsScraperError(Exception):
    """Custom exception for scraper errors"""
    pass

class GoodreadsScraper:
    def __init__(self):
        self.base_url = "https://www.goodreads.com"
        self.headers = {  # Browser headers for requests
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def search_books(self, query):
        """Search for books and return results"""
        try:
            search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"  # Add timeout to requests
            response = requests.get(search_url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.select('tr[itemtype="http://schema.org/Book"]')[:3]
            
            if not search_results:
                raise GoodreadsScraperError(f"No results found for '{query}'")
            
            detailed_results = []  # Get detailed info for each result
            for result in search_results:
                book_link = result.select_one('a.bookTitle')  # Get book URL
                if book_link and 'href' in book_link.attrs:
                    book_url = book_link['href']
                    if not book_url.startswith('http'):
                        book_url = f"https://www.goodreads.com{book_url}"
                    
                    print(f"Debug - Found book URL: {book_url}")  # Debug print
                    
                    sleep(1)  # Respectful delay between requests
                    detailed_data = self._get_detailed_book_data(book_url)
                    if detailed_data:
                        detailed_data['Goodreads_URL'] = book_url
                        detailed_results.append(detailed_data)
            
            return detailed_results
            
        except requests.RequestException as e:
            raise GoodreadsScraperError(f"Network error: {str(e)}")
        except Exception as e:
            raise GoodreadsScraperError(f"Scraping error: {str(e)}")

    def _get_detailed_book_data(self, book_url):
        """Scrape detailed book information from book's page"""
        try:
            print(f"Debug - Fetching details from: {book_url}")  # Debug print
            response = requests.get(book_url, headers=self.headers)  # Get page data
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            genres = self._get_detailed_genres(soup)  # Get genres first
            
            book_data = {  # Compile all book data
                'Title': self._get_detailed_title(soup),
                'Author': self._get_detailed_author(soup),
                'Year': self._get_detailed_year(soup),
                'Pages': self._get_detailed_pages(soup),
                'Rating': self._get_detailed_rating(soup),
                'Genre1': genres[0],
                'Genre2': genres[1],
                'Genre3': genres[2],
                'Genre4': genres[3],
                'Description': self._get_detailed_description(soup),
                'Image_URL': self._get_detailed_image(soup),
                'Goodreads_URL': book_url  # Use the original URL
            }
            
            print(f"Debug - Book data URL: {book_data['Goodreads_URL']}")  # Debug print
            return book_data
            
        except Exception as e:
            print(f"Error getting details for {book_url}: {str(e)}")
            return None

    def _get_detailed_title(self, soup):
        """Get title from book page"""
        title_elem = soup.select_one('h1.Text__title1')  # Current title structure
        return title_elem.text.strip() if title_elem else "Unknown Title"

    def _get_detailed_author(self, soup):
        """Get author from book page"""
        author_elem = soup.select_one('span.ContributorLink__name')  # Current author structure
        return author_elem.text.strip() if author_elem else "Unknown Author"

    def _get_detailed_year(self, soup):
        """Get publication year from book page"""
        all_text = soup.text  # Look for "First published" text
        match = re.search(r'First published.*?(\d{4})', all_text)
        if match:
            year = int(match.group(1))
            print(f"Debug - Found year: {year} from text: {match.group(0)}")  # Show full match vs captured year
            if 1000 <= year <= 9999:  # Sanity check
                return year
        
        print("Debug - Publication text found:",  # Print debug info
              [text for text in all_text.split('\n') if 'published' in text.lower()])
        
        return 0

    def _get_detailed_pages(self, soup):
        """Get page count from book page"""
        details = soup.select_one('div.FeaturedDetails')  # Current page count location
        if details:
            pages_text = details.text
            match = re.search(r'(\d+) pages', pages_text)
            if match:
                print(f"Debug - Found pages: {match.group(1)}")  # Debug print
                return int(match.group(1))
        print("Debug - No page count found")  # Debug print
        return 0

    def _get_detailed_rating(self, soup):
        """Get rating from book page"""
        rating_elem = soup.select_one('div.RatingStatistics__rating')  # Current rating structure
        if rating_elem:
            try:
                print(f"Debug - Found rating: {rating_elem.text.strip()}")  # Debug print
                return float(rating_elem.text.strip())
            except ValueError:
                print("Debug - Invalid rating format")  # Debug print
                return 0.0
        print("Debug - No rating found")  # Debug print
        return 0.0

    def _get_detailed_genres(self, soup):
        """Get up to 4 genres from book page"""
        genres = set()  # Use set to avoid duplicates
        genre_selectors = [  # Current genre locations
            'div.BookPageMetadataSection__genres a.Button__link',
            'div.BookPageMetadataSection__classification a.Button__link'
        ]
        
        for selector in genre_selectors:
            elements = soup.select(selector)
            for element in elements:
                genre_text = element.text.strip()
                if (genre_text.lower() not in ['genres', 'genre'] and 
                    len(genre_text) > 1):  # Avoid empty or single-char genres
                    genres.add(genre_text)
        
        genre_list = list(genres)[:4]  # Convert set to list and get up to 4 genres
        
        while len(genre_list) < 4:  # Pad with None if we have fewer than 4 genres
            genre_list.append(None)
        
        return genre_list

    def _get_detailed_description(self, soup):
        """Get book description from book page"""
        desc_elem = soup.select_one('div.DetailsLayoutRightParagraph__widthConstrained')  # Current description location
        if not desc_elem:
            desc_elem = soup.select_one('div.TruncatedContent__text--large')  # Alternate description location
        return desc_elem.text.strip() if desc_elem else "No description available"

    def _get_detailed_image(self, soup):
        """Get book cover image URL from book page"""
        img_container = soup.select_one('div.BookCover__image img')  # Current image container
        if img_container and 'src' in img_container.attrs:
            url = img_container['src']
            return url.replace('._SY475_', '._SX1200_')  # Convert to high-res version
        return None

def save_image(url, book_title, image_folder="book_covers"):
    """Save book cover image to local folder"""
    if not url:
        return None
    
    if not os.path.exists(image_folder):  # Create image folder if it doesn't exist
        os.makedirs(image_folder)
    
    safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()  # Create safe filename
    filename = f"{safe_title}.jpg"
    filepath = os.path.join(image_folder, filename)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        print(f"Error saving image for {book_title}: {str(e)}")
        return None