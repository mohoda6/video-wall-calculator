import sys
# sys.path.append(r"C:\Users\asus\AppData\Roaming\Python\Python313\site-packages")

import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime


def gregorian_to_jalali(gy, gm, gd):
    """تبدیل تاریخ میلادی به هجری شمسی"""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if (gm > 2):
        gy2 = gy + 1
    else:
        gy2 = gy

    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 1
    days += g_d_m[gm - 1] + gd

    if (gm > 2):
        if (((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)) == False):
            days -= 1

    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if (days < 186):
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)

    return jy, jm, jd

def get_jalali_date():
    """دریافت تاریخ هجری شمسی فعلی"""
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    return f"{jy}/{jm:02d}/{jd:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"

def videowall_calc(
    wall_width_cm,
    wall_height_cm,
    dot_pitch_mm=1.8,
    power_per_module_w=23,
    receiving_card_capacity_px=512*512,
    psu_watt=60
):
    module_width_cm = 32
    module_height_cm = 16

    wall_w_mm = wall_width_cm * 10
    wall_h_mm = wall_height_cm * 10
    module_w_mm = module_width_cm * 10
    module_h_mm = module_height_cm * 10

    modules_x = round(wall_w_mm / module_w_mm)
    modules_y_round = round(wall_h_mm / module_h_mm)

    px_per_module_x = round(module_w_mm / dot_pitch_mm)
    px_per_module_y = round(module_h_mm / dot_pitch_mm)
    px_per_module = px_per_module_x * px_per_module_y

    width_px = modules_x * px_per_module_x
    height_px_round = modules_y_round * px_per_module_y

    total_px_round = width_px * height_px_round

    cards_round = round(total_px_round / receiving_card_capacity_px)

    total_modules_round = modules_x * modules_y_round

    total_power_round = total_modules_round * power_per_module_w

    psu_count_round = round(total_power_round / psu_watt)

    return {
        "modules_x": modules_x,
        "modules_y_round": modules_y_round,
        "px_per_module_x": px_per_module_x,
        "px_per_module_y": px_per_module_y,
        "px_per_module_total": px_per_module,
        "resolution_round": (width_px, height_px_round),
        "total_pixels_round": total_px_round,
        "receiving_cards_round": cards_round,
        "total_modules_round": total_modules_round,
        "total_power_w_round": total_power_round,
        "psu_60w_round": psu_count_round
    }

def optimize_layout(modules_x, modules_y, block_w, block_h, max_size):
    blocks = []
    grid = np.zeros((modules_y, modules_x), dtype=int)
    card_id = 1

    y = 0
    while y + block_h <= modules_y:
        x = 0
        while x + block_w <= modules_x:
            if np.all(grid[y:y+block_h, x:x+block_w] == 0):
                blocks.append((x, y, block_w, block_h, card_id))
                grid[y:y+block_h, x:x+block_w] = card_id
                card_id += 1
            x += block_w
        y += block_h

    user_max_block_size = block_w * block_h

    for h in range(user_max_block_size, 0, -1):
        for w in range(user_max_block_size, 0, -1):
            if w * h > user_max_block_size:
                continue
            y = 0
            while y < modules_y:
                x = 0
                while x < modules_x:
                    if grid[y, x] == 0:
                        can_place = True
                        for dy in range(h):
                            for dx in range(w):
                                if y + dy >= modules_y or x + dx >= modules_x or grid[y + dy, x + dx] != 0:
                                    can_place = False
                                    break
                            if not can_place:
                                break
                        if can_place:
                            blocks.append((x, y, w, h, card_id))
                            for dy in range(h):
                                for dx in range(w):
                                    grid[y + dy, x + dx] = card_id
                            card_id += 1
                            x += w
                        else:
                            x += 1
                    else:
                        x += 1
                y += 1

    return blocks, grid

