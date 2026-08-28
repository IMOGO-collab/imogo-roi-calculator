import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from translations_Fmax import LANGUAGES

# ------------------------------------------------------------------------------
# PAGE CONFIGURATION (Måste vara första st-kommandot)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="F-Max ROI & Sustainability Calculator",
    page_icon="💰",
    layout="wide"
)

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

# ====================== SPRÅKHANTERING ======================
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

def t(key):
    return LANGUAGES.get(st.session_state.lang, {}).get(key, key)

# Helper function for formatting numbers with space as thousands separator
def fmt_num(val, decimals=0):
    if decimals == 0:
        return f"{int(round(val)):,}".replace(",", " ")
    else:
        return f"{val:,.{decimals}f}".replace(",", " ")

# ------------------------------------------------------------------------------
# CALCULATOR LOGIC
# ------------------------------------------------------------------------------
class FMaxCalculator:
    def __init__(self, inputs):
        self.inputs = inputs

    def calculate(self):
        # 1. Extract inputs
        fabric_width = self.inputs['fabric_width']
        fabric_weight_sqm = self.inputs['fabric_weight_sqm']
        speed = self.inputs['speed']
        hours_day = self.inputs['hours_day']
        days_year = self.inputs['days_year']
        changeovers_day = self.inputs['changeovers_day']
        drying_energy = self.inputs['drying_energy']
        
        padder_operating_power = self.inputs['padder_operating_power']
        fmax_operating_power = self.inputs['fmax_operating_power']
        
        padder_waste_changeover = self.inputs['padder_waste_changeover']
        fmax_waste_changeover = self.inputs['fmax_waste_changeover']
        
        padder_fabric_waste_m = self.inputs['padder_fabric_waste_m']
        fmax_fabric_waste_m = self.inputs['fmax_fabric_waste_m']

        padder_changeover_time = self.inputs['padder_changeover_time']
        fmax_changeover_time = self.inputs['fmax_changeover_time']
        
        cost_energy = self.inputs['cost_energy']
        cost_water = self.inputs['cost_water']
        cost_waste = self.inputs['cost_waste']
        cost_fabric_waste = self.inputs['cost_fabric_waste']
        cost_chem_a = self.inputs['cost_chem_a']
        cost_chem_b = self.inputs['cost_chem_b']
        cost_chem_c = self.inputs['cost_chem_c']

        # Weight per linear meter (kg/m)
        weight_per_linear_meter = fabric_width * fabric_weight_sqm

        # 1. Tider
        total_minutes_day = hours_day * 60.0
        changeover_min_day_padder = changeovers_day * padder_changeover_time
        changeover_min_day_fmax = changeovers_day * fmax_changeover_time

        prod_minutes_day_padder = max(0.0, total_minutes_day - changeover_min_day_padder)
        prod_minutes_day_fmax_theoretical = max(0.0, total_minutes_day - changeover_min_day_fmax)

        # 2. Beräkna Padderns volymer (Detta blir basen för ALLT)
        lm_day_padder = prod_minutes_day_padder * speed
        lm_year_padder = lm_day_padder * days_year
        weight_day_padder = lm_day_padder * weight_per_linear_meter
        weight_year_padder = weight_day_padder * days_year

        # 3. Beräkna F-max teoretiska volymer (Endast för att få fram "extra kapacitet")
        lm_day_fmax_theoretical = prod_minutes_day_fmax_theoretical * speed
        lm_year_fmax_theoretical = lm_day_fmax_theoretical * days_year
        weight_day_fmax_theoretical = lm_day_fmax_theoretical * weight_per_linear_meter
        weight_year_fmax_theoretical = weight_day_fmax_theoretical * days_year

        # 4. LÅS F-max officiella volymer till Padderns volym
        lm_day_fmax = lm_day_padder
        lm_year_fmax = lm_year_padder
        weight_day_fmax = weight_day_padder
        weight_year_fmax = weight_year_padder

        # 5. Beräkna den extra kapaciteten (skickas med för att visas som info under)
        extra_lm_day = lm_day_fmax_theoretical - lm_day_padder
        extra_lm = lm_year_fmax_theoretical - lm_year_padder
        extra_weight_day = weight_day_fmax_theoretical - weight_day_padder
        extra_weight = weight_year_fmax_theoretical - weight_year_padder

        # Pickups (%)
        pad_pickup = self.inputs['padder_softener_vol'] / 100.0
        fmax_pickup = self.inputs['fmax_softener_vol'] / 100.0

        # Drying & Operating energy
        energy_per_kg_padder = drying_energy * pad_pickup
        energy_per_kg_fmax = drying_energy * fmax_pickup

        drying_energy_year_padder = weight_year_padder * energy_per_kg_padder
        drying_energy_year_fmax = weight_year_padder * energy_per_kg_fmax

        # Operating energy (kW * total operating hours per year)
        operating_hours_year = hours_day * days_year
        operating_energy_year_padder = padder_operating_power * operating_hours_year
        operating_energy_year_fmax = fmax_operating_power * operating_hours_year

        # Total energy consumption
        energy_year_padder = drying_energy_year_padder + operating_energy_year_padder
        energy_year_fmax = drying_energy_year_fmax + operating_energy_year_fmax
        energy_savings_kwh = energy_year_padder - energy_year_fmax       

        # Water / Softener liquid consumption
        softener_day_padder_applied = weight_day_padder * pad_pickup
        softener_day_fmax_applied = weight_day_padder * fmax_pickup

        # Årligt vätskespill
        padder_waste_year_l = padder_waste_changeover * changeovers_day * days_year
        fmax_waste_year_l = fmax_waste_changeover * changeovers_day * days_year

        # Total årlig vätska (Applicerad + Spill)
        softener_year_padder = (softener_day_padder_applied * days_year) + padder_waste_year_l
        softener_year_fmax = (softener_day_fmax_applied * days_year) + fmax_waste_year_l
        
        water_savings_liters = softener_year_padder - softener_year_fmax
        water_savings_m3 = water_savings_liters / 1000.0

        # Chemical Savings
        chem_a_padder_year = softener_year_padder * (self.inputs['padder_chem_a_g_l'] / 1000.0)
        chem_a_fmax_year = softener_year_fmax * (self.inputs['fmax_chem_a_g_l'] / 1000.0)
        chem_a_savings_kg = chem_a_padder_year - chem_a_fmax_year

        chem_b_padder_year = softener_year_padder * (self.inputs['padder_chem_b_g_l'] / 1000.0)
        chem_b_fmax_year = softener_year_fmax * (self.inputs['fmax_chem_b_g_l'] / 1000.0)
        chem_b_savings_kg = chem_b_padder_year - chem_b_fmax_year

        chem_c_padder_year = softener_year_padder * (self.inputs['padder_chem_c_g_l'] / 1000.0)
        chem_c_fmax_year = softener_year_fmax * (self.inputs['fmax_chem_c_g_l'] / 1000.0)
        chem_c_savings_kg = chem_c_padder_year - chem_c_fmax_year

        total_chem_savings_kg = chem_a_savings_kg + chem_b_savings_kg + chem_c_savings_kg

        # Årligt tygspill (kg)
        padder_fabric_waste_year_kg = padder_fabric_waste_m * weight_per_linear_meter * changeovers_day * days_year
        fmax_fabric_waste_year_kg = fmax_fabric_waste_m * weight_per_linear_meter * changeovers_day * days_year

        # Besparingar i pengar
        savings_energy = energy_savings_kwh * cost_energy
        savings_water = water_savings_liters * cost_water
        savings_waste_handling = (padder_waste_year_l - fmax_waste_year_l) * cost_waste
        savings_fabric_waste = (padder_fabric_waste_year_kg - fmax_fabric_waste_year_kg) * cost_fabric_waste
        savings_chem_a = chem_a_savings_kg * cost_chem_a
        savings_chem_b = chem_b_savings_kg * cost_chem_b
        savings_chem_c = chem_c_savings_kg * cost_chem_c

        # Totalsumma av alla besparingar
        total_annual_savings = (
            savings_energy +
            savings_water +
            savings_waste_handling +
            savings_fabric_waste +
            savings_chem_a +
            savings_chem_b +
            savings_chem_c
        )
        
        # Dynamic CO2 Savings
        co2_factor = self.inputs.get('co2_factor', 0.202)
        co2_savings_tonnes = (energy_savings_kwh * co2_factor) / 1000.0

        # Payback Calculation
        investment = self.inputs['investment']
        if total_annual_savings > 0:
            payback_months = (investment / total_annual_savings) * 12.0
            payback_years = investment / total_annual_savings
        else:
            payback_months = 0.0
            payback_years = 0.0

        # --- COST PER KG FABRIC ---
        chem_a_padder = softener_year_padder * (self.inputs['padder_chem_a_g_l'] / 1000.0)
        chem_b_padder = softener_year_padder * (self.inputs['padder_chem_b_g_l'] / 1000.0)
        chem_c_padder = softener_year_padder * (self.inputs['padder_chem_c_g_l'] / 1000.0)

        cost_padder_year = (
            (energy_year_padder * self.inputs['cost_energy']) +
            (softener_year_padder * self.inputs['cost_water']) +
            (chem_a_padder * self.inputs['cost_chem_a']) +
            (chem_b_padder * self.inputs['cost_chem_b']) +
            (chem_c_padder * self.inputs['cost_chem_c'])
        )

        cost_fmax_year = cost_padder_year - total_annual_savings

        if weight_year_padder > 0:
            cost_per_kg_padder = cost_padder_year / weight_year_padder
            cost_per_kg_fmax = cost_fmax_year / weight_year_padder
        else:
            cost_per_kg_padder = 0.0
            cost_per_kg_fmax = 0.0

        cost_per_kg_savings = cost_per_kg_padder - cost_per_kg_fmax
        cost_per_kg_pct = (cost_per_kg_savings / cost_per_kg_padder * 100.0) if cost_per_kg_padder > 0 else 0.

        # Kapacitetsökning
        energy_ratio = (pad_pickup / fmax_pickup) if fmax_pickup > 0 else 1.0
        max_potential_speed = speed * energy_ratio
        speed_increase_percent = (energy_ratio - 1.0) * 100.0
        extra_volume_same_energy_kg = weight_year_padder * (energy_ratio - 1.0)
        extra_volume_same_energy_lm = lm_year_padder * (energy_ratio - 1.0)

        # Hämta inmatningar och optimeringskrav (för att passera vidare till output dict)
        wpu_ratio = (self.inputs['padder_softener_vol'] / self.inputs['fmax_softener_vol']) if self.inputs['fmax_softener_vol'] > 0 else 1.0
        req_fmax_chem_a = self.inputs['padder_chem_a_g_l'] * wpu_ratio
        req_fmax_chem_b = self.inputs['padder_chem_b_g_l'] * wpu_ratio
        req_fmax_chem_c = self.inputs['padder_chem_c_g_l'] * wpu_ratio

        return {
            'meters_day': lm_day_padder,
            'weight_day_padder': weight_day_padder,
            'weight_year_padder': weight_year_padder,
            'weight_per_linear_meter': weight_per_linear_meter,
            'energy_savings_kwh': energy_savings_kwh,
            'water_savings_m3': water_savings_m3,
            'savings_waste_handling': savings_waste_handling,
            'total_chem_savings_kg': total_chem_savings_kg,
            'co2_savings_tonnes': co2_savings_tonnes,
            'savings_energy': savings_energy,
            'savings_water': savings_water,
            'savings_chem_a': savings_chem_a,
            'savings_chem_b': savings_chem_b,
            'savings_chem_c': savings_chem_c,
            'total_annual_savings': total_annual_savings,
            'payback_months': payback_months,
            'payback_years': payback_years,
            'cost_per_kg_padder': cost_per_kg_padder,
            'cost_per_kg_fmax': cost_per_kg_fmax,
            'cost_per_kg_savings': cost_per_kg_savings,
            'cost_per_kg_pct': cost_per_kg_pct,
            'savings_fabric_waste': savings_fabric_waste,
            'lm_day_padder': lm_day_padder,
            'lm_year_padder': lm_year_padder,
            'weight_day_fmax': weight_day_fmax,
            'weight_year_fmax': weight_year_fmax,
            'lm_day_fmax': lm_day_fmax,
            'lm_year_fmax': lm_year_fmax,
            'extra_weight': extra_weight,
            'extra_lm': extra_lm,
            'energy_ratio': energy_ratio,
            'max_potential_speed': max_potential_speed,
            'speed_increase_percent': speed_increase_percent,
            'extra_volume_same_energy_kg': extra_volume_same_energy_kg,
            'extra_volume_same_energy_lm': extra_volume_same_energy_lm,
            'req_fmax_chem_a': req_fmax_chem_a,
            'req_fmax_chem_b': req_fmax_chem_b,
            'req_fmax_chem_c': req_fmax_chem_c,
        }

