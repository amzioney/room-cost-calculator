import streamlit as st
from datetime import date, timedelta
from typing import List, Dict

st.set_page_config(
    page_title="出差拼房费用计算器",
    page_icon="🏨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 15px; }
.block-container { padding: 1rem 1rem 3rem; max-width: 560px; }
details summary p { font-weight: 600; }
.res-card {
    border-radius: 12px; border: 1px solid #e5e5e5;
    padding: 14px 16px; margin-bottom: 10px; background: #fff;
}
.res-name { font-size: 17px; font-weight: 600; margin-bottom: 8px; }
.res-row  { display: flex; justify-content: space-between; font-size: 14px; padding: 4px 0; }
.res-label { color: #888; }
.res-val   { font-weight: 500; }
.pos { color: #1D9E75; }
.neg { color: #E24B4A; }
.big { font-size: 20px; font-weight: 700; }
div[data-testid="stButton"] button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def date_range(start: date, end: date) -> List[date]:
    days, cur = [], start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days

def get_paid(p) -> float:
    return p["flat_amt"] * p["flat_days"]

DOW_CN = "日一二三四五六"

def fmt_date(d: date) -> str:
    dow = DOW_CN[(d.weekday() + 1) % 7]
    return f"{d.month}/{d.day}（{dow}）"


# ── session state 初始化 ──────────────────────────────────────────────────────

def init_state():
    if "rooms" not in st.session_state:
        st.session_state.rooms = [
            {"name": "房间1", "price": 0},
            {"name": "房间2", "price": 0},
        ]
    if "persons" not in st.session_state:
        st.session_state.persons = [
            {"name": "成员1", "room_idx": 0,
             "flat_amt": 0, "flat_days": 0, "stay_dates": None},
            {"name": "成员2", "room_idx": 0,
             "flat_amt": 0, "flat_days": 0, "stay_dates": None},
        ]

init_state()


# ── 基础设置 ──────────────────────────────────────────────────────────────────

st.title("🏨 出差拼房费用计算器")

with st.expander("⚙️ 基础设置", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("开始日期", value=date.today(), key="start")
    with c2:
        end_date = st.date_input(
            "结束日期", value=date.today() + timedelta(days=6), key="end")

    if end_date < start_date:
        st.error("结束日期不能早于开始日期")
        st.stop()

    all_dates     = date_range(start_date, end_date)
    all_dates_set = set(all_dates)
    total_days    = len(all_dates)

    c3, c4 = st.columns(2)
    with c3:
        st.info(f"共 **{total_days}** 天")
    with c4:
        discount = st.number_input(
            "退款折扣", min_value=0.0, max_value=1.0, value=1.0, step=0.01,
            help="实际退款 = 退款 × 折扣，如 0.95 = 退 95%")


# ── 房间设置 ──────────────────────────────────────────────────────────────────

st.markdown("### 🚪 房间设置")

del_room_idx = None
for i, room in enumerate(st.session_state.rooms):
    with st.expander(f"{room['name']}  ·  ¥{room['price']}/晚", expanded=True):
        st.session_state.rooms[i]["name"] = st.text_input(
            "房间名称", value=room["name"], key=f"rn_{i}")
        st.session_state.rooms[i]["price"] = st.number_input(
            "每晚整间房价（元）", min_value=0, value=room["price"],
            step=10, key=f"rp_{i}")
        if len(st.session_state.rooms) > 1:
            if st.button("🗑 删除此房间", key=f"dr_{i}", use_container_width=True):
                del_room_idx = i

if del_room_idx is not None:
    st.session_state.rooms.pop(del_room_idx)
    for p in st.session_state.persons:
        if p["room_idx"] >= len(st.session_state.rooms):
            p["room_idx"] = 0
    st.rerun()

if st.button("＋ 添加房间", use_container_width=True):
    st.session_state.rooms.append(
        {"name": f"房间{len(st.session_state.rooms)+1}", "price": 0})
    st.rerun()


# ── 人员设置 ──────────────────────────────────────────────────────────────────

st.markdown("### 👥 人员设置")

room_names     = [r["name"] for r in st.session_state.rooms]
del_person_idx = None

for pi, p in enumerate(st.session_state.persons):

    # 同步 stay_dates：None → 全选；范围扩展时新日期默认选中
    prev = p.get("stay_dates")
    if prev is None:
        current = set(all_dates)
    else:
        current = (prev & all_dates_set) | (all_dates_set - prev)
    st.session_state.persons[pi]["stay_dates"] = current

    stay_count   = len(current)
    paid_preview = get_paid(p)
    room_name    = room_names[min(p["room_idx"], len(room_names) - 1)]

    with st.expander(
        f"**{p['name']}** · {room_name} · 住{stay_count}天 · 已付¥{paid_preview:.0f}",
        expanded=True
    ):
        # 姓名 + 房间
        ca, cb = st.columns(2)
        with ca:
            st.session_state.persons[pi]["name"] = st.text_input(
                "姓名", value=p["name"], key=f"pn_{pi}")
        with cb:
            st.session_state.persons[pi]["room_idx"] = st.selectbox(
                "房间", options=list(range(len(room_names))),
                format_func=lambda x, rn=room_names: rn[x],
                index=min(p["room_idx"], len(room_names) - 1),
                key=f"pr_{pi}")

        # ── 入住日期：pills 多选 ──
        st.markdown("**入住日期**")

        # 按月分组，每月单独一行 pills
        months: Dict[tuple, List[date]] = {}
        for d in all_dates:
            months.setdefault((d.year, d.month), []).append(d)

        new_stay: set = set()
        for (yr, mo), month_dates in months.items():
            st.markdown(
                f"<div style='font-size:12px;color:#888;margin:8px 0 2px'>"
                f"{yr}年{mo}月</div>",
                unsafe_allow_html=True)
            selected_pills = st.pills(
                label=f"{yr}年{mo}月",
                options=month_dates,
                selection_mode="multi",
                default=[d for d in month_dates if d in current],
                format_func=fmt_date,
                key=f"pills_{pi}_{yr}_{mo}",
                label_visibility="collapsed",
            )
            new_stay.update(selected_pills)

        st.session_state.persons[pi]["stay_dates"] = new_stay
        st.caption(f"已选 {len(new_stay)} 天入住")

        # ── 预付金额 ──
        st.markdown("**预付金额**")
        ma, mb = st.columns(2)
        with ma:
            st.session_state.persons[pi]["flat_amt"] = st.number_input(
                "每天金额（元）", min_value=0, value=p["flat_amt"],
                step=10, key=f"pa_{pi}")
        with mb:
            st.session_state.persons[pi]["flat_days"] = st.number_input(
                "预付天数", min_value=0, value=p["flat_days"],
                step=1, key=f"pd_{pi}")
        t = (st.session_state.persons[pi]["flat_amt"]
             * st.session_state.persons[pi]["flat_days"])
        st.caption(f"已付总额：**¥{t:.0f}**（与入住天数无关）")

        if len(st.session_state.persons) > 1:
            if st.button("🗑 删除此人员", key=f"dp_{pi}",
                         use_container_width=True):
                del_person_idx = pi

if del_person_idx is not None:
    st.session_state.persons.pop(del_person_idx)
    st.rerun()

if st.button("＋ 添加人员", use_container_width=True):
    st.session_state.persons.append({
        "name": f"成员{len(st.session_state.persons)+1}",
        "room_idx": 0,
        "flat_amt": 0,
        "flat_days": total_days,
        "stay_dates": set(all_dates),
    })
    st.rerun()


# ── 计算 ──────────────────────────────────────────────────────────────────────

st.markdown("---")
if st.button("🧮  计算费用分摊", type="primary", use_container_width=True):

    persons_data = st.session_state.persons
    rooms_data   = st.session_state.rooms

    total_cost = 0.0
    owed = [0.0] * len(persons_data)

    for room_idx, room in enumerate(rooms_data):
        for d in all_dates:
            staying = [i for i, p in enumerate(persons_data)
                       if p["room_idx"] == room_idx
                       and d in p.get("stay_dates", set())]
            if not staying:
                continue
            total_cost += room["price"]
            share = room["price"] / len(staying)
            for i in staying:
                owed[i] += share

    paid_list  = [get_paid(p) for p in persons_data]
    total_paid = sum(paid_list)

    st.markdown("### 📊 计算结果")
    mc1, mc2 = st.columns(2)
    mc1.metric("总住宿成本", f"¥{total_cost:.0f}")
    mc2.metric("总预付金额", f"¥{total_paid:.0f}")
    mc3, mc4 = st.columns(2)
    mc3.metric("待退总额（折前）", f"¥{total_paid - total_cost:.0f}")
    mc4.metric("退款折扣", f"{discount*100:.0f}%")

    st.markdown("---")

    for i, p in enumerate(persons_data):
        nights   = len(p.get("stay_dates", set()))
        raw      = paid_list[i] - owed[i]
        final    = raw * discount
        rn       = rooms_data[min(p["room_idx"], len(rooms_data)-1)]["name"]
        cls_raw  = "pos" if raw   >= 0 else "neg"
        cls_fin  = "pos" if final >= 0 else "neg"
        sign_raw = "+" if raw   >= 0 else ""
        sign_fin = "+" if final >= 0 else ""

        st.markdown(f"""
<div class="res-card">
  <div class="res-name">{p['name']}
    <span style="font-size:13px;font-weight:400;color:#888">· {rn}</span>
  </div>
  <div class="res-row">
    <span class="res-label">入住天数</span>
    <span class="res-val">{nights} 天</span>
  </div>
  <div class="res-row">
    <span class="res-label">应付</span>
    <span class="res-val">¥{owed[i]:.2f}</span>
  </div>
  <div class="res-row">
    <span class="res-label">已付（¥{p['flat_amt']}/天 × {p['flat_days']}天）</span>
    <span class="res-val">¥{paid_list[i]:.2f}</span>
  </div>
  <div class="res-row">
    <span class="res-label">退款（折扣前）</span>
    <span class="res-val {cls_raw}">{sign_raw}¥{raw:.2f}</span>
  </div>
  <div class="res-row"
       style="border-top:1px solid #eee;margin-top:8px;padding-top:8px">
    <span class="res-label">实际退款（×{discount}）</span>
    <span class="res-val {cls_fin} big">{sign_fin}¥{final:.2f}</span>
  </div>
</div>
""", unsafe_allow_html=True)

    st.caption(
        "应付：每天只有实际入住该房间的人才均摊当天房费（房价 ÷ 当天入住人数）。"
        "已付：预付金额/天 × 预付天数，与入住天数无关。"
        "退款 = 已付 − 应付；实际退款 = 退款 × 折扣。"
    )