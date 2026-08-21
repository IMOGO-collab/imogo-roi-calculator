import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Sidans layout
st.set_page_config(page_title="Munstycksanalys - Banbreddsanalys", layout="wide")

st.title("🎛️ Dynamisk Munstycksanalys med Fast Banbredd")
st.write("Jämför den dynamiskt beräknade täckningen mot en **fast tygbredd**. Se direkt i grafen och mätvärdena hur mycket av tyget som påverkas när flödena justeras.")

# --- SIDEBAR: REGLAGE FÖR GEOMETRI & FLÖDEN ---
st.sidebar.header("Tygkonfiguration")
fixed_fabric_width = st.sidebar.number_input(
    "Fast banbredd / Tygbredd [mm]", 
    value=2400.0, step=50.0
)

st.sidebar.header("Geometri & Marginaler")
# Uppdaterad default till C-C 360 mm
cc_distance = st.sidebar.slider(
    "C-C Avstånd mellan munstycken [mm]", 
    min_value=250.0, max_value=500.0, value=360.0, step=1.0
)

oscillation_margin = st.sidebar.number_input(
    "Oscilleringsmarginal per sida [mm]", 
    value=35.0, step=5.0
)

offset = cc_distance / 2.0

st.sidebar.header("Flöden per munstycke (%)")

# Nummerordning: Udda i Ramp 1, Jämna i Ramp 2
ramp1_ids = [1, 3, 5, 7, 9, 11, 13, 15]
ramp2_ids = [2, 4, 6, 8, 10, 12, 14, 16]

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

# --- SUPERMJUK PROFIL FÖR ETT MUNSTYCKE (Anpassad för C-C = 360 mm) ---
def super_smooth_profile(x, x_pos=0.0):
    dist = np.abs(x - x_pos)
    # Summan av half_flat och half_total sätts till exakt 360 mm för 100% täckning i överlappet
    half_flat = 120.0   # Platt kärna i mitten (mm)
    half_total = 240.0  # Total halvbredd per munstycke (mm)
    
    profile = np.zeros_like(x, dtype=float)
    profile[dist <= half_flat] = 1.0
    
    taper_mask = (dist > half_flat) & (dist <= half_total)
    t = (dist[taper_mask] - half_flat) / (half_total - half_flat)
    
    smooth_step = 6 * t**5 - 15 * t**4 + 10 * t**3
    profile[taper_mask] = 1.0 - smooth_step
    
    return profile

# Positioner för alla 16 munstycken
pos_ramp1 = [i * cc_distance for i in range(8)]
pos_ramp2 = [i * cc_distance + offset for i in range(8)]

nozzle_info = []
for i in range(8):
    nozzle_info.append({'id': f"R1-M{ramp1_ids[i]}", 'pos': pos_ramp1[i], 'flow': ramp1_flows[i], 'ramp': 1})
for i in range(8):
    nozzle_info.append({'id': f"R2-M{ramp2_ids[i]}", 'pos': pos_ramp2[i], 'flow': ramp2_flows[i], 'ramp': 2})

nozzle_info_sorted = sorted(nozzle_info, key=lambda k: k['pos'])

# Mätpunkter för mjuk graf
total_width_max = max(pos_ramp2)
x_smooth = np.linspace(-300.0, total_width_max + 300.0, 1500)

smooth_individual = {}
y_combined = np.zeros_like(x_smooth)

for n in nozzle_info:
    curve = n['flow'] * super_smooth_profile(x_smooth, x_pos=n['pos'])
    smooth_individual[n['id']] = curve
    y_combined += curve

# --- BERÄKNING AV DYNAMISK MAX BREDD ---
max_flow_val = 2.0  # Nominellt target-flöde
full_cov_mask = y_combined >= (max_flow_val - 0.02)
x_full_cov = x_smooth[full_cov_mask]

if len(x_full_cov) > 0:
    dyn_start = x_full_cov[0] + oscillation_margin
    dyn_end = x_full_cov[-1] - oscillation_margin
    max_dyn_width = max(0.0, dyn_end - dyn_start)
else:
    dyn_start, dyn_end, max_dyn_width = 0.0, 0.0, 0.0

