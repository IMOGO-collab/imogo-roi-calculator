import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Sidans layout
st.set_page_config(page_title="Munstycksanalys - Profilering", layout="wide")

st.title("🎛️ Dynamisk Munstycksanalys (Profilering)")
st.write("Använd reglagen för att medvetet justera flödet och kompensera för tygvariationer. Grafen och mätvärdena visar exakt **vilken del av tyget som påverkas** av dina justeringar.")

# --- SIDEBAR: REGLAGE FÖR GEOMETRI & FLÖDEN ---
st.sidebar.header("Tygkonfiguration")
fixed_fabric_width = st.sidebar.number_input(
    "Fast banbredd / Tygbredd [mm]", 
    value=2400.0, step=50.0
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

st.sidebar.header("Flöden per munstycke (%)")

ramp1_ids = [1, 3, 5, 7, 9, 11, 13, 15]
ramp2_ids = [2, 4, 6, 8, 10, 12, 14, 16]

# --- RESET-KNAPP FÖR MUNSTYCKEN ---
def reset_nozzles():
    for n_id in ramp1_ids + ramp2_ids:
        st.session_state[f"nozzle_slider_{n_id}"] = 100

st.sidebar.button("🔄 Återställ alla ventiler till 100%", on_click=reset_nozzles, use_container_width=True)

ramp1_flows = []
with st.sidebar.expander("Ramp 1 (Munstycke 1, 3, 5, 7, 9, 11, 13, 15)", expanded=True):
    for n_id in ramp1_ids:
        flow_val = st.slider(
            f"Munstycke {n_id}", 
            min_value=0, max_value=150, value=100, step=5,
            key=f"nozzle_slider_{n_id}"
        ) / 100.0
        ramp1_flows.append(flow_val)

ramp2_flows = []
with st.sidebar.expander("Ramp 2 - Förskjuten (Munstycke 2, 4, 6, 8, 10, 12, 14, 16)", expanded=False):
    for n_id in ramp2_ids:
        flow_val = st.slider(
            f"Munstycke {n_id}", 
            min_value=0, max_value=150, value=100, step=5,
            key=f"nozzle_slider_{n_id}"
        ) / 100.0
        ramp2_flows.append(flow_val)

# --- SUPERMJUK PROFIL FÖR ETT MUNSTYCKE ---
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

# --- POSITIONERING: Tyget börjar på 0 ---
fixed_start = 0.0
fixed_end = fixed_fabric_width
fabric_center = fixed_fabric_width / 2.0

ramp1_center = fabric_center - (cc_distance / 4.0)
ramp2_center = fabric_center + (cc_distance / 4.0)

pos_ramp1 = [ramp1_center - 3.5 * cc_distance + i * cc_distance for i in range(8)]
pos_ramp2 = [ramp2_center - 3.5 * cc_distance + i * cc_distance for i in range(8)]

nozzle_info = []
for i in range(8):
    nozzle_info.append({'id': f"R1-M{ramp1_ids[i]}", 'pos': pos_ramp1[i], 'flow': ramp1_flows[i], 'ramp': 1})
for i in range(8):
    nozzle_info.append({'id': f"R2-M{ramp2_ids[i]}", 'pos': pos_ramp2[i], 'flow': ramp2_flows[i], 'ramp': 2})

nozzle_info_sorted = sorted(nozzle_info, key=lambda k: k['pos'])

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
    
    curve_base = 1.0 * super_smooth_profile(x_smooth, x_pos=n['pos'], h_flat=half_flat, h_total=half_total)
    y_baseline += curve_base

# --- BERÄKNING AV DYNAMISK MAX BREDD ---
full_cov_mask = y_baseline >= 1.98
x_full_cov = x_smooth[full_cov_mask]

if len(x_full_cov) > 0:
    dyn_start = x_full_cov[0] + oscillation_margin
    dyn_end = x_full_cov[-1] - oscillation_margin
    max_dyn_width = max(0.0, dyn_end - dyn_start)
else:
    dyn_start, dyn_end, max_dyn_width = 0.0, 0.0, 0.0

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

# --- PRESENTATION AV METRIKER ---
st.subheader("📏 Banbreddsanalys (Profilering)")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Fast tygbredd", f"{fixed_fabric_width:.0f} mm")

c2.metric(
    "Max beräknad banbredd", 
    f"{max_dyn_width:.0f} mm",
    help="Den maximala banbredden maskinen kan täcka baserat på standardflödet och angivna marginaler."
)

if adj_width_total > 0:
    c3.metric(
        "Totalt justerad bredd", 
        f"{adj_width_total:.0f} mm", 
        delta=f"{pct_total:+.1f}% snittflöde", 
        delta_color="off"
    )
else:
    c3.metric("Totalt justerad bredd", "0 mm", delta="Standardflöde", delta_color="off")

if adj_width_left > 0:
    c4.metric(
        "Vänster sida", 
        f"{adj_width_left:.0f} mm", 
        delta=f"{pct_left:+.1f}% snittflöde", 
        delta_color="off"
    )
else:
    c4.metric("Vänster sida", "0 mm", delta="Ej justerad", delta_color="off")

if adj_width_right > 0:
    c5.metric(
        "Höger sida", 
        f"{adj_width_right:.0f} mm", 
        delta=f"{pct_right:+.1f}% snittflöde", 
        delta_color="off"
    )
else:
    c5.metric("Höger sida", "0 mm", delta="Ej justerad", delta_color="off")

# --- GRAFISK PRESENTATION ---
st.subheader("📊 Visualisering av flödesprofilering")

fig, ax = plt.subplots(figsize=(14, 6))

ax.axvspan(fixed_start, fixed_end, color='gray', alpha=0.1, label=f'Fast tygbredd ({fixed_fabric_width:.0f} mm)')
ax.axvline(fixed_start, color='darkred', linestyle='-', linewidth=2, label=f'Vänster tygkant ({fixed_start:.0f} mm)')
ax.axvline(fixed_end, color='darkred', linestyle='-', linewidth=2, label=f'Höger tygkant ({fixed_end:.0f} mm)')

ax.axvline(fabric_center, color='black', linestyle='-.', linewidth=1.5, label=f'Tygets centrum ({fabric_center:.0f} mm)')

ax.plot(x_smooth, y_baseline, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Standardflöde (100% på alla ventiler)')

if len(x_fabric) > 0 and np.any(adjusted_mask):
    ax.fill_between(
        x_fabric, y_fabric_baseline, y_fabric, 
        where=adjusted_mask, color='orange', alpha=0.4, 
        label=f'Justerat område ({adj_width_total:.0f} mm)'
    )

for n in nozzle_info:
    color = 'tab:blue' if n['ramp'] == 1 else 'tab:orange'
    style = '--' if n['ramp'] == 1 else ':'
    ax.plot(x_smooth, smooth_individual[n['id']], linestyle=style, color=color, alpha=0.25)

ax.plot(x_smooth, y_combined, color='darkblue', linewidth=3.0, label='Aktuell flödesprofil')

y_max = max(2.5, np.max(y_combined) * 1.1)
offset_text = cc_distance / 4.0
ax.scatter(pos_ramp1, [y_max * 0.95]*8, color='tab:blue', marker='v', s=80, zorder=5, label=f'Munstycken Ramp 1 (-{offset_text:.0f} mm från centrum)')
ax.scatter(pos_ramp2, [y_max * 0.95]*8, color='tab:orange', marker='v', s=80, zorder=5, label=f'Munstycken Ramp 2 (+{offset_text:.0f} mm från centrum)')

ax.set_title(f'Flödesprofil över tygbredd ({fixed_fabric_width:.0f} mm) | C-C = {cc_distance:.0f} mm', fontsize=11)
ax.set_xlabel('Position över tyget [mm]', fontsize=10)
ax.set_ylabel('Relativt flöde', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.7)
ax.set_ylim(0, y_max)

# --- HORISONTELL MARKÖR LÄNGS X-AXELN ---
x_table = np.arange(round(total_width_min - 200.0, -1), round(total_width_max + 201.0, -1), 20.0)
table_start = x_table[0]
table_end = x_table[-1]

y_pos = 0.05  # Placeras precis ovanför bottenlinjen

# Horisontell linje med ändhakar (bracket |---|)
ax.plot([table_start, table_end], [y_pos, y_pos], color='purple', linewidth=2, label=f'Tabellens intervall ({table_start:.0f} till {table_end:.0f} mm)')
ax.plot([table_start, table_start], [0.0, 0.12], color='purple', linewidth=2)  # Vänster ändhake |
ax.plot([table_end, table_end], [0.0, 0.12], color='purple', linewidth=2)      # Höger ändhake |

ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1), fontsize=8)
plt.tight_layout()

# --- RITA UT GRAFEN ---
st.pyplot(fig)


# --- 3. TABELLPRESENTATION ---
st.subheader("📋 Numeriska värden i tabellform (var 20:e mm)")

table_data = {'Position (mm)': np.round(x_table, 1)}
combined_table_flow = np.zeros_like(x_table)

for n in nozzle_info_sorted:
    t_curve = n['flow'] * super_smooth_profile(x_table, n['pos'], h_flat=half_flat, h_total=half_total)
    table_data[f"{n['id']} ({n['pos']:.0f}mm)"] = np.round(t_curve, 2)
    combined_table_flow += t_curve

table_data['Kombinerat flöde'] = np.round(combined_table_flow, 2)
df = pd.DataFrame(table_data)

st.dataframe(df, use_container_width=True)
