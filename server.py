import os
import base64
import tempfile
import traceback
import asyncio
import urllib.request
import warnings
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import torch

# Limit PyTorch to 4 Threads (Leaves 4 threads for Chrome/Edge & Background services on an 8-thread i5 CPU)
torch.set_num_threads(4)

# Suppress annoying PyTorch CPU pin_memory warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.data.dataloader")

# Import our pipeline
from pipeline.detector import TextDetector
from pipeline.translator import TextTranslator
from pipeline.inpaint import Inpainter
from pipeline.typesetter import Typesetter
from pipeline.utils import ensure_font_downloaded

app = FastAPI(title="Manga Translator API")

# Setup CORS to allow the Chrome Extension to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline components on startup to avoid reloading models on every request
print("Loading NLP & OCR Models...")
font_path = ensure_font_downloaded()
detector = TextDetector() # Lazy loads languages En/Ja
translator = TextTranslator() # NLLB-200 robust translation
inpainter = Inpainter()
typesetter = Typesetter(font_path=font_path)
print("Models loaded. Ready to serve.")

# Import Cache Manager
from pipeline.cache import CacheManager
cache_manager = CacheManager()

@app.post("/clear_cache")
def clear_cache():
    cache_manager.clear_all()
    return {"status": "success", "message": "Đã dọn dẹp bộ nhớ đệm thành công."}

class TranslationRequest(BaseModel):
    image_url: str 
    src_lang: str = "en"
    dest_lang: str = "vi"

class TranslationResponse(BaseModel):
    translated_image_base64: str

# HTTP ENDPOINT (Keep for backward compatibility)
@app.post("/translate", response_model=TranslationResponse)
def translate_manga_image(req: TranslationRequest):
    # Backward compatibility checking
    cached_b64 = cache_manager.get_cached_image_base64(req.image_url)
    if cached_b64:
        return TranslationResponse(translated_image_base64=cached_b64)
    raise HTTPException(status_code=500, detail="Use WebSocket Endpoint for stability.")

# NEW WEBSOCKET ENDPOINT FOR REALTIME PROGRESS
@app.websocket("/ws/translate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            image_url = data.get("image_url")
            src_lang = data.get("src_lang", "en")
            if not image_url:
                continue
            
            # Start a background task for this image so multiple images can process concurrently
            asyncio.create_task(process_image_websocket(websocket, image_url, src_lang))
                
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket")

# Global queue to limit AI processing to 1 image at a time on low-end hardware
ai_processing_semaphore = asyncio.Semaphore(1)

async def process_image_websocket(websocket: WebSocket, image_url: str, src_lang: str = "en"):
    import aiohttp
    async def safe_send(data):
        try:
            await websocket.send_json(data)
            return True
        except RuntimeError as e:
            return False
        except Exception:
            return False

    try:
        # 0. Check Image Cache first
        cached_b64 = await asyncio.to_thread(cache_manager.get_cached_image_base64, image_url)
        if cached_b64:
            await safe_send({
                "status": "done", 
                "message": "[Cache Hit] Tải ảnh vèo vèo!", 
                "image_url": image_url,
                "translated_image_base64": cached_b64
            })
            return

        # 1. Download Async using aiohttp
        if not await safe_send({"status": "downloading", "message": "Đang tải ảnh...", "image_url": image_url}): return
        
        async def download_image_async(url):
            fd, temp_input_path = tempfile.mkstemp(suffix='.jpg')
            os.close(fd)
            fd2, temp_output_path = tempfile.mkstemp(suffix='.jpg')
            os.close(fd2)
            fd3, temp_inpainted_path = tempfile.mkstemp(suffix='.jpg')
            os.close(fd3)

            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                async with session.get(url, headers=headers, timeout=10) as response:
                    image_data = await response.read()
                    
            def _write(data, p):
                with open(p, 'wb') as f:
                    f.write(data)
            await asyncio.to_thread(_write, image_data, temp_input_path)
            return temp_input_path, temp_output_path, temp_inpainted_path

        temp_input_path, temp_output_path, temp_inpainted_path = await download_image_async(image_url)
        
        try:
            # Enqueue into the single-file pipeline!
            if not await safe_send({"status": "queued", "message": "Xếp hàng chờ xài AI...", "image_url": image_url}): return
            
            async with ai_processing_semaphore:
                # 2. Detect Text
                if not await safe_send({"status": "detecting", "message": f"Đang quét chữ AI ({src_lang.upper()})...", "image_url": image_url}): return
                detected_items = await asyncio.to_thread(detector.detect, temp_input_path, src_lang)
            
            # 3. Translate using Offline Local AI with TEXT CACHE
            if not await safe_send({"status": "translating", "message": "Siêu máy tính đang dịch...", "image_url": image_url}): return
            
            def do_translate_batch(items):
                # We separate out the items that actually need HuggingFace translation (cache miss)
                uncached_items_subset = []
                for item in items:
                    og_text = item['text']
                    if not og_text.strip():
                        item['translated_text'] = ""
                        continue
                    
                    cached_text = cache_manager.get_cached_translation(og_text)
                    if cached_text:
                        item['translated_text'] = cached_text
                    else:
                        uncached_items_subset.append(item)
                
                # Perform 1 single batch call for the misses!
                if uncached_items_subset:
                    translator.translate_batch(uncached_items_subset, src_lang)
                    # Cache the new results
                    for item in uncached_items_subset:
                        if 'translated_text' in item and item['translated_text']:
                            cache_manager.set_cached_translation(item['text'], item['translated_text'])

                return items
            
            detected_items = await asyncio.to_thread(do_translate_batch, detected_items)
            
            # 4. Inpaint
            if not await safe_send({"status": "inpainting", "message": "Đang xóa nền chữ gốc...", "image_url": image_url}): return
            await asyncio.to_thread(inpainter.inpaint_image, temp_input_path, detected_items, temp_inpainted_path)

            # 5. Typeset
            if not await safe_send({"status": "typesetting", "message": "Đang chèn font tiếng Việt...", "image_url": image_url}): return
            await asyncio.to_thread(typesetter.draw_text_on_image, temp_inpainted_path, detected_items, temp_output_path)

            # 6. Read Base64, Save Cache, and Return
            def encode_and_cache(path, url):
                with open(path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                result_base64 = f"data:image/jpeg;base64,{encoded_string}"
                cache_manager.set_cached_image_base64(url, result_base64)
                return result_base64

            result_base64 = await asyncio.to_thread(encode_and_cache, temp_output_path, image_url)
            
            await safe_send({
                "status": "done", 
                "message": "Hoàn tất!", 
                "image_url": image_url,
                "translated_image_base64": result_base64
            })
            
        finally:
            if os.path.exists(temp_input_path): os.remove(temp_input_path)
            if os.path.exists(temp_output_path): os.remove(temp_output_path)
            if os.path.exists(temp_inpainted_path): os.remove(temp_inpainted_path)

    except Exception as e:
        print(f"Translation Error for {image_url}: {e}")
        await safe_send({
            "status": "error", 
            "message": f"Lỗi xử lý AI: {str(e)}", 
            "image_url": image_url
        })

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