def draw_module_layout(modules_x, modules_y, blocks, grid):
    fig, ax = plt.subplots(figsize=(modules_x * 0.6, modules_y * 0.4))

    colors = [
        '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E',
        '#BC4749', '#2A9D8F', '#E76F51', '#F4A261', '#E9C46A',
        '#264653', '#6B5B95', '#88498F', '#C8B8DB', '#E5989B',
        '#D4A5A5', '#9A8C98', '#C9ADA7', '#9A8B7A', '#B4A582',
        '#FFB703', '#FB8500', '#8ECAE6', '#219EBC', '#023047',
        '#FFB703', '#FB8500', '#37B7C3', '#048A81', '#54B3B0',
        '#FFC857', '#E5323B', '#42A4BF', '#1D7874', '#14919B'
    ]

    for y in range(modules_y):
        for x in range(modules_x):
            card_id = grid[y, x]
            color = colors[(card_id - 1) % len(colors)]
            rect = patches.Rectangle(
                (x * 32, (modules_y - 1 - y) * 16),
                32, 16,
                linewidth=1.5,
                edgecolor='#333333',
                facecolor=color,
                alpha=0.85
            )
            ax.add_patch(rect)
            ax.text(
                x * 32 + 16, (modules_y - 1 - y) * 16 + 8,
                str(card_id),
                ha='center', va='center',
                fontsize=8, fontweight='bold', color='white'
            )

    for i in range(modules_x):
        ax.text(i * 32 + 16, -5, str(i + 1), ha='center', va='top', fontsize=9, color='#555555', fontweight='bold')
    for j in range(modules_y):
        ax.text(-5, (modules_y - 1 - j) * 16 + 8, str(j + 1), ha='right', va='center', fontsize=9, color='#555555', fontweight='bold')

    ax.set_xlim(-10, modules_x * 32)
    ax.set_ylim(-10, modules_y * 16)
    ax.set_title(f'{modules_x} × {modules_y} ماژول', fontsize=14, fontweight='bold', pad=15)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    return fig

def get_stats_from_grid(grid):
    """استخراج اطلاعات از گرید"""
    unique_cards = np.unique(grid)
    cards_used = len(unique_cards)
    total_modules = grid.size

    card_counts = {}
    for card in unique_cards:
        card_counts[card] = np.sum(grid == card)

    return {
        'cards_used': cards_used,
        'total_modules': total_modules,
        'card_counts': card_counts
    }

@st.cache_data
def get_default_prices():
    default_controller_prices = {}
    default_controller_units = {}
    for name in CONTROLLERS.keys():
        default_controller_prices[name] = 100.0
        default_controller_units[name] = "ریال"

    return {
        "module": 100.0,
        "receiver_card": 200.0,
        "power_supply_60w": 50.0,
        "structure": 100.0,  # ✅ این الان قیمت هر متر مربع هست
        "hdmi_cable": 100.0,
        "cable_magnet": 100.0,
        "module_unit": "ریال",
        "receiver_unit": "ریال",
        "power_unit": "ریال",
        "structure_unit": "ریال",
        "hdmi_cable_unit": "ریال",
        "cable_magnet_unit": "ریال",
        "controller_prices": default_controller_prices,
        "controller_units": default_controller_units
    }

def format_number(amount):
    """فرمت کردن اعداد با جداکننده سه رقمی"""
    if amount == 0:
        return "0"
    amount_int = int(amount)
    formatted = f"{amount_int:,}".replace(",", ".")
    return formatted

def format_currency(amount):
    """فرمت کردن اعداد با جداکننده سه رقمی و واحد ریال"""
    if amount == 0:
        return "0 ریال"
    amount_int = int(amount)
    formatted = f"{amount_int:,}".replace(",", ".")
    return f"{formatted} ریال"

