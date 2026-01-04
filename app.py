#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非遗AI智能问答 - Flask Web服务
"图谱溯文脉・AI焕非遗"

API接口：
- GET  /api/health        - 健康检查
- GET  /api/stats         - 知识图谱统计
- POST /api/chat          - 智能问答
- GET  /api/search        - 搜索非遗项目
- GET  /api/categories    - 获取类别分布
- GET  /api/project/<name> - 获取项目详情
"""

import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import logging

from rag_engine import ICHRAGEngine, Neo4jKnowledgeGraph

# 加载.env文件
load_dotenv()

# 配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Neo4j配置
NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'user': os.getenv('NEO4J_USER', 'neo4j'),
    'password': os.getenv('NEO4J_PASSWORD', 'password')
}

# 初始化RAG引擎
rag_engine = None
kg = None


def init_engines():
    """初始化引擎"""
    global rag_engine, kg
    try:
        kg = Neo4jKnowledgeGraph(**NEO4J_CONFIG)
        # 使用向量索引（如果存在）
        vector_index_path = 'vector_index' if os.path.exists('vector_index') else None
        rag_engine = ICHRAGEngine(neo4j_config=NEO4J_CONFIG, vector_index_path=vector_index_path)
        logger.info("引擎初始化成功")
    except Exception as e:
        logger.error(f"引擎初始化失败: {e}")


# ==================== 大模型调用 ====================
def call_qwen_api(prompt: str) -> str:
    """调用通义千问API"""
    api_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
    
    if not api_key:
        return "API密钥未配置，无法生成AI回答。请设置 QWEN_API_KEY 环境变量。"
    
    try:
        import dashscope
        from dashscope import Generation
        
        dashscope.api_key = api_key
        
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '你是一位中国非物质文化遗产专家，擅长讲解各类非遗的历史渊源、文化价值和传承意义。回答要专业、准确、有文化底蕴。'},
                {'role': 'user', 'content': prompt}
            ],
            result_format='message'
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"AI服务暂时不可用: {response.message}"
    except ImportError:
        return "请安装 dashscope 库: pip install dashscope"
    except Exception as e:
        logger.error(f"API调用错误: {e}")
        return f"生成回答时出错: {str(e)}"


# ==================== API 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """健康检查"""
    kg_status = "connected" if kg and kg.driver else "disconnected"
    return jsonify({
        'status': 'ok',
        'knowledge_graph': kg_status,
        'rag_engine': 'ready' if rag_engine else 'not_ready'
    })


@app.route('/api/stats')
def get_stats():
    """获取知识图谱统计"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    try:
        stats = kg.get_statistics()
        return jsonify({
            'total_projects': stats.get('total_items', 0),
            'total_categories': stats.get('total_categories', 0),
            'total_regions': stats.get('total_regions', 0),
            'total_organizations': stats.get('total_orgs', 0)
        })
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/categories')
def get_categories():
    """获取类别分布"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    try:
        distribution = kg.get_category_distribution()
        return jsonify({
            'categories': [
                {'name': d['类别'], 'count': d['数量']} 
                for d in distribution
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/init')
def graph_init():
    """获取初始图谱数据"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    try:
        # 获取部分节点和关系用于展示
        with kg.driver.session() as session:
            result = session.run("""
                MATCH (n:Item)-[r]->(m)
                RETURN n, r, m LIMIT 30
            """)
            
            nodes = []
            links = []
            node_ids = set()
            categories = set()
            
            for record in result:
                n = record['n']
                m = record['m']
                r = record['r']
                
                # 处理节点
                for node in [n, m]:
                    if node.id not in node_ids:
                        node_ids.add(node.id)
                        # 确定类别
                        category = 'Item'
                        if 'Category' in node.labels:
                            category = 'Category'
                        elif 'Region' in node.labels:
                            category = 'Region'
                        
                        nodes.append({
                            'id': str(node.id),
                            'name': node.get('name', 'Unknown'),
                            'category': category, # ECharts category index logic needed usually, simplified here
                            'symbolSize': 20 if category == 'Item' else 30,
                            'draggable': True
                        })
                        categories.add(category)

                # 处理关系
                links.append({
                    'source': str(n.id),
                    'target': str(m.id),
                    'name': type(r).__name__
                })
            
            # format categories for echarts
            unique_categories = list(categories)
            # map node category string to index
            for node in nodes:
                node['category'] = unique_categories.index(node['category'])

            cat_objs = [{'name': c} for c in unique_categories]
                
            return jsonify({
                'nodes': nodes,
                'links': links,
                'categories': cat_objs
            })
    except Exception as e:
        logger.error(f"图谱初始化失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/search')
def graph_search():
    """搜索图谱节点 - 按优先级搜索: Item → Category → Region → Organization"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    query = request.args.get('q', '')
    if not query:
        return graph_init()
        
    try:
        with kg.driver.session() as session:
            # 按优先级依次搜索各类型节点
            node_types = ['Item', 'Category', 'Region', 'Organization']
            center_node = None
            center_type = None
            
            for node_type in node_types:
                result = session.run(f"""
                    MATCH (n:{node_type}) WHERE n.name CONTAINS $q
                    RETURN n LIMIT 1
                """, q=query)
                record = result.single()
                if record and record['n']:
                    center_node = record['n']
                    center_type = node_type
                    break
            
            if not center_node:
                return jsonify({'nodes': [], 'links': [], 'categories': [], 'message': '未找到匹配节点'})
            
            # 获取中心节点的所有关联
            result = session.run("""
                MATCH (n) WHERE elementId(n) = $node_id
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n, labels(n) as n_labels, m, labels(m) as m_labels
            """, node_id=center_node.element_id)
            
            nodes = []
            links = []
            node_ids = set()
            
            type_to_cat = {'Item': 0, 'Category': 1, 'Region': 2, 'Organization': 3}
            
            for record in result:
                n = record['n']
                n_labels = record['n_labels']
                
                # 添加中心节点
                if n.element_id not in node_ids:
                    node_ids.add(n.element_id)
                    cat_idx = type_to_cat.get(center_type, 0)
                    nodes.append({
                        'id': n.element_id,
                        'name': n.get('name'),
                        'category': cat_idx,
                        'symbolSize': 50,
                        'itemStyle': {'color': '#C00000'}
                    })
                
                m = record['m']
                m_labels = record['m_labels'] or []
                
                if m:
                    if m.element_id not in node_ids:
                        node_ids.add(m.element_id)
                        cat_idx = 0
                        for label in m_labels:
                            if label in type_to_cat:
                                cat_idx = type_to_cat[label]
                                break
                        
                        nodes.append({
                            'id': m.element_id,
                            'name': m.get('name'),
                            'category': cat_idx,
                            'symbolSize': 30
                        })
                    
                    links.append({
                        'source': n.element_id,
                        'target': m.element_id
                    })
            
            categories = [
                {'name': '非遗项目'},
                {'name': '类别'},
                {'name': '地区'},
                {'name': '保护单位'}
            ]
            
            return jsonify({
                'nodes': nodes,
                'links': links,
                'categories': categories
            })

    except Exception as e:
        logger.error(f"图谱搜索失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/creative', methods=['POST'])
def creative_gen():
    """创意工坊统一接口"""
    data = request.get_json()
    c_type = data.get('type', '文创设计')
    item_name = data.get('item_name', '非遗项目')
    
    prompt = f"请为非遗项目“{item_name}”设计一个{c_type}方案。要求：1. 结合传统元素与现代审美；2. 具有实用性或传播价值；3. 描述具体的设计理念和产品形态。"
    
    content = call_qwen_api(prompt)
    
    return jsonify({
        'title': f"{item_name} - {c_type}方案",
        'content': content
    })


@app.route('/api/wenmai', methods=['POST'])
def wenmai_gen():
    """文脉溯源接口"""
    data = request.get_json()
    project_name = data.get('project_name', '非遗项目')
    
    prompt = f"""请追溯非遗项目"{project_name}"的历史渊源与文化脉络。要求：
1. 介绍该项目的起源年代和发源地
2. 阐述其历史演变过程和重要节点
3. 分析其与当地文化、民俗、信仰的关联
4. 探讨其在当代的传承现状和文化价值
5. 语言要有文化底蕴，像讲述一段历史故事"""
    
    content = call_qwen_api(prompt)
    
    return jsonify({
        'title': f'{project_name} - 文脉溯源',
        'content': content
    })


@app.route('/api/wenxue', methods=['POST'])
def wenxue_gen():
    """文学创作接口"""
    data = request.get_json()
    theme = data.get('theme', '非遗传承')
    creation_type = data.get('type', '诗')
    
    type_prompts = {
        '诗': f'请以"{theme}"为主题，创作一首七言或五言古诗。要求意境优美，富有文化韵味。',
        '词': f'请以"{theme}"为主题，创作一首词（可选词牌：如《水调歌头》《念奴娇》《满江红》等）。要求格律工整，意境深远。',
        '故事': f'请以"{theme}"为主题，创作一个约500字的文化故事。要求故事生动，有传承精神和时代意义。'
    }
    
    prompt = type_prompts.get(creation_type, type_prompts['诗'])
    content = call_qwen_api(prompt)
    
    return jsonify({
        'title': f'{theme} - {creation_type}',
        'content': content
    })


@app.route('/api/search')
def search():
    """搜索非遗项目"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'name')  # name, category, region
    
    if not query:
        return jsonify({'error': '请提供搜索关键词'}), 400
    
    try:
        if search_type == 'category':
            results = kg.query_by_category(query)
        elif search_type == 'region':
            results = kg.query_by_region(query)
        else:
            results = kg.query_by_name(query)
        
        return jsonify({
            'query': query,
            'type': search_type,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """智能问答"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': '请提供消息内容'}), 400
    
    user_message = data['message']
    use_ai = data.get('use_ai', True)
    
    try:
        if rag_engine:
            # 使用RAG引擎
            if use_ai:
                result = rag_engine.answer(user_message, llm_func=call_qwen_api)
            else:
                result = rag_engine.answer(user_message)
            
            return jsonify({
                'answer': result['answer'],
                'sources': result['sources'],
                'intent': result['retrieval']['intent']
            })
        else:
            # 降级：直接调用大模型
            if use_ai:
                answer = call_qwen_api(f"作为非遗专家，请回答：{user_message}")
            else:
                answer = "RAG引擎未初始化"
            
            return jsonify({
                'answer': answer,
                'sources': [],
                'intent': {'type': 'unknown', 'keyword': user_message}
            })
    except Exception as e:
        logger.error(f"问答错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/project/<name>')
def get_project(name: str):
    """获取项目详情"""
    if not kg or not kg.driver:
        return jsonify({'error': '知识图谱未连接'}), 503
    
    try:
        results = kg.query_by_name(name)
        if results:
            return jsonify({
                'found': True,
                'project': results[0],
                'related': results[1:5] if len(results) > 1 else []
            })
        else:
            return jsonify({'found': False, 'project': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-poem', methods=['POST'])
def generate_poem():
    """AI生成非遗主题诗词"""
    data = request.get_json()
    project_name = data.get('project_name', '')
    
    if not project_name:
        return jsonify({'error': '请提供非遗项目名称'}), 400
    
    prompt = f"""请以"{project_name}"为主题，创作一首古风诗词（五言或七言），
要求：
1. 体现该非遗项目的文化特色
2. 语言优美，意境深远
3. 表达对非遗传承的敬意

请直接给出诗词内容，不需要解释。"""
    
    poem = call_qwen_api(prompt)
    
    return jsonify({
        'project': project_name,
        'poem': poem
    })


@app.route('/api/generate-story', methods=['POST'])
def generate_story():
    """AI续写非遗故事"""
    data = request.get_json()
    project_name = data.get('project_name', '')
    story_start = data.get('story_start', '')
    
    if not project_name:
        return jsonify({'error': '请提供非遗项目名称'}), 400
    
    if story_start:
        prompt = f"""关于"{project_name}"的故事：

{story_start}

请续写这个故事（约300字），要求：
1. 延续故事风格
2. 融入该非遗的文化元素
3. 结局富有寓意"""
    else:
        prompt = f"""请创作一个关于"{project_name}"的短篇故事（约400字），
要求：
1. 故事生动有趣
2. 融入该非遗的历史和技艺
3. 体现文化传承的主题"""
    
    story = call_qwen_api(prompt)
    
    return jsonify({
        'project': project_name,
        'story': story
    })


# ==================== 启动 ====================

if __name__ == '__main__':
    # 初始化引擎
    init_engines()
    
    # 启动服务
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          图谱溯文脉 · AI焕非遗                            ║
║          非物质文化遗产智能问答系统                         ║
╠══════════════════════════════════════════════════════════╣
║  API服务已启动: http://localhost:{port}                   ║
║  健康检查: http://localhost:{port}/api/health             ║
║  统计信息: http://localhost:{port}/api/stats              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
