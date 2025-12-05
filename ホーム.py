import streamlit as st

def home_page():
    st.set_page_config(
        page_title="SHELL ARC - ホーム",
        page_icon="🏠"
    )
    st.title("SHELL ARCへようこそ！")
    st.image("null_logo.png")
    st.write("""
    サイドバーから各機能にアクセスしてください。
    """)

if __name__ == "__main__":
    home_page()
