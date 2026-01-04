/**
 * 图谱溯文脉 · AI焕非遗 - 前端交互脚本
 * 中国非物质文化遗产智能问答系统
 */

// API基础URL
const API_BASE = '';

// ===== 工具函数 =====
function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return document.querySelectorAll(selector);
}

function createElement(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.firstChild;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== 页面初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initStats();
    initChat();
    initExplore();
    initCreative();
    initNavigation();
});

// ===== 导航 =====
function initNavigation() {
    const navLinks = $$('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    // 滚动监听
    window.addEventListener('scroll', () => {
        const sections = $$('section[id]');
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (window.scrollY >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// ===== 统计数据 =====
async function initStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (response.ok) {
            const data = await response.json();
            animateNumber($('#stat-projects'), data.total_projects);
            animateNumber($('#stat-categories'), data.total_categories);
            animateNumber($('#stat-regions'), data.total_regions);
        }
    } catch (error) {
        console.warn('获取统计数据失败:', error);
        // 使用默认值
        $('#stat-projects').textContent = '3778';
        $('#stat-categories').textContent = '10';
        $('#stat-regions').textContent = '1557';
    }
}

function animateNumber(element, target) {
    const duration = 1500;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 缓动函数
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.round(start + (target - start) * easeOutQuart);

        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ===== 智能问答 =====
function initChat() {
    const chatMessages = $('#chat-messages');
    const chatInput = $('#chat-input');
    const sendBtn = $('#send-btn');
    const quickBtns = $$('.quick-btn');

    // 发送消息
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        const useAI = $('#use-ai').checked;

        // 添加用户消息
        addMessage(message, 'user');
        chatInput.value = '';
        sendBtn.disabled = true;

        // 添加加载指示
        const loadingId = addLoadingMessage();

        try {
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message, use_ai: useAI })
            });

            removeLoadingMessage(loadingId);

            if (response.ok) {
                const data = await response.json();
                addMessage(data.answer, 'assistant', data.sources);
            } else {
                const error = await response.json();
                addMessage(`抱歉，处理请求时出现错误：${error.error || '未知错误'}`, 'assistant');
            }
        } catch (error) {
            removeLoadingMessage(loadingId);
            addMessage('抱歉，网络连接失败。请检查服务是否正常运行。\n\n提示：请先启动Flask服务 (python app.py)', 'assistant');
        }

        sendBtn.disabled = false;
    }

    function addMessage(content, type, sources = []) {
        const avatar = type === 'user' ? '👤' : '🎭';
        const sourceHtml = sources.length > 0
            ? `<p class="message-sources"><small>📚 参考来源: ${sources.join('、')}</small></p>`
            : '';

        // 处理Markdown格式的内容
        const formattedContent = formatContent(content);

        const messageHtml = `
            <div class="message ${type}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    ${formattedContent}
                    ${sourceHtml}
                </div>
            </div>
        `;

        chatMessages.appendChild(createElement(messageHtml));
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatContent(content) {
        // 简单的Markdown处理
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/^• /gm, '<li>')
            .split('<br>').map(line => `<p>${line}</p>`).join('');
    }

    function addLoadingMessage() {
        const id = 'loading-' + Date.now();
        const loadingHtml = `
            <div class="message assistant" id="${id}">
                <div class="message-avatar">🎭</div>
                <div class="message-content">
                    <div class="loading">
                        <span></span><span></span><span></span>
                    </div>
                    正在思考中...
                </div>
            </div>
        `;
        chatMessages.appendChild(createElement(loadingHtml));
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeLoadingMessage(id) {
        const loading = $(`#${id}`);
        if (loading) loading.remove();
    }

    // 事件绑定
    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    quickBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.question;
            sendMessage();
        });
    });
}

