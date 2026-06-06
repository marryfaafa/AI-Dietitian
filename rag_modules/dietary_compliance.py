"""
饮食合规性检查模块 - Phase 2
基于用户体质/病症/忌口进行食材合规性检查

支持两种数据源:
1. Neo4j 图数据库（优先）- 从 Constitution/HealthCondition/DietaryRestriction 节点加载
2. JSON 文件（降级方案）- 从 dietary_knowledge.json 加载
"""

import json
import logging
from typing import List, Dict, Set, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """合规检查结果"""
    is_compliant: bool
    score: float  # 0~1，越高越适合
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suitable_ingredients: List[str] = field(default_factory=list)
    forbidden_ingredients: List[str] = field(default_factory=list)


class DietaryComplianceModule:
    """饮食合规性检查模块"""

    def __init__(self, knowledge_path: str = None, neo4j_driver=None,
                 neo4j_driver_factory: Callable = None):
        """
        初始化合规模块

        Args:
            knowledge_path: dietary_knowledge.json 文件路径（降级方案）
            neo4j_driver: Neo4j driver 实例
            neo4j_driver_factory: 返回 Neo4j driver 的工厂函数（懒加载用）
        """
        self._driver = neo4j_driver
        self._driver_factory = neo4j_driver_factory
        self._knowledge_path = knowledge_path

        # 快速查询索引
        self._forbidden_map: Dict[str, Set[str]] = {}  # {条件名: {禁忌食材}}
        self._recommended_map: Dict[str, Set[str]] = {}  # {条件名: {推荐食材}}
        self._limited_map: Dict[str, Set[str]] = {}  # {条件名: {限制食材}}

        # 选项列表（供前端使用）
        self._constitutions: List[Dict] = []
        self._conditions: List[Dict] = []
        self._restrictions: List[Dict] = []

        self._initialized = False

    def _ensure_initialized(self):
        """懒加载 - 首次使用时初始化"""
        if self._initialized:
            return
        self._initialized = True

        # 优先使用 Neo4j
        driver = self._get_driver()
        if driver:
            try:
                self._build_index_from_neo4j(driver)
                logger.info("饮食合规模块初始化完成（数据源: Neo4j）")
                return
            except Exception as e:
                logger.warning(f"从 Neo4j 加载健康数据失败: {e}，尝试 JSON 降级")

        # 降级到 JSON
        if self._knowledge_path:
            self._build_index_from_json()
            logger.info("饮食合规模块初始化完成（数据源: JSON）")
        else:
            logger.warning("无可用数据源，饮食合规模块将使用空知识库")

    def _get_driver(self):
        """获取 Neo4j driver"""
        if self._driver:
            return self._driver
        if self._driver_factory:
            try:
                self._driver = self._driver_factory()
                return self._driver
            except Exception as e:
                logger.warning(f"通过工厂函数获取 Neo4j driver 失败: {e}")
        return None

    def _build_index_from_neo4j(self, driver):
        """从 Neo4j 图数据库构建索引"""
        with driver.session() as session:
            # 加载体质
            result = session.run("""
                MATCH (c:Constitution)
                OPTIONAL MATCH (c)-[:RECOMMENDS]->(r:Ingredient)
                OPTIONAL MATCH (c)-[:FORBIDS]->(f:Ingredient)
                RETURN c.name AS name, c.description AS description,
                       collect(DISTINCT r.name) AS recommended,
                       collect(DISTINCT f.name) AS forbidden
            """)
            for record in result:
                name = record["name"]
                self._constitutions.append({"name": name, "description": record["description"]})
                self._recommended_map[name] = set(record["recommended"]) - {""}
                self._forbidden_map[name] = set(record["forbidden"]) - {""}

            # 加载病症
            result = session.run("""
                MATCH (h:HealthCondition)
                OPTIONAL MATCH (h)-[:FORBIDS]->(f:Ingredient)
                OPTIONAL MATCH (h)-[:LIMITS]->(l:Ingredient)
                OPTIONAL MATCH (h)-[:RECOMMENDS]->(r:Ingredient)
                RETURN h.name AS name, h.description AS description,
                       collect(DISTINCT f.name) AS forbidden,
                       collect(DISTINCT l.name) AS limited,
                       collect(DISTINCT r.name) AS recommended
            """)
            for record in result:
                name = record["name"]
                self._conditions.append({"name": name, "description": record["description"]})
                self._forbidden_map[name] = set(record["forbidden"]) - {""}
                self._limited_map[name] = set(record["limited"]) - {""}
                self._recommended_map[name] = set(record["recommended"]) - {""}

            # 加载忌口
            result = session.run("""
                MATCH (d:DietaryRestriction)
                OPTIONAL MATCH (d)-[:FORBIDS]->(f:Ingredient)
                OPTIONAL MATCH (d)-[:LIMITS]->(l:Ingredient)
                OPTIONAL MATCH (d)-[:RECOMMENDS]->(r:Ingredient)
                RETURN d.name AS name, d.description AS description,
                       collect(DISTINCT f.name) AS forbidden,
                       collect(DISTINCT l.name) AS limited,
                       collect(DISTINCT r.name) AS recommended
            """)
            for record in result:
                name = record["name"]
                self._restrictions.append({
                    "name": name,
                    "description": record["description"],
                    "forbidden_count": len(set(record["forbidden"]) - {""})
                })
                self._forbidden_map[name] = set(record["forbidden"]) - {""}
                if record["limited"]:
                    self._limited_map[name] = set(record["limited"]) - {""}
                if record["recommended"]:
                    self._recommended_map[name] = set(record["recommended"]) - {""}

    def _build_index_from_json(self):
        """从 JSON 文件构建索引（降级方案）"""
        knowledge = self._load_knowledge(self._knowledge_path)

        for item in knowledge.get("body_constitutions", []):
            name = item["name"]
            self._constitutions.append({"name": name, "description": item.get("description", "")})
            self._forbidden_map[name] = set(item.get("avoid", []))
            self._recommended_map[name] = set(item.get("recommend", []))

        for item in knowledge.get("health_conditions", []):
            name = item["name"]
            self._conditions.append({"name": name, "description": item.get("description", "")})
            self._forbidden_map[name] = set(item.get("forbidden_ingredients", []))
            self._limited_map[name] = set(item.get("limited_ingredients", []))
            self._recommended_map[name] = set(item.get("recommended_ingredients", []))

        for item in knowledge.get("dietary_restrictions", []):
            name = item["name"]
            self._restrictions.append({
                "name": name,
                "description": item.get("description", ""),
                "forbidden_count": len(item.get("forbidden", []))
            })
            self._forbidden_map[name] = set(item.get("forbidden", []))

    def _load_knowledge(self, path: str) -> Dict:
        """加载健康知识库"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"健康知识文件不存在: {path}，使用空知识库")
            return {"body_constitutions": [], "health_conditions": [], "dietary_restrictions": [], "nutrients": []}
        except Exception as e:
            logger.error(f"加载健康知识库失败: {e}")
            return {"body_constitutions": [], "health_conditions": [], "dietary_restrictions": [], "nutrients": []}

    def refresh(self):
        """强制重新加载数据"""
        self._initialized = False
        self._forbidden_map.clear()
        self._recommended_map.clear()
        self._limited_map.clear()
        self._constitutions.clear()
        self._conditions.clear()
        self._restrictions.clear()
        self._ensure_initialized()

    def get_forbidden_ingredients(self,
                                   constitutions: Optional[List[str]] = None,
                                   conditions: Optional[List[str]] = None,
                                   restrictions: Optional[List[str]] = None) -> Set[str]:
        """获取用户的所有禁忌食材"""
        self._ensure_initialized()
        forbidden = set()
        all_labels = []

        if constitutions:
            all_labels.extend(constitutions)
        if conditions:
            all_labels.extend(conditions)
        if restrictions:
            all_labels.extend(restrictions)

        for label in all_labels:
            forbidden.update(self._forbidden_map.get(label, set()))

        # 同时检查限制食材
        for label in all_labels:
            forbidden.update(self._limited_map.get(label, set()))

        return forbidden

    def get_recommended_ingredients(self,
                                     constitutions: Optional[List[str]] = None,
                                     conditions: Optional[List[str]] = None,
                                     restrictions: Optional[List[str]] = None) -> Set[str]:
        """获取推荐食材"""
        self._ensure_initialized()
        recommended = set()
        all_labels = []

        if constitutions:
            all_labels.extend(constitutions)
        if conditions:
            all_labels.extend(conditions)
        if restrictions:
            all_labels.extend(restrictions)

        for label in all_labels:
            recommended.update(self._recommended_map.get(label, set()))

        return recommended

    def check_recipe_compliance(self,
                                 recipe_name: str,
                                 recipe_ingredients: List[str],
                                 constitutions: Optional[List[str]] = None,
                                 conditions: Optional[List[str]] = None,
                                 restrictions: Optional[List[str]] = None) -> ComplianceResult:
        """
        检查菜谱对用户的合规性
        Args:
            recipe_name: 菜谱名称
            recipe_ingredients: 菜谱食材列表
            constitutions: 用户体质
            conditions: 用户病症
            restrictions: 用户忌口
        Returns:
            ComplianceResult 合规检查结果
        """
        self._ensure_initialized()
        reasons = []
        warnings = []
        suitable_ings = []
        forbidden_ings = []

        all_labels = (constitutions or []) + (conditions or []) + (restrictions or [])

        if not all_labels:
            return ComplianceResult(
                is_compliant=True,
                score=1.0,
                reasons=["未设置健康条件，默认合规"],
                warnings=[],
                suitable_ingredients=recipe_ingredients,
                forbidden_ingredients=[]
            )

        penalty = 0.0
        bonus = 0.0

        for ingredient in recipe_ingredients:
            matched_forbidden = False
            for label in all_labels:
                forbidden_set = self._forbidden_map.get(label, set())
                limited_set = self._limited_map.get(label, set())
                recommended_set = self._recommended_map.get(label, set())

                if self._match_ingredient(ingredient, forbidden_set):
                    forbidden_ings.append(ingredient)
                    penalty += 0.3
                    warnings.append(f"[{label}] 禁忌食材: {ingredient}")
                    matched_forbidden = True
                    break
                elif self._match_ingredient(ingredient, limited_set):
                    penalty += 0.1
                    warnings.append(f"[{label}] 限制食用: {ingredient}")

            if not matched_forbidden:
                for label in all_labels:
                    recommended_set = self._recommended_map.get(label, set())
                    if self._match_ingredient(ingredient, recommended_set):
                        suitable_ings.append(ingredient)
                        bonus += 0.05
                        break

        # 计算合规分数
        n_ingredients = len(recipe_ingredients) if recipe_ingredients else 1
        score = max(0.0, min(1.0, 1.0 - penalty + bonus / max(n_ingredients * 0.1, 1)))

        is_compliant = score >= 0.6 and not forbidden_ings

        if is_compliant:
            reasons.append("菜谱基本适合您的健康状况")
        else:
            reasons.append("菜谱包含不适合您的食材，建议替换或避免")

        if suitable_ings:
            reasons.append(f"适合您的食材: {', '.join(suitable_ings[:5])}")

        return ComplianceResult(
            is_compliant=is_compliant,
            score=round(score, 2),
            reasons=reasons,
            warnings=warnings,
            suitable_ingredients=suitable_ings,
            forbidden_ingredients=forbidden_ings
        )

    def _match_ingredient(self, ingredient: str, target_set: Set[str]) -> bool:
        """模糊匹配食材"""
        if not target_set:
            return False
        ingredient_lower = ingredient.lower()
        for target in target_set:
            target_lower = target.lower()
            # 精准匹配或包含匹配
            if ingredient_lower == target_lower or target_lower in ingredient_lower:
                return True
            # 去掉括号内容后匹配
            clean_ing = ingredient_lower.split('(')[0].strip()
            clean_target = target_lower.split('(')[0].strip()
            if clean_ing == clean_target:
                return True
        return False

    def filter_recipes(self,
                        recipes: List[Dict],
                        constitutions: Optional[List[str]] = None,
                        conditions: Optional[List[str]] = None,
                        restrictions: Optional[List[str]] = None) -> List[Dict]:
        """过滤菜谱列表，按合规分数排序"""
        scored_recipes = []
        for recipe in recipes:
            name = recipe.get("name", "未知菜谱")
            ingredients = recipe.get("ingredients", [])
            result = self.check_recipe_compliance(
                name, ingredients, constitutions, conditions, restrictions
            )
            recipe["compliance"] = {
                "score": result.score,
                "is_compliant": result.is_compliant,
                "warnings": result.warnings,
                "reasons": result.reasons
            }
            scored_recipes.append(recipe)

        # 按合规分数降序排序
        scored_recipes.sort(key=lambda r: r["compliance"]["score"], reverse=True)
        return scored_recipes

    def generate_compliance_report(self,
                                    constitutions: Optional[List[str]] = None,
                                    conditions: Optional[List[str]] = None,
                                    restrictions: Optional[List[str]] = None) -> str:
        """生成用户饮食合规报告"""
        forbidden = self.get_forbidden_ingredients(constitutions, conditions, restrictions)
        recommended = self.get_recommended_ingredients(constitutions, conditions, restrictions)

        report_parts = []
        if constitutions:
            report_parts.append(f"体质: {', '.join(constitutions)}")
        if conditions:
            report_parts.append(f"健康关注: {', '.join(conditions)}")
        if restrictions:
            report_parts.append(f"饮食限制: {', '.join(restrictions)}")

        if recommended:
            report_parts.append(f"\n推荐食材: {', '.join(list(recommended)[:10])}")
        if forbidden:
            report_parts.append(f"需避免食材: {', '.join(list(forbidden)[:10])}")

        return '\n'.join(report_parts)

    def get_constitution_list(self) -> List[Dict]:
        """获取支持的体质列表"""
        self._ensure_initialized()
        return self._constitutions

    def get_condition_list(self) -> List[Dict]:
        """获取支持的健康状况列表"""
        self._ensure_initialized()
        return self._conditions

    def get_restriction_list(self) -> List[Dict]:
        """获取支持的饮食限制列表"""
        self._ensure_initialized()
        return self._restrictions
