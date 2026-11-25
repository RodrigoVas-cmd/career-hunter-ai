from fastapi import APIRouter

from app.api.v1 import applications, auth, dashboard, jobs, notifications, profile, resumes, targeting

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(resumes.router)
api_router.include_router(targeting.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(notifications.router)
api_router.include_router(dashboard.router)
