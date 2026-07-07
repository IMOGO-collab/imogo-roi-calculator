import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Imogo Dye-max vs Exhaust ROI", layout="wide", page_icon="💰")
st.title("💰 Imogo Dye-Max vs Traditional Exhaust – ROI Calculator")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("💲 Cost Prices")
    elec_price = st.number_input("Electricity (€/kWh)", value=0.10, step=0.01, key="elec")
    water_price = st.number_input("Water (€/L)", value=0.0001, step=0.0001, format="%.4f", key="water")
    dye_price = st.number_input("Dye stuff (€/kg)", value=5.0, step=0.5, key="dye_p")
    
    st.subheader("Chemistry Prices (€/kg)")
    wetting_price = st.number_input("Wetting agent", value=0.8, key="wet_p")
    soda_price = st.number_input("Soda ash", value=0.35, key="soda_p")
    caustic_price = st.number_input("NAOH 50%", value=0.25, key="cau_p")
    seq_price = st.number_input("Sequestering", value=1.2, key="seq_p")
    lev_price = st.number_input("Levelling", value=1.0, key="lev_p")
    lub_price = st.number_input("Lubrication", value=1.0, key="lub_p")
    anti_price = st.number_input("Anti foaming", value=1.2, key="anti_p")
    salt_price = st.number_input("Salt", value=0.1, key="salt_p")
    
    st.subheader("Fabric")
    fiber_price = st.number_input("Fiber / Fabric cost (€/kg)", value=2.0, step=0.1, key="fiber_p")
    
    labor_price = st.number_input("Labor (€/man-hour)", value=1.0, key="labor")
    waste_price = st.number_input("Waste handling (€/L)", value=0.002, format="%.4f", key="waste_p")
    co2_factor = st.number_input("CO₂ kg/kWh", value=0.202, step=0.001, key="co2")
    investment = st.number_input("Imogo Investment (€)", value=635000, step=5000, key="inv")

# ====================== PRODUCTION PARAMETERS ======================
st.subheader("📊 Production Parameters")
col_ex, col_dm, col_shared = st.columns([2, 2, 2])

with col_ex:
    st.subheader("🔴 Traditional Exhaust")
    batch_ex = st.number_input("Batch size (kg)", value=200, key="batch_ex")
    ports_ex = st.number_input("Number of ports", value=5, key="ports_ex")
    liq_ex = st.number_input("Liquid ratio (L/kg)", value=5.0, key="liq_ex")
    
    waste_ex = batch_ex * liq_ex
    total_waste_all_ports = waste_ex * ports_ex
    st.info(f"**Waste per color change:** {waste_ex:,.0f} L")
    st.info(f"**Total waste in all ports:** {total_waste_all_ports:,.0f} L")

    batches_per_day_ex = ports_ex * 6
    st.info(f"**Batches per day:** {batches_per_day_ex} (6 per port)")

    fiber_loss_ex = st.number_input("Fiber loss (%)", value=2.0, step=0.1, key="fl_ex") / 100

with col_dm:
    st.subheader("🔵 Imogo Dye-max")
    batch_dm = st.number_input("Batch size (kg)", value=400, key="batch_dm")
    liq_dm = st.number_input("Liquid ratio (L/kg)", value=1.3, key="liq_dm")
    waste_dm = st.number_input("Waste/changeover (L)", value=50, key="waste_dm")
    batches_per_day_dm = st.number_input("Batches per day", value=15.00, step=0.25, key="bpd_dm")
    fiber_loss_dm = st.number_input("Fiber loss (%)", value=0.3, step=0.1, key="fl_dm") / 100

    changeover_min_dm = st.number_input("Changeover time per batch (min)", value=30, step=1, key="ch_dm")

with col_shared:
    st.subheader("Common")
    fabric_width = st.number_input("Fabric width (m)", value=2.2, key="width")
    gsm = st.number_input("Fabric GSM (kg/m²)", value=0.2, key="gsm")
    days_year = st.number_input("Working days/year", value=300, key="days")

# ====================== PRODUCTION SPEED FOR DYE-MAX ======================
daily_kg_dm = batch_dm * batches_per_day_dm
daily_meters_dm = daily_kg_dm / (fabric_width * gsm) if (fabric_width * gsm) > 0 else 0
effective_hours_dm = 24 - (batches_per_day_dm * changeover_min_dm / 60.0)
production_speed_dm = daily_meters_dm / (effective_hours_dm * 60) if effective_hours_dm > 0 else 0

