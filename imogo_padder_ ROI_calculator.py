import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from translations_padder import LANGUAGES

# ====================== KONFIGURATION & FUNKTIONER ======================
# set_page_config MÅSTE vara det allra första Streamlit-anropet
st.set_page_config(page_title="Imogo Dye-max ROI Calculator", layout="wide", page_icon="💰")

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

# ====================== SPRÅKHANTERING ======================
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

def t(key):
    return LANGUAGES.get(st.session_state.lang, {}).get(key, key)

def format_num(value):
    return "{:,.0f}".format(value).replace(",", " ")

# ====================== INITIALISERING ======================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.local_currency = "EUR"
    st.session_state.currency_rate = 1.0
    st.session_state.prev_rate = 1.0
    st.session_state.ui_elec = 0.15
    st.session_state.ui_water = 0.0001
    st.session_state.ui_dye = 6.0
    st.session_state.ui_chem_a = 0.8
    st.session_state.ui_chem_b = 0.35
    st.session_state.ui_chem_c = 0.25
    st.session_state.ui_waste = 0.002
    st.session_state.ui_labor = 2.0
    st.session_state.ui_inv = 550000.0
    st.session_state.ui_price_a = 2.8
    st.session_state.ui_price_b = 1.8
    st.session_state.ui_price_waste = 0.8
    st.session_state.ui_co2 = 0.20

# ====================== SIDEBAR ======================
with st.sidebar:
    # Hämtar språkkoder (t.ex. 'EN', 'PT-BR') direkt från translations_padder.py
    available_languages = list(LANGUAGES.keys())
    current_index = available_languages.index(st.session_state.lang) if st.session_state.lang in available_languages else 0
    
    st.session_state.lang = st.selectbox(
        "🌐 Language", 
        options=available_languages,
        index=current_index
    )
    st.markdown("---")    
    customer_name = st.text_input(t("customer_name"), value="", key="customer_name_input")
    curr = st.text_input(t("currency"), value="EUR", key="curr_input").strip().upper()
    current_rate = st.session_state.get("conv_key", 1.00)
    conv = st.number_input(f"{t('exchange_rate')} (1 EUR = {current_rate:.2f} {curr})", value=1.00, step=0.10, format="%.2f", key="conv_key")
    
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

    st.header(f"{t('costs')} ({curr})")
    st.number_input(f"{t('electricity')} ({curr}/kWh)", key="ui_elec", format="%.3f")
    st.number_input(f"{t('water')} ({curr}/L)", key="ui_water", format="%.4f")
    st.number_input(f"{t('dye_stuff')} ({curr}/kg)", key="ui_dye")
    st.number_input(f"{t('wetting_agent')} ({curr}/kg)", key="ui_chem_a")
    st.number_input(f"{t('soda_ash')} ({curr}/kg)", key="ui_chem_b")
    st.number_input(f"{t('naoh')} ({curr}/kg)", key="ui_chem_c")
    st.number_input(f"{t('waste_handling')} ({curr}/L)", key="ui_waste", format="%.4f")
    st.number_input(f"{t('labor')} ({curr}/man-hour)", key="ui_labor")
    st.number_input("CO₂ kg/kWh", key="ui_co2", format="%.2f", step=0.01)
    st.number_input(f"{t('investment_cost')} ({curr})", key="ui_inv")
    
    st.subheader(f"{t('fabric_prices')} ({curr}/kg)")
    st.number_input(t("price_a_quality"), key="ui_price_a")
    st.number_input(t("price_b_quality"), key="ui_price_b")
    st.number_input(t("price_waste_fabric"), key="ui_price_waste")

st.title(t("app_title"))

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
    fabric_width = st.number_input(t("fabric_width"), value=2.2, step=0.1, key="fabric_width")
    fabric_gsm = st.number_input(t("fabric_gsm"), value=0.18, step=0.01, key="fabric_gsm")
    working_hours_day = st.number_input(t("working_hours_day"), value=18.0, step=0.5, key="working_hours_day")
    prod_speed = st.number_input(t("prod_speed"), value=25.0, step=0.1, key="prod_speed")

