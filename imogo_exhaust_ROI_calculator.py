import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from translations_exhaust import LANGUAGES  # Importerar vår språkfil

# ⚠️ VIKTIGT: st.set_page_config MÅSTE ligga först av alla Streamlit-kommandon!
st.set_page_config(page_title="Imogo Dye-max vs Exhaust ROI", layout="wide", page_icon="💰")

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


# ====================== SPRÅKVAL & INITIALISERA ======================
lang = st.sidebar.selectbox("🌐 Language", list(LANGUAGES.keys()))
t = LANGUAGES[lang]
st.title(t["title"])

# ====================== INITIALISERA VALUTA-STATE ======================
if 'prev_conv' not in st.session_state:
    st.session_state.prev_conv = 1.0

defaults = {
    "elec": 0.15, "water": 0.0001, "dye_p": 6.0,
    "wet_p": 0.8, "soda_p": 0.35, "cau_p": 0.25, "seq_p": 1.2,
    "lev_p": 1.0, "lub_p": 1.0, "anti_p": 1.2, "salt_p": 0.1,
    "fiber_p": 2.0, "labor": 1.0, "waste_p": 0.002, "inv": 635000.0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = float(v)

# ====================== SIDEBAR ======================
with st.sidebar:
    customer_name = st.text_input(t["customer"], value="", key="customer_name_input")
    
    curr = st.text_input(t["currency"], value="EUR").strip().upper()
    
    current_rate = st.session_state.get("conv_key", 1.00)
    
    conv = st.number_input(
        t["exchange_rate"].format(rate=current_rate, curr=curr), 
        value=1.00, 
        step=0.10, 
        format="%.2f",
        key="conv_key"
    )
    
    if conv != st.session_state.prev_conv:
        factor = conv / st.session_state.prev_conv
        for k in defaults.keys():
            st.session_state[k] = float(st.session_state[k] * factor)
        st.session_state.prev_conv = conv

    st.markdown("---")
    st.header(t["costs_header"].format(curr=curr))
    
    elec_price = st.number_input(t["elec_label"].format(curr=curr), step=0.01, format="%.2f", key="elec")
    water_price = st.number_input(t["water_label"].format(curr=curr), step=0.0001, format="%.5f", key="water")
    dye_price = st.number_input(t["dye_label"].format(curr=curr), step=0.5, format="%.2f", key="dye_p")
    
    st.subheader(t["chem_prices_header"].format(curr=curr))
    wetting_price = st.number_input(t["wetting_price"], step=0.1, format="%.2f", key="wet_p")
    soda_price = st.number_input(t["soda_price"], step=0.05, format="%.2f", key="soda_p")
    caustic_price = st.number_input(t["caustic_price"], step=0.05, format="%.2f", key="cau_p")
    seq_price = st.number_input(t["seq_price"], step=0.1, format="%.2f", key="seq_p")
    lev_price = st.number_input(t["lev_price"], step=0.1, format="%.2f", key="lev_p")
    lub_price = st.number_input(t["lub_price"], step=0.1, format="%.2f", key="lub_p")
    anti_price = st.number_input(t["anti_price"], step=0.1, format="%.2f", key="anti_p")
    salt_price = st.number_input(t["salt_price"], step=0.05, format="%.2f", key="salt_p")
    
    st.subheader(t["fabric_header"])
    fiber_price = st.number_input(t["fiber_price"].format(curr=curr), step=0.1, format="%.2f", key="fiber_p")
    
    labor_price = st.number_input(t["labor_price"].format(curr=curr), step=0.1, format="%.2f", key="labor")
    waste_price = st.number_input(t["waste_price"].format(curr=curr), format="%.5f", key="waste_p")
    co2_factor = st.number_input(t["co2_factor"], value=0.202, step=0.001, key="co2")
    
    current_ports_dm = st.session_state.get("ports_dm", 1)
    
    base_investment = st.number_input(t["inv_price"].format(curr=curr), step=5000.0, format="%.0f", key="inv")
    
    investment = base_investment * current_ports_dm
    
    if current_ports_dm > 1:
        st.info(t["total_inv_info"].format(ports=current_ports_dm, inv=investment, curr=curr))

# ====================== PRODUCTION PARAMETERS ======================
st.subheader(t["prod_params_header"])
col_ex, col_dm, col_shared = st.columns([2, 2, 2])

with col_ex:
    st.subheader(t["exhaust_header"])
    batch_ex = st.number_input(t["batch_ex"], value=500, key="batch_ex")
    ports_ex = st.number_input(t["ports_ex"], value=4, key="ports_ex")
    liq_ex = st.number_input(t["liq_ex"], value=5.0, key="liq_ex")
    
    batches_per_day_per_machine = st.number_input(t["batches_per_day_ex"], value=3.0, step=1.0, key="batches_per_machine")
    batches_per_day_ex = ports_ex * batches_per_day_per_machine
    
    st.info(t["total_batches_day_info"].format(batches=batches_per_day_ex, per_machine=batches_per_day_per_machine, ports=ports_ex))
    
    waste_ex = batch_ex * liq_ex
    total_waste_daily = waste_ex * batches_per_day_ex
    st.info(t["waste_machine_info"].format(waste=waste_ex))
    st.info(t["total_daily_waste_info"].format(waste=total_waste_daily))

    fiber_loss_ex = st.number_input(t["fiber_loss_ex"], value=2.0, step=0.1, key="fl_ex") / 100
with col_dm:
    st.subheader(t["dm_header"])
    batch_dm = st.number_input(t["batch_dm"], value=500, max_value=500, step=10, key="batch_dm")
    liq_dm = st.number_input(t["liq_dm"], value=1.3, key="liq_dm")
    waste_dm = st.number_input(t["waste_dm"], value=50, key="waste_dm")
    batches_per_day_dm = st.number_input(t["bpd_dm"], value=12.00, step=0.25, key="bpd_dm")
    ports_dm = st.number_input(t["ports_dm"], value=1, key="ports_dm")
    changeover_min_dm = st.number_input(t["ch_dm"], value=30, step=1, key="ch_dm")
    fiber_loss_dm = st.number_input(t["fl_dm"], value=0.3, step=0.1, key="fl_dm") / 100

with col_shared:
    st.subheader(t["shared_header"])
    fabric_width = st.number_input(t["width"], value=2.2, key="width")
    gsm = st.number_input(t["gsm"], value=0.2, key="gsm")
    days_year = st.number_input(t["days"], value=320, key="days")
    hours_day = st.number_input(t["hours_day"], value=18.0, step=1.0, key="hours_day")

# ====================== PRODUCTION VOLUME SUMMARY ======================
st.subheader(t["vol_summary_header"])

ex_annual_vol = batch_ex * batches_per_day_ex * days_year
dm_annual_vol = batch_dm * batches_per_day_dm * days_year
dm_daily_vol = batch_dm * batches_per_day_dm

max_daily_capacity_dm = 8000 * ports_dm
max_annual_capacity_dm = max_daily_capacity_dm * days_year

extra_daily_capacity = max_daily_capacity_dm - dm_daily_vol
extra_annual_capacity = max_annual_capacity_dm - dm_annual_vol

if ex_annual_vol != dm_annual_vol:
    st.warning(t["vol_mismatch_warn"].format(ex=ex_annual_vol, dm=dm_annual_vol))

if dm_daily_vol > max_daily_capacity_dm:
    st.error(t["vol_exceeded_err"].format(max_vol=max_daily_capacity_dm, ports=ports_dm))

p1, p2, p3, p4 = st.columns(4)

total_batches_ex = batches_per_day_ex * days_year
total_batches_dm = batches_per_day_dm * days_year

if total_batches_ex > 0:
    pct_diff_batches = ((total_batches_dm - total_batches_ex) / total_batches_ex) * 100
    pct_diff_vol = ((dm_annual_vol - ex_annual_vol) / ex_annual_vol) * 100 if ex_annual_vol > 0 else 0.0
else:
    pct_diff_batches = 0.0
    pct_diff_vol = 0.0

with p1:
    ex_annual_text = f"{ex_annual_vol:,.0f}".replace(",", " ")
    st.metric(t["metric_trad_ex"], f"{ex_annual_text} kg/yr")
    ex_daily_text = f"{batch_ex * batches_per_day_ex:,.0f}".replace(",", " ")
    ex_batches_text = f"{total_batches_ex:,.0f}".replace(",", " ")
    st.caption(f"{ex_daily_text} kg/d | {ex_batches_text} batches/yr")

with p2:
    dm_annual_text = f"{dm_annual_vol:,.0f}".replace(",", " ")
    st.metric(
        t["metric_dm"], 
        f"{dm_annual_text} kg/yr", 
        delta=f"{pct_diff_vol:.1f}% vs Exhaust"
    )
    dm_daily_text = f"{dm_daily_vol:,.0f}".replace(",", " ")
    dm_batches_text = f"{total_batches_dm:,.0f}".replace(",", " ")
    st.caption(f"{dm_daily_text} kg/d | {dm_batches_text} batches/yr")

with p3:
    st.metric(
        t["metric_flex"], 
        f"{pct_diff_batches:.1f}%", 
        delta=f"{pct_diff_batches:.1f}%"
    )
    st.caption(f"{total_batches_dm:,.0f} vs {total_batches_ex:,.0f} total batches/yr")

if dm_annual_vol > 0:
    pct_extra_cap = (extra_annual_capacity / dm_annual_vol) * 100
else:
    pct_extra_cap = 0.0

with p4:
    extra_annual_text = f"{extra_annual_capacity:,.0f}".replace(",", " ")
    extra_daily_text = f"{extra_daily_capacity:,.0f}".replace(",", " ")
    max_daily_text = f"{max_daily_capacity_dm:,.0f}".replace(",", " ")
    
    st.metric(
        t["metric_extra_cap"], 
        f"+{extra_annual_text} kg/yr", 
        delta=f"+{pct_extra_cap:.1f}% free cap"
    )
    st.caption(f"+{extra_daily_text} kg/d | Max {max_daily_text} kg/d")

# ====================== ENERGY ======================
st.subheader(t["energy_header"])
en1, en2 = st.columns(2)
with en1:
    st.markdown(t["metric_trad_ex"])
    en_op_ex = st.number_input(t["machine_op"], value=0.11, key="enop_ex")
    en_steam_ex = st.number_input(t["steam"], value=0.4, key="ensteam_ex")
    en_wwt_ex = st.number_input(t["wwt"], value=0.005, key="enwwt_ex")
    en_dry_ex = st.number_input(t["drying"], value=0.0, key="endry_ex")
with en2:
    st.markdown(t["metric_dm"])
    en_op_dm = st.number_input(t["machine_op"], value=0.028, key="enop_dm")
    en_steam_dm = st.number_input(t["steam"], value=0.0, key="ensteam_dm")
    en_wwt_dm = st.number_input(t["wwt"], value=0.005, key="enwwt_dm")
    en_dry_dm = st.number_input(t["drying"], value=0.4, key="endry_dm")

# ====================== RECIPE ======================
st.subheader(t["recipe_header"])
r1, r2 = st.columns(2)

with r1:
    st.markdown(t["metric_trad_ex"])
    dye_a_ex_owf = st.number_input("Dye A (%) OWF", value=7.125, step=0.01, key="da_ex") / 100
    wetting_ex = st.number_input(t["wetting_g_l"], value=2.0, key="wet_ex")
    soda_ex = st.number_input(t["soda_g_l"], value=5.0, key="soda_ex")
    caustic_ex = st.number_input(t["naoh_g_l"], value=1.5, key="cau_ex")
    seq_ex = st.number_input(t["seq_g_l"], value=1.0, key="seq_ex")
    lev_ex = st.number_input(t["lev_g_l"], value=2.0, key="lev_ex")
    lub_ex = st.number_input(t["lub_g_l"], value=2.0, key="lub_ex")
    anti_ex = st.number_input(t["anti_g_l"], value=0.5, key="anti_ex")
    salt_ex = st.number_input(t["salt_g_l"], value=80.0, key="salt_ex")

    total_water_ex_batch = batch_ex * liq_ex
    dye_ex_batch_kg = batch_ex * dye_a_ex_owf
    wetting_ex_batch_kg = (total_water_ex_batch * wetting_ex) / 1000
    soda_ex_batch_kg = (total_water_ex_batch * soda_ex) / 1000
    caustic_ex_batch_kg = (total_water_ex_batch * caustic_ex) / 1000
    salt_ex_batch_kg = (total_water_ex_batch * salt_ex) / 1000

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-top: 15px; border: 1px solid #b6e0fe;">
        <strong>📋 Exhaust Bath Summary:</strong><br>
        • Total water per batch: <b>{total_water_ex_batch:,.0f} L</b> (1:{liq_ex})<br>
        • Dye A: <b>{dye_a_ex_owf*100:.3f}% OWF</b> ({dye_ex_batch_kg:.2f} kg)<br>
        • {t["cat_wetting"]}: <b>{wetting_ex:.1f} g/L</b> ({wetting_ex_batch_kg:.2f} kg) | {t["cat_soda"]}: <b>{soda_ex:.1f} g/L</b> ({soda_ex_batch_kg:.2f} kg)<br>
        • NAOH: <b>{caustic_ex:.1f} g/L</b> ({caustic_ex_batch_kg:.2f} kg) | {t["cat_salt"]}: <b>{salt_ex:.1f} g/L</b> ({salt_ex_batch_kg:.2f} kg)
    </div>
    """, unsafe_allow_html=True)

with r2:
    st.markdown(t["metric_dm"])
    
    with st.expander(t["dye_red_guide"]):
        st.markdown(t["dye_red_text"])
        
    dye_reduction_pct = st.number_input(t["dye_red_input"], value=10.0, step=0.1, key="dye_red")
    dye_a_dm_owf = dye_a_ex_owf * (1 - dye_reduction_pct / 100)
    dye_a_dm_gl = (dye_a_dm_owf * 1000) / liq_dm if liq_dm > 0 else 0
        
    wetting_dm = st.number_input(t["wetting_g_l"], value=1.0, key="wet_dm")
    soda_dm = st.number_input(t["soda_g_l"], value=16.0, key="soda_dm")
    caustic_dm = st.number_input(t["naoh_g_l"], value=5.0, key="cau_dm")
    seq_dm = st.number_input(t["seq_g_l"], value=0.0, key="seq_dm")
    lev_dm = st.number_input(t["lev_g_l"], value=1.0, key="lev_dm")
    lub_dm = st.number_input(t["lub_g_l"], value=0.0, key="lub_dm")
    anti_dm = st.number_input(t["anti_g_l"], value=0.0, key="anti_dm")
    salt_dm = st.number_input(t["salt_g_l"], value=0.0, key="salt_dm")

    total_water_dm_batch = batch_dm * liq_dm
    dye_dm_batch_kg = batch_dm * dye_a_dm_owf
    wetting_dm_batch_kg = (total_water_dm_batch * wetting_dm) / 1000
    soda_dm_batch_kg = (total_water_dm_batch * soda_dm) / 1000
    caustic_dm_batch_kg = (total_water_dm_batch * caustic_dm) / 1000

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-top: 15px; border: 1px solid #b6e0fe;">
        <strong>📋 Dye-max Bath Summary (Spray Pickup):</strong><br>
        • Spray pickup / Liquid: <b>{liq_dm:.2f} L/kg</b> ({liq_dm*100:.0f}%) — Total: <b>{total_water_dm_batch:,.1f} L</b><br>
        • Dye A: <b>{dye_a_dm_owf*100:.3f}% OWF</b> (Conc: <b>{dye_a_dm_gl:.1f} g/L</b> | {dye_dm_batch_kg:.2f} kg)<br>
        • {t["cat_wetting"]}: <b>{wetting_dm:.1f} g/L</b> ({wetting_dm_batch_kg:.2f} kg) | {t["cat_soda"]}: <b>{soda_dm:.1f} g/L</b> ({soda_dm_batch_kg:.2f} kg)<br>
        • NAOH: <b>{caustic_dm:.1f} g/L</b> ({caustic_dm_batch_kg:.2f} kg)
    </div>
    """, unsafe_allow_html=True)

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

