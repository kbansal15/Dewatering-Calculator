import streamlit as st
import pandas as pd
import io
from scipy.interpolate import interp1d
import numpy as np
import re

# Data extracted from the graph
graph_data_csv = """Pump Model,Flow (LPM),Head (Meters)
DJ-10006 100HP,0,88
DJ-10006 100HP,600,86
DJ-10006 100HP,1200,84
DJ-10006 100HP,1800,82
DJ-10006 100HP,2400,80
DJ-10006 100HP,3000,78
DJ-10006 100HP,3600,74
DJ-10006 100HP,4200,68
DJ-10006 100HP,4800,58
DJ-10006 100HP,5000,48
DJ-10006 100HP,5200,40
DJ-10006 100HP,5400,32
DJ-7506 75HP,0,68
DJ-7506 75HP,600,66
DJ-7506 75HP,1200,65
DJ-7506 75HP,1800,63
DJ-7506 75HP,2400,61
DJ-7506 75HP,3000,58
DJ-7506 75HP,3600,50
DJ-7506 75HP,4200,38
DJ-7506 75HP,4350,30
DJ-7506 75HP,4500,24
DJ-7506 75HP,4650,20
DJ-7506 75HP,4700,16
DJ-5006 50HP,0,60
DJ-5006 50HP,600,59
DJ-5006 50HP,1200,57
DJ-5006 50HP,1800,53
DJ-5006 50HP,2400,51
DJ-5006 50HP,3000,50
DJ-5006 50HP,3600,43
DJ-5006 50HP,3600,39
DJ-5006 50HP,4200,32
DJ-5006 50HP,4500,20
DJ-5006 50HP,4650,13
DJ-4006 40HP,0,50
DJ-4006 40HP,600,49
DJ-4006 40HP,1200,47
DJ-4006 40HP,1800,44
DJ-4006 40HP,2400,40
DJ-4006 40HP,3000,34
DJ-4006 40HP,3600,26
DJ-4006 40HP,4000,18
DJ-3506 35HP,0,45
DJ-3506 35HP,600,44
DJ-3506 35HP,1200,42
DJ-3506 35HP,1800,39
DJ-3506 35HP,2400,34
DJ-3506 35HP,3000,28
DJ-3506 35HP,3400,20
DJ-3006 30HP,0,47.5
DJ-3006 30HP,400,47
DJ-3006 30HP,600,46
DJ-3006 30HP,1200,41
DJ-3006 30HP,1600,40
DJ-3006 30HP,1800,38
DJ-3006 30HP,2000,35
DJ-3006 30HP,2400,30
DJ-3006 30HP,2600,24
DJ-3006 30HP,2800,21
DJ-3006 30HP,3000,16
DJ-3006 30HP,3100,10
DJ-2506 25HP,0,43
DJ-2506 25HP,400,42
DJ-2506 25HP,800,40
DJ-2506 25HP,1200,37
DJ-2506 25HP,1600,33
DJ-2506 25HP,2000,28
DJ-2506 25HP,2400,21
DJ-2506 25HP,2800,12
DJ-2006 20HP,0,37
DJ-2006 20HP,400,36
DJ-2006 20HP,800,34
DJ-2006 20HP,1200,31
DJ-2006 20HP,1600,27
DJ-2006 20HP,2000,21
DJ-2006 20HP,2400,14
DJ-2006 20HP,2800,6
DJ-1506 15HP,0,26
DJ-1506 15HP,400,25
DJ-1506 15HP,800,23
DJ-1506 15HP,1200,20
DJ-1506 15HP,1600,16
DJ-1506 15HP,2000,11
DJ-1506 15HP,2400,5
"""

df = pd.read_csv(io.StringIO(graph_data_csv))
pump_models = df['Pump Model'].unique().tolist()
electricity_cost_per_kwh_symbol = "₹"
HP_TO_KW = 0.7457

def extract_hp_from_model_name(model_name):
    match = re.search(r'(\d+)HP', model_name)
    if match:
        return float(match.group(1))
    return 0.0

