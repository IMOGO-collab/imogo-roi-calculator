import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Imogo Dye-Max ROI Calculator", layout="wide", page_icon="🧪")
st.title("💰 Imogo Dye-Max vs Traditional Padder – ROI Calculator")
st.markdown("**All savings now include Production + Waste + Startup + Fabric waste**")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("💲 Your Exact Cost Prices")
    elec_price = st.number_input("Electricity (€/kWh)", value=0.10, step=0.01, format="%.3f")
    water_price = st.number_input("Water (€/L)", value=0.0005, step=0.0001, format="%.4f")
    dye_stuff_price = st.number_input("Dye stuff (€/kg)", value=6.0, step=0.5)
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
    roll_size = st.number_input("Average roll size (kg)", value=225.0, step=1.0)
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

# ====================== CALCULATED RUNNING SPEED ======================
effective_hours_p = working_hours_per_shift - (changeovers_shift * 30 / 60.0)
running_speed_kg_h_p = (roll_size * rolls_per_shift) / effective_hours_p if effective_hours_p > 0 else 0
running_speed_m_min_p = running_speed_kg_h_p / (60 * fabric_width * fabric_gsm) if fabric_width * fabric_gsm > 0 else 0

effective_hours_i = working_hours_per_shift - (changeovers_shift * 15 / 60.0)
running_speed_kg_h_i = (roll_size * rolls_per_shift) / effective_hours_i if effective_hours_i > 0 else 0
running_speed_m_min_i = running_speed_kg_h_i / (60 * fabric_width * fabric_gsm) if fabric_width * fabric_gsm > 0 else 0

# ====================== PRODUCTION SUMMARY ======================
st.subheader("📊 Production Volume Summary")
col_sum1, col_sum2 = st.columns(2)

with col_sum1:
    st.metric("**Traditional Padder**", f"{base_annual_kg:,.0f} kg/year")
    st.caption(f"**{base_daily_kg:,.0f} kg/day**   |   **{running_speed_m_min_p:,.1f} m/min**")

with col_sum2:
    time_saved_per_shift_h = changeovers_shift * (30 - 15) / 60.0
    extra_kg_per_day = time_saved_per_shift_h * running_speed_kg_h_i
    extra_kg_per_year = extra_kg_per_day * days_year
    st.metric("**Imogo Dye-Max**", f"{base_annual_kg:,.0f} kg/year", f"↑ {extra_kg_per_year:,.0f} kg/year extra")
    st.caption(f"**{base_daily_kg:,.0f} kg/day**   |   **{running_speed_m_min_i:,.1f} m/min**")

# ====================== DIFFERING INPUTS ======================
col_p, col_i = st.columns(2)
with col_p:
    st.subheader("🟠 Traditional Padder")
    p_changeover_min = st.number_input("Changeover time (min)", value=30, step=1, key="p_ch")
    p_disp_l_per_kg = st.number_input("Dye dispersion (L/kg)", value=1.0, step=0.1, key="p_disp")
    p_dye_conc = st.number_input("Dye concentration (%)", value=2.0, step=0.1, key="p_dye")
    p_chem_a_pct = st.number_input("Chem A (%) in solution", value=3.0, step=0.1, key="p_a")
    p_chem_b_pct = st.number_input("Chem B (%) in solution", value=3.0, step=0.1, key="p_b")
    p_chem_c_pct = st.number_input("Chem C (%) in solution", value=3.0, step=0.1, key="p_c")
    p_waste_changeover = st.number_input("Waste water/changeover (L)", value=70, step=1, key="p_w")
    p_b_quality_pct = st.number_input("B-quality fabric waste (%)", value=4.0, step=0.1, key="p_bq")
    p_waste_fabric_pct = st.number_input("Waste fabric (%)", value=2.0, step=0.1, key="p_wf")
    p_startup_waste_m = st.number_input("Startup waste fabric (m/changeover)", value=50.0, step=1.0, key="p_startup")
    p_energy_kwh_per_kg = st.number_input("Energy (kWh/kg fabric)", value=0.04, step=0.001, format="%.4f", key="p_en")

