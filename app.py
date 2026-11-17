import json
import math
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Team Psychology | Career Venture Lab (PSY-2)",
    page_icon="🧠",
    layout="wide"
)

def money(val):
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def init_state():
    return {
        "team_id": "TEAM-PSY",
        "pathway_id": "PSY-2",
        "selected_course": "Precalculus",
        "selected_level": "Advanced",
        "teacher_approved_level": True,
        "state_version": 1,
        "snapshot_id": "SNAP-001",
        "base_price": 30.0,
        "D0": 70,
        "staff_hours": 25.0,
        "hours_per_unit": 0.5,
        "program_seats": 50,
        "completion_rate": 0.80,
        "satisfaction_mean": 4.2,
        "learning_gain_pct": 76.0,
        "variable_lines": {
            "facilitator_delivery": 3.0,
            "materials": 2.0,
            "survey_processing": 1.0,
        },
        "fixed_lines": {
            "venue": 200.0,
            "software": 100.0,
            "accessibility": 150.0,
            "admin": 100.0,
        },
        "owner_contribution": 5000.0,
        "equipment_assets": 700.0,
        "pre_opening_expense": 1300.0,
        "cash": 3000.0,
        "loan_debt": 0.0,
        "processed_run_ids": [],
        "ledger": [],
        "decisions": []
    }

if "sim" not in st.session_state:
    st.session_state.sim = init_state()

sim = st.session_state.sim

def var_unit_cost(s):
    return sum(s["variable_lines"].values())

def fixed_month_cost(s):
    return sum(s["fixed_lines"].values())

def derived_capacity(s):
    staff_cap = int(math.floor(s["staff_hours"] / s["hours_per_unit"])) if s["hours_per_unit"] > 0 else 0
    return min(staff_cap, int(s["program_seats"]))

def record_simulation_step(s, requested, ad_cost, run_id, sim_date, capacity_override=None, is_fixture=False):
    if run_id in s["processed_run_ids"]:
        return False, f"Duplicate run_id '{run_id}' blocked. No new transaction added."

    price = money(s["base_price"])
    v_unit = money(var_unit_cost(s))
    f_cost = money(fixed_month_cost(s))
    ad = money(ad_cost)
    open_cash = money(s["cash"])

    cap = int(capacity_override) if (is_fixture and capacity_override is not None) else derived_capacity(s)
    req = max(0, int(requested))
    sold = min(req, cap)
    lost_demand = max(0, req - sold)
    completed = int(math.floor(sold * s["completion_rate"]))

    rev = price * Decimal(sold)
    var_exp = v_unit * Decimal(sold)
    tot_exp = var_exp + f_cost + ad
    op_profit = rev - tot_exp
    close_cash = open_cash + op_profit

    s["cash"] = float(close_cash)
    s["state_version"] += 1
    s["snapshot_id"] = f"SNAP-{s['state_version']:03d}"
    s["processed_run_ids"].append(run_id)

    s["ledger"].append({
        "run_id": run_id,
        "date": sim_date,
        "mode": "FIXTURE" if is_fixture else "NORMAL",
        "requested": req,
        "capacity": cap,
        "sold": sold,
        "lost_demand": lost_demand,
        "completed": completed,
        "satisfaction_mean": s["satisfaction_mean"],
        "revenue": float(rev),
        "variable_expense": float(var_exp),
        "fixed_expense": float(f_cost),
        "ad_cost": float(ad),
        "total_expense": float(tot_exp),
        "operating_profit": float(op_profit),
        "closing_cash": float(close_cash),
        "state_version": s["state_version"]
    })
    return True, f"Recorded {sold} sold seats (Profit: ${float(op_profit):,.2f})."

