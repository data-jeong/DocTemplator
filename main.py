import os
import json
import openai
import streamlit as st
from datetime import datetime
from streamlit import set_page_config



# OpenAI API 키 설정
openai.api_key = ''  # 실제 사용 시 환경 변수 등을 통해 안전하게 관리해야 합니다.

def load_document_categories():
    with open('document_categories.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_document_categories(categories):
    with open('document_categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

def generate_document_template(document_name):
    prompt = f"""당신은 소프트웨어 개발 프로젝트에서 사용되는 문서 템플릿을 만드는 전문가입니다. "{document_name}"에 대한 현업에서 바로 사용 가능한 템플릿을 작성해 주세요. 다음 가이드라인을 따라 주세요:

1. 문서의 목적과 중요성을 간단히 설명해 주세요.
2. 문서의 주요 섹션들을 나열하고, 각 섹션에 포함되어야 할 내용을 설명해 주세요.
3. 각 섹션에 대해 실제로 채워넣을 수 있는 템플릿 형식으로 작성해 주세요.
4. 필요한 경우, 작성 지침이나 예시를 포함해 주세요.
5. 문서 끝에는 승인 및 변경 이력을 기록할 수 있는 섹션을 추가해 주세요.
6. 전체적인 형식은 마크다운으로 작성해 주세요."""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in creating software development document templates."},
            {"role": "user", "content": prompt}
        ],
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].message['content']

def save_template(category, document_name, content):
    base_dir = "document_templates"
    category_dir = os.path.join(base_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    
    safe_filename = "".join([c for c in document_name if c.isalnum() or c in (' ', '_')]).rstrip()
    filename = f"{safe_filename}_template.md"
    filepath = os.path.join(category_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath

def update_template(category, document_name, new_content):
    filepath = save_template(category, document_name, new_content)
    st.success(f"템플릿이 업데이트되었습니다: {filepath}")

def add_new_template(category, document_name):
    categories = load_document_categories()
    if category not in categories:
        categories[category] = []
    if document_name not in categories[category]:
        categories[category].append(document_name)
        save_document_categories(categories)
        content = generate_document_template(document_name)
        filepath = save_template(category, document_name, content)
        st.success(f"새 템플릿이 생성되었습니다: {filepath}")
    else:
        st.warning("이미 존재하는 템플릿입니다.")

def main():
    set_page_config(layout="wide", page_title="DocTemplator - 문서 템플릿 관리 시스템")
    st.title("DocTemplator - 문서 템플릿 관리 시스템")

    categories = load_document_categories()

    # 사이드바: 카테고리 선택 및 새 카테고리 추가
    st.sidebar.header("카테고리 관리")
    selected_category = st.sidebar.selectbox("카테고리 선택", list(categories.keys()), key="sidebar_category")
    
    new_category = st.sidebar.text_input("새 카테고리 이름")
    if st.sidebar.button("새 카테고리 추가"):
        if new_category and new_category not in categories:
            categories[new_category] = []
            save_document_categories(categories)
            os.makedirs(os.path.join("document_templates", new_category), exist_ok=True)
            st.sidebar.success(f"새 카테고리 '{new_category}'가 추가되었습니다.")
        elif new_category in categories:
            st.sidebar.warning("이미 존재하는 카테고리입니다.")
        else:
            st.sidebar.warning("카테고리 이름을 입력해주세요.")

    # 메인 화면: 탭으로 기능 분리
    tab1, tab2, tab3 = st.tabs(["템플릿 조회 및 수정", "새 템플릿 추가", "템플릿 다운로드"])

    with tab1:
        st.header(f"{selected_category} 문서 목록")
        selected_document = st.selectbox("문서 선택", categories[selected_category], key="tab1_document")

        if selected_document:
            filepath = os.path.join("document_templates", selected_category, f"{selected_document}_template.md")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                edit_method = st.radio("수정 방법 선택", ["에디터로 수정"], key="edit_method")
                
                if edit_method == "에디터로 수정":
                    col1, col2 = st.columns(2)
                    with col1:
                        new_content = st.text_area("템플릿 내용", content, height=3000, key="markdown_editor")
                    with col2:
                        st.markdown(new_content)
                    if st.button("템플릿 업데이트 (에디터)", key="update_editor"):
                        update_template(selected_category, selected_document, new_content)
            else:
                st.warning("템플릿 파일을 찾을 수 없습니다.")

    with tab2:
        st.header("새 템플릿 추가")
        new_category = st.selectbox("카테고리 선택", list(categories.keys()), key="tab2_category")
        new_document = st.text_input("새 문서 이름", key="new_document_name")
        if st.button("템플릿 생성", key="create_template"):
            add_new_template(new_category, new_document)

    with tab3:
        st.header("템플릿 다운로드")
        download_category = st.selectbox("다운로드할 카테고리 선택", list(categories.keys()), key="download_category")
        search_query = st.text_input("문서 검색", "", key="search_query")
        
        filtered_documents = [doc for doc in categories[download_category] if search_query.lower() in doc.lower()]
        
        for document in filtered_documents:
            filepath = os.path.join("document_templates", download_category, f"{document}_template.md")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                col1, col2 = st.columns([3, 1])
                col1.write(document)
                col2.download_button(
                    label="다운로드",
                    data=content,
                    file_name=f"{document}_template.md",
                    mime="text/markdown",
                    key=f"{download_category}_{document}_download"
                )
            else:
                st.warning(f"{document} 템플릿 파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()