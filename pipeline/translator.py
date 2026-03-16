from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os

class TextTranslator:
    def __init__(self):
        self.model_name = "facebook/nllb-200-distilled-600M"
        print(f"============================================================")
        print(f" LOADING BIG BRAIN AI: NLLB-200 (2.4GB)")
        print(f" The first run will take a few minutes to download the model.")
        print(f"============================================================")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.eval() # Set to evaluation mode
            print("NLLB-200 Translation model loaded successfully.")
        except Exception as e:
            print(f"Failed to load NLLB-200 model: {e}")
            self.model = None
            self.tokenizer = None
        
    def translate_batch(self, items, src_lang='en'):
        """
        Translates a list of dictionary items using the robust NLLB-200 offline model.
        Supports both EN -> VI and JA -> VI seamlessly out of the box.
        """
        if not items:
            return items

        if not getattr(self, 'model', None):
            print("Translation model is not available.")
            for item in items:
                item['translated_text'] = item.get('text', '')
            return items

        # Map our simple ISO codes to NLLB BCP-47 codes
        lang_map = {
            'en': 'eng_Latn',
            'ja': 'jpn_Jpan',
            'ko': 'kor_Hang'
        }
        nllb_src_lang = lang_map.get(src_lang, 'eng_Latn')
        nllb_tgt_lang = 'vie_Latn'

        texts_to_translate = []
        indices = []
        
        for i, item in enumerate(items):
            text = item.get('text', '').strip()
            # If text is too short or just punctuation, skip AI
            if len(text) > 1:
                texts_to_translate.append(text)
                indices.append(i)
            else:
                item['translated_text'] = text

        if not texts_to_translate:
            return items

        try:
            # Tell the tokenizer what the source language is
            self.tokenizer.src_lang = nllb_src_lang
            
            # Tokenize all sentences into a batch
            inputs = self.tokenizer(texts_to_translate, return_tensors="pt", padding=True, truncation=True)
            
            # Identify the target language code sequence for the generation model
            tgt_lang_id = self.tokenizer.lang_code_to_id[nllb_tgt_lang]
            
            # Generate translations using torch.no_grad() to save RAM on low-end CPUs
            with torch.no_grad():
                translated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=tgt_lang_id,
                    max_length=200
                )
            
            # Decode matrix back to human readable text
            results = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            
            # Map back to original items
            for idx, res in zip(indices, results):
                items[idx]['translated_text'] = res
                    
        except Exception as e:
            print(f"Local Offline NLLB Translation Error: {e}")
            # Fallback to copy original if failed
            for idx in indices:
                item = items[idx]
                item['translated_text'] = item.get('text', '')

        return items
