"""
饮食合规性检查模块 - Phase 2
基于用户体质/病症/忌口进行食材合规性检查
"""

import json
import logging
from typing import List, Dict, Set, Optional
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

    def __init__(self, knowledge_path: str):
        """
        初始化合规模块
        Args:
            knowledge_path: dietary_knowledge.json 文件路径
        """
        self.knowledge = self._load_knowledge(knowledge_path)

        # 快速查询索引
        self._forbidden_map: Dict[str, Set[str]] = {}  # {条件名: {禁忌食材}}
        self._recommended_map: Dict[str, Set[str]] = {}  # {条件名: {推荐食材}}
        self._limited_map: Dict[str, Set[str]] = {}  # {条件名: {限制食材}}
        self._build_index()

        logger.info(f"饮食合规模块初始化完成，已加载 {len(self.knowledge)} 条健康知识")

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

    def _build_index(self):
        """构建快速查询索引"""
        # 体质
        for item in self.knowledge.get("body_constitutions", []):
            name = item["name"]
            self._forbidden_map[name] = set(item.get("avoid", []))
            self._recommended_map[name] = set(item.get("recommend", []))

        # 病症
        for item in self.knowledge.get("health_conditions", []):
            name = item["name"]
            self._forbidden_map[name] = set(item.get("forbidden_ingredients", []))
            self._limited_map[name] = set(item.get("limited_ingredients", []))
            self._recommended_map[name] = set(item.get("recommended_ingredients", []))

        # 忌口/过敏
        for item in self.knowledge.get("dietary_restrictions", []):
            name = item["name"]
            self._forbidden_map[name] = set(item.get("forbidden", []))

    def get_forbidden_ingredients(self,
                                   constitutions: Optional[List[str]] = None,
                                   conditions: Optional[List[str]] = None,
                                   restrictions: Optional[List[str]] = None) -> Set[str]:
        """获取用户的所有禁忌食材"""
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
        return [{"name": c["name"], "description": c["description"]}
                for c in self.knowledge.get("body_constitutions", [])]

    def get_condition_list(self) -> List[Dict]:
        """获取支持的健康状况列表"""
        return [{"name": c["name"], "description": c["description"]}
                for c in self.knowledge.get("health_conditions", [])]

    def get_restriction_list(self) -> List[Dict]:
        """获取支持的饮食限制列表"""
        return [{"name": r["name"], "forbidden_count": len(r.get("forbidden", []))}
                for r in self.knowledge.get("dietary_restrictions", [])]
