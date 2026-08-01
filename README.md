# 🎮 Video Game Sales & Ratings Dashboard

An interactive Streamlit dashboard analyzing video game data from two angles:
**user ratings & engagement** (reviews, wishlists, playtime) and **historical
global sales** (regional breakdowns, platforms, publishers, genres).

The project covers the full pipeline — cleaning messy raw data (mixed types,
missing values, shorthand numbers like "3.2K"), merging two independent
datasets on game title, exploring it with pandas, and surfacing the findings
in a filterable, multi-tab dashboard built with Streamlit and Plotly.

## Highlights

- **Data cleaning**: type coercion, missing-value handling, and title
  normalization to merge two datasets that don't share a common key.
- **EDA**: top-rated games, genre popularity, studio performance, regional
  sales trends, platform market share, rating-vs-sales correlation, and more.
- **Dashboard**: interactive Plotly charts (hover, zoom, pan), a "Top N"
  slider, and platform/genre filters — no database required, runs entirely
  off two CSVs.

## Tech stack

`Python` · `pandas` · `Streamlit` · `Plotly`

## Datasets

- [Video Game Reviews & Ratings](#) — user ratings, playtime, wishlist/backlog counts
- [Video Game Sales (vgsales)](#) — regional and global sales by platform/publisher
