"""
Phase 2 & 3 集成测试脚本 (Windows 兼容版)
测试 SQLite 用户画像、Redis 会话管理、饮食合规检查、配餐规划
"""

import os
import sys
import json
import uuid
import logging

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger("TestSuite")

from dotenv import load_dotenv
load_dotenv()

from config import DEFAULT_CONFIG

PASS = "[PASS]"
FAIL = "[FAIL]"


# ============ Test 1: SQLite  ============
def test_user_profile_manager():
    print("\n" + "=" * 60)
    print("Test 1: SQLite UserProfileManager")
    print("=" * 60)

    from rag_modules.user_profile import UserProfileManager

    mgr = UserProfileManager(DEFAULT_CONFIG.sqlite_db_path)

    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    profile = mgr.create_user(
        user_id=user_id, name="TestUser-ZS",
        constitutions=["痰湿质", "气虚质"],
        conditions=["高血压"],
        restrictions=["海鲜过敏"],
        preferences=["川菜", "粤菜"]
    )
    assert profile.user_id == user_id
    print(f"{PASS} Created: {profile.name} ({profile.user_id})")

    loaded = mgr.get_profile(user_id)
    assert loaded is not None
    assert "痰湿质" in loaded.constitutions
    print(f"{PASS} Loaded: constitutions={loaded.constitutions}")

    mgr.update_constitutions(user_id, ["湿热质", "阴虚质"])
    updated = mgr.get_profile(user_id)
    assert "湿热质" in updated.constitutions
    print(f"{PASS} Updated constitutions: {updated.constitutions}")

    log_id = mgr.log_meal(user_id, "午餐", "清蒸鲈鱼", "201001001", rating=4)
    assert log_id > 0
    mgr.log_meal(user_id, "晚餐", "蒜蓉西兰花", "201001002", rating=5)
    meals = mgr.get_recent_meals(user_id)
    assert len(meals) >= 2
    print(f"{PASS} Meal records: {len(meals)}, latest: {meals[0]['recipe_name']}")

    mgr.log_feedback(user_id, "推荐菜", "清蒸鲈鱼", rating=5)
    stats = mgr.get_feedback_stats(user_id)
    print(f"{PASS} Feedback stats: {stats}")

    users = mgr.list_all_users()
    assert len(users) >= 1
    print(f"{PASS} User list: {len(users)} users")

    mgr.delete_profile(user_id)
    assert mgr.get_profile(user_id) is None
    print(f"{PASS} Cleanup OK")
    print(f"{PASS} Test 1 PASSED\n")
    return True


# ============ Test 2: DietaryCompliance ============
def test_dietary_compliance():
    print("=" * 60)
    print("Test 2: DietaryComplianceModule")
    print("=" * 60)

    from rag_modules.dietary_compliance import DietaryComplianceModule

    knowledge_path = os.path.join(BASE_DIR, "data", "dietary_knowledge.json")
    dm = DietaryComplianceModule(knowledge_path)

    forbidden = dm.get_forbidden_ingredients(
        constitutions=["痰湿质"], conditions=["糖尿病"]
    )
    assert len(forbidden) > 0
    print(f"{PASS} Forbidden({len(forbidden)}): {list(forbidden)[:5]}...")

    recommended = dm.get_recommended_ingredients(conditions=["高血压"])
    assert len(recommended) > 0
    print(f"{PASS} Recommended({len(recommended)}): {list(recommended)[:5]}...")

    result = dm.check_recipe_compliance(
        "红烧肉", ["猪肉", "冰糖", "酱油", "生姜", "料酒", "食用油"],
        constitutions=["痰湿质"], conditions=["高血压", "糖尿病"]
    )
    assert not result.is_compliant
    print(f"{PASS} RedBraisedPork: compliant={result.is_compliant}, score={result.score}")
    print(f"   Warnings: {result.warnings[:3]}")

    result2 = dm.check_recipe_compliance(
        "凉拌芹菜", ["芹菜", "蒜末", "香醋", "麻油", "盐"],
        conditions=["高血压"]
    )
    assert result2.is_compliant, f"Expected compliant, got score={result2.score}"
    print(f"{PASS} CelerySalad: compliant={result2.is_compliant}, score={result2.score}")

    result3 = dm.check_recipe_compliance(
        "咖喱炒蟹", ["青蟹", "咖喱块", "洋葱", "椰浆", "鸡蛋", "大蒜", "食用油"],
        restrictions=["海鲜过敏"]
    )
    assert not result3.is_compliant
    print(f"{PASS} Seafood allergy: compliant={result3.is_compliant}, forbidden={result3.forbidden_ingredients}")

    report = dm.generate_compliance_report(
        constitutions=["痰湿质", "气虚质"], conditions=["高血脂"], restrictions=["海鲜过敏"]
    )
    print(f"{PASS} Report:\n{report}")

    cl = dm.get_constitution_list()
    hl = dm.get_condition_list()
    rl = dm.get_restriction_list()
    print(f"{PASS} Supports: {len(cl)} constitutions, {len(hl)} conditions, {len(rl)} restrictions")
    print(f"{PASS} Test 2 PASSED\n")
    return True


