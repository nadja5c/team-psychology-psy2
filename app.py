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
        "campaigns": [],
        "ai_recommendations": [],
        "decisions": []
    }

if "sim" not in st.session_state:
    st.session_state.sim = init_state()

for key, default_val in [("campaigns", []), ("ai_recommendations", []), ("decisions", [])]:
    if key not in st.session_state.sim:
        st.session_state.sim[key] = default_val

sim = st.session_state.sim

def var_unit_cost(s):
    return sum(s["variable_lines"].values())

def fixed_month_cost(s):
    return sum(s["fixed_lines"].values())

def derived_capacity(s):
    staff_cap = int(math.floor(s["staff_hours"] / s["hours_per_unit"])) if s["hours_per_unit"] > 0 else 0
    return min(staff_cap, int(s["program_seats"]))

def record_simulation_step(s, requested, ad_cost, run_id, sim_date, capacity_override=None, is_fixture=False, campaign_id=""):
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
        "campaign_id": campaign_id,
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
                for key, default_val in [("campaigns", []), ("ai_recommendations", []), ("decisions", [])]:
                    if key not in imported:
                        imported[key] = default_val
                st.session_state.sim = imported
                st.success(f"Restored snapshot v{imported['state_version']}!")
                st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON file: {e}")

    st.divider()
    if st.button("Reset to PSY Opening Baseline", type="secondary", use_container_width=True):
        st.session_state.sim = init_state()
        st.rerun()

st.header("Stage 2 Dashboard: Study Habits & Wellness Education Studio")
st.caption("Stage 2 Active: Core Engine + AI Department Handoffs + Report Center + Costed Marketing Studio + Decision Memos. (Stage 3 Snapshot Assessments planned next.)")

c1, c2, c3, c4, c5 = st.columns(5)
cap_now = derived_capacity(sim)
c1.metric("Current Cash", f"${sim['cash']:,.2f}")
c2.metric("Monthly Seat Capacity", f"{cap_now} seats", help="min(floor(staff_hours / hours_per_unit), program_seats)")
c3.metric("Base Seat Price", f"${sim['base_price']:,.2f}")
c4.metric("Variable / Fixed Cost", f"${var_unit_cost(sim):.2f} / ${fixed_month_cost(sim):.0f}")
c5.metric("Quality (Separate from Rev)", f"{int(sim['completion_rate']*100)}% compl. | {sim['satisfaction_mean']}/5")

tabs = st.tabs([
    "1. Inputs & Run Month",
    "2. Precalculus Math (PSY-2)",
    "3. AI Department Handoffs",
    "4. Report Center & Decisions",
    "5. Costed Marketing Studio",
    "6. Ledger & Tests"
])

with tabs[0]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Startup Financing & Opening Balances")
        st.markdown(f"- **Owner Contribution:** ${sim['owner_contribution']:,.2f}\n- **Equipment Assets (Capitalized):** ${sim['equipment_assets']:,.2f}\n- **Pre-Opening Expense:** ${sim['pre_opening_expense']:,.2f} (Retained earnings start at -${sim['pre_opening_expense']:,.2f})\n- **Opening Spendable Cash:** $3,000.00 (Not counted as sales revenue)")

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
    approved_campaigns = [c for c in sim["campaigns"] if c["status"] == "APPROVED_READY"]
    camp_options = ["None ($0)"] + [f"{c['campaign_id']} - {c['offering']} (${c['total_cost']:,.2f})" for c in approved_campaigns]
    selected_camp_label = st.selectbox("Attach Approved Marketing Campaign (Charged Once at Launch)", camp_options)

    linked_ad_cost = 0.0
    linked_camp_id = ""
    if selected_camp_label != "None ($0)":
        linked_camp_id = selected_camp_label.split(" - ")[0]
        for c in approved_campaigns:
            if c["campaign_id"] == linked_camp_id:
                linked_ad_cost = float(c["total_cost"])

    r1, r2, r3, r4 = st.columns(4)
    req_input = r1.number_input("Requested Seats This Month", min_value=0, max_value=500, value=int(sim["D0"]), step=1)
    ad_input = r2.number_input("Ad Expense This Month ($)", min_value=0.0, max_value=5000.0, value=linked_ad_cost, step=25.0)
    date_input = r3.text_input("Month-End Date (YYYY-MM-DD)", value=f"2027-{len(sim['ledger'])+1:02d}-28")
    run_id_input = r4.text_input("Unique Run ID", value=f"RUN-{len(sim['ledger'])+1:03d}")

    if st.button("Approve & Advance Simulation Month", type="primary"):
        ok, msg = record_simulation_step(sim, req_input, ad_input, run_id_input, date_input, is_fixture=False, campaign_id=linked_camp_id)
        if ok:
            if linked_camp_id:
                for c in sim["campaigns"]:
                    if c["campaign_id"] == linked_camp_id:
                        c["status"] = "LAUNCHED"
                        c["launched_run_id"] = run_id_input
            st.success(msg)
            st.rerun()
        else:
            st.warning(msg)

