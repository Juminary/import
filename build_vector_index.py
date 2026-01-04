#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建非遗项目向量索引
将JSON格式的非遗介绍转换为FAISS向量索引
"""

import json
import os
from rag_engine import VectorRetriever

def build_vector_index():
    """构建向量索引"""
    
    # 加载非遗介绍数据
    json_file = 'ich_ai_introductions.json'
    if not os.path.exists(json_file):
        print(f"❌ 未找到数据文件: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        projects = json.load(f)
    
    print(f"📚 加载了 {len(projects)} 个非遗项目")
    
    # 转换为文档格式
    documents = []
    for proj in projects:
        doc = {
            'title': f"{proj['项目名称']} - {proj['类别']}",
            'content': f"类别：{proj['类别']}\n申报地区：{proj['申报地区']}\n保护单位：{proj['保护单位']}\n\n{proj['详细介绍']}",
            'metadata': {
                '名称': proj['项目名称'],
                '类别': proj['类别'],
                '地区': proj['申报地区']
            }
        }
        documents.append(doc)
    
    # 构建向量索引
    print("🔨 开始构建向量索引...")
    retriever = VectorRetriever()
    
    index_path = 'vector_index'
    retriever.build_index(documents, save_path=index_path)
    
    print(f"✅ 向量索引已保存至 {index_path}/")
    print("\n现在可以在 app.py 中使用向量检索功能了！")

if __name__ == '__main__':
    build_vector_index()
