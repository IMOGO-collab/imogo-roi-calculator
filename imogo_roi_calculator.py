import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Imogo Dye-Max ROI Calculator", layout="wide", page_icon="🧪")
st.title("💰 Imogo Dye-Max vs Traditional Padder – ROI Calculator")
st.markdown("**Full chemistry (production + startup + changeover) in g/L**")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("💲 Your Exact Cost Prices")
    elec_price = st.number_input("Electricity (€/kWh)", value=0.10, step=0.01, format="%.3f")
    water_price = st.number_input("Water (€/L)", value=0.0005, step=0.0001, format="%.4f")
    dye_stuff_price = st.number_input("Dye stuff (€/kg)", value=5.0, step=0.5)
    chem_a_price = st.number_input("Chem A (€/kg)", value=2.0, step=0.1)
    chem_b_price = st.number_input("Chem B (€/kg)", value=3.0, step=0.1)
    chem_c_price = st.number_input("Chem C (€/kg)", value=5.0, step=0.1)
    waste_handling_price = st.number_input("Waste handling (€/L)", value=0.002, step=0.0001, format="%.4f")
    labor_price = st.number_input("Labor (€/man-hour)", value=2.0, step=0.5)
    co2_per_kwh = st.number_input("Natural gas CO₂ (kg/kWh)", value=0.202, step=0.001, format="%.3f")
    investment_cost = st.number_input("Imogo investment cost (€)", value=550_000, step=5_000)

    st.markdown("---")
    st.subheader("🧵 Fabric Waste Prices")
    price_a_fabric = st.number_input("Price A quality fabric (€/kg)", value=2.8, step=0.1)
    price_b_fabric = st.number_input("Price B quality fabric (€/kg)", value=1.8, step=0.1)
    price_waste_fabric = st.number_input("Waste fabric (€/kg)", value=0.8, step=0.1)

# ====================== SHARED PARAMETERS ======================
st.subheader("📦 Shared Parameters")
col_shared1, col_shared2 = st.columns(2)
with col_shared1:
    roll_size = st.number_input("Average roll size (kg)", value=500.0, step=1.0)
    rolls_per_shift = st.number_input("Rolls per shift", value=4.0, step=0.1)
    shifts_day = st.number_input("Shifts per day", value=3, step=1)
    days_year = st.number_input("Working days per year", value=330, step=1)

with col_shared2:
    changeovers_shift = st.number_input("Changeovers per shift", value=3, step=1)
    working_hours_per_shift = st.number_input("Working hours per shift (h)", value=8.0, step=0.5)
    fabric_width = st.number_input("Fabric width (m)", value=1.8, step=0.1)
    fabric_gsm = st.number_input("Fabric GSM (kg/m²)", value=0.18, step=0.01)

annual_changeovers = shifts_day * changeovers_shift * days_year
base_annual_kg = roll_size * rolls_per_shift * shifts_day * days_year
base_daily_kg = base_annual_kg / days_year if days_year > 0 else 0

# ====================== PRODUCTION SUMMARY ======================
effective_hours_p = working_hours_per_shift - (changeovers_shift * 30 / 60.0)
running_speed_kg_h_p = (roll_size * rolls_per_shift) / effective_hours_p if effective_hours_p > 0 else 0
running_speed_m_min_p = running_speed_kg_h_p / (60 * fabric_width * fabric_gsm) if fabric_width * fabric_gsm > 0 else 0

effective_hours_i = working_hours_per_shift - (changeovers_shift * 15 / 60.0)
running_speed_kg_h_i = (roll_size * rolls_per_shift) / effective_hours_i if effective_hours_i > 0 else 0
running_speed_m_min_i = running_speed_kg_h_i / (60 * fabric_width * fabric_gsm) if fabric_width * fabric_gsm > 0 else 0

st.subheader("📊 Production Volume Summary")
col_sum1, col_sum2 = st.columns(2)
with col_sum1:
    st.metric("**Traditional Padder**", f"{base_annual_kg:,.0f} kg/year")
    st.caption(f"**{base_daily_kg:,.0f} kg/day** | **{running_speed_m_min_p:,.1f} m/min**")
with col_sum2:
    time_saved_per_shift_h = changeovers_shift * (30 - 15) / 60.0
    extra_kg_per_day = time_saved_per_shift_h * running_speed_kg_h_i
    extra_kg_per_year = extra_kg_per_day * days_year
    st.metric("**Imogo Dye-Max**", f"{base_annual_kg:,.0f} kg/year", f"↑ {extra_kg_per_year:,.0f} kg/year extra")
    st.caption(f"**{base_daily_kg:,.0f} kg/day** | **{running_speed_m_min_i:,.1f} m/min**")