# ------------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ------------------------------------------------------------------------------
with st.sidebar:
    # --- SPRÅKVÄLJARE ---
    available_languages = list(LANGUAGES.keys())
    current_index = available_languages.index(st.session_state.lang) if st.session_state.lang in available_languages else 0
    
    st.session_state.lang = st.selectbox(
        "🌐 Language", 
        options=available_languages,
        index=current_index
    )
    st.markdown("---")

    st.header(t("currency_settings"))
    
    currency = st.text_input(t("currency"), value="EUR")
    currency_display = currency if currency else ""
    current_rate = st.session_state.get("conv_key", 1.00)

    conv = st.number_input(
        f"{t('exchange_rate')} (1 EUR = {current_rate:.2f} {currency_display})".strip(),
        value=1.00,
        step=0.10,
        format="%.2f",
        key="conv_key"
    )
    currency = currency_display
    exchange_rate = conv

    st.header(f"{t('costs')} ({currency})")
    cost_energy = st.number_input(f"{t('electricity')} ({currency}/kWh)", value=0.100 * exchange_rate, format="%.3f")
    cost_water = st.number_input(f"{t('water')} ({currency}/L)", value=0.0001 * exchange_rate, format="%.5f")
    cost_waste = st.number_input(f"{t('waste_handling')} ({currency}/L)", value=0.0020 * exchange_rate, format="%.4f")
    cost_chem_a = st.number_input(f"{t('chem_a')} ({currency}/kg)", value=2.00 * exchange_rate, format="%.2f")
    cost_chem_b = st.number_input(f"{t('chem_b')} ({currency}/kg)", value=2.00 * exchange_rate, format="%.2f")
    cost_chem_c = st.number_input(f"{t('chem_c')} ({currency}/kg)", value=5.00 * exchange_rate, format="%.2f")
    cost_fabric_waste = st.number_input(f"{t('fabric_waste_cost')} ({currency}/kg)", value=1.00 * exchange_rate, format="%.2f")
    
    co2_factor = st.number_input(
        t("co2_factor"),
        min_value=0.000,
        max_value=2.000,
        value=0.202,
        step=0.005,
        format="%.3f",
        help=t("co2_help")
    )

    investment = st.number_input(
        f"{t('investment_cost')} ({currency})", 
        value=float(int(235000 * exchange_rate)), 
        step=1000.0,
        format="%.0f"
    )

