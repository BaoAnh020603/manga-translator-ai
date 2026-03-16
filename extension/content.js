// This script runs on WeebCentral pages

const WS_URL = "ws://localhost:8000/ws/translate";
let socket = null;
let isConnected = false;
let pendingImages = [];

function connectWebSocket() {
    socket = new WebSocket(WS_URL);
    
    socket.onopen = () => {
        console.log("[Manga Translator] WebSocket connected");
        isConnected = true;
        // Process any queued images
        pendingImages.forEach(imgUrl => {
            socket.send(JSON.stringify({ image_url: imgUrl }));
        });
        pendingImages = [];
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const { image_url, status, message, translated_image_base64 } = data;
        
        const imgElement = document.querySelector(`img[src="${image_url}"]`);
        if (!imgElement) return;

        let overlay = document.getElementById(`overlay-${image_url}`);
        if (!overlay && status !== "done" && status !== "error") {
            overlay = createOverlay(imgElement, image_url);
        }

        if (status === "done") {
            imgElement.src = translated_image_base64;
            imgElement.dataset.translated = "true";
            imgElement.style.filter = "none";
            if (overlay) {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.remove(), 300);
            }
        } else if (status === "error") {
            imgElement.dataset.translating = "error";
            imgElement.style.filter = "none";
            if (overlay) {
                overlay.querySelector('.progress-text').innerText = "❌ Lỗi dịch thuật";
                overlay.querySelector('.spinner').style.display = 'none';
            }
        } else {
            // Update progress text
            if (overlay) {
                const textElem = overlay.querySelector('.progress-text');
                if (textElem) textElem.innerText = message;
                
                // Update progress bar
                const barElem = overlay.querySelector('.progress-fill');
                if (barElem) {
                    let pct = "0%";
                    if (status === "downloading") pct = "20%";
                    if (status === "detecting") pct = "40%";
                    if (status === "translating") pct = "60%";
                    if (status === "inpainting") pct = "80%";
                    if (status === "typesetting") pct = "95%";
                    barElem.style.width = pct;
                }
            }
        }
    };

    socket.onclose = () => {
        console.log("[Manga Translator] WebSocket disconnected. Reconnecting in 3s...");
        isConnected = false;
        setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error("[Manga Translator] WebSocket error:", error);
    };
}

// Inject styling for overlays directly
const style = document.createElement('style');
style.textContent = `
    .manga-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        z-index: 9999;
        font-family: 'Inter', sans-serif;
        opacity: 1;
        transition: opacity 0.3s ease;
        border-radius: 8px;
    }
    .manga-overlay-box {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        backdrop-filter: blur(12px);
    }
    .manga-spinner {
        width: 32px;
        height: 32px;
        border: 4px solid rgba(255, 255, 255, 0.2);
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: manga-spin 1s linear infinite;
    }
    @keyframes manga-spin {
        to { transform: rotate(360deg); }
    }
    .manga-progress-text {
        font-weight: 500;
        font-size: 15px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        letter-spacing: 0.5px;
    }
    .manga-progress-bar {
        width: 160px;
        height: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.1);
        position: relative;
    }
    .manga-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
        width: 0%;
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    /* Shimmer Effect */
    .manga-progress-fill::after {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: shimmer 1.5s infinite;
        transform: translateX(-100%);
    }
    @keyframes shimmer {
        100% { transform: translateX(100%); }
    }
`;
document.head.appendChild(style);

function createOverlay(imgElement, imageUrl) {
    const parent = imgElement.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
    }
    
    // Smooth image transition
    imgElement.style.transition = 'filter 0.3s ease';

    const overlay = document.createElement('div');
    overlay.className = 'manga-overlay';
    overlay.id = `overlay-${imageUrl}`;

    const box = document.createElement('div');
    box.className = 'manga-overlay-box';

    const spinner = document.createElement('div');
    spinner.className = 'manga-spinner spinner';

    const text = document.createElement('div');
    text.className = 'manga-progress-text progress-text';
    text.innerText = 'Đang xếp hàng...';

    const barContainer = document.createElement('div');
    barContainer.className = 'manga-progress-bar';
    
    const barFill = document.createElement('div');
    barFill.className = 'manga-progress-fill progress-fill';

    barContainer.appendChild(barFill);
    box.appendChild(spinner);
    box.appendChild(text);
    box.appendChild(barContainer);
    overlay.appendChild(box);
    
    if (parent) {
        parent.appendChild(overlay);
    }
    return overlay;
}

// Check extension state before translating
let extensionEnabled = true;
let srcLang = 'en';

// Get initial state
chrome.storage.sync.get(['enabled', 'srcLang'], (data) => {
    if (data.enabled !== undefined) {
        extensionEnabled = data.enabled;
    }
    if (data.srcLang !== undefined) {
        srcLang = data.srcLang;
    }
    if (extensionEnabled) {
        connectWebSocket();
        setTimeout(scanAndTranslate, 1000);
    }
});

// Listen for popup toggles
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'sync') {
        if (changes.enabled !== undefined) {
            extensionEnabled = changes.enabled.newValue;
            if (extensionEnabled) {
                if (!isConnected) connectWebSocket();
                scanAndTranslate();
            }
        }
        if (changes.srcLang !== undefined) {
            srcLang = changes.srcLang.newValue;
        }
    }
});

async function translateImage(imgElement) {
    if (!extensionEnabled) return;
    if (imgElement.dataset.translating || imgElement.dataset.translated) return;
    if (imgElement.width < 300 || imgElement.height < 300) return; // Ignore small icons

    imgElement.dataset.translating = "true";
    console.log(`[Manga Translator] Queueing image: ${imgElement.src}`);

    // Create wrapper div if needed so absolute overlay fits the image perfectly
    const parent = imgElement.parentElement;
    if (parent && parent.childNodes.length > 1) {
        // Find if already wrapped
        if (!parent.classList.contains("manga-img-wrapper")) {
            const wrapper = document.createElement('div');
            wrapper.className = "manga-img-wrapper";
            wrapper.style.position = "relative";
            wrapper.style.display = "inline-block";
            // Replace img with wrapper containing img
            parent.insertBefore(wrapper, imgElement);
            wrapper.appendChild(imgElement);
        }
    }

    if (isConnected) {
        socket.send(JSON.stringify({ image_url: imgElement.src, src_lang: srcLang }));
    } else {
        pendingImages.push(imgElement.src);
        if (!socket) connectWebSocket();
    }
}

// IntersectionObserver to lazily translate images when they are about to enter the viewport (1000px margin)
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            // Stop observing once we queue it for translation
            observer.unobserve(img);
            if (img.complete) {
                translateImage(img);
            } else {
                img.addEventListener('load', () => translateImage(img));
            }
        }
    });
}, {
    rootMargin: '1000px 0px 1000px 0px', // Start translating when image is 1000px away from viewport
    threshold: 0.01
});

// Find all manga images and observe them
function scanAndTranslate() {
    if (!extensionEnabled) return;
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        imageObserver.observe(img);
    });
}

// Setup MutationObserver to watch for new images loaded dynamically
const observer = new MutationObserver((mutations) => {
    if (!extensionEnabled) return;
    mutations.forEach((mutation) => {
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {
            for (let i = 0; i < mutation.addedNodes.length; i++) {
                const node = mutation.addedNodes[i];
                if (node.tagName === 'IMG') {
                    imageObserver.observe(node);
                } else if (node.querySelectorAll) {
                    const imgs = node.querySelectorAll('img');
                    imgs.forEach(img => {
                        imageObserver.observe(img);
                    });
                }
            }
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});
