#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非遗知识图谱RAG引擎
结合Neo4j知识图谱和向量检索实现智能问答

功能：
1. 知识图谱查询 - 从Neo4j获取结构化信息
2. 向量检索 - 从文本库中检索相关内容
3. 融合生成 - 结合两种检索结果生成回答
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """Neo4j知识图谱查询引擎"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "password"):
        """初始化Neo4j连接"""
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j连接成功")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def query_by_name(self, name: str) -> List[Dict]:
        """根据名称查询非遗项目"""
        query = """
        MATCH (item:Item)
        WHERE item.name CONTAINS $name OR item.名称 CONTAINS $name
        OPTIONAL MATCH (item)-[:属于]->(category:Category)
        OPTIONAL MATCH (item)-[:申报于]->(region:Region)
        OPTIONAL MATCH (item)-[:由保护单位]->(org:Organization)
        RETURN item.name AS 名称,
               category.name AS 类别,
               region.name AS 申报地区,
               org.name AS 保护单位
        LIMIT 10
        """
        with self.driver.session() as session:
            result = session.run(query, name=name)
            return [dict(record) for record in result]
    
    def query_by_category(self, category: str) -> List[Dict]:
        """根据类别查询非遗项目"""
        query = """
        MATCH (c:Category {name: $category})<-[:属于]-(item:Item)
        OPTIONAL MATCH (item)-[:申报于]->(region:Region)
        RETURN item.name AS 名称, region.name AS 申报地区
        LIMIT 20
        """
        with self.driver.session() as session:
            result = session.run(query, category=category)
            return [dict(record) for record in result]
    
    def query_by_region(self, region: str) -> List[Dict]:
        """根据地区查询非遗项目"""
        query = """
        MATCH (r:Region)
        WHERE r.name CONTAINS $region
        MATCH (r)<-[:申报于]-(item:Item)
        OPTIONAL MATCH (item)-[:属于]->(category:Category)
        RETURN item.name AS 名称, category.name AS 类别, r.name AS 申报地区
        LIMIT 20
        """
        with self.driver.session() as session:
            result = session.run(query, region=region)
            return [dict(record) for record in result]
    
    def get_statistics(self) -> Dict:
        """获取知识图谱统计信息"""
        queries = {
            'total_items': "MATCH (i:Item) RETURN count(i) AS count",
            'total_categories': "MATCH (c:Category) RETURN count(c) AS count",
            'total_regions': "MATCH (r:Region) RETURN count(r) AS count",
            'total_orgs': "MATCH (o:Organization) RETURN count(o) AS count",
        }
        
        stats = {}
        with self.driver.session() as session:
            for key, query in queries.items():
                result = session.run(query)
                stats[key] = result.single()['count']
        return stats
    
    def get_category_distribution(self) -> List[Dict]:
        """获取各类别项目分布"""
        query = """
        MATCH (c:Category)<-[:属于]-(item:Item)
        RETURN c.name AS 类别, count(item) AS 数量
        ORDER BY 数量 DESC
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]


