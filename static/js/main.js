// DOM Elements
document.addEventListener('DOMContentLoaded', function () {
    // Initialize specific components if they exist on loading
    if (document.getElementById('graph-container')) {
        initGraph();
    }

    // Initialize Heritage Overview
    if (document.getElementById('category-grid')) {
        loadCategories();
    }

    // Initialize count-up animation for hero stats
    initCountUp();

    // Highlight active nav item based on scroll position
    const observerOptions = {
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                document.querySelectorAll('.nav-item').forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + id) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);

    document.querySelectorAll('.page-section').forEach(section => {
        observer.observe(section);
    });
});

// ==================== Count-Up Animation ====================
function initCountUp() {
    const counters = document.querySelectorAll('.count-up');

    const observerOptions = {
        threshold: 0.5
    };

    const countObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-target'));
                animateCounter(counter, target);
                countObserver.unobserve(counter); // Only animate once
            }
        });
    }, observerOptions);

    counters.forEach(counter => {
        countObserver.observe(counter);
    });
}

function animateCounter(element, target) {
    const duration = 2000; // 2 seconds
    const step = target / (duration / 16); // ~60fps
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            element.textContent = target.toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString();
        }
    }, 16);
}

// Chat Functionality
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const chatHistory = document.getElementById('chat-history');
    const useRAG = document.getElementById('rag-toggle').checked;

    const query = userInput.value.trim();
    if (!query) return;

    // Display User Message
    addMessage(query, 'user');
    userInput.value = '';

    // Show Loading
    const loadingId = addFunctionMessage('正在思考中...', 'ai');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: query,
                use_ai: useRAG
            })
        });

        const data = await response.json();

        // Remove Loading Message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        // Display AI Response
        if (data.answer) {
            addMessage(data.answer, 'ai');
        } else if (data.error) {
            addMessage('抱歉，出错了：' + data.error, 'ai');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('网络请求失败，请稍后再试。', 'ai');
    }
}

function addMessage(text, type) {
    const chatHistory = document.getElementById('chat-history');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerText = type === 'user' ? '您' : 'AI';

    const content = document.createElement('div');
    content.className = 'content';
    content.innerHTML = text.replace(/\n/g, '<br>'); // Simple Markdown formatting could come here

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content); // Correct order is managed by Flexbox row-reverse for user

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    if (type === 'ai') {
        msgDiv.id = 'msg-' + Date.now();
        return msgDiv.id; // Return ID for potential removal
    }
    return null;
}

function addFunctionMessage(text, type) {
    return addMessage(text, type);
}

// Graph Visualization (ECharts)
let myChart = null;

function initGraph() {
    const dom = document.getElementById('graph-container');
    myChart = echarts.init(dom);

    window.addEventListener('resize', function () {
        myChart.resize();
    });

    // Initial load
    fetchGraphData();
}


async function fetchGraphData(searchQuery = '') {
    myChart.showLoading();
    try {
        const url = searchQuery
            ? `/api/graph/search?q=${encodeURIComponent(searchQuery)}`
            : '/api/graph/init';

        const response = await fetch(url);
        const data = await response.json();

        myChart.hideLoading();

        if (data.nodes && data.nodes.length > 0) {
            const option = {
                tooltip: {},
                legend: [{
                    data: data.categories.map(function (a) {
                        return a.name;
                    })
                }],
                series: [
                    {
                        name: '非遗图谱',
                        type: 'graph',
                        layout: 'force',
                        data: data.nodes,
                        links: data.links,
                        categories: data.categories,
                        roam: true,
                        label: {
                            show: true,
                            position: 'right',
                            formatter: '{b}'
                        },
                        labelLayout: {
                            hideOverlap: true
                        },
                        scaleLimit: {
                            min: 0.4,
                            max: 2
                        },
                        lineStyle: {
                            color: 'source',
                            curveness: 0.3
                        },
                        force: {
                            repulsion: 100,
                            edgeLength: 50,
                            gravity: 0.1
                        }
                    }
                ]
            };
            myChart.setOption(option);
        } else {
            // Handle no data
            console.log('No data found');
        }

    } catch (error) {
        console.error('Graph Error:', error);
        myChart.hideLoading();
    }
}

