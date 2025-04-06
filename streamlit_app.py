import streamlit as st
import pdfkit
import os
import tempfile
import subprocess
from pathlib import Path

# wkhtmltopdf 경로 동적으로 찾기
try:
    wkhtmltopdf_path = subprocess.check_output(['which', 'wkhtmltopdf']).decode('utf-8').strip()
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    wkhtmltopdf_installed = True
except (subprocess.CalledProcessError, OSError):
    wkhtmltopdf_installed = False

# Streamlit 앱 제목
st.title("📄 HTML → PDF 변환기")

if not wkhtmltopdf_installed:
    st.error("wkhtmltopdf가 설치되어 있지 않습니다. 다음 명령어로 설치하세요:")
    st.code("sudo apt-get update && sudo apt-get install -y wkhtmltopdf fonts-nanum")
    st.stop()

# 한글 폰트 설치 확인
try:
    font_check = subprocess.check_output(['ls', '/usr/share/fonts/truetype/nanum']).decode('utf-8')
    korean_fonts_installed = 'NanumGothic.ttf' in font_check
except (subprocess.CalledProcessError, OSError):
    korean_fonts_installed = False

if not korean_fonts_installed:
    st.warning("한글 폰트가 설치되어 있지 않습니다. 다음 명령어로 나눔 폰트를 설치하세요:")
    st.code("sudo apt-get update && sudo apt-get install -y fonts-nanum")

# 사이드바에 옵션 추가
st.sidebar.header("PDF 설정")
page_size = st.sidebar.selectbox("페이지 크기", ["A4", "Letter", "Legal"], index=0)
orientation = st.sidebar.radio("방향", ["Portrait", "Landscape"], index=0)
include_css = st.sidebar.checkbox("HTML에 연결된 CSS 포함", value=True)

# 폰트 설정 추가
st.sidebar.subheader("한글 설정")
use_korean_font = st.sidebar.checkbox("한글 폰트 사용", value=True)
korean_font = st.sidebar.selectbox(
    "한글 폰트 선택", 
    ["NanumGothic", "NanumMyeongjo", "NanumBarunGothic", "맑은 고딕", "궁서체"],
    index=0
)

# HTML 파일 업로드
uploaded_file = st.file_uploader("HTML 파일을 업로드하세요", type=["html"])

# CSS 파일 업로드 (선택사항)
css_file = None
if include_css:
    css_file = st.file_uploader("CSS 파일을 업로드하세요 (선택사항)", type=["css"])

# 변환 버튼
if uploaded_file is not None:
    st.success("✅ HTML 파일 업로드 완료!")
    
    # 임시 디렉토리 생성 및 파일 경로 설정
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        html_path = temp_dir_path / "uploaded_file.html"
        pdf_path = temp_dir_path / "converted_file.pdf"
        
        # 업로드된 HTML 파일 내용 읽기
        content = uploaded_file.getvalue().decode('utf-8')
        
        # 한글 폰트 지원을 위한 메타태그와 스타일 추가
        if use_korean_font:
            if "<head>" in content:
                enhanced_content = content.replace("<head>", f"""<head>
                <meta charset="utf-8">
                <style>
                    @font-face {{
                        font-family: '{korean_font}';
                        src: local('{korean_font}');
                    }}
                    body, p, h1, h2, h3, h4, h5, h6, div, span, li, a, table, th, td {{
                        font-family: '{korean_font}', sans-serif !important;
                    }}
                </style>""")
            else:
                enhanced_content = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @font-face {{
                            font-family: '{korean_font}';
                            src: local('{korean_font}');
                        }}
                        body, p, h1, h2, h3, h4, h5, h6, div, span, li, a, table, th, td {{
                            font-family: '{korean_font}', sans-serif !important;
                        }}
                    </style>
                </head>
                <body>
                {content}
                </body>
                </html>"""
        else:
            enhanced_content = content
        
        # 수정된 HTML 파일 저장
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(enhanced_content)
        
        # CSS 파일이 있으면 저장
        css_path = None
        if css_file is not None:
            css_path = temp_dir_path / "styles.css"
            with open(css_path, "wb") as f:
                f.write(css_file.getbuffer())
        
        # 변환 옵션 설정
        options = {
            'enable-local-file-access': '',
            'page-size': page_size,
            'orientation': orientation.lower(),
            'encoding': "UTF-8",
            'no-outline': None,
            'disable-smart-shrinking': '',
            'dpi': 300,
            'print-media-type': '',
            'javascript-delay': 1000,
            'debug-javascript': ''
        }
        
        # 한글 폰트 관련 옵션 추가
        if use_korean_font:
            options['encoding'] = 'UTF-8'
        
        # CSS 파일이 있으면 옵션에 추가
        if css_path:
            options['user-style-sheet'] = str(css_path)
        
        # PDF 변환 실행 버튼
        if st.button("🔄 HTML → PDF 변환"):
            try:
                with st.spinner("PDF로 변환 중..."):
                    # configuration 객체를 전달하여 PDF 변환
                    pdfkit.from_file(str(html_path), str(pdf_path), options=options, configuration=config)
                
                # 변환 완료 메시지
                st.success("🎉 변환 완료! PDF 파일을 다운로드하세요.")
                
                # PDF 다운로드 버튼 제공
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="📥 PDF 다운로드",
                    data=pdf_data,
                    file_name=f"{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"PDF 변환 중 오류가 발생했습니다: {e}")
                st.markdown("""
                ### 문제 해결 방법:
                1. 한글 폰트 설치:
                   ```
                   sudo apt-get update
                   sudo apt-get install -y fonts-nanum
                   ```
                2. wkhtmltopdf 재설치:
                   ```
                   sudo apt-get install -y wkhtmltopdf
                   ```
                3. 앱 재시작
                """)

