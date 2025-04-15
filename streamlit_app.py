import streamlit as st
import openai
import googlemaps
import requests

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from openai import OpenAI

st.title("AI Trip Planner")
OPENAI_API_KEY = st.text_input("Enter your OpenAI API Key:")
googlemaps_api_key=st.text_input("Enter your GoogleMaps API Key:")
openweather_api_key=st.text_input("Enter your OpenWeather API Key:")
destination = st.text_input("Enter your destination:")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
budget = st.number_input("Enter your budget (£):", min_value=0)
interests = st.multiselect("Select your interests:",
                          ["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"]
                           )
llm = ChatOpenAI(model="gpt-3.5-turbo-0125",
                 temperature=0, 
                 api_key=OPENAI_API_KEY)
conversation = ConversationChain(llm=llm)

def generate_itinerary(destination, start_date, end_date, interests):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
    I am planning a trip to {destination} from {start_date} to {end_date}.
    My interests are {', '.join(interests)}.
    Please create a day-by-day itinerary including activities, restaurants, and must-see attractions.
    """
    response = client.completions.create(engine="gpt-3.5-turbo-0125",prompt=prompt,max_tokens=500,temperature=0)
    return response['choices'][0]['text']

if destination:
    itinerary = generate_itinerary(destination, start_date, end_date, interests)
    st.text_area("Your AI-generated itinerary:", itinerary)

def get_attractions(destination):
    gmaps = googlemaps.Client(key=googlemaps_api_key)
    places_result = gmaps.places_nearby(location=destination,radius=5000,type='tourist_attraction')
    return [place['name'] for place in places_result['results']]

if destination:
    attractions = get_attractions(destination)
    st.write("Top Attractions:", attractions)

def get_weather(destination):
    api_key = openweather_api_key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={api_key}"
    response = requests.get(url).json()
    return response['weather'][0]['description']

if destination:
    weather = get_weather(destination)
    st.write(f"Weather in {destination}: {weather}")

if st.button("Generate Plan"):
    # Call the AI model and APIs here
    st.write("Generating your trip plan...")
    generate_itinerary(destination, start_date, end_date, interests)
    get_attractions(destination)
    get_weather(destination)

st.header("Your Final Itinerary")
st.write(itinerary)
st.write("Top Attractions:", ", ".join(attractions))
st.write(f"Weather Forecast: {weather}")

user_message = st.text_input("Refine your plan by asking questions:")
if user_message:
    reply = conversation.run(input=user_message)
    st.write(reply)
