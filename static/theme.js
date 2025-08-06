// 立即应用保存的主题，避免闪烁
(function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

// 主题切换功能
document.addEventListener('DOMContentLoaded', () => {
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    
    // 检查本地存储中的主题设置，默认为light
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // 应用主题
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // 更新切换按钮状态
        if (toggleSwitch) {
            toggleSwitch.checked = (theme === 'dark');
        }
        
        // 切换代码高亮主题
        switchHighlightThemeByDisabling(theme === 'dark' ? 'highlight-theme-dark' : 'highlight-theme-default');
    }
    
    // 初始化主题
    applyTheme(currentTheme);
    
    // 切换主题函数
    function switchTheme(e) {
        const newTheme = e.target.checked ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    }
    
    // 监听切换事件
    if (toggleSwitch) {
        toggleSwitch.addEventListener('change', switchTheme, false);
    }
});


function switchHighlightThemeByDisabling(themeIdToEnable) {
    const themes = ['highlight-theme-default', 'highlight-theme-dark'];
    themes.forEach(id => {
        const link = document.getElementById(id);
        if (link) {
            link.disabled = (id !== themeIdToEnable);
        }
    });
}
