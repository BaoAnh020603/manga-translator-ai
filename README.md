# Manga Translator AI 📖🚀

An intelligent, real-time localized Manga, Manhwa, and Comic translation system. This tool runs **100% offline** on your local machine, utilizing state-of-the-art Natural Language Processing (NLP) models and Computer Vision techniques to detect, mask, and translate comics instantly as you scroll through your browser.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-green)
![PyTorch](https://img.shields.io/badge/PyTorch-Offline-orange)

---

## 🔥 Key Features

1. **Smart Real-time Viewport Translation:** (via Intersection Observer). The browser extension only translates panels as they enter your screen. No more translating the whole website upfront.
2. **100% Local & Offline (No APIs):** Say goodbye to Google Translate API limits. Powered by Facebook's **NLLB-200** (No Language Left Behind) 2.4GB Machine Learning model via HuggingFace `transformers`.
3. **Multi-Language Support:** Translates directly from English (EN), Japanese Raw Manga (JA), and Korean Webtoon/Manhwa (KO) directly into Vietnamese contextually. 
4. **Hardware Optimized (Low-End PC):** Utilizes `asyncio.Semaphore` queuing and `torch.no_grad()` to heavily restrict CPU and RAM consumption. Works smoothly on 8GB RAM Laptops!
5. **Advanced Smart Inpainting:** Features OpenCV Adaptive Otsu Thresholding to isolate text logic, removing text cleanly **without smudging** the background comic artwork. 
6. **Professional Typesetting:** Uses Python Pillow to calculate word wraps automatically and applies a heavy `stroke_width` white-outline around translated text so it's readable on complex dark backgrounds.
7. **Custom Fine-Tuning:** Comes with a built in `train.py` script. Feed `dataset/manga_vocab.csv` to train your own custom LLM pipeline offline.

---

## 🧠 System Architecture

We designed `Manga Translator AI` to be a non-blocking macro-system:
- **Client**: A Glassmorphism Chrome Extension injecting WebSockets.
- **Backend**: FastAPI managing Image Caching, Text Caching, Asynchronous `aiohttp` downloads, and ML Pipelines.

👉 **View the detailed UML & Mermaid Flowcharts here: [Architecture Documentation](docs/architecture.md)**

---

## 🛠️ Installation & Setup

### 1. Backend Server Setup
Ensure you have Python 3.9+ installed natively.

```bash
# Clone the Repository
git clone https://github.com/your-username/manga-translator-ai.git
cd manga-translator-ai

# Install dependencies (Downloads PyTorch, EasyOCR, Transformers, OpenCV)
pip install -r requirements.txt

# Start the Web Socket Server
python server.py
```
> *Note: First startup will take 5-10 minutes to download the 2.4GB NLLB-200 AI model directly from HuggingFace.*

### 2. Chrome Extension Setup
1. Open up Google Chrome or Microsoft Edge and navigate to `chrome://extensions/` (or `edge://extensions/`).
2. Toggle **Developer mode** on the top right.
3. Click **Load unpacked** and select the `/extension` directory inside this repository.
4. Pin the 🤖 Manga Translator AI extension.

---

## 📖 How to Use
1. Ensure the Python Backend Server is running (`python server.py`).
2. Open a Manga Web page (e.g., WeebCentral).
3. Click the Extension icon and select the Source Language of the comic (EN, JA, KO).
4. Start scrolling! The Chrome extension will project a beautiful Glassmorphism shimmer over images currently being processed.

---

## 🔬 Fine-tuning Your Own Masterpiece AI (Phase 6)
Want the AI to translate slang just like your favorite fan-sub group? Use the built-in LLM trainer tailored for low-VRAM CPUs:
1. Open `dataset/manga_vocab.csv` and insert pairs of translations.
2. Run `python train.py`.
3. The server will detect your newly trained weights at `models/my_custom_ai` upon next restart and use it automatically!

### ⚖️ License
Distributed under the MIT License. Feel free to fork, expand, and contribute!
