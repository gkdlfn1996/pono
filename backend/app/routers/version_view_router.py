# /backend/app/routers/version_view_router.py

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import time
import json
from operator import itemgetter
from .. import shotgrid_api
from .auth_router import get_shotgrid_instance

router = APIRouter(
    prefix="/api/view/versions",  # 이 라우터는 /api/view/versions 경로를 사용
    tags=["Version View"],
)

# --- 백엔드 인메모리 캐시 ---
API_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 600 # 10분

def _apply_sorting(data: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
    """
    데이터 목록에 다단계 정렬을 적용합니다. (내부 함수 정의 없음)
    """
    reverse = sort_order == 'desc'

    # 1단계: 정렬 기준값(_sort_value)을 각 항목에 추가
    for item in data:
        entity = item.get('entity')
        entity_type = entity.get('type') if entity else None
        sort_value = None

        if sort_by == 'version_name':
            sort_value = item.get('code')
        elif sort_by == 'created_at':
            sort_value = item.get('created_at')
        elif sort_by == 'shot_rnum':
            if entity_type == 'Shot':
                sort_value = item.get('entity.Shot.sg_rnum')
        elif sort_by == 'shot_name':
            if entity and entity_type == 'Shot':
                sort_value = entity.get('name')
        elif sort_by == 'asset_name':
            if entity and entity_type == 'Asset':
                sort_value = entity.get('name')
        
        item['_sort_value'] = sort_value

    # 2단계: 정렬 실행
    # 2-1. 주요 값으로 1차 정렬 (None 값을 항상 뒤로 보내는 로직)                               
    items_with_values = []
    items_with_nones = []
    for item in data:
        if item['_sort_value'] is None:
            items_with_nones.append(item)
        else:
            items_with_values.append(item)
    # 값이 있는 목록만 정렬
    items_with_values.sort(key=itemgetter('_sort_value'), reverse=reverse)                      
    sorted_by_value = items_with_values + items_with_nones
    # 2-2. 주요 타입으로 2차 안정 정렬
    primarySortType = None
    if sort_by.startswith('shot_'):
        primarySortType = 'Shot'
    elif sort_by.startswith('asset_'):
        primarySortType = 'Asset'

    if primarySortType:
        final_sorted = sorted(sorted_by_value, key=lambda item: 0 if item.get('entity', {}).get('type') == primarySortType else 1)
    else:
        final_sorted = sorted_by_value

    # 3단계: 임시 키(_sort_value) 제거
    for item in final_sorted:
        del item['_sort_value']

    return final_sorted


# --- 데이터 처리 기능이 통합된 엔드포인트 --- 

@router.get("/")
async def get_processed_versions(
    project_id: int,
    task_name: str,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    use_cache: bool = False, # 캐시 사용 여부 파라미터 (기본값: False)
    sg = Depends(get_shotgrid_instance)
):
    # 1. 캐시 키 생성 및 확인
    cache_key = f"{project_id}_{task_name}"
    current_time = time.time()
    
    # use_cache=true 일 때만 캐시를 사용하도록 조건 변경
    if use_cache and cache_key in API_CACHE and (current_time - API_CACHE[cache_key]["timestamp"]) < CACHE_TTL_SECONDS:
        all_versions = API_CACHE[cache_key]["data"]
    else:
        # 2. 캐시 없으면 ShotGrid에서 모든 데이터를 가져옴
        all_versions = shotgrid_api.get_versions_for_task(sg, project_id, task_name)
        API_CACHE[cache_key] = {"timestamp": current_time, "data": all_versions}

    # 3. 정렬 적용
    sorted_versions = _apply_sorting(all_versions, sort_by, sort_order)

    # 4. 페이지네이션 적용
    total_items = len(sorted_versions)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_versions = sorted_versions[start_index:end_index]

    # 5. 존재하는 엔티티 타입 확인
    present_types = set()
    for v in all_versions:
        entity = v.get('entity')
        if not entity: continue
        entity_type = entity.get('type')
        if entity_type:
            present_types.add(entity_type)

    # 6. 최종 데이터 반환
    return {
        "versions": paginated_versions,
        "presentEntityTypes": list(present_types),
        "total_pages": total_pages,
        "current_page": page,
        "total_versions": total_items
    }
