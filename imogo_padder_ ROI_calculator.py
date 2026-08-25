import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ====================== LÖSENORDSSKYDD ======================
def check_password():
    try:
        CORRECT_PASSWORD = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        return True 

    def password_entered():
        if st.session_state.get("password_input") == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            if "password_input" in st.session_state:
                del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter password to gain access:", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password to gain access:", type="password", on_change=password_entered, key="password_input")
        st.error("🔒 Incorrect password. Please try again.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ====================== KONFIGURATION & FUNKTIONER ======================
st.set_page_config(page_title="Imogo Dye-max ROI Calculator", layout="wide", page_icon="💰")

def format_num(value):
    return "{:,.0f}".format(value).replace(",", " ")

st.title("💰 Imogo Dye-max vs Traditional Padder – ROI Calculator")

# ====================== INITIALISERING ======================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.local_currency = "EUR"
    st.session_state.currency_rate = 1.0
    st.session_state.prev_rate = 1.0
    st.session_state.ui_elec = 0.15
    st.session_state.ui_water = 0.0001
    st.session_state.ui_dye = 6.0
    st.session_state.ui_chem_a = 2.0
    st.session_state.ui_chem_b = 3.0
    st.session_state.ui_chem_c = 5.0
    st.session_state.ui_waste = 0.002
    st.session_state.ui_labor = 2.0
    st.session_state.ui_inv = 550000.0
    st.session_state.ui_price_a = 2.8
    st.session_state.ui_price_b = 1.8
    st.session_state.ui_price_waste = 0.8
    st.session_state.ui_co2 = 0.20

# ====================== SIDEBAR ======================
with st.sidebar:
    customer_name = st.text_input("Customer name", value="", key="customer_name_input")
    curr = st.text_input("Currency (i.e. EUR, SEK, USD)", value="EUR", key="curr_input").strip().upper()
    current_rate = st.session_state.get("conv_key", 1.00)
    conv = st.number_input(f"Exchange rate (1 EUR = {current_rate:.2f} {curr})", value=1.00, step=0.10, format="%.2f", key="conv_key")
    
    if "prev_rate" not in st.session_state:
        st.session_state.prev_rate = 1.0
        
    if conv != st.session_state.prev_rate:
        factor = conv / st.session_state.prev_rate if st.session_state.prev_rate != 0 else 1.0
        cost_keys = [
            "ui_elec", "ui_water", "ui_dye", "ui_chem_a", "ui_chem_b", 
            "ui_chem_c", "ui_waste", "ui_labor", "ui_inv", 
            "ui_price_a", "ui_price_b", "ui_price_waste"
        ]
        for k in cost_keys:
            if k in st.session_state:
                st.session_state[k] *= factor
        st.session_state.prev_rate = conv
        st.rerun()

    st.header(f"Costs ({curr})")
    st.number_input(f"Electricity ({curr}/kWh)", key="ui_elec", format="%.3f")
    st.number_input(f"Water ({curr}/L)", key="ui_water", format="%.4f")
    st.number_input(f"Dye stuff ({curr}/kg)", key="ui_dye")
    st.number_input(f"Wetting Agent ({curr}/kg)", key="ui_chem_a")
    st.number_input(f"Soda Ash ({curr}/kg)", key="ui_chem_b")
    st.number_input(f"NAOH 50% ({curr}/kg)", key="ui_chem_c")
    st.number_input(f"Waste handling ({curr}/L)", key="ui_waste", format="%.4f")
    st.number_input(f"Labor ({curr}/man-hour)", key="ui_labor")
    st.number_input("CO₂ kg/kWh", key="ui_co2", format="%.2f", step=0.01)
    st.number_input(f"Investment cost ({curr})", key="ui_inv")
    
    st.subheader(f"Tygpriser ({curr}/kg)")
    st.number_input(f"Price A-quality fabric", key="ui_price_a")
    st.number_input(f"Price B-quality fabric", key="ui_price_b")
    st.number_input(f"Price Waste fabric", key="ui_price_waste")

# ====================== KONVERTERING ======================
elec_price = st.session_state.ui_elec
water_price = st.session_state.ui_water
dye_stuff_price = st.session_state.ui_dye
chem_a_price = st.session_state.ui_chem_a
chem_b_price = st.session_state.ui_chem_b
chem_c_price = st.session_state.ui_chem_c
waste_handling_price = st.session_state.ui_waste
labor_price = st.session_state.ui_labor
investment_cost = st.session_state.ui_inv
price_a_fabric = st.session_state.ui_price_a
price_b_fabric = st.session_state.ui_price_b
price_waste_fabric = st.session_state.ui_price_waste

# ====================== PARAMETRAR ======================
col_s1, col_s2 = st.columns(2)

with col_s1:
    fabric_width = st.number_input("Fabric width (m)", value=2.0, step=0.1, key="fabric_width")
    fabric_gsm = st.number_input("Fabric GSM (kg/m²)", value=0.18, step=0.01, key="fabric_gsm")
    working_hours_day = st.number_input("Working hours per day (h)", value=24.0, step=0.5, key="working_hours_day")
    prod_speed = st.number_input("Production speed (m/min)", value=20.0, step=0.1, key="prod_speed")

with col_s2:
    rolls_day = st.number_input("Batches/Rolls per day", value=14.0, step=1.0, key="rolls_day")
    days_year = st.number_input("Working days per year", value=300, step=1, key="days_year")
    changeovers_day = st.number_input("Bath changes per day", value=9, step=1, key="changeovers_day")

est_changeover_time = 20 
eff_hours_day = working_hours_day - (changeovers_day * est_changeover_time / 60.0)

meters_per_roll = (prod_speed * 60 * eff_hours_day) / rolls_day if rolls_day > 0 else 0
weight_per_roll = meters_per_roll * fabric_width * fabric_gsm

top_banner_placeholder = st.empty()
prod_summary_placeholder = st.container()

# ====================== MACHINE SPECIFIC ======================
col_p, col_i = st.columns(2)
with col_p:
    st.subheader("🟠 Traditional Padder")
    p_ch = st.number_input("Changeover time (min)", value=30, key="p_ch")
    
    # Uppdaterat med format="%d" för att ta bort decimaler
    p_pickup = st.number_input("Pickup (%)", value=100, step=1, format="%d", key="p_pickup")
    p_disp = p_pickup / 100.0
    
    p_dye = st.number_input("Dye conc (%)", value=4.0, key="p_dye")
    p_dye_conc_g_l = (p_dye * 10) / p_disp if p_disp > 0 else 0
    st.info(f"Concentration: {p_dye_conc_g_l:.1f} g/L")
    
    p_a = st.number_input("Wetting Agent (g/L at 100% pickup)", value=3.0, key="p_a")
    p_b = st.number_input("Soda Ash (g/L at 100% pickup)", value=2.0, key="p_b")
    p_c = st.number_input("NAOH 50% (g/L at 100% pickup)", value=1.5, key="p_c")
    p_w = st.number_input("Waste water/changeover (L)", value=70, key="p_w")
    p_startup = st.number_input("Startup waste (m)", value=50.0, key="p_startup")
    p_en = st.number_input("Energy (kWh/kg)", value=0.05, format="%.4f", key="p_en")
    p_bq = st.number_input("B-quality fabric (%)", value=4.0, key="p_bq")
    p_wf = st.number_input("Waste fabric (%)", value=1.0, key="p_wf")
    
    # Beräkna faktiska koncentrationer baserat på vald pickup (%)
    p_a_conc_g_l = p_a / p_disp if p_disp > 0 else 0
    p_b_conc_g_l = p_b / p_disp if p_disp > 0 else 0
    p_c_conc_g_l = p_c / p_disp if p_disp > 0 else 0

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-top: 10px; border: 1px solid #b6e0fe;">
        <strong>📋 Actual Bath Concentrations (Padder):</strong><br>
        • Dye: <b>{p_dye_conc_g_l:.1f} g/L</b><br>
        • Wetting Agent: <b>{p_a_conc_g_l:.1f} g/L</b><br>
        • Soda Ash: <b>{p_b_conc_g_l:.1f} g/L</b><br>
        • NAOH 50%: <b>{p_c_conc_g_l:.1f} g/L</b>
    </div>
    """, unsafe_allow_html=True)

with col_i:
    st.subheader("🔵 Imogo Dye-max")
    i_ch = st.number_input("Changeover time (min)", value=20, key="i_ch")
    
    # Uppdaterat med format="%d" för att ta bort decimaler
    i_pickup = st.number_input("Pickup (%)", value=100, step=1, format="%d", key="i_pickup")
    i_disp = i_pickup / 100.0
    
    i_dye = st.number_input("Dye conc (%)", value=4.0, key="i_dye")
    i_dye_conc_g_l = (i_dye * 10) / i_disp if i_disp > 0 else 0
    st.info(f"Concentration: {i_dye_conc_g_l:.1f} g/L")
    
    i_a = st.number_input("Wetting Agent (g/L at 100% pickup)", value=3.0, key="i_a")
    i_b = st.number_input("Soda Ash (g/L at 100% pickup)", value=2.0, key="i_b")
    i_c = st.number_input("NAOH 50% (g/L at 100% pickup)", value=1.5, key="i_c")
    i_w = st.number_input("Waste water/changeover (L)", value=15, key="i_w")
    i_startup = st.number_input("Startup waste (m)", value=7.0, key="i_startup")
    i_en = st.number_input("Energy (kWh/kg)", value=0.035, format="%.4f", key="i_en")
    i_bq = st.number_input("B-quality fabric (%)", value=3.0, key="i_bq")
    i_wf = st.number_input("Waste fabric (%)", value=0.5, key="i_wf")
    
    # Beräkna faktiska koncentrationer baserat på vald pickup (%)
    i_a_conc_g_l = i_a / i_disp if i_disp > 0 else 0
    i_b_conc_g_l = i_b / i_disp if i_disp > 0 else 0
    i_c_conc_g_l = i_c / i_disp if i_disp > 0 else 0

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-top: 10px; border: 1px solid #b6e0fe;">
        <strong>📋 Actual Bath Concentrations (Imogo):</strong><br>
        • Dye: <b>{i_dye_conc_g_l:.1f} g/L</b><br>
        • Wetting Agent: <b>{i_a_conc_g_l:.1f} g/L</b><br>
        • Soda Ash: <b>{i_b_conc_g_l:.1f} g/L</b><br>
        • NAOH 50%: <b>{i_c_conc_g_l:.1f} g/L</b>
    </div>
    """, unsafe_allow_html=True)