chem_kg_ex = sum([calc_chem(annual_ex, liq_ex, v) for v in [wetting_ex, soda_ex, caustic_ex, seq_ex, lev_ex, lub_ex, anti_ex, salt_ex]])
chem_kg_dm = sum([calc_chem(annual_dm, liq_dm, v) for v in [wetting_dm, soda_dm, caustic_dm, seq_dm, lev_dm, lub_dm, anti_dm, salt_dm]])
chem_sav_kg_total = chem_kg_ex - chem_kg_dm

dye_sav = (dye_ex - dye_dm) * dye_price
water_sav = (water_ex - water_dm) * water_price
chem_sav = chem_ex - chem_dm
energy_sav = energy_sav_kwh * elec_price
fiber_sav = (fiber_loss_kg_ex - fiber_loss_kg_dm) * fiber_price
waste_sav = (waste_ex * batches_ex - waste_dm * batches_dm) * waste_price

total_savings = dye_sav + water_sav + chem_sav + energy_sav + fiber_sav + waste_sav
payback_months = (investment / total_savings * 12) if total_savings > 0 else 0
co2_savings = energy_sav_kwh * co2_factor / 1000

# ====================== SAVINGS OVERVIEW ======================
st.subheader(t["savings_overview_header"])
c1, c2, c3, c4 = st.columns(4)

