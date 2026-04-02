# edutut/tgassess/dashboard/aatdb.py 
# --------- AAT Executive Dashboard ----------
# FROZEN 31.03.2026 15:30 Hours



import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import numpy as np

import os
from dotenv import load_dotenv
from openai import OpenAI

# =====================================================
# LOAD ENV (LOCAL)
# =====================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key) if api_key else None


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="AAT 2.0 Executive Dashboard", page_icon = "🧞", layout="wide")

COLORS = ["#FFD700","#00C2FF","#FF7F50","#7CFC00","#FF69B4","#8A2BE2"]

# =========================================================
# HEADER
# =========================================================
colA, colB = st.columns([8,1])
with colA:
    st.title("📊 Assess-A-Thon Executive Dashboard v2.0")
    st.caption("**TeachGenie**.ai Analytics | LPU 26th March 2026 - 28th March 2026 | ©2026 **YOM** Private Limited")
with colB:
    try:
        st.image(Image.open("assets/AAT-Mascot.png"), width=100)
    except:
        st.write("🧞")

# =========================================================
# LOAD
# =========================================================
@st.cache_data
def load_data():
    df = pd.read_excel("AAT-Data-28.03.2026.xlsx")
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_data()

# =========================================================
# SAFE COLUMN DETECTOR
# =========================================================
def get_col_safe(df, index):
    return df.columns[index] if len(df.columns) > index else None

# =========================================================
# COLUMN LOCK (ROBUST + FUTURE-PROOF)
# =========================================================
COL_UID = get_col_safe(df, 1)
COL_NAME = get_col_safe(df, 2)
COL_REG_COUNT = get_col_safe(df, 4)
COL_TOTAL = get_col_safe(df, 29)   # 🔥 CRITICAL FIX
COL_REG_TIME = get_col_safe(df, 31)
COL_SUB_TIME = get_col_safe(df, 32)

COL_DISC = None
COL_CAT = None
COL_GRADE = None
COL_MARKS = None

for col in df.columns:
    name = str(col).lower()

    if "discipline" in name:
        COL_DISC = col

    elif "category" in name:
        COL_CAT = col

    elif "grade" in name:
        COL_GRADE = col

    elif "mark" in name or "score" in name:
        COL_MARKS = col

# =========================================================
# FINAL MARKS COLUMN RESOLUTION (CRITICAL)
# =========================================================
# Priority: detected marks column → fallback to COL_TOTAL
FINAL_MARKS_COL = COL_MARKS if COL_MARKS else COL_TOTAL

# Safety check
if FINAL_MARKS_COL is None:
    st.error("❌ Unable to detect Marks/Score column. Check dataset format.")
    st.stop()

# Create unified numeric marks column (USE THIS EVERYWHERE)
df["Marks"] = pd.to_numeric(df[FINAL_MARKS_COL], errors="coerce")

# =========================================================
# CLEAN
# =========================================================
df = df[df[COL_UID].notna()]

df[COL_REG_TIME] = pd.to_datetime(df[COL_REG_TIME], errors="coerce")
df[COL_SUB_TIME] = pd.to_datetime(df[COL_SUB_TIME], errors="coerce")

# Event window
df = df[
    (df[COL_REG_TIME] >= "2026-03-26 10:00") &
    (df[COL_REG_TIME] <= "2026-03-29 23:00")
]

df["completed"] = df[COL_REG_COUNT] == 3

df_valid = df[df[COL_REG_TIME].notna()].copy()

df_valid["delay_minutes"] = (
    (df_valid[COL_SUB_TIME] - df_valid[COL_REG_TIME]).dt.total_seconds()/60
)

# =========================================================
# FEATURE ENGINEERING (CRITICAL FIX)
# =========================================================

# Ensure datetime columns are valid
df_valid = df_valid.copy()

df_valid[COL_REG_TIME] = pd.to_datetime(df_valid[COL_REG_TIME], errors="coerce")
df_valid[COL_SUB_TIME] = pd.to_datetime(df_valid[COL_SUB_TIME], errors="coerce")

# Drop rows where registration time is missing
df_valid = df_valid[df_valid[COL_REG_TIME].notna()]

# SAFE creation of date & hour
df_valid["date"] = df_valid[COL_REG_TIME].dt.date
df_valid["hour"] = df_valid[COL_REG_TIME].dt.hour

# Delay
df_valid["delay_minutes"] = (
    (df_valid[COL_SUB_TIME] - df_valid[COL_REG_TIME])
    .dt.total_seconds() / 60
)

# Safety fallback (never break charts)
if "date" not in df_valid.columns:
    df_valid["date"] = "Unknown"

if "hour" not in df_valid.columns:
    df_valid["hour"] = 0

# =========================================================
# GLOBAL PARTICIPATION METRICS (SHARED ACROSS TABS)
# =========================================================

df_fac = pd.read_excel("FacultyDetails.xlsx")
df_aat = pd.read_excel("AAT-Data-31.03.2026.xlsx")

df_fac.columns = [str(c).strip() for c in df_fac.columns]
df_aat.columns = [str(c).strip() for c in df_aat.columns]

# Column mapping
FAC_UID = df_fac.columns[2]   # Column C
AAT_UID = df_aat.columns[1]   # Column B
AAT_REG = df_aat.columns[4]   # Column E