st.info(f"**Imogo Dye-Max Production speed:** **{production_speed_dm:,.1f} m/min**  "
        f"({daily_kg_dm:,.0f} kg/day | Effective {effective_hours_dm:.1f} h/day)")

# ====================== PRODUCTION VOLUME SUMMARY ======================
st.subheader("📊 Production Volume Summary")
p1, p2 = st.columns(2)
with p1:
    st.metric("**Traditional Exhaust**", f"{batch_ex * batches_per_day_ex * days_year:,.0f} kg/year")
    st.caption(f"{batch_ex * batches_per_day_ex:,.0f} kg/day | {batches_per_day_ex * days_year:,.0f} batches/year")
with p2:
    annual_dm = batch_dm * batches_per_day_dm * days_year
    extra = annual_dm - (batch_ex * batches_per_day_ex * days_year)
    st.metric("**Imogo Dye-Max**", f"{annual_dm:,.0f} kg/year", f"↑ {extra:,.0f} kg/year extra")
    st.caption(f"{batch_dm * batches_per_day_dm:,.0f} kg/day | {batches_per_day_dm * days_year:,.0f} batches/year")

# Production speed for Dye-Max
daily_kg_dm = batch_dm * batches_per_day_dm
daily_meters_dm = daily_kg_dm / (fabric_width * gsm) if (fabric_width * gsm) > 0 else 0
production_speed_dm = daily_meters_dm / (24 * 60)

st.info(f"**Imogo Dye-Max Production speed:** **{production_speed_dm:,.1f} m/min**  ({daily_kg_dm:,.0f} kg/day)")

# ====================== ENERGY ======================
st.subheader("⚡ Energy per kg fabric")
en1, en2 = st.columns(2)
with en1:
    st.markdown("**Exhaust**")
    en_op_ex = st.number_input("Machine op (kWh/kg)", value=0.11, key="enop_ex")
    en_steam_ex = st.number_input("Steam (kWh/kg)", value=0.4, key="ensteam_ex")
    en_wwt_ex = st.number_input("WW Treatment (kWh/L)", value=0.005, key="enwwt_ex")
    en_dry_ex = st.number_input("Drying (kWh/kg)", value=0.0, key="endry_ex")
with en2:
    st.markdown("**Dye-max**")
    en_op_dm = st.number_input("Machine op (kWh/kg)", value=0.028, key="enop_dm")
    en_steam_dm = st.number_input("Steam (kWh/kg)", value=0.0, key="ensteam_dm")
    en_wwt_dm = st.number_input("WW Treatment (kWh/L)", value=0.005, key="enwwt_dm")
    en_dry_dm = st.number_input("Drying (kWh/kg)", value=0.4, key="endry_dm")

# ====================== RECIPE ======================
st.subheader("🧪 Chemistry Recipe")
r1, r2 = st.columns(2)

with r1:
    st.markdown("**Exhaust**")
    dye_a_ex_owf = st.number_input("Dye A (%) OWF", value=7.125, step=0.01, key="da_ex") / 100
    wetting_ex = st.number_input("Wetting (g/L)", value=2.0, key="wet_ex")
    soda_ex = st.number_input("Soda (g/L)", value=20.0, key="soda_ex")
    caustic_ex = st.number_input("NAOH (g/L)", value=1.5, key="cau_ex")
    seq_ex = st.number_input("Sequestering (g/L)", value=1.0, key="seq_ex")
    lev_ex = st.number_input("Levelling (g/L)", value=2.0, key="lev_ex")
    lub_ex = st.number_input("Lubrication (g/L)", value=2.0, key="lub_ex")
    anti_ex = st.number_input("Anti foam (g/L)", value=0.5, key="anti_ex")
    salt_ex = st.number_input("Salt (g/L)", value=80.0, key="salt_ex")

with r2:
    st.markdown("**Dye-max**")
    dye_reduction_pct = st.number_input("Dye reduction (%) vs Exhaust", value=10.0, step=0.1, key="dye_red")
    dye_a_dm_owf = dye_a_ex_owf * (1 - dye_reduction_pct / 100)
    dye_a_dm_gl = (dye_a_dm_owf * 1000) / liq_dm if liq_dm > 0 else 0
    st.info(f"Dye A OWF: **{dye_a_dm_owf*100:.3f}%** | Concentration: **{dye_a_dm_gl:.1f} g/L**")
    
    wetting_dm = st.number_input("Wetting (g/L)", value=1.0, key="wet_dm")
    soda_dm = st.number_input("Soda (g/L)", value=20.0, key="soda_dm")
    caustic_dm = st.number_input("NAOH (g/L)", value=5.0, key="cau_dm")
    seq_dm = st.number_input("Sequestering (g/L)", value=0.0, key="seq_dm")
    lev_dm = st.number_input("Levelling (g/L)", value=1.0, key="lev_dm")
    lub_dm = st.number_input("Lubrication (g/L)", value=0.0, key="lub_dm")
    anti_dm = st.number_input("Anti foam (g/L)", value=0.0, key="anti_dm")
    salt_dm = st.number_input("Salt (g/L)", value=0.0, key="salt_dm")