with col_i:
    st.subheader("🔵 Imogo Dye-Max")
    i_changeover_min = st.number_input("Changeover time (min)", value=15, step=1, key="i_ch")
    i_disp_l_per_kg = st.number_input("Dye dispersion (L/kg)", value=1.0, step=0.1, key="i_disp")
    i_dye_conc = st.number_input("Dye concentration (%)", value=2.0, step=0.1, key="i_dye")
    i_chem_a_pct = st.number_input("Chem A (%) in solution", value=3.0, step=0.1, key="i_a")
    i_chem_b_pct = st.number_input("Chem B (%) in solution", value=3.0, step=0.1, key="i_b")
    i_chem_c_pct = st.number_input("Chem C (%) in solution", value=3.0, step=0.1, key="i_c")
    i_waste_changeover = st.number_input("Waste water/changeover (L)", value=15, step=1, key="i_w")
    i_b_quality_pct = st.number_input("B-quality fabric waste (%)", value=4.0, step=0.1, key="i_bq")
    i_waste_fabric_pct = st.number_input("Waste fabric (%)", value=2.0, step=0.1, key="i_wf")
    i_startup_waste_m = st.number_input("Startup waste fabric (m/changeover)", value=5.0, step=1.0, key="i_startup")
    i_energy_kwh_per_kg = st.number_input("Energy (kWh/kg fabric)", value=0.025, step=0.001, format="%.4f", key="i_en")

# ====================== CALCULATIONS ======================
p_disp_L = base_annual_kg * p_disp_l_per_kg
i_disp_L = base_annual_kg * i_disp_l_per_kg

p_dye_kg = p_disp_L * (p_dye_conc / 100)
i_dye_kg = i_disp_L * (i_dye_conc / 100)

p_chem_kg = p_disp_L * ((p_chem_a_pct + p_chem_b_pct + p_chem_c_pct) / 100)
i_chem_kg = i_disp_L * ((i_chem_a_pct + i_chem_b_pct + i_chem_c_pct) / 100)

p_waste_L = annual_changeovers * p_waste_changeover
i_waste_L = annual_changeovers * i_waste_changeover

p_startup_waste_kg = annual_changeovers * p_startup_waste_m * fabric_width * fabric_gsm
i_startup_waste_kg = annual_changeovers * i_startup_waste_m * fabric_width * fabric_gsm

p_startup_disp_L = p_startup_waste_kg * p_disp_l_per_kg
i_startup_disp_L = i_startup_waste_kg * i_disp_l_per_kg

p_startup_dye_kg = p_startup_disp_L * (p_dye_conc / 100)
i_startup_dye_kg = i_startup_disp_L * (i_dye_conc / 100)

p_startup_chem_kg = p_startup_disp_L * ((p_chem_a_pct + p_chem_b_pct + p_chem_c_pct) / 100)
i_startup_chem_kg = i_startup_disp_L * ((i_chem_a_pct + i_chem_b_pct + i_chem_c_pct) / 100)

p_changeover_dye_kg = p_waste_L * (p_dye_conc / 100)
i_changeover_dye_kg = i_waste_L * (i_dye_conc / 100)

p_changeover_chem_kg = p_waste_L * ((p_chem_a_pct + p_chem_b_pct + p_chem_c_pct) / 100)
i_changeover_chem_kg = i_waste_L * ((i_chem_a_pct + i_chem_b_pct + i_chem_c_pct) / 100)

p_b_quality_kg = base_annual_kg * (p_b_quality_pct / 100)
i_b_quality_kg = base_annual_kg * (i_b_quality_pct / 100)
p_waste_fabric_kg = base_annual_kg * (p_waste_fabric_pct / 100)
i_waste_fabric_kg = base_annual_kg * (i_waste_fabric_pct / 100)

avg_chem_price = (chem_a_price + chem_b_price + chem_c_price) / 3

# ====================== FULL SAVINGS ======================
total_dye_savings_kg = (p_dye_kg + p_startup_dye_kg + p_changeover_dye_kg - i_dye_kg - i_startup_dye_kg - i_changeover_dye_kg)
total_chem_savings_kg = (p_chem_kg + p_startup_chem_kg + p_changeover_chem_kg - i_chem_kg - i_startup_chem_kg - i_changeover_chem_kg)