# ------------------------------------------------------------------------------
# MAIN PAGE INPUTS
# ------------------------------------------------------------------------------
st.title(t("app_title"))

st.header(t("gen_prod_data"))
col1, col2 = st.columns(2)

with col1:
    fabric_width = st.number_input(t("fabric_width"), value=3.20, step=0.10, format="%.2f")
    fabric_weight_sqm = st.number_input(t("fabric_weight_sqm"), value=0.130, step=0.010, format="%.3f")
    fabric_weight_lm = fabric_width * fabric_weight_sqm
    st.number_input(t("fabric_weight_lm"), value=fabric_weight_lm, disabled=True, format="%.3f")
    speed = st.number_input(t("prod_speed"), value=30.00, step=5.0, format="%.2f")
    drying_energy = st.number_input(t("drying_energy"), value=0.70, step=0.05, format="%.2f")

with col2:
    hours_day = st.number_input(t("working_hours"), value=18.00, step=0.5, format="%.2f")
    days_year = st.number_input(t("working_days"), value=320, min_value=1, max_value=365, step=5)
    changeovers_day = st.number_input(t("changeovers_day"), value=3, min_value=0, step=1)

summary_placeholder = st.container()

st.header(t("recipe_data"))
rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.markdown(f"**{t('trad_padder')}**")
    padder_softener_vol = st.number_input(t("padder_pickup"), value=70.0, step=1.0, format="%.1f", key="padder_pickup")
    padder_operating_power = st.number_input(t("operating_energy"), value=7.5, step=0.5, format="%.2f", key="padder_op_power")
    padder_waste_changeover = st.number_input(t("waste_changeover"), value=20.0, step=1.0, format="%.1f", key="padder_waste")
    padder_fabric_waste_m = st.number_input(t("fabric_waste_changeover"), value=15.0, step=1.0, format="%.1f", key="padder_fab_waste")
    padder_changeover_time = st.number_input(t("changeover_time"), value=30.0, step=1.0, format="%.1f", key="padder_changeover_time") 
    
    padder_chem_a_g_l = st.number_input(f"{t('chem_a')} (g/L)", value=30.0, step=1.0, format="%.1f", key="padder_chem_a")
    padder_chem_b_g_l = st.number_input(f"{t('chem_b')} (g/L)", value=15.0, step=1.0, format="%.1f", key="padder_chem_b")
    padder_chem_c_g_l = st.number_input(f"{t('chem_c')} (g/L)", value=1.0, step=0.5, format="%.1f", key="padder_chem_c")

    if "padder_base_pickup" not in st.session_state:
        st.session_state["padder_base_pickup"] = padder_softener_vol

    padder_actual_pickup = padder_softener_vol / 100.0

    st.info(f"""
    **{t('applied_chem_info')} ({t('at_pickup')} {padder_softener_vol:.1f}% {t('pickup')}):**
    * {t('chem_a')}: **{padder_chem_a_g_l * padder_actual_pickup:.1f} g/kg**
    * {t('chem_b')}: **{padder_chem_b_g_l * padder_actual_pickup:.1f} g/kg**
    * {t('chem_c')}: **{padder_chem_c_g_l * padder_actual_pickup:.1f} g/kg**
    """)

