import sqlite3, pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = "social_media.db"
CSV_SOCIAL = Path("social_media_dashboard.csv")
CSV_USERS = Path("users.csv")

def init_db():
    con = sqlite3.connect(DB_PATH)
    df_social = pd.read_csv(CSV_SOCIAL)
    df_social.to_sql("kpis", con, if_exists="replace", index=False)
    df_users = pd.read_csv(CSV_USERS)
    df_users.to_sql("users", con, if_exists="replace", index=False)
    con.commit()
    con.close()

def sync_to_csv():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM kpis", con)
    df.to_csv(CSV_SOCIAL, index=False)
    con.close()

def sync_users():
    con = sqlite3.connect(DB_PATH)
    df_users = pd.read_csv(CSV_USERS)
    df_users.to_sql("users", con, if_exists="replace", index=False)
    con.commit()
    con.close()

def authenticate(username, password):
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password),
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

if not Path(DB_PATH).exists():
    init_db()
sync_users()

st.title("Social Media Dashboard")
if "auth" not in st.session_state:
    st.session_state.auth = None

if not st.session_state.auth:
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        role = authenticate(user, pwd)
        if role:
            st.session_state.auth = {"user": user, "role": role}
        else:
            st.error("Invalid")
    st.stop()

role = st.session_state.auth["role"]
con = sqlite3.connect(DB_PATH)

df = pd.read_sql("SELECT * FROM kpis", con)
platform = st.selectbox("Platform", df["platform"].unique())
df_platform = df[df["platform"] == platform]

st.subheader("Followers per Week")
week_data = pd.DataFrame({
    "Week": range(1, len(df_platform)+1),
    "Followers": df_platform["total_follower"]
})
st.line_chart(week_data.set_index("Week"))

st.subheader("Top Posts & Likes")
st.bar_chart(df_platform.set_index("platform")["total_follower"])

st.subheader("Audience Age Demographics")
age_dist = {
    "13-17": 15,
    "18-24": 45,
    "25-34": 25,
    "35-44": 10,
    "45+": 5
}
st.bar_chart(pd.Series(age_dist))

if role == "admin":
    st.subheader("Edit KPI")
    col1, col2 = st.columns(2)
    with col1:
        new_follower = st.number_input("Total Follower", value=int(df_platform["total_follower"].iloc[0]))
        new_eng = st.text_input("Engagement Rate", value=df_platform["engagement_rate"].iloc[0])
        new_view = st.number_input("Total View", value=int(df_platform["total_view"].iloc[0]))
    with col2:
        new_feature = st.text_input("Interactive Feature", value=df_platform["interactive_feature"].iloc[0])
    if st.button("Save Changes"):
        con.execute(
            "UPDATE kpis SET total_follower=?, engagement_rate=?, total_view=?, interactive_feature=? WHERE platform=?",
            (new_follower, new_eng, new_view, new_feature, platform)
        )
        con.commit()
        sync_to_csv()
        st.success("Saved & CSV updated")
con.close()