# ====================== CALCULATIONS ======================
batches_ex = batches_per_day_ex * days_year
batches_dm = batches_per_day_dm * days_year

annual_ex = batch_ex * batches_ex
annual_dm = batch_dm * batches_dm
daily_ex = annual_ex / days_year if days_year > 0 else 0
daily_dm = annual_dm / days_year if days_year > 0 else 0

water_ex = annual_ex * liq_ex
water_dm = annual_dm * liq_dm

dye_ex = annual_ex * dye_a_ex_owf
dye_dm = annual_dm * dye_a_dm_owf

def calc_chem(kg, liq, g_l):
    return kg * liq * (g_l / 1000)

chem_ex = sum([calc_chem(annual_ex, liq_ex, v) * p for v, p in [
    (wetting_ex, wetting_price),(soda_ex, soda_price),(caustic_ex, caustic_price),
    (seq_ex, seq_price),(lev_ex, lev_price),(lub_ex, lub_price),
    (anti_ex, anti_price),(salt_ex, salt_price)]])

chem_dm = sum([calc_chem(annual_dm, liq_dm, v) * p for v, p in [
    (wetting_dm, wetting_price),(soda_dm, soda_price),(caustic_dm, caustic_price),
    (seq_dm, seq_price),(lev_dm, lev_price),(lub_dm, lub_price),
    (anti_dm, anti_price),(salt_dm, salt_price)]])

# ====================== ENERGY ======================
energy_base_ex = (en_op_ex + en_steam_ex + en_dry_ex) * annual_ex
energy_wwt_ex = batches_ex * waste_ex * en_wwt_ex
energy_total_ex = energy_base_ex + energy_wwt_ex

energy_base_dm = (en_op_dm + en_steam_dm + en_dry_dm) * annual_dm
energy_wwt_dm = batches_dm * waste_dm * en_wwt_dm
energy_total_dm = energy_base_dm + energy_wwt_dm

energy_sav_kwh = energy_total_ex - energy_total_dm

# Fiber
fiber_loss_kg_ex = annual_ex * fiber_loss_ex
fiber_loss_kg_dm = annual_dm * fiber_loss_dm

# Savings
dye_sav = (dye_ex - dye_dm) * dye_price
water_sav = (water_ex - water_dm) * water_price
chem_sav = chem_ex - chem_dm
energy_sav = energy_sav_kwh * elec_price
fiber_sav = (fiber_loss_kg_ex - fiber_loss_kg_dm) * fiber_price
waste_sav = (waste_ex * batches_ex - waste_dm * batches_dm) * waste_price

total_savings = dye_sav + water_sav + chem_sav + energy_sav + fiber_sav + waste_sav
payback_months = (investment / total_savings * 12) if total_savings > 0 else 0
co2_savings = energy_sav_kwh * co2_factor / 1000

# ====================== ENERGY DEBUG ======================
st.subheader("🔍 Base Energy Debug")
col_b1, col_b2 = st.columns(2)
with col_b1:
    st.write("**Exhaust Base Energy**")
    st.write(f"Machine op: {en_op_ex:.3f} kWh/kg")
    st.write(f"Steam: {en_steam_ex:.3f} kWh/kg")
    st.write(f"Drying: {en_dry_ex:.3f} kWh/kg")
    st.write(f"**Sum per kg:** {en_op_ex + en_steam_ex + en_dry_ex:.3f} kWh/kg")
    st.write(f"**Total Base:** {energy_base_ex:,.0f} kWh")
with col_b2:
    st.write("**Dye-Max Base Energy**")
    st.write(f"Machine op: {en_op_dm:.3f} kWh/kg")
    st.write(f"Steam: {en_steam_dm:.3f} kWh/kg")
    st.write(f"Drying: {en_dry_dm:.3f} kWh/kg")
    st.write(f"**Sum per kg:** {en_op_dm + en_steam_dm + en_dry_dm:.3f} kWh/kg")
    st.write(f"**Total Base:** {energy_base_dm:,.0f} kWh")