def show_results_and_edit():
    """نمایش نتایج و فرم ویرایش"""
    # --- خواندن عرض و ارتفاع از session_state ---
    wall_width_cm = st.session_state.wall_width_cm
    wall_height_cm = st.session_state.wall_height_cm

    stats = get_stats_from_grid(st.session_state.module_grid)
    cards_needed = stats['cards_used']
    total_modules = stats['total_modules']

    psu_count = int(np.ceil(total_modules / 6))

    px_per_module_x = round(320 / dot_pitch)
    px_per_module_y = round(160 / dot_pitch)
    resolution_x = modules_x * px_per_module_x
    resolution_y = modules_y_round * px_per_module_y
    total_resolution = resolution_x * resolution_y
    module_resolution = px_per_module_x * px_per_module_y

    prices = st.session_state.get("prices", get_default_prices())

    def convert_to_rial(price, unit, dollar_rate):
        if unit == "دلار":
            return price * dollar_rate
        else:
            return price

    dollar_rate = st.session_state.get("dollar_rate", 0)

    module_cost = total_modules * convert_to_rial(prices["module"], prices["module_unit"], dollar_rate)
    receiver_cost = cards_needed * convert_to_rial(prices["receiver_card"], prices["receiver_unit"], dollar_rate)
    power_cost = psu_count * convert_to_rial(prices["power_supply_60w"], prices["power_unit"], dollar_rate)

    controller_info = st.session_state.get("selected_controller_info", {})
    selected_controller_name = controller_info.get("name", "")

    controller_price = 0.0
    controller_unit = "ریال"
    if selected_controller_name and selected_controller_name in prices["controller_prices"]:
        controller_price = prices["controller_prices"][selected_controller_name]
        controller_unit = prices["controller_units"].get(selected_controller_name, "ریال")

    controller_cost = convert_to_rial(controller_price, controller_unit, dollar_rate)

    # ✅ اصلاح: ضرب قیمت سازه در مساحت گرد شده
    wall_area_m2 = (wall_width_cm / 100) * (wall_height_cm / 100)
    wall_area_m2_rounded = round(wall_area_m2)  # ✅ گرد کردن مساحت
    structure_price_per_sqm = prices.get("structure", 100.0)
    structure_unit = prices.get("structure_unit", "ریال")
    structure_cost_per_sqm_rial = convert_to_rial(structure_price_per_sqm, structure_unit, dollar_rate)
    structure_cost = structure_cost_per_sqm_rial * wall_area_m2_rounded  # ✅ ضرب در مساحت گرد شده

    hdmi_cable_cost = convert_to_rial(prices["hdmi_cable"], prices["hdmi_cable_unit"], dollar_rate)
    cable_magnet_cost = convert_to_rial(prices["cable_magnet"], prices["cable_magnet_unit"], dollar_rate)

    total_cost = module_cost + receiver_cost + power_cost + controller_cost + structure_cost + hdmi_cable_cost + cable_magnet_cost

    tab1, tab2, tab3 = st.tabs(["📊 نتایج", "💰 هزینه‌ها", "✏️ ویرایش"])

    with tab1:
        col_l, col_r = st.columns(2)

        with col_l:
            st.metric("تعداد ماژول در طول", f"{modules_x} عدد")
            st.metric("تعداد ماژول در ارتفاع", f"{modules_y_round} عدد")
            st.metric("تعداد کل ماژول‌ها", f"{format_number(total_modules)} عدد")  # ✅ اصلاح

        with col_r:
            st.metric("رزولوشن هر ماژول", f"{format_number(module_resolution)}")  # ✅ اصلاح
            st.metric("رزولوشن کل", f"{format_number(total_resolution)}")  # ✅ اصلاح
            st.metric("کارت‌های گیرنده", f"{format_number(cards_needed)} عدد")  # ✅ اصلاح

        st.divider()

        col_l2, col_r2 = st.columns(2)
        with col_l2:
            st.metric("پاور 60 وات", f"{format_number(psu_count)} عدد")  # ✅ اصلاح
        with col_r2:
            controller_display = selected_controller_name if selected_controller_name else "انتخاب نشده"
            st.metric("کنترلر انتخاب شده", controller_display)

        if "max_resolution" in controller_info:
            st.info(f"حداکثر رزولوشن پشتیبانی‌شده: {format_number(controller_info['max_resolution'])}")  # ✅ اصلاح

        st.subheader("چیدمان ماژول‌ها")
        fig = draw_module_layout(modules_x, modules_y_round, blocks, st.session_state.module_grid)
        st.pyplot(fig, use_container_width=True)

    with tab2:
        st.subheader("تفکیک هزینه‌ها")

        cost_data = {
            "ماژول‌ها": module_cost,
            "کارت‌های گیرنده": receiver_cost,
            "پاورها": power_cost,
            "کنترلر": controller_cost,
            "سازه": structure_cost,  # ✅ این الان هزینه کل سازه (قیمت × مساحت گرد شده) هست
            "کابل HDMI": hdmi_cable_cost,
            "کابل و مگنت": cable_magnet_cost
        }

        col1, col2 = st.columns([1, 1])

        with col1:
            for item, cost in cost_data.items():
                with st.container(border=True):
                    st.write(f"**{item}**")
                    st.write(format_currency(cost))

        with col2:
            st.subheader("جمع کل")
            with st.container(border=True):
                st.metric("هزینه کل", format_currency(total_cost), delta=None)

            st.divider()

            df_costs = pd.DataFrame({
                "مورد": list(cost_data.keys()),
                "هزینه (ریال)": [format_currency(cost) for cost in cost_data.values()]  # ✅ اصلاح
            })

            st.dataframe(df_costs, hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("ویرایش جداگانه ماژول‌ها")

        with st.form(key='edit_module_form'):
            col_e1, col_e2, col_e3 = st.columns(3)

            with col_e1:
                edit_row = st.number_input("ردیف", min_value=1, max_value=modules_y_round, step=1, key="edit_row")

            with col_e2:
                edit_col = st.number_input("ستون", min_value=1, max_value=modules_x, step=1, key="edit_col")

            with col_e3:
                current_card = int(st.session_state.module_grid[edit_row-1, edit_col-1])
                new_card = st.number_input(
                    "کارت جدید",
                    min_value=1,
                    max_value=cards_needed if cards_needed > 0 else 1,
                    value=current_card,
                    step=1,
                    key="new_card_for_single"
                )

            submit_button = st.form_submit_button("✓ اعمال تغییر")

        if submit_button:
            row_idx = edit_row - 1
            col_idx = edit_col - 1
            st.session_state.module_grid[row_idx, col_idx] = int(new_card)
            st.success(f"ماژول ({edit_col}, {edit_row}) به کارت {new_card} تغییر یافت")
            st.rerun()


CONTROLLERS = {
    "x100 pro 4u": {"max_resolution": 26000000},
    "x10pro 7u": {"max_resolution": 52000000},
    "x40 m": {"max_resolution": 26000000},
    "x26m": {"max_resolution": 17000000},
    "x12": {"max_resolution": 7800000},
    "x7": {"max_resolution": 5200000},
    "x6": {"max_resolution": 3900000},
    "x4": {"max_resolution": 2600000},
    "x2": {"max_resolution": 1300000},
    "vx1000": {"max_resolution": 6500000},
    "vx600": {"max_resolution": 3900000},
    "vx4s": {"max_resolution": 2300000}
}

dot_pitch_limits = {
    "1.5 داخلی": {"dot_pitch": 1.5, "max_modules_per_card": 8},
    "1.8 داخلی": {"dot_pitch": 1.8, "max_modules_per_card": 13},
    "2.5 داخلی": {"dot_pitch": 2.5, "max_modules_per_card": 16},
    "2.5 خارجی": {"dot_pitch": 2.5, "max_modules_per_card": 8},
    "4 خارجی": {"dot_pitch": 4.0, "max_modules_per_card": 12}
}

st.set_page_config(
    page_title="محاسبه‌گر ویدئووال",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
    }

    * {
        font-family: 'Tahoma', 'Arial', sans-serif;
    }

    .main {
        max-width: 1400px;
        margin: 0 auto;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1a472a;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    .stMetric {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #2E86AB;
    }

    .stButton > button {
        background: linear-gradient(90deg, #2E86AB 0%, #1a472a 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #1a472a 0%, #2E86AB 100%);
        box-shadow: 0 4px 12px rgba(46, 134, 171, 0.3);
    }

    .stExpander {
        border-left: 4px solid #2E86AB !important;
        background-color: #f8f9fa;
    }

    [data-baseweb="tab-list"] {
        border-bottom: 2px solid #e0e0e0;
    }

    [data-baseweb="tab"] {
        background-color: #f5f7fa;
        color: #333;
        border-radius: 8px 8px 0 0;
    }

    [aria-selected="true"] {
        background-color: #2E86AB !important;
        color: white !important;
    }

    .stContainer {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
    }

    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 8px;
        padding: 1rem;
    }

    .stInfo {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
        color: #1976D2;
    }

    .stSuccess {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
        color: #2E7D32;
    }

    .stWarning {
        background-color: #fff3e0;
        border-left: 4px solid #FF9800;
        color: #E65100;
    }

    .stError {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }

    .header-box {
        background: linear-gradient(135deg, #2E86AB 0%, #1a472a 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.2);
    }

    .input-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }

    section[data-testid="stSidebar"] {
        width: 450px !important;
    }

    /* مخفی کردن محتوای sidebar وقتی بسته شده */
    section[data-testid="stSidebar"][aria-expanded="false"] .stSidebarContent {
        display: none !important;
    }

    </style>
""", unsafe_allow_html=True)

jalali_date = get_jalali_date()
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown(f"""
    <div class="header-box">
        <h1 style="margin: 0; color: white;">📺 محاسبه‌گر ویدئووال</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
            📅 {current_time} | 📅 {jalali_date}
        </p>
    </div>
""", unsafe_allow_html=True)

if 'calculation_performed' not in st.session_state:
    st.session_state.calculation_performed = False

with st.sidebar:
    st.markdown("### ⚙️ تنظیمات")

    with st.expander("💰 تنظیم قیمت‌ها", expanded=False):
        st.markdown("#### قیمت دلار")
        current_dollar_rate = st.session_state.get("dollar_rate", 0)
        new_dollar_rate = st.number_input(
            "قیمت روز دلار (ریال)",
            value=float(current_dollar_rate),
            step=1000.0,
            format="%.0f",
            key="dollar_input"
        )
        st.info(f"💵 {int(new_dollar_rate):,} ریال")

        prices = st.session_state.get("prices", get_default_prices())

        st.markdown("#### قیمت مواد")

        # --- ماژول ---
        module_col1, module_col2 = st.columns([3, 1])  # نسبت ۳ به ۱ برای فضای بیشتر
        with module_col1:
            module_price = st.number_input(
                "ماژول",
                value=prices["module"],
                step=0.01,
                format="%.2f",
                key="module_price"
            )
        with module_col2:
            module_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["module_unit"] == "ریال" else 1,
                key="module_unit"
            )

        # --- کارت گیرنده ---
        receiver_col1, receiver_col2 = st.columns([3, 1])
        with receiver_col1:
            receiver_price = st.number_input(
                "کارت گیرنده",
                value=prices["receiver_card"],
                step=0.01,
                format="%.2f",
                key="receiver_price"
            )
        with receiver_col2:
            receiver_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["receiver_unit"] == "ریال" else 1,
                key="receiver_unit"
            )

        # --- پاور 60 وات ---
        power_col1, power_col2 = st.columns([3, 1])
        with power_col1:
            psu_price = st.number_input(
                "پاور 60 وات",
                value=prices["power_supply_60w"],
                step=0.01,
                format="%.2f",
                key="psu_price"
            )
        with power_col2:
            power_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["power_unit"] == "ریال" else 1,
                key="power_unit"
            )

        # --- سازه ---
        structure_col1, structure_col2 = st.columns([3, 1])
        with structure_col1:
            structure_price = st.number_input(
                "سازه (قیمت هر متر مربع)",  # ✅ تغییر لیبل
                value=prices["structure"],
                step=0.01,
                format="%.2f",
                key="structure_price"
            )
        with structure_col2:
            structure_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["structure_unit"] == "ریال" else 1,
                key="structure_unit"
            )

        # --- کابل HDMI ---
        hdmi_col1, hdmi_col2 = st.columns([3, 1])
        with hdmi_col1:
            hdmi_price = st.number_input(
                "کابل HDMI",
                value=prices["hdmi_cable"],
                step=0.01,
                format="%.2f",
                key="hdmi_price"
            )
        with hdmi_col2:
            hdmi_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["hdmi_cable_unit"] == "ریال" else 1,
                key="hdmi_cable_unit"
            )

        # --- کابل و مگنت ---
        cable_col1, cable_col2 = st.columns([3, 1])
        with cable_col1:
            cable_price = st.number_input(
                "کابل و مگنت",
                value=prices["cable_magnet"],
                step=0.01,
                format="%.2f",
                key="cable_price"
            )
        with cable_col2:
            cable_unit = st.selectbox(
                "واحد",
                ["ریال", "دلار"],
                index=0 if prices["cable_magnet_unit"] == "ریال" else 1,
                key="cable_magnet_unit"
            )

        # --- قیمت کنترلرها ---
        st.markdown("#### قیمت کنترلرها")

        controller_prices = prices.get("controller_prices", {})
        controller_units = prices.get("controller_units", {})

        for name, info in CONTROLLERS.items():
            col_price, col_unit = st.columns([3, 1])

            with col_price:
                st.markdown(f"**{name}**")
                price = controller_prices.get(name, 100.0)
                new_price = st.number_input(
                    "قیمت",
                    value=price,
                    step=0.01,
                    format="%.2f",
                    key=f"controller_{name}",
                    label_visibility="collapsed"
                )
                controller_prices[name] = new_price

            with col_unit:
                unit = controller_units.get(name, "ریال")
                new_unit = st.selectbox(
                    "واحد",
                    ["ریال", "دلار"],
                    index=0 if unit == "ریال" else 1,
                    key=f"unit_{name}",
                    label_visibility="collapsed"
                )
                controller_units[name] = new_unit

        # --- ذخیره قیمت‌ها ---
        if st.button("💾 ذخیره قیمت‌ها", use_container_width=True):
            st.session_state.dollar_rate = new_dollar_rate
            st.session_state.prices = {
                "module": module_price,
                "receiver_card": receiver_price,
                "power_supply_60w": psu_price,
                "structure": structure_price,  # ✅ ذخیره قیمت هر متر مربع
                "hdmi_cable": hdmi_price,
                "cable_magnet": cable_price,
                "module_unit": module_unit,
                "receiver_unit": receiver_unit,
                "power_unit": power_unit,
                "structure_unit": structure_unit,
                "hdmi_cable_unit": hdmi_unit,
                "cable_magnet_unit": cable_unit,
                "controller_prices": controller_prices,
                "controller_units": controller_units
            }
            st.success("✓ قیمت‌ها ذخیره شدند!")

# ... (بقیه کد بدون تغییر)

st.markdown('<div class="input-section">', unsafe_allow_html=True)

st.subheader("📐 ورودی‌های ویدئووال")

col1, col2, col3 = st.columns(3)

with col1:
    wall_w = st.number_input(
        "عرض ویدئووال (سانتی‌متر)",
        value=480.0,
        step=1.0,
        min_value=10.0
    )

with col2:
    wall_h = st.number_input(
        "ارتفاع ویدئووال (سانتی‌متر)",
        value=270.0,
        step=1.0,
        min_value=10.0
    )

with col3:
    selected_option = st.selectbox(
        "دات‌پیچ و نوع نصب",
        options=list(dot_pitch_limits.keys()),
        index=1
    )
    dot_pitch_info = dot_pitch_limits[selected_option]
    dot_pitch = dot_pitch_info["dot_pitch"]
    max_modules_per_card = dot_pitch_info["max_modules_per_card"]

st.info(f"📊 حداکثر ماژول در هر کارت: **{max_modules_per_card}**")

# --- اصلاح شده ---
st.subheader("🎛️ تنظیمات بلوک")

col_block1, col_block2 = st.columns(2)

with col_block1:
    block_w = st.number_input(
        "ماژول در عرض بلوک",
        min_value=1,
        max_value=max_modules_per_card,
        value=2,
        step=1
    )

with col_block2:
    block_h = st.number_input(
        "ماژول در ارتفاع بلوک",
        min_value=1,
        max_value=max_modules_per_card,
        value=6,
        step=1
    )

st.markdown('</div>', unsafe_allow_html=True)

# --- ذخیره عرض و ارتفاع در session_state ---
st.session_state.wall_width_cm = wall_w
st.session_state.wall_height_cm = wall_h

# ... (بقیه کد بدون تغییر)

modules_x = None
modules_y_round = None
blocks = None

def perform_calculation():
    global modules_x, modules_y_round, blocks
    res = videowall_calc(wall_w, wall_h, dot_pitch_mm=dot_pitch)
    modules_x = res['modules_x']
    modules_y_round = res['modules_y_round']

    total_modules = modules_x * modules_y_round
    blocks, grid = optimize_layout(modules_x, modules_y_round, block_w, block_h, max_modules_per_card)

    if 'module_grid' not in st.session_state:
        st.session_state.module_grid = grid.copy()
    else:
        if st.session_state.module_grid.shape == grid.shape:
            st.session_state.module_grid = grid.copy()
        else:
            st.session_state.module_grid = grid.copy()

    st.session_state.modules_x = modules_x
    st.session_state.modules_y_round = modules_y_round
    st.session_state.blocks = blocks
    st.session_state.calculation_performed = True

    px_per_module_x = round(320 / dot_pitch)
    px_per_module_y = round(160 / dot_pitch)
    total_resolution = (modules_x * px_per_module_x) * (modules_y_round * px_per_module_y)

    st.session_state.total_resolution = total_resolution

col_button1, col_button2, col_button3 = st.columns([1, 1, 2])

with col_button1:
    if not st.session_state.get("calculation_performed", False):
        if st.button("🔢 محاسبه", use_container_width=True):
            perform_calculation()
            st.rerun()
    else:
        if st.button("🔄 محاسبه مجدد", use_container_width=True):
            perform_calculation()
            st.rerun()

if st.session_state.get("calculation_performed", False):
    modules_x = st.session_state.get("modules_x")
    modules_y_round = st.session_state.get("modules_y_round")
    blocks = st.session_state.get("blocks")
    total_resolution = st.session_state.get("total_resolution", 0)

    st.divider()

    st.subheader("🎮 انتخاب کنترلر")

    available_controllers = {}
    for name, info in CONTROLLERS.items():
        if info["max_resolution"] >= total_resolution:
            available_controllers[name] = info

    if not available_controllers:
        st.error("❌ هیچ کنترلری برای این رزولوشن موجود نیست!")
        selected_controller = None
    else:
        controller_options = []
        for name, info in available_controllers.items():
            option_text = f"{name} (حداکثر: {format_number(info['max_resolution'])})"  # ✅ اصلاح
            controller_options.append(option_text)

        default_controller_index = 0
        selected_controller_info = st.session_state.get("selected_controller_info", {})
        if selected_controller_info:
            default_controller_name = selected_controller_info.get("name", "")
            try:
                default_controller_index = list(available_controllers.keys()).index(default_controller_name)
            except ValueError:
                default_controller_index = 0

        selected_option_text = st.selectbox(
            "کنترلر مناسب:",
            options=controller_options,
            index=default_controller_index,
            key="controller_selector"
        )

        selected_controller_name = selected_option_text.split(" (")[0]
        selected_controller = available_controllers[selected_controller_name]
        st.session_state.selected_controller_info = {
            "name": selected_controller_name,
            "max_resolution": selected_controller["max_resolution"],
            "price": selected_controller_name
        }

    show_results_and_edit()