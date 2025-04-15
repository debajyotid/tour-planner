import streamlit as st
import openai
import googlemaps
import requests

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from openai import OpenAI

st.title("AI Trip Planner")
destination = st.text_input("Enter your destination:")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
budget = st.number_input("Enter your budget (£):", min_value=0)
interests = st.multiselect("Select your interests:",["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"])
llm = ChatOpenAI(model="gpt-3.5-turbo-0125",
                 temperature=0, 
                 api_key=st.secrets["OPENAI_API_KEY"])
conversation = ConversationChain(llm=llm)

def generate_itinerary(destination, start_date, end_date, budget, interests):

    tourist_attraction = get_attractions(destination)
    weather_forecast = get_weather(destination)

    """Generates a day-by-day itinerary using OpenAI's ChatCompletion API.

    Constructs a prompt based on user inputs and queries OpenAI's model to
    generate a travel itinerary.
    """
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"""
    You are a helpful tour planner.
    Please create a day-by-day itinerary for a trip to {destination} 
    from {start_date} to {end_date}
    within a budget of £{budget} and 
    with focus on the below interests {', '.join(interests)}.
    Please also include places like, {tourist_attraction}, in the itinerary and
    factor the forecasted weather, like {weather_forecast} into your itinerary.
    """
    response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
                                              messages=[
                                                            {
                                                                "role": "developer",
                                                                "content": prompt
                                                            }
                                                        ],
                                              max_tokens=500,
                                              temperature=0)
    return response.choices[0].message.content
    
def get_attractions(destination):
    """
    Fetches a list of tourist attractions near a given destination using the Google Maps API.

    Args:
        destination (str): The location (latitude and longitude as a string) around which to search for tourist attractions.

    Returns:
        list: A list of names of tourist attractions near the specified destination.

    Note:
        - The function uses the Google Maps API and requires a valid API key stored in `st.secrets["googlemaps_api_key"]`.
        - The search radius is set to 5000 meters.
        - The type of places searched is restricted to 'tourist_attraction'.
    """
    gmaps = googlemaps.Client(key=st.secrets["googlemaps_api_key"])
    places_result = gmaps.places_nearby(location=destination,radius=5000,type='tourist_attraction')
    return [place['name'] for place in places_result['results']]

def get_weather(destination):
    """Fetches the current weather description for a given destination using OpenWeatherMap API.

    Args:
        destination (str): The city name for which to retrieve the weather.

    Returns:
        str: A string describing the current weather conditions (e.g., 'clear sky').
             Note: This function assumes the API key is stored in Streamlit secrets
             and does not handle potential errors like invalid destinations,
             network issues, or API key problems gracefully. It might raise
             exceptions (e.g., KeyError, requests.exceptions.RequestException)
             if the API call fails or the response format is unexpected. Requires
             'requests' and 'streamlit' libraries to be imported.
    """    
    api_key = st.secrets["openweather_api_key"]
    url = f"http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={api_key}"
    response = requests.get(url).json()
    return response['weather'][0]['description']
    
if st.button("Generate Plan"):
    # Call the AI model and APIs here
    st.write("Generating your trip plan...")
    itinerary = generate_itinerary(destination, start_date, end_date, budget, interests)
    st.text_area("Your AI-generated itinerary:", itinerary)

# user_message = st.text_input("Refine your plan by asking questions:")
# if user_message:
#     reply = conversation.run(input=user_message)
#     st.write(reply)
