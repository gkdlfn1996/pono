# /backend/app/version_view.py
# 이 파일은 라우터가 아니며, 오직 데이터 가공을 위한 헬퍼 함수들의 모음입니다.

from typing import Dict, Any, List
import json
from operator import itemgetter

# --- 데이터 가공 헬퍼 함수들 ---

def apply_sorting(data: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
    """
    데이터 목록에 다단계 정렬을 적용합니다.
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

def apply_search_filters(data: List[Dict], filters_str: str) -> List[Dict]:
    """
    주어진 데이터 목록에 SearchBar 필터를 적용합니다.
    """
    if not filters_str:
        return data
    try:
        filters = json.loads(filters_str)
    except json.JSONDecodeError:
        return data # 파싱 실패 시 원본 데이터 반환
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
                    match_all = False; break
            elif filter_type == 'Tag':
                tags = item.get('tags', [])
                if not any(filter_value in tag.get('name', '').lower() for tag in tags):
                    match_all = False; break
            elif filter_type == 'Playlist':
                playlists = item.get('playlists', [])
                if not any(filter_value in pl.get('name', '').lower() for pl in playlists):
                    match_all = False; break
            elif filter_type == 'Subject':
                notes = item.get('notes', [])
                if not any(filter_value in note.get('subject', '').lower() for note in notes if note.get('subject')):
                    match_all = False; break
            elif filter_type == 'Shot' or filter_type == 'Asset':
                entity = item.get('entity')
                if not (entity and entity.get('type') == filter_type and filter_value in entity.get('name', '').lower()):
                    match_all = False; break
            elif filter_type == 'Task':
                task = item.get('sg_task')
                if not (task and task.get('name', '').lower()):
                    match_all = False; break
            # 다른 필터 타입에 대한 로직 추가 가능

        if match_all:
            filtered_data.append(item)
            
    return filtered_data

def extract_suggestions(data: List[Dict]) -> Dict[str, List[str]]:
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
        if item.get('code'): suggestions['Version'].add(item['code'])
        # Tag 이름 추가
        for tag in item.get('tags', []):
            if tag.get('name'): suggestions['Tag'].add(tag['name'])
        # Playlist 이름 추가
        for pl in item.get('playlists', []):
            if pl.get('name'): suggestions['Playlist'].add(pl['name'])
        # Shot 또는 Asset 이름 추가
        entity = item.get('entity')
        if entity and entity.get('type') in ['Shot', 'Asset'] and entity.get('name'):
            suggestions[entity['type']].add(entity['name'])
        # Subject 이름 추가
        for note in item.get('notes', []):
            if note.get('subject'): suggestions['Subject'].add(note['subject'])
        # Task 이름 추가
        task = item.get('sg_task')
        if task and task.get('name'): suggestions['Task'].add(task['name'])

    # 각 set을 정렬된 리스트로 변환
    return {key: sorted(list(value)) for key, value in suggestions.items()}

def get_present_entity_types(all_versions: List[Dict]) -> List[str]:
    """
    전체 버전 목록에서 존재하는 모든 엔티티 타입(Shot, Asset 등)을 추출합니다.
    """
    present_types = set()
    for v in all_versions:
        entity = v.get('entity')
        if entity and entity.get('type'):
            present_types.add(entity['type'])
    return list(present_types)

def apply_pagination(data: List[Dict], page: int, page_size: int) -> List[Dict]:
    """
    데이터 목록에 페이지네이션을 적용합니다.
    """
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    return data[start_index:end_index]


# --- 메인 데이터 처리 함수 ---

def process_view_data(
    all_versions: List[Dict],
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    filters: str
) -> Dict:
    """
    전체 버전 목록을 받아, 필터링, 정렬, 페이지네이션, 제안 목록 추출 등
    모든 뷰 관련 가공을 처리하고 최종 응답 데이터를 반환합니다.
    """
    # 1. SearchBar 필터 적용
    filtered_versions = apply_search_filters(all_versions, filters)

    # 2. 정렬 적용 (필터링된 결과에 대해)
    sorted_versions = apply_sorting(filtered_versions, sort_by, sort_order)

    # 3. 페이지네이션 적용 및 전체 페이지 수 계산
    total_items = len(sorted_versions)
    total_pages = (total_items + page_size - 1) // page_size
    paginated_versions = apply_pagination(sorted_versions, page, page_size)

    # 4. 존재하는 엔티티 타입 확인 (필터링 전 전체 데이터 기준)
    present_types = get_present_entity_types(all_versions)

    # 5. 제안 목록 추출 (필터링 전 전체 데이터 기준)
    suggestions = extract_suggestions(all_versions)

    # 6. 최종 데이터 반환
    return {
        "versions": paginated_versions,
        "presentEntityTypes": present_types,
        "suggestions": suggestions,
        "total_pages": total_pages,
        "current_page": page,
        "total_versions": total_items
    }