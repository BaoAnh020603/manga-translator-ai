import os
import json
import hashlib
import time

class CacheManager:
    def __init__(self, cache_dir='cache'):
        # Get path relative to the root project folder
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cache_dir = os.path.join(project_root, cache_dir)
        self.image_cache_dir = os.path.join(self.cache_dir, 'images')
        self.text_cache_path = os.path.join(self.cache_dir, 'texts.json')
        
        # Ensure directories exist
        os.makedirs(self.image_cache_dir, exist_ok=True)
        
        # Load text cache
        self.text_cache = {}
        if os.path.exists(self.text_cache_path):
            try:
                with open(self.text_cache_path, 'r', encoding='utf-8') as f:
                    self.text_cache = json.load(f)
            except Exception:
                pass

    def _hash_url(self, url):
        """Generate a safe filename from a URL string."""
        url_bytes = str(url).encode('utf-8')
        return hashlib.md5(url_bytes).hexdigest()

    # --- IMAGE CACHING ---
    def get_cached_image_base64(self, image_url):
        """Returns the base64 string if the image URL is cached, otherwise None."""
        file_hash = self._hash_url(image_url)
        cache_path = os.path.join(self.image_cache_dir, f"{file_hash}.txt")
        
        if os.path.exists(cache_path):
            try:
                # Basic TTL check (cache valid for 7 days)
                file_age = time.time() - os.path.getmtime(cache_path)
                if file_age > 7 * 24 * 3600:
                    os.remove(cache_path)
                    return None
                    
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
        return None

    def set_cached_image_base64(self, image_url, base64_data):
        """Saves the final translated base64 image data to cache."""
        file_hash = self._hash_url(image_url)
        cache_path = os.path.join(self.image_cache_dir, f"{file_hash}.txt")
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(base64_data)
        except Exception as e:
            print(f"Failed to write image cache: {e}")

    # --- TEXT CACHING ---
    def get_cached_translation(self, text):
        """Returns the translated text if it exists in the JSON dictionary cache."""
        return self.text_cache.get(text.strip().lower())

    def set_cached_translation(self, original_text, translated_text):
        """Saves a new translation mapping to the JSON dictionary cache."""
        key = original_text.strip().lower()
        if not key or not translated_text:
            return
            
        self.text_cache[key] = translated_text
        
        # Randomly save to disk occasionally to avoid disk thrashing when translating many items
        # In a real heavy production app, use Redis. For local, this is fine.
        if len(self.text_cache) % 5 == 0:
            self._save_text_cache()

    def _save_text_cache(self):
        try:
            with open(self.text_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.text_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write text cache: {e}")
            
    # --- CLEAR ---
    def clear_all(self):
        """Clears all caches to free up disk space."""
        import shutil
        if os.path.exists(self.image_cache_dir):
            shutil.rmtree(self.image_cache_dir)
            os.makedirs(self.image_cache_dir, exist_ok=True)
            
        self.text_cache = {}
        if os.path.exists(self.text_cache_path):
            os.remove(self.text_cache_path)
