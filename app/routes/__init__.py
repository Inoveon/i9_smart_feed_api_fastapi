from fastapi import APIRouter

from app.routes import auth, campaigns, images, tablets, health, profile, metrics, views, activity, branches, stations, analytics, reports, admin, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(images.router, tags=["images"])  # Sem prefix, será incluído em campaigns
api_router.include_router(tablets.router, prefix="/tablets", tags=["tablets"])
api_router.include_router(profile.router, prefix="/auth", tags=["profile"])  # /auth/me
api_router.include_router(users.router, tags=["users"])  # /api/users - gerenciamento de usuários
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(views.router, prefix="/metrics", tags=["views"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(branches.router, tags=["branches"])
api_router.include_router(stations.router, tags=["stations"])
api_router.include_router(admin.router, tags=["admin"])  # Router admin sem prefix pois já tem /api/admin no router
api_router.include_router(health.router, prefix="/health", tags=["health"])