# Clean UID
df_fac[FAC_UID] = pd.to_numeric(df_fac[FAC_UID], errors="coerce")
df_aat[AAT_UID] = pd.to_numeric(df_aat[AAT_UID], errors="coerce")

df_fac = df_fac.dropna(subset=[FAC_UID])
df_aat = df_aat.dropna(subset=[AAT_UID])

df_fac[FAC_UID] = df_fac[FAC_UID].astype(int)
df_aat[AAT_UID] = df_aat[AAT_UID].astype(int)

df_fac = df_fac.drop_duplicates(subset=[FAC_UID])
df_aat = df_aat.drop_duplicates(subset=[AAT_UID])

# Registration logic
df_aat[AAT_REG] = pd.to_numeric(df_aat[AAT_REG], errors="coerce").fillna(0)

df_aat["Status"] = df_aat[AAT_REG].apply(
    lambda x: "Completed" if x == 3 else
              "Partial" if x in [1, 2] else
              "Not Participated"
)

# Metrics
total_faculty = df_fac[FAC_UID].nunique()
completed = df_aat[df_aat["Status"] == "Completed"][AAT_UID].nunique()
partial = df_aat[df_aat["Status"] == "Partial"][AAT_UID].nunique()
participated = completed + partial

participation_rate = (participated / total_faculty * 100) if total_faculty else 0


# =========================================================
# TABS
# =========================================================
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📌 Executive Summary",
    "📊 Participation",
    "⚡ Performance",
    "🏆 Leaderboard",
    "📈 SWOT Analysis",
    "🤖 AI Insights",
    "🔍 Micro Analysis"
])

# =========================================================
# EXECUTIVE SUMMARY 
# =========================================================
with tab0:

    st.markdown("# 🎓 Executive Intelligence Brief")
    st.caption("Assess-A-Thon 2.0 | Institutional Capability Analytics | Powered by TeachGenie")

    # =====================================================
    # CHAPTER 1: INSTITUTIONAL PULSE
    # =====================================================
    st.markdown("## 📊 Chapter 1: Institutional Pulse")

    total_participants = df_valid[COL_UID].nunique()
    completion_rate = df_valid["completed"].mean() * 100
    avg_score = pd.to_numeric(df_valid[df_valid.columns[29]], errors="coerce").mean()
    avg_delay = df_valid["delay_minutes"].mean()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Participants", total_participants)
    c2.metric("Completion Rate", f"{completion_rate:.2f}%")
    c3.metric("Avg Score", f"{avg_score:.2f}")
    c4.metric("Avg Completion Time", f"{avg_delay:.1f} mins")

    st.markdown("""
**Insight:**  
The institution demonstrates **strong engagement momentum**, however completion efficiency and performance dispersion indicate **structured intervention opportunities**.
""")

    st.markdown("---")

    # =====================================================
    # CHAPTER 2: PARTICIPATION INTELLIGENCE
    # =====================================================
    st.markdown("## 📈 Chapter 2: Participation Intelligence")

    discipline_part = (
        df_valid.groupby(COL_DISC)[COL_UID]
        .nunique()
        .sort_values(ascending=False)
        .reset_index(name="Participants")
    )

    st.plotly_chart(
        px.bar(
            discipline_part,
            x=COL_DISC,
            y="Participants",
            color="Participants",
            color_continuous_scale="Turbo"
        ),
        use_container_width=True
    )

    st.markdown("""
**Key Observations:**
- Participation is **uneven across disciplines**
- High-performing disciplines act as **engagement anchors**
- Low participation areas signal **adoption resistance or awareness gaps**
""")

    st.markdown("---")

    # =====================================================
    # CHAPTER 3: PERFORMANCE INTELLIGENCE
    # =====================================================
    st.markdown("## 📊 Chapter 3: Performance Intelligence")

    df_perf = df_valid.copy()
    df_perf["Score"] = pd.to_numeric(df_perf[COL_TOTAL], errors="coerce")

    st.plotly_chart(
        px.histogram(df_perf, x="Score", nbins=30),
        use_container_width=True
    )

    st.markdown("""
**Key Observations:**
- Performance follows a **near-normal distribution**
- Presence of **long tail indicates capability variance**
- High performers exist but **scalability of excellence is limited**
""")

    st.markdown("---")

    # =====================================================
    # CHAPTER 4: CAPABILITY GAPS & RISKS
    # =====================================================
    st.markdown("## ⚠️ Chapter 4: Capability Gaps & Risks")

    cat_cols = df_valid.columns[5:30]

    df_es = df_valid.copy()

    df_long = df_es.melt(
        id_vars=[COL_UID],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Score_TEMP"
    )

    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")
    df_long = df_long.dropna(subset=["Score_TEMP"])
    df_long = df_long[df_long["Score_TEMP"] > 0]

    weak_areas = (
        df_long.groupby("Category")["Score_TEMP"]
        .mean()
        .sort_values()
        .head(5)
    )

    st.markdown("### 🔻 Critical Weak Areas")

    for k, v in weak_areas.items():
        st.markdown(f"- **{k}** → {v:.2f}")

    st.markdown("""
**Risk Signals:**
- Cognitive depth gaps in higher-order thinking (Analyze, Evaluate)
- Uneven exposure to application-based problem solving
- Partial completion indicates **attention fatigue / UX friction**
""")

    st.markdown("---")

    # =====================================================
    # CHAPTER 5: STRATEGIC BUSINESS PROPOSITION
    # =====================================================
    st.markdown("## 🚀 Chapter 5: Strategic Business Proposition")

    st.markdown("""
### 🧠 TeachGenie Opportunity Layer

Assess-A-Thon is not just an assessment—it is a **faculty intelligence system**.

### 🎯 What This Enables:

- Continuous **faculty capability mapping**
- AI-driven **training need analysis**
- Real-time **intervention tracking**
- Institutional **benchmarking engine**

---

### 💡 Proposed Transformation:

| Layer | Current State | Future State |
|------|-------------|-------------|
| Assessment | Event-based | Continuous Intelligence |
| Training | Generic | AI-Personalized |
| Evaluation | Static | Real-time adaptive |
| Decision | Reactive | Predictive |

---

### 📈 Business Impact:

- ↑ Faculty Effectiveness  
- ↑ Student Learning Outcomes  
- ↓ Training Cost Leakage  
- ↑ Institutional Ranking Readiness  

---

### 🏁 Final Proposition:

**Deploy TeachGenie as an Institutional Intelligence Platform**

→ Convert Assess-A-Thon into a **continuous capability engine**  
→ Build LPU as a **data-driven academic excellence model**
""")

