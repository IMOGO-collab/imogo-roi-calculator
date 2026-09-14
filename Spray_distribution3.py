import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- SUPERMJUK PROFIL FÖR ETT MUNSTYCKE ---
# (definieras här överst så den kan användas både för auto-beräkning av
#  antal munstycken och för alla grafer/tabeller längre ner)
def super_smooth_profile(x, x_pos=0.0, h_flat=120.0, h_total=250.0):
    dist = np.abs(x - x_pos)
    profile = np.zeros_like(x, dtype=float)
    profile[dist <= h_flat] = 1.0

    taper_mask = (dist > h_flat) & (dist <= h_total)
    if h_total > h_flat:
        t = (dist[taper_mask] - h_flat) / (h_total - h_flat)
        smooth_step = 6 * t**5 - 15 * t**4 + 10 * t**3
        profile[taper_mask] = 1.0 - smooth_step

    return profile


def calc_required_nozzles_per_ramp(fabric_width, cc, h_flat, h_total, osc_margin, max_k=60):
    """Hittar minsta antal munstycken per ramp (två ramper totalt) som ger
    en garanterad täckningsbredd (efter oscillationsmarginal) >= fabric_width."""
    width = 0.0
    for k in range(1, max_k + 1):
        half_count = (k - 1) / 2.0
        pos1 = [-cc / 4.0 - half_count * cc + i * cc for i in range(k)]
        pos2 = [cc / 4.0 - half_count * cc + i * cc for i in range(k)]
        all_pos = pos1 + pos2

        x = np.linspace(min(all_pos) - h_total - 50, max(all_pos) + h_total + 50, 2000)
        y = np.zeros_like(x)
        for p in all_pos:
            y += super_smooth_profile(x, x_pos=p, h_flat=h_flat, h_total=h_total)

        mask = y >= 1.98
        xs = x[mask]
        if len(xs) > 0:
            width = max(0.0, (xs[-1] - osc_margin) - (xs[0] + osc_margin))
        else:
            width = 0.0

        if width >= fabric_width:
            return k, width

    return max_k, width

# Sidans layout
st.set_page_config(page_title="Munstycksanalys - Profilering", layout="wide")

st.title("🎛️ Dynamisk Munstycksanalys (Profilering)")
st.write("Använd reglagen för att medvetet justera flödet och kompensera för tygvariationer. Grafen och mätvärdena visar exakt **vilken del av tyget som påverkas** av dina justeringar.")

# --- SIDEBAR: REGLAGE FÖR GEOMETRI & FLÖDEN ---
st.sidebar.header("Tygkonfiguration")
fixed_fabric_width = st.sidebar.number_input(
    "Fast banbredd / Tygbredd [mm]", 
    value=3400.0, step=50.0
)

st.sidebar.header("Munstycksprofil (Enskilt munstycke)")
half_flat = st.sidebar.number_input(
    "Platåhalva (100% flöde) [mm]", 
    value=120.0, step=5.0, min_value=0.0
)
flank_width = st.sidebar.number_input(
    "Flankbredd (avtrappning) [mm]", 
    value=120.0, step=5.0, min_value=1.0
)
half_total = half_flat + flank_width
ideal_cc = half_flat + half_total

st.sidebar.caption(f"💡 **Teoretiskt perfekt C-C för profilen:** {ideal_cc:.0f} mm")

st.sidebar.header("Geometri & Marginaler")
cc_distance = st.sidebar.slider(
    "C-C Avstånd mellan munstycken [mm]", 
    min_value=250.0, max_value=500.0, value=360.0, step=1.0
)

if abs(cc_distance - ideal_cc) < 0.5:
    st.sidebar.success(f"Ditt C-C ({cc_distance:.0f} mm) matchar munstycksprofilen perfekt!")
else:
    st.sidebar.info(f"Vid C-C {cc_distance:.0f} mm får du en svag överlappseffekt baserad på profilen (verklighetstroget).")

oscillation_margin = st.sidebar.number_input(
    "Oscilleringsmarginal per sida [mm]", 
    value=35.0, step=5.0
)

offset = cc_distance / 2.0

# --- AUTOMATISK BERÄKNING AV ANTAL MUNSTYCKEN ---
st.sidebar.header("Antal munstycken")
recommended_k, recommended_width = calc_required_nozzles_per_ramp(
    fixed_fabric_width, cc_distance, half_flat, half_total, oscillation_margin
)
n_nozzles_per_ramp = recommended_k
total_nozzles = 2 * n_nozzles_per_ramp

st.sidebar.info(
    f"📦 **Totalt antal munstycken / spraykassett:** {total_nozzles} "
    f"\n\n"
    f"Beräknat automatiskt för {fixed_fabric_width:.0f} mm banbredd "
    f"(ger ≈{recommended_width:.0f} mm garanterad täckning)."
)


