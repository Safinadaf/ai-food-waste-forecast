"""AIAssistant — uses Gemini or OpenAI if keys exist, else returns demo reply.
Input (stdin): {store, message, history[], context:{products,sales,waste,events}}
Output (stdout): JSON {reply, provider}
"""
import os, sys, json
from dotenv import load_dotenv

# Load .env file from the backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def demo_reply(payload):
    ctx = payload.get("context", {})
    msg = payload.get("message", "")
    store = payload.get("store") or "all stores"
    return {
        "reply": (
            f"(demo mode) You asked: '{msg}'. "
            f"For {store} I see {len(ctx.get('products', []))} products, "
            f"{len(ctx.get('sales', []))} recent sales rows, "
            f"{len(ctx.get('waste', []))} waste records, "
            f"{len(ctx.get('events', []))} events."
        ),
        "provider": "demo"
    }

def build_system_prompt():
    return (
        "You are a smart retail store assistant helping managers with inventory, "
        "sales forecasting, waste reduction, and ordering decisions. "
        "Answer concisely and practically using the provided JSON context."
    )

def gemini_reply(payload):
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("Missing Gemini API Key")

    # Build prompt with context
    ctx_text = f"CONTEXT:\n{json.dumps(payload.get('context', {}))[:8000]}"
    user_msg = payload.get("message", "")
    full_prompt = f"{build_system_prompt()}\n\n{ctx_text}\n\nUSER: {user_msg}"

    try:
        # Try new google-genai SDK first
        from google import genai
        client = genai.Client(api_key=key)
        
        # Build history for new SDK
        history = []
        for h in payload.get("history", [])[-10:]:
            role = "user" if h.get("role") == "user" else "model"
            history.append({"role": role, "parts": [{"text": h.get("content", "")}]})
        
        # Start chat if history exists, else just generate
        if history:
            chat = client.chats.create(model="gemini-2.0-flash", history=history)
            resp = chat.send_message(full_prompt)
        else:
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=full_prompt)
        
        return {"reply": resp.text, "provider": "gemini"}
    except ImportError:
        # Fallback to old google-generativeai SDK
        import google.generativeai as genai_old
        genai_old.configure(api_key=key)
        model = genai_old.GenerativeModel("gemini-2.0-flash")
        
        # Build history for old SDK
        history = []
        for h in payload.get("history", [])[-10:]:
            role = "user" if h.get("role") == "user" else "model"
            history.append({"role": role, "parts": [h.get("content", "")]})
        
        chat = model.start_chat(history=history)
        resp = chat.send_message(full_prompt)
        return {"reply": resp.text, "provider": "gemini"}

def openai_reply(payload):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    msgs = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "system", "content": "CONTEXT: " + json.dumps(payload.get("context", {}))[:8000]},
    ]
    for h in payload.get("history", [])[-10:]:
        msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    msgs.append({"role": "user", "content": payload.get("message", "")})

    out = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return {"reply": out.choices[0].message.content, "provider": "openai"}

if __name__ == "__main__":
    try:
        input_data = sys.stdin.read().strip()
        data = json.loads(input_data) if input_data else {}
    except Exception:
        data = {}

    try:
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            result = gemini_reply(data)
            print(json.dumps(result))
            sys.exit(0)
        if os.getenv("OPENAI_API_KEY"):
            result = openai_reply(data)
            print(json.dumps(result))
            sys.exit(0)
    except Exception as e:
        # Fall through to demo on any API error
        result = {**demo_reply(data), "error": str(e)}
        print(json.dumps(result))
        sys.exit(0)

    print(json.dumps(demo_reply(data)))