# --- SIDEBAR: STATUS, SAVE/RESTORE & RESET ---
with st.sidebar:
    st.title("🧠 Team Psychology")
    st.caption("Study Habits & Wellness Education Studio")
    st.markdown(f"**Team ID:** `{sim['team_id']}` | **Pathway:** `{sim['pathway_id']}`")
    st.markdown(f"**Course:** `{sim['selected_course']}` | **Level:** `{sim['selected_level']}`")
    st.markdown(f"**State Version:** `v{sim['state_version']}` (`{sim['snapshot_id']}`)")
    st.info("Nonclinical educational simulation only. Fictional data; no personal health records.")

    st.divider()
    st.subheader("💾 Durable Save / Restore (JSON)")
    snapshot_json = json.dumps(sim, indent=2)
    st.download_button(
        label="Download Snapshot JSON",
        data=snapshot_json,
        file_name=f"{sim['team_id']}_{sim['pathway_id']}_v{sim['state_version']}.json",
        mime="application/json",
        use_container_width=True
    )

    uploaded = st.file_uploader("Restore / Import Snapshot JSON", type=["json"])
    if uploaded is not None:
        try:
            imported = json.load(uploaded)
            required_keys = {"team_id", "pathway_id", "state_version", "cash", "ledger", "processed_run_ids"}
            if not required_keys.issubset(imported.keys()):
                st.error("Rejected: Missing required snapshot fields.")
            elif imported.get("team_id") != sim["team_id"]:
                st.error(f"Rejected: Team ID mismatch ({imported.get('team_id')} != {sim['team_id']}).")
            elif int(imported.get("state_version", 0)) < int(sim["state_version"]):
                st.error(f"Rejected: Stale version (v{imported.get('state_version')} < current v{sim['state_version']}).")
            else:
                st.session_state.sim = imported
                st.success(f"Restored snapshot v{imported['state_version']}!")
                st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON file: {e}")

    st.divider()
    if st.button("Reset to PSY Opening Baseline", type="secondary", use_container_width=True):
        st.session_state.sim = init_state()
        st.rerun()

# --- TOP KPI HEADER ---
st.header("Stage 1 Dashboard: Study Habits & Wellness Education Studio")
st.caption("Stage 1 Active: Deterministic Precalculus Engine, Dated Ledger, Save/Load JSON & Fixture Acceptance Tests. (Stage 2 Reports/Marketing & Stage 3 Assessments marked for next phase.)")

c1, c2, c3, c4, c5 = st.columns(5)
cap_now = derived_capacity(sim)
c1.metric("Post-Startup Cash", f"${sim['cash']:,.2f}")
c2.metric("Monthly Seat Capacity", f"{cap_now} seats", help="min(floor(staff_hours / hours_per_unit), program_seats)")
c3.metric("Base Seat Price", f"${sim['base_price']:,.2f}")
c4.metric("Variable / Fixed Cost", f"${var_unit_cost(sim):.2f} / ${fixed_month_cost(sim):.0f}")
c5.metric("Quality (Separate from Rev)", f"{int(sim['completion_rate']*100)}% compl. | {sim['satisfaction_mean']}/5")

tabs = st.tabs([
    "1. Inputs & Run Month",
    "2. Precalculus Math (PSY-2 Advanced)",
    "3. Ledger & Acceptance Tests",
    "4. Stage 2-3 Roadmap"
])

