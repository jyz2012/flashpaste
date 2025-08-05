// 主题切换功能
(function() {
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    const currentTheme = localStorage.getItem('theme');
    
    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
    }
    
    // 切换主题函数
    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            switchHighlightThemeByDisabling('highlight-theme-dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            switchHighlightThemeByDisabling('highlight-theme-default');
        }
    }
    
    // 监听切换事件
    toggleSwitch.addEventListener('change', switchTheme, false);
});


function switchHighlightThemeByDisabling(themeIdToEnable) {
    const themes = ['highlight-theme-default', 'highlight-theme-dark']; // 列出所有主题的ID
    themes.forEach(id => {
        const link = document.getElementById(id);
        if (link) {
            link.disabled = (id !== themeIdToEnable);
        }
    });
}

// 示例：
// const checkbox = document.getElementById('checkbox');
// checkbox.addEventListener('change', function() {
//     if (this.checked) {
//         document.documentElement.setAttribute('data-theme', 'dark');
//         switchHighlightThemeByDisabling('highlight-theme-dark');
//     } else {
//         document.documentElement.removeAttribute('data-theme');
//         switchHighlightThemeByDisabling('highlight-theme-default');
//     }
// });


function setHighlightTheme(isDark) {
    const lightTheme = document.getElementById('highlight-theme-default');
    const darkTheme = document.getElementById('highlight-theme-dark');
    if (isDark) {
        lightTheme.disabled = true;
        darkTheme.disabled = false;
    } else {
        lightTheme.disabled = false;
        darkTheme.disabled = true;
    }
}

function applyTheme(isDark) {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    setHighlightTheme(isDark);
}

// 页面加载时自动检测
window.addEventListener('DOMContentLoaded', function() {
    const isDark = localStorage.getItem('theme') === 'dark' ||
        (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    applyTheme(isDark);
});

// 主题切换按钮事件里也要调用 applyTheme
toggleSwitch.addEventListener('change', switchTheme, false);
