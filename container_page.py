import streamlit as st
import docker
import time

def calculate_price(cpu, ram, storage, duration):
    base_price = 1000
    cpu_cost = cpu * 20
    ram_cost = ram * 15
    storage_cost = storage * 10
    duration_cost = duration * 50
    return base_price + cpu_cost + ram_cost + storage_cost + duration_cost

client = docker.from_env()

# Функция для создания контейнера без получения SSH-порта сразу

import os

def create_container(cpu, ram, storage, os_name, location, duration):
    container_name = f"container_{time.strftime('%Y%m%d-%H%M%S')}"
    
    os_images = {
        "Ubuntu": "ubuntu:20.04",
        "CentOS": "centos:8",
        "Fedora": "fedora:latest"
    }
    
    if os_name not in os_images:
        raise ValueError("Unsupported OS")
    
    image = os_images[os_name]
    
    # Создаём папку для монтирования вручную
    mount_path = os.path.join(os.path.expanduser("~"), "docker_data", container_name)
    os.makedirs(mount_path, exist_ok=True)

    
    try:
        container = client.containers.create(
            image=image,
            name=container_name,
            cpu_period=100000,
            cpu_quota=cpu * 100000,  # Исправлено
            mem_limit=f"{ram}g",
            volumes={mount_path: {'bind': '/data', 'mode': 'rw'}},
            tty=True,
            ports={'22/tcp': 0},  # Автоматическое назначение порта
            command="/bin/bash -c 'apt update && apt install -y openssh-server && service ssh start && tail -f /dev/null'"
        )
        st.success(f"Контейнер '{container_name}' успешно создан, но пока не запущен.")
        return container_name
    except Exception as e:
        st.error(f"Ошибка при создании контейнера: {e}")


# Функция для запуска контейнера и получения SSH-порта

def start_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.start()
        
        # Ждем, чтобы Docker назначил порт
        time.sleep(2)
        container.reload()
        ports = container.attrs['NetworkSettings']['Ports']
        ssh_port = ports['22/tcp'][0]['HostPort'] if ports and ports['22/tcp'] else None

        
        if ssh_port:
            st.success(f"Контейнер '{container_name}' запущен. SSH доступен на порте {ssh_port}.")
        else:
            st.warning(f"Контейнер '{container_name}' запущен, но SSH порт не найден.")
        
        return ssh_port
    except docker.errors.NotFound:
        st.error(f"Контейнер '{container_name}' не найден.")
    except Exception as e:
        st.error(f"Ошибка в запуске контейнера: {e}")

def manage_container(action, container_name):
    try:
        container = client.containers.get(container_name)
        if action == "start":
            return start_container(container_name)
        elif action == "stop":
            container.stop()
            st.success(f"Контейнер '{container_name}' остановлен.")
        elif action == "delete":
            container.remove()
            st.success(f"Контейнер '{container_name}' удалён.")
    except docker.errors.NotFound:
        st.error(f"Контейнер '{container_name}' не найден.")
    except Exception as e:
        st.error(f"Ошибка в упралении контейнером: {e}")

def container_page():
    port = None
    st.header("Страница о Контейнерах")
    st.write("Информация о контейнерах...")
    st.subheader("Наши тарифные планы для Контейнеров")
    st.write("Здесь будет таблица с тарифами и описаниями контейнеров.")
    
    with st.container():
        st.header("Параметры контейнера")
        cpu = st.slider("CPU Cores", min_value=1, max_value=32, value=4)
        ram = st.slider("RAM (GB)", min_value=1, max_value=128, value=8)
        storage = st.number_input("Storage (GB)", min_value=10, max_value=1000, step=10)
        distribute = ["Ubuntu", "CentOS", "Fedora"]
        os_name = st.selectbox("Операционная система", options=distribute)
        location = st.selectbox("Location", ["US East", "US West", "Europe", "Asia"])
        duration = st.slider("Длительность аренды (минуты)", min_value=1, max_value=60, value=10)
    
    with st.container():
        st.header("Краткая выжимка")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Storage:** {storage} GB")
        st.write(f"**Операционная система:** {os_name}")
        st.write(f"**Длительность аренды:** {duration} минут")
    
    price = calculate_price(cpu, ram, storage, duration)
    with st.container():
        st.subheader("Стоимость аренды")
        st.write(f"**₽{price:.2f}**")
    
    if st.button("Арендовать сейчас"):
        container_name = create_container(cpu, ram, storage, os_name, location, duration)
    
    with st.container():
        container_name = st.text_input("Введите имя контейнера для управления")
        if container_name:
            if st.button("Start"):
                port = manage_container("start", container_name)
                if port:
                    st.write(f"SSH доступен на порту {port}")
            if st.button("Stop"):
                manage_container("stop", container_name)
            if st.button("Delete"):
                manage_container("delete", container_name)
        else:
            st.warning("Введите имя объекта для управления.")

if __name__ == "__main__":
    container_page()
