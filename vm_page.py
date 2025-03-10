import streamlit as st


def calculate_price(cpu, ram, storage, duration):
    base_price = 1000
    cpu_cost = cpu * 20
    ram_cost = ram * 15
    storage_cost = storage * 10
    duration_cost = duration * 50
    return base_price + cpu_cost + ram_cost + storage_cost + duration_cost

def vm_page():
    st.title("Конфигуратор аренды виртуальных машин")
    with st.container():
        st.header("Что такое виртуальная машина?")
        st.write("Виртуальная машина (VM) – это программная копия компьютера, работающая внутри другого. Она не существует как физическое устройство, но функционирует как полноценный компьютер, используя ресурсы основного. Представьте, что вы запускаете один компьютер внутри другого, создавая “воображаемую” машину, которая ведет себя так, как если бы была реальной.")
        st.subheader("Как начать работу?")
        st.write("Вы получаете ssh ключ к доступу VM")
        st.subheader("Преимущества виртуальной машины")
        
        
    st.header("Параметры")
    cpu = st.slider("CPU Cores", min_value=1, max_value=32, value=4)
    ram = st.slider("RAM (GB)", min_value=1, max_value=128, value=8)
    storage = st.number_input("Storage (GB)", min_value=10, max_value=1000, step=10)
    distribute_options = ["Ubuntu", "CentOS", "Fedora"]
    distribute = st.selectbox("Дистрибутив Linux", options=distribute_options)
    duration = st.slider("Длительность аренды (минуты)", min_value=1, max_value=60, value=10)

    with st.container():
        st.header("Краткая выжимка")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Storage:** {storage} GB")
        st.write(f"**Дистрибутив Linux:** {distribute}")
        st.write(f"**Длительность аренды:** {duration} минут")

    price = calculate_price(cpu, ram, storage, duration)
    st.subheader("Стоимость")
    st.write(f"**₽{price:.2f}**")

    if st.button("Арендовать сейчас"):
        st.success("Ваша заявка принята!")
    