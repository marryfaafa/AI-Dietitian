

import sys
import os
import json
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config import DEFAULT_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ID 范围分配
CONSTITUTION_ID_START = 300000001
HEALTH_CONDITION_ID_START = 300000010
DIETARY_RESTRICTION_ID_START = 300000016
VIRTUAL_INGREDIENT_ID_START = 310000001


def load_json_data(knowledge_path: str) -> dict:
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_indexes(session):
    """创建索引"""
    indexes = [
        "CREATE INDEX constitution_nodeId IF NOT EXISTS FOR (c:Constitution) ON (c.nodeId)",
        "CREATE INDEX constitution_name IF NOT EXISTS FOR (c:Constitution) ON (c.name)",
        "CREATE INDEX healthcondition_nodeId IF NOT EXISTS FOR (h:HealthCondition) ON (h.nodeId)",
        "CREATE INDEX healthcondition_name IF NOT EXISTS FOR (h:HealthCondition) ON (h.name)",
        "CREATE INDEX dietaryrestriction_nodeId IF NOT EXISTS FOR (d:DietaryRestriction) ON (d.nodeId)",
        "CREATE INDEX dietaryrestriction_name IF NOT EXISTS FOR (d:DietaryRestriction) ON (d.name)",
    ]
    for cypher in indexes:
        session.run(cypher)
    logger.info("索引创建完成")


def create_constitutions(session, constitutions: list, dry_run: bool = False):
    """创建体质节点"""
    count = 0
    for i, item in enumerate(constitutions):
        node_id = str(CONSTITUTION_ID_START + i)
        name = item["name"]
        description = item.get("description", "")
        if dry_run:
            logger.info(f"  [DRY-RUN] Constitution: {name} (ID: {node_id})")
        else:
            session.run("""
                MERGE (c:Constitution {name: $name})
                SET c.nodeId = $nodeId,
                    c.description = $description,
                    c.category = '体质'
            """, name=name, nodeId=node_id, description=description)
        count += 1
    logger.info(f"体质节点: {count} 个")
    return count


def create_health_conditions(session, conditions: list, dry_run: bool = False):
    """创建病症节点"""
    count = 0
    for i, item in enumerate(conditions):
        node_id = str(HEALTH_CONDITION_ID_START + i)
        name = item["name"]
        description = item.get("description", "")
        if dry_run:
            logger.info(f"  [DRY-RUN] HealthCondition: {name} (ID: {node_id})")
        else:
            session.run("""
                MERGE (h:HealthCondition {name: $name})
                SET h.nodeId = $nodeId,
                    h.description = $description,
                    h.category = '病症'
            """, name=name, nodeId=node_id, description=description)
        count += 1
    logger.info(f"病症节点: {count} 个")
    return count


def create_dietary_restrictions(session, restrictions: list, dry_run: bool = False):
    """创建忌口节点"""
    count = 0
    for i, item in enumerate(restrictions):
        node_id = str(DIETARY_RESTRICTION_ID_START + i)
        name = item["name"]
        description = item.get("description", "")
        if dry_run:
            logger.info(f"  [DRY-RUN] DietaryRestriction: {name} (ID: {node_id})")
        else:
            session.run("""
                MERGE (d:DietaryRestriction {name: $name})
                SET d.nodeId = $nodeId,
                    d.description = $description,
                    d.category = '忌口'
            """, name=name, nodeId=node_id, description=description)
        count += 1
    logger.info(f"忌口节点: {count} 个")
    return count


