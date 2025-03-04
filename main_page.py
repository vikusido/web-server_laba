import streamlit as st
st.set_page_config(
    page_title="VM Rental",
    page_icon=":computer:",
)

def calculate_price(cpu, ram, storage, duration):
    base_price = 10
    cpu_cost = cpu * 2
    ram_cost = ram * 1.5
    storage_cost = storage * 0.1
    duration_cost = duration * 0.5
    return base_price + cpu_cost + ram_cost + storage_cost + duration_cost

def main():
    st.title("Virtual Machine Rental Configurator")

    with st.sidebar:
        st.header("Configuration Parameters")

        cpu = st.slider("CPU Cores", min_value=1, max_value=32, value=4)
        ram = st.slider("RAM (GB)", min_value=1, max_value=128, value=8)
        storage = st.number_input("Storage (GB)", min_value=10, max_value=1000, step=10)
        os_options = ["Ubuntu", "CentOS", "Windows Server"]
        os = st.selectbox("Operating System", options=os_options)
        location_options = ["US East", "US West", "Europe", "Asia"]
        location = st.selectbox("Location", options=location_options)
        duration = st.slider("Rental Duration (Days)", min_value=1, max_value=365, value=30)

        st.header("Configuration Summary")
        st.write(f"**CPU Cores:** {cpu}")
        st.write(f"**RAM:** {ram} GB")
        st.write(f"**Storage:** {storage} GB")
        st.write(f"**Operating System:** {os}")
        st.write(f"**Location:** {location}")
        st.write(f"**Rental Duration:** {duration} days")

        price = calculate_price(cpu, ram, storage, duration)
        st.subheader("Estimated Price")
        st.write(f"**${price:.2f}**")

        if st.button("Rent Now"):
            st.success("Rental request submitted!")
            st.write("Your VM will be provisioned shortly.")
            st.write("Selected Parameters:")
            st.write({
            "cpu": cpu,
            "ram": ram,
            "storage": storage,
            "os": os,
            "location": location,
            "duration": duration,
            "price": price,
        })

if __name__ == "__main__":
    main()