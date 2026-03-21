import os
import json
from google import genai
from google.genai import types

API_KEY = os.getenv("GEMINI_KEY", "")
if not API_KEY:
    raise ValueError("GEMINI_KEY is missing. Set GEMINI_KEY in environment variables.")

client = genai.Client(api_key=API_KEY)


# Tool definition - NO "type": "function" wrapper for google.genai
TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_weather_data",
        description="Get weather data for a specific location",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "latitude": types.Schema(type="NUMBER", description="Latitude (-90 to 90)"),
                "longitude": types.Schema(type="NUMBER", description="Longitude (-180 to 180)"),
            },
            required=["latitude", "longitude"]
        )
    )
])


def get_weather_data(latitude: float, longitude: float) -> dict:
    """
    Fetch weather data from Open-Meteo API
    Returns 7 days of hourly weather data
    """
    import requests
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,visibility,cloud_cover,wind_speed_10m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "ms",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            "date": data.get("hourly", {}).get("time", []),
            "temperature_2m": data.get("hourly", {}).get("temperature_2m", []),
            "relative_humidity_2m": data.get("hourly", {}).get("relative_humidity_2m", []),
            "precipitation": data.get("hourly", {}).get("precipitation", []),
            "visibility": data.get("hourly", {}).get("visibility", []),
            "cloud_cover": data.get("hourly", {}).get("cloud_cover", []),
            "wind_speed_10m": data.get("hourly", {}).get("wind_speed_10m", [])
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}


def process_tool_call(tool_name: str, tool_input: dict) -> dict:
    """Execute tool calls from the model"""
    if tool_name == "get_weather_data":
        return get_weather_data(
            latitude=tool_input.get("latitude"),
            longitude=tool_input.get("longitude")
        )
    return {"error": f"Unknown tool: {tool_name}"}


def generate_response(message: str) -> str:
    """
    Generate response with tool use enabled.
    Handles agentic loop for tool calls.
    """
    
    messages = [{"role": "user", "parts": [{"text": message}]}]
    
    # Make initial request WITH TOOLS enabled
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[TOOLS]
        )
    )
    
    # Agentic loop: handle tool calls until model returns final response
    while True:
        # Extract tool calls and text from response
        tool_calls = []
        text_content = ""
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call'):
                tool_calls.append(part.function_call)
            elif hasattr(part, 'text'):
                text_content += part.text
        
        # If no tool calls, return the text response
        if not tool_calls:
            return text_content if text_content else "No response generated"
        
        # Process tool calls
        print(f"🔍 Model called {len(tool_calls)} tool(s)")
        
        # Add model's response to messages
        messages.append({"role": "model", "parts": response.candidates[0].content.parts})

        
        # Execute tools and collect results
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_input = dict(tool_call.args)
            
            print(f"   → {tool_name}({tool_input})")
            
            # Execute the tool
            result = process_tool_call(tool_name, tool_input)
            
            tool_results.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response=result
                    )
                )
            )
        
        # Add tool results back to conversation
        messages.append({"role": "user", "parts": tool_results})
        
        # Get next response from model (may call tools again or return final answer)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[TOOLS]
                )
)


if __name__ == "__main__":
    # Test example
    print("Testing Gemini with tool use...")
    response = generate_response(
        "What's the weather like in New York City (latitude: 40.7128, longitude: -74.0060)?"
    )
    print(f"\nBot: {response}")