# ====================== MACHINE SPECIFIC ======================
col_p, col_i = st.columns(2)
with col_p:
    st.subheader("🟠 Traditional Padder")
    p_changeover_min = st.number_input("Changeover time (min)", value=30, step=1, key="p_ch")
    p_disp_l_per_kg = st.number_input("Dye dispersion (L/kg)", value=0.8, step=0.1, key="p_disp")
    p_dye_conc = st.number_input("Dye concentration (%) OWF", value=4.0, step=0.1, key="p_dye")
    p_chem_a_gl = st.number_input("Chem A (g/L)", value=3.0, step=1.0, key="p_a")
    p_chem_b_gl = st.number_input("Chem B (g/L)", value=2.0, step=1.0, key="p_b")
    p_chem_c_gl = st.number_input("Chem C (g/L)", value=1.5, step=1.0, key="p_c")
    p_waste_changeover = st.number_input("Waste water/changeover (L)", value=70, step=1, key="p_w")
    p_startup_waste_m = st.number_input("Startup waste fabric (m)", value=50.0, step=1.0, key="p_startup")
    p_energy_kwh_per_kg = st.number_input("Energy (kWh/kg)", value=0.05, step=0.001, format="%.4f", key="p_en")

with col_i:
    st.subheader("🔵 Imogo Dye-Max")
    i_changeover_min = st.number_input("Changeover time (min)", value=15, step=1, key="i_ch")
    i_disp_l_per_kg = st.number_input("Dye dispersion (L/kg)", value=0.8, step=0.1, key="i_disp")
    i_dye_conc = st.number_input("Dye concentration (%) OWF", value=4.0, step=0.1, key="i_dye")
    i_chem_a_gl = st.number_input("Chem A (g/L)", value=3.0, step=1.0, key="i_a")
    i_chem_b_gl = st.number_input("Chem B (g/L)", value=2.0, step=1.0, key="i_b")
    i_chem_c_gl = st.number_input("Chem C (g/L)", value=1.5, step=1.0, key="i_c")
    i_waste_changeover = st.number_input("Waste water/changeover (L)", value=15, step=1, key="i_w")
    i_startup_waste_m = st.number_input("Startup waste fabric (m)", value=7.0, step=1.0, key="i_startup")
    i_energy_kwh_per_kg = st.number_input("Energy (kWh/kg)", value=0.035, step=0.001, format="%.4f", key="i_en")

# ====================== CALCULATIONS ======================
p_disp_L = base_annual_kg * p_disp_l_per_kg
i_disp_L = base_annual_kg * i_disp_l_per_kg

# Dye calculations
p_dye_g_per_l = (p_dye_conc / 100 * 1000) / p_disp_l_per_kg if p_disp_l_per_kg > 0 else 0
i_dye_g_per_l = (i_dye_conc / 100 * 1000) / i_disp_l_per_kg if i_disp_l_per_kg > 0 else 0

p_dye_kg = base_annual_kg * (p_dye_conc / 100)
i_dye_kg = base_annual_kg * (i_dye_conc / 100)

p_startup_waste_kg = annual_changeovers * p_startup_waste_m * fabric_width * fabric_gsm
i_startup_waste_kg = annual_changeovers * i_startup_waste_m * fabric_width * fabric_gsm
p_startup_dye_kg = p_startup_waste_kg * (p_dye_conc / 100)
i_startup_dye_kg = i_startup_waste_kg * (i_dye_conc / 100)

p_waste_L = annual_changeovers * p_waste_changeover
i_waste_L = annual_changeovers * i_waste_changeover
p_changeover_dye_kg = p_waste_L * (p_dye_g_per_l / 1000)
i_changeover_dye_kg = i_waste_L * (i_dye_g_per_l / 1000)

total_dye_savings_kg = (p_dye_kg + p_startup_dye_kg + p_changeover_dye_kg) - \
                       (i_dye_kg + i_startup_dye_kg + i_changeover_dye_kg)

# Chemistry FULL (production + startup + changeover)
p_chem_a_kg = p_disp_L * (p_chem_a_gl / 1000)
p_chem_b_kg = p_disp_L * (p_chem_b_gl / 1000)
p_chem_c_kg = p_disp_L * (p_chem_c_gl / 1000)

i_chem_a_kg = i_disp_L * (i_chem_a_gl / 1000)
i_chem_b_kg = i_disp_L * (i_chem_b_gl / 1000)
i_chem_c_kg = i_disp_L * (i_chem_c_gl / 1000)

