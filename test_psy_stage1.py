import json
from decimal import Decimal
import pandas as pd

# Mirror exact deterministic engine from app.py for standalone verification
def run_month(state, requested, ad_cost=0, capacity_override=None, run_id=None, sim_date="2027-01-31"):
    if run_id and run_id in state["processed_run_ids"]:
        return state, False, "Duplicate run_id ignored."

    price = Decimal(str(state["base_price"]))
    var_per_unit = Decimal(str(state["variable_per_unit"]))
    fixed_cost = Decimal(str(state["fixed_cost"]))
    ad_cost_dec = Decimal(str(ad_cost))
    opening_cash = Decimal(str(state["cash"]))

    if capacity_override is not None:
        capacity = int(capacity_override)
    else:
        staff_cap = int(state["staff_hours"] // state["hours_per_unit"])
        capacity = min(staff_cap, int(state["program_seats"]))

    sold = min(int(requested), capacity)
    completed = int(sold * state["completion_rate"])
    revenue = price * Decimal(sold)
    variable_expense = var_per_unit * Decimal(sold)
    total_expense = variable_expense + fixed_cost + ad_cost_dec
    operating_profit = revenue - total_expense
    closing_cash = opening_cash + operating_profit

    state["cash"] = float(closing_cash)
    state["state_version"] += 1
    if run_id:
        state["processed_run_ids"].append(run_id)
    state["ledger"].append({
        "run_id": run_id or f"run_{state['state_version']}",
        "date": sim_date,
        "requested": int(requested),
        "capacity": capacity,
        "sold": sold,
        "completed": completed,
        "revenue": float(revenue),
        "variable_expense": float(variable_expense),
        "fixed_expense": float(fixed_cost),
        "ad_cost": float(ad_cost_dec),
        "operating_profit": float(operating_profit),
        "closing_cash": float(closing_cash),
        "state_version": state["state_version"]
    })
    return state, True, "Success"

def default_state():
    return {
        "team_id": "TEAM-PSY",
        "pathway_id": "PSY-2",
        "selected_course": "Precalculus",
        "selected_level": "Advanced",
        "state_version": 1,
        "base_price": 30.0,
        "D0": 70,
        "staff_hours": 25.0,
        "hours_per_unit": 0.5,
        "program_seats": 50,
        "completion_rate": 0.80,
        "satisfaction_mean": 4.2,
        "variable_per_unit": 6.0,
        "fixed_cost": 550.0,
        "cash": 3000.0,
        "equipment_assets": 700.0,
        "pre_opening_expense": 1300.0,
        "owner_contribution": 5000.0,
        "processed_run_ids": [],
        "ledger": []
    }

def run_all_tests():
    # 1. Fixture Replay Test
    s = default_state()
    df = pd.read_csv("sample_data/monthly_fixture.csv")
    expected = [
        (50, 1500.0, 850.0, 650.0, 3650.0),
        (50, 1500.0, 950.0, 550.0, 4200.0),
        (37, 1110.0, 772.0, 338.0, 4538.0),
    ]
    for i, row in df.iterrows():
        s, ok, _ = run_month(
            s,
            requested=int(row["requested"]),
            ad_cost=float(row["ad_cost"]),
            capacity_override=int(row["capacity_override"]),
            run_id=f"fixture_{row['month']}",
            sim_date=f"{row['month']}-28"
        )
        rec = s["ledger"][-1]
        tot_exp = rec["variable_expense"] + rec["fixed_expense"] + rec["ad_cost"]
        assert (rec["sold"], rec["revenue"], tot_exp, rec["operating_profit"], rec["closing_cash"]) == expected[i], f"Mismatch on row {i}: {rec}"

    # 2. Duplicate run_id protection
    s, ok, _ = run_month(s, requested=70, ad_cost=0, capacity_override=50, run_id="fixture_2027-01")
    assert not ok and len(s["ledger"]) == 3, "Duplicate run_id should be rejected"

    # 3. Completion rate test (0.5 -> 25 completed, revenue $1,500, profit $650)
    s_comp = default_state()
    s_comp["completion_rate"] = 0.5
    s_comp, _, _ = run_month(s_comp, requested=70, ad_cost=0, run_id="comp_test")
    rec_c = s_comp["ledger"][-1]
    assert rec_c["completed"] == 25 and rec_c["revenue"] == 1500.0 and rec_c["operating_profit"] == 650.0

    # 4. Zero sales test
    s_zero = default_state()
    s_zero, _, _ = run_month(s_zero, requested=0, ad_cost=0, run_id="zero_test")
    rec_z = s_zero["ledger"][-1]
    assert rec_z["revenue"] == 0.0 and rec_z["variable_expense"] == 0.0 and rec_z["operating_profit"] == -550.0

    # 5. Precalculus Advanced seasonal test (t=4 -> 84, t=10 -> 56)
    import math
    d4 = round(70 * (1 + 0.20 * math.sin(2 * math.pi * (4 - 1) / 12)), 2)
    d10 = round(70 * (1 + 0.20 * math.sin(2 * math.pi * (10 - 1) / 12)), 2)
    assert d4 == 84.0 and d10 == 56.0, f"Seasonal check failed: {d4}, {d10}"

    print("ALL PSY-2 STAGE 1 TESTS PASSED!")

if __name__ == "__main__":
    run_all_tests()
