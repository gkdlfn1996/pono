# /backend/app/shotgrid_cache_manager.py

from typing import Dict, Any, List
from fastapi import Request
import time


# version_view_router에서 캐시 관련 로직을 이곳으로 이동
API_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 600  # 10분


async def get_or_create_versions_cache(
    sg: Any,
    project_id: int,
    pipeline_step: str,
    shotgrid_api_module: Any,
    use_cache: bool,
    request: Request
) -> List[Dict]:
    """
    캐시를 확인하고, 없으면 '가벼운' 버전 데이터를 조회하여 캐시를 생성한 후 반환합니다.
    """
    cache_key = f"{project_id}_{pipeline_step}"
    current_time = time.time()

    if use_cache and cache_key in API_CACHE and (current_time - API_CACHE[cache_key]["timestamp"]) < CACHE_TTL_SECONDS:
        print(f"Cache HIT for {cache_key}")
        return API_CACHE[cache_key]["data"]

    print(f"Cache MISS for {cache_key}. Fetching lightweight data...")
    # 캐시가 없으면 shotgrid_api 모듈을 통해 가벼운 데이터를 가져옴
    lightweight_versions = await shotgrid_api_module.get_lightweight_versions(
        sg, project_id, pipeline_step
    )

    # 그룹 리더 정보를 가져와서 버전에 추가하는 로직
    if lightweight_versions:
       # 1. 버전 목록에서 아티스트 ID 목록을 중복 없이 추출
       artist_id_set = set()
       for v in lightweight_versions:
           if v.get('user') and v['user'].get('id'):
               artist_id_set.add(v['user']['id'])
       artist_ids = list(artist_id_set)

       if artist_ids:
           # 2. 아티스트 ID 목록으로 그룹 리더 정보를 한 번에 조회
           leaders_by_artist = await shotgrid_api_module.get_group_leaders_for_artists(sg, artist_ids)

           # 3. 각 버전에 해당 아티스트의 그룹 리더 정보를 추가
           for version in lightweight_versions:
                artist_id = None
                user_info = version.get('user')
                if user_info:
                    artist_id = user_info.get('id')
                
                version['group_leaders'] = leaders_by_artist.get(artist_id, [])

    
    # 클라이언트 연결이 끊겼는지 확인
    if await request.is_disconnected():
        print(f"Client disconnected for {cache_key}, discarding results.")
        return None # None을 반환하여 후속 처리를 막음

    API_CACHE[cache_key] = {
        "timestamp": current_time,
        "data": lightweight_versions,
    }
    return lightweight_versions


def update_cache_with_heavy_details(
    project_id: int,
    pipeline_step: str,
    heavy_data: Dict[str, Any]
):
    """
    기존의 '가벼운 캐시'에 썸네일, 노트 등 '무거운' 정보를 추가하여 '완성된 캐시'로 만듭니다.
    """
    cache_key = f"{project_id}_{pipeline_step}"
    if cache_key not in API_CACHE:
        print(f"Cache for {cache_key} not found. Cannot update.")
        return

    # 성능을 위해 버전 ID를 키로 하는 맵을 생성
    version_map = {version['id']: version for version in API_CACHE[cache_key]['data']}

    # 썸네일 정보 업데이트
    for thumb_info in heavy_data.get("thumbnails", []):
        if thumb_info['id'] in version_map:
            version_map[thumb_info['id']]['image'] = thumb_info['image']

    # 노트 정보 업데이트
    for version_id, notes in heavy_data.get("notes", {}).items():
        # version_id가 문자열로 올 수 있으므로 정수형으로 변환
        version_id_int = int(version_id)
        if version_id_int in version_map:
            version_map[version_id_int]['notes'] = notes