def _find_or_create_ingredient(session, ing_name: str, virtual_id_counter: list, dry_run: bool) -> str:
    """
    查找或创建 Ingredient 节点。
    优先精确匹配，其次子串匹配，最后创建虚拟节点。
    返回匹配到的 Ingredient name。
    """
    # 1. 精确匹配
    result = session.run(
        "MATCH (i:Ingredient {name: $name}) RETURN i.name AS name LIMIT 1",
        name=ing_name
    )
    record = result.single()
    if record:
        return record["name"]

    # 2. 子串匹配（JSON名称包含在已有Ingredient名称中，或反过来）
    result = session.run("""
        MATCH (i:Ingredient)
        WHERE i.name CONTAINS $name OR $name CONTAINS i.name
        RETURN i.name AS name LIMIT 1
    """, name=ing_name)
    record = result.single()
    if record:
        return record["name"]

    # 3. 创建虚拟 Ingredient 节点
    virtual_id = str(virtual_id_counter[0])
    virtual_id_counter[0] += 1
    if dry_run:
        logger.info(f"  [DRY-RUN] 虚拟 Ingredient: {ing_name} (ID: {virtual_id})")
    else:
        session.run("""
            MERGE (i:Ingredient {name: $name})
            ON CREATE SET i.nodeId = $nodeId, i.source = 'health_knowledge'
        """, name=ing_name, nodeId=virtual_id)
    return ing_name


