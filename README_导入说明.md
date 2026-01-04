# Neo4j 知识图谱导入指南

## 数据文件
- `ich_national_full_data.csv` - 中国非物质文化遗产数据

## 导入步骤

### 方法一：使用 Neo4j Browser（推荐）

1. **启动 Neo4j 服务器**
   ```bash
   # 在 Neo4j 安装目录下执行
   bin\neo4j.bat console
   ```
   或者使用 PowerShell：
   ```powershell
   bin\neo4j.ps1 console
   ```

2. **打开 Neo4j Browser**
   - 在浏览器中访问：http://localhost:7474
   - 默认用户名：neo4j
   - 默认密码：neo4j（首次登录需要修改）

3. **执行导入脚本**
   - 在 Neo4j Browser 的查询框中，复制粘贴 `import_to_neo4j.cypher` 文件中的内容
   - 点击运行按钮执行导入

### 方法二：使用 Cypher Shell（命令行）

1. **打开命令行工具**
   ```bash
   # 进入 Neo4j bin 目录
   cd bin
   
   # 启动 Cypher Shell
   cypher-shell.bat -u neo4j -p neo4j
   ```

2. **执行导入脚本**
   ```cypher
   // 在 cypher-shell 中执行
   :source import/import_to_neo4j.cypher
   ```
   或者直接复制粘贴脚本内容执行

### 方法三：使用 neo4j-admin import（批量导入，适合大数据量）

如果需要重新导入大量数据，可以使用 neo4j-admin 工具：

1. **停止 Neo4j 服务器**

2. **准备数据文件**
   需要将 CSV 转换为 Neo4j 导入格式（节点文件和关系文件）

3. **执行导入**
   ```bash
   bin\neo4j-admin.bat database import full --nodes=import/nodes.csv --relationships=import/relationships.csv
   ```

## 知识图谱结构

导入后将创建以下节点类型和关系：

### 节点类型
- **Item（项目）**: 非物质文化遗产项目
  - 属性：id, name, 序号, 名称
- **Category（类别）**: 项目类别（如：民间文学、传统音乐等）
  - 属性：name
- **Region（地区）**: 申报地区
  - 属性：name
- **Organization（保护单位）**: 保护单位
  - 属性：name

### 关系类型
- **属于**: Item → Category（项目属于某个类别）
- **申报于**: Item → Region（项目申报于某个地区）
- **由保护单位**: Item → Organization（项目由某个保护单位保护）

## 查询示例

### 1. 查看所有类别
```cypher
MATCH (c:Category)
RETURN c.name AS 类别名称
ORDER BY c.name
```

### 2. 查看某个类别的所有项目
```cypher
MATCH (c:Category {name: '民间文学'})<-[:属于]-(item:Item)
RETURN item.name AS 项目名称
LIMIT 20
```

### 3. 查看某个地区的所有项目
```cypher
MATCH (r:Region {name: '贵州省台江县'})<-[:申报于]-(item:Item)
RETURN item.name AS 项目名称, item.类别 AS 类别
```

### 4. 查看项目的完整信息
```cypher
MATCH (item:Item {name: '苗族古歌'})
OPTIONAL MATCH (item)-[:属于]->(category:Category)
OPTIONAL MATCH (item)-[:申报于]->(region:Region)
OPTIONAL MATCH (item)-[:由保护单位]->(org:Organization)
RETURN item.name AS 项目名称,
       category.name AS 类别,
       collect(region.name) AS 申报地区,
       collect(org.name) AS 保护单位
```

### 5. 统计各类别的项目数量
```cypher
MATCH (c:Category)<-[:属于]-(item:Item)
RETURN c.name AS 类别, count(item) AS 项目数量
ORDER BY 项目数量 DESC
```

### 6. 查找某个保护单位保护的所有项目
```cypher
MATCH (org:Organization {name: '台江县非物质文化遗产保护中心'})<-[:由保护单位]-(item:Item)
RETURN item.name AS 项目名称
```

## 注意事项

1. **文件路径**: 确保 CSV 文件在 `import` 目录下
2. **编码问题**: 如果遇到中文乱码，确保 CSV 文件使用 UTF-8 编码
3. **性能优化**: 对于大数据量，建议分批导入或使用 neo4j-admin import
4. **清理数据**: 如果需要重新导入，可以取消注释脚本开头的清理语句

## 故障排除

### 问题1：找不到文件
- 确保 CSV 文件在 `import` 目录下
- 检查 `conf/neo4j.conf` 中的 `server.directories.import=import` 配置

### 问题2：中文乱码
- 确保 CSV 文件使用 UTF-8 编码
- 可以在 LOAD CSV 语句中添加编码参数

### 问题3：导入速度慢
- 对于大数据量，考虑使用 neo4j-admin import
- 确保已创建索引
- 可以分批导入数据