dye_savings_eur = total_dye_savings_kg * dye_stuff_price
chem_savings_eur = total_chem_savings_kg * avg_chem_price
fabric_b_savings = (p_b_quality_kg - i_b_quality_kg) * (price_a_fabric - price_b_fabric)
fabric_waste_savings = (p_waste_fabric_kg - i_waste_fabric_kg) * price_waste_fabric
water_savings = (p_disp_L + p_startup_disp_L - i_disp_L - i_startup_disp_L) * water_price
waste_handling_savings = (p_waste_L + p_startup_disp_L - i_waste_L - i_startup_disp_L) * waste_handling_price
energy_savings = (base_annual_kg * p_energy_kwh_per_kg + p_startup_waste_kg * p_energy_kwh_per_kg - base_annual_kg * i_energy_kwh_per_kg - i_startup_waste_kg * i_energy_kwh_per_kg) * elec_price
labor_savings = (annual_changeovers * p_changeover_min / 60 - annual_changeovers * i_changeover_min / 60) * labor_price

annual_savings = dye_savings_eur + chem_savings_eur + fabric_b_savings + fabric_waste_savings + water_savings + waste_handling_savings + energy_savings + labor_savings

payback_months = (investment_cost / annual_savings * 12) if annual_savings > 0 else 0

# ====================== DASHBOARD ======================
st.markdown("---")
st.header("📊 Savings Overview")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Annual € Savings", f"€{annual_savings:,.0f}")
m2.metric("Payback Period", f"{payback_months:.1f} months")
m3.metric("Dye Stuff Savings", f"{total_dye_savings_kg:,.0f} kg/year")
m4.metric("Chemistry Savings", f"{total_chem_savings_kg:,.0f} kg/year")

st.markdown("### 🌍 Environmental Savings")
e1, e2, e3, e4 = st.columns(4)
e1.metric("**Water Savings**", f"{(p_disp_L + p_startup_disp_L + p_waste_L - i_disp_L - i_startup_disp_L - i_waste_L)/1000:,.0f} m³/year")
e2.metric("CO₂ Savings", f"{(energy_savings / elec_price * co2_per_kwh / 1000):,.1f} tonnes/year")
e3.metric("Energy Savings", f"{energy_savings:,.0f} kWh/year")

st.markdown("### 💵 Monetary Savings Breakdown (€/year)")
monetary_df = pd.DataFrame({
    "Category": ["Dye stuff - Full", "Chemistry - Full", "B-quality Fabric", "Waste Fabric", "Process Water", "Waste Handling", "Energy", "Man hours"],
    "Savings (€/year)": [dye_savings_eur, chem_savings_eur, fabric_b_savings, fabric_waste_savings, water_savings, waste_handling_savings, energy_savings, labor_savings]
})
st.dataframe(monetary_df.style.format("€{:,.0f}", subset=["Savings (€/year)"]), use_container_width=True, hide_index=True)

# ====================== COSTS (for charts) ======================
p_energy_cost = (base_annual_kg * p_energy_kwh_per_kg + p_startup_waste_kg * p_energy_kwh_per_kg) * elec_price
i_energy_cost = (base_annual_kg * i_energy_kwh_per_kg + i_startup_waste_kg * i_energy_kwh_per_kg) * elec_price

p_water_cost = (p_disp_L + p_startup_disp_L) * water_price
i_water_cost = (i_disp_L + i_startup_disp_L) * water_price

p_dye_cost = (p_dye_kg + p_startup_dye_kg) * dye_stuff_price
i_dye_cost = (i_dye_kg + i_startup_dye_kg) * dye_stuff_price

p_chem_cost = (p_chem_kg + p_startup_chem_kg + p_changeover_chem_kg) * avg_chem_price
i_chem_cost = (i_chem_kg + i_startup_chem_kg + i_changeover_chem_kg) * avg_chem_price

p_waste_cost = (p_waste_L + p_startup_disp_L) * waste_handling_price + (p_changeover_dye_kg + p_startup_dye_kg) * dye_stuff_price + (p_changeover_chem_kg + p_startup_chem_kg) * avg_chem_price
i_waste_cost = (i_waste_L + i_startup_disp_L) * waste_handling_price + (i_changeover_dye_kg + i_startup_dye_kg) * dye_stuff_price + (i_changeover_chem_kg + i_startup_chem_kg) * avg_chem_price

p_labor_cost = (annual_changeovers * p_changeover_min / 60) * labor_price
i_labor_cost = (annual_changeovers * i_changeover_min / 60) * labor_price