with rec_col2:
    st.markdown(f"**{t('imogo_fmax')}**")
    fmax_softener_vol = st.number_input(t("fmax_pickup"), value=35.0, step=1.0, format="%.1f", key="fmax_pickup")
    fmax_operating_power = st.number_input(t("operating_energy"), value=2.0, step=0.5, format="%.2f", key="fmax_op_power")
    fmax_waste_changeover = st.number_input(t("waste_changeover"), value=2.0, step=1.0, format="%.1f", key="fmax_waste")
    fmax_fabric_waste_m = st.number_input(t("fabric_waste_changeover"), value=2.0, step=1.0, format="%.1f", key="fmax_fab_waste")
    fmax_changeover_time = st.number_input(t("changeover_time"), value=10.0, step=1.0, format="%.1f", key="fmax_changeover_time") 
    chem_reduction = st.number_input(t("chem_reduction"), value=30.0, step=1.0, format="%.1f", key="chem_reduction")
    
    wpu_ratio = (padder_softener_vol / fmax_softener_vol) if fmax_softener_vol > 0 else 1.0
    reduction_factor = (1.0 - (chem_reduction / 100.0))

    req_fmax_chem_a = padder_chem_a_g_l * wpu_ratio
    req_fmax_chem_b = padder_chem_b_g_l * wpu_ratio
    req_fmax_chem_c = padder_chem_c_g_l * wpu_ratio

    target_a = req_fmax_chem_a * reduction_factor
    target_b = req_fmax_chem_b * reduction_factor
    target_c = req_fmax_chem_c * reduction_factor

    if "last_chem_reduction" not in st.session_state:
        st.session_state["last_chem_reduction"] = chem_reduction
    if "last_fmax_pickup" not in st.session_state:
        st.session_state["last_fmax_pickup"] = fmax_softener_vol
    if "last_padder_pickup" not in st.session_state:
        st.session_state["last_padder_pickup"] = padder_softener_vol

    if (chem_reduction != st.session_state["last_chem_reduction"] or 
        fmax_softener_vol != st.session_state["last_fmax_pickup"] or 
        padder_softener_vol != st.session_state["last_padder_pickup"]):
        
        st.session_state["fmax_chem_a"] = target_a
        st.session_state["fmax_chem_b"] = target_b
        st.session_state["fmax_chem_c"] = target_c
        
        st.session_state["last_chem_reduction"] = chem_reduction
        st.session_state["last_fmax_pickup"] = fmax_softener_vol
        st.session_state["last_padder_pickup"] = padder_softener_vol

    fmax_chem_a_g_l = st.number_input(f"{t('chem_a')} (g/L)", value=float(target_a), step=0.1, format="%.1f", key="fmax_chem_a")
    fmax_chem_b_g_l = st.number_input(f"{t('chem_b')} (g/L)", value=float(target_b), step=0.1, format="%.1f", key="fmax_chem_b")
    fmax_chem_c_g_l = st.number_input(f"{t('chem_c')} (g/L)", value=float(target_c), step=0.1, format="%.1f", key="fmax_chem_c")

    st.info(f"""
    **{t('target_conc_info')}**
    * {t('chem_a')}: **{req_fmax_chem_a:.1f} g/L**
    * {t('chem_b')}: **{req_fmax_chem_b:.1f} g/L**
    * {t('chem_c')}: **{req_fmax_chem_c:.1f} g/L**
    """)

