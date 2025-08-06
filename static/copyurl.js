// 复制分享链接功能
function copyShareUrl() {
    const input = document.getElementById('share-url-input');
    const status = document.getElementById('copy-status');
    
    if (navigator.clipboard && window.isSecureContext) {
        // 使用现代 Clipboard API
        navigator.clipboard.writeText(input.value).then(() => {
            showCopyStatus('✓ 链接已复制到剪贴板');
        }).catch(() => {
            fallbackCopyText(input);
        });
    } else {
        // 降级方案
        fallbackCopyText(input);
    }
}

function fallbackCopyText(input) {
    try {
        input.select();
        input.setSelectionRange(0, 99999); // 移动端兼容
        document.execCommand('copy');
        showCopyStatus('✓ 链接已复制到剪贴板');
    } catch (err) {
        showCopyStatus('✗ 复制失败，请手动复制', true);
    }
}

function showCopyStatus(message, isError = false) {
    const status = document.getElementById('copy-status');
    if (status) {
        status.textContent = message;
        status.style.color = isError ? '#e74c3c' : '#27ae60';
        setTimeout(() => {
            status.textContent = '';
        }, 3000);
    }
}