with tabs[1]:
    st.subheader("Math Skills & Challenge Level Panel | Precalculus (PSY-2)")
    level_choice = st.selectbox(
        "Challenge Level (Teacher-Approved: Advanced)",
        ["Foundation", "Applied", "Advanced"],
        index=["Foundation", "Applied", "Advanced"].index(sim["selected_level"])
    )
    if level_choice != sim["selected_level"]:
        sim["selected_level"] = level_choice
        st.info(f"Switched view to {level_choice}. Teacher approval is required before changing official level.")

    F = fixed_month_cost(sim)
    v = var_unit_cost(sim)
    cap = max(1, derived_capacity(sim))
    p0 = sim["base_price"]
    D0 = sim["D0"]

    if level_choice == "Foundation":
        st.markdown("### Foundation: Average Cost Rational Function $A(s) = \frac{F}{s} + v$")
        st.write(f"**Equation:** $A(s) = \frac{{{F:.0f}}}{{s}} + {v:.2f}$ on practical domain $0 < s \le {cap}$ seats.")
        st.markdown(f"- **Vertical Asymptote:** $s = 0$ (Average cost per seat is undefined when 0 seats are sold).\n- **Horizontal Asymptote:** $y = {v:.2f}$ (As volume grows, fixed costs spread out and cost per seat approaches ${v:.2f}).\n- **At Full Capacity ($s = {cap}$):** $A({cap}) = \${F/cap + v:.2f}$ per seat.")
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
        st.markdown(f"- **Demand Function:** $q(p) = \max(0, {intercept:.0f} - {slope:.4f}p)$ on $0 \le p \le {2*p0:.0f}$\n- **Capacity-Constrained Sales:** $s(p) = \min({cap}, q(p))$\n- **Composed Revenue & Cost:** $R(p) = p \cdot s(p)$ and $C(s(p)) = {F:.0f} + {v:.2f} \cdot s(p)$\n- **Capacity Breakpoint Price:** $p = \${p_break:.2f}$ (Below this price, demand exceeds your {cap}-seat cap!)")
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
        st.markdown(f"**Assumed Seasonal Model:** $D(t) = D_0 \left(1 + 0.20 \sin\left(\frac{{2\pi(t - 1)}}{{12}}\right)\right)$ for month index $t = 1 \dots 12$.\n- **Period:** 12 months | **Peak Demand:** Month $t = 4$ ($1.20 \times D_0 = {1.2*D0:.0f}$ seats) | **Lowest Demand:** Month $t = 10$ ($0.80 \times D_0 = {0.8*D0:.0f}$ seats).\n- **Business Insight:** Even at the seasonal low ($t = 10$, 56 seats at baseline), demand still exceeds the studio's 50-seat capacity cap—meaning capacity, not seasonal advertising, is your primary bottleneck!")
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