st.sidebar.header("🧴 Vätskepåslag (Pickup) → Duty Cycle")
fabric_weight = st.sidebar.number_input(
    "Tygvikt [g/m²]",
    value=160.0, step=5.0, min_value=0.0
)
pickup_pct = st.sidebar.number_input(
    "Önskad pickup [%]",
    value=120.0, step=5.0, min_value=0.0,
    help="100% pickup = vätskepåslaget väger lika mycket som det torra tyget (t.ex. 100 gsm tyg + 100% pickup = 200 gsm totalt)."
)
line_speed = st.sidebar.number_input(
    "Banhastighet [m/min]",
    value=20.0, step=1.0, min_value=0.1
)
nozzle_flow_rate = st.sidebar.number_input(
    "Munstyckesflöde vid 100% duty cycle [ml/min]",
    value=690.0, step=10.0, min_value=0.1,
    help="Flödet ut ur ett munstycke när det står helt öppet (duty cycle = 100%), kontinuerligt, "
         "angivet i ml/min."
)
duty_split_ramps = st.sidebar.number_input(
    "Antal ramper i verkligheten (delar på påslaget)",
    value=4, step=1, min_value=1,
    help="Hur många fysiska ramper som tillsammans applicerar vätskan på samma bredd. "
         "Modellen ovan visualiserar munstyckena som 2 sammanflätade ramper, men om ni i "
         "verkligheten har fler ramper som delar på samma yta ska duty cycle-beräkningen "
         "dela målpåslaget på det verkliga antalet ramper."
)
target_addon = fabric_weight * pickup_pct / 100.0
st.sidebar.caption(f"💡 Målpåslag: **{target_addon:.1f} g/m²** (totalvikt tyg+vätska: {fabric_weight + target_addon:.1f} g/m²)")

st.sidebar.header("Flöden per munstycke (%)")

ramp1_ids = list(range(1, 2 * n_nozzles_per_ramp, 2))
ramp2_ids = list(range(2, 2 * n_nozzles_per_ramp + 1, 2))

# --- POSITIONERING (beräknas tidigt så vi vet vilka munstycken som är YTTERST just nu) ---
fixed_start = 0.0
fixed_end = fixed_fabric_width
fabric_center = fixed_fabric_width / 2.0

ramp1_center = fabric_center - (cc_distance / 4.0)
ramp2_center = fabric_center + (cc_distance / 4.0)

half_count = (n_nozzles_per_ramp - 1) / 2.0
pos_ramp1 = [ramp1_center - half_count * cc_distance + i * cc_distance for i in range(n_nozzles_per_ramp)]
pos_ramp2 = [ramp2_center - half_count * cc_distance + i * cc_distance for i in range(n_nozzles_per_ramp)]

# --- FLYTTA KANTJUSTERINGAR MED NÄR ANTAL MUNSTYCKEN ÄNDRAS (t.ex. vid annan banbredd) ---
# Om man har sänkt flödet på de yttersta munstyckena ska sänkningen alltid följa med till
# de munstycken som ÄR yttrest just nu — inte ligga kvar på ett fast munstycksnummer som kan
# hamna mer mot mitten när fler/färre munstycken läggs till.
current_sorted_ids = [nid for nid, _ in sorted(
    zip(ramp1_ids + ramp2_ids, pos_ramp1 + pos_ramp2), key=lambda t: t[1]
)]
prev_sorted_ids = st.session_state.get('_prev_sorted_ids')

if prev_sorted_ids is not None and prev_sorted_ids != current_sorted_ids:
    def _get_flow(nid):
        return st.session_state.get(f"nozzle_slider_{nid}", 100)

    left_trim = []
    for nid in prev_sorted_ids:
        v = _get_flow(nid)
        if v == 100:
            break
        left_trim.append((nid, v))

    right_trim = []
    for nid in reversed(prev_sorted_ids):
        v = _get_flow(nid)
        if v == 100:
            break
        right_trim.append((nid, v))

    # Undvik överlapp om i princip alla munstycken var ändrade
    max_total = len(prev_sorted_ids)
    if len(left_trim) + len(right_trim) > max_total:
        half = max_total // 2
        left_trim = left_trim[:half]
        right_trim = right_trim[:max_total - half]

    # Nollställ de gamla kantmunstyckena (de kan nu ligga mer mot mitten)
    for nid, _ in left_trim + right_trim:
        st.session_state[f"nozzle_slider_{nid}"] = 100

    # Applicera samma "steg in från kanten"-mönster på de NYA yttersta munstyckena
    for rank, (_, v) in enumerate(left_trim):
        if rank < len(current_sorted_ids):
            st.session_state[f"nozzle_slider_{current_sorted_ids[rank]}"] = v
    for rank, (_, v) in enumerate(right_trim):
        if rank < len(current_sorted_ids):
            st.session_state[f"nozzle_slider_{current_sorted_ids[-(rank + 1)]}"] = v

st.session_state['_prev_sorted_ids'] = current_sorted_ids

# --- RESET-KNAPP FÖR MUNSTYCKEN ---
def reset_nozzles():
    for n_id in ramp1_ids + ramp2_ids:
        st.session_state[f"nozzle_slider_{n_id}"] = 100

