import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Intelligence", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("data/superstore.csv", encoding="latin-1")
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df


df = load_data()


st.title("Sales Intelligence Dashboard")


col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${df['Sales'].sum():,.0f}")
col1.metric("Total Orders", f"${df['Order ID'].nunique():,}")
col1.metric("Avg Order Value", f"${df['Sales'].mean():,.1f}")


fig = px.line(
    df.groupby("Order Date")["Sales"].sum().reset_index(),
    x = "Order Date", y="Sales", title="Revenue over time"
)
st.plotly_chart(fig, use_container_width=True)


fig2 = px.bar(
    df.groupby("Category")["Sales"].sum().reset_index().sort_values("Sales"),
    x="Sales", y="Category", orientation="h", title="Revenue by category"
)

st.plotly_chart(fig2, use_container_width=True)