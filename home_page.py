import streamlit as st

def home_page():
    st.header("Главная страница")
    st.write("Добро пожаловать!")
    st.write("Здесь вы можете арендовать виртуальную машину или контейнер.")
    st.subheader("Как арендовать?")
    st.write("Вы выбираете необходимые параметры (CPU, Storage, RAM и т.д.) и получаете SSH ключ для доступа.")
    if st.button("Перейти к аренде виртуальных машин"):
        st.session_state.page = "vm"
        st.rerun()
    if st.button("Перейти к аренде контейнеров"):
        st.session_state.page = "container"
        st.rerun()