st.sidebar.button("🔄 Återställ alla ventiler till 100%", on_click=reset_nozzles, use_container_width=True)

ramp1_label = ", ".join(str(i) for i in ramp1_ids)
ramp2_label = ", ".join(str(i) for i in ramp2_ids)

ramp1_flows = []
with st.sidebar.expander(f"Ramp 1 (Munstycke {ramp1_label})", expanded=True):
    for n_id in ramp1_ids:
        key = f"nozzle_slider_{n_id}"
        current_val = st.session_state.get(key, 100)
        if current_val == 0:
            st.markdown(f"<span style='color:#9e9e9e'>⚪ Munstycke {n_id} — AVSTÄNGT</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#31333F'>🔵 Munstycke {n_id}</span>", unsafe_allow_html=True)
        flow_val = st.slider(
            f"Munstycke {n_id}", 
            min_value=0, max_value=150, value=100, step=5,
            key=key, label_visibility="collapsed"
        ) / 100.0
        ramp1_flows.append(flow_val)

ramp2_flows = []
with st.sidebar.expander(f"Ramp 2 - Förskjuten (Munstycke {ramp2_label})", expanded=False):
    for n_id in ramp2_ids:
        key = f"nozzle_slider_{n_id}"
        current_val = st.session_state.get(key, 100)
        if current_val == 0:
            st.markdown(f"<span style='color:#9e9e9e'>⚪ Munstycke {n_id} — AVSTÄNGT</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#31333F'>🟠 Munstycke {n_id}</span>", unsafe_allow_html=True)
        flow_val = st.slider(
            f"Munstycke {n_id}", 
            min_value=0, max_value=150, value=100, step=5,
            key=key, label_visibility="collapsed"
        ) / 100.0
        ramp2_flows.append(flow_val)

# --- EGET DIAGRAM FÖR ENSKILT MUNSTYCKE ---
with st.expander("🔍 Visualisera enskilt munstycke (Profil & Sprutbild)", expanded=True):
    fig_single, ax_s = plt.subplots(figsize=(12, 3.5))
    x_single = np.linspace(-half_total - 100, half_total + 100, 600)
    y_single = super_smooth_profile(x_single, 0.0, half_flat, half_total)
    
    ax_s.plot(x_single, y_single, color='teal', linewidth=2.5, label='Munstycksprofil')
    ax_s.axvspan(-half_flat, half_flat, color='green', alpha=0.15, label=f'Platå ({2*half_flat:.0f} mm)')
    ax_s.axvspan(-half_total, -half_flat, color='orange', alpha=0.15, label=f'Vänster flank ({flank_width:.0f} mm)')
    ax_s.axvspan(half_flat, half_total, color='orange', alpha=0.15, label=f'Höger flank ({flank_width:.0f} mm)')
    
    ax_s.set_title(f"Sprutprofil per munstycke | Totalsprutbredd: {2*half_total:.0f} mm | Platå: {2*half_flat:.0f} mm | Flank: {flank_width:.0f} mm", fontsize=10)
    ax_s.set_xlabel("Avstånd från munstyckets centrum [mm]", fontsize=9)
    ax_s.set_ylabel("Relativt flöde", fontsize=9)
    ax_s.set_ylim(0, 1.2)
    ax_s.grid(True, linestyle=':', alpha=0.6)
    ax_s.legend(loc='upper right', fontsize=8)
    plt.tight_layout()
    st.pyplot(fig_single)

# --- BYGG NOZZLE_INFO (positioner beräknades tidigare, ovanför reglagen) ---
nozzle_info = []
for i in range(n_nozzles_per_ramp):
    nozzle_info.append({'id': f"R1-M{ramp1_ids[i]}", 'pos': pos_ramp1[i], 'flow': ramp1_flows[i], 'ramp': 1})
for i in range(n_nozzles_per_ramp):
    nozzle_info.append({'id': f"R2-M{ramp2_ids[i]}", 'pos': pos_ramp2[i], 'flow': ramp2_flows[i], 'ramp': 2})

nozzle_info_sorted = sorted(nozzle_info, key=lambda k: k['pos'])

# --- DUTY CYCLE PER MUNSTYCKE (KOPPLAT TILL PICKUP) ---
# Massbalans: Bas-duty = (Målpåslag × Banhastighet × C-C-avstånd) / (2 × Munstyckesflöde)
# Divisorn styrs av "Antal ramper i verkligheten" i sidopanelen — de fysiska ramperna
# delar tillsammans upp ansvaret för målpåslaget på den bredd (C-C) varje munstycke "äger".
cc_m = cc_distance / 1000.0
if nozzle_flow_rate > 0:
    base_duty = (target_addon * line_speed * cc_m) / (duty_split_ramps * nozzle_flow_rate)
else:
    base_duty = 0.0

DUTY_MAX = 0.9  # max tillåten/möjlig duty cycle (90%) — utrymme kvar för ventilens öppnings-/stängningstid

