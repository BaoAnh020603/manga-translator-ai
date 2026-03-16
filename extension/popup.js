document.addEventListener('DOMContentLoaded', () => {
    const toggleSwitch = document.getElementById('toggleSwitch');
    const statusText = document.getElementById('status-text');
    const srcLangSelect = document.getElementById('src-lang');

    // Get current state
    chrome.storage.sync.get(['enabled', 'srcLang'], (data) => {
        const isEnabled = data.enabled !== undefined ? data.enabled : true;
        toggleSwitch.checked = isEnabled;
        updateUI(isEnabled);
        
        if (data.srcLang) {
            srcLangSelect.value = data.srcLang;
        }
    });

    // Listen for toggle
    toggleSwitch.addEventListener('change', (e) => {
        const isEnabled = e.target.checked;
        chrome.storage.sync.set({ enabled: isEnabled }, () => {
            updateUI(isEnabled);
        });
    });

    // Listen for language change
    srcLangSelect.addEventListener('change', (e) => {
        chrome.storage.sync.set({ srcLang: e.target.value });
    });

    function updateUI(isEnabled) {
        if (isEnabled) {
            statusText.innerText = 'Đang tự động quét & dịch';
            statusText.style.color = '#10b981'; // Green
        } else {
            statusText.innerText = 'Đã tạm dừng dịch thuật';
            statusText.style.color = '#f43f5e'; // Red
        }
    }

    // Clear Cache Logic
    const btnClearCache = document.getElementById('btn-clear-cache');
    const cacheStatus = document.getElementById('cache-status');

    btnClearCache.addEventListener('click', async () => {
        try {
            btnClearCache.innerText = "Đang dọn...";
            btnClearCache.disabled = true;
            
            const req = await fetch('http://localhost:8000/clear_cache', { method: 'POST' });
            if (req.ok) {
                cacheStatus.innerText = "Đã dọn dẹp sạch sẽ 🧹";
                cacheStatus.style.color = '#10b981';
            } else {
                throw new Error("API Lỗi");
            }
        } catch (e) {
            cacheStatus.innerText = "Lỗi kết nối Server ❌";
            cacheStatus.style.color = '#f43f5e';
        } finally {
            setTimeout(() => {
                btnClearCache.innerText = "Dọn dẹp";
                btnClearCache.disabled = false;
                cacheStatus.innerText = "Lưu trữ bộ nhớ siêu tốc";
                cacheStatus.style.color = '#94a3b8';
            }, 3000);
        }
    });
});
