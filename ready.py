import streamlit as st
import libvirt
import os
import uuid
import subprocess
import time
import requests

# Словарь с ISO-образами для каждой ОС
OS_IMAGES = {
    "Ubuntu": "https://releases.ubuntu.com/noble/ubuntu-24.04.2-desktop-amd64.iso",
    "CentOS": "https://mirrors.centos.org/mirrorlist?path=/10-stream/BaseOS/x86_64/iso/CentOS-Stream-10-latest-x86_64-dvd1.iso&redirect=1&protocol=https",
    "Windows Server": "https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server"
}

# Функция для скачивания ISO-образа
def download_iso(iso_url, save_path):
    response = requests.get(iso_url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"ISO image downloaded to {save_path}")
    else:
        print(f"Failed to download {iso_url}")

# Пример функции для выбора и скачивания ISO-образа
def get_os_image(os_name):
    iso_url = OS_IMAGES.get(os_name)
    if iso_url:
        file_name = iso_url.split("/")[-1]  # Извлекаем имя файла из URL
        file_path = os.path.join("/var/lib/libvirt/images/", file_name)  # Укажите правильный путь для сохранения

        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            print(f"ISO image for {os_name} already exists at {file_path}. Skipping download.")
        else:
            print(f"Downloading ISO image for {os_name}...")
            download_iso(iso_url, file_path)
        return file_path
    else:
        raise ValueError(f"ISO image for {os_name} is not available.")

# Пример использования
get_os_image("Ubuntu")  # Укажите нужную ОС


def create_disk(disk_path, size):
    try:
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', disk_path, f'{size}G'],check=True)
        st.success(f"Disk created at {disk_path} with_size {size}GB.")
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to create disk: {e}")
def create_vm(cpu, ram, storage, os_name, location, duration):

    vm_name=time.strftime("%Y%m%d-%H%M%S")
    disk_path = f"/var/lib/libvirt/images/{vm_name}.qcow2"
    os_image=get_os_image(os_name)
    create_disk(disk_path, storage)
    

    print(f"Creating VM with:")
    print(f"CPU: {cpu}, RAM: {ram}GB, Storage: {storage}GB, OS: {os_name}, Location: {location}, Duration: {duration}")
    print(f"Disk image path: {disk_path}")

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
        </interface>
      </devices>
    </domain>
    """

    print("VM XML configuration:")
    print(vm_xml)

    conn = libvirt.open('qemu:///system')
    if conn is None:
        raise Exception("Failed to open connection to libvirt.")

    try:
        print("Trying to define the VM in libvirt...")
        domain = conn.defineXML(vm_xml) 
        st.success(f"Virtual machine '{vm_name}' created successfully") # Определяем виртуальную машину
        if domain is None:
            st.error("Failed to define VM: ")
        else:
            st.success("VM successfully defined!")
    except libvirt.libvirtError as e:
        st.error(f"Failed to create VM: {e}")
    finally:
        conn.close()
def manage_vm(action, vm_name):
    conn=libvirt.open('qemu:///system')
    if conn is None:
        st.error("Failed to open connection to libvirt")
        return
    try:
        dom=conn.lookupByName(vm_name)
        if action == "start":
            dom.create()
            st.success(f"Virtual machine '{vm_name}' started.")
        elif action == "shutdown":
            dom.shutdown()
            st.success(f"Virtual machine '{vm_name}' stopped.")
        elif action == "delete":
            dom.underfine()
            st.success(f"Virtual machine '{vm_name}' deleted.")
    except libvirt.libvirtError as e:
        st.error(f"Failed to {action} virtual machine: {e}")
    finally:
        conn.close()


def main():
    st.set_page_config(page_title="VM Rental", page_icon=":computer:")
    st.title("Virtual Machine Rental Configurator")

    with st.sidebar:
        st.header("Configuration Parameters")
        cpu = st.slider("CPU Cores", 1, 32, 4)
        ram = st.slider("RAM (GB)", 1, 128, 8)
        storage = st.number_input("Storage (GB)", 10, 1000, step=10)
        os_name = st.selectbox("Operating System", ["Ubuntu", "CentOS", "Windows Server"])
        location = st.selectbox("Location", ["US East", "US West", "Europe", "Asia"])
        duration = st.slider("Rental Duration (Days)", 1, 365, 30)

        price = 10 + cpu * 2 + ram * 1.5 + storage * 0.1 + duration * 0.5
        st.subheader("Estimated Price")
        st.write(f"**${price:.2f}**")

        if st.button("Rent Now"):
            try:
                result = create_vm(cpu, ram, storage, os_name, location, duration)
                st.success(result)
            except Exception as e:
                st.error(str(e))
        vm_name=st.text_input("Enter VM name to manage")
        if st.button("Start VM"):
            manage_vm("start", vm_name)
        if st.button("Stop VM"):
            manage_vm("stop", vm_name)
        if st.button("Delete VM"):
            manage_vm("delete", vm_name)


if __name__ == "__main__":
    main()