# UI Setup
st.set_page_config(layout="centered", page_title="Pump Performance Calculator")
st.title("💧 Pump Performance & Sump Emptying Time Calculator")
st.markdown("""This app estimates the adjusted pump discharge and sump emptying time based on selected pump efficiency.""")

st.header(" 🔧 Pump Selection and Operating Conditions")
selected_pump_model = st.selectbox("Select Pump Model (HP):", pump_models)
head_input = st.number_input("Enter Head in Meters:", min_value=0.0, value=30.0, step=0.1)
st.header("🌊 Sump Details")
sump_volume_kl = st.number_input("Enter Sump Volume in Kiloliters (kL):", min_value=0.0, value=1000.0, step=10.0)
sump_volume_liters = sump_volume_kl * 1000
num_pumps = st.number_input("Number of Pumps Operating Simultaneously:", min_value=1, value=2, step=1)
st.header("💰Cost and Efficiency")
electricity_cost_per_kwh = st.number_input(f"Electricity Cost per kWh ({electricity_cost_per_kwh_symbol}/kWh):", min_value=0.0, value=10.0, step=0.1)
pump_efficiency_percent = st.number_input("Pump Efficiency (%):", min_value=0.1, max_value=100.0, value=80.0, step=1.0)

if st.button("Calculate Performance"):
    pump_df = df[df['Pump Model'] == selected_pump_model].copy()
    if pump_df.empty:
        st.error(f"No data found for pump model: {selected_pump_model}.")
    else:
        pump_df = pump_df.sort_values(by='Head (Meters)', ascending=True)
        heads = pump_df['Head (Meters)'].values
        flows = pump_df['Flow (LPM)'].values

        if len(heads) < 2:
            st.error(f"Not enough data for interpolation.")
        else:
            try:
                interp_func = interp1d(heads, flows, kind='linear', bounds_error=False, fill_value="extrapolate")
                single_pump_discharge = interp_func(head_input).item()

                min_head = heads.min()
                max_head = heads.max()
                if head_input < min_head or head_input > max_head:
                    st.warning(f"⚠️ Head ({head_input} m) is outside the data range ({min_head}–{max_head} m). Result may be extrapolated.")
                    single_pump_discharge = max(0.0, single_pump_discharge)

                # ✅ Adjusting discharge by pump efficiency
                efficiency_factor = pump_efficiency_percent / 100
                adjusted_single_pump_discharge = single_pump_discharge * efficiency_factor
                total_discharge = adjusted_single_pump_discharge * num_pumps

                st.subheader("Calculated Results:")
                st.metric(f"Adjusted Total Discharge (Flow) for {num_pumps} Pump(s)", f"{total_discharge:.2f} LPM")
                st.metric("Adjusted Individual Pump Discharge", f"{adjusted_single_pump_discharge:.2f} LPM")

                if total_discharge > 0:
                    time_to_empty_minutes = sump_volume_liters / total_discharge
                    time_to_empty_days = time_to_empty_minutes / (60 * 24)
                    st.metric("Time to Empty Sump", f"{time_to_empty_days:.2f} days")

                    rated_hp = extract_hp_from_model_name(selected_pump_model)
                    if rated_hp == 0.0:
                        st.error("Could not extract rated HP. Electricity cost cannot be calculated.")
                    else:
                        rated_power_kw = rated_hp * HP_TO_KW
                        power_per_pump_kw = rated_power_kw * efficiency_factor
                        total_power_kw = power_per_pump_kw * num_pumps
                        total_time_hours = time_to_empty_minutes / 60
                        total_electricity_cost = total_power_kw * total_time_hours * electricity_cost_per_kwh

                        st.metric(f"Total Power Consumption for {num_pumps} Pump(s)", f"{total_power_kw:.2f} kW")
                        st.metric("Estimated Electricity Cost", f"{electricity_cost_per_kwh_symbol}{total_electricity_cost:.2f}")
                else:
                    st.info("Total discharge is too low. Cannot compute time or cost.")

            except Exception as e:
                st.error(f"Error: {e}")