# RUN CALCULATIONS
inputs = {
    'fabric_width': fabric_width,
    'fabric_weight_sqm': fabric_weight_sqm,
    'speed': speed,
    'hours_day': hours_day,
    'days_year': days_year,
    'changeovers_day': changeovers_day,
    'drying_energy': drying_energy,
    'padder_operating_power': padder_operating_power, 
    'fmax_operating_power': fmax_operating_power,
    'padder_waste_changeover': padder_waste_changeover,
    'fmax_waste_changeover': fmax_waste_changeover,
    'padder_softener_vol': padder_softener_vol,
    'fmax_softener_vol': fmax_softener_vol,
    'padder_chem_a_g_l': padder_chem_a_g_l,
    'padder_chem_b_g_l': padder_chem_b_g_l,
    'padder_chem_c_g_l': padder_chem_c_g_l,
    'fmax_chem_a_g_l': fmax_chem_a_g_l,
    'fmax_chem_b_g_l': fmax_chem_b_g_l,
    'fmax_chem_c_g_l': fmax_chem_c_g_l,
    'padder_fabric_waste_m': padder_fabric_waste_m,
    'fmax_fabric_waste_m': fmax_fabric_waste_m,
    'padder_changeover_time': padder_changeover_time,
    'fmax_changeover_time': fmax_changeover_time,
    'cost_fabric_waste': cost_fabric_waste,
    'cost_energy': cost_energy,
    'cost_water': cost_water,
    'cost_waste': cost_waste,
    'cost_chem_a': cost_chem_a,
    'cost_chem_b': cost_chem_b,
    'cost_chem_c': cost_chem_c,
    'co2_factor': co2_factor,
    'investment': investment,
    'currency': currency
}
calc = FMaxCalculator(inputs)
res = calc.calculate()