# --- BERÄKNING FÖR FAST BANBREDD ---
ramp_center = (min(pos_ramp1) + max(pos_ramp2)) / 2.0
fixed_start = ramp_center - (fixed_fabric_width / 2.0)
fixed_end = ramp_center + (fixed_fabric_width / 2.0)

# Utvärdera flödet på det fasta tyget
fabric_mask = (x_smooth >= fixed_start) & (x_smooth <= fixed_end)
x_fabric = x_smooth[fabric_mask]
y_fabric = y_combined[fabric_mask]

# Hitta områden på tyget där flödet viker av från nominellt (2.0) med mer än 2%
defect_mask = np.abs(y_fabric - max_flow_val) > 0.04
dx = x_smooth[1] - x_smooth[0]
affected_width_mm = np.sum(defect_mask) * dx
ok_fabric_percentage = max(0.0, 100.0 * (1.0 - (affected_width_mm / fixed_fabric_width))) if fixed_fabric_width > 0 else 0.0

# --- PRESENTATION AV METRIKER ---
st.subheader("📏 Banbreddsanalys")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Fast tygbredd", f"{fixed_fabric_width:.0f} mm")
c2.metric("Godkänd tygyta", f"{ok_fabric_percentage:.1f} %")
c3.metric(
    "Påverkad/Defekt bredd", 
    f"{affected_width_mm:.0f} mm", 
    delta=f"-{affected_width_mm:.0f} mm" if affected_width_mm > 0 else "Perfekt täckning", 
    delta_color="inverse"
)
c4.metric("Teoretisk maxbredd", f"{max_dyn_width:.0f} mm")

# --- GRAFISK PRESENTATION ---
st.subheader("📊 Visualisering av flödespåverkan på tyget")

fig, ax = plt.subplots(figsize=(14, 6))

# 1. Fast tygbredd (Röd/Grå inramning)
ax.axvspan(fixed_start, fixed_end, color='gray', alpha=0.1, label=f'Fast tygbredd ({fixed_fabric_width:.0f} mm)')
ax.axvline(fixed_start, color='darkred', linestyle='-', linewidth=2, label=f'Tygkant ({fixed_start:.0f} mm)')
ax.axvline(fixed_end, color='darkred', linestyle='-', linewidth=2, label=f'Tygkant ({fixed_end:.0f} mm)')

# 2. Röd skuggning där tyget har flödesavvikelse
if len(x_fabric) > 0 and np.any(defect_mask):
    ax.fill_between(
        x_fabric, 0, y_fabric, 
        where=defect_mask, color='red', alpha=0.3, 
        label=f'Avvikande flöde på tyg ({affected_width_mm:.0f} mm)'
    )

# 3. Enskilda munstycken
for n in nozzle_info:
    color = 'tab:blue' if n['ramp'] == 1 else 'tab:orange'
    style = '--' if n['ramp'] == 1 else ':'
    ax.plot(x_smooth, smooth_individual[n['id']], linestyle=style, color=color, alpha=0.25)

# 4. Totalkurva
ax.plot(x_smooth, y_combined, color='darkblue', linewidth=3.0, label='Kombinerat totalflöde')

ax.set_title(f'Flöde över fast tygbredd ({fixed_fabric_width:.0f} mm) | C-C = {cc_distance} mm | Påverkad bredd: {affected_width_mm:.0f} mm', fontsize=11)
ax.set_xlabel('Position längs rampen [mm]', fontsize=10)
ax.set_ylabel('Relativt flöde', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.7)
ax.set_ylim(0, max(2.5, np.max(y_combined) * 1.1))

ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1), fontsize=8)
plt.tight_layout()

st.pyplot(fig)

# --- TABELLPRESENTATION ---
st.subheader("📋 Numeriska värden i tabellform (var 20:e mm)")

x_table = np.arange(-200.0, total_width_max + 201.0, 20.0)
table_data = {'Position (mm)': np.round(x_table, 1)}
combined_table_flow = np.zeros_like(x_table)

for n in nozzle_info_sorted:
    t_curve = n['flow'] * super_smooth_profile(x_table, n['pos'])
    table_data[f"{n['id']} ({n['pos']:.0f}mm)"] = np.round(t_curve, 2)
    combined_table_flow += t_curve

table_data['Kombinerat flöde'] = np.round(combined_table_flow, 2)
df = pd.DataFrame(table_data)

st.dataframe(df, use_container_width=True)