for n in nozzle_info:
    n['duty'] = base_duty * n['flow']          # faktisk (begärd) duty cycle, kan bli > 90% = mättad
    n['duty_saturated'] = n['duty'] > DUTY_MAX
    n['duty_capped'] = min(n['duty'], DUTY_MAX)
    n['actual_flow'] = n['duty_capped'] * nozzle_flow_rate  # verkligt uppnåeligt flöde [ml/min]

nozzle_info_sorted = sorted(nozzle_info, key=lambda k: k['pos'])  # uppdatera sorterad lista med duty-data
saturated_nozzles = [n for n in nozzle_info if n['duty_saturated']]
total_flow_out = sum(n['actual_flow'] for n in nozzle_info)
total_flow_requested = sum(n['duty'] * nozzle_flow_rate for n in nozzle_info)
total_flow_out_l = total_flow_out / 1000.0
total_flow_requested_l = total_flow_requested / 1000.0

st.subheader("🧴 Vätskepåslag (Pickup) → Duty Cycle per munstycke")
st.write(
    "Utifrån tygvikt, önskad pickup, banhastighet och munstyckets flöde vid 100% duty cycle "
    "räknas här ut hur stor andel av tiden (PWM/duty cycle) varje munstycke behöver vara öppet "
    "för att uppnå rätt vätskepåslag. Profil-reglagen (%) ovan fungerar som en multiplikator "
    "ovanpå bas-duty:n — sänker du ett munstycke till 50% profil blir dess duty cycle hälften "
    "så stor. Max tillåten duty cycle är 90%."
)

total_wet_weight = fabric_weight + target_addon

dc1, dc2, dc3, dc4, dc5 = st.columns(5)
dc1.metric(
    "Målpåslag (vätska)",
    f"{target_addon:.1f} g/m²",
    help=f"Bara vätskan: {fabric_weight:.0f} g/m² tyg × {pickup_pct:.0f}% pickup / 100"
)
dc2.metric(
    "Totalvikt (tyg + vätska)",
    f"{total_wet_weight:.1f} g/m²",
    help=f"{fabric_weight:.0f} g/m² tyg + {target_addon:.1f} g/m² vätska"
)
dc3.metric("Bas-duty cycle (vid 100% profil)", f"{base_duty*100:.1f} %")
dc4.metric(
    "Totalt flöde ut ur ramperna",
    f"{total_flow_out_l:.2f} L/min",
    delta=None if abs(total_flow_out - total_flow_requested) < 0.5 else f"begärt: {total_flow_requested_l:.2f} L/min",
    delta_color="off",
    help="Summan av verkligt flöde (kapat vid 90% duty cycle) från alla munstycken som används, "
         "dvs. det totala vätskeflödet som just nu går ut ur samtliga ramper tillsammans."
)
dc5.metric(
    "Mättade munstycken",
    f"{len(saturated_nozzles)} / {len(nozzle_info)}",
    delta=None if not saturated_nozzles else "Kräver högre flöde eller lägre hastighet",
    delta_color="off"
)

if saturated_nozzles:
    sat_ids = ", ".join(n['id'] for n in sorted(saturated_nozzles, key=lambda k: k['pos']))
    st.warning(
        f"⚠️ Följande munstycken kräver >90% duty cycle (över den tillåtna maxgränsen): "
        f"**{sat_ids}**. Öka munstyckesflödet, sänk banhastigheten/pickup:en, eller sänk profil-% "
        f"på dessa munstycken."
    )

fig_duty, ax_d = plt.subplots(figsize=(14, 4))
duty_sorted = nozzle_info_sorted
ids = [n['id'] for n in duty_sorted]
duty_pcts = [n['duty'] * 100 for n in duty_sorted]
bar_colors = []
for n in duty_sorted:
    if n['duty_saturated']:
        bar_colors.append('crimson')
    elif n['flow'] == 0.0:
        bar_colors.append('lightgray')
    elif n['ramp'] == 1:
        bar_colors.append('tab:blue')
    else:
        bar_colors.append('tab:orange')

bars = ax_d.bar(ids, duty_pcts, color=bar_colors)
ax_d.axhline(90, color='crimson', linestyle='--', linewidth=1.2, label='90% (max tillåten duty cycle)')
for rect, val in zip(bars, duty_pcts):
    ax_d.annotate(f"{val:.0f}%", (rect.get_x() + rect.get_width() / 2, val),
                   textcoords="offset points", xytext=(0, 4), ha='center', fontsize=7, rotation=90 if len(ids) > 25 else 0)

ax_d.set_title(f"Duty cycle per munstycke | Målpåslag {target_addon:.1f} g/m² @ {line_speed:.0f} m/min | Totalflöde {total_flow_out_l:.2f} L/min", fontsize=10)
ax_d.set_ylabel("Duty cycle [%]", fontsize=9)
ax_d.set_ylim(0, max(100, max(duty_pcts) * 1.1 if duty_pcts else 100))
ax_d.tick_params(axis='x', labelsize=7, rotation=90)
ax_d.grid(True, axis='y', linestyle=':', alpha=0.6)
ax_d.legend(loc='upper right', fontsize=8)
plt.tight_layout()
st.pyplot(fig_duty)

