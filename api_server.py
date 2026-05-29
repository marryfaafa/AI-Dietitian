"""
智能膳食健康顾问 - Flask API 后端 (with Auth)
"""

import json
import uuid
import logging
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

from rag_modules.dietary_compliance import DietaryComplianceModule
from rag_modules.user_profile import UserProfileManager
from rag_modules.session_manager import SessionManager
from rag_modules.meal_planner import MealPlanner
from config import DEFAULT_CONFIG

compliance = DietaryComplianceModule(DEFAULT_CONFIG.dietary_knowledge_path)
profile_mgr = UserProfileManager(DEFAULT_CONFIG.sqlite_db_path)
session_mgr = SessionManager(host=DEFAULT_CONFIG.redis_host, port=DEFAULT_CONFIG.redis_port, ttl=DEFAULT_CONFIG.session_ttl)

meal_planner = None


def get_meal_planner():
    global meal_planner
    if meal_planner is None:
        import os
        from openai import OpenAI
        api_key = os.getenv("MOONSHOT_API_KEY")
        client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1") if api_key else None
        meal_planner = MealPlanner(compliance, client)
    return meal_planner


# ============ Auth Decorator ============
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        if not token:
            return jsonify({"success": False, "error": "请先登录"}), 401
        user_id = profile_mgr.verify_token(token)
        if not user_id:
            return jsonify({"success": False, "error": "登录已过期，请重新登录"}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated


# ============ Auth API ============
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip() or username
    if not username or len(username) < 2:
        return jsonify({"success": False, "error": "用户名至少2个字符"}), 400
    if not password or len(password) < 4:
        return jsonify({"success": False, "error": "密码至少4个字符"}), 400
    result = profile_mgr.register(username, password, name)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 409


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "error": "请输入用户名和密码"}), 400
    result = profile_mgr.login(username, password)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 401


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def auth_me():
    profile = profile_mgr.get_profile(g.user_id)
    return jsonify({"success": True, "user_id": g.user_id, "profile": profile.to_dict() if profile else {}})


# ============ Health Options ============
@app.route("/api/health/options", methods=["GET"])
def health_options():
    return jsonify({
        "constitutions": compliance.get_constitution_list(),
        "conditions": compliance.get_condition_list(),
        "restrictions": compliance.get_restriction_list()
    })


# ============ User Profile ============
@app.route("/api/user/profile", methods=["GET"])
@require_auth
def get_profile():
    profile = profile_mgr.get_profile(g.user_id)
    if profile:
        return jsonify({"success": True, "profile": profile.to_dict()})
    return jsonify({"success": False, "error": "用户不存在"}), 404


