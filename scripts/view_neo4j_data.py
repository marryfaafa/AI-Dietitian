"""
查看 Neo4j 数据库中的数据
"""

from neo4j import GraphDatabase
from config import GraphRAGConfig

def view_neo4j_data():
    config = GraphRAGConfig()

    print(f"正在连接 Neo4j: {config.neo4j_uri}")
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_user, config.neo4j_password)
    )

    try:
        with driver.session() as session:
            # 1. 查看所有节点标签和数量
            print("\n" + "="*50)
            print("节点统计")
            print("="*50)
            result = session.run("""
                MATCH (n)
                RETURN labels(n) AS labels, count(n) AS count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"  {record['labels']}: {record['count']} 个")

            # 2. 查看所有关系类型和数量
            print("\n" + "="*50)
            print("关系统计")
            print("="*50)
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"  {record['type']}: {record['count']} 条")

            # 3. 查看各类型节点的示例
            print("\n" + "="*50)
            print("节点示例（每类最多5个）")
            print("="*50)

            # 获取所有标签
            result = session.run("""
                MATCH (n)
                WITH labels(n) AS lbls, n
                UNWIND lbls AS label
                RETURN DISTINCT label
                ORDER BY label
            """)
            labels = [record['label'] for record in result]

            for label in labels:
                print(f"\n  【{label}】:")
                result = session.run(f"""
                    MATCH (n:`{label}`)
                    RETURN n
                    LIMIT 5
                """)
                for record in result:
                    node = record['n']
                    props = dict(node)
                    # 只显示前3个属性
                    display_props = {k: v for i, (k, v) in enumerate(props.items()) if i < 3}
                    print(f"    {display_props}")

            # 4. 查看关系示例
            print("\n" + "="*50)
            print("关系示例（每种最多3条）")
            print("="*50)

            result = session.run("""
                MATCH ()-[r]->()
                RETURN DISTINCT type(r) AS rel_type
                ORDER BY rel_type
            """)
            rel_types = [record['rel_type'] for record in result]

            for rel_type in rel_types:
                print(f"\n  【{rel_type}】:")
                result = session.run(f"""
                    MATCH (a)-[r:`{rel_type}`]->(b)
                    RETURN labels(a) AS from_labels, a.name AS from_name,
                           labels(b) AS to_labels, b.name AS to_name
                    LIMIT 3
                """)
                for record in result:
                    from_name = record['from_name'] or '未知'
                    to_name = record['to_name'] or '未知'
                    print(f"    {from_name} --> {to_name}")

            # 5. 数据库总体信息
            print("\n" + "="*50)
            print("数据库概览")
            print("="*50)
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            node_count = result.single()['node_count']
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            rel_count = result.single()['rel_count']
            print(f"  总节点数: {node_count}")
            print(f"  总关系数: {rel_count}")
            print(f"  节点类型数: {len(labels)}")
            print(f"  关系类型数: {len(rel_types)}")

    except Exception as e:
        print(f"\n错误: {e}")
        print("\n请确保:")
        print("1. Neo4j 服务已启动")
        print(f"2. 连接地址正确: {config.neo4j_uri}")
        print(f"3. 用户名/密码正确: {config.neo4j_user} / {config.neo4j_password}")
    finally:
        driver.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    view_neo4j_data()