st.caption(
    "🔵 Ramp 1  🟠 Ramp 2  ⚪ Avstängt munstycke (0% profil)  🔴 Mättat (kräver >90% duty cycle). "
    "Beräkningen antar munstyckesflödet är angivet i ml/min (≈ g/min för vattenbaserad vätska), och "
    "att målpåslaget delas mellan de **verkliga** ramperna (angivet i sidopanelen)."
)

# Mätpunkter för mjuk graf
total_width_min = min(pos_ramp1)
total_width_max = max(pos_ramp2)
x_smooth = np.linspace(total_width_min - 300.0, total_width_max + 300.0, 1500)

y_combined = np.zeros_like(x_smooth)
y_baseline = np.zeros_like(x_smooth)
smooth_individual = {}

for n in nozzle_info:
    curve = n['flow'] * super_smooth_profile(x_smooth, x_pos=n['pos'], h_flat=half_flat, h_total=half_total)
    smooth_individual[n['id']] = curve
    y_combined += curve

    # Helt avstängda munstycken (flöde = 0) räknas bort från "standardflödet" (baslinjen),
    # så att baslinjen och den beräknade max-bredden följer vilka munstycken som faktiskt är aktiva.
    is_active = n['flow'] > 0.0
    curve_base = (1.0 if is_active else 0.0) * super_smooth_profile(x_smooth, x_pos=n['pos'], h_flat=half_flat, h_total=half_total)
    y_baseline += curve_base

active_nozzle_count = sum(1 for n in nozzle_info if n['flow'] > 0.0)
off_nozzle_count = len(nozzle_info) - active_nozzle_count

# --- BERÄKNING AV DYNAMISK MAX BREDD ---
full_cov_mask = y_baseline >= 1.98
x_full_cov = x_smooth[full_cov_mask]

if len(x_full_cov) > 0:
    dyn_start = x_full_cov[0] + oscillation_margin
    dyn_end = x_full_cov[-1] - oscillation_margin
    max_dyn_width = max(0.0, dyn_end - dyn_start)
else:
    dyn_start, dyn_end, max_dyn_width = 0.0, 0.0, 0.0

# --- BERÄKNING AV OSCILLATIONENS EFFEKT (används i huvudgrafen nedan) ---
y_baseline_shift_pos = np.zeros_like(x_smooth)
y_baseline_shift_neg = np.zeros_like(x_smooth)
for n in nozzle_info:
    is_active = n['flow'] > 0.0
    active_val = 1.0 if is_active else 0.0
    y_baseline_shift_pos += active_val * super_smooth_profile(
        x_smooth, x_pos=n['pos'] + oscillation_margin, h_flat=half_flat, h_total=half_total
    )
    y_baseline_shift_neg += active_val * super_smooth_profile(
        x_smooth, x_pos=n['pos'] - oscillation_margin, h_flat=half_flat, h_total=half_total
    )

y_worst_case = np.minimum.reduce([y_baseline, y_baseline_shift_pos, y_baseline_shift_neg])
worst_cov_mask = y_worst_case >= 1.98
x_worst_cov = x_smooth[worst_cov_mask]

if len(x_worst_cov) > 0:
    worst_start, worst_end = x_worst_cov[0], x_worst_cov[-1]
    worst_width = worst_end - worst_start
else:
    worst_start, worst_end, worst_width = 0.0, 0.0, 0.0

# --- BANBREDDSSTEG VID AVSTÄNGNING AV MUNSTYCKSPAR ---
st.subheader("✂️ Banbreddssteg vid avstängning av munstyckspar")
st.write(
    "Vid en smalare bana kan man stänga av de yttersta munstyckena parvis (ett på vänster sida "
    "och ett på höger sida samtidigt, oavsett vilken ramp de tillhör) för att undvika onödig "
    "materialförbrukning utanför tyget. Tabellen visar hur den maximala banbredden minskar för "
    "varje steg, med oscillationsmarginalen inräknad. Beräkningen utgår från nominellt 100% "
    "flöde på alla aktiva munstycken, oavsett vad reglagen ovan är satta till."
)

