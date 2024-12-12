import os
import shutil

def cleanup_files():
    """Clean up all generated files"""
    files_to_remove = [
        'library_data.csv',
        'book_covers'
    ]
    
    for item in files_to_remove:
        try:
            if os.path.isfile(item):  # Remove file
                os.remove(item)
                print(f"Removed file: {item}")
            elif os.path.isdir(item):  # Remove directory
                shutil.rmtree(item)
                print(f"Removed directory: {item}")
        except Exception as e:
            print(f"Error removing {item}: {str(e)}")

if __name__ == "__main__":
    cleanup_files()