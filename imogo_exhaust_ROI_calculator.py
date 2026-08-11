import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ⚠️ VIKTIGT: st.set_page_config MÅSTE ligga först av alla Streamlit-kommandon!
st.set_page_config(page_title="Imogo Dye-max vs Exhaust ROI", layout="wide", page_icon="💰")

# ====================== LÖSENORDSSKYDD ======================
def check_password():
    """Returns True if the user has entered the correct password."""
    
    # Försök hämta lösenord från Streamlit Secrets (används online)
    try:
        CORRECT_PASSWORD = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        # Om filen/nyckeln inte finns (t.ex. vid lokal körning), hoppa över lösenordet helt!
        return True 

    # Resten körs bara online där lösenord är konfigurerat:
    def password_entered():
        if st.session_state.get("password_input") == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            if "password_input" in st.session_state:
                del st.session_state["password_input"]  # Rensa fältet ur minnet
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter password to gain access:", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Enter password to gain access:", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        st.error("🔒 Incorrect password. Please try again.")
        return False
    else:
        return True
# 🔑 ANROPA FUNKTIONEN BARA EN GÅNG HÄR
if not check_password():
    st.stop()

# ====================== DIN APP BÖRJAR HÄR ======================
st.title("💰 Imogo Dye-Max vs Traditional Exhaust – ROI Calculator")

# ====================== INITIALISERA VALUTA-STATE ======================
# Vi sätter upp standardvärden i Euro som bas. Dessa anpassas dynamiskt om växelkursen ändras.
if 'prev_conv' not in st.session_state:
    st.session_state.prev_conv = 1.0

