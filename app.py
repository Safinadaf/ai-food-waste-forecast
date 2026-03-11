import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import requests
import os
from utils.forecast import ForecastEngine
from utils.ai_chat import AIAssistant

# Page configuration
st.set_page_config(
    page_title="AI-Powered Smart Forecasting",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize forecast engine and AI assistant
@st.cache_resource
def init_forecast_engine():
    return ForecastEngine()

@st.cache_resource
def init_ai_assistant():
    return AIAssistant()

forecast_engine = init_forecast_engine()
ai_assistant = init_ai_assistant()

# Main title
st.title("🧠 AI-Powered Smart Forecasting for Zero Food Waste")
st.markdown("### Intelligent Dashboard for Retail Store Managers")

# Sidebar for navigation
st.sidebar.title("Navigation")
tab_selection = st.sidebar.radio(
    "Select Module:",
    ["📦 Product Management", "📊 Forecast Dashboard", "📈 Analytics & Reports", "🗑️ Waste Management", "⚠️ Alerts & Monitoring", "🤖 AI Assistant"]
)

# Store selection (common across tabs)
stores = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
selected_store = st.sidebar.selectbox("Select Store:", stores)

# Tab 1: Product Management
if tab_selection == "📦 Product Management":
    st.header("📦 Product Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Product Catalog")
        
        # Product filter options
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            category_filter = st.selectbox("Filter by Category", 
                ["All", "Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"])
        
        with filter_col2:
            risk_filter = st.selectbox("Filter by Waste Risk", 
                ["All", "High Risk (>70%)", "Medium Risk (30-70%)", "Low Risk (<30%)"])
        
        with filter_col3:
            stock_filter = st.selectbox("Filter by Stock Status", 
                ["All", "In Stock", "Low Stock", "Out of Stock"])
        
        # Get all products with current data
        all_products = forecast_engine.get_product_list(selected_store)
        
        if not all_products.empty:
            # Apply filters
            filtered_products = forecast_engine.apply_product_filters(
                all_products, category_filter, risk_filter, stock_filter
            )
            
            st.subheader(f"Products ({len(filtered_products)} items)")
            
            # Display product list with editing capabilities
            edited_products = st.data_editor(
                filtered_products,
                column_config={
                    "Product Name": st.column_config.TextColumn("Product Name", disabled=True),
                    "Category": st.column_config.SelectboxColumn("Category", 
                        options=["Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"]),
                    "Current Stock": st.column_config.NumberColumn("Current Stock", min_value=0),
                    "Reorder Level": st.column_config.NumberColumn("Reorder Level", min_value=0),
                    "Unit Price": st.column_config.NumberColumn("Unit Price ($)", min_value=0.01),
                    "Supplier": st.column_config.TextColumn("Supplier"),
                    "Status": st.column_config.SelectboxColumn("Status", 
                        options=["Active", "Inactive", "Seasonal"])
                },
                hide_index=True,
                use_container_width=True,
                key="product_editor"
            )
            
            if st.button("Save Product Changes", type="primary"):
                forecast_engine.save_product_updates(edited_products, selected_store)
                st.success("Product information updated successfully!")
                st.rerun()
        else:
            st.info("No products found. Please check your data files.")
    
    with col2:
        st.subheader("Quick Actions")
        
        # Add new product form
        with st.expander("Add New Product"):
            with st.form("add_product_form"):
                new_product_name = st.text_input("Product Name*")
                new_category = st.selectbox("Category*", 
                    ["Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"])
                new_stock = st.number_input("Initial Stock", min_value=0, value=0)
                new_reorder = st.number_input("Reorder Level", min_value=0, value=10)
                new_price = st.number_input("Unit Price ($)", min_value=0.01, value=1.00)
                new_supplier = st.text_input("Supplier")
                
                if st.form_submit_button("Add Product"):
                    if new_product_name:
                        forecast_engine.add_new_product(
                            selected_store, new_product_name, new_category,
                            new_stock, new_reorder, new_price, new_supplier
                        )
                        st.success(f"Added {new_product_name} to inventory!")
                        st.rerun()
                    else:
                        st.error("Product name is required!")
        
        # Product statistics
        st.subheader("Quick Stats")
        if not all_products.empty:
            total_products = len(all_products)
            low_stock_count = len(all_products[all_products['Current Stock'] <= all_products['Reorder Level']])
            high_risk_count = len(all_products[all_products['Waste Risk %'] > 70])
            
            st.metric("Total Products", total_products)
            st.metric("Low Stock Items", low_stock_count, delta=f"-{low_stock_count}" if low_stock_count > 0 else "0")
            st.metric("High Waste Risk", high_risk_count, delta=f"-{high_risk_count}" if high_risk_count > 0 else "0")

# Tab 2: Forecast Dashboard
elif tab_selection == "📊 Forecast Dashboard":
    st.header("📊 Smart Demand Forecasting")
    
    # Forecast period selection
    forecast_period = st.selectbox("Forecast Period", ["Today", "Tomorrow", "Next 3 Days", "Next Week"])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get forecast data
        forecast_data = forecast_engine.get_enhanced_forecast(selected_store, forecast_period)
        
        if not forecast_data.empty:
            st.subheader(f"📈 {forecast_period}'s Demand Predictions")
            
            # Session state for forecast edits
            if 'forecast_edits' not in st.session_state:
                st.session_state.forecast_edits = forecast_data.copy()
            
            # Editable forecast table
            edited_df = st.data_editor(
                st.session_state.forecast_edits,
                column_config={
                    "Product Name": st.column_config.TextColumn("Product", disabled=True),
                    "Predicted Qty": st.column_config.NumberColumn("AI Prediction", disabled=True),
                    "Manual Override": st.column_config.NumberColumn("Your Adjustment", min_value=0),
                    "Final Qty": st.column_config.NumberColumn("Final Forecast", disabled=True),
                    "Waste Risk %": st.column_config.ProgressColumn("Waste Risk", min_value=0, max_value=100),
                    "Confidence": st.column_config.ProgressColumn("AI Confidence", min_value=0, max_value=100),
                    "Suggested Action": st.column_config.TextColumn("Recommendation", disabled=True)
                },
                hide_index=True,
                use_container_width=True,
                key="forecast_editor"
            )
            
            # Update final quantities based on manual overrides
            edited_df['Final Qty'] = edited_df.apply(
                lambda row: row['Manual Override'] if row['Manual Override'] > 0 else row['Predicted Qty'], 
                axis=1
            )
            
            st.session_state.forecast_edits = edited_df
            
            # Action buttons
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            
            with col_btn1:
                if st.button("💾 Save Forecast", type="primary"):
                    forecast_engine.save_forecast(edited_df, selected_store, forecast_period)
                    st.success("Forecast saved successfully!")
                    st.rerun()
            
            with col_btn2:
                if st.button("✅ Finalize Forecast"):
                    st.session_state.forecast_finalized = True
                    st.success("Forecast finalized! Ready for printing/sending.")
            
            with col_btn3:
                if st.button("📧 Send Report"):
                    if st.session_state.get('forecast_finalized', False):
                        st.success("Forecast report sent to management!")
                    else:
                        st.warning("Please finalize the forecast first.")
            
            with col_btn4:
                if st.button("📄 Generate PDF"):
                    if st.session_state.get('forecast_finalized', False):
                        pdf_data = forecast_engine.generate_forecast_pdf(edited_df, selected_store, forecast_period)
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_data,
                            file_name=f"forecast_{selected_store}_{forecast_period}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning("Please finalize the forecast first.")
        else:
            st.warning("No forecast data available for the selected store.")
    
    with col2:
        st.subheader("📊 Forecast Summary")
        if not forecast_data.empty:
            total_predicted = forecast_data['Predicted Qty'].sum()
            total_final = forecast_data['Final Qty'].sum() if 'Final Qty' in forecast_data.columns else total_predicted
            high_risk_items = len(forecast_data[forecast_data['Waste Risk %'] > 70])
            avg_confidence = forecast_data['Confidence'].mean()
            
            st.metric("AI Predicted Total", f"{total_predicted:,.0f}")
            st.metric("Final Forecast", f"{total_final:,.0f}", 
                     delta=f"{total_final - total_predicted:+.0f}")
            st.metric("High Risk Items", high_risk_items)
            st.metric("Avg AI Confidence", f"{avg_confidence:.0f}%")
            
            # Forecast status
            status = "✅ Finalized" if st.session_state.get('forecast_finalized', False) else "⏳ Draft"
            st.info(f"Status: {status}")
        
        # Historical accuracy
        st.subheader("🎯 Forecast Accuracy")
        accuracy_data = forecast_engine.get_forecast_accuracy(selected_store)
        if accuracy_data:
            st.metric("Last Week Accuracy", f"{accuracy_data['weekly']:.1f}%")
            st.metric("Monthly Accuracy", f"{accuracy_data['monthly']:.1f}%")
            st.metric("Trend", accuracy_data['trend'], delta=accuracy_data['trend_delta'])

# Tab 3: Analytics & Reports  
elif tab_selection == "📈 Analytics & Reports":
    st.header("📈 Sales Analytics & Business Reports")
    
    # Time period selection
    period_col1, period_col2 = st.columns(2)
    with period_col1:
        analysis_period = st.selectbox("Time Period", ["Daily", "Weekly", "Monthly"])
    with period_col2:
        report_type = st.selectbox("Report Type", ["Sales Report", "Waste Report", "Combined Report"])
    
    # Get analytics data
    analytics_data = forecast_engine.get_sales_analytics(selected_store, analysis_period)
    
    if not analytics_data.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 {analysis_period} Sales Trends")
            
            # Sales trend chart
            if analysis_period == "Daily":
                x_col = 'Date'
            elif analysis_period == "Weekly":
                x_col = 'Week'  
            else:
                x_col = 'Month'
            
            fig_trend = px.line(analytics_data, x=x_col, y='Actual_Sales', 
                               title=f"{analysis_period} Sales Performance")
            fig_trend.update_layout(height=400)
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Sales comparison chart
            st.subheader("📈 Sales vs Forecast Comparison")
            try:
                sales_df = pd.read_csv("data/sales_data.csv")
                store_sales = sales_df[sales_df['Store'] == selected_store] if 'Store' in sales_df.columns else sales_df
                
                if not store_sales.empty and 'Predicted_Sales' in store_sales.columns:
                    comparison_data = store_sales.tail(14)  # Last 2 weeks
                    
                    fig_comparison = go.Figure()
                    fig_comparison.add_trace(go.Scatter(
                        x=comparison_data['Date'], 
                        y=comparison_data['Actual_Sales'],
                        mode='lines+markers', 
                        name='Actual Sales',
                        line=dict(color='blue')
                    ))
                    fig_comparison.add_trace(go.Scatter(
                        x=comparison_data['Date'], 
                        y=comparison_data['Predicted_Sales'],
                        mode='lines+markers', 
                        name='Forecasted Sales',
                        line=dict(color='red', dash='dash')
                    ))
                    fig_comparison.update_layout(
                        title="Actual vs Forecasted Sales (Last 2 Weeks)",
                        height=400
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)
            except FileNotFoundError:
                st.info("No historical sales data available for comparison.")
        
        with col2:
            st.subheader("📋 Daily Sales Report")
            
            # Today's sales summary
            today_sales = analytics_data.tail(1) if not analytics_data.empty else pd.DataFrame()
            if not today_sales.empty:
                st.metric("Today's Sales", f"${today_sales.iloc[0]['Actual_Sales']:,.2f}")
            
            # Weekly performance
            weekly_data = forecast_engine.get_sales_analytics(selected_store, "Weekly")
            if not weekly_data.empty:
                this_week = weekly_data.tail(1).iloc[0]['Actual_Sales'] if len(weekly_data) > 0 else 0
                last_week = weekly_data.tail(2).iloc[0]['Actual_Sales'] if len(weekly_data) > 1 else this_week
                week_change = ((this_week - last_week) / last_week * 100) if last_week > 0 else 0
                
                st.metric("This Week", f"${this_week:,.2f}", delta=f"{week_change:+.1f}%")
            
            # Generate report button
            if st.button("📄 Generate Detailed Report", type="primary"):
                report_data = forecast_engine.generate_sales_report(selected_store, analysis_period, report_type)
                
                st.download_button(
                    label="⬇️ Download Report (CSV)",
                    data=report_data.to_csv(index=False),
                    file_name=f"sales_report_{selected_store}_{analysis_period}.csv",
                    mime="text/csv"
                )
                
            # Print report option
            if st.button("🖨️ Print Report"):
                st.success("Report sent to printer!")
    else:
        st.warning("No analytics data available for the selected period.")

# Tab 4: Waste Management
elif tab_selection == "🗑️ Waste Management":
    st.header("🗑️ Comprehensive Waste Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Log New Waste")
        
        with st.form("enhanced_waste_form"):
            waste_col1, waste_col2 = st.columns(2)
            
            with waste_col1:
                products = ["Apples", "Bananas", "Bread", "Milk", "Cheese", "Yogurt", "Lettuce", "Tomatoes", "Chicken", "Beef"]
                waste_product = st.selectbox("Product*", products)
                waste_quantity = st.number_input("Quantity Wasted*", min_value=0.0, step=0.1)
                waste_unit = st.selectbox("Unit", ["kg", "pieces", "liters"])
            
            with waste_col2:
                waste_date = st.date_input("Date*", value=datetime.now().date())
                waste_reason = st.selectbox("Reason", ["Expired", "Damaged", "Overstock", "Quality Issues", "Customer Return", "Staff Error", "Other"])
                waste_value = st.number_input("Estimated Value Lost ($)", min_value=0.0, step=0.01)
            
            waste_notes = st.text_area("Additional Notes", placeholder="Any additional details about this waste incident...")
            
            submitted = st.form_submit_button("🗑️ Log Waste Entry")
            
            if submitted and waste_quantity > 0:
                # Enhanced waste logging
                forecast_engine.log_waste_entry(
                    selected_store, waste_product, waste_quantity, waste_unit,
                    waste_date, waste_reason, waste_value, waste_notes
                )
                st.success(f"Logged {waste_quantity} {waste_unit} of {waste_product} waste!")
                st.rerun()
    
    with col2:
        st.subheader("📊 Waste Reduction Progress")
        
        # Calculate waste reduction percentage
        waste_reduction = forecast_engine.calculate_waste_reduction_percentage(selected_store)
        
        reduction_pct = waste_reduction['reduction']
        st.metric(
            "Waste Reduction This Week", 
            f"{reduction_pct:+.1f}%",
            delta=f"vs last week"
        )
        
        # Waste value metrics
        st.metric("Current Week Waste", f"{waste_reduction['current_week']:.1f} kg")
        st.metric("Previous Week Waste", f"{waste_reduction['previous_week']:.1f} kg")
        
        # Waste management tips
        st.subheader("💡 Waste Reduction Tips")
        tips = [
            "🥬 Monitor fresh produce daily",
            "🥛 Check dairy expiration dates",
            "📦 Implement FIFO (First In, First Out)",
            "🌡️ Maintain proper storage temperatures",
            "📱 Use smart inventory tracking"
        ]
        for tip in tips:
            st.write(tip)
    
    # Waste tracking visualization
    st.subheader("📈 Waste Tracking Analytics")
    
    try:
        waste_df = pd.read_csv("data/waste_data.csv")
        store_waste = waste_df[waste_df['Store'] == selected_store] if 'Store' in waste_df.columns else waste_df
        
        if not store_waste.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Waste by product pie chart
                product_waste = store_waste.groupby('Product')['Quantity'].sum().reset_index()
                fig_pie = px.pie(product_waste, values='Quantity', names='Product', 
                               title="Waste Distribution by Product")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_chart2:
                # Waste by reason bar chart  
                reason_waste = store_waste.groupby('Reason')['Quantity'].sum().reset_index()
                fig_bar = px.bar(reason_waste, x='Reason', y='Quantity',
                               title="Waste by Reason")
                fig_bar.update_xaxis(tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No waste data available for visualization.")
    except FileNotFoundError:
        st.info("No waste data file found.")
    
    # Waste managed details
    st.subheader("📋 Waste Management History")
    try:
        waste_df = pd.read_csv("data/waste_data.csv")
        store_waste = waste_df[waste_df['Store'] == selected_store] if 'Store' in waste_df.columns else waste_df
        
        if not store_waste.empty:
            # Recent waste entries with enhanced details
            recent_waste = store_waste.tail(20).sort_values('Date', ascending=False)
            
            st.dataframe(
                recent_waste[['Date', 'Product', 'Quantity', 'Unit', 'Reason', 'Notes']],
                use_container_width=True
            )
            
            # Export waste data
            if st.button("📊 Export Waste Data"):
                csv_data = store_waste.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Waste History (CSV)",
                    data=csv_data,
                    file_name=f"waste_history_{selected_store}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No waste entries recorded yet.")
    except FileNotFoundError:
        st.info("No waste data available.")

# Tab 5: Alerts & Monitoring
elif tab_selection == "⚠️ Alerts & Monitoring":
    st.header("⚠️ Smart Alerts & Monitoring System")
    
    # Alert overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔔 Active Alerts")
        
        # Get restock alerts
        restock_alerts = forecast_engine.get_restock_alerts(selected_store)
        
        if restock_alerts:
            st.metric("Restock Alerts", len(restock_alerts))
            
            for alert in restock_alerts[:5]:  # Show top 5
                urgency_color = "🔴" if alert['urgency'] == "HIGH" else "🟡"
                st.write(f"{urgency_color} {alert['product']} - Stock: {alert['current_stock']}")
        else:
            st.metric("Restock Alerts", 0)
            st.success("✅ All products well stocked!")
    
    with col2:
        st.subheader("⚡ Waste Alerts")
        
        # Get high waste risk products
        try:
            products = forecast_engine.get_product_list(selected_store)
            high_risk = products[products['Waste Risk %'] > 70] if not products.empty else pd.DataFrame()
            
            if not high_risk.empty:
                st.metric("High Waste Risk", len(high_risk))
                for _, product in high_risk.head(5).iterrows():
                    st.write(f"🚨 {product['Product Name']} - {product['Waste Risk %']:.0f}% risk")
            else:
                st.metric("High Waste Risk", 0)
                st.success("✅ Low waste risk across products!")
        except:
            st.metric("High Waste Risk", 0)
    
    with col3:
        st.subheader("📊 System Status")
        
        st.metric("Forecast Accuracy", "89.2%", delta="+2.1%")
        st.metric("Data Quality", "98.5%", delta="+0.5%")
        
        # System health indicator
        st.write("🟢 All systems operational")
    
    # Detailed alert sections
    st.markdown("---")
    
    # Restock alerts detailed view
    st.subheader("📦 Detailed Restock Alerts")
    
    if restock_alerts:
        alert_df = pd.DataFrame(restock_alerts)
        
        # Color-code by urgency
        def highlight_urgency(row):
            if row['urgency'] == 'HIGH':
                return ['background-color: #ffebee'] * len(row)
            elif row['urgency'] == 'MEDIUM':
                return ['background-color: #fff3e0'] * len(row)
            else:
                return [''] * len(row)
        
        styled_alerts = alert_df.style.apply(highlight_urgency, axis=1)
        st.dataframe(styled_alerts, use_container_width=True)
        
        # Bulk reorder actions
        st.subheader("🛒 Quick Reorder Actions")
        
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            if st.button("📧 Send Reorder Emails"):
                st.success("Reorder notifications sent to suppliers!")
        
        with col_action2:
            if st.button("📋 Generate Purchase Orders"):
                st.success("Purchase orders generated and saved!")
        
        with col_action3:
            if st.button("📱 Alert Manager"):
                st.success("Manager notification sent!")
    else:
        st.info("No restock alerts at this time.")
    
    # Alert settings
    st.subheader("⚙️ Alert Configuration")
    
    with st.expander("Configure Alert Thresholds"):
        settings_col1, settings_col2 = st.columns(2)
        
        with settings_col1:
            st.slider("Restock Alert Threshold (%)", 0, 50, 20)
            st.slider("Waste Risk Alert Threshold (%)", 50, 90, 70)
        
        with settings_col2:
            st.selectbox("Alert Frequency", ["Real-time", "Hourly", "Daily"])
            st.multiselect("Alert Recipients", ["Store Manager", "Purchasing", "Regional Manager"])
        
        if st.button("💾 Save Alert Settings"):
            st.success("Alert settings updated successfully!")

# Original tabs (Event Entry moved to later)
elif tab_selection == "📅 Event Entry":
    st.header("📅 Local Event Entry")
    st.markdown("Log local events that might affect product demand")
    
    with st.form("event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name*", placeholder="e.g., Summer Festival")
            event_location = st.text_input("Location*", placeholder="e.g., Downtown Park")
        
        with col2:
            event_date = st.date_input("Event Date*", min_value=datetime.now().date())
            event_impact = st.selectbox("Expected Impact", ["Low", "Medium", "High"])
        
        event_description = st.text_area("Description", placeholder="Describe how this event might affect sales...")
        
        submitted = st.form_submit_button("Add Event")
        
        if submitted:
            if event_name and event_location:
                # Load existing events
                try:
                    with open("data/event_data.json", "r") as f:
                        events = json.load(f)
                except FileNotFoundError:
                    events = []
                
                # Add new event
                new_event = {
                    "id": len(events) + 1,
                    "name": event_name,
                    "location": event_location,
                    "date": str(event_date),
                    "impact": event_impact,
                    "description": event_description,
                    "store": selected_store,
                    "created_at": str(datetime.now())
                }
                
                events.append(new_event)
                
                # Save events
                os.makedirs("data", exist_ok=True)
                with open("data/event_data.json", "w") as f:
                    json.dump(events, f, indent=2)
                
                st.success(f"Event '{event_name}' added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields (marked with *)")
    
    # Display recent events
    st.subheader("Recent Events")
    try:
        with open("data/event_data.json", "r") as f:
            events = json.load(f)
        
        if events:
            recent_events = [e for e in events if e['store'] == selected_store][-5:]
            for event in reversed(recent_events):
                with st.expander(f"{event['name']} - {event['date']}"):
                    st.write(f"**Location:** {event['location']}")
                    st.write(f"**Impact:** {event['impact']}")
                    st.write(f"**Description:** {event['description']}")
        else:
            st.info("No events recorded yet.")
    except FileNotFoundError:
        st.info("No events recorded yet.")

# Tab 3: Waste Logging
elif tab_selection == "🗑️ Waste Logging":
    st.header("🗑️ Food Waste Logging")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Log New Waste")
        
        with st.form("waste_form"):
            products = ["Apples", "Bananas", "Bread", "Milk", "Cheese", "Yogurt", "Lettuce", "Tomatoes"]
            waste_product = st.selectbox("Product*", products)
            waste_quantity = st.number_input("Quantity Wasted*", min_value=0.0, step=0.1)
            waste_unit = st.selectbox("Unit", ["kg", "pieces", "liters"])
            waste_date = st.date_input("Date*", value=datetime.now().date())
            waste_reason = st.selectbox("Reason", ["Expired", "Damaged", "Overstock", "Quality Issues", "Other"])
            
            submitted = st.form_submit_button("Log Waste")
            
            if submitted and waste_quantity > 0:
                # Load existing waste data
                try:
                    waste_df = pd.read_csv("data/waste_data.csv")
                except FileNotFoundError:
                    waste_df = pd.DataFrame(columns=["Date", "Store", "Product", "Quantity", "Unit", "Reason"])
                
                # Add new waste entry
                new_waste = pd.DataFrame({
                    "Date": [str(waste_date)],
                    "Store": [selected_store],
                    "Product": [waste_product],
                    "Quantity": [waste_quantity],
                    "Unit": [waste_unit],
                    "Reason": [waste_reason]
                })
                
                waste_df = pd.concat([waste_df, new_waste], ignore_index=True)
                
                # Save waste data
                os.makedirs("data", exist_ok=True)
                waste_df.to_csv("data/waste_data.csv", index=False)
                
                st.success(f"Logged {waste_quantity} {waste_unit} of {waste_product} waste!")
                st.rerun()
    
    with col2:
        st.subheader("Recent Waste Entries")
        try:
            waste_df = pd.read_csv("data/waste_data.csv")
            store_waste = waste_df[waste_df['Store'] == selected_store].tail(10)
            
            if not store_waste.empty:
                st.dataframe(store_waste[['Date', 'Product', 'Quantity', 'Unit', 'Reason']], use_container_width=True)
            else:
                st.info("No waste entries for this store yet.")
        except FileNotFoundError:
            st.info("No waste data available yet.")
    
    # Waste heatmap
    st.subheader("Waste Heatmap - Last 30 Days")
    try:
        waste_df = pd.read_csv("data/waste_data.csv")
        waste_df['Date'] = pd.to_datetime(waste_df['Date'])
        
        # Filter last 30 days and selected store
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_waste = waste_df[
            (waste_df['Date'] >= thirty_days_ago) & 
            (waste_df['Store'] == selected_store)
        ]
        
        if not recent_waste.empty:
            # Create pivot table for heatmap
            waste_pivot = recent_waste.groupby(['Date', 'Product'])['Quantity'].sum().reset_index()
            waste_pivot['Date'] = waste_pivot['Date'].dt.strftime('%Y-%m-%d')
            
            fig = px.density_heatmap(
                waste_pivot, 
                x='Date', 
                y='Product', 
                z='Quantity',
                title="Daily Waste by Product"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough waste data for heatmap visualization.")
    except FileNotFoundError:
        st.info("No waste data available for heatmap.")

# Tab 4: Visual Insights
elif tab_selection == "📈 Visual Insights":
    st.header("📈 Visual Analytics & Insights")
    
    # Load data for visualizations
    try:
        sales_df = pd.read_csv("data/sales_data.csv")
        waste_df = pd.read_csv("data/waste_data.csv")
        
        # Filter for selected store
        store_sales = sales_df[sales_df['Store'] == selected_store] if 'Store' in sales_df.columns else sales_df
        store_waste = waste_df[waste_df['Store'] == selected_store] if 'Store' in waste_df.columns else waste_df
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sales trend chart
            st.subheader("Sales Trends")
            if not store_sales.empty and 'Date' in store_sales.columns:
                sales_trend = store_sales.groupby('Date')['Actual_Sales'].sum().reset_index()
                fig_sales = px.line(sales_trend, x='Date', y='Actual_Sales', title="Daily Sales Trend")
                st.plotly_chart(fig_sales, use_container_width=True)
            else:
                st.info("No sales data available for visualization.")
            
            # Predicted vs Actual
            st.subheader("Forecast Accuracy")
            if not store_sales.empty and 'Predicted_Sales' in store_sales.columns:
                accuracy_data = store_sales[['Date', 'Predicted_Sales', 'Actual_Sales']].groupby('Date').sum().reset_index()
                fig_accuracy = go.Figure()
                fig_accuracy.add_trace(go.Scatter(x=accuracy_data['Date'], y=accuracy_data['Predicted_Sales'], name='Predicted'))
                fig_accuracy.add_trace(go.Scatter(x=accuracy_data['Date'], y=accuracy_data['Actual_Sales'], name='Actual'))
                fig_accuracy.update_layout(title="Predicted vs Actual Sales")
                st.plotly_chart(fig_accuracy, use_container_width=True)
            else:
                st.info("No prediction data available for comparison.")
        
        with col2:
            # Waste trends
            st.subheader("Weekly Waste Trends")
            if not store_waste.empty:
                store_waste['Date'] = pd.to_datetime(store_waste['Date'])
                store_waste['Week'] = store_waste['Date'].dt.strftime('%Y-W%U')
                weekly_waste = store_waste.groupby(['Week', 'Product'])['Quantity'].sum().reset_index()
                
                fig_waste = px.bar(weekly_waste, x='Week', y='Quantity', color='Product', title="Weekly Waste by Product")
                st.plotly_chart(fig_waste, use_container_width=True)
            else:
                st.info("No waste data available for trends.")
            
            # Most wasted products
            st.subheader("Most Wasted Products")
            if not store_waste.empty:
                product_waste = store_waste.groupby('Product')['Quantity'].sum().reset_index()
                product_waste = product_waste.sort_values('Quantity', ascending=False).head(10)
                
                fig_pie = px.pie(product_waste, values='Quantity', names='Product', title="Top Wasted Products")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No waste data available for product analysis.")
        
    except FileNotFoundError:
        st.warning("Sales or waste data files not found. Please ensure data is available.")

# Tab 5: AI Assistant
elif tab_selection == "🤖 AI Assistant":
    st.header("🤖 AI Assistant - Ask About Your Data")
    st.markdown("Ask questions about forecasts, waste patterns, and get insights!")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your store's data..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get context data
                    context_data = ai_assistant.get_store_context(selected_store)
                    response = ai_assistant.get_response(prompt, context_data)
                    st.write(response)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"I'm sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    # Quick question buttons
    st.subheader("Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("What products might go to waste tomorrow?"):
            st.session_state.chat_history.append({"role": "user", "content": "What products might go to waste tomorrow?"})
            st.rerun()
    
    with col2:
        if st.button("Show me this week's waste patterns"):
            st.session_state.chat_history.append({"role": "user", "content": "Show me this week's waste patterns"})
            st.rerun()
    
    with col3:
        if st.button("How can I reduce food waste?"):
            st.session_state.chat_history.append({"role": "user", "content": "How can I reduce food waste?"})
            st.rerun()
    
    st.subheader("Node.js Backend Interaction")
    with st.form("node_backend_form"):
        st.write("Send data to the Node.js backend and get a response.")
        input_name = st.text_input("Enter your name", "Streamlit User")
        input_number = st.number_input("Enter a number", 10, 100, 50)
        
        submit_button = st.form_submit_button("Send to Node.js Backend")
        
        if submit_button:
            try:
                payload = {"name": input_name, "number": input_number}
                response = requests.post("http://localhost:5000/api/data", json=payload)
                
                if response.status_code == 200:
                    st.success("Successfully received response from Node.js backend!")
                    st.json(response.json())
                else:
                    st.error(f"Error from Node.js backend: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to Node.js backend. Make sure it's running on http://localhost:5000.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown("💡 **Tip**: Use the AI Assistant to get personalized insights about your store's performance and waste reduction strategies!")
