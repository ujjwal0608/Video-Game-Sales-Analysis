"""
Video Game Sales & Ratings Dashboard
-------------------------------------
Reproduces the cleaning + EDA from Video_Game_Sales_Analysis.ipynb as an
interactive Streamlit app. Reads directly from the two source CSVs
(no database dependency), so it can run locally or be deployed as-is.

Expected files (place inside a `data/` folder next to this script):
    data/games.csv    -> the review-site dataset (Title, Rating, Genres, Plays, ...)
    data/vgsales.csv  -> the classic sales dataset (Name, Platform, Year, Global_Sales, ...)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Video Game Sales & Ratings Dashboard",
    page_icon="🎮",
    layout="wide",
)

DATA_DIR = "data"
REGIONS = ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]

# --------------------------------------------------------------------------
# Data loading + cleaning (mirrors the notebook, cached so it only runs once)
# --------------------------------------------------------------------------


def convert_k(value):
    """Turn strings like '3.2K' / '1.1M' into numbers."""
    if isinstance(value, str):
        value = value.strip().upper()
        if value.endswith("K"):
            return float(value.replace("K", "")) * 1_000
        if value.endswith("M"):
            return float(value.replace("M", "")) * 1_000_000
    return value


def clean_title(title):
    if pd.isnull(title):
        return ""
    return str(title).lower().replace(":", "")


@st.cache_data(show_spinner="Loading and cleaning data...")
def load_data():
    games_df = pd.read_csv("/Users/ujjwalraj/Desktop/Project Import Material 1/games.csv")
    sales_df = pd.read_csv("/Users/ujjwalraj/Desktop/Project Import Material 1/vgsales.csv")

    # ---- clean games_df ----
    games_df["Release Date"] = pd.to_datetime(
        games_df["Release Date"], format="%b %d, %Y", errors="coerce"
    )
    for col in ["Times Listed", "Number of Reviews", "Plays", "Playing", "Backlogs", "Wishlist"]:
        games_df[col] = games_df[col].apply(convert_k).astype(float)

    games_df["Rating"] = games_df["Rating"].fillna(games_df["Rating"].median())
    games_df["Release Date"] = games_df["Release Date"].fillna(pd.Timestamp("2000-01-01"))
    games_df["Team"] = games_df["Team"].fillna(" ")
    games_df["Summary"] = games_df["Summary"].fillna(" ")

    games_df["Genres"] = (
        games_df["Genres"]
        .astype(str)
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.replace("'", "", regex=False)
        .str.strip()
    )

    games_df["Backlog_gap"] = games_df["Backlogs"] - games_df["Wishlist"]

    # ---- clean sales_df ----
    sales_df["Year"] = pd.to_datetime(sales_df["Year"], format="%Y", errors="coerce")
    sales_df["Year"] = sales_df["Year"].fillna(pd.Timestamp("2000"))
    sales_df["Publisher"] = sales_df["Publisher"].fillna(" ")

    # ---- merge ----
    games_df["Clean_Title"] = games_df["Title"].apply(clean_title)
    sales_df["Clean_Name"] = sales_df["Name"].apply(clean_title)
    merged_df = pd.merge(
        games_df, sales_df, how="left", left_on="Clean_Title", right_on="Clean_Name"
    )
    merged_df.drop(columns=["Clean_Title", "Clean_Name"], inplace=True)

    return games_df, sales_df, merged_df


@st.cache_data(show_spinner=False)
def explode_genres(df, genre_col="Genres"):
    exploded = df.copy()
    exploded[genre_col] = exploded[genre_col].astype(str).str.split(", ")
    exploded = exploded.explode(genre_col)
    exploded[genre_col] = exploded[genre_col].str.strip()
    return exploded


try:
    games_df, sales_df, merged_df = load_data()
except FileNotFoundError:
    st.error(
        "Couldn't find `data/games.csv` and/or `data/vgsales.csv`. "
        "Create a `data/` folder next to `app.py` and place both CSVs inside it."
    )
    st.stop()

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
st.sidebar.title("🎮 Dashboard Filters")

section = st.sidebar.radio(
    "Section",
    ["Overview", "Game Ratings & Engagement (games.csv)", "Global Sales (vgsales.csv)", "Merged Insights"],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Games dataset: {len(games_df):,} titles\n\n"
    f"Sales dataset: {len(sales_df):,} platform-level records"
)

# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------
if section == "Overview":
    st.title("🎮 Video Game Sales & Ratings Dashboard")
    st.markdown(
        "Exploring two datasets: user ratings/engagement (**games.csv**) and "
        "historical **global sales** (**vgsales.csv**), plus a merged view."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Titles (games.csv)", f"{len(games_df):,}")
    c2.metric("Sales records (vgsales.csv)", f"{len(sales_df):,}")
    c3.metric("Avg. rating", f"{games_df['Rating'].mean():.2f} / 5")
    c4.metric("Total global sales", f"{sales_df['Global_Sales'].sum():,.0f}M units")

    st.markdown("### Global sales trend over time")
    trend = sales_df.copy()
    trend["Year"] = trend["Year"].dt.year
    trend = trend[trend["Year"] > 1980].groupby("Year")["Global_Sales"].sum().reset_index()
    fig = px.area(trend, x="Year", y="Global_Sales", labels={"Global_Sales": "Global Sales (M units)"})
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Use the sidebar to explore ratings & engagement, sales figures, "
        "or the merged dataset in depth."
    )

# --------------------------------------------------------------------------
# Games (ratings / engagement) section
# --------------------------------------------------------------------------
elif section == "Game Ratings & Engagement (games.csv)":
    st.title("Game Ratings & Engagement")

    top_n = st.sidebar.slider("Top N", 5, 20, 10)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Top Rated", "Genres & Studios", "Backlog / Wishlist", "Release & Rating Trends"]
    )

    with tab1:
        st.subheader("Top-rated games by user reviews")
        top_rated = games_df.sort_values("Rating", ascending=False).head(top_n)
        fig = px.bar(top_rated, x="Rating", y="Title", orientation="h", color="Rating")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top wishlisted games")
        wishlisted = games_df[["Title", "Wishlist"]].sort_values("Wishlist", ascending=False).head(top_n)
        fig = px.bar(wishlisted, x="Wishlist", y="Title", orientation="h", color="Wishlist")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Most common genres")
        genre_exp = explode_genres(games_df)
        genre_counts = genre_exp["Genres"].value_counts().head(top_n).reset_index()
        genre_counts.columns = ["Genre", "Count"]
        fig = px.bar(genre_counts, x="Genre", y="Count", color="Count")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Average plays per genre")
        genre_exp["Plays"] = pd.to_numeric(genre_exp["Plays"], errors="coerce")
        avg_plays = genre_exp.groupby("Genres")["Plays"].mean().sort_values(ascending=False).head(top_n)
        fig = px.bar(avg_plays.reset_index(), x="Genres", y="Plays", color="Plays")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Highest-rated studios (5+ games)")
        studio_stats = (
            games_df.groupby("Team")
            .agg(total_games=("Title", "count"), avg_rating=("Rating", "mean"), avg_plays=("Plays", "mean"))
            .sort_values("total_games", ascending=False)
        )
        impactful = studio_stats[studio_stats["total_games"] >= 5].sort_values("avg_rating", ascending=False).head(top_n)
        fig = px.bar(impactful.reset_index(), x="Team", y="avg_rating", color="avg_rating")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Games with the highest backlog-vs-wishlist gap")
        top_gap = (
            games_df[["Title", "Backlogs", "Wishlist", "Backlog_gap"]]
            .sort_values("Backlog_gap", ascending=False)
            .head(top_n)
        )
        fig = px.bar(top_gap, x="Title", y="Backlog_gap", color="Backlog_gap")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Rating vs. Wishlist / Backlogs")
        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(games_df, x="Rating", y="Wishlist", opacity=0.5, trendline="ols")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.scatter(games_df, x="Rating", y="Backlogs", opacity=0.5, trendline="ols")
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Distribution of user ratings")
        fig = px.histogram(games_df, x="Rating", nbins=20)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Release volume over time (by year)")
        release_by_year = games_df.copy()
        release_by_year["Year"] = release_by_year["Release Date"].dt.year
        release_by_year = release_by_year[release_by_year["Year"] > 1980]
        counts = release_by_year["Year"].value_counts().sort_index().reset_index()
        counts.columns = ["Year", "Releases"]
        fig = px.line(counts, x="Year", y="Releases", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# Sales section
# --------------------------------------------------------------------------
elif section == "Global Sales (vgsales.csv)":
    st.title("Global Sales")

    top_n = st.sidebar.slider("Top N", 5, 20, 10)
    sale_visual = sales_df.copy()
    sale_visual["Year"] = sale_visual["Year"].dt.year

    tab1, tab2, tab3 = st.tabs(["By Region / Platform", "By Publisher / Game", "Over Time"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sales share by region")
            total_sale = sale_visual[REGIONS].sum().reset_index()
            total_sale.columns = ["Region", "Sales"]
            fig = px.pie(total_sale, names="Region", values="Sales", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Best-selling platforms")
            platform_sale = sale_visual.groupby("Platform")["Global_Sales"].sum().sort_values(ascending=False).head(top_n)
            fig = px.bar(platform_sale.reset_index(), x="Platform", y="Global_Sales", color="Global_Sales")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Regional sales comparison for a chosen platform")
        platform_choice = st.selectbox("Platform", sorted(sale_visual["Platform"].unique()), index=0)
        platform_data = sale_visual[sale_visual["Platform"] == platform_choice]
        fig = px.box(platform_data[REGIONS])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Top publishers by total sales")
        top_pub = sale_visual.groupby("Publisher")["Global_Sales"].sum().sort_values(ascending=False).head(top_n)
        fig = px.bar(top_pub.reset_index(), x="Global_Sales", y="Publisher", orientation="h", color="Global_Sales")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top-selling games globally")
        top_games = sale_visual.sort_values("Global_Sales", ascending=False).head(top_n)
        fig = px.bar(top_games, x="Global_Sales", y="Name", orientation="h", color="Global_Sales")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Average sales per publisher")
        avg_sales = sale_visual.groupby("Publisher")["Global_Sales"].mean().sort_values(ascending=False).head(top_n)
        fig = px.bar(avg_sales.reset_index(), x="Publisher", y="Global_Sales", color="Global_Sales")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Global sales trend over years")
        yearly = sale_visual[sale_visual["Year"] > 1980].groupby("Year")["Global_Sales"].sum().reset_index()
        fig = px.line(yearly, x="Year", y="Global_Sales", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Market evolution by platform over time")
        platform_sales = (
            sale_visual[sale_visual["Year"] > 1980]
            .groupby(["Year", "Platform"])["Global_Sales"]
            .sum()
            .reset_index()
        )
        fig = px.area(platform_sales, x="Year", y="Global_Sales", color="Platform")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Yearly sales by region")
        year_region = sale_visual[sale_visual["Year"] > 1980].groupby("Year")[REGIONS].sum().reset_index()
        fig = px.line(year_region, x="Year", y=REGIONS, markers=False)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Regional genre preferences")
        genre_region = sale_visual.groupby("Genre")[REGIONS].sum()
        fig = px.bar(genre_region.reset_index(), x="Genre", y=REGIONS, barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# Merged section
# --------------------------------------------------------------------------
else:
    st.title("Merged Insights (games.csv + vgsales.csv)")
    st.caption(
        "Note: this merge is on cleaned title text. Not every game in games.csv has "
        "an exact match in vgsales.csv, and matched titles can appear once per platform, "
        "so treat these charts as a partial-coverage view rather than the full catalog."
    )

    top_n = st.sidebar.slider("Top N", 5, 20, 10)
    merged = merged_df.copy()
    merged["Rating"] = pd.to_numeric(merged["Rating"], errors="coerce")
    merged["Global_Sales"] = pd.to_numeric(merged["Global_Sales"], errors="coerce")

    tab1, tab2 = st.tabs(["Genre Sales", "Rating vs Sales"])

    with tab1:
        st.subheader("Global sales by genre")
        genre_merged = explode_genres(merged)
        genre_sales = genre_merged.groupby("Genres")["Global_Sales"].sum().sort_values(ascending=False).head(top_n)
        fig = px.bar(genre_sales.reset_index(), x="Genres", y="Global_Sales", color="Global_Sales")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Regional sales heatmap by genre")
        regional = genre_merged[["Genres"] + REGIONS].dropna()
        regional_agg = regional.groupby("Genres")[REGIONS].sum()
        fig = px.imshow(regional_agg, aspect="auto", color_continuous_scale="YlOrRd", labels=dict(color="Sales"))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("User engagement (avg. plays) by genre")
        genre_merged["Plays"] = pd.to_numeric(genre_merged["Plays"], errors="coerce")
        engagement = genre_merged.groupby("Genres")["Plays"].mean().sort_values(ascending=False).head(top_n)
        fig = px.bar(engagement.reset_index(), x="Plays", y="Genres", orientation="h", color="Plays")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        rating_sales = merged[["Rating", "Global_Sales"]].dropna()
        corr = rating_sales["Rating"].corr(rating_sales["Global_Sales"])
        st.metric("Correlation: Rating vs Global Sales", f"{corr:.3f}")

        fig = px.scatter(rating_sales, x="Rating", y="Global_Sales", opacity=0.4, trendline="ols")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Games with high ratings (> 4) by platform")
        high_rating = merged[merged["Rating"] > 4]
        platform_high = high_rating["Platform"].value_counts().head(top_n).reset_index()
        platform_high.columns = ["Platform", "Count"]
        fig = px.bar(platform_high, x="Platform", y="Count", color="Count")
        st.plotly_chart(fig, use_container_width=True)

