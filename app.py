import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Supabase client setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

st.title("Pulse Dashboard – Recent Listings")

# Calculate the date 7 days ago
seven_days_ago = datetime.utcnow() - timedelta(days=7)

# Fetch listings from last 7 days
try:
    response = (
        supabase
        .table("listings")
        .select("*")
        .gte("date_added", seven_days_ago.isoformat())
        .execute()
    )
    data = response.data
except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(data)

if df.empty:
    st.info("No listings found in the last 7 days.")
    st.stop()

# Clean up data for filters
df = df.dropna(subset=["city", "price", "beds"], how="all")

# Sidebar filters
st.sidebar.header("Filters")

# City filter
if "city" in df.columns and not df["city"].dropna().empty:
    cities = sorted(df["city"].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("City", options=cities, default=cities)
else:
    st.info("No city data available.")
    st.stop()

# Price Range filter
if "price" in df.columns and not df["price"].dropna().empty:
    min_price = int(df["price"].min())
    max_price = int(df["price"].max())
    price_range = st.sidebar.slider(
        "Price Range",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=1000,
    )
else:
    st.info("No price data available.")
    st.stop()

# Square footage filter
if "sqft" in df.columns and df["sqft"].notnull().any():
    min_sqft, max_sqft = int(df["sqft"].min()), int(df["sqft"].max())
    if min_sqft == max_sqft:
        sqft_range = (min_sqft, max_sqft)
        st.sidebar.write(f"Only one square footage value: {min_sqft}")
    else:
        sqft_range = st.sidebar.slider(
            "Square Footage",
            min_value=min_sqft,
            max_value=max_sqft,
            value=(min_sqft, max_sqft),
            step=100,
        )
else:
    sqft_range = None

# Beds filter
if "beds" in df.columns and not df["beds"].dropna().empty:
    min_beds = int(df["beds"].min())
    max_beds = int(df["beds"].max())
    beds_range = st.sidebar.slider(
        "Bedrooms",
        min_value=min_beds,
        max_value=max_beds,
        value=(min_beds, max_beds),
        step=1,
    )
else:
    st.info("No bedroom data available.")
    st.stop()

# Apply filters
filtered = df[
    (df["city"].isin(selected_cities)) &
    (df["price"].between(price_range[0], price_range[1])) &
    (df["beds"].between(beds_range[0], beds_range[1]))
]

if sqft_range:
    filtered = filtered[filtered["sqft"].between(sqft_range[0], sqft_range[1])]

# Show results
st.write(f"Showing {len(filtered)} of {len(df)} listings from the last 7 days.")
st.dataframe(filtered.reset_index(drop=True))