annual_savings_text = f"{curr} {total_savings:,.0f}".replace(",", " ")
c1.metric(t["annual_savings_metric"].format(curr=curr), annual_savings_text)

payback_text = f"{payback_months:.1f}".replace(".", ",")
c2.metric(t["payback_metric"], f"{payback_text} months")

dye_savings_text = f"{dye_ex - dye_dm:,.0f}".replace(",", " ")
c3.metric(t["dye_savings_metric"], f"{dye_savings_text} kg/yr")

chem_savings_text = f"{chem_sav_kg_total:,.0f}".replace(",", " ")
c4.metric(t["chem_savings_metric"], f"{chem_savings_text} kg/yr")


st.subheader(t["env_header"])
e1, e2, e3 = st.columns(3)

water_text = f"{(water_ex - water_dm)/1000:,.0f}".replace(",", " ")
e1.metric(t["water_savings_metric"], f"{water_text} m³/yr")

co2_text = f"{co2_savings:.1f}".replace(".", ",")
e2.metric(t["co2_savings_metric"], f"{co2_text} tonnes/yr")

energy_text = f"{energy_sav_kwh:,.0f}".replace(",", " ")
e3.metric(t["energy_savings_metric"], f"{energy_text} kWh/yr")

# ====================== BREAKDOWN ======================
st.subheader(t["monetary_breakdown_header"].format(curr=curr))