# ====================== INJEKTERA BANNERN ======================
p_roll_weight_wet = weight_per_roll * (1 + p_disp)
i_roll_weight_wet = weight_per_roll * (1 + i_disp)

if p_roll_weight_wet > 1500 or i_roll_weight_wet > 1500:
    bg_color = "#f8d7da"
    text_color = "#721c24"
    warning = " ⚠️"
else:
    bg_color = "#e8f4fd"
    text_color = "#1e3a8a"
    warning = ""

with top_banner_placeholder.container():
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; font-size: 1.1em; color: {text_color};">
        <strong>Fabric length per roll:</strong> {meters_per_roll:,.0f} m 
        <span style="margin: 0 15px; opacity: 0.5;">|</span> 
        <strong>Fabric weight per roll:</strong> {weight_per_roll:,.1f} kg
        <span style="margin: 0 15px; opacity: 0.5;">|</span> 
        <strong>Roll wet weight total:</strong> {i_roll_weight_wet:.1f} kg{warning}
    </div>
    """, unsafe_allow_html=True)
    
    with st.popover("ℹ️"):
        st.write("Max wet roll weight is 1500 kg.")
# ====================== BERÄKNINGAR ======================
effective_hours_p = working_hours_day - (changeovers_day * p_ch / 60.0)
p_daily_m = prod_speed * 60 * effective_hours_p
p_daily_kg = p_daily_m * fabric_width * fabric_gsm
base_annual_kg = p_daily_kg * days_year

effective_hours_i = working_hours_day - (changeovers_day * i_ch / 60.0)
i_daily_m = prod_speed * 60 * effective_hours_i
i_daily_kg = i_daily_m * fabric_width * fabric_gsm
i_annual_kg_potential = i_daily_kg * days_year

extra_annual_kg = i_annual_kg_potential - base_annual_kg
annual_changeovers = changeovers_day * days_year

with prod_summary_placeholder:
    st.markdown("---")
    st.subheader("📊 Production Volume Summary")
    col_sum1, col_sum2 = st.columns(2)

    with col_sum1:
        st.metric("**Traditional Padder**", f"{format_num(base_annual_kg)} kg/year")
        st.caption(f"**{format_num(p_daily_m)} m/day** | **{format_num(p_daily_kg)} kg/day** | **{prod_speed:.1f} m/min**")

    with col_sum2:
        st.metric(
            "**Imogo Dye-Max**", 
            f"{format_num(base_annual_kg)} kg/year", 
            delta=f"↑ {format_num(extra_annual_kg)} kg/year extra capacity"
        )
        st.caption(f"**{format_num(p_daily_m)} m/day** | **{format_num(p_daily_kg)} kg/day** | **{prod_speed:.1f} m/min**")
    st.markdown("---")

p_disp_L = base_annual_kg * p_disp
i_disp_L = base_annual_kg * i_disp
p_dye_g_per_l = (p_dye / 100 * 1000) / p_disp if p_disp > 0 else 0
i_dye_g_per_l = (i_dye / 100 * 1000) / i_disp if i_disp > 0 else 0

p_dye_kg = base_annual_kg * (p_dye / 100)
i_dye_kg = base_annual_kg * (i_dye / 100)

p_startup_waste_kg = annual_changeovers * p_startup * fabric_width * fabric_gsm
i_startup_waste_kg = annual_changeovers * i_startup * fabric_width * fabric_gsm

p_startup_dye_kg = p_startup_waste_kg * (p_dye / 100)
i_startup_dye_kg = i_startup_waste_kg * (i_dye / 100)

p_waste_L = annual_changeovers * p_w
i_waste_L = annual_changeovers * i_w

p_changeover_dye_kg = p_waste_L * (p_dye_g_per_l / 1000)
i_changeover_dye_kg = i_waste_L * (i_dye_g_per_l / 1000)

total_dye_savings_kg = (p_dye_kg + p_startup_dye_kg + p_changeover_dye_kg) - (i_dye_kg + i_startup_dye_kg + i_changeover_dye_kg)
total_dye_savings = total_dye_savings_kg * dye_stuff_price

p_chem_a_kg = p_disp_L * (p_a / 1000) + (p_startup_waste_kg * p_disp * (p_a / 1000)) + (p_waste_L * (p_a / 1000))
i_chem_a_kg = i_disp_L * (i_a / 1000) + (i_startup_waste_kg * i_disp * (i_a / 1000)) + (i_waste_L * (i_a / 1000))
total_chem_a_savings_kg = p_chem_a_kg - i_chem_a_kg

p_chem_b_kg = p_disp_L * (p_b / 1000) + (p_startup_waste_kg * p_disp * (p_b / 1000)) + (p_waste_L * (p_b / 1000))
i_chem_b_kg = i_disp_L * (i_b / 1000) + (i_startup_waste_kg * i_disp * (i_b / 1000)) + (i_waste_L * (i_b / 1000))
total_chem_b_savings_kg = p_chem_b_kg - i_chem_b_kg

p_chem_c_kg = p_disp_L * (p_c / 1000) + (p_startup_waste_kg * p_disp * (p_c / 1000)) + (p_waste_L * (p_c / 1000))
i_chem_c_kg = i_disp_L * (i_c / 1000) + (i_startup_waste_kg * i_disp * (i_c / 1000)) + (i_waste_L * (i_c / 1000))
total_chem_c_savings_kg = p_chem_c_kg - i_chem_c_kg

total_chem_savings_kg = total_chem_a_savings_kg + total_chem_b_savings_kg + total_chem_c_savings_kg
total_chem_savings = (total_chem_a_savings_kg * chem_a_price) + (total_chem_b_savings_kg * chem_b_price) + (total_chem_c_savings_kg * chem_c_price)

p_total_water = (base_annual_kg * p_disp) + (p_startup_waste_kg * p_disp) + p_waste_L
i_total_water = (base_annual_kg * i_disp) + (i_startup_waste_kg * i_disp) + i_waste_L
water_savings = (p_total_water - i_total_water) * water_price

p_total_energy = (base_annual_kg + p_startup_waste_kg) * p_en
i_total_energy = (base_annual_kg + i_startup_waste_kg) * i_en
energy_savings = (p_total_energy - i_total_energy) * elec_price

waste_savings = (p_waste_L - i_waste_L) * waste_handling_price

p_labor_cost = (annual_changeovers * p_ch / 60) * labor_price
i_labor_cost = (annual_changeovers * i_ch / 60) * labor_price
labor_savings = p_labor_cost - i_labor_cost

p_b_quality_kg = base_annual_kg * (p_bq / 100)
i_b_quality_kg = base_annual_kg * (i_bq / 100)
p_waste_fabric_kg = base_annual_kg * (p_wf / 100)
i_waste_fabric_kg = base_annual_kg * (i_wf / 100)

b_quality_savings = (p_b_quality_kg - i_b_quality_kg) * (price_a_fabric - price_b_fabric)
waste_fabric_savings = (p_waste_fabric_kg - i_waste_fabric_kg) * (price_a_fabric - price_waste_fabric)

annual_savings = total_dye_savings + total_chem_savings + water_savings + energy_savings + waste_savings + labor_savings + b_quality_savings + waste_fabric_savings
payback_months = (investment_cost / annual_savings * 12) if annual_savings > 0 else 0

water_savings_m3 = (p_total_water - i_total_water) / 1000

co2_kg_per_kwh = st.session_state.ui_co2

# Räknar om till kWh för att matcha bilden, istället för MWh
water_savings_m3 = (p_total_water - i_total_water) / 1000
energy_savings_kwh = p_total_energy - i_total_energy
co2_savings_tonnes = (energy_savings_kwh * co2_kg_per_kwh) / 1000

p_total_dye = p_dye_kg + p_startup_dye_kg + p_changeover_dye_kg
p_total_chem = p_chem_a_kg + p_chem_b_kg + p_chem_c_kg
i_total_dye = i_dye_kg + i_startup_dye_kg + i_changeover_dye_kg
i_total_chem = i_chem_a_kg + i_chem_b_kg + i_chem_c_kg

p_total_cost = (p_total_dye * dye_stuff_price) + (p_chem_a_kg * chem_a_price) + (p_chem_b_kg * chem_b_price) + (p_chem_c_kg * chem_c_price) + (p_total_water * water_price) + (p_total_energy * elec_price) + (p_waste_L * waste_handling_price) + p_labor_cost + (p_b_quality_kg * (price_a_fabric - price_b_fabric)) + (p_waste_fabric_kg * (price_a_fabric - price_waste_fabric))
i_total_cost = (i_total_dye * dye_stuff_price) + (i_chem_a_kg * chem_a_price) + (i_chem_b_kg * chem_b_price) + (i_chem_c_kg * chem_c_price) + (i_total_water * water_price) + (i_total_energy * elec_price) + (i_waste_L * waste_handling_price) + i_labor_cost + (i_b_quality_kg * (price_a_fabric - price_b_fabric)) + (i_waste_fabric_kg * (price_a_fabric - price_waste_fabric))

p_cost_per_kg = p_total_cost / base_annual_kg if base_annual_kg > 0 else 0
i_cost_per_kg = i_total_cost / base_annual_kg if base_annual_kg > 0 else 0

# ====================== NYA UI-UPPDATERINGAR ENLIGT BILDER ======================

st.markdown("---")
st.header("📈 Savings Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Annual Savings", f"{curr} {format_num(annual_savings)}")
col2.metric("Payback Period", f"{payback_months:.0f} months")
col3.metric("Dye Stuff Savings", f"{format_num(total_dye_savings_kg)} kg/year")
col4.metric("Chemistry Savings", f"{format_num(total_chem_savings_kg)} kg/year")

st.write("") # Skapar lite visuell rymd mellan raderna

st.header("🌍 Environmental Savings")
col_env1, col_env2, col_env3 = st.columns(3)
col_env1.metric("Water Savings", f"{format_num(water_savings_m3)} m³/year")
col_env2.metric("CO₂ Savings", f"{co2_savings_tonnes:.1f} tonnes/year")
col_env3.metric("Energy Savings", f"{format_num(energy_savings_kwh)} kWh/year")

st.markdown("---")
st.header("💰 Total Cost per kg Fabric")

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric("Traditional Padder", f"{curr} {p_cost_per_kg:.2f} / kg")

with col_c2:
    cost_diff = p_cost_per_kg - i_cost_per_kg
    cost_diff_pct = (cost_diff / p_cost_per_kg) * 100 if p_cost_per_kg > 0 else 0
    # Streamlit skapar automatiskt pilen nedåt när strängen börjar med '-', och 'inverse' gör den grön
    delta_str = f"-{curr} {cost_diff:.2f} / kg ({cost_diff_pct:.1f}%)"
    st.metric("Imogo Dye-Max", f"{curr} {i_cost_per_kg:.2f} / kg", delta=delta_str, delta_color="inverse")


# ====================== DETALJERAD INFO ======================
st.markdown("---")
st.header("📊 Detailed Savings Breakdown")
breakdown_data = {
    "Category": ["Dye Stuff", "Chemistry", "Water", "Energy", "Waste Handling", "Labor", "B-Quality Reduction", "Waste Fabric Reduction"],
    "Savings (" + curr + ")": [total_dye_savings, total_chem_savings, water_savings, energy_savings, waste_savings, labor_savings, b_quality_savings, waste_fabric_savings]
}
df_breakdown = pd.DataFrame(breakdown_data)
df_breakdown = df_breakdown.sort_values(by="Savings (" + curr + ")", ascending=False)
st.dataframe(df_breakdown.style.format({"Savings (" + curr + ")": "{:,.0f}"}), use_container_width=True)

# ====================== VISUALISERING ENLIGT BILD ======================

st.markdown("---")

# 1. Yearly savings per category (Liggande staplar)
categories = [
    "Dye Stuff", "Chem A", "Chem B", "Chem C", 
    "Process Water", "Waste Handling", "Energy", 
    "Labor", "B-Quality", "Waste Fabric"
]

savings_values = [
    total_dye_savings,
    total_chem_a_savings_kg * chem_a_price,
    total_chem_b_savings_kg * chem_b_price,
    total_chem_c_savings_kg * chem_c_price,
    water_savings,
    waste_savings,
    energy_savings,
    labor_savings,
    b_quality_savings,
    waste_fabric_savings
]

fig_savings = go.Figure(go.Bar(
    x=savings_values,
    y=categories,
    orientation='h',
    marker_color='#00bfff'
))
fig_savings.update_layout(
    title=f"Yearly savings per category ({curr}/year)",
    xaxis_title=f"{curr} Savings",
    yaxis=dict(autorange="reversed"),  # För att få Dye Stuff högst upp som på bilden
    height=450
)
st.plotly_chart(fig_savings, use_container_width=True)

# 2. Total Cost per kg Fabric (Stående staplar)
fig_cost = go.Figure(go.Bar(
    x=['Traditional Padder', 'Imogo Dye-max'],
    y=[p_cost_per_kg, i_cost_per_kg],
    marker_color=['#ff5252', '#00c896']
))
fig_cost.update_layout(
    title=f"Total Cost per kg Fabric ({curr})",
    yaxis_title=f"{curr} / kg",
    height=400
)
st.plotly_chart(fig_cost, use_container_width=True)
# ====================== RAPPORTGENERERING ======================
def generate_html_report():
    html_content = f"""
    <html>
    <head>
        <title>Imogo Dye-max ROI Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            h1, h2, h3 {{ color: #1e3a8a; }}
            .summary-box {{ background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #e5e7eb; }}
            .highlight {{ color: #059669; font-weight: bold; }}
            .footer {{ margin-top: 40px; font-size: 0.9em; color: #666; text-align: center; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div style="text-align: right; color: #666;">Date: {datetime.now().strftime("%Y-%m-%d")}</div>
        <h1>Imogo Dye-max ROI Analysis</h1>
        <h3>Customer: {customer_name if customer_name else "Not specified"}</h3>
        
        <div class="summary-box">
            <h2>Financial Summary</h2>
            <p><strong>Total Annual Savings:</strong> <span class="highlight">{format_num(annual_savings)} {curr}</span></p>
            <p><strong>Estimated Payback Time:</strong> <span class="highlight">{payback_months:.1f} months</span></p>
            <p><strong>Cost per kg (Padder):</strong> {curr} {p_cost_per_kg:.3f} / kg</p>
            <p><strong>Cost per kg (Imogo):</strong> {curr} {i_cost_per_kg:.3f} / kg</p>
        </div>

        <h2>Production Volume summary</h2>
        <p><strong>Daily Volume:</strong> {format_num(p_daily_m)} m/day ({format_num(p_daily_kg)} kg/day)</p>
        <p><strong>Total Base Annual Volume:</strong> {format_num(base_annual_kg)} kg/year</p>
        <p><strong>Extra Annual Capacity (Imogo):</strong> <span class="highlight">+{format_num(extra_annual_kg)} kg/year</span></p>

        <h2>Annual Environmental & Resource Savings</h2>
        <table>
            <tr><th>Resource</th><th>Savings</th></tr>
            <tr><td>Water</td><td>{format_num(water_savings_m3)} m³</td></tr>
            <tr><td>Energy</td><td>{format_num(energy_savings_kwh)} kWh</td></tr>
            <tr><td>CO2</td><td>{co2_savings_tonnes:.1f} tonnes</td></tr>
            <tr><td>Dye Stuff</td><td>{format_num(total_dye_savings_kg)} kg</td></tr>
            <tr><td>Chemistry</td><td>{format_num(total_chem_savings_kg)} kg</td></tr>
        </table>

        <h2>Detailed Savings Breakdown</h2>
        <table>
            <tr><th>Category</th><th>Savings ({curr})</th></tr>
            <tr><td>Dye Stuff</td><td>{format_num(total_dye_savings)}</td></tr>
            <tr><td>Chemistry</td><td>{format_num(total_chem_savings)}</td></tr>
            <tr><td>Water</td><td>{format_num(water_savings)}</td></tr>
            <tr><td>Energy</td><td>{format_num(energy_savings)}</td></tr>
            <tr><td>Waste Handling</td><td>{format_num(waste_savings)}</td></tr>
            <tr><td>Labor</td><td>{format_num(labor_savings)}</td></tr>
            <tr><td>B-Quality Fabric</td><td>{format_num(b_quality_savings)}</td></tr>
            <tr><td>Waste Fabric</td><td>{format_num(waste_fabric_savings)}</td></tr>
        </table>

        <h2>Machine Parameters</h2>
        <table>
            <tr><th>Parameter</th><th>Traditional Padder</th><th>Imogo Dye-max</th></tr>
            <tr><td>Changeover Time (min)</td><td>{p_ch}</td><td>{i_ch}</td></tr>
            <tr><td>Dye Dispersion (L/kg)</td><td>{p_disp}</td><td>{i_disp}</td></tr>
            <tr><td>Waste Water/Changeover (L)</td><td>{p_w}</td><td>{i_w}</td></tr>
            <tr><td>Startup Waste (m)</td><td>{p_startup}</td><td>{i_startup}</td></tr>
            <tr><td>Energy (kWh/kg)</td><td>{p_en}</td><td>{i_en}</td></tr>
            <tr><td>B-Quality Fabric (%)</td><td>{p_bq}%</td><td>{i_bq}%</td></tr>
            <tr><td>Waste Fabric (%)</td><td>{p_wf}%</td><td>{i_wf}%</td></tr>
        </table>

        <div class="footer">
            Generated by Imogo Dye-max ROI Calculator
        </div>
    </body>
    </html>
    """
    return html_content

st.markdown("---")
st.download_button(
    label="📄 Download Full Report (HTML)",
    data=generate_html_report(),
    file_name=f"imogo_roi_report_{customer_name.replace(' ', '_') if customer_name else 'customer'}.html",
    mime="text/html"
)
