import csv
import os
from datetime import datetime

class LibraryData:
    def __init__(self, csv_file="library_data.csv"):
        self.csv_file = csv_file
        self.fieldnames = [  # Define all fields for CSV structure
            'Title', 'Author', 'Year', 'Pages', 'Rating', 
            'Genre1', 'Genre2', 'Genre3', 'Genre4',
            'Description', 'Image_URL', 'Local_Image_Path',
            'Date_Added', 'Last_Modified', 'Read', 'Goodreads_URL'
        ]
        self._ensure_csv_exists()  # Create CSV if it doesn't exist
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def add_book(self, book_data): # Add a new book to the CSV file
        existing_books = self.get_all_books()
        if any(book['Title'] == book_data['Title'] for book in existing_books):
            print(f"Book '{book_data['Title']}' already exists in library")
            return False
        
        print(f"Adding book: {book_data['Title']}")  # Debug print
        book_data['Date_Added'] = datetime.now().isoformat()
        book_data['Last_Modified'] = book_data['Date_Added']
        
        for field in self.fieldnames:  # Ensure all fields exist
            if field not in book_data:
                book_data[field] = None
        
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(book_data)
        
        print(f"Successfully added: {book_data['Title']}")  # Debug print
        return True
    
    def get_all_books(self):
        if not os.path.exists(self.csv_file):
            return []
            
        books = []
        with open(self.csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['Year'] = int(row['Year']) if row['Year'] else 0  # Convert numeric fields
                row['Pages'] = int(row['Pages']) if row['Pages'] else 0
                row['Rating'] = float(row['Rating']) if row['Rating'] else 0.0
                row['Read'] = row['Read'].lower() == 'true' if row['Read'] else False  # Convert boolean field
                books.append(row)
        return books
    
    def update_book(self, title, updates):
        """Update a book's information in the CSV file"""
        books = self.get_all_books()
        updated = False
        
        for book in books:
            if book['Title'] == title:
                book.update(updates)
                book['Last_Modified'] = datetime.now().isoformat()  # Add timestamp
                updated = True
                break
        
        if updated:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(books)
        
        return updated
    
    def remove_book(self, title):
        """Remove a book from the CSV file"""
        books = self.get_all_books()
        original_length = len(books)
        books = [book for book in books if book['Title'] != title]
        
        if len(books) < original_length:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(books)
            return True
        return False