function searchGraph() {
    const query = document.getElementById('search-input').value;
    fetchGraphData(query);
}


// ==================== Modal Functions ====================

function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function (event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// ==================== 文创生成 ====================
async function generateWenchuang() {
    const project = document.getElementById('wc-project').value.trim();
    const product = document.getElementById('wc-product').value.trim();
    const resultBox = document.getElementById('wc-result');

    if (!project) {
        alert('请输入非遗项目名称');
        return;
    }

    resultBox.innerHTML = '✨ AI正在为您构思创意方案...';

    try {
        const response = await fetch('/api/creative', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: product || '文创产品',
                item_name: project
            })
        });

        const data = await response.json();
        resultBox.innerHTML = data.content ? data.content.replace(/\n/g, '<br>') : '生成失败';
    } catch (e) {
        resultBox.innerHTML = '请求失败，请检查网络连接。';
    }
}

// ==================== 文脉溯源 ====================
async function generateWenmai() {
    const project = document.getElementById('wm-project').value.trim();
    const resultBox = document.getElementById('wm-result');

    if (!project) {
        alert('请输入非遗项目名称');
        return;
    }

    resultBox.innerHTML = '📜 AI正在追溯历史脉络...';

    try {
        const response = await fetch('/api/wenmai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: project })
        });

        const data = await response.json();
        resultBox.innerHTML = data.content ? data.content.replace(/\n/g, '<br>') : '生成失败';
    } catch (e) {
        resultBox.innerHTML = '请求失败，请检查网络连接。';
    }
}

// ==================== 文学创作 ====================
async function generateWenxue() {
    const theme = document.getElementById('wx-theme').value.trim();
    const type = document.getElementById('wx-type').value;
    const resultBox = document.getElementById('wx-result');

    if (!theme) {
        alert('请输入创作主题');
        return;
    }

    resultBox.innerHTML = `✒️ AI正在创作${type}...`;

    try {
        const response = await fetch('/api/wenxue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                theme: theme,
                type: type
            })
        });

        const data = await response.json();
        resultBox.innerHTML = data.content ? data.content.replace(/\n/g, '<br>') : '生成失败';
    } catch (e) {
        resultBox.innerHTML = '请求失败，请检查网络连接。';
    }
}
// ==================== Heritage Overview ====================
async function loadCategories() {
    const grid = document.getElementById('category-grid');
    if (!grid) return;

    try {
        const response = await fetch('/api/categories');
        const data = await response.json();

        if (data.categories) {
            grid.innerHTML = '';
            data.categories.forEach(cat => {
                const card = document.createElement('div');
                card.className = 'category-card';
                card.onclick = () => viewCategory(cat.name);
                card.innerHTML = `
                    <h3>${cat.name}</h3>
                    <div class="count">${cat.count} 个项目</div>
                `;
                grid.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
        grid.innerHTML = '<div class="error">加载失败，请重试</div>';
    }
}

async function viewCategory(categoryName) {
    const grid = document.getElementById('category-grid');
    const viewer = document.getElementById('items-viewer');
    const list = document.getElementById('items-list');
    const title = document.getElementById('current-category-name');

    toggleOverviewMode('viewer');
    title.textContent = categoryName;
    list.innerHTML = '<div class="loading-state">加载项目中...</div>';

    try {
        const response = await fetch(`/api/search?type=category&q=${encodeURIComponent(categoryName)}`);
        const data = await response.json();

        if (data.results) {
            list.innerHTML = '';

            if (data.results.length === 0) {
                list.innerHTML = '<div class="loading-state">暂无项目数据</div>';
                return;
            }

            data.results.forEach(item => {
                const badge = document.createElement('div');
                badge.className = 'item-badge';
                badge.textContent = item['名称'] || item.name;
                list.appendChild(badge);
            });
        }
    } catch (error) {
        console.error('Error loading category items:', error);
        list.innerHTML = '<div class="error">加载失败</div>';
    }
}

function toggleOverviewMode(mode) {
    const grid = document.getElementById('category-grid');
    const viewer = document.getElementById('items-viewer');

    if (mode === 'grid') {
        grid.style.display = 'grid';
        viewer.style.display = 'none';
    } else {
        grid.style.display = 'none';
        viewer.style.display = 'block';
    }
}