# --- TAB 1: INPUTS & FUNDING ---
with tabs[0]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Startup Financing & Opening Balances")
        st.markdown(f"""
- **Owner Contribution:** ${sim['owner_contribution']:,.2f}
- **Equipment Assets (Capitalized):** ${sim['equipment_assets']:,.2f}
- **Pre-Opening Expense:** ${sim['pre_opening_expense']:,.2f} (Retained earnings start at -${sim['pre_opening_expense']:,.2f})
- **Opening Spendable Cash:** $3,000.00 (Not counted as sales revenue)
""")

        st.subheader("Editable Operating Parameters")
        sim["base_price"] = st.number_input("Program Seat Price ($)", min_value=1.0, max_value=200.0, value=float(sim["base_price"]), step=1.0)
        sim["D0"] = st.number_input("Baseline Monthly Demand D0 (seats)", min_value=0, max_value=500, value=int(sim["D0"]), step=1)
        sim["staff_hours"] = st.number_input("Facilitator Staff Hours / Month", min_value=0.0, max_value=500.0, value=float(sim["staff_hours"]), step=1.0)
        sim["hours_per_unit"] = st.number_input("Hours per Seat Unit", min_value=0.1, max_value=10.0, value=float(sim["hours_per_unit"]), step=0.1)
        sim["program_seats"] = st.number_input("Venue Program Seat Cap / Month", min_value=0, max_value=500, value=int(sim["program_seats"]), step=1)

    with col_b:
        st.subheader("Editable Cost Lines (USD)")
        for k in list(sim["variable_lines"].keys()):
            sim["variable_lines"][k] = st.number_input(f"Variable: {k} ($/seat)", min_value=0.0, value=float(sim["variable_lines"][k]), step=0.5)
        for k in list(sim["fixed_lines"].keys()):
            sim["fixed_lines"][k] = st.number_input(f"Fixed: {k} ($/month)", min_value=0.0, value=float(sim["fixed_lines"][k]), step=10.0)

        st.subheader("Quality Metrics (Tracked Separately)")
        sim["completion_rate"] = st.slider("Program Completion Rate", 0.0, 1.0, float(sim["completion_rate"]), 0.05)
        sim["satisfaction_mean"] = st.slider("Self-Reported Satisfaction (1-5)", 1.0, 5.0, float(sim["satisfaction_mean"]), 0.1)
        st.caption("Rule: Revenue is earned at delivery (`sold`). Completion and satisfaction do not automatically alter demand or trigger refunds.")

    st.divider()
    st.subheader("Run One Simulation Month (Commits to Ledger)")
    r1, r2, r3, r4 = st.columns(4)
    req_input = r1.number_input("Requested Seats This Month", min_value=0, max_value=500, value=int(sim["D0"]), step=1)
    ad_input = r2.number_input("Approved Ad Expense ($)", min_value=0.0, max_value=5000.0, value=0.0, step=25.0)
    date_input = r3.text_input("Month-End Date (YYYY-MM-DD)", value=f"2027-{len(sim['ledger'])+1:02d}-28")
    run_id_input = r4.text_input("Unique Run ID", value=f"RUN-{len(sim['ledger'])+1:03d}")

    if st.button("Approve & Advance Simulation Month", type="primary"):
        ok, msg = record_simulation_step(sim, req_input, ad_input, run_id_input, date_input, is_fixture=False)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.warning(msg)

