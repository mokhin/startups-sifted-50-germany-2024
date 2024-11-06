import altair as alt
import polars as pl
import streamlit as st

alt.themes.enable("vox")
st.set_page_config(layout="wide")

SIFTED_50_FILE = "sifted_50_germany_top_growing_startups.csv"


# Functions
@st.cache_data
def create_startups_df(data_file: str) -> pl.DataFrame:
    df = pl.read_csv(data_file)
    df = df.with_columns(
        pl.col("Sector")
        .str.split_exact(" - ", n=2)
        .struct.rename_fields(["Industry", "Segment"])
        .alias("fields")
    ).unnest("fields")
    return df


@st.cache_data
def get_all_cities(df: pl.DataFrame) -> list:
    return df["Location"].unique()


def bar_chart(
    df: pl.DataFrame,
    y: str,
    x: str,
    func: str,
    title: str = "",
) -> alt.Chart:
    bars = (
        alt.Chart(df, title=title)
        .mark_bar()
        .encode(
            y=alt.Y(
                f"{y}:N",
                sort=alt.EncodingSortField(op="count", order="descending"),
                title=None,
                axis=alt.Axis(labelColor="black", labelBaseline="middle"),
            ),
            x=alt.X(f"{func}({x})", title=None, axis=None),
        )
    )

    text = bars.mark_text(
        align="left",
        baseline="middle",
        dx=3,
    ).encode(text=f"{func}({x}):Q")

    return bars + text


def combine_bar_charts(*plots):
    combined = alt.vconcat()
    for plot in plots:
        combined |= plot
    return (
        combined.configure_view(stroke=None)
        .configure_concat(spacing=10)
        .configure_axisY(labelPadding=70, labelAlign="left")
    )


def main():
    # Main dataset
    startups_df = create_startups_df(SIFTED_50_FILE)

    # Page layout
    st.markdown("## Top 50 Fastest Growing Startups in Germany 2024")
    st.markdown(
        "##### Source: [Sifted 50: Germany](https://sifted.eu/leaderboards/germany-2024)"
    )

    # Filters
    col_1, col_2, _ = st.columns([1, 1, 4])

    # Total scorecards
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.metric(label="Total Startups", value=startups_df.height)

    with col_2:
        st.metric(label="Total Employees", value=startups_df["Employees"].sum())

    with col_3:
        st.metric(
            label="Total Funding (€M)", value=startups_df["Total Funding (€M)"].sum()
        )

    with col_4:
        st.metric(
            label="Median Revenue Grow (2-yr CAGR %)",
            value=startups_df["2-yr Revenue CAGR (%)"].median(),
        )

    with col_1:
        location = st.selectbox(
            "Select city",
            ["All"] + sorted(startups_df["Location"].unique()),
        )

    with col_2:
        industry = st.selectbox(
            "Select industry",
            ["All"] + sorted(startups_df["Industry"].unique()),
        )

    # Filter polars dataframe
    if location == "All":
        filtered_df = startups_df
    else:
        filtered_df = startups_df.filter(pl.col("Location") == location)

    if industry != "All":
        filtered_df = filtered_df.filter(pl.col("Industry") == industry)

    st.altair_chart(
        combine_bar_charts(
            bar_chart(
                df=filtered_df,
                y="Location",
                x="Company",
                func="count",
                title="Number of Startups in Top 50",
            ),
            bar_chart(
                df=filtered_df,
                y="Location",
                x="Employees",
                func="sum",
                title="Number of Employees",
            ),
            bar_chart(
                df=filtered_df,
                y="Location",
                x="Total Funding (€M)",
                func="sum",
                title="Total Funding (€M)",
            ),
            bar_chart(
                df=filtered_df,
                y="Location",
                x="2-yr Revenue CAGR (%)",
                func="median",
                title="Median Revenue Grow (2-yr CAGR %)",
            ),
        ),
    )

    st.markdown("##### ")

    st.altair_chart(
        combine_bar_charts(
            bar_chart(
                df=filtered_df,
                y="Industry",
                x="Company",
                func="count",
            ),
            bar_chart(
                df=filtered_df,
                y="Industry",
                x="Employees",
                func="sum",
            ),
            bar_chart(
                df=filtered_df,
                y="Industry",
                x="Total Funding (€M)",
                func="sum",
            ),
            bar_chart(
                df=filtered_df,
                y="Industry",
                x="2-yr Revenue CAGR (%)",
                func="median",
            ),
        ),
    )

    st.dataframe(
        filtered_df.select(
            [
                "Rank",
                "Company",
                "Sector",
                "Location",
                "Launch Year",
                "Employees",
                "Total Funding (€M)",
                "2-yr Revenue CAGR (%)",
            ]
        ),
        column_config={
            "Launch Year": st.column_config.NumberColumn(
                "Launched",
                help="The year the company was launched",
                min_value=2000,
                max_value=2024,
                step=1,
                format="%d",
            ),
            "2-yr Revenue CAGR (%)": st.column_config.NumberColumn(
                "Revenue Growth",
                help="2-year compound annual growth rate",
                min_value=0,
                max_value=100,
                step=0.1,
                format="%0.0f%%",
            ),
        },
    )


if __name__ == "__main__":
    main()
