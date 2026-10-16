"""Day 7 interactive dashboard. Run: python -m streamlit run app.py."""

from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "data" / "sales_profitability.csv"
MONEY = ["revenue", "cost_of_goods_sold", "gross_profit"]
BLUE = "#3B82F6"
TEAL = "#14B8A6"


def load_data(path):
    """Read Day 4 money as integer cents to preserve verified totals."""
    data = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"order_id", "date", "product", "quantity", "category", "region", *MONEY}
    if not required.issubset(data.columns):
        raise ValueError("The transaction file is missing required columns.")
    if data.empty:
        raise ValueError("The transaction file has no records.")
    if data["order_id"].eq("").any() or data["order_id"].duplicated().any():
        raise ValueError("This sample requires one unique order ID per row.")
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
    for field in ["product", "category", "region"]:
        if data[field].str.strip().eq("").any():
            raise ValueError(f"The transaction file contains a missing {field}.")
    quantities = pd.to_numeric(data["quantity"], errors="raise")
    if quantities.isna().any() or ((quantities <= 0) | (quantities % 1 != 0)).any():
        raise ValueError("Quantities must be positive whole numbers.")
    data["quantity"] = quantities.astype("int64")
    for field in MONEY:
        def cents(text):
            amount = Decimal(text)
            if not amount.is_finite() or amount * 100 != (amount * 100).to_integral_value():
                raise ValueError(f"Invalid cent-precision amount in {field}.")
            return int(amount * 100)
        data[field + "_cents"] = data[field].map(cents)
    if ((data["revenue_cents"] < 0) | (data["cost_of_goods_sold_cents"] < 0)).any():
        raise ValueError("Negative revenue or cost is outside this sample's scope.")
    if not (data["revenue_cents"] - data["cost_of_goods_sold_cents"]).equals(data["gross_profit_cents"]):
        raise ValueError("Transaction revenue, cost, and gross profit do not reconcile.")
    data["month"] = data["date"].dt.to_period("M").dt.to_timestamp()
    return data


def grouped_totals(data, dimension):
    fields = [field + "_cents" for field in MONEY]
    result = data.groupby(dimension, as_index=False)[fields].sum()
    # Floats are used only for chart presentation after exact-cent aggregation.
    for field in MONEY:
        result[field] = result[field + "_cents"] / 100
    return result


def filter_transactions(data, start, end, regions, categories):
    """Apply inclusive dates and selections once for all dashboard outputs."""
    return data.loc[
        data["date"].between(pd.Timestamp(start), pd.Timestamp(end))
        & data["region"].isin(regions)
        & data["category"].isin(categories)
    ].copy()


def product_summary(data):
    grouped = data.groupby(["product", "category"], as_index=False).agg(
        transactions=("order_id", "size"), units_sold=("quantity", "sum"),
        revenue_cents=("revenue_cents", "sum"),
        cost_of_goods_sold_cents=("cost_of_goods_sold_cents", "sum"),
        gross_profit_cents=("gross_profit_cents", "sum"),
        loss_making_transactions=("gross_profit_cents", lambda values: int((values < 0).sum())),
    )
    grouped["gross_margin_pct"] = [
        None if revenue == 0 else float(Decimal(int(profit)) / Decimal(int(revenue)) * 100)
        for profit, revenue in zip(grouped["gross_profit_cents"], grouped["revenue_cents"])
    ]
    for field in MONEY:
        grouped[field] = grouped[field + "_cents"] / 100
    return grouped.sort_values(["gross_profit_cents", "product"], ascending=[False, True])


def transaction_csv(data):
    """Download filtered source fields without internal calculation columns."""
    columns = [column for column in data.columns if column != "month" and not column.endswith("_cents")]
    output = data[columns].copy()
    output["date"] = output["date"].dt.strftime("%Y-%m-%d")
    return output.to_csv(index=False, lineterminator="\n").encode("utf-8")


