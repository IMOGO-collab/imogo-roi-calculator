import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ====================== LÖSENORDSSKYDD ======================
def check_password():
    """Returns True if the user has entered the correct password."""
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
    st.session_state.ui_elec = 0.10
    st.session_state.ui_water = 0.0001
    st.session_state.ui_dye = 5.0
    st.session_state.ui_chem_a = 2.0
    st.session_state.ui_chem_b = 3.0
    st.session_state.ui_chem_c = 5.0
    st.session_state.ui_waste = 0.002
    st.session_state.ui_labor = 2.0
    st.session_state.ui_inv = 550000.0
    st.session_state.ui_price_a = 2.8
    st.session_state.ui_price_b = 1.8
    st.session_state.ui_price_waste = 0.8

# ====================== SIDEBAR ======================
with st.sidebar:
    customer_name = st.text_input("Customer name", value="", key="customer_name_input")
    curr = st.text_input("Currency (i.e. EUR, SEK, USD)", value="EUR", key="curr_input").strip().upper()
    current_rate = st.session_state.get("conv_key", 1.00)
    conv = st.number_input(f"Exchange rate (1 EUR = {current_rate:.2f} {curr})", value=1.00, step=0.10, format="%.2f", key="conv_key")
    
    # Automatisk omräkning av kostnader i session_state om växelkursen ändras
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
    st.number_input(f"Chem A ({curr}/kg)", key="ui_chem_a")
    st.number_input(f"Chem B ({curr}/kg)", key="ui_chem_b")
    st.number_input(f"Chem C ({curr}/kg)", key="ui_chem_c")
    st.number_input(f"Waste handling ({curr}/L)", key="ui_waste", format="%.4f")
    st.number_input(f"Labor ({curr}/man-hour)", key="ui_labor")
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
    working_hours = st.number_input("Working hours per shift (h)", value=8.0, step=0.5, key="working_hours")
    prod_speed = st.number_input("Production speed (m/min)", value=20.0, step=0.1, key="prod_speed")

with col_s2:
    rolls_shift = st.number_input("Rolls per shift", value=4.0, step=0.1, key="rolls_shift")
    shifts_day = st.number_input("Shifts per day", value=3, step=1, key="shifts_day")
    days_year = st.number_input("Working days per year", value=300, step=1, key="days_year")
    changeovers = st.number_input("Changeovers per shift", value=3, step=1, key="changeovers")

# --- Rullberäkning ---
est_changeover_time = 20 
eff_hours = working_hours - (changeovers * est_changeover_time / 60.0)

meters_per_roll = (prod_speed * 60 * eff_hours) / rolls_shift if rolls_shift > 0 else 0
weight_per_roll = meters_per_roll * fabric_width * fabric_gsm

st.markdown(f"""
<div style="background-color: #e8f4fd; padding: 10px; border-radius: 10px; font-size: 1.1em; color: #1e3a8a;">
    <strong>Fabric length per roll:</strong> {meters_per_roll:,.0f} m 
    <span style="margin: 0 15px; color: #6b7280;">|</span> 
    <strong>Fabric weight per roll:</strong> {weight_per_roll:,.1f} kg
</div>
""", unsafe_allow_html=True)

prod_summary_placeholder = st.container()

# ====================== MACHINE SPECIFIC ======================
col_p, col_i = st.columns(2)
with col_p:
    st.subheader("🟠 Traditional Padder")
    p_ch = st.number_input("Changeover time (min)", value=30, key="p_ch")
    p_disp = st.number_input("Dye dispersion (L/kg)", value=0.8, key="p_disp")
    p_dye = st.number_input("Dye conc (%)", value=4.0, key="p_dye")
    p_conc_g_l = (p_dye * 10) / p_disp if p_disp > 0 else 0
    st.info(f"Concentration: {p_conc_g_l:.1f} g/L")
    p_a = st.number_input("Chem A (g/L)", value=3.0, key="p_a")
    p_b = st.number_input("Chem B (g/L)", value=2.0, key="p_b")
    p_c = st.number_input("Chem C (g/L)", value=1.5, key="p_c")
    p_w = st.number_input("Waste water/changeover (L)", value=70, key="p_w")
    p_startup = st.number_input("Startup waste (m)", value=50.0, key="p_startup")
    p_en = st.number_input("Energy (kWh/kg)", value=0.05, format="%.4f", key="p_en")
    p_bq = st.number_input("B-quality fabric (%)", value=4.0, key="p_bq")
    p_wf = st.number_input("Waste fabric (%)", value=1.0, key="p_wf")
