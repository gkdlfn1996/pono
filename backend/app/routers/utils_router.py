from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from bs4 import BeautifulSoup
import os

router = APIRouter()

@router.get("/user-manual", response_class=HTMLResponse)
async def get_user_manual(request: Request):
    """
    docs/User_Manual.md 파일을 읽고 HTML로 변환하여 반환합니다.
    이때, HTML 내의 모든 상대 경로 이미지 src를 절대 URL로 변환합니다.
    """
    # 프로젝트 루트를 기준으로 파일 경로를 설정합니다.
    # 현재 파일 위치: backend/app/routers, 프로젝트 루트: ../../
    # os.path.abspath를 사용하여 절대 경로를 구합니다.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    manual_path = os.path.join(project_root, "docs/User_Manual.md")

    # docs 폴더가 backend 폴더와 같은 레벨에 있다고 가정합니다.
    # StaticFiles 마운트 경로: /static/docs -> docs 폴더
    # 이미지 URL 기본 경로: http://<server_ip>:<port>/static/docs/
    base_url = f"{request.base_url}static/docs"

    try:
        with open(manual_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User manual not found.")

    # Markdown을 HTML로 변환
    # 앵커 플러그인을 사용하여 헤더에 id 자동 생성
    md = MarkdownIt().use(anchors_plugin)
    html_body = md.render(markdown_content)

    # BeautifulSoup를 사용하여 이미지 경로 수정
    soup = BeautifulSoup(html_body, 'html.parser')
    for img in soup.find_all('img'):
        if img.get('src') and img['src'].startswith('./'):
            # 상대 경로('./images/...')를 절대 URL로 변경
            img['src'] = f"{base_url}/{img['src'][2:]}"
    html_body = str(soup)

    # 가독성을 위한 기본 CSS 스타일
    html_style = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background-color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        code {
            padding: .2em .4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,.05);
            border-radius: 3px;
        }
        pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 3px;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            margin: 0;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
                a:hover {
                    text-decoration: underline;
                }
                blockquote {
                    padding: 0 1em;
                    color: #6a737d;
                    border-left: .25em solid #dfe2e5;
                }
         
                 /* 다크 모드 스타일 */
                 @media (prefers-color-scheme: dark) {
                     body {
                         color: #c9d1d9;
                         background-color: #0d1117;
                     }
                     .container {
                         background-color: #161b22;
                         box-shadow: none;
                         border: 1px solid #30363d;
                     }
                     h1, h2, h3, h4, h5, h6 {
                         color: #f0f6fc;
                         border-bottom-color: #30363d;
                     }
                     code {
                         background-color: rgba(110,118,129,0.4);
                     }
                     pre {
                         background-color: #161b22;
                         border: 1px solid #30363d;
                     }
                     a { color: #58a6ff; }
                    blockquote {
                        color: #8b949e;
                        border-left-color: #30363d;
                    }
                 }
             </style>
             """
    # 전체 HTML 페이지 구성
    full_html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PONO User Manual</title>
        {html_style}
    </head>
    <body>
        <div class="container">
            {html_body}
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=full_html)
