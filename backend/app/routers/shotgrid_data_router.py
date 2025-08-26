from fastapi import APIRouter, Depends

from ..shotgrid_api import async_api
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
    return await async_api.get_projects(sg)

@router.get("/projects/{project_id}/tasks")
async def get_tasks_for_project(project_id, sg = Depends(get_shotgrid_instance)):
    """
    특정 프로젝트에 연결된 Task 목록을 조회합니다.
    """
    return await async_api.get_tasks_for_project(sg, int(project_id))

@router.get("/projects/{project_id}/pipeline-steps")
async def get_pipeline_steps_for_project(project_id: int, sg = Depends(get_shotgrid_instance)):
    """
    특정 프로젝트에 연결된 Pipeline Step 목록을 조회합니다.
    """
    return await async_api.get_pipeline_steps_for_project(sg, project_id)

# @router.get("/projects/{project_id}/tasks/{task_name}/versions")
# async def get_versions_for_task(project_id: int, task_name: str, sg = Depends(get_shotgrid_instance)):
#     """
#     특정 프로젝트와 태스크 이름에 연결된 Version 목록을 조회합니다.
#     """
#     return shotgrid_api.get_versions_for_task(sg, project_id, task_name)

@router.get("/projects/{project_id}/pipeline-steps/{pipeline_step_name}/versions")
async def get_versions_for_pipeline_step(project_id: int, pipeline_step_name: str, sg = Depends(get_shotgrid_instance)):
    """
    특정 프로젝트와 파이프라인 스텝에 연결된 Version 목록을 조회합니다.
    """
    return await async_api.get_versions_for_pipeline_step(sg, project_id, pipeline_step_name)