with summary_placeholder:
    st.header(t("prod_summary"))
    vol_col1, vol_col2 = st.columns(2)
    
    with vol_col1:
        st.markdown(f"**{t('trad_padder')}**")
        st.markdown(f"### {res['weight_year_padder']:,.0f} {t('kg_year')}".replace(",", " "))
        st.markdown(f"#### {res['lm_year_padder']:,.0f} {t('m_year')}".replace(",", " "))
        st.caption(f"{res['weight_day_padder']:,.0f} {t('kg_day')} | {res['lm_day_padder']:,.0f} {t('m_day')} | {speed:.1f} m/min".replace(",", " "))
        
    with vol_col2:
        st.markdown(f"**{t('imogo_fmax')}**")
        st.markdown(f"### {res['weight_year_fmax']:,.0f} {t('kg_year')}".replace(",", " "))
        st.markdown(f"#### {res['lm_year_fmax']:,.0f} {t('m_year')}".replace(",", " "))
        if res['extra_weight'] > 0:
            st.markdown(f"<span style='color:green; font-weight:bold;'>↑ {res['extra_weight']:,.0f} {t('kg_year')} {t('extra')} ({res['extra_lm']:,.0f} {t('m_year')})</span>".replace(",", " "), unsafe_allow_html=True)
        st.caption(f"{res['weight_day_fmax']:,.0f} {t('kg_day')} | {res['lm_day_fmax']:,.0f} {t('m_day')} | {speed:.1f} m/min".replace(",", " "))
        
    st.markdown("---")
    
    st.subheader(t("capacity_boost_title"))
    st.markdown(t("capacity_boost_desc"))

    cap_col1, cap_col2, cap_col3 = st.columns(3)

    with cap_col1:
        st.metric(
            label=t("max_potential_speed"),
            value=f"{res['max_potential_speed']:.1f} m/min",
            delta=f"+{res['speed_increase_percent']:.1f} %"
        )
        
    with cap_col2:
        st.metric(
            label=t("extra_vol_weight"),
            value=f"{res['extra_volume_same_energy_kg']:,.0f} {t('kg_year')}".replace(",", " ")
        )
        
    with cap_col3:
        st.metric(
            label=t("extra_vol_length"),
            value=f"{res['extra_volume_same_energy_lm']:,.0f} {t('m_year')}".replace(",", " ")
        )

st.divider()

# RESULTS & SAVINGS DISPLAY
st.header(t("savings_overview"))
m1, m2, m3 = st.columns(3)
m1.metric(t("annual_savings"), f"{currency} {fmt_num(res['total_annual_savings'])}")
m2.metric(t("payback_period"), f"{res['payback_months']:.1f} {t('months')}")
m3.metric(t("chem_savings"), f"{fmt_num(res['total_chem_savings_kg'])} {t('kg_year')}")

st.header(t("env_savings"))
e1, e2, e3 = st.columns(3)
e1.metric(t("water_savings"), f"{fmt_num(res['water_savings_m3'])} m³/{t('kg_year').split('/')[1]}")
e2.metric(t("co2_savings"), f"{res['co2_savings_tonnes']:.1f} {t('tonnes_year')}")
e3.metric(t("energy_savings"), f"{fmt_num(res['energy_savings_kwh'])} kWh/{t('kg_year').split('/')[1]}")

st.header(t("monetary_savings"))

breakdown_data = {
    t("category"): [
        t("chem_a"),
        t("chem_b"),
        t("chem_c"),
        t("process_water"),
        t("waste_water_treatment"),
        t("fabric_waste"),
        t("energy"),
        t("total_annual_savings")
    ],
    f"{t('savings')} ({currency})": [
        f"{currency} {fmt_num(res['savings_chem_a'])}",
        f"{currency} {fmt_num(res['savings_chem_b'])}",
        f"{currency} {fmt_num(res['savings_chem_c'])}",
        f"{currency} {fmt_num(res['savings_water'])}",
        f"{currency} {fmt_num(res['savings_waste_handling'])}",
        f"{currency} {fmt_num(res['savings_fabric_waste'])}",
        f"{currency} {fmt_num(res['savings_energy'])}",
        f"{currency} {fmt_num(res['total_annual_savings'])}"
    ]
}

df_breakdown = pd.DataFrame(breakdown_data)
st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

st.header(t("total_cost_kg"))
c_kg1, c_kg2 = st.columns(2)

