## **Neo4j**

> [Neo4j的使用_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV13K4y187b4/?spm_id_from=333.1245.0.0)  -> NSeo 4j 节点/关系 的 增删查改 

Neo4j 是一种广为人知和应用的图形数据库,在知识图谱领域扮演着重要的角色。

作为一种原生的图形数据库, Neo4j非常适合存储和管理高度连接的半结构化数据, 如知识图谱中的实体-关系模型数据。Neo4j使用灵活的属性图模型, 能自然地对应知识图谱中的节点(实体)、关系(predicate)和属性。

Neo4j主要在以下几个方面为知识图谱应用提供支持:

| 功能         | 描述                                                         |
| ------------ | ------------------------------------------------------------ |
| 知识存储     | Neo4j 可高效存储大规模的知识图谱数据, <br />每个节点、关系和属性都被自动编制索引, 支持快速遍历和查询。 |
| 数据建模     | Neo4j 支持使用声明式的图形查询语言 Cypher 进行知识图谱数据建模, <br />能自然地表示事物之间的网状关联关系, 符合人类的认知模式。 |
| 图遍历和查询 | Cypher 提供了丰富的图遍历和查询功能, <br />如节点/关系查找、模式匹配、路径查询、聚合分析等, 可方便地挖掘知识图谱中的复杂关联模式。 |
| 数据可视化   | Neo4j 提供友好的数据可视化工具, <br />直观展示知识图谱的结构拓扑关系,可应用于知识探索、解释等场景。 |
| 图数据库集群 | Neo4j 支持集群部署, 提供水平扩展能力, 可适应大规模知识图谱应用的需求。 |

> **Neo4j的基本语法和语言模式**:
>
> Neo4j使用声明式的图形查询语言Cypher作为主要查询语言。Cypher语法类似SQL,但以图形模式来表达查询,能够直观地表示节点、关系和属性。
>
> 1. 节点(Node)
>
>   节点用圆括号表示,如`()`。可以在圆括号内定义节点标签(Label)和属性(Property)。
>   例如: `(m:Movie {title:'The Matrix', released:1999})`
>
> 2. 关系(Relationship)  
>
>   关系用方括号表示,如`[]`。用连字符`--`连接两个节点,表示它们之间存在某种关系。方括号中可以定义关系类型和属性。
>   例如: `(m:Movie)--[r:ACTED_IN]->(p:Person)`
>
> 3. 模式匹配
>
>   使用MATCH子句来指定需要查找的模式,可匹配节点、关系和属性。
>   例如:
>
> ```cypher
> MATCH (m:Movie)-->(p:Person) 
> RETURN m.title, p.name
> ```
>
> 4. 创建节点和关系
>
>   使用CREATE子句创建新节点和关系:
>
> ```cypher
> CREATE (p:Person {name:'Keanu Reeves'})
> CREATE (m:Movie {title:'The Matrix'})
> CREATE (p)-[:ACTED_IN]->(m)
> ```
>
> 5. 更新和删除
>
>   使用SET子句更新属性, REMOVE子句删除节点/关系:
>
> ```cypher
> MATCH (m:Movie) 
> WHERE m.released < 2000
> SET m.oldMovie = true
> 
> MATCH (p:Person)-[r]->()
> DELETE r
> ```
>
> 6. 约束和索引 
>
>   使用CREATE CONSTRAINT创建约束, CREATE INDEX创建索引:
>
> ```cypher
> CREATE CONSTRAINT ON (p:Person) ASSERT p.name IS UNIQUE
> CREATE INDEX ON :Movie(title)  
> ```
>
> 7. 路径查询
>
>   MATCH支持路径模式查询, 如查找两节点之间的所有路径:
>
> ```cypher
> MATCH path = (p1:Person)-[*]-(p2:Person)
> WHERE p1.name = 'Keanu Reeves' AND p2.name = 'Hugo Weaving'
> RETURN path
> ```
>
> 8. 聚合、过滤等
>
>   Cypher支持COUNT、SUM等聚合函数, WITH子句用于链接查询步骤, ORDER BY排序等。
>
> Neo4j查询语言Cypher的主旨是**直观地使用图形模式来表达需求**, 并提供声明式的高阶查询能力, 从而高效地处理图数据查询和分析任务。使用起来比较直白易懂。

### 常用查询

```cypher
//[1] 返回知识图谱中的所有节点和关系
MATCH (n) // 匹配图谱中的所有节点,并将它们绑定到变量 n。
OPTIONAL MATCH (n)-[r]->() // 对于每个节点 n,尝试匹配从它出发的所有关系,并将关系绑定到变量 r。使用 OPTIONAL MATCH 而不是 MATCH,是为了处理那些没有任何关系的孤立节点。
RETURN n, r // 返回所有匹配到的节点 n 和关系 r。对于没有关系的节点,r 将会是 null。

//[2] 返回图谱的元数据
// 利用APOC(Awesome Procedures On Cypher)库的meta.graph过程,它会返回图谱的元数据,包括所有的节点标签、关系类型、属性等
CALL apoc.meta.graph()
CALL db.schema.visualization()

//[3] 获得更详细的信息
MATCH (n) 
OPTIONAL MATCH (n)-[r]->()
RETURN n.name, labels(n), r, type(r)
                                  
//[4] 删除所有节点
MATCH (n)
DETACH DELETE n
```