all_nozzles_sorted = sorted(nozzle_info, key=lambda k: k['pos'])
n_total = len(all_nozzles_sorted)
max_steps = max(0, (n_total // 2) - 1)  # lämna minst 2 munstycken aktiva i mitten

step_rows = []
for step in range(0, max_steps + 1):
    off_ids = set()
    if step > 0:
        off_ids.update(n['id'] for n in all_nozzles_sorted[:step])
        off_ids.update(n['id'] for n in all_nozzles_sorted[n_total - step:])

    y_step_baseline = np.zeros_like(x_smooth)
    for n in all_nozzles_sorted:
        flow_step = 0.0 if n['id'] in off_ids else 1.0
        y_step_baseline += flow_step * super_smooth_profile(
            x_smooth, x_pos=n['pos'], h_flat=half_flat, h_total=half_total
        )

    step_mask = y_step_baseline >= 1.98
    x_step_cov = x_smooth[step_mask]
    if len(x_step_cov) > 0:
        step_start = x_step_cov[0] + oscillation_margin
        step_end = x_step_cov[-1] - oscillation_margin
        step_width = max(0.0, step_end - step_start)
    else:
        step_width = 0.0

    active_count = n_total - len(off_ids)
    off_left = ", ".join(n['id'] for n in all_nozzles_sorted[:step]) if step > 0 else "-"
    off_right = ", ".join(n['id'] for n in all_nozzles_sorted[n_total - step:]) if step > 0 else "-"

    step_rows.append({
        'Steg (par avstängda)': step,
        'Avstängda vänster': off_left,
        'Avstängda höger': off_right,
        'Aktiva munstycken': active_count,
        'Max banbredd (mm)': round(step_width),
    })

df_steps = pd.DataFrame(step_rows)
df_steps['Minskning vs. steg 0 (mm)'] = df_steps['Max banbredd (mm)'].iloc[0] - df_steps['Max banbredd (mm)']
if df_steps['Max banbredd (mm)'].iloc[0] > 0:
    df_steps['Minskning (%)'] = (
        df_steps['Minskning vs. steg 0 (mm)'] / df_steps['Max banbredd (mm)'].iloc[0] * 100
    ).round(1)
else:
    df_steps['Minskning (%)'] = 0.0

st.dataframe(df_steps, use_container_width=True)

# Minsta antal aktiva munstycken (av den fysiska grid som finns) för att täcka den
# angivna fasta banbredden - används som info under "Max beräknad banbredd" nedan.
qualifying_steps = df_steps[df_steps['Max banbredd (mm)'] >= fixed_fabric_width]
if not qualifying_steps.empty:
    min_active_for_target = int(qualifying_steps['Aktiva munstycken'].min())
else:
    min_active_for_target = None  # även alla munstycken aktiva räcker inte

fig_steps, ax_st = plt.subplots(figsize=(10, 3.5))
ax_st.plot(df_steps['Steg (par avstängda)'], df_steps['Max banbredd (mm)'], marker='o', color='darkblue')
for _, row in df_steps.iterrows():
    ax_st.annotate(
        f"{row['Max banbredd (mm)']:.0f}", (row['Steg (par avstängda)'], row['Max banbredd (mm)']),
        textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8
    )
ax_st.set_xlabel('Antal munstyckspar avstängda', fontsize=9)
ax_st.set_ylabel('Max banbredd (mm)', fontsize=9)
ax_st.set_title('Max banbredd per avstängningssteg', fontsize=10)
ax_st.set_xticks(df_steps['Steg (par avstängda)'])
ax_st.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
st.pyplot(fig_steps)

# --- BERÄKNING AV JUSTERAT OMRÅDE OCH PROCENTUELL MINSKNING ---
ramp_center = fabric_center

fabric_mask = (x_smooth >= fixed_start) & (x_smooth <= fixed_end)
x_fabric = x_smooth[fabric_mask]
y_fabric = y_combined[fabric_mask]
y_fabric_baseline = y_baseline[fabric_mask]

# Mask för justerade punkter på tyget
adjusted_mask = np.abs(y_fabric - y_fabric_baseline) > 0.005 
dx = x_smooth[1] - x_smooth[0]

# Uppdelning Vänster vs Höger sida om mitten
left_side_mask = adjusted_mask & (x_fabric <= ramp_center)
right_side_mask = adjusted_mask & (x_fabric > ramp_center)

# Bredd per zon (mm) med exakt avrundningslogik
adj_width_left = round(np.sum(left_side_mask) * dx)
adj_width_right = round(np.sum(right_side_mask) * dx)
adj_width_total = adj_width_left + adj_width_right

# Beräkning av snittförändring (%)
def calc_pct_change(y_act, y_base, mask):
    if np.sum(mask) == 0 or np.sum(y_base[mask]) == 0:
        return 0.0
    sum_base = np.sum(y_base[mask])
    sum_act = np.sum(y_act[mask])
    return ((sum_act - sum_base) / sum_base) * 100.0

pct_total = calc_pct_change(y_fabric, y_fabric_baseline, adjusted_mask)
pct_left = calc_pct_change(y_fabric, y_fabric_baseline, left_side_mask)
pct_right = calc_pct_change(y_fabric, y_fabric_baseline, right_side_mask)

# Flödesändringen (%) översätts direkt till pickup, eftersom duty cycle (och därmed
# vätskemängden) skalar linjärt med flödesreglaget: lokal pickup = mål-pickup × (flöde/baslinje)
pickup_total = pickup_pct * (1.0 + pct_total / 100.0)
pickup_left = pickup_pct * (1.0 + pct_left / 100.0)
pickup_right = pickup_pct * (1.0 + pct_right / 100.0)
addon_total = target_addon * (1.0 + pct_total / 100.0)
addon_left = target_addon * (1.0 + pct_left / 100.0)
addon_right = target_addon * (1.0 + pct_right / 100.0)

# --- PRESENTATION AV METRIKER ---
st.subheader("📏 Banbreddsanalys (Profilering)")

if off_nozzle_count > 0:
    st.info(f"ℹ️ {off_nozzle_count} munstycke(n) är helt avstängda (flöde = 0%) — max banbredd och oscillationsberäkningen nedan är uppdaterade utifrån de {active_nozzle_count} kvarvarande aktiva munstyckena.")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Fast tygbredd (mål)", f"{fixed_fabric_width:.0f} mm")

c2.metric(
    "Max beräknad banbredd", 
    f"{max_dyn_width:.0f} mm",
    delta=None if off_nozzle_count == 0 else f"{active_nozzle_count}/{len(nozzle_info)} munstycken aktiva",
    delta_color="off",
    help="Den maximala banbredden som just nu går att täcka, baserat på vilka munstycken som faktiskt är "
         "aktiva (avstängda munstycken, flöde=0%, räknas bort) och angivna marginaler."
)
with c2:
    if min_active_for_target is not None:
        st.caption(f"📐 Kräver minst **{min_active_for_target}** aktiva munstycken (av {n_total}) för {fixed_fabric_width:.0f} mm")
    else:
        st.caption(f"📐 Även alla {n_total} munstycken räcker inte till {fixed_fabric_width:.0f} mm — öka antalet i sidopanelen")

if max_dyn_width < fixed_fabric_width - 0.5:
    st.warning(
        f"⚠️ Med nuvarande avstängda munstycken räcker inte täckningen till hela den fasta "
        f"tygbredden ({fixed_fabric_width:.0f} mm) — max banbredd är nu **{max_dyn_width:.0f} mm** "
        f"(garanterat med oscillation: **{worst_width:.0f} mm**)."
    )

if adj_width_total > 0:
    c3.metric(
        "Totalt justerad bredd", 
        f"{adj_width_total:.0f} mm", 
        delta=f"{pickup_total:.0f}% pickup (mål {pickup_pct:.0f}%)",
        delta_color="off"
    )
    with c3:
        st.caption(f"≈{addon_total:.0f} g/m² vätska ({pct_total:+.1f}% flöde mot standard)")
else:
    c3.metric("Totalt justerad bredd", "0 mm", delta="Standardflöde", delta_color="off")

if adj_width_left > 0:
    c4.metric(
        "Vänster sida", 
        f"{adj_width_left:.0f} mm", 
        delta=f"{pickup_left:.0f}% pickup (mål {pickup_pct:.0f}%)",
        delta_color="off"
    )
    with c4:
        st.caption(f"≈{addon_left:.0f} g/m² vätska ({pct_left:+.1f}% flöde mot standard)")
else:
    c4.metric("Vänster sida", "0 mm", delta="Ej justerad", delta_color="off")

if adj_width_right > 0:
    c5.metric(
        "Höger sida", 
        f"{adj_width_right:.0f} mm", 
        delta=f"{pickup_right:.0f}% pickup (mål {pickup_pct:.0f}%)",
        delta_color="off"
    )
    with c5:
        st.caption(f"≈{addon_right:.0f} g/m² vätska ({pct_right:+.1f}% flöde mot standard)")
else:
    c5.metric("Höger sida", "0 mm", delta="Ej justerad", delta_color="off")



# --- GRAFISK PRESENTATION ---
st.subheader("📊 Visualisering av flödesprofilering & oscillation")
st.write(
    "Grafen visar både din aktuella flödesjustering och hur oscillationen (rampens rörelse "
    "± marginalen) påverkar täckningen. De röda/gröna tunna linjerna visar standardflödet vid "
    "ramparnas ytterlägen, och det lila området visar den garanterade täckningen (sämsta "
    "tänkbara fallet) oavsett var i oscillationscykeln ramperna befinner sig just nu."
)

fig, ax = plt.subplots(figsize=(14, 6))

ax.axvspan(fixed_start, fixed_end, color='gray', alpha=0.1, label=f'Fast tygbredd ({fixed_fabric_width:.0f} mm)')
ax.axvline(fixed_start, color='darkred', linestyle='-', linewidth=2, label=f'Vänster tygkant ({fixed_start:.0f} mm)')
ax.axvline(fixed_end, color='darkred', linestyle='-', linewidth=2, label=f'Höger tygkant ({fixed_end:.0f} mm)')

ax.axvline(fabric_center, color='black', linestyle='-.', linewidth=1.5, label=f'Tygets centrum ({fabric_center:.0f} mm)')

ax.plot(x_smooth, y_baseline, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Standardflöde (100% på aktiva ventiler)')
ax.plot(x_smooth, y_baseline_shift_pos, color='tab:red', linewidth=1.0, alpha=0.6, label=f'Ramp förskjuten +{oscillation_margin:.0f} mm (oscillation)')
ax.plot(x_smooth, y_baseline_shift_neg, color='tab:green', linewidth=1.0, alpha=0.6, label=f'Ramp förskjuten -{oscillation_margin:.0f} mm (oscillation)')
ax.fill_between(
    x_smooth, 0, y_worst_case, where=worst_cov_mask, color='purple', alpha=0.15,
    label=f'Garanterad täckning oavsett oscillationsfas ({worst_width:.0f} mm)'
)
if worst_width > 0:
    ax.axvline(worst_start, color='purple', linestyle=':', linewidth=1.5)
    ax.axvline(worst_end, color='purple', linestyle=':', linewidth=1.5)

for n in nozzle_info:
    color = 'tab:blue' if n['ramp'] == 1 else 'tab:orange'
    style = '--' if n['ramp'] == 1 else ':'
    ax.plot(x_smooth, smooth_individual[n['id']], linestyle=style, color=color, alpha=0.25)

ax.plot(x_smooth, y_combined, color='darkblue', linewidth=3.0, label='Aktuell flödesprofil')

if len(x_fabric) > 0 and np.any(adjusted_mask):
    ax.fill_between(
        x_fabric, y_fabric_baseline, y_fabric,
        where=adjusted_mask, color='gold', alpha=0.75, zorder=6,
        edgecolor='darkorange', linewidth=0.8,
        label=f'Justerat område ({adj_width_total:.0f} mm)'
    )

y_max = max(2.5, np.max(y_combined) * 1.1)
offset_text = cc_distance / 4.0
ax.scatter(pos_ramp1, [y_max * 0.95] * n_nozzles_per_ramp, color='tab:blue', marker='v', s=80, zorder=5, label=f'Munstycken Ramp 1 (-{offset_text:.0f} mm från centrum)')
ax.scatter(pos_ramp2, [y_max * 0.95] * n_nozzles_per_ramp, color='tab:orange', marker='v', s=80, zorder=5, label=f'Munstycken Ramp 2 (+{offset_text:.0f} mm från centrum)')

ax.set_title(f'Flödesprofil över tygbredd ({fixed_fabric_width:.0f} mm) | C-C = {cc_distance:.0f} mm', fontsize=11)
ax.set_xlabel('Position över tyget [mm]', fontsize=10)
ax.set_ylabel('Relativt flöde', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.7)
ax.set_ylim(0, y_max)

# --- HORISONTELL MARKÖR & DYNAMISKA MÄTPUNKTER ---
# Beräkna marginalen så att tabellen GARANTERAT når 0.0 i båda ändar
margin = half_total + 60.0  
x_table = np.arange(round(total_width_min - margin, -1), round(total_width_max + margin + 1.0, -1), 20.0)
table_start = x_table[0]
table_end = x_table[-1]

y_pos = 0.05  # Placeras precis ovanför bottenlinjen

# Horisontell linje med ändhakar
ax.plot([table_start, table_end], [y_pos, y_pos], color='purple', linewidth=2, label=f'Tabellens intervall ({table_start:.0f} till {table_end:.0f} mm)')
ax.plot([table_start, table_start], [0.0, 0.12], color='purple', linewidth=2)  # Vänster ändhake |
ax.plot([table_end, table_end], [0.0, 0.12], color='purple', linewidth=2)      # Höger ändhake |

# --- TECKENFÖRKLARING & UTRITNING ---
ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1), fontsize=8)
plt.tight_layout()

st.pyplot(fig)

st.caption(
    f"💡 Den lila zonen (**{worst_width:.0f} mm**) visar täckningen som är garanterad oavsett "
    f"oscillationsfas, beräknat utifrån hur flankernas form faktiskt förändras vid förskjutning. "
    f"Det kan jämföras med **{max_dyn_width:.0f} mm** från den enklare metoden i mätvärdena ovan "
    f"(rak avdragning av marginalen från plattåkanterna)."
)

# --- 3. TABELLPRESENTATION ---
st.subheader("📋 Numeriska värden i tabellform (var 20:e mm)")

combined_table_flow = np.zeros_like(x_table)
nozzle_columns = {}

# Beräkna alla enskilda munstycken och det kombinerade flödet
for n in nozzle_info_sorted:
    t_curve = n['flow'] * super_smooth_profile(x_table, n['pos'], h_flat=half_flat, h_total=half_total)
    nozzle_columns[f"{n['id']} ({n['pos']:.0f}mm)"] = np.round(t_curve, 2)
    combined_table_flow += t_curve

# Bygg upp tabellen i önskad kolumnordning
table_data = {
    'Position (mm)': np.round(x_table, 1),
    'Kombinerat flöde': np.round(combined_table_flow, 2),
    **nozzle_columns  # Lägger till de enskilda munstyckena efter kombinerat flöde
}

df = pd.DataFrame(table_data)

st.dataframe(df, use_container_width=True)
