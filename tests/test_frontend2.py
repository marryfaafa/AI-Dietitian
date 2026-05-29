"""
Frontend2 前后端集成测试
测试完整功能链路：注册 → 登录 → 画像 → 合规 → 配餐 → 会话
"""
import requests
import json
import uuid
import sys
import os

BASE = "http://localhost:5000"
username = f"ftest_{uuid.uuid4().hex[:6]}"
password = "test1234"
token = ""
passed = 0
failed = 0

def t(name, cond, msg=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {msg}")

# ========== Test 1: Register ==========
print("Test 1: User Registration")
r = requests.post(f"{BASE}/api/auth/register", json={"username": username, "password": password, "name": "测试用户"})
d = r.json()
t("Register success", d.get("success"), d.get("error"))
t("Token returned", d.get("token") is not None)
token = d.get("token", "")

# ========== Test 2: Login ==========
print("\nTest 2: User Login")
r = requests.post(f"{BASE}/api/auth/login", json={"username": username, "password": password})
d = r.json()
t("Login success", d.get("success"), d.get("error"))
t("Same user_id", d.get("user_id") == f"user_{username}")
token = d.get("token", token)
h = {"Authorization": f"Bearer {token}"}

# ========== Test 3: Auth Me ==========
print("\nTest 3: Auth Me")
r = requests.get(f"{BASE}/api/auth/me", headers=h)
d = r.json()
t("Auth me success", d.get("success"))
t("Has profile", d.get("profile") is not None)

# ========== Test 4: Health Options ==========
print("\nTest 4: Health Options")
r = requests.get(f"{BASE}/api/health/options")
d = r.json()
t("Constitutions", len(d["constitutions"]) == 9)
t("Conditions", len(d["conditions"]) == 6)
t("Restrictions", len(d["restrictions"]) == 10)

# ========== Test 5: Update Profile ==========
print("\nTest 5: Update Profile")
r = requests.put(f"{BASE}/api/user/profile", headers=h, json={
    "constitutions": ["气虚质", "痰湿质"],
    "conditions": ["高血压"],
    "restrictions": ["海鲜过敏"]
})
t("Update profile", r.json().get("success"))

r = requests.get(f"{BASE}/api/user/profile", headers=h)
d = r.json()
t("Get profile", d.get("success"))
t("Constitutions set", d["profile"].get("constitutions") == "气虚质,痰湿质")

# ========== Test 6: Compliance Check ==========
print("\nTest 6: Compliance Check")
r = requests.post(f"{BASE}/api/compliance/check", headers=h, json={
    "recipe_name": "红烧肉", "ingredients": ["猪肉", "冰糖", "酱油"]
})
d = r.json()
t("Check success", d.get("success"))
t("Should be non-compliant", not d.get("is_compliant"), f"score={d.get('score')}")
t("Has warnings", len(d.get("warnings", [])) > 0)

# ========== Test 7: Meal Planning ==========
print("\nTest 7: Meal Planning")
candidates = [
    {"name":"清蒸鲈鱼","nodeId":"103","category":"水产","ingredient_names":["鲈鱼","葱"],"ingredients":["鲈鱼","葱"]},
    {"name":"小米粥","nodeId":"101","category":"早餐","ingredient_names":["小米","水"],"ingredients":["小米","水"]},
]
r = requests.post(f"{BASE}/api/meal/plan/daily", headers=h, json={"candidates":candidates})
d = r.json()
t("Daily plan", d.get("success"))
t("Has meals", len(d.get("meals", [])) > 0)

r = requests.post(f"{BASE}/api/meal/plan/weekly", headers=h, json={"candidates":candidates,"days":3})
d = r.json()
t("Weekly plan", d.get("success"))
t("3 days", len(d.get("daily_plans", [])) == 3)

# ========== Test 8: Session & Chat ==========
print("\nTest 8: Session & Chat")
r = requests.post(f"{BASE}/api/session/create", headers=h, json={})
d = r.json()
sid = d.get("session_id","")
t("Session created", d.get("success") and sid != "")

r = requests.post(f"{BASE}/api/session/{sid}/chat", headers=h, json={"role":"user", "content":"吃什么好？"})
t("Send message", r.json().get("success"))

r = requests.get(f"{BASE}/api/session/{sid}/history", headers=h)
t("Get history", len(r.json().get("history",[])) > 0)

# ========== Test 9: Unauthorized ==========
print("\nTest 9: Unauthorized Access")
r = requests.get(f"{BASE}/api/user/profile")
t("401 without token", r.status_code == 401)

r = requests.get(f"{BASE}/api/user/profile", headers={"Authorization":"Bearer invalid"})
t("401 with invalid token", r.status_code == 401)

# ========== Test 10: Error Handling ==========
print("\nTest 10: Error Handling")
r = requests.post(f"{BASE}/api/compliance/check", headers=h, json={})
t("Missing params still returns JSON", isinstance(r.json(), dict))

r = requests.post(f"{BASE}/api/auth/login", json={"username":"x","password":""})
t("Empty password rejected", not r.json().get("success"))

print(f"\n{'='*50}")
print(f"Results: {passed} PASS / {failed} FAIL / {passed+failed} total")
print(f"{'='*50}")
sys.exit(0 if failed == 0 else 1)