with col_s2:
    rolls_day = st.number_input(t("batches_day"), value=14.0, step=1.0, key="rolls_day")
    days_year = st.number_input(t("days_year"), value=320, step=1, key="days_year")
    changeovers_day = st.number_input(t("changeovers_day"), value=10, step=1, key="changeovers_day")

est_changeover_time = 20 
eff_hours_day = working_hours_day - (changeovers_day * est_changeover_time / 60.0)

meters_per_roll = (prod_speed * 60 * eff_hours_day) / rolls_day if rolls_day > 0 else 0
weight_per_roll = meters_per_roll * fabric_width * fabric_gsm

top_banner_placeholder = st.empty()
prod_summary_placeholder = st.container()

# ====================== MACHINE SPECIFIC ======================
col_p, col_i = st.columns(2)
with col_p:
    st.subheader(t("trad_padder"))
    p_ch = st.number_input(t("changeover_time"), value=30, key="p_ch")
    
    p_pickup = st.number_input(t("pickup"), value=100, step=1, format="%d", key="p_pickup")
    p_disp = p_pickup / 100.0 
    
    p_dye = st.number_input(t("dye_conc"), value=4.0, key="p_dye")
    p_dye_conc_g_l = (p_dye * 10) / p_disp if p_disp > 0 else 0
    
    val_p_a = st.session_state.get("p_a", 3.0)
    val_p_b = st.session_state.get("p_b", 2.0)
    val_p_c = st.session_state.get("p_c", 1.5)
    
    p_a_conc_g_l = val_p_a / p_disp if p_disp > 0 else 0
    p_b_conc_g_l = val_p_b / p_disp if p_disp > 0 else 0
    p_c_conc_g_l = val_p_c / p_disp if p_disp > 0 else 0

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-bottom: 15px; border: 1px solid #b6e0fe;">
        <strong>{t('actual_bath_padder')}</strong><br>
        • {t('dye')} <b>{p_dye_conc_g_l:.1f} g/L</b><br>
        • {t('wetting_agent')}: <b>{p_a_conc_g_l:.1f} g/L</b><br>
        • {t('soda_ash')}: <b>{p_b_conc_g_l:.1f} g/L</b><br>
        • {t('naoh')}: <b>{p_c_conc_g_l:.1f} g/L</b>
    </div>
    """, unsafe_allow_html=True)

    p_a = st.number_input(t("wetting_agent_100"), value=3.0, key="p_a")
    p_b = st.number_input(t("soda_ash_100"), value=2.0, key="p_b")
    p_c = st.number_input(t("naoh_100"), value=1.5, key="p_c")

    p_w = st.number_input(t("waste_water_ch"), value=70, key="p_w")
    p_startup = st.number_input(t("startup_waste"), value=50.0, key="p_startup")
    p_en = st.number_input(t("energy"), value=0.05, format="%.4f", key="p_en")
    p_bq = st.number_input(t("b_quality_pct"), value=4.0, key="p_bq")
    p_wf = st.number_input(t("waste_fabric_pct"), value=1.0, key="p_wf")

with col_i:
    st.subheader(t("imogo_dyemax"))
    i_ch = st.number_input(t("changeover_time"), value=20, key="i_ch", help="i_ch")
    
    i_pickup = st.number_input(t("pickup"), value=100, step=1, format="%d", key="i_pickup", help="i_pickup")
    i_disp = i_pickup / 100.0
    
    i_dye = st.number_input(t("dye_conc"), value=4.0, key="i_dye", help="i_dye")
    i_dye_conc_g_l = (i_dye * 10) / i_disp if i_disp > 0 else 0
    
    val_i_a = st.session_state.get("i_a", 3.0)
    val_i_b = st.session_state.get("i_b", 2.0)
    val_i_c = st.session_state.get("i_c", 1.5)
    
    i_a_conc_g_l = val_i_a / i_disp if i_disp > 0 else 0
    i_b_conc_g_l = val_i_b / i_disp if i_disp > 0 else 0
    i_c_conc_g_l = val_i_c / i_disp if i_disp > 0 else 0

    st.markdown(f"""
    <div style="background-color: #e8f4fd; padding: 12px; border-radius: 8px; font-size: 0.95em; color: #1e3a8a; margin-bottom: 15px; border: 1px solid #b6e0fe;">
        <strong>{t('actual_bath_imogo')}</strong><br>
        • {t('dye')} <b>{i_dye_conc_g_l:.1f} g/L</b><br>
        • {t('wetting_agent')}: <b>{i_a_conc_g_l:.1f} g/L</b><br>
        • {t('soda_ash')}: <b>{i_b_conc_g_l:.1f} g/L</b><br>
        • {t('naoh')}: <b>{i_c_conc_g_l:.1f} g/L</b>
    </div>
    """, unsafe_allow_html=True)

    i_a = st.number_input(t("wetting_agent_100"), value=3.0, key="i_a", help="i_a")
    i_b = st.number_input(t("soda_ash_100"), value=2.0, key="i_b", help="i_b")
    i_c = st.number_input(t("naoh_100"), value=1.5, key="i_c", help="i_c")

    i_w = st.number_input(t("waste_water_ch"), value=15, key="i_w", help="i_w")
    i_startup = st.number_input(t("startup_waste"), value=7.0, key="i_startup", help="i_startup")
    i_en = st.number_input(t("energy"), value=0.035, format="%.4f", key="i_en", help="i_en")
    i_bq = st.number_input(t("b_quality_pct"), value=3.0, key="i_bq", help="i_bq")
    i_wf = st.number_input(t("waste_fabric_pct"), value=0.5, key="i_wf", help="i_wf")

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
        <strong>{t('fabric_length_roll')}</strong> {meters_per_roll:,.0f} m 
        <span style="margin: 0 15px; opacity: 0.5;">|</span> 
        <strong>{t('fabric_weight_roll')}</strong> {weight_per_roll:,.1f} kg
        <span style="margin: 0 15px; opacity: 0.5;">|</span> 
        <strong>{t('roll_wet_weight')}</strong> {i_roll_weight_wet:.1f} kg{warning}
    </div>
    """, unsafe_allow_html=True)
    
    with st.popover("ℹ️"):
        st.write(t("max_weight_warning"))

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
    st.subheader(t("prod_volume_summary"))
    col_sum1, col_sum2 = st.columns(2)

    with col_sum1:
        st.metric(f"**{t('trad_padder')[2:]}**", f"{format_num(base_annual_kg)} {t('kg_year')}")
        st.caption(f"**{format_num(p_daily_m)} {t('m_day')}** | **{format_num(p_daily_kg)} {t('kg_day')}** | **{prod_speed:.1f} m/min**")

    with col_sum2:
        st.metric(
            f"**{t('imogo_dyemax')[2:]}**", 
            f"{format_num(base_annual_kg)} {t('kg_year')}", 
            delta=f"↑ {format_num(extra_annual_kg)} {t('kg_year')} {t('extra_capacity')}"
        )
        st.caption(f"**{format_num(p_daily_m)} {t('m_day')}** | **{format_num(p_daily_kg)} {t('kg_day')}** | **{prod_speed:.1f} m/min**")
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
st.header(t("savings_overview"))

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("annual_savings"), f"{curr} {format_num(annual_savings)}")
col2.metric(t("payback_period"), f"{payback_months:.0f} {t('months')}")
col3.metric(t("dye_savings"), f"{format_num(total_dye_savings_kg)} {t('kg_year')}")
col4.metric(t("chem_savings"), f"{format_num(total_chem_savings_kg)} {t('kg_year')}")

