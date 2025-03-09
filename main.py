import streamlit as st
from container_page import container_page
from vm_page import vm_page
from home_page import home_page

st.set_page_config(
    page_title="Rental",
    page_icon=":computer:",
)

if 'page' not in st.session_state:
    st.session_state.page = 'home'

def change_page(page_name):
    st.session_state.page = page_name

with st.sidebar:
    st.title("Навигация")
    if st.button("Главная", on_click=change_page, args=('home',)):
        pass
    if st.button("Виртуальные машины", on_click=change_page, args=('vm',)):
        pass
    if st.button("Контейнеры", on_click=change_page, args=('container',)):
        pass
if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'vm':
    vm_page()
elif st.session_state.page == 'container':
    container_page()