# ====================== SAVINGS OVERVIEW ======================
st.subheader("📈 Savings Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("**Annual € Savings**", f"€{total_savings:,.0f}")
c2.metric("**Payback Period**", f"{payback_months:.1f} months")
c3.metric("**Dye Stuff Savings**", f"{dye_ex - dye_dm:,.0f} kg/year")
c4.metric("**Chemistry Savings**", f"{chem_ex - chem_dm:,.0f} kg/year")

st.subheader("🌍 Environmental Savings")
e1, e2, e3 = st.columns(3)
e1.metric("**Water Savings**", f"{(water_ex - water_dm)/1000:,.0f} m³/year")
e2.metric("**CO₂ Savings**", f"{co2_savings:,.1f} tonnes/year")
e3.metric("**Energy Savings**", f"{energy_sav_kwh:,.0f} kWh/year")

# ====================== BREAKDOWN ======================
st.subheader("💰 Monetary Savings Breakdown (€/year)")
breakdown = pd.DataFrame({
    "Category": ["Dye Stuff", "Wetting Agent", "Soda Ash", "NAOH 50%", "Sequestering", "Levelling", 
                 "Lubrication", "Anti Foaming", "Salt", "Process Water", "Waste Water Handling", "Energy", "Fiber Loss"],
    "Savings (€/year)": [
        dye_sav,
        calc_chem(annual_ex, liq_ex, wetting_ex)*wetting_price - calc_chem(annual_dm, liq_dm, wetting_dm)*wetting_price,
        calc_chem(annual_ex, liq_ex, soda_ex)*soda_price - calc_chem(annual_dm, liq_dm, soda_dm)*soda_price,
        calc_chem(annual_ex, liq_ex, caustic_ex)*caustic_price - calc_chem(annual_dm, liq_dm, caustic_dm)*caustic_price,
        calc_chem(annual_ex, liq_ex, seq_ex)*seq_price - calc_chem(annual_dm, liq_dm, seq_dm)*seq_price,
        calc_chem(annual_ex, liq_ex, lev_ex)*lev_price - calc_chem(annual_dm, liq_dm, lev_dm)*lev_price,
        calc_chem(annual_ex, liq_ex, lub_ex)*lub_price - calc_chem(annual_dm, liq_dm, lub_dm)*lub_price,
        calc_chem(annual_ex, liq_ex, anti_ex)*anti_price - calc_chem(annual_dm, liq_dm, anti_dm)*anti_price,
        calc_chem(annual_ex, liq_ex, salt_ex)*salt_price - calc_chem(annual_dm, liq_dm, salt_dm)*salt_price,
        water_sav,
        waste_sav,
        energy_sav,
        fiber_sav
    ]
})

df = pd.DataFrame(breakdown)
df = df.round(0)
df["Savings (€/year)"] = df["Savings (€/year)"].map("€{:,.0f}".format)

st.table(
    breakdown.style.format("€{:,.0f}", subset=["Savings (€/year)"])
)
# ====================== TOTAL COST PER KG ======================
st.subheader("💰 Total Cost per kg Fabric")

annual_kg = annual_ex   # Använder Exhaust volym som bas (samma volym för båda)

# ====================== TOTAL COST FOR TRADITIONAL EXHAUST ======================
total_cost_ex = (
    (dye_ex * dye_price) + 
    chem_ex +
    (water_ex * water_price) +
    (waste_ex * batches_ex * waste_price) +
    (energy_total_ex * elec_price) +
    (batches_ex * 30 / 60 * labor_price) +      # ungefärlig labor
    (fiber_loss_kg_ex * fiber_price)            # fiber loss
)

# ====================== TOTAL COST FOR IMOGO DYE-MAX ======================
total_cost_dm = (
    (dye_dm * dye_price) + 
    chem_dm +
    (water_dm * water_price) +
    (waste_dm * batches_dm * waste_price) +
    (energy_total_dm * elec_price) +
    (batches_dm * changeover_min_dm / 60 * labor_price) +
    (fiber_loss_kg_dm * fiber_price)
)

cost_per_kg_ex = total_cost_ex / annual_kg if annual_kg > 0 else 0
cost_per_kg_dm = total_cost_dm / annual_kg if annual_kg > 0 else 0

savings_per_kg = cost_per_kg_ex - cost_per_kg_dm
percentage_savings = (savings_per_kg / cost_per_kg_ex * 100) if cost_per_kg_ex > 0 else 0

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric("**Traditional Exhaust**", f"€{cost_per_kg_ex:.3f} / kg")

with col_c2:
    st.metric(
        label="**Imogo Dye-Max**", 
        value=f"€{cost_per_kg_dm:.3f} / kg",
        delta=f"↓ €{savings_per_kg:.3f} / kg ({percentage_savings:.1f}%)"
    )

st.caption("Total cost per kg includes Dye, Chemistry, Water, Waste, Energy, Labor and Fiber loss")

# ====================== GRAPHS ======================
st.markdown("### 📊 Visual Savings Overview")

# Horizontal bar chart - Savings per category
fig1 = go.Figure(go.Bar(
    y=breakdown["Category"],
    x=breakdown["Savings (€/year)"],
    orientation='h',
    marker_color=['#FF9800', '#FF5722', '#00B0FF', '#9C27B0', '#00C853', '#1E88E5', '#FF5252', '#1E88E5', '#10B981', '#F59E0B']
))
fig1.update_layout(
    title="Årliga besparingar per kategori (€/year)",
    height=520,
    xaxis_title="€ Savings",
    yaxis={'categoryorder':'total ascending'},
    margin=dict(l=250)
)
st.plotly_chart(fig1, use_container_width=True)

# Total Cost per kg comparison
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="Traditional Exhaust",
    x=["Total Cost / kg"],
    y=[cost_per_kg_ex],
    marker_color="#EF4444"
))
fig2.add_trace(go.Bar(
    name="Imogo Dye-Max",
    x=["Total Cost / kg"],
    y=[cost_per_kg_dm],
    marker_color="#10B981"
))
fig2.update_layout(
    title="Total Cost per kg Fabric",
    height=400,
    barmode='group',
    yaxis_title="€ / kg",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig2, use_container_width=True)

