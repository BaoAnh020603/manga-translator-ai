import os
import urllib.request

def ensure_font_downloaded():
    """
    Ensures that a Vietnamese-compatible font (Roboto) is downloaded.
    Returns the absolute path to the font file.
    """
    # Assuming this file is located in the 'pipeline' folder
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    font_dir = os.path.join(project_root, 'fonts')
    os.makedirs(font_dir, exist_ok=True)
    
    font_path = os.path.join(font_dir, 'Roboto-Regular.ttf')
    
    if not os.path.exists(font_path):
        print("Downloading Vietnamese-compatible font (Roboto)...")
        # Direct link to raw font file
        url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
            print(f"Font downloaded successfully to {font_path}")
        except Exception as e:
            print(f"Failed to download font: {e}")
            
    return font_path
