import customtkinter as ctk
from PIL import Image
import requests
from io import BytesIO
from web_scraper import GoodreadsScraper, save_image
from library_data import LibraryData
import os
import threading
import io

class ModernLibraryGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.geometry("1200x800")
        self.window.title("Library Manager")
        ctk.set_appearance_mode("dark")
        
        self.load_custom_fonts()  # Load custom fonts for the application
        self.scraper = GoodreadsScraper()
        self.library_data = LibraryData()
        
        self.main_container = ctk.CTkFrame(self.window, fg_color="transparent")  # Main container for all widgets
        self.main_container.pack(fill="both", expand=True)
        
        self.current_sort = {  # Add sort state tracking
            'key': 'date_added',
            'reverse': True
        }
        
        self.image_cache = {}  # Add image cache with compression
        self.image_quality = 85  # JPEG compression quality (0-100)
        self.max_cache_size = 50  # Maximum number of images to keep in cache
        self.preloading = False  # Add preload flag
        
        self.show_search()

    def load_custom_fonts(self):
        """Load custom fonts for the application"""
        self.fonts = {  # Define font configurations using system fonts
            'title': ("Georgia", 75, "bold"),        # Changed from Garamond to Georgia
            'header': ("Trebuchet MS", 24, "bold"),   # Modern sans-serif
            'normal': ("Segoe UI", 14),               # Clean, readable font
            'search': ("Trebuchet MS", 20),           # Consistent with header
            'description': ("Segoe UI", 14)           # Consistent with normal
        }

    def show_search(self):
        for widget in self.main_container.winfo_children():  # Clear container
            widget.destroy()
        
        title_section = ctk.CTkFrame(self.main_container, fg_color="transparent")  # Title section
        title_section.pack(fill="x", pady=(20, 30))
        
        ctk.CTkLabel(  # Main title with white text
            title_section,
            text="My Personal Library",
            font=self.fonts['title'],
            text_color="white"
        ).pack(pady=10)
        
        search_section = ctk.CTkFrame(self.main_container, fg_color="transparent")  # Search section
        search_section.pack(fill="x", pady=(0, 20))
        
        search_entry = ctk.CTkEntry(  # Search bar
            search_section,
            width=400,
            height=45,
            placeholder_text="Search for a book",
            font=self.fonts['search'],
            border_width=0
        )
        search_entry.place(relx=0.5, rely=0.5, anchor="center")
        search_entry.bind("<Return>", lambda e: self.handle_search(search_entry.get()))
        
        books = self.library_data.get_all_books()  # Show library section if there are books
        if books:
            self.preload_images(books)  # Start preloading images
            
            sort_keys = {  # Define sort keys
                'title': lambda x: x['Title'].lower() if x['Title'] else '',
                'author': lambda x: x['Author'].lower() if x['Author'] else '',
                'year': lambda x: int(x['Year']) if x['Year'] else 0,
                'rating': lambda x: float(x['Rating']) if x['Rating'] else 0.0,
                'date_added': lambda x: x['Date_Added'] if x['Date_Added'] else '',
                'read': lambda x: (x.get('Read', False), x['Title'].lower())
            }
            
            if self.current_sort['key'] in sort_keys:  # Sort books according to current sort state
                books.sort(
                    key=sort_keys[self.current_sort['key']], 
                    reverse=self.current_sort['reverse']
                )
            
            sort_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")  # Create sorting buttons
            sort_frame.pack(fill="x", padx=50, pady=10)
            
            ctk.CTkLabel(
                sort_frame,
                text="Sort by:",
                font=self.fonts['header']
            ).pack(side="left", padx=(0, 10))
            
            sort_options = [  # Expanded sorting options
                ("Title (A-Z)", "title", False),
                ("Author (A-Z)", "author", False),
                ("Year (Newest)", "year", True),
                ("Year (Oldest)", "year", False),
                ("Rating (High-Low)", "rating", True),
                ("Rating (Low-High)", "rating", False),
                ("Recently Added", "date_added", True)
            ]
            
            for label, key, reverse in sort_options:  # Create sort buttons
                is_current = (key == self.current_sort['key'] and 
                            reverse == self.current_sort['reverse'])
                
                button = ctk.CTkButton(
                    sort_frame,
                    text=label,
                    width=120,
                    command=lambda k=key, r=reverse: self.sort_library(k, r),
                    font=self.fonts['normal'],
                    fg_color=("#1B2838" if not is_current else "#2A4157"),
                    hover_color="#2A4157"
                )
                button.pack(side="left", padx=5)
            
            library_container = ctk.CTkFrame(self.main_container, fg_color="transparent")  # Create container for library
            library_container.pack(fill="both", expand=True, padx=50, pady=20)
            
            library_frame = ctk.CTkScrollableFrame(  # Create scrollable frame
                library_container,
                fg_color="transparent",
                height=600,
                scrollbar_button_hover_color=("gray70", "gray30")
            )
            library_frame.pack(fill="both", expand=True)
            
            def load_batch(start_idx):  # Load books in batches
                end_idx = min(start_idx + 5, len(books))
                for i in range(start_idx, end_idx):
                    self.create_library_entry(library_frame, books[i], i + 1)
                if end_idx < len(books):
                    self.window.after(50, lambda: load_batch(end_idx))
            
            load_batch(0)

    def create_library_entry(self, container, book, index):
        tile = ctk.CTkFrame(  # Create main tile with fixed size
            container,
            fg_color=("gray95", "gray15"),
            height=370,  # Increased tile height
            corner_radius=10
        )
        tile.pack(fill="x", pady=5)
        tile.pack_propagate(False)
        
        def load_image():  # Lazy load image
            if book['Local_Image_Path'] and os.path.exists(book['Local_Image_Path']):
                try:
                    cache_key = book['Local_Image_Path']
                    if cache_key in self.image_cache:  # Check cache first
                        return self.image_cache[cache_key]
                    
                    with Image.open(book['Local_Image_Path']) as img:  # Load and process image
                        img = img.resize((200, 280), Image.Resampling.LANCZOS)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG', quality=self.image_quality, optimize=True)
                        buffer.seek(0)
                        compressed_img = Image.open(buffer)
                        
                        ctk_image = ctk.CTkImage(
                            light_image=compressed_img,
                            dark_image=compressed_img,
                            size=(200, 280)
                        )
                        
                        if len(self.image_cache) >= self.max_cache_size:  # Manage cache size
                            self.image_cache.pop(next(iter(self.image_cache)))
                        
                        self.image_cache[cache_key] = ctk_image
                        return ctk_image
                except Exception as e:
                    print(f"Error loading image: {e}")
                    return None
            return None
        
        image_frame = ctk.CTkFrame(tile, width=220, height=300, fg_color="transparent")  # Reduced width
        image_frame.pack(side="left", padx=20, pady=20)  # Same padding all around
        image_frame.pack_propagate(False)
        
        def delayed_image_load():  # Load image after short delay
            ctk_image = load_image()
            if ctk_image:
                image_button = ctk.CTkButton(
                    image_frame,
                    image=ctk_image,
                    text="",
                    fg_color="transparent",
                    hover_color=("gray85", "gray25"),
                    corner_radius=0,  # Remove button corner radius
                    command=lambda: self.open_goodreads(book.get('Goodreads_URL', None))
                )
                image_button.pack(fill="both", expand=True)  # Remove internal padding
                self.create_tooltip(image_button, "Open Goodreads Page")
        
        self.window.after(100 * index, delayed_image_load)  # Schedule image loading
        
        remove_button = ctk.CTkButton(  # Remove button
            tile,  # Parent is now the blue tile frame
            text="Remove book",
            width=120,
            command=lambda: self.remove_book(book['Title']),
            font=self.fonts['normal'],
            fg_color="#1B2838",
            hover_color="#2A4157"
        )
        remove_button.place(x=70, y=340)  # Adjusted for narrower frame
        
        details_container = ctk.CTkFrame(tile, fg_color="transparent")  # Right side: Scrollable content
        details_container.pack(side="left", fill="both", expand=True)
        
        details_scroll = ctk.CTkScrollableFrame(  # Create scrollable frame for details
            details_container,
            fg_color="transparent",
            height=300
        )
        details_scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(  # Title
            details_scroll,
            text=book['Title'],
            font=self.fonts['header'],
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(  # Author and Year
            details_scroll,
            text=f"by {book['Author']} ({book['Year']})",
            font=self.fonts['normal'],
            anchor="w"
        ).pack(fill="x", pady=5)
        
        genres = [book.get(f'Genre{i}') for i in range(1, 5) if book.get(f'Genre{i}')]  # Genres
        if genres:
            genre_text = " | ".join(genres)
            ctk.CTkLabel(
                details_scroll,
                text=f"Genres: {genre_text}",
                font=self.fonts['normal'],
                anchor="w"
            ).pack(fill="x", pady=5)
        
        rating_frame = ctk.CTkFrame(details_scroll, fg_color="transparent")  # Rating with stars
        rating_frame.pack(fill="x", pady=5)
        
        rating = float(book['Rating'])
        full_stars = int(rating)
        half_star = rating - full_stars >= 0.5
        
        stars_text = "★" * full_stars
        if half_star:
            stars_text += "½"
        stars_text += "☆" * (5 - full_stars - (1 if half_star else 0))
        
        ctk.CTkLabel(
            rating_frame,
            text=f"Rating: {stars_text} ({rating:.1f})",
            font=self.fonts['normal'],
            text_color=("gold", "gold"),
            anchor="w"
        ).pack(side="left")
        
        if book.get('Description'):  # Description
            description = book['Description']
            description_frame = ctk.CTkFrame(details_scroll, fg_color="transparent")
            description_frame.pack(fill="x", pady=10)
            
            description_label = ctk.CTkLabel(
                description_frame,
                text=description,
                font=self.fonts['description'],
                anchor="w",
                justify="left",
                wraplength=600
            )
            description_label.pack(fill="x")

    def handle_search(self, query):
        if not query.strip():
            return
        
        for widget in self.main_container.winfo_children():  # Show loading
            widget.destroy()
        
        loading_label = ctk.CTkLabel(
            self.main_container,
            text="Loading...",
            font=self.fonts['header']
        )
        loading_label.place(relx=0.5, rely=0.4, anchor="center")
        
        self.window.after(100, lambda: self.search_and_display(query))  # Perform search after brief delay

    def search_and_display(self, query):
        try:
            results = self.scraper.search_books(query)
            self.show_results(results)
        except Exception as e:
            self.show_error(str(e))

    def show_results(self, results):
        for widget in self.main_container.winfo_children():  # Clear container
            widget.destroy()
        
        title_section = ctk.CTkFrame(self.main_container, fg_color="transparent")  # Title section
        title_section.pack(fill="x", pady=(20, 30))
        
        ctk.CTkLabel(  # Main title
            title_section,
            text="Search Results",
            font=self.fonts['title'],
            text_color="white"
        ).pack(pady=10)
        
        back_button = ctk.CTkButton(  # Back button
            self.main_container,
            text="← Back to Library",
            command=self.show_search,
            width=150,
            font=self.fonts['normal'],
            fg_color="#1B2838",
            hover_color="#2A4157"
        )
        back_button.pack(anchor="w", padx=50, pady=(0, 20))
        
        results_container = ctk.CTkScrollableFrame(  # Make results scrollable
            self.main_container,
            fg_color="transparent",
            height=600,  # Set a fixed height
            scrollbar_button_hover_color=("gray70", "gray30")
        )
        results_container.pack(fill="both", expand=True, padx=50)
        
        if not results:  # Show message if no results
            ctk.CTkLabel(
                results_container,
                text="No results found",
                font=self.fonts['header']
            ).pack(pady=20)
            return
        
        for result in results:  # Create tiles for each result
            self.create_result_tile(results_container, result)

    def preload_images(self, books):
        """Preload and compress images in a separate thread"""
        def preload():
            self.preloading = True
            for book in books:
                if book['Local_Image_Path'] and os.path.exists(book['Local_Image_Path']):
                    cache_key = book['Local_Image_Path']
                    if cache_key not in self.image_cache:
                        try:
                            with Image.open(book['Local_Image_Path']) as img:  # Open and resize image
                                img = img.resize((200, 280), Image.Resampling.LANCZOS)
                                if img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                buffer = io.BytesIO()
                                img.save(buffer, format='JPEG', quality=self.image_quality, optimize=True)
                                buffer.seek(0)
                                compressed_img = Image.open(buffer)
                                
                                ctk_image = ctk.CTkImage(
                                    light_image=compressed_img,
                                    dark_image=compressed_img,
                                    size=(200, 280)
                                )
                                
                                if len(self.image_cache) >= self.max_cache_size:  # Manage cache size
                                    self.image_cache.pop(next(iter(self.image_cache)))
                                
                                self.image_cache[cache_key] = ctk_image
                        except Exception as e:
                            print(f"Error preloading image: {e}")
            self.preloading = False
        
        threading.Thread(target=preload, daemon=True).start()  # Start preloading thread

    def sort_library(self, key, reverse=False):
        """Sort library by given key and refresh display"""
        print(f"Sorting by {key} {'descending' if reverse else 'ascending'}")
        
        self.current_sort = {  # Update current sort state
            'key': key,
            'reverse': reverse
        }
        
        self.show_search()  # Refresh display with new sort order

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        tooltip_label = None
        
        def show_tooltip(event):
            nonlocal tooltip_label
            if tooltip_label is None:
                tooltip_label = ctk.CTkLabel(
                    self.window,
                    text=text,
                    fg_color=("gray80", "gray20"),
                    corner_radius=6,
                    text_color=("gray20", "gray80"),
                    font=self.fonts['normal'],
                    padx=10,
                    pady=5
                )
            update_position(event)
            tooltip_label.lift()
        
        def update_position(event):
            if tooltip_label:
                x = widget.winfo_rootx() - self.window.winfo_rootx() + event.x + 15
                y = widget.winfo_rooty() - self.window.winfo_rooty() + event.y + 10
                tooltip_label.place(x=x, y=y)
        
        def hide_tooltip(event):
            nonlocal tooltip_label
            if tooltip_label:
                tooltip_label.destroy()
                tooltip_label = None
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Motion>", lambda e: self.window.after(5, lambda: update_position(e)))
        widget.bind("<Leave>", hide_tooltip)

    def open_goodreads(self, url):
        """Open URL in default web browser"""
        if url and url != 'None' and isinstance(url, str):
            try:
                if not url.startswith('http'):
                    url = 'https://www.goodreads.com' + url
                import webbrowser
                webbrowser.open(url)
            except Exception as e:
                self.show_error(f"Error opening URL: {str(e)}")
        else:
            self.show_error("Goodreads URL not available for this book")

    def update_read_status(self, title, is_read):
        """Update the read status of a book"""
        self.library_data.update_book(title, {'Read': is_read})

    def show_error(self, message):
        """Show error message and return to search after delay"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.main_container,
            text=f"Error: {message}",
            font=self.fonts['header']
        )
        error_label.place(relx=0.5, rely=0.4, anchor="center")
        
        self.window.after(2000, self.show_search)

    def create_result_tile(self, container, book):
        """Create a tile for a search result"""
        tile = ctk.CTkFrame(  # Create main tile
            container,
            fg_color=("gray95", "gray15"),
            height=220,  # Increased height to accommodate button
            corner_radius=10
        )
        tile.pack(fill="x", pady=5, padx=5)
        tile.pack_propagate(False)
        
        left_frame = ctk.CTkFrame(tile, fg_color="transparent")  # Left side: Image and add button
        left_frame.pack(side="left", padx=20, pady=(20, 10))  # Adjusted padding
        
        if book.get('Image_URL'):  # Load and display image
            try:
                response = requests.get(book['Image_URL'])
                image = Image.open(BytesIO(response.content))
                image = image.resize((100, 140), Image.Resampling.LANCZOS)
                
                ctk_image = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(100, 140)
                )
                
                image_label = ctk.CTkLabel(
                    left_frame,
                    image=ctk_image,
                    text=""
                )
                image_label.pack(pady=(0, 10))
            except Exception as e:
                print(f"Error loading image: {e}")
        
        add_button = ctk.CTkButton(  # Add to library button
            left_frame,
            text="Add to Library",
            width=100,
            command=lambda: self.add_book_to_library(book),
            font=self.fonts['normal'],
            fg_color="#1B2838",
            hover_color="#2A4157"
        )
        add_button.pack()
        
        right_frame = ctk.CTkFrame(tile, fg_color="transparent")  # Right side: Book details
        right_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        ctk.CTkLabel(  # Title
            right_frame,
            text=book['Title'],
            font=self.fonts['header'],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(  # Author and Year
            right_frame,
            text=f"by {book['Author']} ({book['Year']})",
            font=self.fonts['normal'],
            anchor="w"
        ).pack(fill="x", pady=5)
        
        genres = [book.get(f'Genre{i}') for i in range(1, 5) if book.get(f'Genre{i}')]  # Genres
        if genres:
            genre_text = " | ".join(genres)
            ctk.CTkLabel(
                right_frame,
                text=f"Genres: {genre_text}",
                font=self.fonts['normal'],
                anchor="w"
            ).pack(fill="x", pady=5)
        
        if book.get('Rating'):  # Rating
            rating = float(book['Rating'])
            full_stars = int(rating)
            half_star = rating - full_stars >= 0.5
            
            stars_text = "★" * full_stars
            if half_star:
                stars_text += "½"
            stars_text += "☆" * (5 - full_stars - (1 if half_star else 0))
            
            ctk.CTkLabel(
                right_frame,
                text=f"Rating: {stars_text} ({rating:.1f})",
                font=self.fonts['normal'],
                text_color=("gold", "gold"),
                anchor="w"
            ).pack(fill="x", pady=5)
        
        if book.get('Description'):  # Description
            description = book['Description']
            if len(description) > 300:  # Truncate long descriptions
                description = description[:297] + "..."
            
            ctk.CTkLabel(
                right_frame,
                text=description,
                font=self.fonts['description'],
                anchor="w",
                justify="left",
                wraplength=800
            ).pack(fill="x", pady=5)

    def add_book_to_library(self, book):
        """Add a book to the library"""
        try:
            if book.get('Image_URL'):  # Save image locally
                local_image = save_image(book['Image_URL'], book['Title'])
                if local_image:
                    book['Local_Image_Path'] = local_image
            
            if self.library_data.add_book(book):  # Add to library
                self.show_search()  # Refresh display
        except Exception as e:
            self.show_error(str(e))

    def remove_book(self, title):
        """Remove a book from the library"""
        try:
            if self.library_data.remove_book(title):
                self.show_search()  # Refresh display
        except Exception as e:
            self.show_error(str(e))

    def run(self):
        """Start the main event loop"""
        self.window.mainloop()