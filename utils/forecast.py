import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from io import BytesIO
import base64

class ForecastEngine:
    def __init__(self):
        self.products = [
            "Apples", "Bananas", "Bread", "Milk", "Cheese", 
            "Yogurt", "Lettuce", "Tomatoes", "Chicken", "Beef"
        ]
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """Ensure sample data files exist"""
        os.makedirs("data", exist_ok=True)
        
        # Create sample sales data if it doesn't exist
        if not os.path.exists("data/sales_data.csv"):
            self.create_sample_sales_data()
    
    def create_sample_sales_data(self):
        """Create sample sales data for demonstration"""
        stores = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
        
        # Generate 30 days of historical data
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
        
        data = []
        for store in stores:
            for date in dates:
                for product in self.products:
                    # Generate realistic sales data with some randomness
                    base_demand = np.random.randint(20, 200)
                    seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * len(data) / 7)  # Weekly pattern
                    actual_sales = int(base_demand * seasonal_factor * np.random.uniform(0.8, 1.2))
                    predicted_sales = int(actual_sales * np.random.uniform(0.9, 1.1))  # Add some prediction variance
                    
                    data.append({
                        'Date': date,
                        'Store': store,
                        'Product': product,
                        'Actual_Sales': actual_sales,
                        'Predicted_Sales': predicted_sales
                    })
        
        df = pd.DataFrame(data)
        df.to_csv("data/sales_data.csv", index=False)
    
    def get_daily_forecast(self, store):
        """Get today's forecast for a specific store"""
        try:
            # Load historical sales data
            sales_df = pd.read_csv("data/sales_data.csv")
            
            # Filter for the selected store
            store_data = sales_df[sales_df['Store'] == store]
            
            if store_data.empty:
                return pd.DataFrame()
            
            # Calculate average demand and trends for each product
            forecasts = []
            
            for product in self.products:
                product_data = store_data[store_data['Product'] == product]
                
                if not product_data.empty:
                    # Calculate base demand from historical average
                    avg_demand = product_data['Actual_Sales'].mean()
                    
                    # Add some seasonality and randomness
                    today_factor = 1 + 0.1 * np.sin(2 * np.pi * datetime.now().timetuple().tm_yday / 365)
                    predicted_qty = int(avg_demand * today_factor * np.random.uniform(0.9, 1.1))
                    
                    # Calculate waste risk based on historical patterns
                    waste_risk = self.calculate_waste_risk(product, store, product_data)
                    
                    forecasts.append({
                        'Product Name': product,
                        'Predicted Qty': predicted_qty,
                        'Waste Risk %': waste_risk
                    })
            
            return pd.DataFrame(forecasts)
            
        except Exception as e:
            print(f"Error generating forecast: {e}")
            return pd.DataFrame()
    
    def calculate_waste_risk(self, product, store, historical_data):
        """Calculate waste risk percentage for a product"""
        try:
            # Try to load waste data
            waste_df = pd.read_csv("data/waste_data.csv")
            
            # Filter waste data for this product and store
            product_waste = waste_df[
                (waste_df['Product'] == product) & 
                (waste_df['Store'] == store)
            ]
            
            if not product_waste.empty:
                # Calculate waste rate based on historical data
                recent_waste = product_waste['Quantity'].sum()
                if 'Actual_Sales' in historical_data.columns:
                    recent_sales = historical_data['Actual_Sales'].tail(7).sum()
                else:
                    recent_sales = 0
                
                if recent_sales > 0:
                    waste_rate = (recent_waste / recent_sales) * 100
                    return min(100, max(0, int(waste_rate)))
            
            # Default risk calculation based on product type
            high_risk_products = ["Lettuce", "Tomatoes", "Bananas", "Milk", "Yogurt"]
            medium_risk_products = ["Bread", "Cheese", "Chicken"]
            
            if product in high_risk_products:
                return np.random.randint(60, 90)
            elif product in medium_risk_products:
                return np.random.randint(30, 60)
            else:
                return np.random.randint(10, 40)
                
        except FileNotFoundError:
            # If no waste data exists, use product-based risk estimation
            high_risk_products = ["Lettuce", "Tomatoes", "Bananas", "Milk", "Yogurt"]
            medium_risk_products = ["Bread", "Cheese", "Chicken"]
            
            if product in high_risk_products:
                return np.random.randint(60, 90)
            elif product in medium_risk_products:
                return np.random.randint(30, 60)
            else:
                return np.random.randint(10, 40)
    
    def get_store_summary(self, store):
        """Get summary statistics for a store"""
        try:
            sales_df = pd.read_csv("data/sales_data.csv")
            store_data = sales_df[sales_df['Store'] == store]
            
            if store_data.empty:
                return {}
            
            # Calculate metrics
            total_sales = store_data['Actual_Sales'].sum()
            avg_daily_sales = store_data.groupby('Date')['Actual_Sales'].sum().mean()
            top_products = store_data.groupby('Product')['Actual_Sales'].sum().nlargest(3)
            
            return {
                'total_sales': total_sales,
                'avg_daily_sales': avg_daily_sales,
                'top_products': top_products.to_dict()
            }
            
        except Exception as e:
            print(f"Error getting store summary: {e}")
            return {}
    
    def get_product_list(self, store):
        """Get comprehensive product list with current data"""
        try:
            # Load or create product master data
            product_file = "data/product_master.csv"
            if not os.path.exists(product_file):
                self.create_product_master()
            
            products_df = pd.read_csv(product_file)
            store_products = products_df[products_df['Store'] == store] if 'Store' in products_df.columns else products_df
            
            # Add current waste risk calculations
            for idx, row in store_products.iterrows():
                waste_risk = self.calculate_waste_risk(row['Product Name'], store, pd.DataFrame())
                store_products.at[idx, 'Waste Risk %'] = waste_risk
            
            return store_products
            
        except Exception as e:
            print(f"Error getting product list: {e}")
            return pd.DataFrame()
    
    def create_product_master(self):
        """Create initial product master data"""
        stores = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
        categories = {
            "Apples": "Fresh Produce", "Bananas": "Fresh Produce", "Lettuce": "Fresh Produce", "Tomatoes": "Fresh Produce",
            "Milk": "Dairy", "Cheese": "Dairy", "Yogurt": "Dairy",
            "Chicken": "Meat", "Beef": "Meat",
            "Bread": "Bakery"
        }
        
        data = []
        for store in stores:
            for product, category in categories.items():
                data.append({
                    'Store': store,
                    'Product Name': product,
                    'Category': category,
                    'Current Stock': np.random.randint(10, 100),
                    'Reorder Level': np.random.randint(5, 25),
                    'Unit Price': round(np.random.uniform(0.5, 15.0), 2),
                    'Supplier': f"Supplier {np.random.choice(['A', 'B', 'C', 'D'])}",
                    'Status': 'Active',
                    'Waste Risk %': 0
                })
        
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/product_master.csv", index=False)
    
    def apply_product_filters(self, products_df, category_filter, risk_filter, stock_filter):
        """Apply filters to product dataframe"""
        filtered_df = products_df.copy()
        
        # Category filter
        if category_filter != "All":
            filtered_df = filtered_df[filtered_df['Category'] == category_filter]
        
        # Risk filter
        if risk_filter != "All":
            if risk_filter == "High Risk (>70%)":
                filtered_df = filtered_df[filtered_df['Waste Risk %'] > 70]
            elif risk_filter == "Medium Risk (30-70%)":
                filtered_df = filtered_df[(filtered_df['Waste Risk %'] >= 30) & (filtered_df['Waste Risk %'] <= 70)]
            elif risk_filter == "Low Risk (<30%)":
                filtered_df = filtered_df[filtered_df['Waste Risk %'] < 30]
        
        # Stock filter
        if stock_filter != "All":
            if stock_filter == "Low Stock":
                filtered_df = filtered_df[filtered_df['Current Stock'] <= filtered_df['Reorder Level']]
            elif stock_filter == "Out of Stock":
                filtered_df = filtered_df[filtered_df['Current Stock'] == 0]
            elif stock_filter == "In Stock":
                filtered_df = filtered_df[filtered_df['Current Stock'] > filtered_df['Reorder Level']]
        
        return filtered_df
    
    def save_product_updates(self, updated_df, store):
        """Save product updates to master file"""
        try:
            # Load existing data
            products_df = pd.read_csv("data/product_master.csv")
            
            # Update products for this store
            store_mask = products_df['Store'] == store
            products_df.loc[store_mask] = updated_df.values
            
            # Save back to file
            products_df.to_csv("data/product_master.csv", index=False)
            return True
            
        except Exception as e:
            print(f"Error saving product updates: {e}")
            return False
    
    def add_new_product(self, store, name, category, stock, reorder, price, supplier):
        """Add new product to master list"""
        try:
            # Load existing data
            products_df = pd.read_csv("data/product_master.csv")
            
            # Add new product
            new_product = pd.DataFrame({
                'Store': [store],
                'Product Name': [name],
                'Category': [category],
                'Current Stock': [stock],
                'Reorder Level': [reorder],
                'Unit Price': [price],
                'Supplier': [supplier],
                'Status': ['Active'],
                'Waste Risk %': [0]
            })
            
            products_df = pd.concat([products_df, new_product], ignore_index=True)
            products_df.to_csv("data/product_master.csv", index=False)
            return True
            
        except Exception as e:
            print(f"Error adding new product: {e}")
            return False
    
    def get_enhanced_forecast(self, store, period):
        """Get enhanced forecast with confidence and recommendations"""
        try:
            forecast_data = self.get_daily_forecast(store)
            if forecast_data.empty:
                return pd.DataFrame()
            
            # Add enhanced columns
            enhanced_data = forecast_data.copy()
            enhanced_data['Manual Override'] = 0
            enhanced_data['Final Qty'] = enhanced_data['Predicted Qty']
            enhanced_data['Confidence'] = np.random.randint(75, 95, len(enhanced_data))  # AI confidence
            
            # Add recommendations
            recommendations = []
            for _, row in enhanced_data.iterrows():
                if row['Waste Risk %'] > 70:
                    recommendations.append("⚠️ Reduce order")
                elif row['Waste Risk %'] < 30:
                    recommendations.append("✅ Safe to order")
                else:
                    recommendations.append("⚡ Monitor closely")
            
            enhanced_data['Suggested Action'] = recommendations
            return enhanced_data
            
        except Exception as e:
            print(f"Error getting enhanced forecast: {e}")
            return pd.DataFrame()
    
    def save_forecast(self, forecast_df, store, period):
        """Save finalized forecast"""
        try:
            # Create forecast history directory
            os.makedirs("data/forecasts", exist_ok=True)
            
            # Save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/forecasts/forecast_{store}_{period}_{timestamp}.csv"
            forecast_df.to_csv(filename, index=False)
            
            return True
        except Exception as e:
            print(f"Error saving forecast: {e}")
            return False
    
    def generate_forecast_pdf(self, forecast_df, store, period):
        """Generate PDF report of forecast"""
        try:
            # Simple HTML to PDF conversion (mock implementation)
            html_content = f"""
            <html>
            <head><title>Forecast Report - {store}</title></head>
            <body>
                <h1>Smart Forecasting Report</h1>
                <h2>Store: {store}</h2>
                <h3>Period: {period}</h3>
                <h3>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h3>
                
                <table border="1">
                    <tr>
                        <th>Product</th>
                        <th>AI Prediction</th>
                        <th>Final Forecast</th>
                        <th>Waste Risk</th>
                        <th>Action</th>
                    </tr>
            """
            
            for _, row in forecast_df.iterrows():
                html_content += f"""
                    <tr>
                        <td>{row['Product Name']}</td>
                        <td>{row['Predicted Qty']}</td>
                        <td>{row['Final Qty']}</td>
                        <td>{row['Waste Risk %']}%</td>
                        <td>{row['Suggested Action']}</td>
                    </tr>
                """
            
            html_content += """
                </table>
            </body>
            </html>
            """
            
            # Return HTML as bytes (in real implementation, would use wkhtmltopdf or similar)
            return html_content.encode('utf-8')
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return b"PDF generation error"
    
    def get_forecast_accuracy(self, store):
        """Calculate forecast accuracy metrics"""
        try:
            sales_df = pd.read_csv("data/sales_data.csv")
            store_sales = sales_df[sales_df['Store'] == store] if 'Store' in sales_df.columns else sales_df
            
            if store_sales.empty:
                return None
            
            # Calculate accuracy for different periods
            recent_data = store_sales.tail(7)  # Last 7 days
            monthly_data = store_sales.tail(30)  # Last 30 days
            
            def calculate_accuracy(data):
                if data.empty or 'Predicted_Sales' not in data.columns:
                    return 50.0  # Default accuracy
                
                actual = data['Actual_Sales'].sum()
                predicted = data['Predicted_Sales'].sum()
                if actual == 0:
                    return 100.0 if predicted == 0 else 0.0
                
                accuracy = max(0, 100 - (abs(actual - predicted) / actual * 100))
                return min(100, accuracy)
            
            weekly_accuracy = calculate_accuracy(recent_data)
            monthly_accuracy = calculate_accuracy(monthly_data)
            
            # Calculate trend
            trend = "Improving" if weekly_accuracy > monthly_accuracy else "Declining"
            trend_delta = f"{abs(weekly_accuracy - monthly_accuracy):.1f}%"
            
            return {
                'weekly': weekly_accuracy,
                'monthly': monthly_accuracy,
                'trend': trend,
                'trend_delta': trend_delta
            }
            
        except Exception as e:
            print(f"Error calculating forecast accuracy: {e}")
            return None
    
    def get_sales_analytics(self, store, period):
        """Get sales analytics for different time periods"""
        try:
            sales_df = pd.read_csv("data/sales_data.csv")
            sales_df['Date'] = pd.to_datetime(sales_df['Date'])
            
            store_sales = sales_df[sales_df['Store'] == store] if 'Store' in sales_df.columns else sales_df
            
            if store_sales.empty:
                return pd.DataFrame()
            
            # Group by period
            if period == "Daily":
                grouped = store_sales.groupby('Date')['Actual_Sales'].sum().reset_index()
            elif period == "Weekly":
                store_sales['Week'] = store_sales['Date'].dt.strftime('%Y-W%U')
                grouped = store_sales.groupby('Week')['Actual_Sales'].sum().reset_index()
            elif period == "Monthly":
                store_sales['Month'] = store_sales['Date'].dt.strftime('%Y-%m')
                grouped = store_sales.groupby('Month')['Actual_Sales'].sum().reset_index()
            else:
                grouped = store_sales.groupby('Date')['Actual_Sales'].sum().reset_index()
            
            return grouped
            
        except Exception as e:
            print(f"Error getting sales analytics: {e}")
            return pd.DataFrame()
    
    def get_restock_alerts(self, store):
        """Generate restock alerts for low inventory items"""
        try:
            products_df = self.get_product_list(store)
            if products_df.empty:
                return []
            
            # Find products that need restocking
            low_stock = products_df[products_df['Current Stock'] <= products_df['Reorder Level']]
            
            alerts = []
            for _, product in low_stock.iterrows():
                urgency = "HIGH" if product['Current Stock'] <= product['Reorder Level'] * 0.5 else "MEDIUM"
                alerts.append({
                    'product': product['Product Name'],
                    'current_stock': product['Current Stock'],
                    'reorder_level': product['Reorder Level'],
                    'urgency': urgency,
                    'supplier': product['Supplier']
                })
            
            return alerts
            
        except Exception as e:
            print(f"Error getting restock alerts: {e}")
            return []
    
    def calculate_waste_reduction_percentage(self, store):
        """Calculate waste reduction percentage over time"""
        try:
            waste_df = pd.read_csv("data/waste_data.csv")
            waste_df['Date'] = pd.to_datetime(waste_df['Date'])
            
            store_waste = waste_df[waste_df['Store'] == store] if 'Store' in waste_df.columns else waste_df
            
            if store_waste.empty:
                return {"current_week": 0, "previous_week": 0, "reduction": 0}
            
            # Calculate current week vs previous week
            current_week_start = datetime.now() - timedelta(days=7)
            previous_week_start = datetime.now() - timedelta(days=14)
            
            current_week_waste = store_waste[store_waste['Date'] >= current_week_start]['Quantity'].sum()
            previous_week_waste = store_waste[
                (store_waste['Date'] >= previous_week_start) & 
                (store_waste['Date'] < current_week_start)
            ]['Quantity'].sum()
            
            if previous_week_waste > 0:
                reduction = ((previous_week_waste - current_week_waste) / previous_week_waste) * 100
            else:
                reduction = 0
            
            return {
                "current_week": current_week_waste,
                "previous_week": previous_week_waste,
                "reduction": round(reduction, 1)
            }
            
        except Exception as e:
            print(f"Error calculating waste reduction: {e}")
            return {"current_week": 0, "previous_week": 0, "reduction": 0}
    
    def generate_sales_report(self, store, period, report_type):
        """Generate comprehensive sales report"""
        try:
            sales_df = pd.read_csv("data/sales_data.csv")
            store_sales = sales_df[sales_df['Store'] == store] if 'Store' in sales_df.columns else sales_df
            
            if store_sales.empty:
                return pd.DataFrame()
            
            # Generate report based on type
            if report_type == "Sales Report":
                return store_sales.groupby(['Date', 'Product']).agg({
                    'Actual_Sales': 'sum',
                    'Predicted_Sales': 'sum'
                }).reset_index()
            
            elif report_type == "Waste Report":
                try:
                    waste_df = pd.read_csv("data/waste_data.csv")
                    store_waste = waste_df[waste_df['Store'] == store] if 'Store' in waste_df.columns else waste_df
                    return store_waste
                except FileNotFoundError:
                    return pd.DataFrame()
            
            else:  # Combined Report
                sales_summary = store_sales.groupby('Product').agg({
                    'Actual_Sales': ['sum', 'mean'],
                    'Predicted_Sales': ['sum', 'mean']
                }).reset_index()
                return sales_summary
                
        except Exception as e:
            print(f"Error generating sales report: {e}")
            return pd.DataFrame()
    
    def log_waste_entry(self, store, product, quantity, unit, date, reason, value, notes):
        """Enhanced waste logging with additional fields"""
        try:
            # Load existing waste data
            try:
                waste_df = pd.read_csv("data/waste_data.csv")
            except FileNotFoundError:
                waste_df = pd.DataFrame(columns=["Date", "Store", "Product", "Quantity", "Unit", "Reason", "Value", "Notes"])
            
            # Add new waste entry
            new_waste = pd.DataFrame({
                "Date": [str(date)],
                "Store": [store],
                "Product": [product],
                "Quantity": [quantity],
                "Unit": [unit],
                "Reason": [reason],
                "Value": [value],
                "Notes": [notes]
            })
            
            waste_df = pd.concat([waste_df, new_waste], ignore_index=True)
            
            # Save waste data
            os.makedirs("data", exist_ok=True)
            waste_df.to_csv("data/waste_data.csv", index=False)
            
            return True
            
        except Exception as e:
            print(f"Error logging waste entry: {e}")
            return False