st.write("") 

st.header(t("env_savings"))
col_env1, col_env2, col_env3 = st.columns(3)
col_env1.metric(t("water_savings"), f"{format_num(water_savings_m3)} m³/{t('kg_year').split('/')[1]}")
col_env2.metric(t("co2_savings"), f"{co2_savings_tonnes:.1f} tonnes/{t('kg_year').split('/')[1]}")
col_env3.metric(t("energy_savings"), f"{format_num(energy_savings_kwh)} kWh/{t('kg_year').split('/')[1]}")

st.markdown("---")
st.header(t("total_cost_kg"))

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric(t("trad_padder")[2:], f"{curr} {p_cost_per_kg:.2f} {t('per_kg')}")

with col_c2:
    cost_diff = p_cost_per_kg - i_cost_per_kg
    cost_diff_pct = (cost_diff / p_cost_per_kg) * 100 if p_cost_per_kg > 0 else 0
    delta_str = f"-{curr} {cost_diff:.2f} {t('per_kg')} ({cost_diff_pct:.1f}%)"
    st.metric(t("imogo_dyemax")[2:], f"{curr} {i_cost_per_kg:.2f} {t('per_kg')}", delta=delta_str, delta_color="inverse")

# ====================== DETALJERAD INFO ======================
st.markdown("---")
st.header(t("detailed_breakdown"))
breakdown_data = {
    t("category"): [t("dye_stuff"), t("chem_savings").replace(" Savings", ""), t("process_water"), t("energy"), t("waste_handling"), t("labor"), t("b_quality_reduction"), t("waste_fabric_reduction")],
    f"{t('savings')} ({curr})": [total_dye_savings, total_chem_savings, water_savings, energy_savings, waste_savings, labor_savings, b_quality_savings, waste_fabric_savings]
}
df_breakdown = pd.DataFrame(breakdown_data)
df_breakdown = df_breakdown.sort_values(by=f"{t('savings')} ({curr})", ascending=False)
st.dataframe(df_breakdown.style.format({f"{t('savings')} ({curr})": "{:,.0f}"}), use_container_width=True)

