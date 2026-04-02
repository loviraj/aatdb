# =========================================================
# AAT 2.0 EXECUTIVE DASHBOARD (FINAL ENTERPRISE VERSION)
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import numpy as np
import os, re
from dotenv import load_dotenv
from openai import OpenAI

# PDF
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="AAT 2.0 Dashboard", layout="wide")
os.makedirs("assets", exist_ok=True)

COLORS = ["#FFD700","#00C2FF","#FF7F50","#7CFC00","#FF69B4","#8A2BE2"]

# =========================================================
# SAVE GRAPH
# =========================================================
def save_fig(fig, title):
    filename = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')
    fig.write_image(f"assets/{filename}.png")

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_all():
    df_aat = pd.read_excel("AAT-Data-28.03.2026.xlsx")
    df_fac = pd.read_excel("FacultyDetails.xlsx")

    df_aat.columns = [str(c).strip() for c in df_aat.columns]
    df_fac.columns = [str(c).strip() for c in df_fac.columns]

    return df_aat, df_fac

df_aat, df_fac = load_all()

# =========================================================
# COLUMN DETECTION
# =========================================================
FAC_UID = df_fac.columns[2]
FAC_DISC = next((c for c in df_fac.columns if "discipline" in c.lower()), None)

AAT_UID = df_aat.columns[1]
AAT_DISC = next((c for c in df_aat.columns if "discipline" in c.lower()), None)
AAT_REG = df_aat.columns[4]

COL_TOTAL = df_aat.columns[29]
COL_NAME = df_aat.columns[2]
COL_GRADE = next((c for c in df_aat.columns if "grade" in c.lower()), None)

# =========================================================
# CLEAN
# =========================================================
df_aat["Marks"] = pd.to_numeric(df_aat[COL_TOTAL], errors="coerce")

df_aat[AAT_UID] = pd.to_numeric(df_aat[AAT_UID], errors="coerce")
df_fac[FAC_UID] = pd.to_numeric(df_fac[FAC_UID], errors="coerce")

df_aat = df_aat.dropna(subset=[AAT_UID])
df_fac = df_fac.dropna(subset=[FAC_UID])

df_aat[AAT_UID] = df_aat[AAT_UID].astype(int)
df_fac[FAC_UID] = df_fac[FAC_UID].astype(int)

# STATUS
df_aat[AAT_REG] = pd.to_numeric(df_aat[AAT_REG], errors="coerce").fillna(0)

df_aat["Status"] = df_aat[AAT_REG].apply(
    lambda x: "Completed" if x == 3 else
              "Partial" if x in [1,2] else
              "Not Participated"
)

# METRICS
total_faculty = df_fac[FAC_UID].nunique()
completed = df_aat[df_aat["Status"]=="Completed"][AAT_UID].nunique()
partial = df_aat[df_aat["Status"]=="Partial"][AAT_UID].nunique()
participated = completed + partial
participation_rate = (participated/total_faculty*100) if total_faculty else 0

# =========================================================
# HEADER
# =========================================================
colA, colB = st.columns([8,1])
with colA:
    st.title("📊 Assess-A-Thon Executive Dashboard v2.0")
with colB:
    try:
        st.image(Image.open("assets/AAT-Mascot.png"), width=100)
    except:
        pass

# =========================================================
# TABS
# =========================================================
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Executive Summary",
    "📊 Participation",
    "⚡ Performance",
    "🏆 Leaderboard",
    "📈 SWOT"
])

# =========================================================
# EXECUTIVE SUMMARY
# =========================================================
with tab0:

    st.subheader("Institutional Pulse")

    c1, c2, c3 = st.columns(3)
    c1.metric("Faculty", total_faculty)
    c2.metric("Participation %", f"{participation_rate:.2f}")
    c3.metric("Completed", completed)

# =========================================================
# PARTICIPATION
# =========================================================
with tab1:

    st.subheader("Participation Status")

    status_df = pd.DataFrame({
        "Status":["Completed","Partial","Not Participated"],
        "Count":[completed,partial,total_faculty-participated]
    })

    fig = px.pie(status_df, names="Status", values="Count")
    st.plotly_chart(fig, use_container_width=True)
    save_fig(fig,"Participation Status")

    # Discipline
    total_disc = df_fac.groupby(FAC_DISC)[FAC_UID].nunique().reset_index(name="Total")
    part_disc = df_aat[df_aat["Status"]!="Not Participated"] \
        .groupby(AAT_DISC)[AAT_UID].nunique().reset_index(name="Participated")

    merged = pd.merge(total_disc, part_disc,
                      left_on=FAC_DISC, right_on=AAT_DISC, how="left").fillna(0)

    fig = px.bar(merged, x=FAC_DISC, y=["Total","Participated"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)
    save_fig(fig,"Discipline Participation")

# =========================================================
# PERFORMANCE
# =========================================================
with tab2:

    df_perf = df_aat.dropna(subset=["Marks"])

    fig = px.histogram(df_perf, x="Marks", nbins=30)
    st.plotly_chart(fig)
    save_fig(fig,"Marks Distribution")

# =========================================================
# LEADERBOARD
# =========================================================
with tab3:

    df_lb = df_aat.dropna(subset=["Marks"])
    top5 = df_lb.sort_values("Marks",ascending=False).head(5)

    st.dataframe(top5[[AAT_UID,COL_NAME,AAT_DISC,"Marks"]],
                 use_container_width=True, hide_index=True)

# =========================================================
# SWOT
# =========================================================
with tab4:

    cat_cols = df_aat.columns[5:30]

    df_long = df_aat.melt(
        id_vars=[AAT_UID],
        value_vars=cat_cols,
        var_name="Category",
        value_name="Score_TEMP"
    )

    df_long["Score_TEMP"] = pd.to_numeric(df_long["Score_TEMP"], errors="coerce")
    df_long = df_long.dropna(subset=["Score_TEMP"])

    heat = df_long.groupby("Category")["Score_TEMP"].mean().reset_index()

    fig = px.imshow([heat["Score_TEMP"].values])
    st.plotly_chart(fig)
    save_fig(fig,"SWOT Heatmap")

# =========================================================
# PDF
# =========================================================
def generate_pdf():

    doc = SimpleDocTemplate("Chancellor_Report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Assess-A-Thon Executive Report", styles["Title"]))
    content.append(PageBreak())

    content.append(RLImage("assets/participation_status.png", width=6*inch, height=3*inch))
    content.append(PageBreak())

    content.append(RLImage("assets/marks_distribution.png", width=6*inch, height=3*inch))

    doc.build(content)

with tab0:
    if st.button("Download Report"):
        generate_pdf()
        with open("Chancellor_Report.pdf","rb") as f:
            st.download_button("Download",f,"Report.pdf")