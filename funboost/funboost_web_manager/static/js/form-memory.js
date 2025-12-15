// 表单记忆功能 - 保存和恢复iframe内的表单值
(function() {
    // 简化版 - 只保存基本输入值
    function saveFormInputs() {
        const iframe = document.getElementById('content');
        if (!iframe || !iframe.contentWindow) return;
        
        const pageId = iframe.src.split('/').pop().replace('.html', '');
        
        try {
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const formData = {};
            
            // 保存所有输入元素值
            const inputs = iframeDoc.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                const inputId = input.id || input.name || input.getAttribute('placeholder');
                if (inputId) {
                    formData[inputId] = input.value;
                }
            });
            
            // 特殊处理下拉框的选中文本
            const selects = iframeDoc.querySelectorAll('select');
            selects.forEach(select => {
                const inputId = select.id || select.name;
                if (inputId && select.selectedIndex >= 0 && select.options[select.selectedIndex]) {
                    formData[`${inputId}_text`] = select.options[select.selectedIndex].text;
                }
            });
            
            localStorage.setItem(`funboost_form_${pageId}`, JSON.stringify(formData));
        } catch (e) {
            console.error("保存表单数据失败:", e);
        }
    }

    // 简化版 - 只恢复基本输入值
    function restoreFormInputs() {
        setTimeout(() => {
            const iframe = document.getElementById('content');
            if (!iframe || !iframe.contentWindow) return;
            
            const pageId = iframe.src.split('/').pop().replace('.html', '');
            const savedData = localStorage.getItem(`funboost_form_${pageId}`);
            
            if (savedData) {
                try {
                    const formData = JSON.parse(savedData);
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    
                    // 恢复所有基本输入元素的值
                    Object.keys(formData).forEach(inputId => {
                        if (inputId.endsWith('_text')) return;
                        
                        const input = iframeDoc.getElementById(inputId) || 
                                  iframeDoc.querySelector(`[name="${inputId}"]`) || 
                                  iframeDoc.querySelector(`[placeholder="${inputId}"]`);
                        
                        if (input) {
                            input.value = formData[inputId];
                            
                            // 触发change事件
                            const event = new Event('change', { bubbles: true });
                            input.dispatchEvent(event);
                        }
                    });
                } catch (e) {
                    console.error("恢复表单数据失败:", e);
                }
            }
        }, 500);
    }

    // 当DOM加载完成时初始化事件监听
    document.addEventListener('DOMContentLoaded', function() {
        // 监听iframe加载完成事件
        const contentFrame = document.getElementById('content');
        if (contentFrame) {
            contentFrame.addEventListener('load', restoreFormInputs);
        }

        // 在页面切换前保存
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', saveFormInputs);
        });

        // 页面离开前保存
        window.addEventListener('beforeunload', saveFormInputs);
    });
})(); 