# ====================== CHARTS ======================
st.markdown("### 📈 Total Annual Operating Costs")
cost_fig = go.Figure()
cost_fig.add_trace(go.Bar(name="Traditional Padder", x=["Energy", "Water", "Dye", "Chemistry", "Waste", "Labor"],
                          y=[p_energy_cost, p_water_cost, p_dye_cost, p_chem_cost, p_waste_cost, p_labor_cost], marker_color="#FF5252"))
cost_fig.add_trace(go.Bar(name="Imogo Dye-Max", x=["Energy", "Water", "Dye", "Chemistry", "Waste", "Labor"],
                          y=[i_energy_cost, i_water_cost, i_dye_cost, i_chem_cost, i_waste_cost, i_labor_cost], marker_color="#1E88E5"))
cost_fig.update_layout(barmode="group", height=420)
st.plotly_chart(cost_fig, use_container_width=True)

st.markdown("### 📊 Savings Breakdown Chart")
fig_savings = go.Figure(go.Bar(
    x=monetary_df["Savings (€/year)"],
    y=monetary_df["Category"],
    orientation='h',
    marker_color=['#FF9800', '#FF5722', '#00B0FF', '#9C27B0', '#00C853', '#1E88E5']
))
fig_savings.update_layout(height=380, xaxis_title="€ Savings per year")
st.plotly_chart(fig_savings, use_container_width=True)

# ====================== NICER PDF REPORT ======================
st.markdown("---")
st.subheader("📄 Export Full Report")

# Create nice HTML report
html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Imogo Dye-Max ROI Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ text-align: center; color: #1E3A8A; }}
        h2 {{ color: #1E40AF; border-bottom: 2px solid #93C5FD; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #94A3B8; padding: 10px; text-align: right; }}
        th {{ background-color: #E0F2FE; text-align: left; }}
        .metric {{ font-size: 1.1em; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Imogo Dye-Max ROI Report</h1>
    <p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

    <h2>Savings Overview</h2>
    <p class="metric">Annual Savings: <strong>€{annual_savings:,.0f}</strong></p>
    <p class="metric">Payback Period: <strong>{payback_months:.1f} months</strong></p>
    <p class="metric">Investment: <strong>€{investment_cost:,.0f}</strong></p>

    <h2>Production Summary</h2>
    <p><strong>Traditional Padder:</strong> {base_annual_kg:,.0f} kg/year ({base_daily_kg:,.0f} kg/day) | {running_speed_m_min_p:,.1f} m/min</p>
    <p><strong>Imogo Dye-Max:</strong> {base_annual_kg:,.0f} kg/year ({base_daily_kg:,.0f} kg/day) | {running_speed_m_min_i:,.1f} m/min (+{extra_kg_per_year:,.0f} kg/year extra)</p>

    <h2>Key Savings</h2>
    <p>Dye Stuff Savings: <strong>{total_dye_savings_kg:,.0f} kg/year</strong></p>
    <p>Chemistry Savings: <strong>{total_chem_savings_kg:,.0f} kg/year</strong></p>
    <p>B-quality Fabric Savings: <strong>€{fabric_b_savings:,.0f}</strong></p>
    <p>Waste Fabric Savings: <strong>€{fabric_waste_savings:,.0f}</strong></p>
    <p>Water Savings: <strong>{(p_disp_L + p_startup_disp_L + p_waste_L - i_disp_L - i_startup_disp_L - i_waste_L)/1000:,.0f} m³/year</strong></p>
    <p>CO₂ Savings: <strong>{(energy_savings / elec_price * co2_per_kwh / 1000):,.1f} tonnes/year</strong></p>

    <h2>Monetary Savings Breakdown</h2>
    {monetary_df.to_html(index=False, classes='table')}

    <p style="text-align:center; margin-top:50px; color:#64748B;">
        Generated with Imogo ROI Calculator
    </p>
</body>
</html>
"""

if st.download_button("📥 Download Professional Report as HTML (Print → Save as PDF)", 
                     data=html_report, 
                     file_name="Imogo_Dye-Max_ROI_Report.html", 
                     mime="text/html"):
    st.success("✅ Report downloaded! Open the file → Ctrl+P → Save as PDF for best result.")

st.success("✅ Nicer report layout with charts ready.")