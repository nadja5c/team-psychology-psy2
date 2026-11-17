# Team Psychology - Study Habits & Wellness Education Studio (PSY-2)

Career Venture Lab Streamlit Dashboard (Stage 1: Core Inputs, Precalculus Math Panel, Ledger, Save/Load JSON, and Acceptance Tests).

## Setup & Local Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the automated acceptance test suite:
   ```bash
   python tests/test_psy_stage1.py
   ```
3. Launch the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```

## Render Deployment Command
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```
