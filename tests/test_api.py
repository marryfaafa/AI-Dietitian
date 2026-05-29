"""
API Server Integration Test
测试所有 Flask API 端点
"""

import requests
import json
import uuid
import sys

BASE = "http://localhost:5000"
uid = f"api_test_{uuid.uuid4().hex[:8]}"
PASS = "[PASS]"
FAIL = "[FAIL]"

failed = 0

def check(name, condition, msg=""):
    global failed
    if condition:
        print(f"{PASS} {name}")
    else:
        print(f"{FAIL} {name}: {msg}")
        failed += 1

# Test 1: Health check
print("Test 1: Health Check")
r = requests.get(f"{BASE}/api/health")
check("GET /api/health", r.json()["status"] == "ok")

# Test 2: Load options
print("\nTest 2: Health Options")
r = requests.get(f"{BASE}/api/health/options")
d = r.json()
check("Constitutions loaded", len(d["constitutions"]) > 0)
check("Conditions loaded", len(d["conditions"]) > 0)
check("Restrictions loaded", len(d["restrictions"]) > 0)

# Test 3: Create user
print("\nTest 3: User Management")
r = requests.post(f"{BASE}/api/user/create", json={
    "user_id": uid, "name": "测试用户",
    "constitutions": ["气虚质"], "conditions": ["糖尿病"],
    "restrictions": ["海鲜过敏"], "preferences": ["素菜"]
})
check("Create user", r.json()["success"])

r = requests.get(f"{BASE}/api/user/{uid}")
check("Get user", r.json()["success"])

r = requests.get(f"{BASE}/api/user/{uid}/report")
check("Get report", r.json()["success"])

# Test 4: Compliance check
print("\nTest 4: Compliance Check")
r = requests.post(f"{BASE}/api/compliance/check", json={
    "recipe_name": "红烧肉", "ingredients": ["猪肉", "冰糖", "酱油"],
    "constitutions": ["痰湿质"], "conditions": ["糖尿病"], "restrictions": []
})
check("Compliance check", r.json()["success"])
check("Should be non-compliant", not r.json()["is_compliant"],
      f"Expected non-compliant, got score={r.json()['score']}")

# Test 5: Session
print("\nTest 5: Session Management")
sid = f"se_api_{uuid.uuid4().hex[:8]}"
r = requests.post(f"{BASE}/api/session/create", json={"session_id": sid, "user_id": uid})
check("Create session", r.json()["success"])

r = requests.post(f"{BASE}/api/session/{sid}/chat", json={
    "role": "user", "content": "今天吃什么？"
})
check("Save chat", r.json()["success"])

r = requests.get(f"{BASE}/api/session/{sid}/history")
check("Get history", r.json()["success"] and len(r.json()["history"]) > 0)

# Test 6: Meal planning
print("\nTest 6: Meal Planning")
candidates = [
    {"name":"清蒸鲈鱼","nodeId":"103","category":"水产","ingredient_names":["鲈鱼","葱"],"ingredients":["鲈鱼","葱"]},
    {"name":"小米粥","nodeId":"101","category":"早餐","ingredient_names":["小米","水"],"ingredients":["小米","水"]},
    {"name":"冬瓜薏米汤","nodeId":"106","category":"汤类","ingredient_names":["冬瓜","薏米"],"ingredients":["冬瓜","薏米"]},
]
r = requests.post(f"{BASE}/api/meal/plan/daily", json={
    "candidates": candidates,
    "user_profile": {"constitutions":["气虚质"],"conditions":[],"restrictions":[]}
})
check("Daily plan", r.json()["success"])
check("Has meals", len(r.json()["meals"]) > 0)

r = requests.post(f"{BASE}/api/meal/plan/weekly", json={
    "candidates": candidates,
    "user_profile": {"constitutions":["气虚质"]},
    "days": 3
})
check("Weekly plan", r.json()["success"])
check("3 days", len(r.json()["daily_plans"]) == 3)

print(f"\n{'='*40}")
print(f"Results: {7-failed} passed / {failed} failed")
sys.exit(0 if failed == 0 else 1)
