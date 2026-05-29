"""
智能配餐规划模块 - Phase 3
基于用户画像和合规检查，生成个性化膳食方案（一日三餐/一周食谱）
"""

import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MealPlan:
    """配餐方案"""
    meal_type: str  # 早餐/午餐/晚餐/加餐
    recipe_name: str
    recipe_node_id: str
    ingredients: List[str] = field(default_factory=list)
    reason: str = ""
    compliance_score: float = 1.0
    warnings: List[str] = field(default_factory=list)


@dataclass
class DailyPlan:
    """一日三餐方案"""
    date: str
    meals: List[MealPlan] = field(default_factory=list)
    total_score: float = 0.0
    summary: str = ""


@dataclass
class WeeklyPlan:
    """一周食谱方案"""
    start_date: str
    end_date: str
    daily_plans: List[DailyPlan] = field(default_factory=list)
    overall_summary: str = ""


class MealPlanner:
    """智能配餐规划器"""

    def __init__(self, compliance_module, llm_client, llm_model: str = "kimi-k2-0711-preview"):
        """
        Args:
            compliance_module: DietaryComplianceModule 实例
            llm_client: OpenAI 客户端（已配置 Moonshot API）
            llm_model: LLM 模型名称
        """
        self.compliance = compliance_module
        self.llm_client = llm_client
        self.llm_model = llm_model

    def plan_daily_meals(self,
                          candidate_recipes: List[Dict],
                          user_profile: Dict,
                          date: str = "今日") -> DailyPlan:
        """
        规划一日三餐
        Args:
            candidate_recipes: 候选菜谱列表 [{name, node_id, ingredients, category, ...}]
            user_profile: 用户画像 {"constitutions": [], "conditions": [], "restrictions": [], ...}
            date: 日期描述
        Returns:
            DailyPlan 一日三餐方案
        """
        constitutions = user_profile.get("constitutions", [])
        conditions = user_profile.get("conditions", [])
        restrictions = user_profile.get("restrictions", [])
        preferences = user_profile.get("cuisine_preferences", [])

        # 1. 合规过滤 + 排序
        scored = self.compliance.filter_recipes(
            candidate_recipes, constitutions, conditions, restrictions
        )

        # 2. 按餐类分组
        breakfast_candidates = [r for r in scored if self._is_breakfast(r)]
        lunch_dinner_candidates = [r for r in scored if not self._is_breakfast(r)]

        # 偏好加权
        if preferences:
            for r in scored:
                cuisine = r.get("cuisineType", "")
                if cuisine in preferences:
                    r["compliance"]["score"] = min(1.0, r["compliance"]["score"] + 0.1)

        scored.sort(key=lambda r: r["compliance"]["score"], reverse=True)

        # 3. 使用 LLM 智能配餐
        plan = self._llm_plan_meals(scored, user_profile, date)
        return plan

    def plan_weekly_meals(self,
                           candidate_recipes: List[Dict],
                           user_profile: Dict,
                           days: int = 7) -> WeeklyPlan:
        """
        规划一周食谱
        Args:
            candidate_recipes: 候选菜谱列表
            user_profile: 用户画像
            days: 天数
        Returns:
            WeeklyPlan 一周食谱方案
        """
        from datetime import date as dt, timedelta

        daily_plans = []
        seen_recipes = set()  # 避免重复推荐

        constitutions = user_profile.get("constitutions", [])
        conditions = user_profile.get("conditions", [])
        restrictions = user_profile.get("restrictions", [])

        # 合规排序
        scored = self.compliance.filter_recipes(
            candidate_recipes, constitutions, conditions, restrictions
        )

        for day_offset in range(days):
            day_date = (dt.today() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            day_name = f"第{day_offset + 1}天 ({day_date})"

            # 当天可用的候选（排除已推荐过的）
            available = [r for r in scored if r.get("name") not in seen_recipes]
            if not available:
                available = scored  # 重新使用全部

            # 每日推荐 2-3 个菜谱
            top_choices = available[:8]

            daily = self._plan_single_day(top_choices, user_profile, day_name)

            for meal in daily.meals:
                seen_recipes.add(meal.recipe_name)

            daily_plans.append(daily)

        # 生成总结
        summary = self._generate_weekly_summary(daily_plans, user_profile)

        return WeeklyPlan(
            start_date=(dt.today()).strftime("%Y-%m-%d"),
            end_date=(dt.today() + timedelta(days=days - 1)).strftime("%Y-%m-%d"),
            daily_plans=daily_plans,
            overall_summary=summary
        )

    def _plan_single_day(self, recipes: List[Dict], user_profile: Dict,
                          date_label: str) -> DailyPlan:
        """规划单天膳食"""
        meals = []
        total_score = 0.0

        breakfast_picks = [r for r in recipes[:5] if self._is_breakfast(r)]
        main_picks = [r for r in recipes[:5] if not self._is_breakfast(r)]

        # 早餐
        if breakfast_picks:
            r = breakfast_picks[0]
            meals.append(MealPlan(
                meal_type="早餐",
                recipe_name=r.get("name", "未知"),
                recipe_node_id=str(r.get("nodeId", "")),
                ingredients=r.get("ingredient_names", r.get("ingredients", [])),
                reason="营养丰富，适合开启一天",
                compliance_score=r.get("compliance", {}).get("score", 1.0),
                warnings=r.get("compliance", {}).get("warnings", [])
            ))

        # 午餐和晚餐（不重复）
        if len(main_picks) >= 2:
            lunch = main_picks[0]
            dinner = main_picks[1]
        elif len(main_picks) == 1:
            lunch = main_picks[0]
            dinner = main_picks[0]
        else:
            lunch = dinner = None

        for meal_type, pick in [("午餐", lunch), ("晚餐", dinner)]:
            if pick:
                meals.append(MealPlan(
                    meal_type=meal_type,
                    recipe_name=pick.get("name", "未知"),
                    recipe_node_id=str(pick.get("nodeId", "")),
                    ingredients=pick.get("ingredient_names", pick.get("ingredients", [])),
                    reason="营养搭配均衡" if meal_type == "午餐" else "清淡适口，有助于消化",
                    compliance_score=pick.get("compliance", {}).get("score", 1.0),
                    warnings=pick.get("compliance", {}).get("warnings", [])
                ))

        if meals:
            total_score = sum(m.compliance_score for m in meals) / len(meals)

        return DailyPlan(
            date=date_label,
            meals=meals,
            total_score=round(total_score, 2),
            summary=self._summarize_day(meals)
        )

    def _llm_plan_meals(self, recipes: List[Dict], user_profile: Dict,
                         date: str) -> DailyPlan:
        """使用 LLM 进行智能配餐"""
        # 构造候选菜谱描述
        recipe_descriptions = []
        for i, r in enumerate(recipes[:15]):
            name = r.get("name", f"菜谱{i}")
            category = r.get("category", "其他")
            cuisine = r.get("cuisineType", "")
            ingredients = r.get("ingredient_names", r.get("ingredients", []))
            score = r.get("compliance", {}).get("score", 1.0)
            warnings = r.get("compliance", {}).get("warnings", [])
            desc = f"{i + 1}. {name} [类别:{category} 菜系:{cuisine} 适宜度:{score} 食材:{','.join(ingredients[:5] if ingredients else [])}"
            if warnings:
                desc += f" 注意:{';'.join(warnings[:2])}"
            desc += "]"
            recipe_descriptions.append(desc)

        profile_desc = self.compliance.generate_compliance_report(
            user_profile.get("constitutions"),
            user_profile.get("conditions"),
            user_profile.get("restrictions")
        )

        prompt = f"""作为一个专业的营养膳食顾问，请根据以下信息为用户规划一日三餐：

【用户健康档案】
{profile_desc}

【候选菜谱】（已按适宜度排序）
{"\n".join(recipe_descriptions)}

请按JSON格式返回配餐方案：
{{
    "meals": [
        {{"meal_type": "早餐", "recipe_index": 1, "reason": "选择理由"}},
        {{"meal_type": "午餐", "recipe_index": 3, "reason": "选择理由"}},
        {{"meal_type": "晚餐", "recipe_index": 5, "reason": "选择理由"}}
    ],
    "summary": "整体配餐说明"
}}

要求：
1. 优先选择适宜度高的菜谱
2. 三餐之间避免重复
3. 考虑营养均衡（荤素搭配、避免连续高油高脂）
4. 早餐优先选易消化、有主食配早餐类型的菜谱
5. recipe_index 从1开始

只返回JSON，不要额外文字。"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
        except Exception as e:
            logger.error(f"LLM 配餐规划失败: {e}，使用规则规划")
            return self._rule_based_plan(recipes, user_profile, date)

        # 构建 DailyPlan
        meals = []
        for meal in result.get("meals", []):
            idx = meal.get("recipe_index", 1) - 1
            if 0 <= idx < len(recipes):
                r = recipes[idx]
                meals.append(MealPlan(
                    meal_type=meal.get("meal_type", "正餐"),
                    recipe_name=r.get("name", "未知"),
                    recipe_node_id=str(r.get("nodeId", "")),
                    ingredients=r.get("ingredient_names", r.get("ingredients", [])),
                    reason=meal.get("reason", ""),
                    compliance_score=r.get("compliance", {}).get("score", 1.0),
                    warnings=r.get("compliance", {}).get("warnings", [])
                ))

        total_score = sum(m.compliance_score for m in meals) / len(meals) if meals else 0

        return DailyPlan(
            date=date,
            meals=meals,
            total_score=round(total_score, 2),
            summary=result.get("summary", "")
        )

    def _rule_based_plan(self, recipes: List[Dict], user_profile: Dict,
                          date: str) -> DailyPlan:
        """规则配餐（LLM 不可用时的降级方案）"""
        return self._plan_single_day(recipes, user_profile, date)

    def _is_breakfast(self, recipe: Dict) -> bool:
        """判断是否为早餐类菜谱"""
        category = recipe.get("category", "")
        name = recipe.get("name", "")
        tags = recipe.get("tags", "")

        if category == "早餐":
            return True
        # 关键词判断
        breakfast_keywords = ["粥", "饼", "包", "糕", "卷", "粉", "饼", "馒头", "面包", "豆浆", "牛奶", "鸡蛋"]
        return any(kw in (name + tags) for kw in breakfast_keywords)

    def _summarize_day(self, meals: List[MealPlan]) -> str:
        """汇总一日配餐"""
        if not meals:
            return "暂无配餐方案"
        names = [f"{m.meal_type}: {m.recipe_name}" for m in meals]
        return " | ".join(names)

    def _generate_weekly_summary(self, daily_plans: List[DailyPlan],
                                   user_profile: Dict) -> str:
        """生成一周配餐总结"""
        constitutions = user_profile.get("constitutions", [])
        conditions = user_profile.get("conditions", [])
        restrictions = user_profile.get("restrictions", [])

        recipe_names = []
        for dp in daily_plans:
            for meal in dp.meals:
                recipe_names.append(meal.recipe_name)

        avg_score = sum(dp.total_score for dp in daily_plans) / len(daily_plans) if daily_plans else 0

        user_desc = ""
        if constitutions:
            user_desc += f"针对您的{','.join(constitutions)}体质，"
        if conditions:
            user_desc += f"兼顾{','.join(conditions)}的健康需求，"
        if restrictions:
            user_desc += f"已排除{','.join(restrictions)}禁忌，"

        summary = (
            f"{user_desc}本周为您规划了 {len(daily_plans)} 天共 {len(recipe_names)} 道菜谱。"
            f"综合适宜度评分 {avg_score:.1f}/1.0。"
            f"建议根据实际感受灵活调整，如有不适请咨询专业营养师。"
        )
        return summary