def link_constitutions(session, constitutions: list, virtual_id_counter: list, dry_run: bool = False):
    """建立体质 → 食材关系"""
    rel_count = 0
    for item in constitutions:
        name = item["name"]

        # RECOMMENDS 关系
        for ing_name in item.get("recommend", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] Constitution({name}) -[:RECOMMENDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (c:Constitution {name: $const_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (c)-[r:RECOMMENDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, const_name=name, ing_name=matched)
            rel_count += 1

        # FORBIDS 关系 (对应 JSON 中的 avoid)
        for ing_name in item.get("avoid", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] Constitution({name}) -[:FORBIDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (c:Constitution {name: $const_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (c)-[r:FORBIDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, const_name=name, ing_name=matched)
            rel_count += 1

    logger.info(f"体质关系: {rel_count} 条")
    return rel_count


def link_health_conditions(session, conditions: list, virtual_id_counter: list, dry_run: bool = False):
    """建立病症 → 食材关系"""
    rel_count = 0
    for item in conditions:
        name = item["name"]

        for ing_name in item.get("forbidden_ingredients", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] HealthCondition({name}) -[:FORBIDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (h:HealthCondition {name: $cond_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (h)-[r:FORBIDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, cond_name=name, ing_name=matched)
            rel_count += 1

        for ing_name in item.get("limited_ingredients", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] HealthCondition({name}) -[:LIMITS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (h:HealthCondition {name: $cond_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (h)-[r:LIMITS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, cond_name=name, ing_name=matched)
            rel_count += 1

        for ing_name in item.get("recommended_ingredients", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] HealthCondition({name}) -[:RECOMMENDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (h:HealthCondition {name: $cond_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (h)-[r:RECOMMENDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, cond_name=name, ing_name=matched)
            rel_count += 1

    logger.info(f"病症关系: {rel_count} 条")
    return rel_count


def link_dietary_restrictions(session, restrictions: list, virtual_id_counter: list, dry_run: bool = False):
    """建立忌口 → 食材关系"""
    rel_count = 0
    for item in restrictions:
        name = item["name"]

        for ing_name in item.get("forbidden", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] DietaryRestriction({name}) -[:FORBIDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (d:DietaryRestriction {name: $res_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (d)-[r:FORBIDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, res_name=name, ing_name=matched)
            rel_count += 1

        for ing_name in item.get("limited", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] DietaryRestriction({name}) -[:LIMITS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (d:DietaryRestriction {name: $res_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (d)-[r:LIMITS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, res_name=name, ing_name=matched)
            rel_count += 1

        for ing_name in item.get("recommended", []):
            matched = _find_or_create_ingredient(session, ing_name, virtual_id_counter, dry_run)
            if dry_run:
                logger.info(f"  [DRY-RUN] DietaryRestriction({name}) -[:RECOMMENDS]-> Ingredient({matched})")
            else:
                session.run("""
                    MATCH (d:DietaryRestriction {name: $res_name})
                    MATCH (i:Ingredient {name: $ing_name})
                    MERGE (d)-[r:RECOMMENDS]->(i)
                    SET r.source = 'dietary_knowledge'
                """, res_name=name, ing_name=matched)
            rel_count += 1

    logger.info(f"忌口关系: {rel_count} 条")
    return rel_count


def clean_health_data(session):
    """清除所有健康相关节点"""
    logger.info("清除健康数据...")
    session.run("""
        MATCH (n) WHERE n:Constitution OR n:HealthCondition OR n:DietaryRestriction
        DETACH DELETE n
    """)
    session.run("""
        MATCH (i:Ingredient) WHERE i.source = 'health_knowledge'
        DETACH DELETE i
    """)
    logger.info("清除完成")


def print_summary(session):
    """打印迁移摘要"""
    result = session.run("MATCH (n:Constitution) RETURN count(n) AS cnt").single()
    const_count = result["cnt"]
    result = session.run("MATCH (n:HealthCondition) RETURN count(n) AS cnt").single()
    cond_count = result["cnt"]
    result = session.run("MATCH (n:DietaryRestriction) RETURN count(n) AS cnt").single()
    res_count = result["cnt"]

    result = session.run("""
        MATCH (n)-[r]->(i:Ingredient)
        WHERE n:Constitution OR n:HealthCondition OR n:DietaryRestriction
        RETURN type(r) AS rel_type, count(r) AS cnt
        ORDER BY cnt DESC
    """)
    rel_summary = {record["rel_type"]: record["cnt"] for record in result}

    result = session.run("MATCH (i:Ingredient) WHERE i.source = 'health_knowledge' RETURN count(i) AS cnt").single()
    virtual_count = result["cnt"]

    print("\n" + "=" * 50)
    print("迁移摘要")
    print("=" * 50)
    print(f"Constitution 节点: {const_count}")
    print(f"HealthCondition 节点: {cond_count}")
    print(f"DietaryRestriction 节点: {res_count}")
    print(f"虚拟 Ingredient 节点: {virtual_count}")
    print(f"关系统计:")
    for rel_type, cnt in rel_summary.items():
        print(f"  {rel_type}: {cnt}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="将健康数据从JSON迁移到Neo4j")
    parser.add_argument("--dry-run", action="store_true", help="预览迁移，不写入数据库")
    parser.add_argument("--clean", action="store_true", help="清除已有健康数据后重新迁移")
    parser.add_argument("--knowledge-path", default=DEFAULT_CONFIG.dietary_knowledge_path,
                        help="dietary_knowledge.json 路径")
    args = parser.parse_args()

    logger.info(f"连接 Neo4j: {DEFAULT_CONFIG.neo4j_uri}")
    driver = GraphDatabase.driver(
        DEFAULT_CONFIG.neo4j_uri,
        auth=(DEFAULT_CONFIG.neo4j_user, DEFAULT_CONFIG.neo4j_password)
    )

    data = load_json_data(args.knowledge_path)
    logger.info(f"加载知识库: 体质 {len(data.get('body_constitutions', []))} 种, "
                f"病症 {len(data.get('health_conditions', []))} 种, "
                f"忌口 {len(data.get('dietary_restrictions', []))} 种")

    virtual_id_counter = [VIRTUAL_INGREDIENT_ID_START]

    with driver.session() as session:
        if args.clean and not args.dry_run:
            clean_health_data(session)

        if not args.dry_run:
            create_indexes(session)

        logger.info("--- 开始迁移 ---")

        node_count = 0
        node_count += create_constitutions(session, data.get("body_constitutions", []), args.dry_run)
        node_count += create_health_conditions(session, data.get("health_conditions", []), args.dry_run)
        node_count += create_dietary_restrictions(session, data.get("dietary_restrictions", []), args.dry_run)

        rel_count = 0
        rel_count += link_constitutions(session, data.get("body_constitutions", []), virtual_id_counter, args.dry_run)
        rel_count += link_health_conditions(session, data.get("health_conditions", []), virtual_id_counter, args.dry_run)
        rel_count += link_dietary_restrictions(session, data.get("dietary_restrictions", []), virtual_id_counter, args.dry_run)

        logger.info(f"--- 迁移完成: {node_count} 个节点, {rel_count} 条关系 ---")

        if not args.dry_run:
            print_summary(session)

    driver.close()


if __name__ == "__main__":
    main()
