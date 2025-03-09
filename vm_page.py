import streamlit as st


def calculate_price(cpu, ram, storage, duration):
    base_price = 10
    cpu_cost = cpu * 2
    ram_cost = ram * 1.5
    storage_cost = storage * 0.1
    duration_cost = duration * 0.5
    return base_price + cpu_cost + ram_cost + storage_cost + duration_cost

def vm_page():
    st.title("Конфигуратор аренды виртуальных машин")
    st.header("Параметры")
    cpu = st.slider("CPU Cores", min_value=1, max_value=32, value=4)
    ram = st.slider("RAM (GB)", min_value=1, max_value=128, value=8)
    storage = st.number_input("Storage (GB)", min_value=10, max_value=1000, step=10)
    os_options = ["Ubuntu", "CentOS", "Windows Server"]
    os = st.selectbox("Операционная система", options=os_options)
    location_options = ["US East", "US West", "Europe", "Asia"]
    location = st.selectbox("Расположение", options=location_options)
    duration = st.slider("Длительность аренды (минуты)", min_value=1, max_value=60, value=10)

    with st.container():
        st.header("Краткая выжимка")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Storage:** {storage} GB")
        st.write(f"**Операционная система:** {os}")
        st.write(f"**Расположение:** {location}")
        st.write(f"**Длительность аренды:** {duration} минут")

    price = calculate_price(cpu, ram, storage, duration)
    st.subheader("Стоимость")
    st.write(f"**₽{price:.2f}**")

    if st.button("Арендовать сейчас"):
        st.success("Ваша заявка принята!")
    