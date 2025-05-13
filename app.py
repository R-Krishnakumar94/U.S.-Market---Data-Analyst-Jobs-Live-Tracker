import streamlit as st
import pandas as pd
from serpapi import GoogleSearch
import re
import time
import matplotlib.pyplot as plt

# --------- Scraping Function ---------
@st.cache_data
def scrape_jobs():
    api_key = "e16223a41fccca3cbd2d2fb51fe3765e7d9b488ea50ee88222934097eaf7efe8"

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

    for search_title in job_titles:
        params = {
            "engine": "google_jobs",
            "q": search_title,
            "api_key": api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        jobs_results = results.get("jobs_results", [])

        for job in jobs_results:
            title = job.get("title", "")
            company = job.get("company_name", "")
            location = job.get("location", "")
            salary = job.get("salary", "")
            description = job.get("description", "")

            if not salary:
                salary_match = re.search(r'(\$\s?\d{2,3}[,]?\d{0,3})|(\d{2,3}[kK])|(\€\s?\d{2,3}[,]?\d{0,3})', description)
                if salary_match:
                    salary = salary_match.group()

            detected_region = ""
            if location:
                if "Anywhere" in location:
                    detected_region = "Remote"
                elif "," in location:
                    potential_region = location.split(",")[-1].strip()
                    detected_region = us_states.get(potential_region, potential_region)
                else:
                    detected_region = location
            else:
                detected_region = "Unknown"

            found_skills = []
            for skill in skills_list:
                if re.search(rf"\b{re.escape(skill)}\b", description, re.IGNORECASE):
                    found_skills.append(skill)

            skills_str = ", ".join(found_skills)

            all_jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": location,
                "Region": detected_region,
                "Salary": salary,
                "Skills Found": skills_str
            })

        time.sleep(2)

    return pd.DataFrame(all_jobs)

# --------- Streamlit Frontend ---------

st.set_page_config(
    page_title="U.S. Data Analyst Jobs Tracker",
    page_icon=":bar_chart:",
    layout="wide"
)

st.title("U.S. Market - Data Analyst Jobs Live Tracker 🗽")
st.info("🔎 Scraping live job data from Google Jobs... Please wait ⏳")

# Scrape data
df = scrape_jobs()

# 🛡️ Safety Checks
if df.empty:
    st.error("❌ No job data found. The scraping returned no results. Please try again later or check your API key usage.")
    st.stop()

required_columns = {"Region", "Skills Found"}
if not required_columns.issubset(df.columns):
    st.error(f"❌ Missing expected columns in scraped data: {required_columns - set(df.columns)}")
    st.stop()

# ========== Filter Sidebar ==========
st.sidebar.header("🔎 Filter Jobs")

region_options = df["Region"].dropna().unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Select Region(s)",
    sorted(region_options),
    default=region_options
)

skills_options = df["Skills Found"].str.split(", ").explode().dropna().unique().tolist()
selected_skills = st.sidebar.multiselect(
    "Select Skill(s)",
    sorted(skills_options),
    default=skills_options
)

# ========== Apply Filters ==========
filtered_df = df.copy()

if selected_regions:
    filtered_df = filtered_df[filtered_df["Region"].isin(selected_regions)]

if selected_skills:
    filtered_df = filtered_df[filtered_df["Skills Found"].str.contains('|'.join(selected_skills), case=False, na=False)]

st.success(f"✅ Showing {len(filtered_df)} job postings after filtering!")

# --------- Display Data Table ---------
st.header("📋 Job Listings Table")
st.dataframe(filtered_df)

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Job Data as CSV",
    data=csv,
    file_name='job_listings.csv',
    mime='text/csv',
)

# --------- Charts ---------

st.header("📈 Top Skills Found (%)")

skills_counter = filtered_df["Skills Found"].str.split(", ").explode().value_counts()
skills_counter_percent = (skills_counter / skills_counter.sum()) * 100

fig1, ax1 = plt.subplots(figsize=(10, 8))
skills_counter_percent_sorted = skills_counter_percent.sort_values(ascending=False)
skills_counter_percent_sorted.plot(kind="barh", ax=ax1)
ax1.invert_yaxis()

for i in ax1.patches:
    ax1.text(i.get_width() + 0.5, i.get_y() + 0.3,
             f"{i.get_width():.1f}%", fontsize=9, color='black')

ax1.set_xlabel("Percentage (%)")
ax1.set_ylabel("Skills")
ax1.set_title("Top Skills (in %)")
st.pyplot(fig1)

# 2. Jobs by Region
st.header("🌍 Jobs by Region")

region_counter = filtered_df["Region"].value_counts()

fig2, ax2 = plt.subplots(figsize=(10, 8))
region_counter_sorted = region_counter.sort_values(ascending=False)
region_counter_sorted.plot(kind="barh", ax=ax2)
ax2.invert_yaxis()

for i in ax2.patches:
    ax2.text(i.get_width() + 0.5, i.get_y() + 0.3,
             str(int(i.get_width())), fontsize=9, color='black')

ax2.set_xlabel("Number of Jobs")
ax2.set_ylabel("Region")
ax2.set_title("Jobs by Region")
st.pyplot(fig2)
