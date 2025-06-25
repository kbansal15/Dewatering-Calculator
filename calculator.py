import streamlit as st
import pandas as pd
import io
from scipy.interpolate import interp1d
import numpy as np
import re # Import regex module to extract HP

# Data extracted from the graph, now in CSV format
# This data will be used to create the interpolation functions for each pump
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
DJ-7506 75HP,43500,30
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

# Read the CSV data into a Pandas DataFrame
df = pd.read_csv(io.StringIO(graph_data_csv))

# Get unique pump models for the dropdown
pump_models = df['Pump Model'].unique().tolist()

# Define the electricity cost symbol
electricity_cost_per_kwh_symbol = "₹" # Set the symbol to Indian Rupee

# Conversion factor from HP to kW
HP_TO_KW = 0.7457

# Function to extract HP from pump model string
def extract_hp_from_model_name(model_name):
    match = re.search(r'(\d+)HP', model_name)
    if match:
        return float(match.group(1))
    return 0.0 # Return 0 if HP not found in name

# Streamlit UI
st.set_page_config(layout="centered", page_title="Pump Performance Calculator")

st.title("💧 Pump Performance & Sump Emptying Time Calculator")
st.markdown("""
This application estimates the pump's discharge (flow rate) and the time required to empty a sump. It also calculates the estimated electricity cost
using the pump's rated power and efficiency.
""")

st.header(" 🔧 Pump Selection and Operating Conditions")

# Input for Pump Model (HP)
selected_pump_model = st.selectbox(
    "Select Pump Model (HP):",
    pump_models,
    help="Choose the pump model from the available options based on its Horsepower."
)

# Input for Head
head_input = st.number_input(
    "Enter Head in Meters:",
    min_value=0.0,
    value=30.0, # Default value for demonstration
    step=0.1,
    help="The vertical distance the pump needs to lift the fluid."
)

st.header("🌊 Sump Details")

# Input for Sump Volume in kL
sump_volume_kl = st.number_input(
    "Enter Sump Volume in Kiloliters (kL):",
    min_value=0.0,
    value=1000.0, # Default value for demonstration (10 kL = 10000 L)
    step=10.0,
    help="The total volume of the sump in Kiloliters (1 kL = 1000 Liters)."
)

# Convert sump volume from kL to Liters for calculations
sump_volume_liters = sump_volume_kl * 1000


# New input for number of pumps
num_pumps = st.number_input(
    "Number of Pumps Operating Simultaneously:",
    min_value=1,
    value=2, # Default to 2 pumps as requested
    step=1,
    help="Enter the number of identical pumps operating at the same conditions."
)

st.header("💰Cost and Efficiency")

# Input for Electricity Cost per kWh
electricity_cost_per_kwh = st.number_input(
    f"Electricity Cost per kWh ({electricity_cost_per_kwh_symbol}/kWh):",
    min_value=0.0,
    value=10.0, # Default value for demonstration (e.g., 7 INR per kWh)
    step=0.1,
    help="Enter the cost of electricity per kilowatt-hour in Rupees."
)

# Input for Pump Efficiency
pump_efficiency_percent = st.number_input(
    "Pump Efficiency (%):",
    min_value=0.1,
    max_value=100.0,
    value=80.0, # Default value for demonstration
    step=1.0,
    help="Enter the overall efficiency of the pump system in percentage (e.g., 70 for 70%)."
)


if st.button("Calculate Performance"):
    # Filter data for the selected pump model
    pump_df = df[df['Pump Model'] == selected_pump_model].copy()

    if pump_df.empty:
        st.error(f"No data found for pump model: {selected_pump_model}. Please select another.")
    else:
        # Sort data by Head in ascending order for interpolation
        pump_df = pump_df.sort_values(by='Head (Meters)', ascending=True)

        heads = pump_df['Head (Meters)'].values
        flows = pump_df['Flow (LPM)'].values

        # Check if there are enough points for interpolation for discharge calculation
        if len(heads) < 2:
            st.error(f"Not enough data points for {selected_pump_model} to perform discharge interpolation.")
        else:
            try:
                interp_func = interp1d(heads, flows, kind='linear', bounds_error=False, fill_value="extrapolate")
                
                # Calculate the discharge for a single pump at the input head
                single_pump_discharge = interp_func(head_input).item()

                # --- Handle extrapolation and invalid ranges for discharge ---
                min_head = heads.min()
                max_head = heads.max()
                
                is_extrapolated_low = head_input < min_head
                is_extrapolated_high = head_input > max_head

                if is_extrapolated_low or is_extrapolated_high:
                    st.warning(
                        f"⚠️ **Warning:** The entered Head ({head_input:.1f} meters) is outside "
                        f"the typical operating range for {selected_pump_model} "
                        f"(Head range: {min_head:.1f} to {max_head:.1f} meters). "
                        f"The **discharge** is an extrapolation and may not be accurate."
                    )
                    single_pump_discharge = max(0.0, single_pump_discharge)
                
                if single_pump_discharge < 0.0:
                     st.warning("Calculated discharge for a single pump is negative, which is physically impossible. Setting to 0 LPM.")
                     single_pump_discharge = 0.0

                # Calculate total discharge for multiple pumps
                total_discharge = single_pump_discharge * num_pumps

                st.subheader("Calculated Results:")
                st.metric(label=f"Estimated Discharge (Flow) for {num_pumps} Pump(s)", value=f"{total_discharge:.2f} LPM")
                st.metric(label="Individual Pump Discharge (for reference)", value=f"{single_pump_discharge:.2f} LPM")

                # Calculate time to empty sump
                if total_discharge > 0:
                    time_to_empty_minutes = sump_volume_liters / total_discharge
                    time_to_empty_days = time_to_empty_minutes / (60 * 24)
                    st.metric(
                        label="Time to Empty Sump",
                        value=f"{time_to_empty_days:.2f} days"
                    )

                    # --- New Power Calculation based on Rated Power * Efficiency ---
                    rated_hp = extract_hp_from_model_name(selected_pump_model)
                    if rated_hp == 0.0:
                        st.error(f"Could not extract rated HP from pump model name: {selected_pump_model}. Electricity cost cannot be calculated with this method.")
                        total_power_kw = 0
                        total_electricity_cost = 0
                    else:
                        rated_power_kw = rated_hp * HP_TO_KW
                        
                        # Ensure efficiency is not zero
                        if pump_efficiency_percent <= 0:
                            st.error("Pump efficiency must be greater than 0% to calculate electricity cost.")
                            total_power_kw = 0
                            total_electricity_cost = 0
                        else:
                            # Power Consumed (kW) = Rated Power (kW) * (Efficiency / 100)
                            # This implements the user's requested formula directly.
                            power_per_pump_kw = rated_power_kw * (pump_efficiency_percent / 100)
                            total_power_kw = power_per_pump_kw * num_pumps
                            
                            total_time_hours = time_to_empty_minutes / 60
                            total_electricity_cost = total_power_kw * total_time_hours * electricity_cost_per_kwh

                    st.metric(label=f"Total Power Consumption for {num_pumps} Pump(s)", value=f"{total_power_kw:.2f} kW")
                    st.metric(label="Estimated Electricity Cost", value=f"{electricity_cost_per_kwh_symbol}{total_electricity_cost:.2f}")

                else:
                    st.info("Total discharge is zero or negligible, sump will not empty (or will take infinite time), and electricity cost cannot be calculated.")

            except ValueError as e:
                st.error(f"Error during calculations: {e}. Please check your inputs and pump data.")
                st.info("Ensure pump data has sufficient points and head values are appropriate.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

st.markdown("---")
