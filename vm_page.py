import streamlit as st
import libvirt
import os
import subprocess
import time
import requests
import sys

private_key_path, public_key=None, None
# Словарь с ISO-образами для каждой ОС
OS_IMAGES = {
    "Ubuntu": "https://releases.ubuntu.com/20.04/ubuntu-20.04.6-desktop-amd64.iso",
    "CentOS": "https://mirrors.centos.org/mirrorlist?path=/10-stream/BaseOS/x86_64/iso/CentOS-Stream-10-latest-x86_64-dvd1.iso&redirect=1&protocol=https",
    "Fedora": "https://download.fedoraproject.org/pub/fedora/linux/releases/41/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-41-1.4.iso"
}
#Генерация ssh ключа
def generate_ssh_keys(vm_name):
    ssh_dir = f"/var/lib/libvirt/images/{vm_name}_ssh"
    os.makedirs(ssh_dir, exist_ok=True)

    private_key_path = os.path.join(ssh_dir, "id_rsa")
    public_key_path = f"{private_key_path}.pub"

    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", private_key_path], check=True)

    with open(public_key_path, "r") as f:
        public_key = f.read().strip()
    
    return private_key_path, public_key

# Функция для скачивания ISO-образа
def download_iso(iso_url, save_path):
    response = requests.get(iso_url, stream=True)
    if response.status_code == 200:
        print ("SUCCESS SUKA ")
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        st.success(f"ISO образ загружен в {save_path}")
    else:
        st.error(f"Не получилось загрузить {iso_url}")

# Пример функции для выбора и скачивания ISO-образа
def get_os_image(os_name):
    iso_url = OS_IMAGES.get(os_name)
    if iso_url:
        file_name = iso_url.split("/")[-1]  # Извлекаем имя файла из URL
        file_path = os.path.join("/var/lib/libvirt/images/", file_name)  # Укажите правильный путь для сохранения

        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            st.warning(f"ISO образ для {os_name} уже существует в {file_path}. Пропуск загрузки.")
        else:
            st.success(f"Загрузка ISO образа для {os_name}...")
            download_iso(iso_url, file_path)
        return file_path
    else:
        raise ValueError(f"ISO образ для {os_name} не подходит.")



def create_disk(disk_path, size):
    try:
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', disk_path, f'{size}G'],check=True)
        st.success(f"Создан диск по {disk_path} размера {size}GB.")
    except subprocess.CalledProcessError as e:
        st.error(f"Не получилось создать образ диска: {e}")
def create_vm(cpu, ram, storage, os_name, location, duration):

    vm_name=time.strftime("%Y%m%d-%H%M%S")
    disk_path = f"/var/lib/libvirt/images/{vm_name}.qcow2"
    os_image=get_os_image(os_name)
    create_disk(disk_path, storage)
    global private_key_path, public_key
    private_key_path, public_key = generate_ssh_keys(vm_name)
    st.session_state["private_key_path"] = private_key_path

    st.header(f"Создание машины со следующими параметрами:")
    st.markdown(f"**CPU:** {cpu}  \n**RAM:** {ram}GB  \n**Storage:** {storage}GB  \n**OS:** {os_name}  \n**Location:** {location}  \n**Duration:** {duration}")

    st.write(f"Путь образа диска: {disk_path}")

    vm_xml = f"""
    <domain type='kvm'>
        <name>{vm_name}</name>
        <memory unit='KiB'>{ram * 1024 * 1024}</memory>
        <vcpu placement='static'>{cpu}</vcpu>
        <os>
            <type arch='x86_64' machine='pc-i440fx-2.9'>hvm</type>
            <boot dev='cdrom'/>
        </os>
        <devices>
            <video>
                <model type='qxl' ram='65536' vram='65536'/>
            </video>
            <graphics type='vnc' port='-1' autoport='yes'/>
            <disk type='file' device='disk'>
                <driver name='qemu' type='qcow2'/>
                <source file='{disk_path}'/>
                <target dev='vda' bus='virtio'/>
            </disk>
            <disk type='file' device='cdrom'>
                <driver name='qemu' type='raw'/>
                <source file='{os_image}'/>
                <target dev='hdc' bus='ide'/>
                <readonly/>
            </disk>
            <interface type='network'>
                <mac address='52:54:00:32:8f:2c'/>
                <source network='default'/>
                <model type='virtio'/>
                <port type='nat'>
                    <source port='2222'/>
                    <target port='22'/>
                </port>
            </interface>

        </devices>
        <metadata>
            <cloud-init>
                <user-data><![CDATA[
    #cloud-config
    users:
        -name: cloud-user
        sudo: ALL=(ALL) NOPASSWD:ALL
        ssh-authorized-keys:        
            -{public_key}
        shell: /bin/bash
    ]]></user-data>
        </cloud-init>
    </metadata>
    </domain>
    """

    print("VM XML configuration:")
    print(vm_xml)

    conn = libvirt.open('qemu:///system')
    if conn is None:
        raise Exception("Не получилось окрыть соединение с libvirt.")

    try:
        st.warning("Попытка определить виртуальную машину в libvirt...")
        domain = conn.defineXML(vm_xml) 
        st.success(f"Виртуальная машина '{vm_name}' успешно создана") # Определяем виртуальную машину
        if domain is None:
            st.error("Не получилось создать виртуальную машину: ")
        else:
            st.success("Виртуальная машина успешно определена")
    except libvirt.libvirtError as e:
        st.error(f"Ошибка в создании виртуальной машины: {e}")
    finally:
        conn.close()