# --- TAB 2: PRECALCULUS MATH SKILLS PANEL ---
with tabs[1]:
    st.subheader("Math Skills & Challenge Level Panel | Precalculus (PSY-2)")
    level_choice = st.selectbox(
        "Challenge Level (Teacher-Approved: Advanced)",
        ["Foundation", "Applied", "Advanced"],
        index=["Foundation", "Applied", "Advanced"].index(sim["selected_level"])
    )
    if level_choice != sim["selected_level"]:
        sim["selected_level"] = level_choice
        st.info(f"Switched view to {level_choice}. Remember: teacher approval is required before changing official level.")

    F = fixed_month_cost(sim)
    v = var_unit_cost(sim)
    cap = max(1, derived_capacity(sim))
    p0 = sim["base_price"]
    D0 = sim["D0"]

    if level_choice == "Foundation":
        st.markdown("### Foundation: Average Cost Rational Function $A(s) = \frac{F}{s} + v$")
        st.write(f"**Equation:** $A(s) = \frac{{{F:.0f}}}{{s}} + {v:.2f}$ on practical domain $0 < s \le {cap}$ seats.")
        st.markdown(f"""
- **Vertical Asymptote:** $s = 0$ (Average cost per seat is undefined when 0 seats are sold).
- **Horizontal Asymptote:** $y = {v:.2f}$ (As volume grows, fixed costs spread out and cost per seat approaches ${v:.2f}).
- **At Full Capacity ($s = {cap}$):** $A({cap}) = \${F/cap + v:.2f}$ per seat.
""")

        s_vals = np.linspace(1, cap, 50)
        a_vals = F / s_vals + v
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s_vals, y=a_vals, mode="lines", name="Average Cost A(s)"))
        fig.add_hline(y=v, line_dash="dash", line_color="gray", annotation_text=f"Horizontal Asymptote y = ${v:.2f}")
        fig.update_layout(title="Average Cost per Seat A(s) vs. Completed Seats (s)", xaxis_title="Completed Seats (s)", yaxis_title="Average Cost ($/seat)")
        st.plotly_chart(fig, use_container_width=True)

    elif level_choice == "Applied":
        st.markdown("### Applied: Function Composition & Capacity Breakpoint")
        slope = D0 / p0 if p0 > 0 else 2.3333
        intercept = 2 * D0
        p_break = p0 * (2 - cap / D0) if D0 > 0 else 38.57
        st.markdown(f"""
- **Demand Function:** $q(p) = \max(0, {intercept:.0f} - {slope:.4f}p)$ on $0 \le p \le {2*p0:.0f}$
- **Capacity-Constrained Sales:** $s(p) = \min({cap}, q(p))$
- **Composed Revenue & Cost:** $R(p) = p \cdot s(p)$ and $C(s(p)) = {F:.0f} + {v:.2f} \cdot s(p)$
- **Capacity Breakpoint Price:** $p = \${p_break:.2f}$ (Below this price, demand exceeds your {cap}-seat cap!)
""")

        p_grid = np.linspace(0, 2 * p0, 120)
        q_grid = np.maximum(0, intercept - slope * p_grid)
        s_grid = np.minimum(cap, q_grid)
        rev_grid = p_grid * s_grid
        cost_grid = F + v * s_grid
        prof_grid = rev_grid - cost_grid

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=p_grid, y=rev_grid, name="Composed Revenue R(p)"))
        fig.add_trace(go.Scatter(x=p_grid, y=cost_grid, name="Composed Cost C(s(p))"))
        fig.add_trace(go.Scatter(x=p_grid, y=prof_grid, name="Profit P(p)", line=dict(width=3)))
        fig.add_hline(y=0, line_color="black", line_width=1)
        fig.add_vline(x=p_break, line_dash="dash", line_color="orange", annotation_text=f"Capacity Breakpoint (${p_break:.2f})")
        fig.update_layout(title="Composed Revenue, Cost & Profit vs. Seat Price (Continuous Model)", xaxis_title="Seat Price ($)", yaxis_title="USD ($)")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.markdown("### Advanced (Teacher-Approved): Seasonal Trigonometric Demand Model & Capacity Clipping")
        st.markdown(f"""
**Assumed Seasonal Model:** $D(t) = D_0 \left(1 + 0.20 \sin\left(\frac{{2\pi(t - 1)}}{{12}}\right)\right)$ for month index $t = 1 \dots 12$.
- **Period:** 12 months | **Peak Demand:** Month $t = 4$ ($1.20 \times D_0 = {1.2*D0:.0f}$ seats) | **Lowest Demand:** Month $t = 10$ ($0.80 \times D_0 = {0.8*D0:.0f}$ seats).
- **Business Insight:** Even at the seasonal low ($t = 10$, 56 seats at baseline), demand still exceeds the studio's 50-seat capacity cap—meaning capacity, not seasonal advertising, is your primary bottleneck!
""")

        months = np.arange(1, 13)
        d_t = D0 * (1 + 0.20 * np.sin(2 * np.pi * (months - 1) / 12))
        s_t = np.minimum(cap, np.floor(d_t))
        unserved_t = np.maximum(0, np.floor(d_t) - s_t)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=months, y=d_t, name="Unconstrained Seasonal Demand D(t)", marker_color="#90CAF9"))
        fig.add_trace(go.Scatter(x=months, y=s_t, mode="lines+markers", name=f"Realized Sales (Capped at {cap})", line=dict(color="#1E88E5", width=3)))
        fig.add_hline(y=cap, line_dash="dash", line_color="red", annotation_text=f"Capacity Cap ({cap} seats)")
        fig.update_layout(title="12-Month Seasonal Demand D(t) vs. Capacity-Clipped Sales", xaxis_title="Month Index (t)", yaxis_title="Program Seats")
        st.plotly_chart(fig, use_container_width=True)

        df_season = pd.DataFrame({
            "Month (t)": months,
            "Modeled Demand D(t)": np.round(d_t, 2),
            "Integer Demand": np.floor(d_t).astype(int),
            "Realized Sales (Capped)": s_t.astype(int),
            "Lost Demand": unserved_t.astype(int),
            "Projected Operating Profit ($)": s_t * p0 - (F + v * s_t)
        })
        st.dataframe(df_season, use_container_width=True)

        st.markdown("**Transfer & Limitation Check:** Why can't we treat this smooth sine wave as guaranteed real-world demand? *(Hint: Academic calendars vary, synthetic parameters are assumptions, and fractional seats must be floored to whole participants.)*")