# ============ Test 3: SessionManager ============
def test_session_manager():
    print("=" * 60)
    print("Test 3: SessionManager (Redis/Memory)")
    print("=" * 60)

    from rag_modules.session_manager import SessionManager, HAS_REDIS

    sm = SessionManager(
        host=DEFAULT_CONFIG.redis_host, port=DEFAULT_CONFIG.redis_port,
        ttl=DEFAULT_CONFIG.session_ttl
    )

    mode = "Redis" if (HAS_REDIS and sm._use_redis) else "Memory(fallback)"
    print(f"   Mode: {mode}")

    session_id = f"session_test_{uuid.uuid4().hex[:8]}"
    session = sm.create_session(
        session_id=session_id, user_id="test_user_001",
        user_profile={"constitutions": ["气虚质"], "conditions": ["糖尿病"]}
    )
    assert session["session_id"] == session_id
    print(f"{PASS} Created session: {session_id}")

    sm.add_message(session_id, "user", "今天吃什么好？")
    sm.add_message(session_id, "assistant", "根据您的体质，推荐清淡饮食...")
    sm.add_message(session_id, "user", "有什么具体推荐吗？")

    history = sm.get_chat_history(session_id)
    assert len(history) == 3, f"Expected 3, got {len(history)}"
    print(f"{PASS} Chat history: {len(history)} messages")

    sm.set_context(session_id, "last_recommendation", "清蒸鲈鱼")
    ctx = sm.get_context(session_id, "last_recommendation")
    assert ctx == "清蒸鲈鱼"
    print(f"{PASS} Context: last_recommendation = {ctx}")

    assert sm.session_exists(session_id)
    print(f"{PASS} Session exists check OK")

    sm.delete_session(session_id)
    assert not sm.session_exists(session_id)
    print(f"{PASS} Session deleted OK")

    sm.close()
    print(f"{PASS} Test 3 PASSED\n")
    return True


# ============ Test 4: MealPlanner ============
def test_meal_planner():
    print("=" * 60)
    print("Test 4: MealPlanner")
    print("=" * 60)

    from rag_modules.dietary_compliance import DietaryComplianceModule
    from rag_modules.meal_planner import MealPlanner

    knowledge_path = os.path.join(BASE_DIR, "data", "dietary_knowledge.json")
    dm = DietaryComplianceModule(knowledge_path)

    # Mock OpenAI client for meal_planner LLM calls
    class MockCompletions:
        @staticmethod
        def create(model, messages, temperature, max_tokens):
            class Choice:
                class Message:
                    content = json.dumps({
                        "meals": [
                            {"meal_type": "早餐", "recipe_index": 1, "reason": "清淡易消化"},
                            {"meal_type": "午餐", "recipe_index": 3, "reason": "营养均衡"},
                            {"meal_type": "晚餐", "recipe_index": 5, "reason": "低脂健康"}
                        ],
                        "summary": "综合配餐方案"
                    })
            class Response:
                choices = [Choice()]
            return Response()

    class MockChat:
        completions = MockCompletions()

    class MockLLMClient:
        chat = MockChat()

    planner = MealPlanner(dm, MockLLMClient())

    candidates = [
        {"name": "小米粥", "nodeId": "101", "category": "早餐", "cuisineType": "",
         "ingredient_names": ["小米", "水"], "ingredients": ["小米", "水"]},
        {"name": "蒸鸡蛋羹", "nodeId": "102", "category": "早餐",
         "ingredient_names": ["鸡蛋", "水"], "ingredients": ["鸡蛋", "水"]},
        {"name": "清蒸鲈鱼", "nodeId": "103", "category": "水产", "cuisineType": "粤菜",
         "ingredient_names": ["鲈鱼", "葱", "姜"], "ingredients": ["鲈鱼", "葱", "姜"]},
        {"name": "蒜蓉西兰花", "nodeId": "104", "category": "素菜",
         "ingredient_names": ["西兰花", "蒜"], "ingredients": ["西兰花", "蒜"]},
        {"name": "红烧肉", "nodeId": "105", "category": "荤菜",
         "ingredient_names": ["猪肉", "冰糖", "酱油"], "ingredients": ["猪肉", "冰糖", "酱油"]},
        {"name": "冬瓜排骨汤", "nodeId": "106", "category": "汤类",
         "ingredient_names": ["冬瓜", "排骨"], "ingredients": ["冬瓜", "排骨"]},
        {"name": "凉拌黄瓜", "nodeId": "107", "category": "素菜",
         "ingredient_names": ["黄瓜", "蒜"], "ingredients": ["黄瓜", "蒜"]},
        {"name": "西红柿炒鸡蛋", "nodeId": "108", "category": "素菜",
         "ingredient_names": ["西红柿", "鸡蛋"], "ingredients": ["西红柿", "鸡蛋"]},
    ]

    user_profile = {
        "constitutions": ["痰湿质"], "conditions": [], "restrictions": [], "cuisine_preferences": ["粤菜"]
    }

    daily = planner.plan_daily_meals(candidates, user_profile, "2026-05-25")
    assert daily is not None
    assert len(daily.meals) >= 1
    print(f"{PASS} Daily plan: {len(daily.meals)} meals, score={daily.total_score}")
    for m in daily.meals:
        print(f"   {m.meal_type}: {m.recipe_name} (score={m.compliance_score:.2f})")

    weekly = planner.plan_weekly_meals(candidates, user_profile, days=3)
    assert weekly is not None
    assert len(weekly.daily_plans) == 3
    print(f"{PASS} Weekly plan: {len(weekly.daily_plans)} days")
    print(f"   Summary: {weekly.overall_summary[:80]}...")

    # Verify compliance filtering sorts correctly
    filtered = dm.filter_recipes(candidates, constitutions=["痰湿质"], conditions=["糖尿病"])
    pork = next((r for r in filtered if r["name"] == "红烧肉"), None)
    fish = next((r for r in filtered if r["name"] == "清蒸鲈鱼"), None)
    if pork and fish:
        assert pork["compliance"]["score"] < fish["compliance"]["score"], \
            f"Pork({pork['compliance']['score']}) should be below Fish({fish['compliance']['score']})"
        print(f"{PASS} Ranking: Pork({pork['compliance']['score']}) < Fish({fish['compliance']['score']})")

    print(f"{PASS} Test 4 PASSED\n")
    return True