with col_i:
    st.subheader("🔵 Imogo Dye-max")
    i_ch = st.number_input("Changeover time (min)", value=20, key="i_ch")
    i_disp = st.number_input("Dye dispersion (L/kg)", value=0.8, key="i_disp")
    i_dye = st.number_input("Dye conc (%)", value=4.0, key="i_dye")
    i_conc_g_l = (i_dye * 10) / i_disp if i_disp > 0 else 0
    st.info(f"Concentration: {i_conc_g_l:.1f} g/L")
    i_a = st.number_input("Chem A (g/L)", value=3.0, key="i_a")
    i_b = st.number_input("Chem B (g/L)", value=2.0, key="i_b")
    i_c = st.number_input("Chem C (g/L)", value=1.5, key="i_c")
    i_w = st.number_input("Waste water/changeover (L)", value=15, key="i_w")
    i_startup = st.number_input("Startup waste (m)", value=7.0, key="i_startup")
    i_en = st.number_input("Energy (kWh/kg)", value=0.035, format="%.4f", key="i_en")
    i_bq = st.number_input("B-quality fabric (%)", value=3.0, key="i_bq")
    i_wf = st.number_input("Waste fabric (%)", value=0.5, key="i_wf")

# ====================== BERÄKNINGAR ======================
effective_hours_p = working_hours - (changeovers * p_ch / 60.0)
p_daily_kg = prod_speed * 60 * effective_hours_p * shifts_day * fabric_width * fabric_gsm
base_annual_kg = p_daily_kg * days_year

effective_hours_i = working_hours - (changeovers * i_ch / 60.0)
i_daily_kg = prod_speed * 60 * effective_hours_i * shifts_day * fabric_width * fabric_gsm
i_annual_kg_potential = i_daily_kg * days_year

extra_annual_kg = i_annual_kg_potential - base_annual_kg
annual_changeovers = shifts_day * changeovers * days_year

with prod_summary_placeholder:
    st.markdown("---")
    st.subheader("📊 Production Volume Summary")
    col_sum1, col_sum2 = st.columns(2)

    with col_sum1:
        st.metric("**Traditional Padder**", f"{format_num(base_annual_kg)} kg/year")
        st.caption(f"**{format_num(p_daily_kg)} kg/day** | **{prod_speed:.1f} m/min**")

    with col_sum2:
        st.metric(
            "**Imogo Dye-Max**", 
            f"{format_num(base_annual_kg)} kg/year", 
            delta=f"↑ {format_num(extra_annual_kg)} kg/year extra"
        )
        st.caption(f"**{format_num(i_daily_kg)} kg/day** | **{prod_speed:.1f} m/min**")
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
energy_savings_kwh = p_total_energy - i_total_energy
co2_savings_tonnes = energy_savings_kwh * 0.202 / 1000

p_total = (p_dye_kg + p_startup_dye_kg + p_changeover_dye_kg) * dye_stuff_price + \
          (p_chem_a_kg * chem_a_price) + (p_chem_b_kg * chem_b_price) + (p_chem_c_kg * chem_c_price) + \
          (p_total_water * water_price) + (p_total_energy * elec_price) + \
          (p_waste_L * waste_handling_price) + p_labor_cost + \
          (p_b_quality_kg * price_b_fabric) + (p_waste_fabric_kg * price_waste_fabric)