def manage_vm(action, vm_name):
    conn=libvirt.open('qemu:///system')
    if conn is None:
        st.error("Ошибка в открытии соединения в libvirt")
        return
    try:
        dom=conn.lookupByName(vm_name)
        if action == "start":
            dom.create()
            st.success(f"Виртуальная машина '{vm_name}'запущена.")
            response=requests.get("https://ifconfig.me").text.strip()
            st.write(f"**Соединение с вашей виртуальной машиной:**")
            st.code(f"ssh cloud-user@{response} -p 2222", language="bash")

            st.write("**Загрузите ваш приватный ключ:**")
            private_key_path = st.session_state.get("private_key_path", None)
            if private_key_path is None:
                st.error("Приватный ключ не найден!")
                return

            st.download_button("Загрузите SSH Key", open(private_key_path, "rb"), file_name="id_rsa")
        elif action == "shutdown":
            dom.destroy()
            st.success(f"Виртуальная машина '{vm_name}' остановлена.")
        elif action == "delete":
            dom.undefine()
            st.success(f"Виртуальная машина '{vm_name}' удалена.")
    except libvirt.libvirtError as e:
        st.error(f"Ошибка в {action} виртуальной машины: {e}")
    finally:
        conn.close()

def calculate_price(cpu, ram, storage, duration):
    base_price = 1000
    cpu_cost = cpu * 20
    ram_cost = ram * 15
    storage_cost = storage * 10
    duration_cost = duration * 50
    return base_price + cpu_cost + ram_cost + storage_cost + duration_cost
def show_all():
    conn=libvirt.open('qemu:///system')
    if conn is None:
        st.error("Не получилось открыть libvirt")
        return
    try:
        st.header("Все виртуальные машины:")
        domains = conn.listAllDomains()
        if not domains:
            st.write("Виртуальные машины не найдены")
        else:
            for domain in domains:
                name = domain.name()
                info = domain.info()  # Получаем информацию о домене
                state = info[0]  # Состояние виртуальной машины (state)
                state_names = {
                    0: "Неизвестно состояние",
                    1: "Запущена",
                    2: "Заблокирована",
                    3: "Приостановлена",
                    4: "Выключена",
                    5: "Остановлена",
                    6: "Приостановлена в режиме сна"
                }
                
                st.write(f"- {name}: {state_names.get(state, 'Неизвестное состояние')}")
        
        # Закрываем соединение
        conn.close()

    except libvirt.libvirtError as e:
        print(f"Libvirt ошибка: {e}", file=sys.stderr)
        exit(1)

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
    distribute = ["Ubuntu", "CentOS", "Fedora"]
    os_name = st.selectbox("Дистрибутив Linux", options=distribute)
    location = st.selectbox("Location", ["US East", "US West", "Europe", "Asia"])

    duration = st.slider("Длительность аренды (минуты)", min_value=1, max_value=60, value=10)

    with st.container():
        st.header("Краткая выжимка")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Storage:** {storage} GB")
        st.write(f"**Дистрибутив Linux:** {os_name}")
        st.write(f"**Длительность аренды:** {duration} минут")

    price = calculate_price(cpu, ram, storage, duration)
    st.subheader("Стоимость")
    st.write(f"**₽{price:.2f}**")

    if st.button("Арендовать сейчас"):

        try:
            st.success("Ваша заявка принята!")
            create_vm(cpu, ram, storage, os_name, location, duration)
            st.session_state.vm_created = True
        except Exception as e:
            st.error(str(e))
            st.session_state.vm_created = False
    if st.button("Показать все виртуальные машины"):
        show_all()
        # Проверка на наличие введенного имени
    
    vm_name = st.text_input("Введите имя виртуальной машины для управления")

    if vm_name:
        if st.button("Запустить виртуальную машину"):
            manage_vm("start", vm_name)
        if st.button("Остановить виртуальную машину"):
            manage_vm("shutdown", vm_name)
        if st.button("Удалить виртуальную машину"):
            manage_vm("delete", vm_name)
            # Сбрасываем состояние после удаления VM
            st.session_state.vm_created = False
        
    else:
        st.warning("Введите имя виртуальной машины для управления.")
if __name__ == "__main__":
    vm_page()
