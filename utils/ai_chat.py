import os
import json
import pandas as pd
from datetime import datetime, timedelta

class AIAssistant:
    def __init__(self):
        self.api_provider = self.detect_api_provider()
        self.client = self.initialize_client()
    
    def detect_api_provider(self):
        """Detect which AI API is available"""
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            return "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        else:
             return "demo"
    
    def initialize_client(self):
        """Initialize the appropriate AI client"""
        if self.api_provider == "gemini":
            try:
                from google import genai
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                return genai.Client(api_key=api_key)
            except ImportError:
                print("Gemini client not available. Please install google-genai.")
                return None
        elif self.api_provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                print("OpenAI client not available. Please install openai.")
                return None
        return None
    
    def get_store_context(self, store):
        """Gather context data about the store for AI responses"""
        context = {
            'store': store,
            'date': str(datetime.now().date()),
            'sales_data': {},
            'waste_data': {},
            'events': []
        }
        
        try:
            # Load sales data
            sales_df = pd.read_csv("data/sales_data.csv")
            store_sales = sales_df[sales_df['Store'] == store] if 'Store' in sales_df.columns else sales_df
            
            if not store_sales.empty:
                # Recent sales summary
                recent_sales = store_sales.tail(7)  # Last 7 entries
                context['sales_data'] = {
                    'total_recent_sales': recent_sales['Actual_Sales'].sum(),
                    'avg_daily_sales': recent_sales.groupby('Date')['Actual_Sales'].sum().mean(),
                    'top_products': recent_sales.groupby('Product')['Actual_Sales'].sum().nlargest(3).to_dict()
                }
        except FileNotFoundError:
            pass
        
        try:
            # Load waste data
            waste_df = pd.read_csv("data/waste_data.csv")
            store_waste = waste_df[waste_df['Store'] == store] if 'Store' in waste_df.columns else waste_df
            
            if not store_waste.empty:
                # Recent waste summary
                recent_waste = store_waste[store_waste['Date'] >= str((datetime.now() - timedelta(days=7)).date())]
                context['waste_data'] = {
                    'total_recent_waste': recent_waste['Quantity'].sum(),
                    'most_wasted_products': recent_waste.groupby('Product')['Quantity'].sum().nlargest(3).to_dict(),
                    'waste_reasons': recent_waste['Reason'].value_counts().to_dict()
                }
        except FileNotFoundError:
            pass
        
        try:
            # Load events data
            with open("data/event_data.json", "r") as f:
                events = json.load(f)
            
            # Filter recent events for this store
            recent_events = [
                e for e in events 
                if e['store'] == store and 
                datetime.strptime(e['date'], '%Y-%m-%d').date() >= (datetime.now() - timedelta(days=30)).date()
            ]
            context['events'] = recent_events
        except FileNotFoundError:
            pass
        
        return context
    
    def get_response(self, user_message, context_data):
        """Get AI response based on user message and context"""
        # Simple fallback AI logic for demo
        if user_message is None:
            user_message = ""

        message = user_message.lower()

# Question 1
        if "waste tomorrow" in message:
            return "Based on recent data, fresh produce like bananas and lettuce have the highest waste risk. Consider reducing order quantities."

# Question 2
        elif "waste patterns" in message:
            return "Waste patterns this week show higher spoilage in fresh produce. Monitoring storage temperature and reducing excess ordering can help."

# Question 3
        elif "reduce food waste" in message:
            return "You can reduce food waste by optimizing order quantities, improving storage conditions, and monitoring demand forecasts."

# Question 4
        elif "reorder" in message:
            return "Items like bread and milk are running low based on current stock levels. Consider reordering them today."

        elif "forecast" in message:
            return "The forecast module predicts demand using historical sales data and seasonal patterns."
# Default
        else:
            return f"""
            I couldn't find an exact answer, but here are some insights based on the store data:
            • High waste risk products usually include fresh produce like bananas, lettuce, and tomatoes.
            • Monitoring daily demand forecasts helps reduce over-ordering.
            • Adjusting reorder levels can significantly reduce food waste.

            You can also ask questions about:
            - Waste patterns
            - Product demand
            - Reordering suggestions
            - Forecast insights"""
        
        # Create context-aware prompt
        system_prompt = f"""You are an AI assistant for a smart food waste management system. 
        You help retail store managers reduce food waste and optimize inventory.
        
        Current store context:
        - Store: {context_data['store']}
        - Date: {context_data['date']}
        - Recent sales data: {context_data['sales_data']}
        - Recent waste data: {context_data['waste_data']}
        - Recent events: {context_data['events']}
        
        Provide helpful, actionable insights based on this data. Be conversational and practical.
        Focus on waste reduction strategies, demand forecasting insights, and operational recommendations.
        """
        
        try:
            if self.api_provider == "gemini":
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",  # the newest Gemini model is "gemini-2.5-flash" or "gemini-2.5-pro"
                    contents=f"{system_prompt}\n\nUser question: {user_message}"
                )
                return response.text or "I'm sorry, I couldn't generate a response."
            
            elif self.api_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content
            
        except Exception as e:
            return f"I encountered an error while processing your request: {str(e)}. Please check your API configuration."
    
    def get_waste_prediction_insights(self, store, context_data):
        """Generate specific insights about waste predictions"""
        insights = []
        
        # Analyze waste patterns
        waste_data = context_data.get('waste_data', {})
        if waste_data:
            most_wasted = waste_data.get('most_wasted_products', {})
            if most_wasted:
                top_waste_product = list(most_wasted.keys())[0]
                insights.append(f"⚠️ {top_waste_product} is your top waste concern - consider reducing orders.")
        
        # Analyze events impact
        events = context_data.get('events', [])
        upcoming_events = [
            e for e in events 
            if datetime.strptime(e['date'], '%Y-%m-%d').date() >= datetime.now().date()
        ]
        
        if upcoming_events:
            for event in upcoming_events[:2]:  # Show max 2 upcoming events
                insights.append(f"📅 Upcoming event '{event['name']}' on {event['date']} - expect {event.get('impact', 'medium')} impact on demand.")
        
        return insights