class VectorRetriever:
    """向量检索引擎（使用FAISS）"""
    
    def __init__(self, index_path: str = None):
        """初始化向量检索器"""
        self.index = None
        self.documents = []
        self.embeddings_model = None
        
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            
            # 加载中文嵌入模型
            self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("向量模型加载成功")
            
            if index_path and os.path.exists(index_path):
                self._load_index(index_path)
        except ImportError:
            logger.warning("请安装依赖: pip install sentence-transformers faiss-cpu")
    
    def _load_index(self, path: str):
        """加载已有索引"""
        import faiss
        self.index = faiss.read_index(f"{path}/faiss.index")
        with open(f"{path}/documents.json", 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        logger.info(f"加载索引成功，文档数: {len(self.documents)}")
    
    def build_index(self, documents: List[Dict], save_path: str = None):
        """
        构建向量索引
        
        Args:
            documents: 文档列表，每个文档包含 'title' 和 'content'
            save_path: 索引保存路径
        """
        import faiss
        import numpy as np
        
        if not self.embeddings_model:
            logger.error("嵌入模型未加载")
            return
        
        self.documents = documents
        
        # 生成文档向量
        texts = [f"{d.get('title', '')} {d.get('content', '')}" for d in documents]
        embeddings = self.embeddings_model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
        faiss.normalize_L2(embeddings)  # 归一化
        self.index.add(embeddings)
        
        logger.info(f"索引构建完成，文档数: {len(documents)}")
        
        # 保存索引
        if save_path:
            os.makedirs(save_path, exist_ok=True)
            faiss.write_index(self.index, f"{save_path}/faiss.index")
            with open(f"{save_path}/documents.json", 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            logger.info(f"索引已保存至 {save_path}")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回前k个结果
            
        Returns:
            (文档, 相似度分数) 列表
        """
        import faiss
        import numpy as np
        
        if not self.index or not self.embeddings_model:
            return []
        
        # 生成查询向量
        query_embedding = self.embeddings_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # 搜索
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results


class ICHRAGEngine:
    """
    非遗智能问答RAG引擎
    融合知识图谱和向量检索
    """
    
    def __init__(self, neo4j_config: Dict = None, vector_index_path: str = None):
        """初始化RAG引擎"""
        # 知识图谱
        if neo4j_config:
            self.kg = Neo4jKnowledgeGraph(**neo4j_config)
        else:
            self.kg = Neo4jKnowledgeGraph()
        
        # 向量检索
        self.retriever = VectorRetriever(vector_index_path)
        
        # 类别关键词映射
        self.category_keywords = {
            '民间文学': ['传说', '故事', '歌谣', '史诗', '神话', '谚语', '童谣'],
            '传统音乐': ['音乐', '民歌', '号子', '曲艺', '器乐', '古琴', '唢呐'],
            '传统舞蹈': ['舞蹈', '龙舞', '狮舞', '秧歌', '傩舞', '花鼓'],
            '传统戏剧': ['戏剧', '京剧', '昆曲', '越剧', '皮影戏', '木偶'],
            '曲艺': ['曲艺', '相声', '评书', '大鼓', '快板'],
            '传统美术': ['美术', '剪纸', '年画', '刺绣', '雕刻', '泥塑'],
            '传统技艺': ['技艺', '织造', '酿造', '制茶', '制瓷', '铸造'],
            '传统医药': ['医药', '中医', '针灸', '推拿', '药物'],
            '民俗': ['民俗', '节日', '习俗', '祭祀', '婚俗']
        }
    
    def _extract_query_intent(self, query: str) -> Dict:
        """
        解析查询意图
        
        Returns:
            {'type': 'name/category/region', 'keyword': '...'}
        """
        # 检测类别查询
        for category, keywords in self.category_keywords.items():
            if category in query:
                return {'type': 'category', 'keyword': category}
            for kw in keywords:
                if kw in query:
                    return {'type': 'category', 'keyword': category}
        
        # 检测地区查询
        provinces = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
                    '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
                    '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
                    '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']
        
        for province in provinces:
            if province in query:
                return {'type': 'region', 'keyword': province}
        
        # 默认按名称查询
        return {'type': 'name', 'keyword': query}
    
    def retrieve(self, query: str) -> Dict:
        """
        混合检索
        
        Args:
            query: 用户查询
            
        Returns:
            检索结果
        """
        intent = self._extract_query_intent(query)
        logger.info(f"查询意图: {intent}")
        
        # 知识图谱检索
        kg_results = []
        if intent['type'] == 'category':
            kg_results = self.kg.query_by_category(intent['keyword'])
        elif intent['type'] == 'region':
            kg_results = self.kg.query_by_region(intent['keyword'])
        else:
            kg_results = self.kg.query_by_name(intent['keyword'])
        
        # 向量检索
        vector_results = self.retriever.search(query, top_k=3)
        
        return {
            'intent': intent,
            'kg_results': kg_results,
            'vector_results': [(doc, score) for doc, score in vector_results]
        }
    
    def generate_context(self, retrieval: Dict) -> str:
        """将检索结果转换为上下文文本"""
        context_parts = []
        
        # 知识图谱结果
        if retrieval['kg_results']:
            context_parts.append("【知识图谱信息】")
            for item in retrieval['kg_results'][:5]:
                context_parts.append(
                    f"- {item.get('名称', '')}: 类别={item.get('类别', '未知')}，"
                    f"地区={item.get('申报地区', '未知')}"
                )
        
        # 向量检索结果
        if retrieval['vector_results']:
            context_parts.append("\n【相关文档】")
            for doc, score in retrieval['vector_results']:
                if score > 0.5:  # 相似度阈值
                    title = doc.get('title', '')
                    content = doc.get('content', '')[:500]
                    context_parts.append(f"- {title}: {content}...")
        
        return '\n'.join(context_parts)
    
    def answer(self, query: str, llm_func: callable = None) -> Dict:
        """
        完整的问答流程
        
        Args:
            query: 用户问题
            llm_func: 大模型调用函数，接收(prompt) -> response
            
        Returns:
            {
                'answer': '回答文本',
                'sources': '来源信息',
                'retrieval': 检索结果
            }
        """
        # 检索
        retrieval = self.retrieve(query)
        context = self.generate_context(retrieval)
        
        # 如果没有大模型，返回结构化结果
        if not llm_func:
            if not retrieval['kg_results'] and not retrieval['vector_results']:
                return {
                    'answer': f"抱歉，未找到与'{query}'相关的非遗信息。",
                    'sources': [],
                    'retrieval': retrieval
                }
            
            # 简单拼接回答
            answer_parts = []
            if retrieval['kg_results']:
                answer_parts.append(f"找到 {len(retrieval['kg_results'])} 个相关非遗项目：")
                for item in retrieval['kg_results'][:5]:
                    answer_parts.append(f"• **{item.get('名称', '')}** ({item.get('类别', '')})")
            
            return {
                'answer': '\n'.join(answer_parts),
                'sources': [item.get('名称', '') for item in retrieval['kg_results'][:5]],
                'retrieval': retrieval
            }
        
        # 使用大模型生成回答
        prompt = f"""你是一位中国非物质文化遗产专家，请根据以下参考信息回答用户问题。

参考信息：
{context}

用户问题：{query}

请给出准确、专业的回答，如果参考信息不足，请诚实说明。"""
        
        try:
            answer = llm_func(prompt)
            return {
                'answer': answer,
                'sources': [item.get('名称', '') for item in retrieval['kg_results'][:5]],
                'retrieval': retrieval
            }
        except Exception as e:
            logger.error(f"大模型调用失败: {e}")
            return {
                'answer': "抱歉，生成回答时出现错误。",
                'sources': [],
                'retrieval': retrieval
            }


# ===================== 测试代码 =====================
if __name__ == '__main__':
    # 测试知识图谱连接
    print("测试Neo4j连接...")
    kg = Neo4jKnowledgeGraph()
    
    if kg.driver:
        print("\n统计信息:")
        stats = kg.get_statistics()
        print(f"  总项目数: {stats['total_items']}")
        print(f"  类别数: {stats['total_categories']}")
        print(f"  地区数: {stats['total_regions']}")
        
        print("\n测试查询 - 苗族古歌:")
        results = kg.query_by_name("苗族古歌")
        for r in results:
            print(f"  {r}")
        
        print("\n类别分布:")
        dist = kg.get_category_distribution()
        for d in dist[:5]:
            print(f"  {d['类别']}: {d['数量']}")
        
        kg.close()
    else:
        print("Neo4j未连接，跳过测试")