i_total = (i_dye_kg + i_startup_dye_kg + i_changeover_dye_kg) * dye_stuff_price + \
          (i_chem_a_kg * chem_a_price) + (i_chem_b_kg * chem_b_price) + (i_chem_c_kg * chem_c_price) + \
          (i_total_water * water_price) + (i_total_energy * elec_price) + \
          (i_waste_L * waste_handling_price) + i_labor_cost + \
          (i_b_quality_kg * price_b_fabric) + (i_waste_fabric_kg * price_waste_fabric)

p_roll_weight_wet = weight_per_roll * (1 + p_disp)
i_roll_weight_wet = weight_per_roll * (1 + i_disp)

if p_roll_weight_wet > 1500 or i_roll_weight_wet > 1500:
    bg_color = "#f8d7da"
    text_color = "#721c24"
else:
    bg_color = "#e6f4ea"
    text_color = "#137333"

st.markdown(f"""
<div style="background-color: {bg_color}; color: {text_color}; padding: 15px; border-radius: 8px; font-size: 1.1em; margin-bottom: 20px;">
    <strong>Roll wet weight total:</strong> {i_roll_weight_wet:.1f} kg
</div>
""", unsafe_allow_html=True)

# ====================== VISNING & UI ======================
st.subheader("📈 Savings Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual Savings", f"{curr} {format_num(annual_savings)}")
c2.metric("Payback Period", f"{format_num(payback_months)} months")
c3.metric("Dye Stuff Savings", f"{format_num(total_dye_savings_kg)} kg/year")
c4.metric("Chemistry Savings", f"{format_num(total_chem_savings_kg)} kg/year")

st.markdown("### 🌍 Environmental Savings")
c_env1, c_env2, c_env3 = st.columns(3)
c_env1.metric("Water Savings", f"{format_num(water_savings_m3)} m³/year")
c_env2.metric("CO₂ Savings", f"{co2_savings_tonnes:.1f} tonnes/year")
c_env3.metric("Energy Savings", f"{format_num(energy_savings_kwh)} kWh/year")

st.subheader("💰 Monetary Savings Breakdown")
breakdown_df = pd.DataFrame({
    "Category": ["Dye Stuff", "Chem A", "Chem B", "Chem C", "Process Water", "Waste Handling", "Energy", "Labor", "B-Quality", "Waste Fabric"],
    "Savings": [total_dye_savings, total_chem_a_savings_kg * chem_a_price, total_chem_b_savings_kg * chem_b_price, total_chem_c_savings_kg * chem_c_price, water_savings, waste_savings, energy_savings, labor_savings, b_quality_savings, waste_fabric_savings]
})
st.dataframe(breakdown_df.style.format({"Savings": lambda x: f"{curr} {format_num(x)}"}), use_container_width=True, hide_index=True)

st.markdown("### 💰 Total Cost per kg Fabric")
col_cost1, col_cost2 = st.columns(2)
cost_per_kg_p = (p_total / base_annual_kg) if base_annual_kg > 0 else 0
cost_per_kg_i = (i_total / base_annual_kg) if base_annual_kg > 0 else 0
diff = cost_per_kg_p - cost_per_kg_i
pct = (diff / cost_per_kg_p * 100) if cost_per_kg_p > 0 else 0
col_cost1.metric("Traditional Exhaust", f"{curr} {cost_per_kg_p:.2f} / kg")
col_cost2.metric("Imogo Dye-Max", f"{curr} {cost_per_kg_i:.2f} / kg", f" ↓ {curr} {diff:.2f} / kg ({pct:.1f}%)")

# ====================== VISUAL SAVINGS OVERVIEW ======================
st.markdown("---")
st.markdown("### 📊 Visual Savings Overview")

fig_savings = go.Figure(go.Bar(
    x=breakdown_df["Savings"], 
    y=breakdown_df["Category"], 
    orientation='h', 
    marker_color='#00B0FF'
))
fig_savings.update_layout(
    title=f"Yearly savings per category ({curr}/year)",
    xaxis_title=f"{curr} Savings",
    yaxis=dict(autorange="reversed"),
    height=400
)
st.plotly_chart(fig_savings, use_container_width=True)