defaults = {
    "elec": 0.10, "water": 0.0001, "dye_p": 5.0,
    "wet_p": 0.8, "soda_p": 0.35, "cau_p": 0.25, "seq_p": 1.2,
    "lev_p": 1.0, "lub_p": 1.0, "anti_p": 1.2, "salt_p": 0.1,
    "fiber_p": 2.0, "labor": 1.0, "waste_p": 0.002, "inv": 635000.0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = float(v)

# ====================== SIDEBAR ======================
with st.sidebar:
    # 👤 Customer name
    customer_name = st.text_input("Customer name", value="", key="customer_name_input")
    
    curr = st.text_input("Currency (i.e. EUR, SEK, USD)", value="EUR").strip().upper()
    
    # Hämta det inskrivna värdet från minnet (eller 1.00 första gången)
    current_rate = st.session_state.get("conv_key", 1.00)
    
    # Skapa fältet med den dynamiska rubriken
    conv = st.number_input(
        f"Exchange rate (1 EUR = {current_rate:.2f} {curr})", 
        value=1.00, 
        step=0.10, 
        format="%.2f",
        key="conv_key"
    )
    # OM användaren ändrar växelkursen, räkna om alla värden i session_state
    if conv != st.session_state.prev_conv:
        factor = conv / st.session_state.prev_conv
        for k in defaults.keys():
            st.session_state[k] = float(st.session_state[k] * factor)
        st.session_state.prev_conv = conv

    st.markdown("---")
    st.header(f"💲 Costs ({curr})")
    
    elec_price = st.number_input(f"Electricity ({curr}/kWh)", step=0.01, format="%.2f", key="elec")
    water_price = st.number_input(f"Water ({curr}/L)", step=0.0001, format="%.5f", key="water")
    dye_price = st.number_input(f"Dye stuff ({curr}/kg)", step=0.5, format="%.2f", key="dye_p")
    
    st.subheader(f"Chemistry Prices ({curr}/kg)")
    wetting_price = st.number_input("Wetting agent", step=0.1, format="%.2f", key="wet_p")
    soda_price = st.number_input("Soda ash", step=0.05, format="%.2f", key="soda_p")
    caustic_price = st.number_input("NAOH 50%", step=0.05, format="%.2f", key="cau_p")
    seq_price = st.number_input("Sequestering", step=0.1, format="%.2f", key="seq_p")
    lev_price = st.number_input("Levelling", step=0.1, format="%.2f", key="lev_p")
    lub_price = st.number_input("Lubrication", step=0.1, format="%.2f", key="lub_p")
    anti_price = st.number_input("Anti foaming", step=0.1, format="%.2f", key="anti_p")
    salt_price = st.number_input("Salt", step=0.05, format="%.2f", key="salt_p")
    
    st.subheader("Fabric")
    fiber_price = st.number_input(f"Fiber / Fabric cost ({curr}/kg)", step=0.1, format="%.2f", key="fiber_p")
    
    labor_price = st.number_input(f"Labor ({curr}/man-hour)", step=0.1, format="%.2f", key="labor")
    waste_price = st.number_input(f"Waste handling ({curr}/L)", format="%.5f", key="waste_p")
    co2_factor = st.number_input("CO₂ kg/kWh", value=0.202, step=0.001, key="co2")
    investment = st.number_input(f"Imogo Investment ({curr})", step=5000.0, format="%.0f", key="inv")

# ====================== PRODUCTION PARAMETERS ======================
st.subheader("📊 Production Parameters")
col_ex, col_dm, col_shared = st.columns([2, 2, 2])

with col_ex:
    st.subheader("🔴 Traditional Exhaust")
    batch_ex = st.number_input("Machine capacity (kg)", value=250, key="batch_ex")
    ports_ex = st.number_input("Number of machines", value=4, key="ports_ex")
    liq_ex = st.number_input("Liquid ratio (L/kg)", value=5.0, key="liq_ex")
    
    waste_ex = batch_ex * liq_ex
    total_waste_all_ports = waste_ex * ports_ex
    st.info(f"**Waste per color change per machine:** {waste_ex:,.0f} L")
    st.info(f"**Total waste in all machines:** {total_waste_all_ports:,.0f} L")

    batches_per_day_ex = ports_ex * 6
    st.info(f"**Batches per day:** {batches_per_day_ex} (6 per machine)")

    fiber_loss_ex = st.number_input("Fiber loss (%)", value=2.0, step=0.1, key="fl_ex") / 100

with col_dm:
    st.subheader("🔵 Imogo Dye-max")
    batch_dm = st.number_input("Batch size (kg)", value=400, key="batch_dm")
    liq_dm = st.number_input("Liquid ratio (L/kg)", value=1.3, key="liq_dm")
    waste_dm = st.number_input("Waste/changeover (L)", value=50, key="waste_dm")
    batches_per_day_dm = st.number_input("Batches per day", value=15.00, step=0.25, key="bpd_dm")
    changeover_min_dm = st.number_input("Changeover time per batch (min)", value=30, step=1, key="ch_dm")
    fiber_loss_dm = st.number_input("Fiber loss (%)", value=0.3, step=0.1, key="fl_dm") / 100

with col_shared:
    st.subheader("Common")
    fabric_width = st.number_input("Fabric width (m)", value=2.2, key="width")
    gsm = st.number_input("Fabric GSM (kg/m²)", value=0.2, key="gsm")
    days_year = st.number_input("Working days/year", value=300, key="days")
    hours_day = st.number_input("Working hours/day", value=24.0, step=1.0, key="hours_day")

# ====================== PRODUCTION VOLUME SUMMARY ======================
st.subheader("📊 Production Volume Summary & Flexibility")
p1, p2, p3 = st.columns(3)

# Använd de befintliga uträknade totala batcherna per år
total_batches_ex = batches_per_day_ex * days_year
total_batches_dm = batches_per_day_dm * days_year

# Räkna ut den procentuella skillnaden mellan Dye-Max och Exhaust
if total_batches_ex > 0:
    pct_diff_batches = ((total_batches_dm - total_batches_ex) / total_batches_ex) * 100
else:
    pct_diff_batches = 0.0

# 1. Traditional Exhaust
with p1:
    ex_annual_text = f"{batch_ex * batches_per_day_ex * days_year:,.0f}".replace(",", " ")
    st.metric("**Traditional Exhaust**", f"{ex_annual_text} kg/year")
    
    ex_daily_text = f"{batch_ex * batches_per_day_ex:,.0f}".replace(",", " ")
    ex_batches_text = f"{total_batches_ex:,.0f}".replace(",", " ")
    st.caption(f"{ex_daily_text} kg/day | {ex_batches_text} batches/year")

# 2. Imogo Dye-Max
with p2:
    annual_dm = batch_dm * batches_per_day_dm * days_year
    extra = annual_dm - (batch_ex * batches_per_day_ex * days_year)
    
    dm_annual_text = f"{annual_dm:,.0f}".replace(",", " ")
    extra_text = f"↑ {extra:,.0f} kg/year extra" if extra != 0 else "Same volume"
    st.metric("**Imogo Dye-Max**", f"{dm_annual_text} kg/year", extra_text)
    
    dm_daily_text = f"{batch_dm * batches_per_day_dm:,.0f}".replace(",", " ")
    dm_batches_text = f"{total_batches_dm:,.0f}".replace(",", " ")
    st.caption(f"{dm_daily_text} kg/day | {dm_batches_text} batches/year")

# 3. Flexibilitet (Procentuell jämförelse av totalt antal batcher)
with p3:
    # Skicka med procentsatsen i delta så fixar Streamlit pilen automatiskt (röd nedåt vid minus, grön uppåt vid plus)
    delta_text = f"{pct_diff_batches:.1f}%".replace(".", ",")
    
    st.metric(
        "**Batch Capacity / Flexibility**", 
        f"{pct_diff_batches:.0f}%".replace(".", ",") + "%" if isinstance(pct_diff_batches, float) else f"{pct_diff_batches}%", 
        delta=delta_text
    )
    
    # Flytta jämförelsen till caption för enhetlig design
    batch_comp_text = f"{total_batches_dm:,.0f} vs {total_batches_ex:,.0f} total batches/yr".replace(",", " ")
    st.caption(batch_comp_text)

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
    soda_ex = st.number_input("Soda (g/L)", value=5.0, key="soda_ex")
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
    soda_dm = st.number_input("Soda (g/L)", value=16.0, key="soda_dm")
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

# 1. Beräkna fysiska kilon för kemikalier (detta löser miljonfelet i kg/year)
chem_kg_ex = sum([calc_chem(annual_ex, liq_ex, v) for v in [wetting_ex, soda_ex, caustic_ex, seq_ex, lev_ex, lub_ex, anti_ex, salt_ex]])
chem_kg_dm = sum([calc_chem(annual_dm, liq_dm, v) for v in [wetting_dm, soda_dm, caustic_dm, seq_dm, lev_dm, lub_dm, anti_dm, salt_dm]])
chem_sav_kg_total = chem_kg_ex - chem_kg_dm

# 2. Beräkna ekonomiska besparingar i pengar
dye_sav = (dye_ex - dye_dm) * dye_price
water_sav = (water_ex - water_dm) * water_price
chem_sav = chem_ex - chem_dm
energy_sav = energy_sav_kwh * elec_price
fiber_sav = (fiber_loss_kg_ex - fiber_loss_kg_dm) * fiber_price
waste_sav = (waste_ex * batches_ex - waste_dm * batches_dm) * waste_price

# 3. Totala sammanställningar
total_savings = dye_sav + water_sav + chem_sav + energy_sav + fiber_sav + waste_sav
payback_months = (investment / total_savings * 12) if total_savings > 0 else 0
co2_savings = energy_sav_kwh * co2_factor / 1000

# ====================== SAVINGS OVERVIEW ======================
st.subheader("📈 Savings Overview")
c1, c2, c3, c4 = st.columns(4)

# 1. Årliga besparingar (dynamisk valuta + mellanslag istället för komma)
annual_savings_text = f"{curr} {total_savings:,.0f}".replace(",", " ")
c1.metric(f"**Annual {curr} Savings**", annual_savings_text)

# 2. Payback period (Gör om amerikansk punkt till svenskt kommatecken för decimalen)
payback_text = f"{payback_months:.1f}".replace(".", ",")
c2.metric("**Payback Period**", f"{payback_text} months")

# 3. Dye Stuff (Mellanslag istället för komma för tusental)
dye_savings_text = f"{dye_ex - dye_dm:,.0f}".replace(",", " ")
c3.metric("**Dye Stuff Savings**", f"{dye_savings_text} kg/year")

# 4. Chemistry (Mellanslag istället för komma för tusental)
chem_savings_text = f"{chem_sav_kg_total:,.0f}".replace(",", " ")
c4.metric("**Chemistry Savings**", f"{chem_savings_text} kg/year")


st.subheader("🌍 Environmental Savings")
e1, e2, e3 = st.columns(3)

# Water (Mellanslag istället för komma för tusental)
water_text = f"{(water_ex - water_dm)/1000:,.0f}".replace(",", " ")
e1.metric("**Water Savings**", f"{water_text} m³/year")

# CO₂ (Ändrar punkt till svenskt kommatecken för decimalen)
co2_text = f"{co2_savings:.1f}".replace(".", ",")
e2.metric("**CO₂ Savings**", f"{co2_text} tonnes/year")

# Energy (Mellanslag istället för komma för tusental)
energy_text = f"{energy_sav_kwh:,.0f}".replace(",", " ")
e3.metric("**Energy Savings**", f"{energy_text} kWh/year")

# ====================== BREAKDOWN ======================
st.subheader(f"💰 Monetary Savings Breakdown ({curr}/year)")

breakdown = pd.DataFrame({
    "Category": ["Dye Stuff", "Wetting Agent", "Soda Ash", "NAOH 50%", "Sequestering", "Levelling", 
                 "Lubrication", "Anti Foaming", "Salt", "Process Water", "Waste Water Handling", "Energy", "Fiber Loss"],
    f"Savings ({curr}/year)": [
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

# Skapa en ren kopia för visning och PDF-rapporten
df = breakdown.copy()

# Denna rad tvingar fram vald valuta, lägger till tusentalsavgränsare (komma) och rensar bort ALLA decimaler (.0f)
df[f"Savings ({curr}/year)"] = df[f"Savings ({curr}/year)"].map(lambda x: f"{curr} {x:,.0f}".replace(",", " "))

# Visa endast den färdigformaterade tabellen i Streamlit-appen
st.table(df)

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

# HÄR SÄTTER VI 2 DECIMALER (.2f) OCH SVENSKT DECIMALTECKEN (,)
cost_ex_text = f"{cost_per_kg_ex:,.2f}".replace(",", " ").replace(".", ",")
cost_dm_text = f"{cost_per_kg_dm:,.2f}".replace(",", " ").replace(".", ",")
savings_kg_text = f"{savings_per_kg:,.2f}".replace(",", " ").replace(".", ",")
pct_text = f"{percentage_savings:.1f}".replace(".", ",")

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric("**Traditional Exhaust**", f"{curr} {cost_ex_text} / kg")

with col_c2:
    st.metric(
        label="**Imogo Dye-Max**", 
        value=f"{curr} {cost_dm_text} / kg",
        delta=f"↓ {curr} {savings_kg_text} / kg ({pct_text}%)"
    )

st.caption("Total cost per kg includes Dye, Chemistry, Water, Waste, Energy, Labor and Fiber loss")

# ====================== GRAPHS ======================
st.markdown("### 📊 Visual Savings Overview")

# Här skickar vi in de råa siffrorna från 'breakdown' så att Plotly kan rita grafen korrekt utan felmeddelanden
fig1 = go.Figure(go.Bar(
    y=breakdown["Category"],
    x=breakdown[f"Savings ({curr}/year)"],
    orientation='h',
    marker_color='#00B0FF'
))
fig1.update_layout(
    title=f"Årliga besparingar per kategori ({curr}/year)",
    height=520,
    xaxis_title=f"{curr} Savings",
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
    name="Imogo Dye-max",
    x=["Total Cost / kg"],
    y=[cost_per_kg_dm],
    marker_color="#10B981"
))
fig2.update_layout(
    title=f"Total Cost per kg Fabric ({curr})",
    height=400,
    barmode='group',
    bargroupgap=0.15,
    yaxis_title=f"{curr} / kg",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig2, use_container_width=True)

# ====================== REPORT GENERATION ======================
st.subheader("📄 Generate Report")

# Formaterade strängar för resultat
pdf_savings_text = f"{curr} {total_savings:,.0f}".replace(",", " ")
pdf_investment_text = f"{curr} {investment:,.0f}".replace(",", " ")
pdf_payback_text = f"{payback_months:.1f}".replace(".", ",")

pdf_annual_ex = f"{annual_ex:,.0f}".replace(",", " ")
pdf_annual_dm = f"{annual_dm:,.0f}".replace(",", " ")

pdf_dye_sav_kg = f"{dye_ex - dye_dm:,.0f}".replace(",", " ")
pdf_chem_sav_kg = f"{chem_sav_kg_total:,.0f}".replace(",", " ")
pdf_water_sav_m3 = f"{(water_ex - water_dm)/1000:,.0f}".replace(",", " ")
pdf_energy_sav_kwh = f"{energy_sav_kwh:,.0f}".replace(",", " ")
pdf_co2_sav_ton = f"{co2_savings:.1f}".replace(".", ",")

customer_line = f"<p style='text-align:center; font-size:1.2em; color:#1e3a8a; margin-top:-10px;'><strong>Prepared for:</strong> {customer_name}</p>" if customer_name else ""

dye_ex_pct_str = f"{dye_a_ex_owf * 100:.2f}%"
dye_dm_pct_str = f"{dye_a_dm_owf * 100:.2f}%"
water_price_m3 = water_price * 1000

html_report = f"""
<!DOCTYPE html>
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
    {customer_line}
    <p style="text-align:center; color:#64748b;"><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        
    <div class="metric">
        <h2>Key Results</h2>
        <p style="font-size:1.5em;"><strong>Annual Savings: {pdf_savings_text}</strong></p>
        <p><strong>Payback Period: {pdf_payback_text} months</strong></p>
        <p><strong>Investment Cost: {pdf_investment_text}</strong></p>
    </div>

    <h2>Production Summary</h2>
    <p><strong>Traditional Exhaust:</strong> {pdf_annual_ex} kg/year</p>
    <p><strong>Imogo Dye-max:</strong> {pdf_annual_dm} kg/year</p>

    <h2>Physical Savings</h2>
    <p>Dye Stuff: <strong>{pdf_dye_sav_kg} kg/year</strong></p>
    <p>Chemistry: <strong>{pdf_chem_sav_kg} kg/year</strong></p>
    <p>Water: <strong>{pdf_water_sav_m3} m³/year</strong></p>
    <p>Energy: <strong>{pdf_energy_sav_kwh} kWh/year</strong></p>
    <p>CO₂: <strong>{pdf_co2_sav_ton} tonnes/year</strong></p>

    <h2>Monetary Savings Breakdown</h2>
    {df.to_html(index=False, classes='table')}
    
    <h2>Process & Recipe Comparison</h2>
    <table>
        <tr>
            <th style="width: 34%;">Parameter</th>
            <th style="width: 33%;">Traditional Exhaust</th>
            <th style="width: 33%;">Imogo Dye-Max</th>
        </tr>
        <!-- Machine & Process -->
        <tr><td colspan="3" class="section-header">Machine & Process Parameters</td></tr>
        <tr><td>Machine Capacity</td><td>{batch_ex} kg</td><td>{batch_dm} kg</td></tr>
        <tr><td>Batches per day</td><td>{batches_per_day_ex} batches</td><td>{batches_per_day_dm} batches</td></tr>
        <tr><td>Number of Machines</td><td>{ports_ex}</td><td>-</td></tr>
        <tr><td>Changeover Time</td><td>-</td><td>{changeover_min_dm} min</td></tr>
        <tr><td>Liquor Ratio</td><td>1:{liq_ex}</td><td>{liq_dm} L/kg</td></tr>
        <tr><td>Waste per Changeover</td><td>{waste_ex:,.0f} L</td><td>{waste_dm} L</td></tr>
        <tr><td>Fiber Loss</td><td>{fiber_loss_ex*100:.1f}%</td><td>{fiber_loss_dm*100:.1f}%</td></tr>
        
        <!-- Recipe -->
        <tr><td colspan="3" class="section-header">Chemistry Recipe</td></tr>
        <tr><td>Dye OWF</td><td>{dye_ex_pct_str}</td><td>{dye_dm_pct_str} (Red: {dye_reduction_pct:.1f}%)</td></tr>
        <tr><td>Wetting Agent</td><td>{wetting_ex} g/L</td><td>{wetting_dm} g/L</td></tr>
        <tr><td>Soda Ash</td><td>{soda_ex} g/L</td><td>{soda_dm} g/L</td></tr>
        <tr><td>NAOH 50%</td><td>{caustic_ex} g/L</td><td>{caustic_dm} g/L</td></tr>
        <tr><td>Sequestering</td><td>{seq_ex} g/L</td><td>{seq_dm} g/L</td></tr>
        <tr><td>Levelling</td><td>{lev_ex} g/L</td><td>{lev_dm} g/L</td></tr>
        <tr><td>Lubrication</td><td>{lub_ex} g/L</td><td>{lub_dm} g/L</td></tr>
        <tr><td>Anti Foaming</td><td>{anti_ex} g/L</td><td>{anti_dm} g/L</td></tr>
        <tr><td>Salt</td><td>{salt_ex} g/L</td><td>{salt_dm} g/L</td></tr>
    </table>

    <h2>General Parameters & Unit Costs</h2>
    <table>
        <tr>
            <th style="width: 50%;">Parameter</th>
            <th style="width: 50%;">Value</th>
        </tr>
        <!-- General Production -->
        <tr><td colspan="2" class="section-header">General Production</td></tr>
        <tr><td>Working days / year</td><td>{days_year} days</td></tr>
        <tr><td>Working hours / day</td><td>{hours_day} h</td></tr>
        <tr><td>Fabric width & GSM</td><td>{fabric_width} m / {gsm} kg/m²</td></tr>
        
        <!-- Unit Costs -->
        <tr><td colspan="2" class="section-header">Costs & Unit Rates</td></tr>
        <tr><td>Electricity Price</td><td>{elec_price:.2f} {curr}/kWh</td></tr>
        <tr><td>Water Price</td><td>{water_price:.5f} {curr}/L ({water_price_m3:.2f} {curr}/m³)</td></tr>
        <tr><td>Dye Price</td><td>{dye_price:.2f} {curr}/kg</td></tr>
        <tr><td>Wetting Agent Price</td><td>{wetting_price:.2f} {curr}/kg</td></tr>
        <tr><td>Soda Ash Price</td><td>{soda_price:.2f} {curr}/kg</td></tr>
        <tr><td>NAOH 50% Price</td><td>{caustic_price:.2f} {curr}/kg</td></tr>
        <tr><td>Sequestering Price</td><td>{seq_price:.2f} {curr}/kg</td></tr>
        <tr><td>Levelling Price</td><td>{lev_price:.2f} {curr}/kg</td></tr>
        <tr><td>Lubrication Price</td><td>{lub_price:.2f} {curr}/kg</td></tr>
        <tr><td>Anti Foaming Price</td><td>{anti_price:.2f} {curr}/kg</td></tr>
        <tr><td>Salt Price</td><td>{salt_price:.2f} {curr}/kg</td></tr>
        <tr><td>Fiber / Fabric Cost</td><td>{fiber_price:.2f} {curr}/kg</td></tr>
        <tr><td>Labor Price</td><td>{labor_price:.2f} {curr}/man-hour</td></tr>
        <tr><td>Waste Handling Price</td><td>{waste_price:.5f} {curr}/L</td></tr>
        <tr><td>CO₂ Factor</td><td>{co2_factor:.3f} kg/kWh</td></tr>
    </table>

    <p style="margin-top: 30px; font-size: 0.9em; color: #64748b; text-align: center;">
        This report was automatically generated by the Imogo ROI Calculator.
    </p>
</body>
</html>
"""

st.download_button(
    label="📥 Download HTML Report (Print and Save as PDF)",
    data=html_report,
    file_name=f"imogo_roi_report_{datetime.now().strftime('%Y%m%d')}.html",
    mime="text/html"
)
