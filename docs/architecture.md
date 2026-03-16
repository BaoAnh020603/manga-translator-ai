# Manga Translator AI - Architecture Diagrams

This document illustrates the exact architecture, data flows, and use cases of the **Manga Translator AI** project. All diagrams reflect the 100% current and real Python/JavaScript codebase implementations.

---

## 1. System Architecture Diagram

This macro-level diagram shows the relationship between the Browser Extension and the Python Backend Server.

```mermaid
graph TD
    classDef frontend fill:#3b82f6,stroke:#1e40af,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef model fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef storage fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff

    subgraph "Chrome Extension (Frontend)"
        P[Popup UI<br>HTML/CSS/JS]:::frontend
        CS[Content Script<br>Smart Scroll Observer]:::frontend
        CS -->|WebSocket: image_url, src_lang| S
        P -.->|Sync Settings: Enabled, Language| CS
    end

    subgraph "FastAPI Server (Backend Localhost:8000)"
        S[WebSocket Router<br>server.py]:::backend
        CacheM[Cache Manager<br>cache.py]:::backend
        AIO[AIOHTTP Image Downloader]:::backend
        Sem[Semaphore Queue<br>Anti-Lag System]:::backend
        
        S --> CacheM
        CacheM -- Cache Miss --> AIO
        AIO --> Sem
        
        subgraph "AI Processing Pipeline"
            Det[TextDetector<br>EasyOCR: EN/JA/KO]:::model
            Tra[TextTranslator<br>NLLB-200 2.4GB]:::model
            Inp[Inpainter<br>Otsu Threshold Masking]:::model
            Typ[Typesetter<br>Pillow + Stroke Outline]:::model
            
            Sem --> Det
            Det --> Tra
            Tra --> Inp
            Inp --> Typ
        end
        
        Typ -->|Base64 Image| S
        CacheM -- Cache Hit --> S
    end
    
    subgraph "Storage"
        IC[(Image Cache <br>.cache/images)]:::storage
        TC[(Text Cache <br>.cache/text)]:::storage
        CacheM <--> IC
        CacheM <--> TC
        Tra <--> TC
    end
```

---

## 2. Sequence Diagram: Data Pipeline Workflow

This sequence diagram depicts the detailed chronological workflow of a single image translation request triggered by the user scrolling the web page.

```mermaid
sequenceDiagram
    participant User
    participant Browser as Content Script
    participant WS as FastAPI WebSocket
    participant Cache as Cache Manager
    participant DL as AIOHTTP Downloader
    participant OCR as EasyOCR Detector
    participant NLP as NLLB-200 Translator
    participant CV as OpenCV Inpainter
    participant PIL as Pillow Typesetter

    User->>Browser: Scrolls to new Manga Image
    Browser->>WS: JSON {image_url, src_lang}
    
    WS->>Cache: check_image(url)
    alt Cache Hit
        Cache-->>WS: Return Cached Base64 Image
        WS-->>Browser: JSON {status: done, translated_image_base64}
    else Cache Miss
        WS->>Browser: JSON {status: downloading}
        WS->>DL: async_download(url)
        DL-->>WS: temp_input_path
        
        Note over WS, NLP: Enters Global Semaphore Queue (1 Process Limit)
        WS->>Browser: JSON {status: detecting}
        WS->>OCR: detect(temp_input_path, src_lang)
        OCR-->>WS: List[BoundingBox, SourceText]
        
        WS->>Browser: JSON {status: translating}
        WS->>Cache: Check translation cache
        WS->>NLP: translate_batch(Uncached_Sentences, src_lang)
        NLP-->>WS: List[TranslatedText]
        WS->>Cache: Save new translations
        
        WS->>Browser: JSON {status: inpainting}
        WS->>CV: cv2.adaptiveThreshold() + cv2.inpaint()
        Note right of CV: Generates Smart Mask preserving Background Art
        CV-->>WS: temp_inpainted_path
        
        WS->>Browser: JSON {status: typesetting}
        WS->>PIL: draw_text with text_wrap & stroke_width
        PIL-->>WS: temp_output_path
        
        WS->>Cache: Save final Base64 image
        WS-->>Browser: JSON {status: done, translated_image_base64}
    end
    
    Browser->>User: Renders Vietnamese Manga Image via DOM Replacement
```

---

## 3. Use Case Diagram

This diagram maps out the core user actions across the Extension and the Backend.

```mermaid
graph LR
    User([User / Reader])
    Dev([Developer / NLP Engineer])
    
    subgraph "Chrome Extension UI"
        Tog(Toggle Auto-Translate)
        Lang(Select Source Language<br>EN, JA, KO)
        Clear(Clear Image & Text Cache)
    end
    
    subgraph "Web Page (Content Script)"
        Scroll(Scroll Page)
        View(View Translating Progress)
        Read(Read Vietnamese Manga)
    end
    
    subgraph "Backend / CLI"
        Run(Start FastAPI Server)
        Train(Run train.py Fine-Tuning)
        CSV(Input Translation Pairs dataset)
    end

    %% User Interactions
    User --> Tog
    User --> Lang
    User --> Clear
    User --> Scroll
    User --> View
    User --> Read
    
    %% Dev Interactions
    Dev --> Run
    Dev --> Train
    Dev --> CSV
    
    %% Logic ties
    Scroll -.->|Triggers| View
```

---

## Technical Highlights

The diagrams above strictly reflect the real architecture found in this repository. Specifically:
- **WebSocket (`server.py`)**: Uses `asyncio.Semaphore(1)` to prevent RAM exhaustion on low-end CPUs while supporting asynchronous background downloads.
- **Smart Masking (`pipeline/inpaint.py`)**: Demonstrates the usage of `cv2.adaptiveThreshold` + `cv2.bitwise_and` combined with `cv2.INPAINT_TELEA`.
- **Text Typesetting (`pipeline/typesetter.py`)**: Wraps text boundaries and uses `stroke_width` and `stroke_fill` to ensure visibility.
- **Offline ML (`pipeline/detector.py` & `pipeline/translator.py`)**: Showcases `EasyOCR` lazy loading and `transformers` offline model loading of `nllb-200-distilled-600M` using `torch.no_grad()`.
