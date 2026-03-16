import os
import argparse
import tempfile
import cv2

from pipeline.detector import TextDetector
from pipeline.translator import TextTranslator
from pipeline.inpaint import Inpainter
from pipeline.typesetter import Typesetter
from pipeline.utils import ensure_font_downloaded

def process_image(input_path, output_path, src_lang='en', dest_lang='vi', font_path=None):
    print("Initializing Pipeline Components...")
    if not font_path:
        font_path = ensure_font_downloaded()
        
    detector = TextDetector(lang=src_lang)
    translator = TextTranslator(src_lang=src_lang, dest_lang=dest_lang)
    inpainter = Inpainter()
    typesetter = Typesetter(font_path=font_path)

    print(f"Step 1: Detecting text in '{input_path}'...")
    detected_items = detector.detect(input_path)
    print(f"Detected {len(detected_items)} text regions.")

    print("Step 2: Translating text...")
    for i, item in enumerate(detected_items):
        original_text = item['text']
        translated = translator.translate(original_text)
        item['translated_text'] = translated
        print(f"  [{i+1}/{len(detected_items)}] '{original_text}' => '{translated}'")

    print("Step 3: Inpainting (removing original text)...")
    # Save inpainted image to a temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
    os.close(temp_fd)
    
    inpainter.inpaint_image(input_path, detected_items, temp_path)
    print("Inpainting completed.")

    print("Step 4: Typesetting (drawing translated text)...")
    typesetter.draw_text_on_image(temp_path, detected_items, output_path)
    print("Typesetting completed.")

    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    print(f"Done! Translated image saved to '{output_path}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manga Translator V1")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input image")
    parser.add_argument("--output", "-o", type=str, required=True, help="Path to output image")
    parser.add_argument("--src-lang", type=str, default="en", help="Source language code (e.g., 'en', 'ja', 'ko', 'ch')")
    parser.add_argument("--dest-lang", type=str, default="vi", help="Destination language code")
    parser.add_argument("--font", type=str, default=None, help="Path to a TrueType font file (.ttf)")

    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        exit(1)
        
    process_image(
        input_path=args.input,
        output_path=args.output,
        src_lang=args.src_lang,
        dest_lang=args.dest_lang,
        font_path=args.font
    )
