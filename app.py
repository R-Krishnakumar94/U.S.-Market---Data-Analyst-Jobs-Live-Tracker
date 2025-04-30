import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import re
import time
import matplotlib.pyplot as plt

# --------- Scraping Function ---------
@st.cache_data
def scrape_jobs():
    api_key = "b9fd6f440c0f1ea6c9b6a83156b8c0c935d77d71a1468440e753f4e3d2d65214"

    job_titles = [
        "Data Analyst", "Junior Data Analyst", "Senior Data Analyst",
        "Entry Level Data Analyst", "Business Analyst", "Data Scientist",
        "Remote Data Analyst", "Data Visualization Specialist",
        "Quantitative Analyst", "Operations Analyst"
    ]

    skills_list = [
        "Python", "SQL", "Excel", "Tableau", "Power BI", "R", "SAS",
        "Statistics", "Machine Learning", "Data Visualization",
        "AWS", "Azure", "Google Cloud", "BigQuery", "ETL", "Data Mining",
        "Business Intelligence", "Data Modeling"
    ]

    us_states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida",
        "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
        "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
        "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
        "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
        "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
        "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
        "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
        "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
        "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
    }

    all_jobs = []

    for title in job_titles:
        params = {
            "engine": "google_jobs",
            "q": title,
            "location": "United States",
            "api_key": api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        jobs_results = results.get("jobs_results", [])

        for job in jobs_results:
            job_title = job.get("title", "")
            company = job.get("company_name", "")
            location = job.get("location", "")
            salary = job.get("salary", "")
            description = job.get("description", "")

            if not salary:
                match = re.search(r'(\$\s?\d{2,3}[,]?\d{0,3})|(\d{2,3}[kK])|(\€\s?\d{2,3}[,]?\d{0,3})', description)
                if match:
                    salary = match.group()

            # Region detection
            detected_region = "Unknown"
            if location:
                if "Anywhere" in location:
                    detected_region = "Remote"
                elif "," in location:
                    part = location.split(",")[-1].strip()
                    detected_region = us_states.get(part, part)
                else:
                    detected_region = location

            # Skills detection
            found_skills = [skill for skill in skills_list if re.search(rf"\b{re.escape(skill)}\b", description, re.IGNORECASE)]
            skills_str = ", ".join(found_skills)

            all_jobs.append({
                "Job Title": job_title,
                "Company": company,
                "Location": location,
                "Region": detected_region,
                "Salary": salary,
                "Skills Found": skills_str
            })

        time.sleep(1.5)

    return pd.DataFrame(all_jobs)

# --------- Streamlit Frontend ---------

st.set_page_config(
    page_title="U.S. Data Analyst Jobs Tracker",
    page_icon=":bar_chart:",
    layout="wide"
)

st.title("U.S. Market - Data Analyst Jobs Live Tracker 🗽")

st.info("🔎 Scraping live job data from Google Jobs... Please wait ⏳")

df = scrape_jobs()

# ---------- Validations ----------
if df.empty:
    st.error("❌ No job data found. Please try again later or check API limits.")
    st.stop()

st.write("🔧 DEBUG - Columns in dataframe:", df.columns.tolist())

# Region filter with column check
if "Region" in df.columns:
    region_options = df["Region"].dropna().unique().tolist()
    selected_regions = st.multiselect("Select Region(s):", region_options, default=region_options)
    df = df[df["Region"].isin(selected_regions)]
else:
    st.warning("⚠️ 'Region' column missing. Showing all data.")
    selected_regions = []

# --------- Display Table ---------
st.header("📋 Job Listings Table")
st.dataframe(df)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Job Data as CSV", csv, "job_listings.csv", "text/csv")

# --------- Charts ---------

# Skills Chart
if "Skills Found" in df.columns and df["Skills Found"].notna().any():
    st.header("📈 Top Skills Found (%)")
    skills = df["Skills Found"].str.split(", ").explode().value_counts()

    if not skills.empty:
        skill_pct = (skills / skills.sum()) * 100
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        skill_pct.sort_values().plot(kind="barh", ax=ax1)
        for bar in ax1.patches:
            ax1.text(bar.get_width() + 0.5, bar.get_y() + 0.2, f"{bar.get_width():.1f}%", fontsize=8)
        ax1.set_xlabel("Percentage (%)")
        ax1.set_title("Top Skills (in %)")
        st.pyplot(fig1)
    else:
        st.warning("⚠️ No skill data available to display.")
else:
    st.warning("⚠️ No 'Skills Found' column or values to display.")

# Region Chart
if "Region" in df.columns:
    st.header("🌍 Jobs by Region")
    region_count = df["Region"].value_counts()

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    region_count.sort_values().plot(kind="barh", ax=ax2)
    for bar in ax2.patches:
        ax2.text(bar.get_width() + 0.5, bar.get_y() + 0.2, str(int(bar.get_width())), fontsize=8)
    ax2.set_xlabel("Number of Jobs")
    ax2.set_title("Jobs by Region")
    st.pyplot(fig2)
else:
    st.warning("⚠️ No 'Region' data to plot.")