with c_kg1:
    st.metric(
        label=t("trad_padder"),
        value=f"{currency} {res['cost_per_kg_padder']:.2f} / kg"
    )

with c_kg2:
    st.metric(
        label=t("imogo_fmax"),
        value=f"{currency} {res['cost_per_kg_fmax']:.2f} / kg",
        delta=f"-{currency} {res['cost_per_kg_savings']:.2f} / kg (-{res['cost_per_kg_pct']:.1f}%)",
        delta_color="inverse"
    )

st.divider()
st.header(t("visual_overview"))

savings_chart_data = pd.DataFrame({
    t("category"): [t("chem_a"), t("chem_b"), t("chem_c"), t("process_water"), t("energy"), t("waste_water_treatment"), t("fabric_waste")],
    t("savings"): [
        res['savings_chem_a'], 
        res['savings_chem_b'], 
        res['savings_chem_c'], 
        res['savings_water'],
        res['savings_waste_handling'],
        res['savings_fabric_waste'], 
        res['savings_energy']
    ]
})

fig_savings = px.bar(
    savings_chart_data,
    x=t("savings"),
    y=t("category"),
    orientation="h",
    title=f"{t('yearly_savings_cat')} ({currency}/{t('kg_year').split('/')[1]})",
    labels={t("savings"): f"{currency} {t('savings')}", t("category"): ""}
)
fig_savings.update_traces(marker_color='#00b4d8')
fig_savings.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_savings, use_container_width=True)

cost_chart_data = pd.DataFrame({
    t("system"): [t("trad_padder"), t("imogo_fmax")],
    t("cost"): [res['cost_per_kg_padder'], res['cost_per_kg_fmax']]
})

fig_cost = px.bar(
    cost_chart_data,
    x=t("system"),
    y=t("cost"),
    title=f"{t('total_cost_kg')} ({currency})",
    color=t("system"),
    color_discrete_map={
        t("trad_padder"): "#ff4d4d",
        t("imogo_fmax"): "#00cc99"
    },
    labels={t("cost"): f"{currency} / kg", t("system"): ""}
)
fig_cost.update_layout(showlegend=False)
st.plotly_chart(fig_cost, use_container_width=True)

# ------------------------------------------------------------------------------
# GENERATE HTML REPORT
# ------------------------------------------------------------------------------
st.divider()
st.header(t("gen_report"))

