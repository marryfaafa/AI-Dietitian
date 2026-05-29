# AI Dietitian - 智能膳食健康顾问

基于图RAG（Retrieval-Augmented Generation）技术的智能膳食健康顾问系统，集成PaddleOCR多模态输入，为用户提供个性化的膳食建议和健康管理服务。

## 核心特性

### 多模态输入支持
- **PaddleOCR文字识别**：支持拍照识别食物标签、营养成分表、食谱等文字信息
- **图像识别**：智能识别食物图片，自动提取营养信息
- **语音输入**：支持语音交互，方便快捷

### 智能膳食管理
- **个性化推荐**：基于用户体质、健康状况、饮食偏好生成定制化膳食方案
- **膳食合规检查**：自动检测膳食方案是否符合用户的健康限制条件
- **营养分析**：详细分析每日营养摄入，提供均衡建议

### 图RAG技术架构
- **知识图谱**：基于Neo4j构建膳食营养知识图谱
- **向量检索**：使用Milvus实现高效的语义检索
- **混合检索**：结合传统检索和图RAG检索，提供精准答案
- **智能路由**：自动选择最适合的检索策略

## 技术栈

### 后端
- Python 3.9+
- Flask - Web框架
- Neo4j - 图数据库
- Milvus - 向量数据库
- Redis - 会话管理
- SQLite - 用户数据存储

### AI模型
- **PaddleOCR** - 多模态文字识别
- BAAI/bge-small-zh-v1.5 - 文本嵌入模型
- Kimi/Moonshot - 大语言模型

### 前端
- Vue 3 + TypeScript
- Vite - 构建工具

## 快速开始

### 环境准备

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 安装PaddleOCR（多模态输入支持）：
```bash
pip install paddlepaddle paddleocr
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，配置以下变量：
# MOONSHOT_API_KEY=your_api_key
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

4. 启动数据库服务：
```bash
# 启动Neo4j
# 启动Milvus
# 启动Redis
```

### 运行项目

1. 启动后端API服务：
```bash
python api_server.py
```

2. 启动前端开发服务器：
```bash
cd frontend2
npm install
npm run dev
```

3. 访问应用：打开浏览器访问 http://localhost:5173

## 项目结构

```
C9/
├── api_server.py          # Flask API后端
├── main.py               # 主程序入口
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── .env.example          # 环境变量示例
├── rag_modules/          # RAG核心模块
│   ├── graph_data_preparation.py    # 图数据准备
│   ├── graph_rag_retrieval.py       # 图RAG检索
│   ├── hybrid_retrieval.py          # 混合检索
│   ├── intelligent_query_router.py  # 智能查询路由
│   ├── dietary_compliance.py        # 膳食合规检查
│   ├── meal_planner.py             # 膳食计划生成
│   ├── user_profile.py             # 用户画像管理
│   └── session_manager.py          # 会话管理
├── frontend2/            # Vue前端应用
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── data/                 # 数据目录
    └── dietary_knowledge.json  # 膳食知识库
```

## API接口

### 用户认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 健康管理
- `GET /api/health/options` - 获取健康选项（体质、病症、限制）
- `POST /api/health/profile` - 更新用户健康档案

### 膳食咨询
- `POST /api/chat` - 智能膳食咨询对话
- `POST /api/meal/plan` - 生成膳食计划
- `POST /api/meal/check` - 膳食合规检查

### 多模态输入
- `POST /api/ocr/recognize` - PaddleOCR文字识别
- `POST /api/image/analyze` - 食物图片分析

## 使用示例

### PaddleOCR识别食物标签
```python
import requests

# 上传食物标签图片进行OCR识别
with open("food_label.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/ocr/recognize",
        files={"image": f}
    )
    print(response.json())
```

### 智能膳食咨询
```python
import requests

# 发送膳食咨询请求
response = requests.post(
    "http://localhost:5000/api/chat",
    json={
        "message": "我最近血糖偏高，能推荐一些适合的早餐吗？",
        "session_id": "user_session_123"
    },
    headers={"Authorization": "Bearer your_token"}
)
print(response.json())
```

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

MIT License