@app.route("/api/user/profile", methods=["PUT"])
@require_auth
def update_profile():
    data = request.json or {}
    if "constitutions" in data:
        profile_mgr.update_constitutions(g.user_id, data["constitutions"])
    if "conditions" in data:
        profile_mgr.update_conditions(g.user_id, data["conditions"])
    if "restrictions" in data:
        profile_mgr.update_restrictions(g.user_id, data["restrictions"])
    # Update name if provided
    if "name" in data:
        try:
            with profile_mgr._get_connection() as conn:
                conn.execute("UPDATE user_profiles SET name=?, updated_at=? WHERE user_id=?",
                            (data["name"], __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"), g.user_id))
                conn.commit()
        except:
            pass
    return jsonify({"success": True})


@app.route("/api/user/report", methods=["GET"])
@require_auth
def user_report():
    profile = profile_mgr.get_profile(g.user_id)
    if not profile:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    report = compliance.generate_compliance_report(
        profile.constitutions, profile.health_conditions, profile.dietary_restrictions
    )
    stats = profile_mgr.get_feedback_stats(g.user_id)
    recent = profile_mgr.get_recent_meals(g.user_id, days=7)
    return jsonify({"success": True, "report": report, "stats": stats, "recent_meals": recent})


@app.route("/api/user/meal", methods=["POST"])
@require_auth
def log_meal():
    """记录用餐"""
    data = request.json or {}
    meal_type = data.get("meal_type", "正餐")
    recipe_name = data.get("recipe_name", "").strip()
    recipe_node_id = str(data.get("recipe_node_id", ""))
    rating = int(data.get("rating", 0))

    if not recipe_name:
        return jsonify({"success": False, "error": "请输入菜名"}), 400

    log_id = profile_mgr.log_meal(g.user_id, meal_type, recipe_name, recipe_node_id, rating)
    if log_id > 0:
        return jsonify({"success": True, "log_id": log_id})
    return jsonify({"success": False, "error": "记录失败"}), 500


# ============ Compliance Check ============
@app.route("/api/compliance/check", methods=["POST"])
@require_auth
def check_compliance():
    data = request.json or {}
    profile = profile_mgr.get_profile(g.user_id)
    if not profile:
        return jsonify({"success": False, "error": "请先完善健康画像"}), 400
    result = compliance.check_recipe_compliance(
        recipe_name=data.get("recipe_name", ""),
        recipe_ingredients=data.get("ingredients", []),
        constitutions=profile.constitutions,
        conditions=profile.health_conditions,
        restrictions=profile.dietary_restrictions
    )
    return jsonify({
        "success": True,
        "is_compliant": result.is_compliant, "score": result.score,
        "reasons": result.reasons, "warnings": result.warnings,
        "forbidden_ingredients": result.forbidden_ingredients,
        "suitable_ingredients": result.suitable_ingredients
    })


# ============ Meal Planning ============
@app.route("/api/meal/plan/daily", methods=["POST"])
@require_auth
def plan_daily():
    data = request.json or {}
    profile = profile_mgr.get_profile(g.user_id)
    planner = get_meal_planner()
    daily_plan = planner.plan_daily_meals(
        data.get("candidates", []),
        {
            "constitutions": profile.constitutions if profile else [],
            "conditions": profile.health_conditions if profile else [],
            "restrictions": profile.dietary_restrictions if profile else [],
            "cuisine_preferences": profile.cuisine_preferences if profile else [],
        },
        data.get("date", "今日")
    )
    return jsonify({
        "success": True, "date": daily_plan.date,
        "total_score": daily_plan.total_score, "summary": daily_plan.summary,
        "meals": [{"meal_type": m.meal_type, "recipe_name": m.recipe_name,
                    "recipe_node_id": m.recipe_node_id, "reason": m.reason,
                    "compliance_score": m.compliance_score, "warnings": m.warnings}
                  for m in daily_plan.meals]
    })


@app.route("/api/meal/plan/weekly", methods=["POST"])
@require_auth
def plan_weekly():
    data = request.json or {}
    profile = profile_mgr.get_profile(g.user_id)
    planner = get_meal_planner()
    weekly = planner.plan_weekly_meals(
        data.get("candidates", []),
        {
            "constitutions": profile.constitutions if profile else [],
            "conditions": profile.health_conditions if profile else [],
            "restrictions": profile.dietary_restrictions if profile else [],
            "cuisine_preferences": profile.cuisine_preferences if profile else [],
        },
        data.get("days", 7)
    )
    return jsonify({
        "success": True,
        "start_date": weekly.start_date, "end_date": weekly.end_date,
        "overall_summary": weekly.overall_summary,
        "daily_plans": [{
            "date": dp.date, "total_score": dp.total_score, "summary": dp.summary,
            "meals": [{"meal_type": m.meal_type, "recipe_name": m.recipe_name,
                        "compliance_score": m.compliance_score, "reason": m.reason,
                        "warnings": m.warnings} for m in dp.meals]
        } for dp in weekly.daily_plans]
    })


# ============ Session / Chat ============
@app.route("/api/session/create", methods=["POST"])
@require_auth
def create_session():
    data = request.json or {}
    profile = profile_mgr.get_profile(g.user_id)
    session_id = data.get("session_id", f"se_{uuid.uuid4().hex[:10]}")
    session = session_mgr.create_session(
        session_id=session_id, user_id=g.user_id,
        user_profile=profile.to_dict() if profile else {}
    )
    profile_mgr.save_session(session_id, g.user_id)
    return jsonify({"success": True, "session_id": session_id})


@app.route("/api/session/list", methods=["GET"])
@require_auth
def list_sessions():
    sessions = profile_mgr.get_user_sessions(g.user_id)
    return jsonify({"success": True, "sessions": sessions})


@app.route("/api/session/<session_id>/chat", methods=["POST"])
@require_auth
def chat_message(session_id):
    data = request.json or {}
    role = data.get("role", "user")
    content = data.get("content", "")
    session_mgr.add_message(session_id, role, content, data.get("metadata", {}))
    history = session_mgr.get_chat_history(session_id, recent_n=50)

    # 记录消息数 & 自动命名会话
    msg_count = len([m for m in history if m["role"] == "user"])
    profile_mgr.save_session(session_id, g.user_id, msg_count)
    if role == "user" and content:
        # 用用户首条消息做会话标题
        existing = profile_mgr.get_user_sessions(g.user_id)
        for s in existing:
            if s["session_id"] == session_id and s["title"] == "新对话":
                title = content[:30] + ("..." if len(content) > 30 else "")
                profile_mgr.update_session_title(session_id, title)
                break
    return jsonify({"success": True, "history": history})


@app.route("/api/session/<session_id>/history", methods=["GET"])
@require_auth
def chat_history(session_id):
    n = request.args.get("n", 50, type=int)
    return jsonify({"success": True, "history": session_mgr.get_chat_history(session_id, recent_n=n)})


@app.route("/api/session/<session_id>", methods=["DELETE"])
@require_auth
def delete_session(session_id):
    session_mgr.delete_session(session_id)
    profile_mgr.delete_session(session_id)
    return jsonify({"success": True})


# ============ LLM Chat (RAG + Redis cache) ============
import hashlib

# Neo4j 图数据库连接（懒加载）
_neo4j_driver = None

def get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase
        _neo4j_driver = GraphDatabase.driver(
            DEFAULT_CONFIG.neo4j_uri,
            auth=(DEFAULT_CONFIG.neo4j_user, DEFAULT_CONFIG.neo4j_password)
        )
    return _neo4j_driver


def rag_retrieve(query: str, profile_data: dict, top_k: int = 8) -> str:
    """从 Neo4j 知识图谱检索真实菜谱 + 合规检查"""
    driver = get_neo4j()
    constitutions = profile_data.get("constitutions", [])
    conditions = profile_data.get("health_conditions", [])
    restrictions = profile_data.get("dietary_restrictions", [])

    recipes = []
    try:
        with driver.session() as session:
            # 用全文索引 + 关键词匹配检索菜谱
            result = session.run("""
                CALL db.index.fulltext.queryNodes('recipe_fulltext_index', $query + '*')
                YIELD node, score
                WHERE node:Recipe
                RETURN node.nodeId as nodeId, node.name as name,
                       node.category as category, node.cuisineType as cuisine,
                       node.difficulty as difficulty, node.tags as tags,
                       node.description as description, score
                ORDER BY score DESC LIMIT $top_k
            """, {"query": query, "top_k": top_k})

            for record in result:
                # 获取食材列表
                ings = []
                ing_result = session.run("""
                    MATCH (:Recipe {nodeId: $rid})-[r:REQUIRES]->(i:Ingredient)
                    RETURN i.name as name, r.amount as amount, r.unit as unit
                """, {"rid": record["nodeId"]})
                for ing in ing_result:
                    ings.append(f"{ing['name']}({ing['amount']}{ing['unit'] or ''})")

                # 合规检查
                com = compliance.check_recipe_compliance(
                    record["name"], [ing.split('(')[0] for ing in ings],
                    constitutions, conditions, restrictions
                )

                recipes.append({
                    "name": record["name"],
                    "category": record["category"] or "",
                    "cuisine": record["cuisine"] or "",
                    "difficulty": record["difficulty"],
                    "tags": record["tags"] or "",
                    "description": record["description"] or "",
                    "ingredients": ings,
                    "score": round(record["score"], 2),
                    "compliant": com.is_compliant,
                    "compliance_score": com.score,
                    "warnings": com.warnings,
                })
    except Exception as e:
        logger.error(f"RAG 检索失败: {e}")
        return "（知识库检索暂时不可用）"

    if not recipes:
        # 降级：按分类/标签模糊搜索
        try:
            with driver.session() as session:
                keywords = [w for w in query.split() if len(w) >= 2]
                category_q = " OR ".join([f"r.category CONTAINS '{k}'" for k in keywords[:3]])
                tags_q = " OR ".join([f"r.tags CONTAINS '{k}'" for k in keywords[:3]])
                fallback = session.run(f"""
                    MATCH (r:Recipe) WHERE {category_q} OR {tags_q}
                    RETURN r.nodeId as nodeId, r.name as name, r.category as category,
                           r.cuisineType as cuisine, r.tags as tags
                    LIMIT {top_k}
                """).data()
                if fallback:
                    return "（找到相关菜谱但无合规数据，请检查检索词）"
        except:
            pass
        return "（知识库中未找到相关菜谱）"

    # 格式化检索结果
    parts = []
    for i, r in enumerate(recipes, 1):
        comp_tag = "✅" if r["compliant"] else "⚠️"
        parts.append(
            f"{i}. {comp_tag} {r['name']} "
            f"[{r['category']} | {r['cuisine']} | 难度{r['difficulty']}] "
            f"适宜度 {r['compliance_score']:.0%}\n"
            f"   食材: {', '.join(r['ingredients'][:5])}\n"
            f"   描述: {r['description'] or r['tags']}"
        )
        if r["warnings"]:
            parts.append(f"   ⚠️ 注意: {'; '.join(r['warnings'][:2])}")

    return "\n\n".join(parts)


@app.route("/api/chat/ask", methods=["POST"])
@require_auth
def chat_ask():
    data = request.json or {}
    question = data.get("question", "").strip()
    history = data.get("history", [])

    if not question:
        return jsonify({"success": False, "error": "请输入问题"}), 400

    # 1. 获取用户画像
    profile = profile_mgr.get_profile(g.user_id)
    profile_dict = {
        "constitutions": profile.constitutions if profile else [],
        "health_conditions": profile.health_conditions if profile else [],
        "dietary_restrictions": profile.dietary_restrictions if profile else [],
    }

    # 2. 构建缓存 key（含用户画像，不同用户不同缓存）
    cache_raw = f"{question}|{','.join(profile_dict['constitutions'])}|{','.join(profile_dict['conditions'])}|{','.join(profile_dict['restrictions'])}"
    cache_key = f"chat:{hashlib.md5(cache_raw.encode()).hexdigest()}"
    if session_mgr._use_redis and session_mgr._client:
        cached = session_mgr._client.get(cache_key)
        if cached:
            return jsonify({"success": True, "reply": cached, "cached": True})

    # 3. RAG 检索 — 从知识图谱获取真实菜谱
    rag_context = rag_retrieve(question, profile_dict)

    # 4. 用户健康档案
    profile_ctx = compliance.generate_compliance_report(
        profile_dict["constitutions"], profile_dict["conditions"], profile_dict["restrictions"]
    )

    # 5. 对话历史
    history_text = "\n".join([f"{h['role']}: {h['content']}" for h in (history or [])[-6:]])

    # 6. 调用 LLM（严格限定只能基于 RAG 检索结果回答）
    prompt = f"""你是膳食顾问，回答必须严格基于下方知识库检索结果，不得编造不存在的数据。

【知识库检索结果】
{rag_context}

【用户健康档案】
{profile_ctx}

【对话历史】
{history_text if history_text else '（无）'}

【用户问题】
{question}

要求：
1. 只推荐知识库中存在的菜谱（带 ✅ 标记的优先）
2. 标注菜谱的适宜度评分和注意事项
3. 如果知识库无结果，明确告知用户
4. 禁止凭空编造菜谱名或食材
5. 300字以内，直接回答"""

    try:
        import os
        from openai import OpenAI
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            return jsonify({"success": False, "error": "LLM 未配置"}), 503

        client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
        response = client.chat.completions.create(
            model=DEFAULT_CONFIG.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        reply = response.choices[0].message.content.strip()

        # 缓存
        if session_mgr._use_redis and session_mgr._client:
            session_mgr._client.setex(cache_key, 3600, reply)

        return jsonify({"success": True, "reply": reply, "cached": False})
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        # 降级：直接返回 RAG 检索结果
        return jsonify({
            "success": True,
            "reply": f"AI 服务暂不可用，以下为知识库匹配结果：\n\n{rag_context}\n\n补充：{profile_ctx}",
            "cached": False
        })


# ============ Health Check ============
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "redis": session_mgr._use_redis})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
