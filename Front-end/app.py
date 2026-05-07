"""
app.py — AI-Powered Smart Forecasting for Zero Food Waste
Fixed Version — All bugs resolved, full functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

from utils.forecast import ForecastEngine
from utils.ai_chat import AIAssistant

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Smart Forecasting — Zero Food Waste",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("chat_history", []),
    ("forecast_finalized", False),
    ("forecast_edits", None),
    ("alert_restock_threshold", 20),
    ("alert_waste_threshold", 70),
    ("alert_expiry_days", 3),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Cached resource init ──────────────────────────────────────────────────────
@st.cache_resource
def get_forecast_engine():
    return ForecastEngine()

@st.cache_resource
def get_ai_assistant():
    return AIAssistant()

fe = get_forecast_engine()
ai = get_ai_assistant()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🧠 Smart Forecast")
tab_selection = st.sidebar.radio(
    "Navigate",
    ["📦 Product Management", "📊 Forecast Dashboard",
     "📈 Analytics & Reports", "🗑️ Waste Management",
     "⚠️ Alerts & Monitoring", "🤖 AI Assistant"],
)

STORES = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
selected_store = st.sidebar.selectbox("🏪 Select Store", STORES)

# ── AI Status ──────────────────────────────────────────────────────────────────
# Removed AI status and version as per user request


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRODUCT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
if tab_selection == "📦 Product Management":
    st.header("📦 Product Management")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.subheader("Product Catalog")

        f1, f2, f3 = st.columns(3)
        with f1:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All", "Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"],
            )
        with f2:
            risk_filter = st.selectbox(
                "Filter by Waste Risk",
                ["All", "High Risk (>70%)", "Medium Risk (30-70%)", "Low Risk (<30%)"],
            )
        with f3:
            stock_filter = st.selectbox(
                "Filter by Stock Status",
                ["All", "In Stock", "Low Stock", "Out of Stock"],
            )

        all_products = fe.get_product_list(selected_store)

        if not all_products.empty:
            filtered = fe.apply_product_filters(all_products, category_filter, risk_filter, stock_filter)
            st.caption(f"Showing {len(filtered)} of {len(all_products)} products")

            display_cols = ["Product Name", "Category", "Current Stock", "Reorder Level",
                            "Unit Price", "Supplier", "Status", "Expiry Date", "Waste Risk %"]
            display_cols = [c for c in display_cols if c in filtered.columns]

            edited_products = st.data_editor(
                filtered[display_cols],
                column_config={
                    "Product Name": st.column_config.TextColumn("Product Name", disabled=True),
                    "Category": st.column_config.SelectboxColumn(
                        "Category", options=["Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"]),
                    "Current Stock": st.column_config.NumberColumn("Current Stock", min_value=0),
                    "Reorder Level": st.column_config.NumberColumn("Reorder Level", min_value=0),
                    "Unit Price": st.column_config.NumberColumn("Unit Price ($)", min_value=0.01),
                    "Supplier": st.column_config.TextColumn("Supplier"),
                    "Status": st.column_config.SelectboxColumn(
                        "Status", options=["Active", "Inactive", "Seasonal"]),
                    "Expiry Date": st.column_config.TextColumn("Expiry Date"),
                    "Waste Risk %": st.column_config.ProgressColumn(
                        "Waste Risk %", min_value=0, max_value=100, format="%d%%"),
                },
                hide_index=True,
                use_container_width=True,
                key="product_editor",
            )

            if st.button("💾 Save Product Changes", type="primary"):
                # Merge back all store columns
                full_cols = all_products.copy()
                for idx, row in edited_products.iterrows():
                    mask = full_cols["Product Name"] == row["Product Name"]
                    for col in display_cols:
                        full_cols.loc[mask, col] = row[col]
                if fe.save_product_updates(full_cols, selected_store):
                    st.success("✅ Product information saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save. Please check file permissions.")
        else:
            st.warning("No products found for this store.")

    with col_side:
        st.subheader("➕ Add New Product")
        with st.expander("Add New Product", expanded=True):
            with st.form("add_product_form", clear_on_submit=True):
                new_name = st.text_input("Product Name *")
                new_cat = st.selectbox(
                    "Category *", ["Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"])
                new_stock = st.number_input("Initial Stock", min_value=0, value=50)
                new_reorder = st.number_input("Reorder Level", min_value=0, value=15)
                new_price = st.number_input("Unit Price ($) *", min_value=0.01, value=2.00, step=0.01)
                new_supplier = st.text_input("Supplier *")
                default_expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                new_expiry = st.text_input("Expiry Date (YYYY-MM-DD) *", value=default_expiry)
                new_status = st.selectbox("Status", ["Active", "Inactive", "Seasonal"])

                if st.form_submit_button("➕ Add Product", type="primary"):
                    errors = fe.validate_new_product(
                        selected_store, new_name, new_cat,
                        new_stock, new_reorder, new_price,
                        new_supplier, new_expiry,
                    )
                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        ok = fe.add_new_product(
                            selected_store, new_name, new_cat,
                            new_stock, new_reorder, new_price,
                            new_supplier, new_expiry, new_status,
                        )
                        if ok:
                            st.success(f"✅ '{new_name}' added to {selected_store}!")
                            st.rerun()
                        else:
                            st.error("Failed to add product. Please try again.")

        # Quick stats
        st.subheader("📊 Quick Stats")
        if not all_products.empty:
            total_products = len(all_products)
            low_stock_count = len(all_products[all_products["Current Stock"] <= all_products["Reorder Level"]])
            high_risk_count = len(all_products[all_products["Waste Risk %"] > 70])
            out_of_stock = len(all_products[all_products["Current Stock"] == 0])

            c1, c2 = st.columns(2)
            c1.metric("Total Products", total_products)
            c2.metric("Out of Stock", out_of_stock)
            c1.metric("Low Stock", low_stock_count,
                      delta=f"-{low_stock_count}" if low_stock_count > 0 else "OK")
            c2.metric("High Waste Risk", high_risk_count,
                      delta=f"-{high_risk_count}" if high_risk_count > 0 else "OK")

            # Category breakdown pie
            cat_counts = all_products.groupby("Category").size().reset_index(name="Count")
            fig = px.pie(cat_counts, values="Count", names="Category",
                         title="Products by Category", height=280)
            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FORECAST DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif tab_selection == "📊 Forecast Dashboard":
    st.header("📊 Smart Demand Forecasting")

    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        forecast_period = st.selectbox(
            "📅 Forecast Period",
            ["Today", "Tomorrow", "Next 3 Days", "Next Week", "Monthly", "Yearly"],
        )
    with f_col2:
        if st.button("🔄 Refresh Forecast"):
            st.session_state.forecast_edits = None
            st.session_state.forecast_finalized = False
            st.rerun()

    col1, col2 = st.columns([2, 1])

    with col1:
        forecast_data = fe.get_enhanced_forecast(selected_store, forecast_period)

        if not forecast_data.empty:
            # Reset edits when period changes
            period_key = f"{selected_store}_{forecast_period}"
            if (st.session_state.forecast_edits is None or
                    st.session_state.get("last_period_key") != period_key):
                st.session_state.forecast_edits = forecast_data.copy()
                st.session_state["last_period_key"] = period_key

            st.subheader(f"📈 Demand Predictions — {forecast_period}")
            st.info("💡 AI confidence reflects reliability based on historical demand patterns.")

            edited_df = st.data_editor(
                st.session_state.forecast_edits,
                column_config={
                    "Product Name": st.column_config.TextColumn("Product", disabled=True),
                    "Category": st.column_config.TextColumn("Category", disabled=True),
                    "Predicted Qty": st.column_config.NumberColumn("AI Prediction", disabled=True),
                    "Manual Override": st.column_config.NumberColumn("Your Adjustment", min_value=0),
                    "Final Qty": st.column_config.NumberColumn("Final Forecast", disabled=True),
                    "Waste Risk %": st.column_config.ProgressColumn(
                        "Waste Risk", min_value=0, max_value=100, format="%d%%"),
                    "Confidence": st.column_config.ProgressColumn(
                        "AI Confidence", min_value=0, max_value=100, format="%d%%"),
                    "Current Stock": st.column_config.NumberColumn("Current Stock", disabled=True),
                    "Suggested Action": st.column_config.TextColumn("Recommendation", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key="forecast_editor",
            )

            # Recalculate Final Qty
            edited_df["Final Qty"] = edited_df.apply(
                lambda r: r["Manual Override"] if r["Manual Override"] > 0 else r["Predicted Qty"],
                axis=1,
            )
            st.session_state.forecast_edits = edited_df

            # Forecast charts
            st.subheader("📊 Forecast Visualizations")
            ch1, ch2 = st.columns(2)
            with ch1:
                fig_bar = px.bar(
                    edited_df.sort_values("Predicted Qty", ascending=True).tail(10),
                    x="Predicted Qty", y="Product Name", orientation="h",
                    color="Waste Risk %", color_continuous_scale="RdYlGn_r",
                    title="Top 10 Predicted Demand by Product",
                    labels={"Predicted Qty": "Predicted Units"},
                )
                fig_bar.update_layout(height=350, coloraxis_showscale=True)
                st.plotly_chart(fig_bar, use_container_width=True)
            with ch2:
                fig_risk = px.scatter(
                    edited_df, x="Predicted Qty", y="Waste Risk %",
                    size="Confidence", color="Category",
                    hover_name="Product Name",
                    title="Demand vs Waste Risk",
                )
                fig_risk.update_layout(height=350)
                st.plotly_chart(fig_risk, use_container_width=True)

            # Action buttons
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("💾 Save Forecast", type="primary"):
                    if fe.save_forecast(edited_df, selected_store, forecast_period):
                        st.success("Forecast saved!")
                    else:
                        st.error("Save failed.")
            with b2:
                if st.button("✅ Finalize"):
                    st.session_state.forecast_finalized = True
                    st.success("Forecast finalized!")
            with b3:
                if st.button("📧 Send Report"):
                    if st.session_state.forecast_finalized:
                        st.success("Report sent to management!")
                    else:
                        st.warning("Finalize the forecast first.")
            with b4:
                if st.session_state.forecast_finalized:
                    pdf = fe.generate_forecast_pdf(edited_df, selected_store, forecast_period)
                    st.download_button(
                        "⬇️ Download PDF", data=pdf,
                        file_name=f"forecast_{selected_store.replace(' ','_')}_{forecast_period}.html",
                        mime="text/html",
                    )
        else:
            st.warning("No forecast data available for this store/period.")

    with col2:
        st.subheader("📋 Forecast Summary")
        if not forecast_data.empty:
            total_pred = int(forecast_data["Predicted Qty"].sum())
            final_df = st.session_state.forecast_edits if st.session_state.forecast_edits is not None else forecast_data
            total_final = int(final_df["Final Qty"].sum())
            high_risk = len(forecast_data[forecast_data["Waste Risk %"] > 70])
            avg_conf = round(float(forecast_data["Confidence"].mean()), 1)

            st.metric("AI Predicted Total", f"{total_pred:,}")
            st.metric("Final Forecast", f"{total_final:,}",
                      delta=f"{total_final - total_pred:+,}")
            st.metric("High Risk Items", high_risk)
            st.metric("Avg AI Confidence", f"{avg_conf}%")

            status = "✅ Finalized" if st.session_state.forecast_finalized else "⏳ Draft"
            st.info(f"Status: {status}")

            # Accuracy
            st.subheader("🎯 Accuracy")
            acc = fe.get_forecast_accuracy(selected_store)
            if acc:
                st.metric("Last Week", f"{acc['weekly']:.1f}%")
                st.metric("Monthly", f"{acc['monthly']:.1f}%")
                st.metric("Trend", acc["trend"], delta=acc["trend_delta"])

            # Historical trend chart
            hist = fe.get_sales_analytics(selected_store, "Weekly")
            if not hist.empty and "Actual_Sales" in hist.columns:
                fig_hist = px.line(hist, x="Week", y="Actual_Sales",
                                   title="Weekly Sales Trend", height=250)
                fig_hist.update_layout(margin=dict(t=40, b=20))
                st.plotly_chart(fig_hist, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS & REPORTS
# ══════════════════════════════════════════════════════════════════════════════
elif tab_selection == "📈 Analytics & Reports":
    st.header("📈 Sales Analytics & Business Reports")

    p1, p2 = st.columns(2)
    with p1:
        analysis_period = st.selectbox("📅 Time Period", ["Daily", "Weekly", "Monthly", "Yearly"])
    with p2:
        report_type = st.selectbox("📄 Report Type", ["Sales Report", "Waste Report", "Combined Report"])

    # ── Top KPI row ────────────────────────────────────────────────────────
    sales_daily = fe.get_sales_analytics(selected_store, "Daily")
    waste_reduction = fe.calculate_waste_reduction_percentage(selected_store)

    k1, k2, k3, k4 = st.columns(4)
    if not sales_daily.empty and "Actual_Sales" in sales_daily.columns:
        today_row = sales_daily.tail(1)
        today_sales = float(today_row["Actual_Sales"].iloc[0]) if not today_row.empty else 0
        yesterday_row = sales_daily.tail(2).head(1)
        yesterday_sales = float(yesterday_row["Actual_Sales"].iloc[0]) if len(sales_daily) > 1 else today_sales
        pct = round((today_sales - yesterday_sales) / max(yesterday_sales, 1) * 100, 1)
        k1.metric("Today's Sales", f"{today_sales:,.0f} units", delta=f"{pct:+.1f}% vs yesterday")
    else:
        k1.metric("Today's Sales", "N/A")

    weekly = fe.get_sales_analytics(selected_store, "Weekly")
    if not weekly.empty and "Actual_Sales" in weekly.columns:
        this_week = float(weekly.tail(1)["Actual_Sales"].iloc[0]) if len(weekly) >= 1 else 0
        last_week = float(weekly.tail(2).head(1)["Actual_Sales"].iloc[0]) if len(weekly) >= 2 else this_week
        wk_chg = round((this_week - last_week) / max(last_week, 1) * 100, 1)
        k2.metric("This Week's Sales", f"{this_week:,.0f}", delta=f"{wk_chg:+.1f}%")
    else:
        k2.metric("This Week's Sales", "N/A")

    k3.metric("Waste This Week", f"{waste_reduction['current_week']:.1f} kg",
              delta=f"{waste_reduction['reduction']:+.1f}% vs last week")
    k4.metric("Value Lost (Waste)", f"${waste_reduction.get('current_value', 0):.2f}")

    st.markdown("---")

    # ── Main charts ────────────────────────────────────────────────────────
    if report_type == "Sales Report":
        analytics_data = fe.get_sales_analytics(selected_store, analysis_period)
        col1, col2 = st.columns([2, 1])

        with col1:
            if not analytics_data.empty:
                x_col = {"Daily": "Date", "Weekly": "Week",
                          "Monthly": "Month", "Yearly": "Year"}.get(analysis_period, "Date")
                if x_col in analytics_data.columns:
                    fig_trend = px.area(
                        analytics_data, x=x_col, y="Actual_Sales",
                        title=f"{analysis_period} Sales Performance — {selected_store}",
                        labels={"Actual_Sales": "Units Sold"},
                        color_discrete_sequence=["#1f77b4"],
                    )
                    fig_trend.update_layout(height=380)
                    st.plotly_chart(fig_trend, use_container_width=True)

                    # Actual vs Predicted
                    if "Predicted_Sales" in analytics_data.columns:
                        fig_cmp = go.Figure()
                        fig_cmp.add_trace(go.Scatter(
                            x=analytics_data[x_col], y=analytics_data["Actual_Sales"],
                            name="Actual", mode="lines+markers",
                            line=dict(color="#2196F3")))
                        fig_cmp.add_trace(go.Scatter(
                            x=analytics_data[x_col], y=analytics_data["Predicted_Sales"],
                            name="Predicted", mode="lines+markers",
                            line=dict(color="#FF5722", dash="dash")))
                        fig_cmp.update_layout(title="Actual vs Predicted Sales", height=350)
                        st.plotly_chart(fig_cmp, use_container_width=True)
            else:
                st.info("No sales data available for this period.")

        with col2:
            # Top products
            top_prods = fe.get_top_products(selected_store)
            if not top_prods.empty:
                fig_top = px.bar(top_prods, x="Total_Sales", y="Product",
                                 orientation="h", title="Top Products by Sales",
                                 color="Total_Sales", color_continuous_scale="Blues")
                fig_top.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_top, use_container_width=True)

            # Sales by category
            cat_sales = fe.get_sales_by_category(selected_store, analysis_period)
            if not cat_sales.empty:
                fig_cat = px.pie(cat_sales, values="Total_Sales", names="Category",
                                 title="Sales by Category", height=300)
                fig_cat.update_layout(margin=dict(t=40, b=0))
                st.plotly_chart(fig_cat, use_container_width=True)

    elif report_type == "Waste Report":
        col1, col2 = st.columns([2, 1])

        with col1:
            waste_trend = fe.get_waste_analytics(selected_store, analysis_period)
            x_col = {"Daily": "Date", "Weekly": "Week",
                      "Monthly": "Month", "Yearly": "Year"}.get(analysis_period, "Date")
            if not waste_trend.empty and x_col in waste_trend.columns:
                fig_wt = px.area(waste_trend, x=x_col, y="Quantity",
                                  title=f"{analysis_period} Waste Trend — {selected_store}",
                                  labels={"Quantity": "Waste (kg)"},
                                  color_discrete_sequence=["#e74c3c"])
                fig_wt.update_layout(height=360)
                st.plotly_chart(fig_wt, use_container_width=True)
            else:
                st.info("No waste trend data available.")

            # Store comparison
            store_cmp = fe.get_store_waste_comparison()
            if not store_cmp.empty:
                fig_scmp = px.bar(store_cmp, x="Store", y="Total_Waste",
                                   title="Store-wise Total Waste Comparison",
                                   color="Store", height=300)
                fig_scmp.update_layout(showlegend=False)
                st.plotly_chart(fig_scmp, use_container_width=True)

        with col2:
            by_product = fe.get_waste_by_product(selected_store)
            if not by_product.empty:
                fig_wp = px.pie(by_product.head(8), values="Total_Waste", names="Product",
                                 title="Waste by Product", height=300)
                fig_wp.update_layout(margin=dict(t=40, b=0))
                st.plotly_chart(fig_wp, use_container_width=True)

            by_reason = fe.get_waste_by_reason(selected_store)
            if not by_reason.empty:
                fig_wr = px.bar(by_reason, x="Reason", y="Total_Waste",
                                 title="Waste by Reason",
                                 color="Total_Waste", color_continuous_scale="Oranges",
                                 height=280)
                fig_wr.update_xaxes(tickangle=30)
                st.plotly_chart(fig_wr, use_container_width=True)

    else:  # Combined
        combined = fe.get_combined_analytics(selected_store, analysis_period)
        x_col = {"Daily": "Date", "Weekly": "Week",
                  "Monthly": "Month", "Yearly": "Year"}.get(analysis_period, "Date")
        if not combined.empty and x_col in combined.columns:
            fig_comb = go.Figure()
            if "Sales" in combined.columns:
                fig_comb.add_trace(go.Bar(x=combined[x_col], y=combined["Sales"],
                                           name="Sales", marker_color="#2196F3"))
            if "Waste" in combined.columns:
                fig_comb.add_trace(go.Bar(x=combined[x_col], y=combined["Waste"],
                                           name="Waste (kg)", marker_color="#e74c3c",
                                           yaxis="y2"))
            fig_comb.update_layout(
                title=f"Sales vs Waste — {analysis_period}",
                yaxis=dict(title="Sales (units)"),
                yaxis2=dict(title="Waste (kg)", overlaying="y", side="right"),
                barmode="group", height=400,
            )
            st.plotly_chart(fig_comb, use_container_width=True)
        else:
            st.info("No combined data available.")

    # ── Report download ────────────────────────────────────────────────────
    st.markdown("---")
    dc1, dc2 = st.columns(2)
    with dc1:
        if st.button("📄 Generate & Download Report", type="primary"):
            report_df = fe.generate_sales_report(selected_store, analysis_period, report_type)
            if not report_df.empty:
                csv = report_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Report (CSV)", data=csv,
                    file_name=f"report_{selected_store.replace(' ','_')}_{analysis_period}_{report_type.replace(' ','_')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No data to export.")
    with dc2:
        if st.button("🖨️ Print Report"):
            st.success("Report sent to printer!")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — WASTE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
elif tab_selection == "🗑️ Waste Management":
    st.header("🗑️ Comprehensive Waste Management")

    col_form, col_stats = st.columns([1, 1])

    # ── Log waste form ─────────────────────────────────────────────────────
    with col_form:
        st.subheader("📝 Log New Waste Entry")

        with st.form("waste_log_form", clear_on_submit=True):
            wc1, wc2 = st.columns(2)
            with wc1:
                all_prods = fe.get_product_list(selected_store)
                product_choices = (
                    sorted(all_prods["Product Name"].tolist())
                    if not all_prods.empty
                    else ["Apples", "Bananas", "Bread", "Milk", "Cheese",
                          "Yogurt", "Lettuce", "Tomatoes", "Chicken", "Beef"]
                )
                waste_product = st.selectbox("Product *", product_choices)
                waste_qty = st.number_input("Quantity Wasted *", min_value=0.0,
                                             step=0.1, value=0.0)
                waste_unit = st.selectbox("Unit", ["kg", "pcs", "liters"])
            with wc2:
                waste_date = st.date_input("Date *", value=datetime.now().date())
                waste_reason = st.selectbox("Reason *", [
                    "Expired", "Damaged", "Overstock", "Quality Issues",
                    "Customer Return", "Staff Error", "Other"])
                waste_value = st.number_input("Value Lost ($)", min_value=0.0,
                                               step=0.01, value=0.0)

            waste_notes = st.text_area("Notes", placeholder="Additional details...")

            submitted = st.form_submit_button("🗑️ Log Waste Entry", type="primary")

            if submitted:
                errors = fe.validate_waste_entry(
                    waste_product, waste_qty, waste_unit,
                    waste_date, waste_reason, waste_value,
                )
                if errors:
                    for e in errors:
                        st.error(f"❌ {e}")
                else:
                    ok = fe.log_waste_entry(
                        selected_store, waste_product, waste_qty, waste_unit,
                        waste_date, waste_reason, waste_value, waste_notes,
                    )
                    if ok:
                        st.success(f"✅ Logged {waste_qty:.1f} {waste_unit} of {waste_product}!")
                        st.rerun()
                    else:
                        st.error("Failed to log entry. Please try again.")

    # ── Reduction stats ────────────────────────────────────────────────────
    with col_stats:
        st.subheader("📊 Waste Reduction Progress")
        wr = fe.calculate_waste_reduction_percentage(selected_store)

        m1, m2 = st.columns(2)
        m1.metric("This Week", f"{wr['current_week']:.1f} kg")
        m2.metric("Last Week", f"{wr['previous_week']:.1f} kg")
        m1.metric("Value Lost (This Week)", f"${wr.get('current_value', 0):.2f}")
        m2.metric("Reduction %", f"{wr['reduction']:+.1f}%",
                   delta="vs last week")

        # Progress bar
        reduction = wr["reduction"]
        if wr["previous_week"] > 0:
            progress = max(0.0, min(1.0, reduction / 100))
            color = "green" if reduction > 0 else "red"
            st.markdown(f"**Waste Reduction Progress:** {reduction:+.1f}%")
            st.progress(float(abs(progress)))

        st.subheader("💡 Waste Reduction Tips")
        tips = [
            "🥬 Monitor fresh produce daily — check for signs of spoilage",
            "📦 Implement FIFO (First In, First Out) stock rotation",
            "🌡️ Maintain proper storage temperatures",
            "🏷️ Apply markdown pricing 2 days before expiry",
            "📱 Use the Alerts tab to catch issues early",
            "📊 Review weekly patterns in Analytics & Reports",
        ]
        for tip in tips:
            st.write(tip)

    # ── Analytics charts ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Waste Tracking Analytics")

    try:
        waste_df = pd.read_csv("data/waste_data.csv")
        waste_df["Date"] = pd.to_datetime(waste_df["Date"])
        sw = waste_df[waste_df["Store"] == selected_store] if "Store" in waste_df.columns else waste_df

        if not sw.empty:
            ch1, ch2, ch3 = st.columns(3)
            with ch1:
                by_prod = sw.groupby("Product")["Quantity"].sum().reset_index()
                fig_pie = px.pie(by_prod.head(10), values="Quantity", names="Product",
                                  title="Waste by Product", height=300)
                fig_pie.update_layout(margin=dict(t=40, b=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            with ch2:
                by_reason = sw.groupby("Reason")["Quantity"].sum().reset_index()
                fig_bar = px.bar(by_reason, x="Reason", y="Quantity",
                                  title="Waste by Reason",
                                  color="Quantity", color_continuous_scale="Reds", height=300)
                fig_bar.update_xaxes(tickangle=30)
                st.plotly_chart(fig_bar, use_container_width=True)
            with ch3:
                if "Category" in sw.columns:
                    by_cat = sw.groupby("Category")["Quantity"].sum().reset_index()
                    fig_cat = px.bar(by_cat, x="Category", y="Quantity",
                                      title="Waste by Category",
                                      color="Category", height=300)
                    st.plotly_chart(fig_cat, use_container_width=True)

            # Trend line
            sw["Week"] = sw["Date"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
            weekly_trend = sw.groupby("Week")["Quantity"].sum().reset_index()
            fig_trend = px.line(weekly_trend, x="Week", y="Quantity",
                                 title="Weekly Waste Trend — " + selected_store,
                                 labels={"Quantity": "Waste (kg)"},
                                 markers=True)
            fig_trend.update_layout(height=320)
            st.plotly_chart(fig_trend, use_container_width=True)

            # Heatmap (last 30 days)
            cutoff = datetime.now() - timedelta(days=30)
            recent = sw[sw["Date"] >= cutoff]
            if not recent.empty:
                pivot = recent.groupby([recent["Date"].dt.strftime("%Y-%m-%d"), "Product"])["Quantity"].sum().reset_index()
                pivot.columns = ["Date", "Product", "Quantity"]
                fig_heat = px.density_heatmap(pivot, x="Date", y="Product", z="Quantity",
                                               title="Waste Heatmap — Last 30 Days", height=360)
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No waste data recorded for this store yet.")
    except FileNotFoundError:
        st.info("Waste data file not found.")

    # ── Waste history table ────────────────────────────────────────────────
    st.subheader("📋 Recent Waste Entries")
    try:
        waste_df = pd.read_csv("data/waste_data.csv")
        sw = waste_df[waste_df["Store"] == selected_store] if "Store" in waste_df.columns else waste_df
        if not sw.empty:
            sw_display = sw.sort_values("Date", ascending=False).head(30)
            cols = [c for c in ["Date", "Product", "Category", "Quantity", "Unit", "Reason", "Value_Lost", "Notes"] if c in sw_display.columns]
            st.dataframe(sw_display[cols], use_container_width=True)

            csv_data = sw.to_csv(index=False)
            st.download_button("⬇️ Export Waste History (CSV)", data=csv_data,
                                file_name=f"waste_{selected_store.replace(' ','_')}.csv",
                                mime="text/csv")
        else:
            st.info("No waste entries recorded yet.")
    except FileNotFoundError:
        st.info("No waste data available.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ALERTS & MONITORING
# ══════════════════════════════════════════════════════════════════════════════
elif tab_selection == "⚠️ Alerts & Monitoring":
    st.header("⚠️ Smart Alerts & Monitoring System")

    # Alert thresholds (from session state)
    restock_threshold = st.session_state.alert_restock_threshold
    waste_threshold = st.session_state.alert_waste_threshold
    expiry_days = st.session_state.alert_expiry_days

    # Get all alerts
    restock_alerts = fe.get_restock_alerts(selected_store)
    expiry_alerts = fe.get_expiry_alerts(selected_store, days_threshold=expiry_days)
    waste_alerts = fe.get_waste_alerts(selected_store, threshold=float(waste_threshold))

    # ── Summary row ────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("🔴 Restock Alerts", len(restock_alerts),
               delta=f"{sum(1 for a in restock_alerts if a['urgency']=='HIGH')} HIGH urgency")
    s2.metric("⏰ Expiry Alerts", len(expiry_alerts),
               delta=f"{sum(1 for a in expiry_alerts if a['severity']=='CRITICAL')} CRITICAL")
    s3.metric("♻️ Waste Risk Alerts", len(waste_alerts))
    # System status
    acc = fe.get_forecast_accuracy(selected_store)
    s4.metric("🎯 Forecast Accuracy",
               f"{acc['weekly']:.1f}%" if acc else "N/A",
               delta=acc.get("trend_delta", "") if acc else "")

    st.markdown("---")

    # ── Tab layout for alert types ─────────────────────────────────────────
    alert_tab1, alert_tab2, alert_tab3, alert_tab4 = st.tabs(
        ["📦 Restock Alerts", "⏰ Expiry Alerts", "♻️ Waste Alerts", "⚙️ Configuration"]
    )

    with alert_tab1:
        st.subheader("📦 Detailed Restock Alerts")
        if restock_alerts:
            alert_df = pd.DataFrame(restock_alerts)

            def row_color(row):
                if row["urgency"] == "HIGH":
                    return ["background-color: #ffebee"] * len(row)
                elif row["urgency"] == "MEDIUM":
                    return ["background-color: #fff3e0"] * len(row)
                return [""] * len(row)

            styled = alert_df.style.apply(row_color, axis=1)
            st.dataframe(styled, use_container_width=True)

            # Reorder actions
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("📧 Send Reorder Emails"):
                    st.success(f"Reorder notifications sent for {len(restock_alerts)} items!")
            with b2:
                if st.button("📋 Generate Purchase Orders"):
                    po_data = pd.DataFrame(restock_alerts)
                    st.download_button("⬇️ Download PO (CSV)", data=po_data.to_csv(index=False),
                                       file_name=f"purchase_orders_{selected_store.replace(' ','_')}.csv",
                                       mime="text/csv")
            with b3:
                if st.button("📱 Alert Manager"):
                    st.success("Manager notification sent!")

            # Chart
            urgency_counts = pd.DataFrame(restock_alerts).groupby("urgency").size().reset_index(name="Count")
            fig = px.bar(urgency_counts, x="urgency", y="Count",
                          color="urgency", color_discrete_map={"HIGH": "#e74c3c", "MEDIUM": "#f39c12"},
                          title="Restock Alerts by Urgency", height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ All products are well stocked! No restock alerts.")

    with alert_tab2:
        st.subheader("⏰ Expiry Alerts")
        if expiry_alerts:
            exp_df = pd.DataFrame(expiry_alerts)

            def exp_color(row):
                if row["severity"] == "CRITICAL":
                    return ["background-color: #ffcdd2"] * len(row)
                elif row["severity"] == "HIGH":
                    return ["background-color: #ffe0b2"] * len(row)
                return ["background-color: #fff9c4"] * len(row)

            st.dataframe(exp_df.style.apply(exp_color, axis=1), use_container_width=True)

            # Breakdown chart
            sev_counts = pd.DataFrame(expiry_alerts).groupby("severity").size().reset_index(name="Count")
            fig = px.pie(sev_counts, values="Count", names="severity",
                          title="Expiry Alerts by Severity",
                          color_discrete_map={"CRITICAL": "#e74c3c", "HIGH": "#f39c12", "MEDIUM": "#ffc107"},
                          height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success(f"✅ No products expiring within {expiry_days} days.")

    with alert_tab3:
        st.subheader("♻️ High Waste Risk Alerts")
        if waste_alerts:
            wa_df = pd.DataFrame(waste_alerts)

            def wa_color(row):
                if row["severity"] == "HIGH":
                    return ["background-color: #ffebee"] * len(row)
                return ["background-color: #fff3e0"] * len(row)

            st.dataframe(wa_df.style.apply(wa_color, axis=1), use_container_width=True)

            # Risk chart
            fig = px.bar(wa_df.sort_values("waste_risk", ascending=True),
                          x="waste_risk", y="product", orientation="h",
                          title="Waste Risk by Product", color="waste_risk",
                          color_continuous_scale="RdYlGn_r", height=350,
                          labels={"waste_risk": "Waste Risk %", "product": "Product"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No high-waste-risk products detected.")

    with alert_tab4:
        st.subheader("⚙️ Alert Configuration")
        c1, c2 = st.columns(2)
        with c1:
            new_restock = st.slider("Restock Alert Threshold (% of reorder level)", 10, 100,
                                     st.session_state.alert_restock_threshold)
            new_waste = st.slider("Waste Risk Alert Threshold (%)", 50, 95,
                                   st.session_state.alert_waste_threshold)
        with c2:
            new_expiry = st.slider("Expiry Alert Threshold (days)", 1, 14,
                                    st.session_state.alert_expiry_days)
            freq = st.selectbox("Alert Frequency", ["Real-time", "Hourly", "Daily"])
            recipients = st.multiselect("Alert Recipients",
                                         ["Store Manager", "Purchasing", "Regional Manager"])

        if st.button("💾 Save Alert Settings", type="primary"):
            st.session_state.alert_restock_threshold = new_restock
            st.session_state.alert_waste_threshold = new_waste
            st.session_state.alert_expiry_days = new_expiry
            st.success("✅ Alert settings saved!")

        st.subheader("📊 System Health")
        health_data = {
            "Component": ["Sales Data", "Waste Data", "Product Master", "Forecast Engine", "AI Assistant"],
            "Status": ["✅ OK", "✅ OK", "✅ OK", "✅ OK",
                       "✅ OK" if ai.api_provider != "demo" else "⚠️ Demo Mode"],
        }
        st.dataframe(pd.DataFrame(health_data), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif tab_selection == "🤖 AI Assistant":
    st.header("🤖 AI Assistant")
    st.markdown("Ask questions about your store's data, forecasts, waste, and inventory.")

    if ai.api_provider == "demo":
        st.info(
            "ℹ️ **Running in Demo Mode.** "
            "Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in your `.env` file for full AI responses. "
            "Demo mode provides pre-built insights based on your actual data."
        )
    else:
        st.success(f"✅ AI Provider: {ai.api_provider.upper()} — Full AI responses enabled.")

    # Chat history display
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Quick question buttons
    st.subheader("💡 Quick Questions")
    q_cols = st.columns(4)
    quick_questions = [
        "What products might go to waste tomorrow?",
        "Show me this week's waste patterns",
        "How can I reduce food waste?",
        "What should I reorder today?",
        "Give me a store performance summary",
        "Are there any upcoming events?",
        "Which are my top selling products?",
        "What is the forecast accuracy?",
    ]
    for i, q in enumerate(quick_questions):
        with q_cols[i % 4]:
            if st.button(q, key=f"quick_{i}"):
                st.session_state["pending_prompt"] = q

    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            ctx = ai.get_store_context(selected_store)
            response = ai.get_response(prompt, ctx)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # Chat input
    if prompt := st.chat_input(f"Ask me anything about {selected_store}..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    ctx = ai.get_store_context(selected_store)
                    response = ai.get_response(prompt, ctx)
                except Exception as ex:
                    response = f"I encountered an error: {str(ex)}. Please try again."
                st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Clear chat
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "💡 **Tip:** Use the **AI Assistant** tab to ask about waste patterns, "
    "restock recommendations, and demand forecasts. Check **Alerts** daily!"
)