fig_cost = go.Figure()
fig_cost.add_trace(go.Bar(
    x=["Traditional Padder", "Imogo Dye-max"],
    y=[cost_per_kg_p, cost_per_kg_i],
    marker_color=['#FF4B4B', '#00CC96']
))
fig_cost.update_layout(
    title=f"Total Cost per kg Fabric ({curr})",
    yaxis_title=f"{curr} / kg",
    height=400
)
st.plotly_chart(fig_cost, use_container_width=True)
clean_customer_name = customer_name.strip() if customer_name else ""
customer_paragraph = f"<p style='text-align:center; font-size:1.2em; color:#1e3a8a; margin-top:-10px;'><strong>Prepared for:</strong> {clean_customer_name}</p>" if clean_customer_name else ""

# ====================== HTML PDF-EXPORT ======================
st.markdown("---")
st.subheader("📄 Generate Report")

current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

table_html = ""
for index, row in breakdown_df.iterrows():
    table_html += f"<tr><td>{row['Category']}</td><td>{curr} {format_num(row['Savings'])}</td></tr>"

clean_customer_name = customer_name.strip() if customer_name else "Imogo"

html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
    h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
    h2 {{ color: #0f172a; margin-top: 25px; border-bottom: 1px solid #cbd5e1; padding-bottom: 5px; }}
    .metric {{ background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-bottom: 15px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; font-size: 0.9em; }}
    th {{ background-color: #f8fafc; color: #1e293b; }}
    .section-header {{ background-color: #e2e8f0; font-weight: bold; text-align: center; font-size: 0.95em; }}
</style>
</head>
<body>
    <h1>Imogo Dye-max ROI & Environmental Report</h1>
    {customer_paragraph}
    <p style="text-align:center; color:#64748b;"><strong>Generated:</strong> {current_time}</p>
           
    <div class="metric">
        <h2>Key Results</h2>
        <p style="font-size:1.5em;"><strong>Annual Savings: {curr} {format_num(annual_savings)}</strong></p>
        <p><strong>Payback Period: {format_num(payback_months)} months</strong></p>
        <p><strong>Investment Cost: {curr} {format_num(investment_cost)}</strong></p>
    </div>

    <h2>Production Summary</h2>
    <p><strong>Traditional Padder:</strong> {format_num(base_annual_kg)} kg/year</p>
    <p><strong>Imogo Dye-max:</strong> {format_num(base_annual_kg)} kg/year</p>

    <h2>Physical Savings</h2>
    <p>Dye Stuff: <strong>{format_num(total_dye_savings_kg)} kg/year</strong></p>
    <p>Chemistry: <strong>{format_num(total_chem_savings_kg)} kg/year</strong></p>
    <p>Water: <strong>{format_num(water_savings_m3)} m³/year</strong></p>
    <p>Energy: <strong>{format_num(energy_savings_kwh)} kWh/year</strong></p>
    <p>CO₂: <strong>{co2_savings_tonnes:.1f} tonnes/year</strong></p>

    <h2>Monetary Savings Breakdown</h2>
    <table border="1" class="dataframe table">
      <thead>
        <tr style="text-align: right;">
          <th>Category</th>
          <th>Savings ({curr}/year)</th>
        </tr>
      </thead>
      <tbody>
        {table_html}
      </tbody>
    </table>
    
    <h2>Process & Recipe Comparison</h2>
    <table>
        <tr>
            <th style="width: 34%;">Parameter</th>
            <th style="width: 33%;">Traditional Padder</th>
            <th style="width: 33%;">Imogo Dye-Max</th>
        </tr>
        <tr><td colspan="3" class="section-header">Machine & Process Parameters</td></tr>
        <tr><td>Working hours / shift</td><td>{working_hours} h</td><td>{working_hours} h</td></tr>
        <tr><td>Production speed</td><td>{prod_speed} m/min</td><td>{prod_speed} m/min</td></tr>
        <tr><td>Changeover Time</td><td>{p_ch} min</td><td>{i_ch} min</td></tr>
        <tr><td>Dye dispersion</td><td>{p_disp} L/kg</td><td>{i_disp} L/kg</td></tr>
        <tr><td>Waste water / changeover</td><td>{p_w} L</td><td>{i_w} L</td></tr>
        <tr><td>Startup waste</td><td>{p_startup} m</td><td>{i_startup} m</td></tr>
        
        <tr><td colspan="3" class="section-header">Chemistry Recipe</td></tr>
        <tr><td>Dye concentration</td><td>{p_dye}%</td><td>{i_dye}%</td></tr>
        <tr><td>Chem A</td><td>{p_a} g/L</td><td>{i_a} g/L</td></tr>
        <tr><td>Chem B</td><td>{p_b} g/L</td><td>{i_b} g/L</td></tr>
        <tr><td>Chem C</td><td>{p_c} g/L</td><td>{i_c} g/L</td></tr>
        <tr><td>B-quality fabric</td><td>{p_bq}%</td><td>{i_bq}%</td></tr>
        <tr><td>Waste fabric</td><td>{p_wf}%</td><td>{i_wf}%</td></tr>
    </table>

    <h2>General Parameters & Unit Costs</h2>
    <table>
        <tr>
            <th style="width: 50%;">Parameter</th>
            <th style="width: 50%;">Value</th>
        </tr>
        <tr><td colspan="2" class="section-header">General Production</td></tr>
        <tr><td>Working days / year</td><td>{days_year} days</td></tr>
        <tr><td>Shifts per day</td><td>{shifts_day}</td></tr>
        <tr><td>Rolls per shift</td><td>{rolls_shift}</td></tr>
        <tr><td>Fabric width & GSM</td><td>{fabric_width} m / {fabric_gsm} kg/m²</td></tr>
        
        <tr><td colspan="2" class="section-header">Costs & Unit Rates</td></tr>
        <tr><td>Electricity Price</td><td>{elec_price:.3f} {curr}/kWh</td></tr>
        <tr><td>Water Price</td><td>{water_price:.5f} {curr}/L</td></tr>
        <tr><td>Dye Stuff Price</td><td>{dye_stuff_price:.2f} {curr}/kg</td></tr>
        <tr><td>Chem A Price</td><td>{chem_a_price:.2f} {curr}/kg</td></tr>
        <tr><td>Chem B Price</td><td>{chem_b_price:.2f} {curr}/kg</td></tr>
        <tr><td>Chem C Price</td><td>{chem_c_price:.2f} {curr}/kg</td></tr>
        <tr><td>Waste Handling Price</td><td>{waste_handling_price:.4f} {curr}/L</td></tr>
        <tr><td>Labor Price</td><td>{labor_price:.2f} {curr}/man-hour</td></tr>
        <tr><td>Investment Cost</td><td>{curr} {format_num(investment_cost)}</td></tr>
        <tr><td>Price A-quality fabric</td><td>{price_a_fabric:.2f} {curr}/kg</td></tr>
        <tr><td>Price B-quality fabric</td><td>{price_b_fabric:.2f} {curr}/kg</td></tr>
        <tr><td>Price Waste fabric</td><td>{price_waste_fabric:.2f} {curr}/kg</td></tr>
        <tr><td>CO₂ Factor</td><td>0.202 kg/kWh</td></tr>
    </table>

    <p style="margin-top: 30px; font-size: 0.9em; color: #64748b; text-align: center;">
        This report was automatically generated by the Imogo ROI Calculator.
    </p>
</body>
</html>
"""

if st.download_button(
    label="📥 Download Report as HTML (Print → Save as PDF)",
    data=html_report,
    file_name="Imogo_Dye-max_ROI_Report.html",
    mime="text/html"
):
    st.success("✅ Report downloaded! Open the file → Ctrl+P → Save as PDF")
