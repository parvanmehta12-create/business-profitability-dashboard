"""Day 6 dashboard. Run: python -m streamlit run app.py."""

from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "data" / "sales_profitability.csv"
MONEY = ["revenue", "cost_of_goods_sold", "gross_profit"]
NAVY = "#17365D"
TEAL = "#008675"


def load_data(path):
    """Read Day 4 money as integer cents to preserve verified totals."""
    data = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"order_id", "date", "category", "region", *MONEY}
    if not required.issubset(data.columns):
        raise ValueError("The transaction file is missing required columns.")
    if data.empty:
        raise ValueError("The transaction file has no records.")
    if data["order_id"].eq("").any() or data["order_id"].duplicated().any():
        raise ValueError("This sample requires one unique order ID per row.")
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
    for field in ["category", "region"]:
        if data[field].str.strip().eq("").any():
            raise ValueError(f"The transaction file contains a missing {field}.")
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

    revenue = int(data["revenue_cents"].sum())
    cost = int(data["cost_of_goods_sold_cents"].sum())
    profit = int(data["gross_profit_cents"].sum())
    gross_margin = None if revenue == 0 else Decimal(profit) / Decimal(revenue) * 100
    start, end = data["date"].min(), data["date"].max()
    st.write(f"**{start:%b %d, %Y} – {end:%b %d, %Y}** · {len(data):,} transactions")
    columns = st.columns(4)
    columns[0].metric("Revenue", f"${Decimal(revenue) / 100:,.2f}")
    columns[1].metric("Cost of goods sold", f"${Decimal(cost) / 100:,.2f}")
    columns[2].metric("Gross profit", f"${Decimal(profit) / 100:,.2f}")
    columns[3].metric("Gross margin", "Unavailable" if gross_margin is None else f"{gross_margin:.2f}%")

    st.divider()
    st.subheader("Monthly performance")
    monthly = grouped_totals(data, "month")
    fig = go.Figure()
    for field, label, color in [("revenue", "Revenue", NAVY), ("gross_profit", "Gross profit", TEAL)]:
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
        (left, "category", "Gross profit by category", NAVY),
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
    st.caption("Source: synthetic 2025 retail transactions. Filters and product-level exploration are planned for Day 7.")


if __name__ == "__main__":
    main()