p_startup_chem_a_kg = p_startup_waste_kg * p_disp_l_per_kg * (p_chem_a_gl / 1000)
p_startup_chem_b_kg = p_startup_waste_kg * p_disp_l_per_kg * (p_chem_b_gl / 1000)
p_startup_chem_c_kg = p_startup_waste_kg * p_disp_l_per_kg * (p_chem_c_gl / 1000)

i_startup_chem_a_kg = i_startup_waste_kg * i_disp_l_per_kg * (i_chem_a_gl / 1000)
i_startup_chem_b_kg = i_startup_waste_kg * i_disp_l_per_kg * (i_chem_b_gl / 1000)
i_startup_chem_c_kg = i_startup_waste_kg * i_disp_l_per_kg * (i_chem_c_gl / 1000)

p_changeover_chem_a_kg = p_waste_L * (p_chem_a_gl / 1000)
p_changeover_chem_b_kg = p_waste_L * (p_chem_b_gl / 1000)
p_changeover_chem_c_kg = p_waste_L * (p_chem_c_gl / 1000)

i_changeover_chem_a_kg = i_waste_L * (i_chem_a_gl / 1000)
i_changeover_chem_b_kg = i_waste_L * (i_chem_b_gl / 1000)
i_changeover_chem_c_kg = i_waste_L * (i_chem_c_gl / 1000)

total_chem_a_savings = (p_chem_a_kg + p_startup_chem_a_kg + p_changeover_chem_a_kg) - (i_chem_a_kg + i_startup_chem_a_kg + i_changeover_chem_a_kg)
total_chem_b_savings = (p_chem_b_kg + p_startup_chem_b_kg + p_changeover_chem_b_kg) - (i_chem_b_kg + i_startup_chem_b_kg + i_changeover_chem_b_kg)
total_chem_c_savings = (p_chem_c_kg + p_startup_chem_c_kg + p_changeover_chem_c_kg) - (i_chem_c_kg + i_startup_chem_c_kg + i_changeover_chem_c_kg)

total_chem_savings_kg = total_chem_a_savings + total_chem_b_savings + total_chem_c_savings

# ====================== WATER SAVINGS (FULL) ======================
# Total water = production + startup + changeover
p_total_water = (base_annual_kg * p_disp_l_per_kg) + \
                (p_startup_waste_kg * p_disp_l_per_kg) + \
                p_waste_L

i_total_water = (base_annual_kg * i_disp_l_per_kg) + \
                (i_startup_waste_kg * i_disp_l_per_kg) + \
                i_waste_L

water_savings = (p_total_water - i_total_water) * water_price
water_savings_m3 = (p_total_water - i_total_water) / 1000

# ====================== ENERGY SAVINGS (inkl. startup fabric) ======================
p_total_energy_kwh = (base_annual_kg + p_startup_waste_kg) * p_energy_kwh_per_kg
i_total_energy_kwh = (base_annual_kg + i_startup_waste_kg) * i_energy_kwh_per_kg

energy_savings_kwh = p_total_energy_kwh - i_total_energy_kwh
energy_savings = energy_savings_kwh * elec_price

# Other savings
waste_savings = (p_waste_L - i_waste_L) * waste_handling_price
labor_savings = (annual_changeovers * p_changeover_min / 60 - annual_changeovers * i_changeover_min / 60) * labor_price

annual_savings = (total_dye_savings_kg * dye_stuff_price + 
                  total_chem_a_savings * chem_a_price +
                  total_chem_b_savings * chem_b_price +
                  total_chem_c_savings * chem_c_price +
                  water_savings + energy_savings + waste_savings + labor_savings)

payback_months = (investment_cost / annual_savings * 12) if annual_savings > 0 else 0

# ====================== SAVINGS OVERVIEW ======================
st.subheader("📈 Savings Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual € Savings", f"€{annual_savings:,.0f}")
c2.metric("Payback Period", f"{payback_months:.1f} months")
c3.metric("Dye Stuff Savings", f"{total_dye_savings_kg:,.0f} kg/year")
c4.metric("Chemistry Savings", f"{total_chem_savings_kg:,.0f} kg/year")

# ====================== ENVIRONMENTAL SAVINGS ======================
st.subheader("🌍 Environmental Savings")
e1, e2, e3, empty = st.columns([1.2, 1.2, 1.2, 1.2])

e1.metric("**Water Savings**", f"{water_savings_m3:,.0f} m³/year")
e2.metric("**CO₂ Savings**", f"{(energy_savings_kwh * co2_per_kwh / 1000):,.1f} tonnes/year")
e3.metric("**Energy Savings**", f"{energy_savings_kwh:,.0f} kWh/year")

