# 文脉智谱

> 图谱溯文脉 · AI焕非遗 —— 非物质文化遗产智能探索平台

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1.svg)](https://neo4j.com/)

## 🎯 项目简介

**文脉智谱**是一个融合知识图谱与大语言模型的非物质文化遗产智能探索平台。项目以"文化自信"为核心理念，运用 Neo4j 知识图谱、FAISS 向量检索与 RAG 技术，构建集**智能问答、可视化探索、AI共创**于一体的数字非遗体验系统。

### ✨ 核心功能

| 模块 | 功能描述 |
|------|----------|
| **览·万象** | 纵览千载非遗，按类别浏览 3778 条国家级非遗项目 |
| **观·图谱** | 以知识图谱可视化非遗间的关联与脉络 |
| **智·问答** | 基于 RAG 技术的智能问答，深度解读非遗文化 |
| **创·新生** | AI 赋诗、文脉溯源、故事续写，人机共创文化新生 |

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Neo4j 5.x
- 通义千问 API 密钥

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 通义千问 API
QWEN_API_KEY=your-api-key

# Neo4j 数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### 3. 导入知识图谱数据

```bash
# 在 Neo4j Browser 中执行
:source import_to_neo4j.cypher
```

### 4. 构建向量索引

```bash
python build_vector_index.py
```

### 5. 启动服务

```bash
python app.py
# 或指定端口
PORT=5001 python app.py
```

访问 http://localhost:5001 开始探索！

---

## 🗂️ 项目结构

```
文脉智谱/
├── app.py                      # Flask Web 服务主入口
├── rag_engine.py               # RAG 引擎（知识图谱 + 向量检索）
├── build_vector_index.py       # FAISS 向量索引构建
├── generate_ich_intro.py       # AI 生成非遗详细介绍
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量配置
│
├── ich_national_full_data.csv  # 非遗原始数据（3778条）
├── ich_ai_introductions.json   # AI 生成的详细介绍
├── import_to_neo4j.cypher      # Neo4j 数据导入脚本
│
├── templates/
│   └── index.html              # 前端主页面
└── static/
    ├── css/style.css           # 国潮风格样式
    ├── js/main.js              # 前端交互逻辑
    └── images/                 # 背景图素材
```

---

## � 数据说明

| 项目 | 数量 |
|------|------|
| 非遗项目总数 | 3,778 条 |
| 传承地区 | 1,846 个 |
| 非遗类别 | 10 大类 |
| AI 详细介绍 | 15 个代表性项目 |

**数据来源**：中国非物质文化遗产网 ([ihchina.cn](https://www.ihchina.cn))

---

## 🔧 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端展示层                          │
│         HTML5 + CSS3 (国潮设计) + JavaScript            │
├─────────────────────────────────────────────────────────┤
│                      Web 服务层                          │
│                    Flask REST API                       │
├─────────────────────────────────────────────────────────┤
│                      智能引擎层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Neo4j 图谱  │  │ FAISS 向量库 │  │ 通义千问 LLM │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**核心技术栈**：
- **后端框架**: Flask
- **知识图谱**: Neo4j
- **向量检索**: FAISS + Sentence Transformers
- **大语言模型**: 通义千问 (Qwen) API
- **可视化**: ECharts

---

## 📄 许可证

本项目为课程实践作品，仅用于学习交流。非遗数据版权归中国非物质文化遗产网所有。

---

<p align="center">
  <b>以图谱织文脉，用智能焕非遗</b><br>
  © 2026 文脉智谱 | 习近平新时代中国特色社会主义思想概论课程实践
</p>