def style_chart(fig):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial", size=13),
        margin=dict(l=0, r=12, t=15, b=0), height=340,
        legend=dict(orientation="h", y=1.15, x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def main():
    st.set_page_config(page_title="Retail Profitability", page_icon="📊", layout="wide")
    st.title("Business Profitability Dashboard")
    st.caption("Retail performance · Synthetic sample · All amounts in USD")

    try:
        data = load_data(DATA_PATH)
    except (OSError, ValueError, InvalidOperation, pd.errors.ParserError) as error:
        st.error(f"Could not load profitability data: {error}")
        st.info("Run python scripts/calculate_profitability.py in the project folder, then refresh this page.")
        st.stop()

    all_count = len(data)
    first_date, last_date = data["date"].min().date(), data["date"].max().date()
    with st.sidebar:
        st.header("Filter transactions")
        selected_dates = st.date_input(
            "Date range", value=(first_date, last_date), min_value=first_date,
            max_value=last_date, format="MM/DD/YYYY", key="date_filter",
        )
        regions = st.multiselect("Regions", options=sorted(data["region"].unique()),
                                 default=sorted(data["region"].unique()), key="region_filter")
        categories = st.multiselect("Categories", options=sorted(data["category"].unique()),
                                    default=sorted(data["category"].unique()), key="category_filter")
        st.caption("Both dates are included. Clear all regions or categories to show no transactions.")
    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
        st.info("Select both a start date and an end date to view the dashboard.")
        st.stop()
    start, end = selected_dates
    if start > end:
        st.warning("Choose an end date on or after the start date.")
        st.stop()
    data = filter_transactions(data, start, end, regions, categories)
    if data.empty:
        st.info("No transactions match these filters. Expand the date range or select additional regions and categories.")
        st.stop()

    revenue = int(data["revenue_cents"].sum())
    cost = int(data["cost_of_goods_sold_cents"].sum())
    profit = int(data["gross_profit_cents"].sum())
    gross_margin = None if revenue == 0 else Decimal(profit) / Decimal(revenue) * 100
    st.write(f"**{start:%b %d, %Y} – {end:%b %d, %Y}** · {len(data):,} of {all_count:,} transactions")
    st.caption("All cards, charts, the product table, and the download reflect the current filters.")
    columns = st.columns(4)
    columns[0].metric("Revenue", f"${Decimal(revenue) / 100:,.2f}")
    columns[1].metric("Cost of goods sold", f"${Decimal(cost) / 100:,.2f}")
    columns[2].metric("Gross profit", f"${Decimal(profit) / 100:,.2f}")
    columns[3].metric("Gross margin", "Unavailable" if gross_margin is None else f"{gross_margin:.2f}%")

    st.divider()
    st.subheader("Monthly performance")
    monthly = grouped_totals(data, "month")
    fig = go.Figure()
    for field, label, color in [("revenue", "Revenue", BLUE), ("gross_profit", "Gross profit", TEAL)]:
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly[field], name=label, mode="lines+markers",
            line=dict(color=color, width=3),
            hovertemplate="%{x|%b %Y}<br>" + label + ": $%{y:,.2f}<extra></extra>",
        ))
    style_chart(fig)
    fig.update_xaxes(title=None, tickformat="%b", dtick="M1")
    fig.update_yaxes(title="USD", tickprefix="$", rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True, key="monthly_chart")

    left, right = st.columns(2)
    for container, dimension, title, color in [
        (left, "category", "Gross profit by category", BLUE),
        (right, "region", "Gross profit by region", TEAL),
    ]:
        with container:
            st.subheader(title)
            summary = grouped_totals(data, dimension).sort_values("gross_profit")
            fig = px.bar(summary, x="gross_profit", y=dimension, orientation="h",
                         color_discrete_sequence=[color], labels={"gross_profit": "Gross profit (USD)", dimension: ""})
            fig.update_traces(hovertemplate="%{y}<br>Gross profit: $%{x:,.2f}<extra></extra>")
            style_chart(fig)
            fig.update_xaxes(tickprefix="$", zeroline=True)
            fig.update_yaxes(categoryorder="array", categoryarray=summary[dimension].tolist())
            st.plotly_chart(fig, use_container_width=True, key=f"{dimension}_chart")

    st.divider()
    st.subheader("Product profitability")
    products = product_summary(data)
    st.dataframe(
        products[["product", "category", "transactions", "units_sold", "revenue",
                  "cost_of_goods_sold", "gross_profit", "gross_margin_pct", "loss_making_transactions"]],
        hide_index=True, width="stretch",
        column_config={
            "product": "Product", "category": "Category", "transactions": "Orders",
            "units_sold": "Units sold", "loss_making_transactions": "Loss-making orders",
            "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
            "cost_of_goods_sold": st.column_config.NumberColumn("Cost of goods sold", format="$%.2f"),
            "gross_profit": st.column_config.NumberColumn("Gross profit", format="$%.2f"),
            "gross_margin_pct": st.column_config.NumberColumn("Gross margin", format="%.2f%%"),
        },
    )
    st.caption("Sorted by gross profit. Click a column heading to sort. Margins use product totals; zero-revenue margins are blank.")
    st.download_button(
        "Download filtered transactions (CSV)", data=transaction_csv(data),
        file_name=f"retail_transactions_{start:%Y%m%d}_{end:%Y%m%d}.csv",
        mime="text/csv", key="download_transactions",
    )

    st.divider()
    loss_count = int((data["gross_profit_cents"] < 0).sum())
    gross_loss = -int(data.loc[data["gross_profit_cents"] < 0, "gross_profit_cents"].sum())
    st.subheader("Loss-making transactions")
    st.write(
        f"**{loss_count:,} transactions** have a combined gross loss of "
        f"**${Decimal(gross_loss) / 100:,.2f}**. These losses are already included in gross profit above."
    )
    with st.expander("How to read this dashboard"):
        st.markdown(
            "- **Revenue:** quantity × unit price × (1 − discount).\n"
            "- **Cost of goods sold:** quantity × unit cost.\n"
            "- **Gross profit:** revenue minus cost of goods sold.\n"
            "- **Gross margin:** total gross profit ÷ total revenue × 100.\n"
            "- Money is rounded to cents per transaction in the Day 4 pipeline.\n"
            "- Gross profit excludes operating expenses, interest, and taxes.\n"
            "- All data is synthetic. Monthly volume and discount patterns were built into the generator."
        )
    st.caption("Source: synthetic 2025 retail transactions. Use the sidebar to explore product and regional performance.")


if __name__ == "__main__":
    main()