// ===== 非遗探索 =====
function initExplore() {
    const searchInput = $('#search-input');
    const searchType = $('#search-type');
    const searchBtn = $('#search-btn');
    const categoriesGrid = $('#categories-grid');
    const searchResults = $('#search-results');

    // 类别图标映射
    const categoryIcons = {
        '民间文学': '📚',
        '传统音乐': '🎵',
        '传统舞蹈': '💃',
        '传统戏剧': '🎭',
        '曲艺': '🪪',
        '传统体育、游艺与杂技': '🤸',
        '传统美术': '🎨',
        '传统技艺': '🔧',
        '传统医药': '💊',
        '民俗': '🎊'
    };

    // 加载类别
    async function loadCategories() {
        try {
            const response = await fetch(`${API_BASE}/api/categories`);
            if (response.ok) {
                const data = await response.json();
                renderCategories(data.categories);
            }
        } catch (error) {
            console.warn('加载类别失败:', error);
            // 使用默认类别
            const defaultCategories = [
                { name: '民间文学', count: 252 },
                { name: '传统音乐', count: 682 },
                { name: '传统舞蹈', count: 309 },
                { name: '传统戏剧', count: 165 },
                { name: '曲艺', count: 145 },
                { name: '传统体育、游艺与杂技', count: 140 },
                { name: '传统美术', count: 393 },
                { name: '传统技艺', count: 629 },
                { name: '传统医药', count: 182 },
                { name: '民俗', count: 464 }
            ];
            renderCategories(defaultCategories);
        }
    }

    function renderCategories(categories) {
        categoriesGrid.innerHTML = '';

        categories.forEach(cat => {
            const icon = categoryIcons[cat.name] || '📌';
            const cardHtml = `
                <div class="category-card" data-category="${cat.name}">
                    <div class="category-icon">${icon}</div>
                    <div class="category-name">${cat.name}</div>
                    <div class="category-count">${cat.count} 个项目</div>
                </div>
            `;
            categoriesGrid.appendChild(createElement(cardHtml));
        });

        // 绑定点击事件
        $$('.category-card').forEach(card => {
            card.addEventListener('click', () => {
                searchInput.value = card.dataset.category;
                searchType.value = 'category';
                search();
            });
        });
    }

    // 搜索
    async function search() {
        const query = searchInput.value.trim();
        if (!query) {
            searchResults.innerHTML = '<p style="color: var(--gray-500); text-align: center;">请输入搜索关键词</p>';
            return;
        }

        searchResults.innerHTML = '<p style="text-align: center;"><div class="loading"><span></span><span></span><span></span></div> 搜索中...</p>';

        try {
            const response = await fetch(
                `${API_BASE}/api/search?q=${encodeURIComponent(query)}&type=${searchType.value}`
            );

            if (response.ok) {
                const data = await response.json();
                renderSearchResults(data);
            } else {
                searchResults.innerHTML = '<p style="color: var(--primary); text-align: center;">搜索失败，请稍后重试</p>';
            }
        } catch (error) {
            searchResults.innerHTML = '<p style="color: var(--primary); text-align: center;">网络连接失败，请确保服务已启动</p>';
        }
    }

    function renderSearchResults(data) {
        if (!data.results || data.results.length === 0) {
            searchResults.innerHTML = `<p style="text-align: center; color: var(--gray-500);">未找到与"${escapeHtml(data.query)}"相关的非遗项目</p>`;
            return;
        }

        let html = `<p style="margin-bottom: 16px; color: var(--gray-700);">找到 <strong>${data.count}</strong> 个相关项目：</p>`;

        data.results.forEach(item => {
            html += `
                <div class="result-item">
                    <div>
                        <div class="result-name">${escapeHtml(item.名称 || item.name || '')}</div>
                        <div class="result-meta">
                            ${item.类别 ? `<span>📂 ${escapeHtml(item.类别)}</span>` : ''}
                            ${item.申报地区 ? `<span style="margin-left: 16px;">📍 ${escapeHtml(item.申报地区)}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        searchResults.innerHTML = html;
    }

    // 事件绑定
    searchBtn.addEventListener('click', search);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') search();
    });

    // 初始化加载类别
    loadCategories();
}

// ===== AI创意 =====
function initCreative() {
    const poemInput = $('#poem-input');
    const poemBtn = $('#poem-btn');
    const poemResult = $('#poem-result');

    const storyInput = $('#story-input');
    const storyBtn = $('#story-btn');
    const storyResult = $('#story-result');

    // 生成诗词
    async function generatePoem() {
        const projectName = poemInput.value.trim();
        if (!projectName) {
            poemResult.innerHTML = '<span style="color: var(--primary);">请输入非遗项目名称</span>';
            return;
        }

        poemBtn.disabled = true;
        poemResult.innerHTML = '<div class="loading"><span></span><span></span><span></span></div> 正在生成诗词...';

        try {
            const response = await fetch(`${API_BASE}/api/generate-poem`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_name: projectName })
            });

            if (response.ok) {
                const data = await response.json();
                poemResult.innerHTML = `<strong>《${escapeHtml(projectName)}》</strong><br><br>${escapeHtml(data.poem)}`;
            } else {
                poemResult.innerHTML = '<span style="color: var(--primary);">生成失败，请稍后重试</span>';
            }
        } catch (error) {
            poemResult.innerHTML = '<span style="color: var(--primary);">网络连接失败，请确保服务已启动</span>';
        }

        poemBtn.disabled = false;
    }

    // 生成故事
    async function generateStory() {
        const projectName = storyInput.value.trim();
        if (!projectName) {
            storyResult.innerHTML = '<span style="color: var(--primary);">请输入非遗项目名称</span>';
            return;
        }

        storyBtn.disabled = true;
        storyResult.innerHTML = '<div class="loading"><span></span><span></span><span></span></div> 正在创作故事...';

        try {
            const response = await fetch(`${API_BASE}/api/generate-story`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_name: projectName })
            });

            if (response.ok) {
                const data = await response.json();
                storyResult.innerHTML = escapeHtml(data.story);
            } else {
                storyResult.innerHTML = '<span style="color: var(--primary);">生成失败，请稍后重试</span>';
            }
        } catch (error) {
            storyResult.innerHTML = '<span style="color: var(--primary);">网络连接失败，请确保服务已启动</span>';
        }

        storyBtn.disabled = false;
    }

    // 事件绑定
    poemBtn.addEventListener('click', generatePoem);
    storyBtn.addEventListener('click', generateStory);

    poemInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') generatePoem();
    });

    storyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') generateStory();
    });
}