# ====================== PDF REPORT ======================
st.markdown("---")
st.subheader("📄 Export Full Report")

html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Imogo Dye-max ROI Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; color: #1f2937; }}
        h1 {{ text-align: center; color: #1E40AF; font-size: 28px; }}
        h2 {{ color: #1E40AF; border-bottom: 3px solid #93C5FD; padding-bottom: 8px; }}
        .metric {{ background: linear-gradient(135deg, #f0f9ff, #e0f2fe); padding: 20px; border-radius: 12px; margin: 15px 0; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 12px; text-align: right; }}
        th {{ background-color: #1E40AF; color: white; }}
        .footer {{ text-align: center; margin-top: 60px; color: #64748b; }}
    </style>
</head>
<body>
    <h1>Imogo Dye-max ROI Report</h1>
    <p style="text-align:center; color:#64748b;"><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    
    <div class="metric">
        <h2>Key Results</h2>
        <p style="font-size:1.5em;"><strong>Annual Savings: €{total_savings:,.0f}</strong></p>
        <p><strong>Payback Period: {payback_months:.1f} months</strong></p>
        <p><strong>Investment Cost: €{investment:,.0f}</strong></p>
    </div>

    <h2>Production Summary</h2>
    <p><strong>Traditional Exhaust:</strong> {annual_ex:,.0f} kg/year</p>
    <p><strong>Imogo Dye-max:</strong> {annual_dm:,.0f} kg/year</p>

    <h2>Physical Savings</h2>
    <p>Dye Stuff: <strong>{dye_ex - dye_dm:,.0f} kg/year</strong></p>
    <p>Chemistry: <strong>{chem_ex - chem_dm:,.0f} kg/year</strong></p>
    <p>Water: <strong>{(water_ex - water_dm)/1000:,.0f} m³/year</strong></p>
    <p>Energy: <strong>{energy_sav_kwh:,.0f} kWh/year</strong></p>
    <p>CO₂: <strong>{co2_savings:,.1f} tonnes/year</strong></p>

    <h2>Monetary Savings Breakdown</h2>
    {df.to_html(index=False, classes='table')}

    <div class="footer">
        Imogo Dye-max ROI Calculator • Confidential
    </div>
</body>
</html>
"""

if st.download_button(
    label="📥 Download Professional Report as HTML (Print → Save as PDF)",
    data=html_report,
    file_name="Imogo_Exhaust_ROI_Report.html",
    mime="text/html"
):
    st.success("✅ Report downloaded! Open the file → Ctrl+P → Save as PDF")
