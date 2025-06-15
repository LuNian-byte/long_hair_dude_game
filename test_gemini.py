import os
import google.generativeai as genai
from pprint import pprint

# Set API key
api_key = "AIzaSyASeO6HAoJHVrhLeeZ_HxtNaqrk2QcMIgM"
genai.configure(api_key=api_key)

# First, let's list available models
print("=== Available Models ===")
for model in genai.list_models():
    print(model.name)

# Test with one of the available models
try:
    # Using gemini-1.5-pro which is available in the model list
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    response = model.generate_content("Hello! Please respond with a short greeting.")
    print("\n=== API Connection Successful ===")
    print("Response from Gemini API:")
    print(response.text)
    print("\nAPI key is working correctly!")
except Exception as e:
    print("\n=== API Connection Failed ===")
    print(f"Error: {e}")
    print("\nPlease check your API key and internet connection.") 