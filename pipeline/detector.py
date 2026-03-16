import easyocr

class TextDetector:
    def __init__(self):
        # Lazy load readers to save RAM on startup
        self.readers = {}

    def get_reader(self, lang):
        if lang not in self.readers:
            print(f"Loading EasyOCR for language: {lang}...")
            self.readers[lang] = easyocr.Reader([lang])
        return self.readers[lang]

    def detect(self, image_path, lang='en'):
        """
        Detect text in an image, grouped into paragraphs.
        """
        reader = self.get_reader(lang)
        # Using paragraph=True groups text, but returns (box, text) instead of (box, text, score)
        result = reader.readtext(image_path, paragraph=True)
        detected_items = []
        
        for item in result:
            box = item[0]
            text_content = item[1]
            
            # Ensure coordinates are floats
            box = [[float(point[0]), float(point[1])] for point in box]
            
            detected_items.append({
                'box': box,
                'text': text_content,
                'score': 1.0  # Paragraph mode does not return a confidence score
            })
        
        return detected_items