# ============ Test 5: Integration ============
def test_integration():
    print("=" * 60)
    print("Test 5: Full Integration")
    print("=" * 60)

    from rag_modules.user_profile import UserProfileManager
    from rag_modules.dietary_compliance import DietaryComplianceModule
    from rag_modules.session_manager import SessionManager

    mgr = UserProfileManager(DEFAULT_CONFIG.sqlite_db_path)
    knowledge_path = os.path.join(BASE_DIR, "data", "dietary_knowledge.json")
    dm = DietaryComplianceModule(knowledge_path)
    sm = SessionManager(host=DEFAULT_CONFIG.redis_host, port=DEFAULT_CONFIG.redis_port, ttl=60)

    user_id = f"full_test_{uuid.uuid4().hex[:8]}"
    profile = mgr.create_user(
        user_id=user_id, name="LiSi",
        constitutions=["痰湿质", "气虚质"],
        conditions=["高血脂"],
        restrictions=["牛奶不耐受/乳糖不耐"],
        preferences=["粤菜", "素菜"]
    )
    print(f"{PASS} 1. Registered: {profile.name}")

    report = dm.generate_compliance_report(
        profile.constitutions, profile.health_conditions, profile.dietary_restrictions
    )
    print(f"{PASS} 2. Compliance report generated")

    session_id = f"se_{uuid.uuid4().hex[:8]}"
    sm.create_session(session_id, user_id, profile.to_dict())
    print(f"{PASS} 3. Session: {session_id}")

    result = dm.check_recipe_compliance(
        "咖喱炒蟹", ["青蟹", "洋葱", "椰浆", "鸡蛋", "大蒜"],
        profile.constitutions, profile.health_conditions, profile.dietary_restrictions
    )
    print(f"{PASS} 4. Recipe check: compliant={result.is_compliant}, score={result.score}")

    mgr.log_feedback(user_id, "推荐一个菜", "Done", rating=4)
    stats = mgr.get_feedback_stats(user_id)
    print(f"{PASS} 5. Feedback: {stats}")

    fb = dm.get_forbidden_ingredients(profile.constitutions, profile.health_conditions, profile.dietary_restrictions)
    rc = dm.get_recommended_ingredients(profile.constitutions, profile.health_conditions, profile.dietary_restrictions)
    print(f"{PASS} 6. Forbidden:{len(fb)}, Recommended:{len(rc)}")

    sm.delete_session(session_id)
    mgr.delete_profile(user_id)
    sm.close()
    print(f"{PASS} Test 5 PASSED\n")
    return True


# ============ Main ============
def run_all_tests():
    tests = [
        ("SQLite UserProfile", test_user_profile_manager),
        ("DietaryCompliance", test_dietary_compliance),
        ("SessionManager", test_session_manager),
        ("MealPlanner", test_meal_planner),
        ("Integration", test_integration),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback
            print(f"\n[FAIL] {name} test failed!")
            traceback.print_exc()
            print()

    print("=" * 60)
    print(f"Results: {passed} passed / {failed} failed / {passed + failed} total")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