# ====================== VISUALISERING ENLIGT BILD ======================
st.markdown("---")

categories = [
    t("dye_stuff"), "Chem A", "Chem B", "Chem C", 
    t("process_water"), t("waste_handling"), t("energy"), 
    t("labor"), "B-Quality", "Waste Fabric"
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
    title=f"{t('yearly_savings_cat')} ({curr}/{t('kg_year').split('/')[1]})",
    xaxis_title=f"{curr} {t('savings')}",
    yaxis=dict(autorange="reversed"),  
    height=450
)
st.plotly_chart(fig_savings, use_container_width=True)

fig_cost = go.Figure(go.Bar(
    x=[t('trad_padder')[2:], t('imogo_dyemax')[2:]],
    y=[p_cost_per_kg, i_cost_per_kg],
    marker_color=['#ff5252', '#00c896']
))
fig_cost.update_layout(
    title=f"{t('total_cost_kg')} ({curr})",
    yaxis_title=f"{curr} {t('per_kg')}",
    height=400
)
st.plotly_chart(fig_cost, use_container_width=True)

# ====================== RAPPORTGENERERING ======================
def generate_html_report():
    html_content = f"""
    <html>
    <head>
        <title>{t('report_title')}</title>
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
        <div style="text-align: right; color: #666;">{t('date')} {datetime.now().strftime("%Y-%m-%d")}</div>
        <h1>{t('report_title')}</h1>
        <h3>{t('customer')} {customer_name if customer_name else t('not_specified')}</h3>
        
        <div class="summary-box">
            <h2>{t('financial_summary')}</h2>
            <p><strong>{t('total_annual_savings')}</strong> <span class="highlight">{format_num(annual_savings)} {curr}</span></p>
            <p><strong>{t('est_payback')}</strong> <span class="highlight">{payback_months:.1f} {t('months')}</span></p>
            <p><strong>{t('cost_kg_padder')}</strong> {curr} {p_cost_per_kg:.3f} {t('per_kg')}</p>
            <p><strong>{t('cost_kg_imogo')}</strong> {curr} {i_cost_per_kg:.3f} {t('per_kg')}</p>
        </div>

        <h2>{t('prod_volume_summary')}</h2>
        <p><strong>{t('daily_volume')}</strong> {format_num(p_daily_m)} {t('m_day')} ({format_num(p_daily_kg)} {t('kg_day')})</p>
        <p><strong>{t('total_base_volume')}</strong> {format_num(base_annual_kg)} {t('kg_year')}</p>
        <p><strong>{t('extra_annual_capacity')}</strong> <span class="highlight">+{format_num(extra_annual_kg)} {t('kg_year')}</span></p>

        <h2>{t('annual_env_savings')}</h2>
        <table>
            <tr><th>{t('resource')}</th><th>{t('savings')}</th></tr>
            <tr><td>{t('water').split(' ')[0]}</td><td>{format_num(water_savings_m3)} m³</td></tr>
            <tr><td>{t('energy').split(' ')[0]}</td><td>{format_num(energy_savings_kwh)} kWh</td></tr>
            <tr><td>CO2</td><td>{co2_savings_tonnes:.1f} tonnes</td></tr>
            <tr><td>{t('dye_stuff')}</td><td>{format_num(total_dye_savings_kg)} kg</td></tr>
            <tr><td>{t('chem_savings').replace(' Savings', '')}</td><td>{format_num(total_chem_savings_kg)} kg</td></tr>
        </table>

        <h2>{t('detailed_breakdown')}</h2>
        <table>
            <tr><th>{t('category')}</th><th>{t('savings')} ({curr})</th></tr>
            <tr><td>{t('dye_stuff')}</td><td>{format_num(total_dye_savings)}</td></tr>
            <tr><td>{t('chem_savings').replace(' Savings', '')}</td><td>{format_num(total_chem_savings)}</td></tr>
            <tr><td>{t('water').split(' ')[0]}</td><td>{format_num(water_savings)}</td></tr>
            <tr><td>{t('energy').split(' ')[0]}</td><td>{format_num(energy_savings)}</td></tr>
            <tr><td>{t('waste_handling')}</td><td>{format_num(waste_savings)}</td></tr>
            <tr><td>{t('labor')}</td><td>{format_num(labor_savings)}</td></tr>
            <tr><td>B-Quality Fabric</td><td>{format_num(b_quality_savings)}</td></tr>
            <tr><td>Waste Fabric</td><td>{format_num(waste_fabric_savings)}</td></tr>
        </table>

        <h2>{t('machine_parameters')}</h2>
        <table>
            <tr><th>{t('parameter')}</th><th>{t('trad_padder')[2:]}</th><th>{t('imogo_dyemax')[2:]}</th></tr>
            <tr><td>{t('changeover_time')}</td><td>{p_ch}</td><td>{i_ch}</td></tr>
            <tr><td>{t('dye_dispersion')}</td><td>{p_disp}</td><td>{i_disp}</td></tr>
            <tr><td>{t('waste_water_ch')}</td><td>{p_w}</td><td>{i_w}</td></tr>
            <tr><td>{t('startup_waste')}</td><td>{p_startup}</td><td>{i_startup}</td></tr>
            <tr><td>{t('energy')}</td><td>{p_en}</td><td>{i_en}</td></tr>
            <tr><td>{t('b_quality_pct')}</td><td>{p_bq}%</td><td>{i_bq}%</td></tr>
            <tr><td>{t('waste_fabric_pct')}</td><td>{p_wf}%</td><td>{i_wf}%</td></tr>
        </table>

        <div class="footer">
            {t('generated_by')}
        </div>
    </body>
    </html>
    """
    return html_content

st.markdown("---")
st.download_button(
    label=t("download_report"),
    data=generate_html_report(),
    file_name=f"imogo_roi_report_{customer_name.replace(' ', '_') if customer_name else 'customer'}.html",
    mime="text/html"
)
