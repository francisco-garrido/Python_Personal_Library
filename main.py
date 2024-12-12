from modern_library_gui import ModernLibraryGUI

def main():
    print("Starting Library Manager...")
    try:
        app = ModernLibraryGUI()
        print("GUI initialized successfully")
        app.run()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 