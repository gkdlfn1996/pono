from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List
import asyncio

from ..shotgrid.shotgrid_api import async_api
from ..shotgrid import shotgrid_cache_manager, shotgrid_authenticator
from .. import version_view
from .auth_router import get_shotgrid_instance

router = APIRouter(
    prefix="/api/data",
    tags=["ShotGrid Data"],
)

@router.get("/projects")
async def get_projects(sg = Depends(get_shotgrid_instance)):
    """
    ShotGrid에서 모든 프로젝트 목록을 조회합니다.
    """
    return await async_api.get_projects(sg)

@router.get("/projects/{project_id}/pipeline-steps")
async def get_pipeline_steps_for_project(project_id: int, sg = Depends(get_shotgrid_instance)):
    """
    특정 프로젝트에 연결된 Pipeline Step 목록을 조회합니다.
    """
    return await async_api.get_pipeline_steps_for_project(sg, project_id)

@router.get("/versions")
async def get_versions_view(
    request: Request,
    project_id: int,
    pipeline_step: str,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    filters: str = None,
    use_cache: bool = False,
    sg=Depends(get_shotgrid_instance)
):
    all_versions = await shotgrid_cache_manager.get_or_create_versions_cache(
        sg, project_id, pipeline_step, async_api, use_cache, request
    )
    if all_versions is None:
        return

    view_data = version_view.process_view_data(
        all_versions, page, page_size, sort_by, sort_order, filters
    )
    return view_data

@router.post("/heavy-version-data")
async def get_heavyweight_data(
    version_ids: List[int],
    request: Request, # Request 객체를 받아 헤더에 접근
    project_id: int,
    pipeline_step: str,
    sg=Depends(get_shotgrid_instance)
):
    # TODO: 썸네일은 나중에 ShotGrid가 아닌 회사 서버에서 가져올 예정이므로,
    # 현재는 임시로 세션 토큰을 직접 파싱하여 Shotgun 인스턴스를 생성합니다.
    # 이 로직은 썸네일 소스가 변경되면 제거될 수 있습니다.
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    session_token = authorization.split(" ")[1]

    # 각 태스크에 독립적인 ShotGrid 인스턴스를 전달하여 SSL 에러 방지
    sg_thumb = shotgrid_authenticator.SessionTokenSG(session_token=session_token).sg
    sg_notes = shotgrid_authenticator.SessionTokenSG(session_token=session_token).sg

    thumbnail_task = async_api.get_thumbnails_by_ids(sg_thumb, version_ids)
    notes_task = async_api.get_notes_by_ids(sg_notes, version_ids)
    results = await asyncio.gather(thumbnail_task, notes_task)
    heavy_data = {"thumbnails": results[0], "notes": results[1]}
    shotgrid_cache_manager.update_cache_with_heavy_details(
        project_id, pipeline_step, heavy_data
    )
    return heavy_data