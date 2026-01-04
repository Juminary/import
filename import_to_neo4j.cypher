// Neo4j 知识图谱导入脚本 - 完整版
// 用于导入中国非物质文化遗产数据
//
// ?? 重要提示：
// 由于 Neo4j 5.x 的事务限制，CALL { ... } IN TRANSACTIONS 不能与其他语句在同一事务中执行
// 请使用分步执行的方式：
// 1. 先执行 01_create_indexes.cypher 创建索引
// 2. 再执行 02_import_data.cypher 导入数据
// 3. 最后执行 03_check_statistics.cypher 查看统计（可选）
//
// 或者，如果您想一次性执行，可以使用下面的简化版本（不使用 IN TRANSACTIONS）

// ============================================
// 方法一：分步执行（推荐，适合大数据量）
// ============================================
// 请分别执行以下文件：
// 1. import/01_create_indexes.cypher
// 2. import/02_import_data.cypher  
// 3. import/03_check_statistics.cypher

// ============================================
// 方法二：一次性执行（简化版，适合小数据量）
// ============================================
// 如果数据量不大（< 10万行），可以使用下面的简化版本：

// 1. 首先清理数据库（可选，如果需要重新导入）
// 注意：取消下面的注释将删除所有现有数据
// MATCH (n) DETACH DELETE n;

// 2. 创建索引
CREATE INDEX item_name_index IF NOT EXISTS FOR (i:Item) ON (i.name);
CREATE INDEX item_id_index IF NOT EXISTS FOR (i:Item) ON (i.id);
CREATE INDEX category_name_index IF NOT EXISTS FOR (c:Category) ON (c.name);
CREATE INDEX region_name_index IF NOT EXISTS FOR (r:Region) ON (r.name);
CREATE INDEX org_name_index IF NOT EXISTS FOR (o:Organization) ON (o.name);

// 3. 导入数据（简化版，不使用 IN TRANSACTIONS）
LOAD CSV WITH HEADERS FROM 'file:///ich_national_full_data.csv' AS row
WITH row
WHERE row.名称 IS NOT NULL AND row.名称 <> '' 
  AND row.类别 IS NOT NULL AND row.类别 <> ''
  AND row.申报地区 IS NOT NULL AND row.申报地区 <> ''
  AND row.保护单位 IS NOT NULL AND row.保护单位 <> ''

MERGE (category:Category {name: trim(row.类别)})
ON CREATE SET category.type = 'Category', category.createdAt = timestamp()

MERGE (region:Region {name: trim(row.申报地区)})
ON CREATE SET region.type = 'Region', region.createdAt = timestamp()

MERGE (org:Organization {name: trim(row.保护单位)})
ON CREATE SET org.type = 'Organization', org.createdAt = timestamp()

MERGE (item:Item {id: row.序号})
ON CREATE SET item.name = trim(row.名称), item.序号 = row.序号, 
              item.名称 = trim(row.名称), item.type = 'Item',
              item.createdAt = timestamp()
ON MATCH SET item.name = trim(row.名称), item.名称 = trim(row.名称)

MERGE (item)-[:属于]->(category)
MERGE (item)-[:申报于]->(region)
MERGE (item)-[:由保护单位]->(org);

