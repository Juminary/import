# "图谱溯文脉・AI焕非遗" 项目

非物质文化遗产知识图谱与AI融合系统 - 习近平新时代中国特色社会主义思想概论课程实践

## 🎯 项目简介

本项目运用知识图谱和大语言模型技术，构建中国非物质文化遗产智能问答系统，让更多人了解、热爱、传承中华优秀传统文化。

## 🗂️ 项目结构

```
import/
├── app.py                   # Flask Web服务
├── rag_engine.py            # RAG引擎（知识图谱+向量检索）
├── scrape_ich_details.py    # 非遗详情爬取脚本
├── generate_ich_intro.py    # AI生成非遗介绍
├── requirements.txt         # Python依赖
├── ich_national_full_data.csv  # 非遗数据（3778条）
├── import_to_neo4j.cypher   # Neo4j导入脚本
├── templates/
│   └── index.html           # 前端页面
└── static/
    ├── css/style.css        # 样式表
    └── js/main.js           # 前端交互
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置Neo4j
- 安装并启动Neo4j数据库
- 导入非遗数据：在Neo4j Browser中执行 `import_to_neo4j.cypher`

### 3. 配置大模型API
```bash
# 设置通义千问API密钥
export QWEN_API_KEY="your-api-key"

# 或设置Neo4j密码（如果修改过）
export NEO4J_PASSWORD="your-password"
```

### 4. 启动服务
```bash
python app.py
```

访问 http://localhost:5000 即可使用

## ✨ 核心功能

1. **智能问答** - 基于知识图谱+大模型的RAG架构
2. **非遗探索** - 按类别、地区浏览非遗项目
3. **AI诗词生成** - 为非遗项目创作古风诗词
4. **AI故事续写** - 创作非遗传承故事

## 📊 数据说明

- 数据来源：中国非物质文化遗产网 (ihchina.cn)
- 数据规模：3778条国家级非遗记录
- 涵盖类别：民间文学、传统音乐、传统舞蹈、传统戏剧等10大类

## 🔧 技术栈

- **后端**: Python Flask
- **知识图谱**: Neo4j
- **向量检索**: FAISS + Sentence Transformers
- **大语言模型**: 通义千问 API
- **前端**: 原生 HTML/CSS/JavaScript

## 📄 许可证

本项目仅用于课程学习，非遗数据版权归原数据源所有。