# ====================== BREAKDOWN ======================
st.subheader("💰 Monetary Savings Breakdown (€/year)")
breakdown = pd.DataFrame({
    "Category": ["Dye Stuff", "Chem A", "Chem B", "Chem C", "Process Water", "Waste Handling", "Energy", "Labor"],
    "Savings (€/year)": [
        total_dye_savings_kg * dye_stuff_price,
        total_chem_a_savings * chem_a_price,
        total_chem_b_savings * chem_b_price,
        total_chem_c_savings * chem_c_price,
        water_savings,
        waste_savings,
        energy_savings,
        labor_savings
    ]
})
st.dataframe(breakdown.style.format("€{:,.0f}", subset=["Savings (€/year)"]), use_container_width=True, hide_index=True)

# ====================== GRAPHS ======================
st.markdown("### 📊 Savings Breakdown")
fig_savings = go.Figure(go.Bar(
    x=breakdown["Savings (€/year)"],
    y=breakdown["Category"],
    orientation='h',
    marker_color=['#FF9800', '#FF5722', '#00B0FF', '#9C27B0', '#00C853', '#1E88E5', '#FF5252', '#1E88E5']
))
fig_savings.update_layout(height=400, xaxis_title="€ Savings per year", title="Årliga besparingar per kategori")
st.plotly_chart(fig_savings, use_container_width=True)

st.markdown("### 📈 Kostnadsjämförelse Padder vs Imogo")
cost_fig = go.Figure()
cost_fig.add_trace(go.Bar(
    name="Traditional Padder",
    x=["Dye", "Chemistry", "Water", "Waste", "Energy", "Labor"],
    y=[p_dye_kg*dye_stuff_price, 
       (p_chem_a_kg + p_chem_b_kg + p_chem_c_kg) * ((chem_a_price+chem_b_price+chem_c_price)/3),
       p_total_water * water_price,
       p_waste_L * waste_handling_price,
       p_total_energy_kwh * elec_price,
       (annual_changeovers * p_changeover_min / 60) * labor_price],
    marker_color="#FF5252"
))
cost_fig.add_trace(go.Bar(
    name="Imogo Dye-Max",
    x=["Dye", "Chemistry", "Water", "Waste", "Energy", "Labor"],
    y=[i_dye_kg*dye_stuff_price, 
       (i_chem_a_kg + i_chem_b_kg + i_chem_c_kg) * ((chem_a_price+chem_b_price+chem_c_price)/3),
       i_total_water * water_price,
       i_waste_L * waste_handling_price,
       i_total_energy_kwh * elec_price,
       (annual_changeovers * i_changeover_min / 60) * labor_price],
    marker_color="#1E88E5"
))
cost_fig.update_layout(barmode='group', height=420, title="Årliga kostnader per kategori")
st.plotly_chart(cost_fig, use_container_width=True)

# ====================== PDF REPORT EXPORT ======================
st.markdown("---")
st.subheader("📄 Export Full Report")

html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Imogo Dye-Max ROI Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ text-align: center; color: #1E88E5; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background: #1E88E5; color: white; }}
    </style>
</head>
<body>
    <h1>Imogo Dye-Max ROI Report</h1>
    <p style="text-align:center;"><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    
    <div class="metric">
        <h2>Key Results</h2>
        <p><strong>Annual Savings:</strong> €{annual_savings:,.0f}</p>
        <p><strong>Payback Time:</strong> {payback_months:.1f} months</p>
    </div>

    <h2>Physical Savings</h2>
    <p>Dye Stuff: <strong>{total_dye_savings_kg:,.0f} kg/year</strong></p>
    <p>Chemistry: <strong>{total_chem_savings_kg:,.0f} kg/year</strong></p>
    <p>Water: <strong>{water_savings_m3:,.0f} m³/year</strong></p>
    <p>Energy: <strong>{energy_savings_kwh:,.0f} kWh/year</strong></p>
    <p>CO₂: <strong>{(energy_savings_kwh * co2_per_kwh / 1000):,.1f} tonnes/year</strong></p>

    <h2>Monetary Savings Breakdown</h2>
    {breakdown.to_html(index=False, classes='table', 
                       formatters={
                           "Savings (€/year)": lambda x: f"€{x:,.0f}"
                       })}
    
    <p style="text-align:center; margin-top:50px; color:#666;">
        Imogo Dye-Max ROI Calculator • Confidential
    </p>
</body>
</html>
"""

if st.download_button(
    label="📥 Download Professional Report as HTML (Print → Save as PDF)",
    data=html_report,
    file_name="Imogo_Dye-Max_ROI_Report.html",
    mime="text/html"
):
    st.success("✅ Report downloaded! Open → Ctrl+P → Save as PDF")