current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{t('report_title')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; margin: 40px; line-height: 1.4; }}
        h1 {{ color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; }}
        h2 {{ color: #003366; margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 5px; font-size: 1.2em; }}
        .meta {{ color: #555; font-size: 0.9em; margin-bottom: 20px; }}
        .card {{ background: #f8f9fa; border-left: 4px solid #003366; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 0.9em; }}
        th {{ background-color: #f1f3f5; color: #003366; }}
        .footer {{ margin-top: 40px; text-align: center; font-size: 0.8em; color: #777; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body>
    <h1>{t('report_title')}</h1>
    <div class="meta">
        <strong>{t('prepared_for')}</strong> Imogo &nbsp;|&nbsp; <strong>{t('generated')}</strong> {current_time_str}
    </div>

    <div class="card">
        <h3>{t('key_results')}</h3>
        <h2 style="border:none; margin:5px 0; color: #003366;">{t('annual_savings')}: {currency} {fmt_num(res['total_annual_savings'])}</h2>
        <p><strong>{t('payback_period')}:</strong> {res['payback_months']:.1f} {t('months')}<br>
        <strong>{t('investment_cost')}:</strong> {currency} {fmt_num(investment)}</p>
    </div>

    <h2>{t('prod_summary_report')}</h2>
    <table>
        <tr><th>{t('system')}</th><th>{t('prod_volume')}</th></tr>
        <tr><td>{t('trad_padder')}</td><td>{fmt_num(res['weight_year_padder'])} {t('kg_year')}</td></tr>
        <tr><td>{t('imogo_fmax')}</td><td>{fmt_num(res['weight_year_padder'])} {t('kg_year')}</td></tr>
    </table>

    <h2>{t('physical_savings')}</h2>
    <ul>
        <li><strong>{t('chem_savings')}:</strong> {fmt_num(res['total_chem_savings_kg'])} {t('kg_year')}</li>
        <li><strong>{t('water_savings')}:</strong> {fmt_num(res['water_savings_m3'])} m³/{t('kg_year').split('/')[1]}</li>
        <li><strong>{t('energy_savings')}:</strong> {fmt_num(res['energy_savings_kwh'])} kWh/{t('kg_year').split('/')[1]}</li>
        <li><strong>{t('co2_savings')}:</strong> {res['co2_savings_tonnes']:.1f} {t('tonnes_year')}</li>
    </ul>

<h3 style="color: #003366;">{t('capacity_boost_title')}</h3>
<p style="margin-bottom: 10px;">{t('capacity_boost_desc')}</p>
<ul>
    <li><strong>{t('max_potential_speed')}:</strong> {res['max_potential_speed']:.1f} m/min (+{res['speed_increase_percent']:.1f}%)</li>
    <li><strong>{t('extra_vol_weight')}:</strong> {fmt_num(res['extra_volume_same_energy_kg'])} {t('kg_year')}</li>
    <li><strong>{t('extra_vol_length')}:</strong> {fmt_num(res['extra_volume_same_energy_lm'])} {t('m_year')}</li>

</ul>
    <h2>{t('monetary_savings')}</h2>
    <table>
        <tr><th>{t('category')}</th><th>{t('savings')} ({currency}/{t('kg_year').split('/')[1]})</th></tr>
        <tr><td>{t('chem_a')}</td><td>{currency} {fmt_num(res['savings_chem_a'])}</td></tr>
        <tr><td>{t('chem_b')}</td><td>{currency} {fmt_num(res['savings_chem_b'])}</td></tr>
        <tr><td>{t('chem_c')}</td><td>{currency} {fmt_num(res['savings_chem_c'])}</td></tr>
        <tr><td>{t('process_water')}</td><td>{currency} {fmt_num(res['savings_water'])}</td></tr>
        <tr><td>{t('waste_water_treatment')}</td><td>{currency} {fmt_num(res['savings_waste_handling'])}</td></tr>
        <tr><td>{t('fabric_waste')}</td><td>{currency} {fmt_num(res['savings_fabric_waste'])}</td></tr>
        <tr><td>{t('energy')}</td><td>{currency} {fmt_num(res['savings_energy'])}</td></tr>
        <tr style="font-weight: bold; background-color: #f1f3f5;"><td>{t('total_annual_savings')}</td><td>{currency} {fmt_num(res['total_annual_savings'])}</td></tr>
    </table>

   <h2>{t('process_recipe_comp')}</h2>
<table>
    <tr><th>{t('parameter')}</th><th>{t('trad_padder')}</th><th>{t('imogo_fmax')}</th></tr>
    <tr><td>{t('working_hours')}</td><td>{hours_day} h</td><td>{hours_day} h</td></tr>
    <tr><td>{t('prod_speed')}</td><td>{speed} m/min</td><td>{speed} m/min</td></tr>
    <tr><td>{t('pickup')}</td><td>{padder_softener_vol}%</td><td>{fmax_softener_vol}%</td></tr>
    <tr><td>{t('chem_a')} (g/L)</td><td>{padder_chem_a_g_l} g/L</td><td>{fmax_chem_a_g_l} g/L</td></tr>
    <tr><td>{t('chem_b')} (g/L)</td><td>{padder_chem_b_g_l} g/L</td><td>{fmax_chem_b_g_l} g/L</td></tr>
    <tr><td>{t('chem_c')} (g/L)</td><td>{padder_chem_c_g_l} g/L</td><td>{fmax_chem_c_g_l} g/L</td></tr>
</table>

<h2>{t('gen_params')}</h2>
<table>
    <tr><th>{t('parameter')}</th><th>{t('value')}</th></tr>
    <tr><td>{t('working_days')}</td><td>{days_year}</td></tr>
    <tr><td>{t('working_hours')}</td><td>{hours_day} h</td></tr>
    <tr><td>{t('fabric_width')} & GSM</td><td>{fabric_width} m / {fabric_weight_sqm} kg/m²</td></tr>
    <tr><td>{t('electricity')} Price</td><td>{cost_energy:.3f} {currency}/kWh</td></tr>
    <tr><td>{t('water')} Price</td><td>{cost_water:.5f} {currency}/L</td></tr>
    <tr><td>{t('chem_a')} Price</td><td>{cost_chem_a:.2f} {currency}/kg</td></tr>
    <tr><td>{t('chem_b')} Price</td><td>{cost_chem_b:.2f} {currency}/kg</td></tr>
    <tr><td>{t('chem_c')} Price</td><td>{cost_chem_c:.2f} {currency}/kg</td></tr>
    <tr><td>{t('investment_cost')}</td><td>{currency} {fmt_num(investment)}</td></tr>
    <tr><td>{t('co2_factor')}</td><td>{co2_factor:.3f} kg/kWh</td></tr>
</table>

    <div class="footer">
        {t('footer_text')}
    </div>
</body>
</html>
"""

st.download_button(
    label=t("dl_report"),
    data=html_content,
    file_name="Imogo_FMax_ROI_Report.html",
    mime="text/html"
)