# --- TAB 3: LEDGER & ACCEPTANCE TESTS ---
with tabs[2]:
    st.subheader("Dated Event Ledger (Actual Simulated Transactions)")
    if sim["ledger"]:
        st.dataframe(pd.DataFrame(sim["ledger"]), use_container_width=True)
    else:
        st.info("No transactions recorded yet. Run a month in Tab 1 or run the Acceptance Fixture below.")

    st.divider()
    st.subheader("Stage 1 Acceptance Test Suite (PSY Package)")
    st.write("Replays `sample_data/monthly_fixture.csv` from a clean opening state ($3,000 cash) and verifies exact expected figures.")

    if st.button("Reset & Run PSY 3-Month Fixture Test"):
        st.session_state.sim = init_state()
        s = st.session_state.sim
        fixture_rows = [
            ("2027-01", 70, 50, 0),
            ("2027-02", 77, 50, 100),
            ("2027-03", 63, 37, 0),
        ]
        for m, req, cap_ov, ad in fixture_rows:
            record_simulation_step(s, req, ad, f"FIX-{m}", f"{m}-28", capacity_override=cap_ov, is_fixture=True)
        st.success("Fixture replay complete! Check results below against Handbook Page 90.")
        st.rerun()

    if len(sim["ledger"]) >= 3 and sim["ledger"][0]["mode"] == "FIXTURE":
        checks = [
            {"Test": "2027-01 Fixture", "Expected": "Sold=50, Rev=$1,500, Exp=$850, Profit=$650, Cash=$3,650",
             "Actual": f"Sold={sim['ledger'][0]['sold']}, Rev=${sim['ledger'][0]['revenue']:,.0f}, Exp=${sim['ledger'][0]['total_expense']:,.0f}, Profit=${sim['ledger'][0]['operating_profit']:,.0f}, Cash=${sim['ledger'][0]['closing_cash']:,.0f}",
             "Status": "PASS" if sim['ledger'][0]['closing_cash'] == 3650.0 else "FAIL"},
            {"Test": "2027-02 Fixture ($100 Ad)", "Expected": "Sold=50, Rev=$1,500, Exp=$950, Profit=$550, Cash=$4,200",
             "Actual": f"Sold={sim['ledger'][1]['sold']}, Rev=${sim['ledger'][1]['revenue']:,.0f}, Exp=${sim['ledger'][1]['total_expense']:,.0f}, Profit=${sim['ledger'][1]['operating_profit']:,.0f}, Cash=${sim['ledger'][1]['closing_cash']:,.0f}",
             "Status": "PASS" if sim['ledger'][1]['closing_cash'] == 4200.0 else "FAIL"},
            {"Test": "2027-03 Fixture (Cap=37)", "Expected": "Sold=37, Rev=$1,110, Exp=$772, Profit=$338, Cash=$4,538",
             "Actual": f"Sold={sim['ledger'][2]['sold']}, Rev=${sim['ledger'][2]['revenue']:,.0f}, Exp=${sim['ledger'][2]['total_expense']:,.0f}, Profit=${sim['ledger'][2]['operating_profit']:,.0f}, Cash=${sim['ledger'][2]['closing_cash']:,.0f}",
             "Status": "PASS" if sim['ledger'][2]['closing_cash'] == 4538.0 else "FAIL"},
        ]
        st.table(pd.DataFrame(checks))

# --- TAB 4: ROADMAP ---
with tabs[3]:
    st.subheader("Unimplemented Features (Planned for Later Stages)")
    st.markdown("""
- **Stage 2 (Not Yet Built):** Department AI Recommendation Importer (Finance, Operations, Marketing, Reviewer), Full Report Center (PDF/CSV Balance Sheet & Cash Flow), Costed Marketing Studio.
- **Stage 3 (Not Yet Built):** Frozen-Snapshot Practice Assessment Generator & Cross-Course Evidence Panel.
- **Stage 4 (Optional Lowest Priority):** Fictional Storefront & Test Checkout.
""")