# =========================================================
# PARTICIPATION (FINAL – CLEAN + CORRECT LOGIC)
# =========================================================
with tab1:

    st.subheader("👥 Faculty Participation Overview")

    # =====================================================
    # METRICS (FROM GLOBAL BLOCK)
    # =====================================================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Faculty", total_faculty)
    c2.metric("Participated", participated)
    c3.metric("Completed", completed)
    c4.metric("Participation (%)", round(participation_rate, 2))

    st.markdown("---")

    # =====================================================
    # 📊 STATUS DISTRIBUTION
    # =====================================================
    st.subheader("📊 Participation Status Distribution")

    status_counts = pd.DataFrame({
        "Status": ["Completed", "Partial", "Not Participated"],
        "Count": [
            completed,
            partial,
            total_faculty - participated
        ]
    })

    st.plotly_chart(
        px.pie(
            status_counts,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map={
                "Completed": "#00C853",
                "Partial": "#FFD600",
                "Not Participated": "#D50000"
            }
        ),
        use_container_width=True
    )

    # =====================================================
    # 📊 DISCIPLINE-WISE PARTICIPATION
    # =====================================================
    FAC_DISC = next((c for c in df_fac.columns if "discipline" in c.lower()), None)
    AAT_DISC = next((c for c in df_aat.columns if "discipline" in c.lower()), None)

    if FAC_DISC and AAT_DISC:

        st.subheader("📊 Discipline-wise Participation")

        # Total faculty per discipline
        total_disc = (
            df_fac.groupby(FAC_DISC)[FAC_UID]
            .nunique()
            .reset_index(name="Total")
        )

        # Participated = Completed + Partial
        part_disc = (
            df_aat[df_aat["Status"] != "Not Participated"]
            .groupby(AAT_DISC)[AAT_UID]
            .nunique()
            .reset_index(name="Participated")
        )

        merged = pd.merge(
            total_disc,
            part_disc,
            left_on=FAC_DISC,
            right_on=AAT_DISC,
            how="left"
        ).fillna(0)

        merged["Participated"] = merged["Participated"].astype(int)

        st.plotly_chart(
            px.bar(
                merged,
                x=FAC_DISC,
                y=["Total", "Participated"],
                barmode="group",
                color_discrete_sequence=["#1E2A44", "#FFD700"]
            ),
            use_container_width=True
        )

    # =====================================================
    # PARTICIPATION RATE (FIXED LABELS + STRAIGHT AXIS)
    # =====================================================
    st.subheader("📈 Participation Rate by Discipline (%)")

    merged["Rate (%)"] = (
        merged["Participated"] / merged["Total"] * 100
    ).round(2)

    fig = px.bar(
        merged,
        x=FAC_DISC,
        y="Rate (%)",
        color="Rate (%)",
        color_continuous_scale="Turbo"
    )

    # ✅ FORCE LABELS FOR ALL BARS
    fig.update_traces(
        text=[f"{v:.2f}%" for v in merged["Rate (%)"]],
        textposition="outside",
        cliponaxis=False   # 🔥 ensures labels outside chart are still shown
    )

    # ✅ MAKE X-AXIS STRAIGHT (NO TILT)
    fig.update_layout(
        xaxis_tickangle=90,   # 🔥 removes tilt
        xaxis_title="Discipline",
        yaxis_title="Participation (%)",
        uniformtext_minsize=8,
        uniformtext_mode='show',  # 🔥 forces display
        margin=dict(t=60, b=120)  # 🔥 prevents cutoff of long names
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # 📉 FUNNEL
    # =====================================================
    st.subheader("📉 Participation Funnel")

    funnel_df = pd.DataFrame({
        "Stage": ["Total Faculty", "Participated", "Completed"],
        "Count": [total_faculty, participated, completed]
    })

    st.plotly_chart(
        px.funnel(funnel_df, x="Count", y="Stage"),
        use_container_width=True
    )

    # =====================================================
    # 🚫 NON-PARTICIPATING FACULTY
    # =====================================================
    st.subheader("🚫 Non-Participating Faculty")

    non_participants = df_fac[
        ~df_fac[FAC_UID].isin(
            df_aat[df_aat["Status"] != "Not Participated"][AAT_UID]
        )
    ]

    st.dataframe(non_participants, use_container_width=True)


# =========================================================
# PERFORMANCE 
# =========================================================
with tab2:

    st.subheader("📊 Performance Insights")

    # =====================================================
    # SETUP
    # =====================================================
    COL_TOTAL = df_valid.columns[29]  # Column AD

    df_perf = df_valid.copy()
    df_perf["Marks"] = pd.to_numeric(df_perf[COL_TOTAL], errors="coerce")
    df_perf = df_perf.dropna(subset=["Marks"])

    if df_perf.empty:
        st.warning("No valid marks data available")
        st.stop()

    # =====================================================
    # 🥇 GRADE DISTRIBUTION (PIE)
    # =====================================================
    if COL_GRADE:

        st.subheader("🏆 Grade Distribution")

        g = (
            df_perf[COL_GRADE]
            .dropna()
            .astype(str)
            .value_counts()
            .reset_index()
        )
        g.columns = ["grade", "count"]

        if len(g) > 0:
            st.plotly_chart(
                px.pie(g, names="grade", values="count",
                       color_discrete_sequence=COLORS),
                use_container_width=True
            )

    # =====================================================
    # 📊 MARKS DISTRIBUTION (BUBBLE + PERCENTILES)
    # =====================================================
    st.subheader("📊 Marks Distribution (with Percentiles)")

    import numpy as np

    df_perf["Marks_round"] = df_perf["Marks"].round(0)

    freq = (
        df_perf.groupby("Marks_round")
        .size()
        .reset_index(name="Count")
        .sort_values("Marks_round")
    )

    if len(freq) > 0:

        # slight jitter to avoid overlap
        freq["y"] = np.random.uniform(0.9, 1.1, size=len(freq))

        # Percentiles
        p25 = df_perf["Marks"].quantile(0.25)
        p50 = df_perf["Marks"].quantile(0.50)
        p75 = df_perf["Marks"].quantile(0.75)

        fig = px.scatter(
            freq,
            x="Marks_round",
            y="y",
            size="Count",
            color="Marks_round",
            size_max=60,
            color_continuous_scale="Turbo"
        )

        # Clean layout
        fig.update_layout(
            yaxis=dict(showticklabels=False, title=""),
            xaxis_title="Marks",
            showlegend=False,
            height=500
        )

        fig.update_traces(
            marker=dict(opacity=0.75),
            text=freq["Count"],
            textposition="middle center"
        )

        # =====================================================
        # 📍 ADD PERCENTILE LINES
        # =====================================================
        percentiles = [
            ("P25", p25, "#00C2FF"),
            ("P50", p50, "#FFD700"),
            ("P75", p75, "#FF7F50"),
        ]

        for label, val, color in percentiles:

            fig.add_vline(
                x=val,
                line_width=2,
                line_dash="dash",
                line_color=color
            )

            fig.add_annotation(
                x=val,
                y=1.15,
                text=f"{label}<br>{val:.1f}",
                showarrow=False,
                font=dict(size=12, color=color),
                align="center"
            )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Insufficient data for distribution")

    # =====================================================
    # 📈 BELL CURVE (HISTOGRAM + KDE)
    # =====================================================
    st.subheader("📈 Score Distribution (Bell Curve)")

    fig = px.histogram(
        df_perf,
        x="Marks",
        nbins=30,
        histnorm="probability density"
    )

    # KDE line
    import numpy as np
    from scipy.stats import gaussian_kde

    try:
        kde = gaussian_kde(df_perf["Marks"])
        x_vals = np.linspace(df_perf["Marks"].min(), df_perf["Marks"].max(), 200)
        y_vals = kde(x_vals)

        fig.add_scatter(x=x_vals, y=y_vals, mode='lines', name='KDE')
    except:
        pass  # safe fallback if scipy fails

    fig.update_layout(height=500)

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # 🎯 PERCENTILE BANDS
    # =====================================================
    st.subheader("🎯 Performance Bands (Percentiles)")

    p25 = df_perf["Marks"].quantile(0.25)
    p50 = df_perf["Marks"].quantile(0.50)
    p75 = df_perf["Marks"].quantile(0.75)

    def band(x):
        if x <= p25:
            return "Low"
        elif x <= p50:
            return "Below Avg"
        elif x <= p75:
            return "Above Avg"
        else:
            return "Top"

    df_perf["Band"] = df_perf["Marks"].apply(band)

    band_dist = (
        df_perf["Band"]
        .value_counts()
        .reindex(["Low", "Below Avg", "Above Avg", "Top"])
        .reset_index()
    )
    band_dist.columns = ["Band", "Count"]

    st.plotly_chart(
        px.bar(
            band_dist,
            x="Band",
            y="Count",
            color="Band",
            color_discrete_sequence=COLORS
        ),
        use_container_width=True
    )

    # =====================================================
    # ⏳ DELAY
    # =====================================================
    st.subheader("⏳ Submission Delay")

    df_delay = df_valid.dropna(subset=["delay_minutes"])

    if len(df_delay) > 0:
        st.plotly_chart(
            px.histogram(df_delay, x="delay_minutes", nbins=40,
                         color_discrete_sequence=["#FFD700"]),
            use_container_width=True
        )
    else:
        st.warning("No delay data available")

# =========================================================
# LEADERBOARD (FINAL - CLEAN + BUG-FREE)
# =========================================================
with tab3:

    st.subheader("🏆 Leaderboard")

    # -------------------------------
    # COLUMN SETUP
    # -------------------------------
    cat_cols = df_valid.columns[5:30]   # F → AD
    COL_TOTAL = df_valid.columns[29]    # AD

    df_lb = df_valid.copy()

    # -------------------------------
    # OVERALL SCORE (SOURCE OF TRUTH)
    # -------------------------------
    df_lb["Total Marks"] = pd.to_numeric(df_lb[COL_TOTAL], errors="coerce")
    df_lb = df_lb.dropna(subset=["Total Marks"])

    # -------------------------------
    # 🥇 TOP 3 CHAMPIONS (FIXED)
    # -------------------------------
    st.markdown("### 🏆 Top 3 Champions")

    top3 = df_lb.sort_values("Total Marks", ascending=False).head(3)

    medals = ["🥇", "🥈", "🥉"]
    cols = st.columns(3)

    for i, (_, row) in enumerate(top3.iterrows()):

        highlight = "#FFD700" if i == 0 else "#1E2A44"
        text_color = "black" if i == 0 else "white"

        with cols[i]:
            st.markdown(f"""
            <div style="
                background:{highlight};
                color:{text_color};
                padding:20px;
                border-radius:16px;
                text-align:center;
                min-height:{'260px' if i==0 else '220px'};
                display:flex;
                flex-direction:column;
                justify-content:center;
                gap:8px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.3);
            ">
                <div style="font-size:28px;">{medals[i]}</div>
                <div style="font-size:18px;font-weight:600;">{row.get(COL_NAME,'N/A')}</div>
                <div>{row[COL_UID]}</div>
                <div>🎓 {row.get(COL_DISC,'N/A')}</div>
                <div style="font-size:20px;font-weight:bold;">{round(row['Total Marks'],2)}</div>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------
    # 🥇 TOP 5
    # -------------------------------
    st.markdown("### 🥇 Top 5 Performers")

    top5 = df_lb.sort_values("Total Marks", ascending=False).head(5)

    st.dataframe(
        top5[[COL_UID, COL_NAME, COL_DISC, "Total Marks"]]
        .rename(columns={
            COL_UID: "UID",
            COL_NAME: "Name",
            COL_DISC: "Discipline"
        }),
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------
    # CATEGORY ANALYSIS (FIXED MELT)
    # -------------------------------
    df_long = df_lb.melt(
        id_vars=[COL_UID, COL_NAME, COL_DISC],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Score_TEMP"   # 🔥 FIXED
    )

    df_long["Category"] = df_long["Category"].astype(str).str.strip()
    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")

    df_long = df_long.dropna(subset=["Score_TEMP"])
    df_long = df_long[df_long["Score_TEMP"] > 0]

    if df_long.empty:
        st.warning("No category-wise data available")
    else:

        # -------------------------------
        # SPLIT CATEGORY
        # -------------------------------
        df_long["RBT"] = df_long["Category"].apply(
            lambda x: x.split("-")[0].strip() if "-" in x else "Other"
        )
        df_long["Type"] = df_long["Category"].apply(
            lambda x: x.split("-")[1].strip() if "-" in x else "Other"
        )

        RBT_ORDER = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        TYPE_ORDER = ["MCQ", "Conceptual", "Numerical", "Scenario"]

        st.markdown("### 🏅 Category Champions")

        medals = ["🥇", "🥈", "🥉"]

        for rbt in RBT_ORDER:

            rbt_df = df_long[df_long["RBT"].str.lower() == rbt.lower()]

            if rbt_df.empty:
                continue

            st.markdown(f"## 🎯 {rbt}")

            for t in TYPE_ORDER:

                sub_df = rbt_df[rbt_df["Type"].str.lower() == t.lower()]

                if sub_df.empty:
                    continue

                with st.expander(f"📘 {rbt}-{t}"):

                    top3 = sub_df.sort_values("Score_TEMP", ascending=False).head(3)
                    cols = st.columns(3)

                    for i, (_, row) in enumerate(top3.iterrows()):

                        color = "#FFD700" if i == 0 else "#1E2A44"

                        with cols[i]:
                            st.markdown(f"""
                            <div style="
                                background:{color};
                                color:{'black' if i==0 else 'white'};
                                padding:16px;
                                border-radius:12px;
                                text-align:center;
                            ">
                                <h3>{medals[i]}</h3>
                                <b>{row.get(COL_NAME,'N/A')}</b><br>
                                <small>{row[COL_UID]}</small><br><br>
                                🎓 {row.get(COL_DISC,'N/A')}<br>
                                📊 <b>{round(row['Score_TEMP'],2)}</b>
                            </div>
                            """, unsafe_allow_html=True)

    # -------------------------------
    # ⏰ EARLY
    # -------------------------------
    st.markdown("### ⏰ Early Birds")

    st.dataframe(
        df_lb.sort_values(COL_REG_TIME).head(5)[
            [COL_UID, COL_NAME, COL_DISC, COL_REG_TIME]
        ].rename(columns={
            COL_UID: "UID",
            COL_NAME: "Name",
            COL_DISC: "Discipline",
            COL_REG_TIME: "Registration Time"
        }),
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------
    # ⚡ FASTEST
    # -------------------------------
    st.markdown("### ⚡ Fastest Finishers")

    st.dataframe(
        df_lb.sort_values("delay_minutes").head(5)[
            [COL_UID, COL_NAME, COL_DISC, "delay_minutes"]
        ].rename(columns={
            COL_UID: "UID",
            COL_NAME: "Name",
            COL_DISC: "Discipline",
            "delay_minutes": "Delay (min)"
        }),
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# SWOT ANALYSIS 
# =========================================================
with tab4:

    st.subheader("📈 SWOT Analysis")

    # =====================================================
    # PREP DATA (WIDE → LONG)df_long.groupby("Category")["Score_TEMP"]
    # =====================================================
    cat_cols = df_valid.columns[5:30]

    df_swot = df_valid.copy()

    df_long = df_swot.melt(
        id_vars=[COL_UID],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Score_TEMP"
    )

    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")
    df_long = df_long.dropna(subset=["Score_TEMP"])
    df_long = df_long[df_long["Score_TEMP"] > 0]

    # -----------------------------
    # CLEANING
    # -----------------------------
    df_long["Category"] = df_long["Category"].astype(str).str.strip()
    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")

    df_long = df_long.dropna(subset=["Score_TEMP"])
    df_long = df_long[df_long["Score_TEMP"] > 0]

    # Remove any accidental "overall"
    df_long = df_long[
        ~df_long["Category"].str.lower().str.contains("overall", na=False)
    ]

    if df_long.empty:
        st.warning("No valid data available for SWOT analysis")
        st.stop()

    # =====================================================
    # SPLIT CATEGORY
    # =====================================================
    df_long["RBT"] = df_long["Category"].apply(
        lambda x: x.split("-")[0].strip() if "-" in x else "Other"
    )
    df_long["Type"] = df_long["Category"].apply(
        lambda x: x.split("-")[1].strip() if "-" in x else "Other"
    )

    # =====================================================
    # HEATMAP (SQUARE + ORDERED)
    # =====================================================
    import plotly.graph_objects as go

    RBT_ORDER = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    TYPE_ORDER = ["MCQ", "Conceptual", "Numerical", "Scenario"]

    pivot = (
        df_long
        .groupby(["RBT", "Type"])["Score_TEMP"]
        .mean()
        .reset_index()
    )

    heatmap = pivot.pivot(index="RBT", columns="Type", values="Score_TEMP")

    # Apply ordering safely
    heatmap = heatmap.reindex(index=RBT_ORDER)
    heatmap = heatmap.reindex(columns=TYPE_ORDER)

    # Reverse for bottom → top (Remember bottom)
    heatmap = heatmap.iloc[::-1]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap.values,
        x=heatmap.columns,
        y=heatmap.index,
        colorscale="RdYlGn",
        text=heatmap.round(1),
        texttemplate="%{text}",
        textfont={"size":12}
    ))

    fig.update_layout(
        height=500,
        width=500,
        margin=dict(l=20, r=20, t=40, b=20),
        title="RBT vs Question Type Performance"
    )

    st.plotly_chart(fig, use_container_width=False)

    # =====================================================
    # STRENGTHS & WEAKNESSES
    # =====================================================
    st.markdown("### 💪 Strengths & Weaknesses")

    avg_scores = (
        df_long
        .groupby("Category")["Score_TEMP"]
        .mean()
        .sort_values(ascending=False)
    )

    strengths = avg_scores.head(3)
    weaknesses = avg_scores.tail(3)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💪 Strength Areas")
        for k, v in strengths.items():
            st.markdown(f"- **{k}** → {v:.1f}")

    with col2:
        st.markdown("#### ⚠ Weak Areas")
        for k, v in weaknesses.items():
            st.markdown(f"- **{k}** → {v:.1f}")

    # =====================================================
    # 🎯 TRAINING NEED ANALYSIS (ACTIONABLE)
    # =====================================================
    st.markdown("### 🎯 Training Need Analysis")

    for cat, val in weaknesses.items():

        rbt = cat.split("-")[0] if "-" in cat else "General"
        qtype = cat.split("-")[1] if "-" in cat else "General"

        st.markdown(f"""
---
### 📌 {cat} _(Avg Score: {val:.1f})_

**🔍 Diagnosis**
- Weakness in **{rbt} cognitive level**
- Difficulty in **{qtype} question type**
- Likely gaps in concept clarity and application strategy

**🛠 Intervention Plan**
- **Concept Boost:** 5–7 min micro-lessons with examples  
- **Guided Practice:** Stepwise solved problems → gradual difficulty  
- **Targeted Drills:** 10–15 daily {qtype} questions  
- **Error Review:** Maintain mistake log + weekly correction  
- **Timed Tests:** 10–20 min quizzes to improve speed & accuracy  

**📈 Expected Outcome**
- Improved accuracy in {qtype}  
- Better {rbt} level thinking  
- Faster and more confident responses  

**⏱ Timeline**
- Week 1–2: Concept + guided practice  
- Week 3–4: Drills + timed tests  
- Week 5: Re-assessment  
""")

# =====================================================
# AI INSIGHTS CACHE (RUN LLM CALL ONCE)
# =====================================================
@st.cache_data(ttl=3600)  # cache for 1 hour
def get_ai_insights(prompt):

    if not client:
        return "⚠ API key not configured."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠ AI Error: {str(e)}"



# =========================================================
# AI INSIGHTS (FINAL – NO MELT CONFLICT EVER)
# =========================================================
with tab5:

    st.subheader("🤖 AI Insights (Institution-Level)")

    df_ai = df_valid.copy()

    # SAFE TOTAL SCORE COLUMN
    df_ai["Total_Score_AI"] = pd.to_numeric(df_ai[COL_TOTAL], errors="coerce")

    total_participants = df_ai[COL_UID].nunique()
    completion_rate = df_ai["completed"].mean() * 100
    avg_score = df_ai["Total_Score_AI"].mean()
    avg_delay = df_ai["delay_minutes"].mean()

    # =====================================================
    # SAFE MELT (UNIQUE COLUMN NAMES)
    # =====================================================
    cat_cols = df_ai.columns[5:30]

    df_long = df_ai.melt(
        id_vars=[COL_UID],
        value_vars=cat_cols,
        var_name="Category_AI_TEMP",
        value_name="Score_AI_TEMP"
    )

    df_long["Score_AI_TEMP"] = pd.to_numeric(df_long["Score_AI_TEMP"], errors="coerce")
    df_long = df_long.dropna(subset=["Score_AI_TEMP"])
    df_long = df_long[df_long["Score_AI_TEMP"] > 0]

    # =====================================================
    # COVERAGE + WEAK AREAS
    # =====================================================
    coverage = (
        len(df_long["Category_AI_TEMP"].unique()) / len(cat_cols) * 100
        if len(cat_cols) else 0
    )

    weak_areas = (
        df_long.groupby("Category_AI_TEMP")["Score_AI_TEMP"]
        .mean()
        .sort_values()
        .head(5)
        .to_dict()
    )

    # =====================================================
    # PROMPT
    # =====================================================
    prompt = f"""
You are an academic analytics expert.

Institutional Assessment Summary:

- Participants: {total_participants}
- Completion Rate: {completion_rate:.2f}%
- Average Score: {avg_score:.2f}
- Avg Delay: {avg_delay:.2f} mins
- Coverage: {coverage:.2f}%

Weak Areas:
{weak_areas}

Provide:
1. Key Challenges
2. Root Causes
3. Strategic Recommendations

Keep it crisp, executive-level.
"""

    # =====================================================
    # REGENERATE BUTTON
    # =====================================================
    if st.button("🔄 Regenerate Insights"):
        st.cache_data.clear()

    # =====================================================
    # CALL AI (SAFE)
    # =====================================================
    if client:
        insights = get_ai_insights(prompt)
        st.markdown(insights)
    else:
        st.warning("⚠ OpenAI API key not found. Showing fallback insights.")

    # =====================================================
    # FALLBACK METRICS
    # =====================================================
    with st.expander("📊 Data Snapshot"):
        st.markdown(f"""
- Participants: {total_participants}
- Completion Rate: {completion_rate:.2f}%
- Avg Score: {avg_score:.2f}
- Coverage: {coverage:.2f}%
""")

# =========================================================
# MICRO ANALYSIS (DISCIPLINE WISE)
# =========================================================

# -------------------------
# TAB STATE FIX
# -------------------------
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Micro"

with tab6:

    st.session_state.active_tab = "Micro"

    st.subheader("🔍 Micro Analysis (Discipline Level)")

    # =====================================================
    # DROPDOWN (STATEFUL)
    # =====================================================
    disciplines = sorted(df_fac[FAC_DISC].dropna().unique())

    selected_disc = st.selectbox(
        "Select Discipline",
        disciplines,
        key="discipline_selector"
    )

    # =====================================================
    # FILTER DATA
    # =====================================================
    fac_disc_df = df_fac[df_fac[FAC_DISC] == selected_disc]
    aat_disc_df = df_aat[df_aat[AAT_DISC] == selected_disc]

    # =====================================================
    # METRICS
    # =====================================================
    total = fac_disc_df[FAC_UID].nunique()

    completed = aat_disc_df[aat_disc_df["Status"] == "Completed"][AAT_UID].nunique()
    partial = aat_disc_df[aat_disc_df["Status"] == "Partial"][AAT_UID].nunique()

    participated = completed + partial
    rate = (participated / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Faculty", total)
    c2.metric("Participated", participated)
    c3.metric("Completed", completed)
    c4.metric("Participation (%)", round(rate, 2))

    st.markdown("---")

    # =====================================================
    # PREP LONG DATA (IMPORTANT FIX)
    # =====================================================
    cat_cols = df_aat.columns[5:30]

    df_long = aat_disc_df.melt(
        id_vars=[AAT_UID],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Score_TEMP"
    )

    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")
    df_long = df_long.dropna(subset=["Score_TEMP"])
    df_long = df_long[df_long["Score_TEMP"] > 0]

    if not df_long.empty:
        df_long["Category"] = df_long["Category"].astype(str).str.strip()
        df_long["RBT"] = df_long["Category"].apply(lambda x: x.split("-")[0])
        df_long["Type"] = df_long["Category"].apply(lambda x: x.split("-")[1] if "-" in x else "Other")

    # =====================================================
    # GRAPHS
    # =====================================================
    col1, col2 = st.columns(2)

    # -------------------------
    # PIE (GRADE)
    # -------------------------
    with col1:
        st.markdown(f"### 🏆 Grade Distribution ({selected_disc})")

        if COL_GRADE and not aat_disc_df.empty:

            g = (
                aat_disc_df[COL_GRADE]
                .dropna()
                .astype(str)
                .value_counts()
                .reset_index()
            )
            g.columns = ["Grade", "Count"]

            st.plotly_chart(
                px.pie(g, names="Grade", values="Count"),
                use_container_width=True
            )
        else:
            st.info("No grade data available")

    # -------------------------
    # HEATMAP (NO PARTICIPATION FIX)
    # -------------------------
    with col2:
        st.markdown(f"### 📊 Performance Heatmap ({selected_disc})")

        try:
            cat_cols = df_aat.columns[5:30]

            df_long = aat_disc_df.melt(
                id_vars=[AAT_UID],
                value_vars=cat_cols,
                var_name="Category",
                value_name="Score_TEMP"
            )

            df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")
            df_long = df_long.dropna(subset=["Score_TEMP"])
            df_long = df_long[df_long["Score_TEMP"] > 0]

            if df_long.empty:
                st.warning("No data available for heatmap")
            else:
                df_long["RBT"] = df_long["Category"].apply(
                    lambda x: x.split("-")[0].strip() if "-" in x else "Other"
                )
                df_long["Type"] = df_long["Category"].apply(
                    lambda x: x.split("-")[1].strip() if "-" in x else "Other"
                )

                pivot = (
                    df_long
                    .groupby(["RBT", "Type"])["Score_TEMP"]
                    .mean()
                    .reset_index()
                )

                heatmap = pivot.pivot(index="RBT", columns="Type", values="Score_TEMP")

                RBT_ORDER = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                TYPE_ORDER = ["MCQ", "Conceptual", "Numerical", "Scenario"]

                heatmap = heatmap.reindex(index=RBT_ORDER)
                heatmap = heatmap.reindex(columns=TYPE_ORDER)

                # IMPORTANT: keep NaN (no fillna)
                heatmap = heatmap.iloc[::-1]

                import plotly.graph_objects as go
                import numpy as np

                z = heatmap.values.astype(float)

                # Mask NaNs for separate coloring
                z_masked = np.where(np.isnan(z), None, z)

                fig = go.Figure(data=go.Heatmap(
                    z=z_masked,
                    x=heatmap.columns,
                    y=heatmap.index,
                    colorscale="RdYlGn",
                    colorbar=dict(title="Performance"),
                    text=np.where(np.isnan(z), "NP", np.round(z,1)),
                    texttemplate="%{text}",
                    hovertemplate="RBT: %{y}<br>Type: %{x}<br>Score: %{z}<extra></extra>"
                ))

                fig.update_layout(height=420)

                st.plotly_chart(fig, use_container_width=True)

                # LEGEND
                st.markdown("""
**Legend:**
- 🟢 High Score → Strong performance  
- 🔴 Low Score → Weak performance  
- ⚪ NP → No Participation (Training Required)
""")

        except Exception as e:
            st.error("Heatmap rendering failed")
            st.write(str(e))

    # =====================================================
    # INSIGHTS + TRAINING 
    # =====================================================
    st.markdown(f"### 💡 Insights for {selected_disc}")

    if not df_long.empty:

        avg_scores = (
            df_long.groupby("Category")["Score_TEMP"]
            .mean()
            .sort_values(ascending=False)
        )

        strengths = avg_scores.head(2)
        weaknesses = avg_scores.tail(2)

        # Detect NO PARTICIPATION categories
        all_categories = df_aat.columns[5:30]
        observed_categories = set(df_long["Category"])
        no_participation = [c for c in all_categories if c not in observed_categories]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💪 Strengths")
            for k,v in strengths.items():
                st.markdown(f"- **{k}** → {v:.1f}")

        with col2:
            st.markdown("#### ⚠ Weaknesses")
            for k,v in weaknesses.items():
                st.markdown(f"- **{k}** → {v:.1f}")

        # =====================================================
        # 🎯 TRAINING RECOMMENDATIONS (SMART)
        # =====================================================
        st.markdown("### 🎯 Training Recommendations")

        # Weak performance
        for cat, val in weaknesses.items():

            rbt = cat.split("-")[0]
            qtype = cat.split("-")[1] if "-" in cat else ""

            st.markdown(f"""
- Improve **{rbt} ({qtype})**
  - Focus on conceptual clarity
  - Introduce guided + timed practice
  - Conduct targeted workshops
""")

        # No participation
        if no_participation:
            st.markdown("#### ⚪ No Participation Areas (Critical)")

            for cat in no_participation[:5]:  # limit for readability
                rbt = cat.split("-")[0]
                qtype = cat.split("-")[1] if "-" in cat else ""

                st.markdown(f"""
- **{cat}**
  - No faculty attempted this category
  - Introduce mandatory exposure sessions
  - Conduct foundational training in **{rbt} ({qtype})**
""")

    # =====================================================
    # NON-PARTICIPANTS
    # =====================================================
    st.markdown(f"### 🚫 Non-Participating Faculty ({selected_disc})")

    non_participants = fac_disc_df[
        ~fac_disc_df[FAC_UID].isin(
            aat_disc_df[aat_disc_df["Status"] != "Not Participated"][AAT_UID]
        )
    ]

    cols = [FAC_UID]
    if "Name" in fac_disc_df.columns:
        cols.append("Name")

    non_participants = non_participants[cols]

    st.dataframe(non_participants, use_container_width=True, hide_index=True)

    # DOWNLOAD
    csv = non_participants.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download List",
        csv,
        f"{selected_disc}_non_participants.csv",
        "text/csv"
    )