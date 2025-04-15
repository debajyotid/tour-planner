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
    """Generates a personalized travel itinerary using OpenAI.

    Fetches local attractions and weather forecasts to create a detailed,
    day-by-day plan based on user preferences and constraints.

    Args:
        destination (str): The city or region for the trip.
        start_date (str): The starting date of the trip (e.g., "YYYY-MM-DD").
        end_date (str): The ending date of the trip (e.g., "YYYY-MM-DD").
        budget (float | int): The total budget for the trip in GBP (£).
        interests (list[str]): A list of the traveler's interests (e.g., ["history", "food"]).

    Returns:
        str: A string containing the generated day-by-day itinerary from the OpenAI model.

    Raises:
        KeyError: If the OpenAI API key ("OPENAI_API_KEY") is not found in Streamlit secrets.
        openai.APIError: If there is an issue communicating with the OpenAI API.
        # Note: This function also depends on the successful execution of
        # get_attractions() and get_weather(), which might raise their own specific errors
        # (e.g., related to Google Maps API, OpenWeatherMap API, network issues, or missing keys).

    Note:
        Requires the 'openai' library and Streamlit ('st') for secret management.
        Assumes `get_attractions` and `get_weather` functions are defined and
        accessible in the same scope and handle their own API interactions.
    """ 
    tourist_attraction = get_attractions(destination)
    weather_forecast = get_weather(destination)

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
    """Fetches a list of tourist attractions near a given destination using the Google Maps API.

    Args:
        destination (str): The name of the destination (e.g., "Paris, France").

    Returns:
        list[str]: A list of names of tourist attractions near the destination.
                   Returns an empty list if no attractions are found.

    Raises:
        ValueError: If the destination cannot be geocoded.
        googlemaps.exceptions.ApiError: If there is an issue with the Google Maps API request.
        KeyError: If the API key is not found in Streamlit secrets.

    Note:
        This function requires the 'googlemaps' and 'streamlit' libraries to be installed
        and a valid Google Maps API key stored in Streamlit secrets under the key
        "googlemaps_api_key". It searches for attractions within a 5km radius
        of the geocoded destination. Requires 'googlemaps' and 'streamlit'
        libraries to be imported.
    """

    gmaps = googlemaps.Client(key=st.secrets["googlemaps_api_key"])

    geocode_result = gmaps.geocode(destination)
    if not geocode_result:
        raise ValueError(f"Could not geocode destination: {destination}")
    location = geocode_result[0]['geometry']['location']
    lat_lng = (location['lat'], location['lng'])

    places_result = gmaps.places_nearby(location=lat_lng,radius=5000,type='tourist_attraction')
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