breakdown = pd.DataFrame({
    "Category": [
        t["cat_dye"], t["cat_wetting"], t["cat_soda"], t["cat_naoh"], t["cat_seq"], 
        t["cat_lev"], t["cat_lub"], t["cat_anti"], t["cat_salt"], 
        t["cat_water"], t["cat_waste"], t["cat_energy"], t["cat_fiber"]
    ],
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

df = breakdown.copy()
df[f"Savings ({curr}/year)"] = df[f"Savings ({curr}/year)"].map(lambda x: f"{curr} {x:,.0f}".replace(",", " "))
st.table(df)

# ====================== TOTAL COST PER KG ======================
st.subheader(t["total_cost_kg_header"])
annual_kg = annual_ex

total_cost_ex = (
    (dye_ex * dye_price) + 
    chem_ex +
    (water_ex * water_price) +
    (waste_ex * batches_ex * waste_price) +
    (energy_total_ex * elec_price) +
    (batches_ex * 30 / 60 * labor_price) +      
    (fiber_loss_kg_ex * fiber_price)            
)

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

cost_ex_text = f"{cost_per_kg_ex:,.2f}".replace(",", " ").replace(".", ",")
cost_dm_text = f"{cost_per_kg_dm:,.2f}".replace(",", " ").replace(".", ",")
savings_kg_text = f"{savings_per_kg:,.2f}".replace(",", " ").replace(".", ",")
pct_text = f"{percentage_savings:.1f}".replace(".", ",")

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric(t["metric_trad_ex"], f"{curr} {cost_ex_text} / kg")

with col_c2:
    st.metric(
        label=t["metric_dm"], 
        value=f"{curr} {cost_dm_text} / kg",
        delta=f"↓ {curr} {savings_kg_text} / kg ({pct_text}%)"
    )

st.caption(t["cost_caption"])

# ====================== GRAPHS ======================
st.markdown(f"### {t['visual_overview_header']}")

fig1 = go.Figure(go.Bar(
    y=breakdown["Category"],
    x=breakdown[f"Savings ({curr}/year)"],
    orientation='h',
    marker_color='#00B0FF'
))
fig1.update_layout(
    title=t["monetary_breakdown_header"].format(curr=curr),
    height=520,
    xaxis_title=f"{curr} Savings",
    yaxis={'categoryorder':'total ascending'},
    margin=dict(l=250)
)
st.plotly_chart(fig1, use_container_width=True)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="Traditional Exhaust",
    x=[t["total_cost_kg_header"]],
    y=[cost_per_kg_ex],
    marker_color="#EF4444"
))
fig2.add_trace(go.Bar(
    name="Imogo Dye-max",
    x=[t["total_cost_kg_header"]],
    y=[cost_per_kg_dm],
    marker_color="#10B981"
))
fig2.update_layout(
    title=t["total_cost_kg_header"],
    height=400,
    barmode='group',
    bargroupgap=0.15,
    yaxis_title=f"{curr} / kg",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig2, use_container_width=True)