with tabs[2]:
    st.subheader("AI Department Handoffs (Manual Workflow)")
    st.info("Manual Handoff Mode: Export your snapshot, paste it into your Finance, Operations, Marketing, or Reviewer Gem/Skill, and log the verified recommendation here before approving changes.")

    h1, h2 = st.columns(2)
    with h1:
        st.markdown("#### Step 1: Copy-Ready Invocation Prompt")
        dept_role = st.selectbox("Select Department Role", ["Finance", "Operations", "Market and Marketing", "Independent Reviewer"])
        dept_question = st.text_input("Decision Question for Assistant", value="Compare keeping seat price at $30 vs. increasing price to $38.57 under our 50-seat cap.")
        prompt_text = (
            f"Role: {dept_role}\n"
            f"Team and pathway: {sim['team_id']} | {sim['pathway_id']}\n"
            f"Snapshot: {sim['snapshot_id']} (state_version = {sim['state_version']})\n"
            f"Course and level: {sim['selected_course']} ({sim['selected_level']})\n"
            f"Current Inputs: price=${sim['base_price']}, D0={sim['D0']}, capacity={cap_now} seats, variable=${var_unit_cost(sim)}/unit, fixed=${fixed_month_cost(sim)}/mo, cash=${sim['cash']:,.2f}, completion_rate={sim['completion_rate']}\n"
            f"Question: {dept_question}\n"
            f"Constraints: Nonclinical educational programs only; max 50 seats unless capacity expanded; separate profit from cash.\n"
            f"Return proposals only; identify dependencies and one independent student check."
        )
        st.code(prompt_text, language="text")

    with h2:
        st.markdown("#### Step 2: Log & Verify Department Recommendation")
        with st.form("log_ai_rec_form"):
            rec_role = st.selectbox("Role Reporting", ["Finance", "Operations", "Market and Marketing", "Independent Reviewer"])
            rec_ver = st.number_input("Snapshot State Version Cited", min_value=1, value=int(sim["state_version"]), step=1)
            rec_summary = st.text_area("Proposed Recommendation & Math Summary", placeholder="e.g., Raising price to $38 keeps demand at ~51 seats (still filling 50-seat cap) and increases monthly profit by $400.")
            rec_checker = st.text_input("Independent Student Checker Name (Cannot be sole author)")
            rec_status = st.selectbox("Approval Status", ["PENDING_CHECK", "VERIFIED_APPROVED", "REJECTED"])
            submitted_rec = st.form_submit_button("Save Recommendation Record")
            if submitted_rec:
                if int(rec_ver) != int(sim["state_version"]):
                    st.error(f"Rejected: Recommendation cites v{rec_ver}, but current simulation is v{sim['state_version']}. Refresh snapshot first!")
                elif not rec_summary.strip() or not rec_checker.strip():
                    st.error("Please enter both the recommendation summary and the independent student checker's name.")
                else:
                    sim["ai_recommendations"].append({
                        "rec_id": f"REC-{len(sim['ai_recommendations'])+1:03d}",
                        "state_version": int(rec_ver),
                        "role": rec_role,
                        "summary": rec_summary.strip(),
                        "checker": rec_checker.strip(),
                        "status": rec_status,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("Department recommendation logged!")
                    st.rerun()

    if sim["ai_recommendations"]:
        st.markdown("#### Logged Department Recommendations")
        st.dataframe(pd.DataFrame(sim["ai_recommendations"]), use_container_width=True)

with tabs[3]:
    st.subheader("Report Center & Two-Report Decision Memo")
    st.caption(f"Team: {sim['team_id']} | Pathway: {sim['pathway_id']} | State: v{sim['state_version']} ({sim['snapshot_id']}) | Currency: USD | Viewing reports does not advance time.")

    if not sim["ledger"]:
        st.warning("Your ledger is currently empty. Run at least one month in Tab 1 (or run the Fixture Test in Tab 6) to populate actual financial and operations reports.")
    else:
        df_led = pd.DataFrame(sim["ledger"])
        tot_rev = df_led["revenue"].sum()
        tot_var = df_led["variable_expense"].sum()
        tot_fix = df_led["fixed_expense"].sum()
        tot_ad = df_led["ad_cost"].sum()
        net_op = df_led["operating_profit"].sum()
        gross_margin = ((tot_rev - tot_var) / tot_rev * 100) if tot_rev > 0 else None

        rep_tab1, rep_tab2, rep_tab3, rep_tab4 = st.tabs([
            "Income & Cash Flow",
            "Operations & Quality",
            "Scenario Forecast (3-Way)",
            "Simplified Balance Sheet"
        ])

        with rep_tab1:
            col_inc, col_cf = st.columns(2)
            with col_inc:
                st.markdown("**Cumulative Income Statement (Actual Ledger)**")
                inc_df = pd.DataFrame([
                    {"Line Item": "Program Sales Revenue", "Amount ($)": tot_rev},
                    {"Line Item": "Variable Delivery & Materials Cost", "Amount ($)": -tot_var},
                    {"Line Item": "Gross Profit", "Amount ($)": tot_rev - tot_var},
                    {"Line Item": "Fixed Monthly Operating Expense", "Amount ($)": -tot_fix},
                    {"Line Item": "Own-Studio Marketing Expense", "Amount ($)": -tot_ad},
                    {"Line Item": "Net Operating Profit (Excl. Tax/Depr.)", "Amount ($)": net_op},
                ])
                st.dataframe(inc_df, use_container_width=True)
                st.write(f"**Gross Margin:** {f'{gross_margin:.1f}%' if gross_margin is not None else 'N/A (Zero revenue)'}")

            with col_cf:
                st.markdown("**Cash Flow Reconciliation (Actual Ledger)**")
                cf_df = pd.DataFrame([
                    {"Cash Flow Item": "Opening Post-Startup Cash", "Amount ($)": 3000.0},
                    {"Cash Flow Item": "Net Cash from Operating Profit", "Amount ($)": net_op},
                    {"Cash Flow Item": "Additional CapEx / Loan Principal", "Amount ($)": 0.0},
                    {"Cash Flow Item": "Closing Cash Balance", "Amount ($)": sim["cash"]},
                ])
                st.dataframe(cf_df, use_container_width=True)

            st.download_button(
                "Export Full Ledger & Financial Report (CSV)",
                data=df_led.to_csv(index=False),
                file_name=f"{sim['team_id']}_financial_report_v{sim['state_version']}.csv",
                mime="text/csv"
            )

        with rep_tab2:
            st.markdown("**Operations, Capacity & Quality Report (Actual Ledger)**")
            tot_req = df_led["requested"].sum()
            tot_sold = df_led["sold"].sum()
            tot_lost = df_led["lost_demand"].sum()
            tot_comp = df_led["completed"].sum()
            tot_cap = df_led["capacity"].sum()
            util_pct = (tot_sold / tot_cap * 100) if tot_cap > 0 else 0.0
            comp_pct = (tot_comp / tot_sold * 100) if tot_sold > 0 else None

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Requested vs. Sold", f"{tot_sold} / {tot_req} seats")
            m2.metric("Unserved Lost Demand", f"{tot_lost} seats")
            m3.metric("Capacity Utilization", f"{util_pct:.1f}%")
            m4.metric("Program Completion", f"{comp_pct:.1f}%" if comp_pct is not None else "N/A")
            st.dataframe(df_led[["date", "run_id", "requested", "capacity", "sold", "lost_demand", "completed", "satisfaction_mean"]], use_container_width=True)

        with rep_tab3:
            st.markdown("**Next-Month Scenario Forecast (Assumed Multipliers: 0.90 / 1.00 / 1.10)**")
            st.caption("Projection only—kept strictly separate from the actual ledger.")
            scen_rows = []
            for label, mult in [("Downside (0.90x D0)", 0.90), ("Baseline (1.00x D0)", 1.00), ("Upside (1.10x D0)", 1.10)]:
                proj_req = int(math.floor(sim["D0"] * mult))
                proj_sold = min(proj_req, cap_now)
                proj_rev = proj_sold * sim["base_price"]
                proj_exp = proj_sold * var_unit_cost(sim) + fixed_month_cost(sim)
                scen_rows.append({
                    "Scenario": label,
                    "Projected Demand": proj_req,
                    "Capacity Cap": cap_now,
                    "Projected Sold": proj_sold,
                    "Projected Revenue ($)": proj_rev,
                    "Projected Expense ($)": proj_exp,
                    "Projected Profit ($)": proj_rev - proj_exp
                })
            st.table(pd.DataFrame(scen_rows))

        with rep_tab4:
            st.markdown("**Simplified Balance Sheet (Reconciled)**")
            assets_total = sim["cash"] + sim["equipment_assets"]
            retained_earnings = -sim["pre_opening_expense"] + net_op
            liab_eq_total = sim["loan_debt"] + sim["owner_contribution"] + retained_earnings
            bs_df = pd.DataFrame([
                {"Category": "Asset: Spendable Cash", "Balance ($)": sim["cash"]},
                {"Category": "Asset: Studio Equipment (Gross)", "Balance ($)": sim["equipment_assets"]},
                {"Category": "TOTAL ASSETS", "Balance ($)": assets_total},
                {"Category": "Liability: Loans Payable", "Balance ($)": sim["loan_debt"]},
                {"Category": "Equity: Owner Contribution", "Balance ($)": sim["owner_contribution"]},
                {"Category": "Equity: Retained Earnings (-$1,300 pre-open + net profit)", "Balance ($)": retained_earnings},
                {"Category": "TOTAL LIABILITIES + EQUITY", "Balance ($)": liab_eq_total},
            ])
            st.table(bs_df)

    st.divider()
    st.subheader("Record Two-Report Decision Memo")
    with st.form("decision_memo_form"):
        d_q = st.text_input("1. Business Question", placeholder="Should we keep price at $30 or raise price toward our $38.57 capacity breakpoint?")
        d_reports = st.multiselect("2. Cite at Least TWO Reports Inspected", ["Income Statement", "Cash Flow Report", "Operations & Capacity Report", "Scenario Forecast", "Simplified Balance Sheet"], default=["Income Statement", "Operations & Capacity Report"])
        d_alts = st.text_area("3. Compare Baseline vs. Two Alternatives & Course Math", placeholder="Baseline ($30, 50 seats = $650 profit) vs. Alt 1 ($38 price, 50 seats = $1,050 profit) vs. Alt 2 (Add 10 staff hours + expand room).")
        d_uncert = st.text_input("4. Uncertainty, Quality & Cross-Department Effect", placeholder="Higher price could reduce accessibility for students; completion rate (80%) must be monitored separately.")
        d_action = st.text_input("5. Chosen Action & Measurable Prediction")
        d_owner = st.text_input("6. Action Owner & Student Checker")
        save_memo = st.form_submit_button("Save Decision Memo")
        if save_memo:
            if len(d_reports) < 2 or not d_q.strip() or not d_action.strip():
                st.error("Please fill in the question, chosen action, and cite at least TWO reports.")
            else:
                sim["decisions"].append({
                    "decision_id": f"DEC-{len(sim['decisions'])+1:03d}",
                    "snapshot_id": sim["snapshot_id"],
                    "question": d_q.strip(),
                    "reports_cited": ", ".join(d_reports),
                    "alternatives_math": d_alts.strip(),
                    "uncertainty_quality": d_uncert.strip(),
                    "chosen_action": d_action.strip(),
                    "owner_checker": d_owner.strip()
                })
                st.success("Decision Memo saved to simulation record!")
                st.rerun()

    if sim["decisions"]:
        st.dataframe(pd.DataFrame(sim["decisions"]), use_container_width=True)

with tabs[4]:
    st.subheader("Costed Marketing Studio (PSY Offerings)")
    st.caption("Advertising is an operating expense charged once at launch. No automatic demand lift is assumed; compare equal-budget variants and test truthfully.")

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("#### Draft & Cost a Campaign")
        camp_id = st.text_input("Unique Campaign ID", value=f"CAMP-{len(sim['campaigns'])+1:03d}")
        offering_choice = st.selectbox("PSY Offering", ["Study-strategy workshop", "Time-management seminar", "General stress-awareness education"])
        audience_txt = st.text_input("Target Student Audience", value="High school juniors & seniors preparing for finals")
        channel_choice = st.selectbox("Channel", ["Campus Flyer (Print)", "School Newsletter Email", "Student Portal Banner"])
        headline_txt = st.text_input("Approved Truthful Headline (No Clinical Claims)", value="Build Sustainable Study Routines Before Exam Week")
        cta_txt = st.text_input("Call to Action & Fictional Contact", value="Reserve 1 of 50 workshop seats at studywellness-demo.edu")

    with m_col2:
        st.markdown("#### Itemized Campaign Cost Calculator")
        design_hrs = st.number_input("Design Labor Hours", min_value=0.0, value=2.0, step=0.5)
        design_rate = st.number_input("Design Labor Rate ($/hr)", min_value=0.0, value=15.0, step=5.0)
        asset_cost = st.number_input("Licensed Graphics / Assets ($)", min_value=0.0, value=10.0, step=5.0)
        print_qty = st.number_input("Print Quantity (flyers)", min_value=0, value=100, step=25)
        print_unit = st.number_input("Print Unit Cost ($/flyer)", min_value=0.0, value=0.25, step=0.05)
        dist_cost = st.number_input("Distribution / Placement Cost ($)", min_value=0.0, value=35.0, step=5.0)

        total_camp_cost = round(design_hrs * design_rate + asset_cost + print_qty * print_unit + dist_cost, 2)
        st.metric("Total Campaign Expense (Charged Once)", f"${total_camp_cost:,.2f}")

        if st.button("Save & Approve Campaign Draft for Launch", type="primary"):
            if any(c["campaign_id"] == camp_id for c in sim["campaigns"]):
                st.error(f"Campaign ID '{camp_id}' already exists. Use a unique ID.")
            else:
                sim["campaigns"].append({
                    "campaign_id": camp_id,
                    "offering": offering_choice,
                    "channel": channel_choice,
                    "audience": audience_txt,
                    "headline": headline_txt,
                    "cta": cta_txt,
                    "total_cost": total_camp_cost,
                    "status": "APPROVED_READY",
                    "launched_run_id": ""
                })
                st.success(f"Campaign {camp_id} approved (${total_camp_cost:,.2f})! Select it in Tab 1 when running your next month.")
                st.rerun()

    st.divider()
    st.markdown("#### Printable Flyer Preview & Copyable Ad Text")
    flyer_preview = (
        f"====================================================\n"
        f"[DEMONSTRATION EDUCATIONAL STUDIO - NONCLINICAL]\n"
        f"{headline_txt.upper()}\n"
        f"Offering: {offering_choice} | Price: ${sim['base_price']:,.2f}/seat\n"
        f"Audience: {audience_txt}\n"
        f"Action: {cta_txt}\n"
        f"Campaign ID: {camp_id} | Est. Cost: ${total_camp_cost:,.2f}\n"
        f"===================================================="
    )
    st.code(flyer_preview, language="text")

    if sim["campaigns"]:
        st.markdown("#### Campaign Register & Acquisition Cost Check")
        st.dataframe(pd.DataFrame(sim["campaigns"]), use_container_width=True)

with tabs[5]:
    st.subheader("Dated Event Ledger (Actual Simulated Transactions)")
    if sim["ledger"]:
        st.dataframe(pd.DataFrame(sim["ledger"]), use_container_width=True)
    else:
        st.info("No transactions recorded yet.")

    st.divider()
    st.subheader("Stage 1 & 2 Acceptance Test Suite (PSY Package)")
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
        st.success("Fixture replay complete!")
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
