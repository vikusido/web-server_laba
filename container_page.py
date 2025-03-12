import streamlit as st
import docker
import time
import threading
import os

# Создаем клиент Docker
client = docker.from_env()

# Функция для расчета стоимости
def calculate_price(cpu, ram, duration):
    base_price = 1000
    cpu_cost = cpu * 20
    ram_cost = ram * 15
    duration_cost = duration * 50
    return base_price + cpu_cost + ram_cost + duration_cost

#функция для установки образа
def ensure_image_exists(image_name):
    try:
        client.images.get(image_name)
        st.success(f"Образ '{image_name}' найден локально.")
    except docker.errors.ImageNotFound:
        st.info(f"Образ '{image_name}' не найден локально. Загрузка из Docker Hub...")
        try:
            client.images.pull(image_name)
            st.success(f"Образ '{image_name}' успешно загружен.")
        except Exception as e:
            st.error(f"Не удалось загрузить образ '{image_name}': {e}")
            return False
    return True

# Функция для создания контейнера
def create_container(cpu, ram, os_name, duration):
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
        ensure_image_exists(image)
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
        st.info(f"Контейнер будет удалён через {duration} минут.")
        
        # Запускаем таймер для удаления контейнера
        delete_container_after_timeout(container_name, duration)
        return container_name
    except Exception as e:
        st.error(f"Ошибка при создании контейнера: {e}")
        return None

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

# Функция для управления контейнером
def manage_container(action, container_name):
    try:
        container = client.containers.get(container_name)
        if action == "start":
            if container.status != "running":
                return start_container(container_name)
            else:
                st.warning(f"Контейнер '{container_name}' уже запущен.")
        elif action == "stop":
            if container.status == "running":
                container.stop()
                st.success(f"Контейнер '{container_name}' остановлен.")
            else:
                st.warning(f"Контейнер '{container_name}' не запущен, остановка не нужна.")
        elif action == "delete":
            if container.status == "exited" or container.status == "created":
                container.remove()
                st.success(f"Контейнер '{container_name}' удалён.")
            elif container.status == "running":
                st.warning(f"Контейнер '{container_name}' запущен, сначала остановите.")
    except docker.errors.NotFound:
        st.error(f"Контейнер '{container_name}' не найден.")
    except Exception as e:
        st.error(f"Ошибка в упралении контейнером: {e}")

# Функция для удаления контейнера через указанное время
def delete_container_after_timeout(container_name, duration):
    def _delete_container():
        time.sleep(duration * 60)  # Исправлено: duration в минутах
        try:
            container = client.containers.get(container_name)
            state = container.status
            if state == "running":
                container.stop()  # Останавливаем контейнер, если он запущен
            container.remove()  # Удаляем контейнер
            st.success(f"Контейнер '{container_name}' удален по истечении времени аренды.")
        except Exception as e:
            st.error(f"Ошибка при удалении контейнера: {e}")
    threading.Thread(target=_delete_container, daemon=True).start

# Функция для отображения всех контейнеров
def show_all():
    try:
        st.header("Все контейнеры Docker:")
        containers = client.containers.list(all=True)
        
        if not containers:
            st.write("Контейнеры не найдены")
        else:
            status_translation = {
                "running": "Запущен",
                "exited": "Остановлен",
                "paused": "Приостановлен",
                "created": "Создан",
                "restarting": "Перезапускается",
                "dead": "Не работает"
            }
            for container in containers:
                name = container.name
                status = container.status  # Текущее состояние контейнера
                translated_status = status_translation.get(status, status)
                st.write(f"- **{name}**: {translated_status}")
    except docker.errors.DockerException as e:
        st.error(f"Ошибка подключения к Docker: {e}")
    except Exception as e:
        st.error(f"Произошла ошибка: {e}")

# Основная страница контейнеров
def container_page():
    if "container_deleted" in st.session_state and st.session_state["container_deleted"]:
        st.success("Контейнер успешно удален.")
        st.session_state["container_deleted"] = False

    st.title("Конфигуратор аренды контейнеров")
    with st.container():
        st.header("Что такое контейнер?")
        st.write("Контейнер – это изолированная среда для запуска приложений. Он использует ядро хостовой системы, но изолирует процессы, файловую систему и сеть.")
        st.subheader("Как начать работу?")
        st.write("Вы получаете SSH доступ к контейнеру.")
        st.subheader("Преимущества контейнеров")
        
    st.header("Параметры")
    cpu = st.slider("CPU Cores", min_value=1, max_value=32, value=4)
    ram = st.slider("RAM (GB)", min_value=1, max_value=128, value=8)
    distribute = ["Ubuntu", "CentOS", "Fedora"]
    os_name = st.selectbox("Операционная система", options=distribute)
    duration = st.slider("Длительность аренды (минуты)", min_value=1, max_value=60, value=10)
    
    with st.container():
        st.header("Краткая выжимка")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Операционная система:** {os_name}")
        st.write(f"**Длительность аренды:** {duration} минут")
    
    price = calculate_price(cpu, ram, duration)
    with st.container():
        st.subheader("Стоимость аренды")
        st.write(f"**₽{price:.2f}**")
    
    if st.button("Арендовать сейчас"):
        try:
            container_name = create_container(cpu, ram, os_name, duration)
            if container_name:
                st.session_state.container_created = True
        except Exception as e:
            st.error(str(e))
            st.session_state.container_created = False
    
    if st.button("Показать все контейнеры"):
        show_all()
    
    # Используем st.session_state для сохранения состояния текстового поля
    if "container_name" not in st.session_state:
        st.session_state.container_name = ""
    
    container_name = st.text_input(
        "Введите имя контейнера для управления",
        value=st.session_state.container_name
    )
    st.session_state.container_name = container_name
    
    if container_name:
        if st.button("Запустить контейнер"):
            port = manage_container("start", container_name)
            if port:
                st.write(f"SSH доступен на порту {port}")
        if st.button("Остановить контейнер"):
            manage_container("stop", container_name)
        if st.button("Удалить контейнер"):
            manage_container("delete", container_name)
    else:
        st.warning("Введите имя контейнера для управления.")

if __name__ == "__main__":
    container_page()