# ====================== REPORT GENERATION ======================
st.subheader(t["report_gen_header"])

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

customer_line = f"<p style='text-align:center; font-size:1.2em; color:#1e3a8a; margin-top:-10px;'><strong>{t['prepared_for']}</strong> {customer_name}</p>" if customer_name else ""

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
    <h1>{t["title"]}</h1>
    {customer_line}
    <p style="text-align:center; color:#64748b;"><strong>{t["generated_label"]}</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        
    <div class="metric">
        <h2>{t["key_results"]}</h2>
        <p style="font-size:1.5em;"><strong>{t["annual_savings_label"]} {pdf_savings_text}</strong></p>
        <p><strong>{t["payback_period_label"]} {pdf_payback_text}</strong></p>
        <p><strong>{t["investment_cost_label"]} {pdf_investment_text}</strong></p>
    </div>

    <h2>{t["prod_summary_label"]}</h2>
    <p><strong>Exhaust:</strong> {pdf_annual_ex} kg/year</p>
    <p><strong>Imogo Dye-max:</strong> {pdf_annual_dm} kg/year</p>
    <p><strong>{t['metric_extra_cap']}:</strong> +{extra_annual_capacity:,.0f} kg/year (+{extra_daily_capacity:,.0f} kg/day)</p>

    <h2>{t["physical_savings_label"]}</h2>
    <p>{t["cat_dye"]}: <strong>{pdf_dye_sav_kg} kg/year</strong></p>
    <p>Chemistry: <strong>{pdf_chem_sav_kg} kg/year</strong></p>
    <p>{t["cat_water"]}: <strong>{pdf_water_sav_m3} m³/year</strong></p>
    <p>{t["cat_energy"]}: <strong>{pdf_energy_sav_kwh} kWh/year</strong></p>
    <p>CO₂: <strong>{pdf_co2_sav_ton} tonnes/year</strong></p>

    <h2>{t["monetary_breakdown_header"].format(curr=curr)}</h2>
    {df.to_html(index=False, classes='table')}
    
    <h2>{t["process_recipe_label"]}</h2>
    <table>
        <tr>
            <th style="width: 34%;">Parameter</th>
            <th style="width: 33%;">Traditional Exhaust</th>
            <th style="width: 33%;">Imogo Dye-Max</th>
        </tr>
        <tr><td colspan="3" class="section-header">{t["machine_process_params"]}</td></tr>
        <tr><td>{t["batch_ex"]}</td><td>{batch_ex} kg</td><td>{batch_dm} kg</td></tr>
        <tr><td>Batches / Day</td><td>{batches_per_day_ex} batches</td><td>{batches_per_day_dm} batches</td></tr>
        <tr><td>{t["ports_ex"]}</td><td>{ports_ex}</td><td>-</td></tr>
        <tr><td>{t["ch_dm"]}</td><td>-</td><td>{changeover_min_dm} min</td></tr>
        <tr><td>Liquor Ratio</td><td>1:{liq_ex}</td><td>{liq_dm} L/kg</td></tr>
        <tr><td>Waste per Changeover</td><td>{waste_ex:,.0f} L</td><td>{waste_dm} L</td></tr>
        <tr><td>{t["fl_dm"]}</td><td>{fiber_loss_ex*100:.1f}%</td><td>{fiber_loss_dm*100:.1f}%</td></tr>
        
        <tr><td colspan="3" class="section-header">{t["chemistry_recipe_label"]}</td></tr>
        <tr><td>Dye OWF</td><td>{dye_ex_pct_str}</td><td>{dye_dm_pct_str} (Red: {dye_reduction_pct:.1f}%)</td></tr>
        <tr><td>{t["cat_wetting"]}</td><td>{wetting_ex} g/L</td><td>{wetting_dm} g/L</td></tr>
        <tr><td>{t["cat_soda"]}</td><td>{soda_ex} g/L</td><td>{soda_dm} g/L</td></tr>
        <tr><td>{t["cat_naoh"]}</td><td>{caustic_ex} g/L</td><td>{caustic_dm} g/L</td></tr>
        <tr><td>{t["cat_seq"]}</td><td>{seq_ex} g/L</td><td>{seq_dm} g/L</td></tr>
        <tr><td>{t["cat_lev"]}</td><td>{lev_ex} g/L</td><td>{lev_dm} g/L</td></tr>
        <tr><td>{t["cat_lub"]}</td><td>{lub_ex} g/L</td><td>{lub_dm} g/L</td></tr>
        <tr><td>{t["cat_anti"]}</td><td>{anti_ex} g/L</td><td>{anti_dm} g/L</td></tr>
        <tr><td>{t["cat_salt"]}</td><td>{salt_ex} g/L</td><td>{salt_dm} g/L</td></tr>
    </table>

    <h2>{t["general_params_costs"]}</h2>
    <table>
        <tr>
            <th style="width: 50%;">Parameter</th>
            <th style="width: 50%;">Value</th>
        </tr>
        <tr><td colspan="2" class="section-header">{t["general_production"]}</td></tr>
        <tr><td>{t["days"]}</td><td>{days_year} days</td></tr>
        <tr><td>{t["hours_day"]}</td><td>{hours_day} h</td></tr>
        <tr><td>{t["width"]} & {t["gsm"]}</td><td>{fabric_width} m / {gsm} kg/m²</td></tr>
        
        <tr><td colspan="2" class="section-header">{t["costs_unit_rates"]}</td></tr>
        <tr><td>{t["elec_label"].format(curr=curr)}</td><td>{elec_price:.2f} {curr}/kWh</td></tr>
        <tr><td>{t["water_label"].format(curr=curr)}</td><td>{water_price:.5f} {curr}/L ({water_price_m3:.2f} {curr}/m³)</td></tr>
        <tr><td>{t["dye_label"].format(curr=curr)}</td><td>{dye_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["wetting_price"]} Price</td><td>{wetting_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["soda_price"]} Price</td><td>{soda_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["caustic_price"]} Price</td><td>{caustic_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["seq_price"]} Price</td><td>{seq_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["lev_price"]} Price</td><td>{lev_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["lub_price"]} Price</td><td>{lub_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["anti_price"]} Price</td><td>{anti_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["salt_price"]} Price</td><td>{salt_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["fiber_price"].format(curr=curr)}</td><td>{fiber_price:.2f} {curr}/kg</td></tr>
        <tr><td>{t["labor_price"].format(curr=curr)}</td><td>{labor_price:.2f} {curr}/man-hour</td></tr>
        <tr><td>{t["waste_price"].format(curr=curr)}</td><td>{waste_price:.5f} {curr}/L</td></tr>
        <tr><td>{t["co2_factor"]}</td><td>{co2_factor:.3f} kg/kWh</td></tr>
    </table>
</body>
</html>
"""

st.download_button("Download Report (HTML)", data=html_report, file_name="imogo_roi_report.html", mime="text/html")
