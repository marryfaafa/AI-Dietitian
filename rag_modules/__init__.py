"""
基于图数据库的RAG模块包 - 智能膳食健康顾问
注意: 部分模块有重型依赖(Neo4j/Milvus), 测试时请直接导入特定模块
"""

# 无外部依赖的模块 - 始终可用
from .dietary_compliance import DietaryComplianceModule
from .user_profile import UserProfileManager, UserProfile
from .session_manager import SessionManager

__all__ = [
    'DietaryComplianceModule',
    'UserProfileManager',
    'UserProfile',
    'SessionManager',
]

# 重型依赖模块 - 按需延迟导入
def _lazy_import():
    global GraphDataPreparationModule, MilvusIndexConstructionModule
    global HybridRetrievalModule, GenerationIntegrationModule
    global MealPlanner, DailyPlan, WeeklyPlan, MealPlan
    from .graph_data_preparation import GraphDataPreparationModule
    from .milvus_index_construction import MilvusIndexConstructionModule
    from .hybrid_retrieval import HybridRetrievalModule
    from .generation_integration import GenerationIntegrationModule
    from .meal_planner import MealPlanner, DailyPlan, WeeklyPlan, MealPlan

# 提供直接导入路径
__all__.extend([
    'GraphDataPreparationModule',
    'MilvusIndexConstructionModule',
    'HybridRetrievalModule',
    'GenerationIntegrationModule',
    'MealPlanner',
    'DailyPlan',
    'WeeklyPlan',
    'MealPlan',
])
