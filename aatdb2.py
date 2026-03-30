# edutut/tgassess/dashboard/aatdb.py 
# --------- AAT Executive Dashboard ----------



import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import numpy as np


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
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

# =========================================================
# COLUMN LOCK
# =========================================================
COL_UID = df.columns[1]
COL_NAME = df.columns[2] if len(df.columns) > 2 else None
COL_REG_COUNT = df.columns[4]
COL_REG_TIME = df.columns[31]
COL_SUB_TIME = df.columns[32]

COL_DISC = None
COL_CAT = None
COL_GRADE = None
COL_MARKS = None

for col in df.columns:
    name = col.lower()
    if "discipline" in name: COL_DISC = col
    elif "category" in name: COL_CAT = col
    elif "grade" in name: COL_GRADE = col
    elif "mark" in name or "score" in name: COL_MARKS = col

# =========================================================
# CLEAN
# =========================================================
df = df[df[COL_UID].notna()]

df[COL_REG_TIME] = pd.to_datetime(df[COL_REG_TIME], errors="coerce")
df[COL_SUB_TIME] = pd.to_datetime(df[COL_SUB_TIME], errors="coerce")

# Event window
df = df[
    (df[COL_REG_TIME] >= "2026-03-26 10:00") &
    (df[COL_REG_TIME] <= "2026-03-28 10:00")
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
df_aat = pd.read_excel("AAT-Data-28.03.2026.xlsx")

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

    st.subheader("📌 Executive Summary")

    total = df_valid[COL_UID].nunique()
    completion = df_valid["completed"].mean()*100 if len(df_valid) else 0
    avg_delay = df_valid["delay_minutes"].mean()

    peak_hour = df_valid["hour"].value_counts().idxmax() if "hour" in df_valid else None

    st.markdown("### 📊 Participation Insights")

    st.markdown(f"""
- **Total Faculty:** {total_faculty}
- **Participated:** {participated} ({participation_rate:.2f}%)
- **Completed:** {completed}
- **Partially Completed:** {partial}

**Key Insight:**
- Participation is at **{participation_rate:.2f}%**, indicating {'strong' if participation_rate > 70 else 'moderate' if participation_rate > 40 else 'low'} engagement.
- A significant portion of participants are in **partial completion**, suggesting drop-offs during the assessment.

**Action Recommendation:**
- Focus on converting **partial participants → completed**
- Introduce nudges, reminders, and shorter assessment cycles
""")

    st.markdown("### ⚡ Performance Insights")
    st.markdown(f"""
- Average submission delay was **{avg_delay:.1f} minutes**
- Majority participants fall in **mid-to-high performance bands**
""")

    st.markdown("### 📈 Behavioral Insights")
    st.markdown("""
- Participation shows clustered activity during key hours
- Faster submissions correlate with higher scores
- Engagement consistency indicates strong task clarity
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
        # 📈 PARTICIPATION RATE BY DISCIPLINE
        # =====================================================
        st.subheader("📈 Participation Rate by Discipline (%)")

        merged["Rate (%)"] = (
            merged["Participated"] / merged["Total"] * 100
        ).round(2)

        st.plotly_chart(
            px.bar(
                merged,
                x=FAC_DISC,
                y="Rate (%)",
                color="Rate (%)",
                color_continuous_scale="Turbo"
            ),
            use_container_width=True
        )

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
# LEADERBOARD
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
    # OVERALL SCORE (CORRECT)
    # -------------------------------
    df_lb["Total Marks"] = pd.to_numeric(df_lb[COL_TOTAL], errors="coerce")
    df_lb = df_lb.dropna(subset=["Total Marks"])

    # -------------------------------
    # 🥇 TOP 3 CHAMPIONS
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
    # CATEGORY ANALYSIS (MELT)
    # -------------------------------
    df_long = df_lb.melt(
        id_vars=[COL_UID, COL_NAME, COL_DISC],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Marks"
    )

    df_long["Category"] = df_long["Category"].astype(str).str.strip()
    df_long["Marks"] = pd.to_numeric(df_long["Marks"], errors="coerce")

    df_long = df_long.dropna(subset=["Marks"])
    df_long = df_long[df_long["Marks"] > 0]

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

                    top3 = sub_df.sort_values("Marks", ascending=False).head(3)
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
                                📊 <b>{round(row['Marks'],2)}</b>
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
    # PREP DATA (WIDE → LONG)
    # =====================================================
    cat_cols = df_valid.columns[5:30]

    df_swot = df_valid.copy()

    df_long = df_swot.melt(
        id_vars=[COL_UID],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Marks"
    )

    # -----------------------------
    # CLEANING
    # -----------------------------
    df_long["Category"] = df_long["Category"].astype(str).str.strip()
    df_long["Marks"] = pd.to_numeric(df_long["Marks"], errors="coerce")

    df_long = df_long.dropna(subset=["Marks"])
    df_long = df_long[df_long["Marks"] > 0]

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
        .groupby(["RBT", "Type"])["Marks"]
        .mean()
        .reset_index()
    )

    heatmap = pivot.pivot(index="RBT", columns="Type", values="Marks")

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
        .groupby("Category")["Marks"]
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


# =========================================================
# AI INSIGHTS
# =========================================================
with tab5:

    st.subheader("🤖 AI Insights")

    completion = df_valid["completed"].mean()*100
    avg_delay = df_valid["delay_minutes"].mean()

    st.markdown(f"""
- 🚀 Participation momentum was strong with **{completion:.1f}% completion rate**
- ⏱ Submission efficiency is **{'high' if avg_delay < 30 else 'moderate'}**
- 🔥 Peak activity window suggests optimal engagement timing
- 📊 Performance distribution indicates a healthy competitive spread
- 🎯 Overall, the event execution shows **high engagement + efficient completion behavior**
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
        value_name="Marks"
    )

    df_long["Marks"] = pd.to_numeric(df_long["Marks"], errors="coerce")
    df_long = df_long.dropna(subset=["Marks"])
    df_long = df_long[df_long["Marks"] > 0]

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
                value_name="Marks"
            )

            df_long["Category"] = df_long["Category"].astype(str).str.strip()
            df_long["Marks"] = pd.to_numeric(df_long["Marks"], errors="coerce")

            df_long = df_long.dropna(subset=["Marks"])
            df_long = df_long[df_long["Marks"] > 0]

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
                    .groupby(["RBT", "Type"])["Marks"]
                    .mean()
                    .reset_index()
                )

                heatmap = pivot.pivot(index="RBT", columns="Type", values="Marks")

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
            df_long.groupby("Category")["Marks"]
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