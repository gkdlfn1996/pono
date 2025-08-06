from fastapi import APIRouter, Depends, HTTPException, status, Header

from .. import shotgrid_service
from .auth_router import get_shotgrid_instance

router = APIRouter(
    prefix="/api",
    tags=["ShotGrid Data"],
)



@router.get("/projects")
async def get_projects(sg = Depends(get_shotgrid_instance)):
    """
    ShotGrid에서 모든 프로젝트 목록을 조회합니다.
    """
    return shotgrid_service.get_projects(sg)

@router.get("/projects/{project_id}/tasks")
async def get_tasks_for_project(project_id, sg = Depends(get_shotgrid_instance)):
    """
    특정 프로젝트에 연결된 Task 목록을 조회합니다.
    """
    return shotgrid_service.get_tasks_for_project(sg, int(project_id))

@router.get("/projects/{project_id}/tasks/{task_id}/versions")
async def get_versions_for_task(task_id, sg = Depends(get_shotgrid_instance)):
    """
    특정 Task에 연결된 Version 목록을 조회합니다.
    """
    return shotgrid_service.get_versions_for_task(sg, int(task_id))

# @router.get("/me")
# async def read_users_me(sg = Depends(get_shotgrid_instance)):
#     """
#     현재 로그인된 사용자의 정보를 반환합니다.
#     """
#     return shotgrid_service.get_current_user_info(sg)
