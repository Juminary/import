#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用大模型API生成非遗项目介绍
当无法从网络获取详细介绍时，利用AI生成高质量内容

支持的API:
- 通义千问 (Qwen)
- 智谱AI (ChatGLM)
- 百度文心一言

使用方法:
1. 设置环境变量 QWEN_API_KEY 或其他API密钥
2. 运行脚本生成非遗项目介绍
"""

import os
import json
import csv
import time
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== 通义千问 API =====================
def generate_with_qwen(prompt: str, api_key: str) -> Optional[str]:
    """使用通义千问API生成内容"""
    try:
        import dashscope
        from dashscope import Generation
        
        dashscope.api_key = api_key
        
        response = Generation.call(
            model='qwen-max',  # 或 qwen-turbo, qwen-plus
            messages=[
                {'role': 'system', 'content': '你是一位中国非物质文化遗产研究专家，熟悉各类非遗项目的历史渊源、技艺特点和文化价值。'},
                {'role': 'user', 'content': prompt}
            ],
            result_format='message'
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            logger.error(f"通义千问API调用失败: {response.message}")
            return None
    except ImportError:
        logger.error("请安装dashscope: pip install dashscope")
        return None
    except Exception as e:
        logger.error(f"通义千问API错误: {e}")
        return None


# ===================== OpenAI兼容API =====================
def generate_with_openai_compatible(prompt: str, api_key: str, 
                                     base_url: str = "https://api.openai.com/v1",
                                     model: str = "gpt-3.5-turbo") -> Optional[str]:
    """使用OpenAI兼容API生成内容（支持本地部署的模型）"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位中国非物质文化遗产研究专家，熟悉各类非遗项目的历史渊源、技艺特点和文化价值。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except ImportError:
        logger.error("请安装openai: pip install openai")
        return None
    except Exception as e:
        logger.error(f"OpenAI API错误: {e}")
        return None


def generate_ich_introduction(name: str, category: str, region: str, 
                               organization: str, api_key: str,
                               api_type: str = "qwen") -> Optional[str]:
    """
    生成非遗项目详细介绍
    
    Args:
        name: 项目名称
        category: 类别
        region: 申报地区
        organization: 保护单位
        api_key: API密钥
        api_type: API类型 (qwen/openai)
    
    Returns:
        生成的项目介绍
    """
    prompt = f"""请为以下国家级非物质文化遗产项目撰写一段详细介绍（约300-500字）：

项目名称：{name}
类别：{category}
申报地区：{region}
保护单位：{organization}

请从以下几个方面进行介绍：
1. 历史渊源：项目的起源、发展历程
2. 技艺特点：主要表现形式、核心技艺
3. 文化价值：承载的文化内涵、历史意义
4. 传承现状：保护与传承情况
5. 代表性特征：与其他同类项目的区别

要求：
- 语言准确、专业
- 突出地域特色
- 体现文化自信
- 内容真实可信"""

    if api_type == "qwen":
        return generate_with_qwen(prompt, api_key)
    elif api_type == "openai":
        return generate_with_openai_compatible(prompt, api_key)
    else:
        logger.error(f"不支持的API类型: {api_type}")
        return None


def batch_generate_introductions(csv_path: str, output_path: str, 
                                  api_key: str, api_type: str = "qwen",
                                  limit: int = None, delay: float = 1.0):
    """
    批量生成非遗项目介绍
    
    Args:
        csv_path: 输入CSV文件路径
        output_path: 输出JSON文件路径
        api_key: API密钥
        api_type: API类型
        limit: 限制生成数量
        delay: 请求间隔（秒）
    """
    # 加载现有结果
    results = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            logger.info(f"加载已有结果 {len(results)} 条")
        except:
            pass
    
    generated_names = set(r.get('项目名称', '') for r in results)
    
    # 读取CSV
    projects = []
    seen_names = set()
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('名称', '')
            if name and name not in seen_names and name not in generated_names:
                seen_names.add(name)
                projects.append(row)
    
    if limit:
        projects = projects[:limit]
    
    logger.info(f"待生成项目数: {len(projects)}")
    
    for i, project in enumerate(projects):
        name = project.get('名称', '')
        category = project.get('类别', '')
        region = project.get('申报地区', '')
        organization = project.get('保护单位', '')
        
        logger.info(f"[{i+1}/{len(projects)}] 生成: {name}")
        
        intro = generate_ich_introduction(
            name, category, region, organization,
            api_key, api_type
        )
        
        if intro:
            results.append({
                '项目名称': name,
                '类别': category,
                '申报地区': region,
                '保护单位': organization,
                '详细介绍': intro,
                '生成方式': f'AI生成 ({api_type})'
            })
            logger.info(f"  ✓ 生成成功，长度: {len(intro)}")
            
            # 定期保存
            if len(results) % 10 == 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
        else:
            logger.warning(f"  ✗ 生成失败")
        
        time.sleep(delay)
    
    # 最终保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"完成！共生成 {len(results)} 条项目介绍")


def main():
    """主函数"""
    # 从环境变量获取API密钥
    api_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
    
    if not api_key:
        print("请设置环境变量 QWEN_API_KEY 或 DASHSCOPE_API_KEY")
        print("export QWEN_API_KEY='your-api-key'")
        return
    
    csv_path = 'ich_national_full_data.csv'
    output_path = 'ich_ai_introductions.json'
    
    # 先测试生成5个
    batch_generate_introductions(
        csv_path, output_path,
        api_key=api_key,
        api_type='qwen',
        limit=5,
        delay=1.5
    )


if __name__ == '__main__':
    main()
