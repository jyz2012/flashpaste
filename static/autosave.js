let autoSaveTimeout;
let lastSavedContent = '';
let lastSavedTitle = '';

function updateShareFormData() {
    const content = document.getElementById('content-textarea').value;
    const title = document.getElementById('content-title').value;
    document.getElementById('share-content').value = content;
    document.getElementById('share-title').value = title;
}

function showAutoSaveStatus(message, isError = false) {
    const status = document.getElementById('auto-save-status');
    status.textContent = message;
    status.style.color = isError ? '#e74c3c' : '#27ae60';
    setTimeout(() => {
        status.textContent = '';
    }, 3000);
}

function autoSave() {
    const content = document.getElementById('content-textarea').value;
    const title = document.getElementById('content-title').value;
    
    // 检查内容是否有变化
    if (content === lastSavedContent && title === lastSavedTitle) {
        return;
    }
    
    // 更新分享表单数据
    updateShareFormData();
    
    // 发送自动保存请求
    fetch('/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `content=${encodeURIComponent(content)}&title=${encodeURIComponent(title)}`
    })
    .then(response => {
        if (response.ok) {
            lastSavedContent = content;
            lastSavedTitle = title;
            showAutoSaveStatus('✓ 已自动保存');
        } else {
            showAutoSaveStatus('✗ 保存失败', true);
        }
    })
    .catch(error => {
        showAutoSaveStatus('✗ 保存失败', true);
    });
}

function scheduleAutoSave() {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(autoSave, 2000); // 2秒后自动保存
}

// 监听内容变化
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('content-textarea');
    const titleInput = document.getElementById('content-title');
    
    // 初始化已保存的内容
    lastSavedContent = textarea.value;
    lastSavedTitle = titleInput.value;
    
    // 监听输入事件
    textarea.addEventListener('input', scheduleAutoSave);
    titleInput.addEventListener('input', scheduleAutoSave);
    
    // 监听内容变化，实时更新分享表单
    textarea.addEventListener('input', updateShareFormData);
    titleInput.addEventListener('input', updateShareFormData);
    
    // 页面离开前保存
    window.addEventListener('beforeunload', function() {
        const content = textarea.value;
        const title = titleInput.value;
        if (content !== lastSavedContent || title !== lastSavedTitle) {
            // 同步保存
            navigator.sendBeacon('/', `content=${encodeURIComponent(content)}&title=${encodeURIComponent(title)}`);
        }
    });
});