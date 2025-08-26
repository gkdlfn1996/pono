# /backend/app/routers/version_view_router.py

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any, List
import time
import json
from operator import itemgetter
from ..shotgrid_api import async_api
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

def _apply_search_filters(data: List[Dict], filters: List[Dict]) -> List[Dict]:
    """
    주어진 데이터 목록에 SearchBar 필터를 적용합니다.
    """
    if not filters:
        return data

    filtered_data = []
    for item in data:
        match_all = True
        for f in filters:
            filter_type = f.get('type')
            filter_value = f.get('value', '').lower()
            
            if filter_type == 'Version':
                if not (item.get('code') and filter_value in item['code'].lower()):
                    match_all = False
                    break
            elif filter_type == 'Tag':
                tags = item.get('tags', [])
                if not any(filter_value in tag.get('name', '').lower() for tag in tags):
                    match_all = False
                    break
            elif filter_type == 'Playlist':
                playlists = item.get('playlists', [])
                if not any(filter_value in pl.get('name', '').lower() for pl in playlists):
                    match_all = False
                    break
            elif filter_type == 'Subject':
                notes = item.get('notes', [])
                if not any(filter_value in note.get('subject', '').lower() for note in notes if note.get('subject')):
                    match_all = False
                    break
            elif filter_type == 'Shot' or filter_type == 'Asset':
                entity = item.get('entity')
                if not (entity and entity.get('type') == filter_type and filter_value in entity.get('name', '').lower()):
                    match_all = False
                    break
            elif filter_type == 'Task':
                task = item.get('sg_task')
                if not (task and filter_value in task.get('name', '').lower()):
                    match_all = False
                    break
            # 다른 필터 타입에 대한 로직 추가 가능

        if match_all:
            filtered_data.append(item)
            
    return filtered_data

def _extract_suggestions(data: List[Dict]) -> Dict[str, List[str]]:
    """
    전체 버전 데이터에서 각 필터 타입에 대한 제안 목록을 추출합니다.
    """
    suggestions = {
        'Task': set(),
        'Shot': set(),
        'Asset': set(),
        'Tag': set(),
        'Playlist': set(),
        'Subject': set(),
        'Version': set(),
    }

    for item in data:
        # Version 이름 추가
        if item.get('code'):
            suggestions['Version'].add(item['code'])

        # Tag 이름 추가
        for tag in item.get('tags', []):
            if tag.get('name'):
                suggestions['Tag'].add(tag['name'])
        
        # Playlist 이름 추가
        for pl in item.get('playlists', []):
            if pl.get('name'):
                suggestions['Playlist'].add(pl['name'])

        # Shot 또는 Asset 이름 추가
        entity = item.get('entity')
        if entity and entity.get('type') in ['Shot', 'Asset'] and entity.get('name'):
            suggestions[entity['type']].add(entity['name'])
            
        # Subject 이름 추가
        for note in item.get('notes', []):
            if note.get('subject'):
                suggestions['Subject'].add(note['subject'])

        # Task 이름 추가
        task = item.get('sg_task')
        if task and task.get('name'):
            suggestions['Task'].add(task['name'])

    # 각 set을 정렬된 리스트로 변환
    return {key: sorted(list(value)) for key, value in suggestions.items()}


# --- 데이터 처리 기능이 통합된 엔드포인트 --- 

@router.get("/")
async def get_processed_versions(
    request: Request,
    project_id: int,
    pipeline_step: str,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    filters: str = None,
    use_cache: bool = False, # 캐시 사용 여부 파라미터 (기본값: False)
    sg = Depends(get_shotgrid_instance)
):
    # 1. 캐시 키 생성 및 확인
    # 캐시는 필터링되지 않은 전체 데이터에 대해서만 사용합니다.
    cache_key = f"{project_id}_{pipeline_step}"
    current_time = time.time()
    
    # use_cache=true 일 때만 캐시를 사용하도록 조건 변경
    if use_cache and cache_key in API_CACHE and (current_time - API_CACHE[cache_key]["timestamp"]) < CACHE_TTL_SECONDS:
        all_versions = API_CACHE[cache_key]["data"]
    else:
        # 캐시 없으면 ShotGrid에서 모든 데이터를 가져옴
        all_versions = await async_api.get_versions_for_pipeline_step(
            sg, project_id, pipeline_step
        )
        # 작업 완료 후 클라이언트 연결 상태 확인
        if await request.is_disconnected():
            print(f"Client disconnected for {project_id}/{pipeline_step}, discarding results.")
            return
        API_CACHE[cache_key] = {"timestamp": current_time, "data": all_versions}

    # 2. SearchBar 필터 적용
    parsed_filters = []
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            parsed_filters = []
    filtered_versions = _apply_search_filters(all_versions, parsed_filters)

    # 3. 정렬 적용 (필터링된 결과에 대해)
    sorted_versions = _apply_sorting(filtered_versions, sort_by, sort_order)

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

    # 6. 제안 목록 추출
    suggestions = _extract_suggestions(all_versions)

    # 7. 최종 데이터 반환
    return {
        "versions": paginated_versions,
        "presentEntityTypes": list(present_types),
        "suggestions": suggestions,
        "total_pages": total_pages,
        "current_page": page,
        "total_versions": total_items
    }
