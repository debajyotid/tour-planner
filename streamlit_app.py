import streamlit as st
import openai
import googlemaps
import requests

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from openai import OpenAI

# Using LanChain's ChatMessageHistory to save Chat session history
history = ChatMessageHistory()

# Using OpenAI "gpt-3.5-turbo-0125" model to generate the itinenary
llm = ChatOpenAI(model="gpt-3.5-turbo-0125",temperature=0,api_key=OPENAI_API_KEY)

st.title("AI Trip Planner")
destination = st.text_input("Enter your destination:")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
budget = st.number_input("Enter your budget (£):", min_value=0)
interests = st.multiselect("Select your interests:",["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"])

def get_attractions(googlemapsapi, destination):
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

    lat_lng = (destination['lat'], destination['lng'])

    # Using the "places_nearby" API to get tourist attractions, within a 5000m radius, of the latitude-longitude of the chosen destination
    places_result = googlemapsapi.places_nearby(
        location=lat_lng, radius=5000, type='tourist_attraction')
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
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={destination['lat']}&lon={destination['lng']}&appid={api_key}"
    response = requests.get(url).json()
    if response.get('weather'):
        return response['weather'][0]['description']
    else:
        return "Weather data not available."

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

    # Generating the latitude and longitudes for the chosen destination using GoogleMaps APIs
    gmaps = googlemaps.Client(key=googlemaps_api_key)
    geocode_result = gmaps.geocode(destination)
    if not geocode_result:
        raise ValueError(f"Could not geocode destination: {destination}")
    location = geocode_result[0]['geometry']['location']

    tourist_attraction = get_attractions(destination)
    weather_forecast = get_weather(destination)

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"""
    You are a helpful tour planner.
    Please create a day-by-day itinerary, within 1000 words or less,
    for a trip to {destination},
    from {start_date} to {end_date},
    within a budget of £{budget}, and 
    with focus on the below interests {', '.join(interests)}.
    Please also include places like, {tourist_attraction}, in the itinerary and
    factor the forecasted weather, like {weather_forecast} while building the itinerary.
    """
    response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
                                              messages=[
                                                            {
                                                                "role": "developer",
                                                                "content": prompt
                                                            }
                                                        ],
                                              max_tokens=1000,
                                              temperature=0)
    return response.choices[0].message.content


def get_refined_reply(user_input, history):

    # Generating a new prompt template to handle conversation history
    prompt = ChatPromptTemplate.from_messages([("system", "You are a helpful travel planning assistant. Refine the itinerary as per the user's requests."),
                                               ("ai", "{history}"),
                                               ("human", "{input}"),])
    
    # Add the user's new request to memory
    history.add_user_message(user_input)

    # Format the conversation so far
    conversation = ""
    for msg in history.messages:
        if msg.type == "human":
            conversation += f"User: {msg.content}\n"
        else:
            conversation += f"AI: {msg.content}\n"

    # Create the chain and run it
    chain = LLMChain(llm=llm, prompt=prompt)
    refined_itinerary = chain.run(history=conversation, input=user_input)
    history.add_ai_message(refined_itinerary)
    return refined_itinerary
    
if st.button("Generate Plan"):
    # Call the AI model and APIs here
    st.write("Generating your trip plan...")
    itinerary = generate_itinerary(destination, start_date, end_date, budget, interests)
    # Passing the generated itinenary to the Chat history
    history.add_ai_message(itinerary)
    st.text_area("Your AI-generated itinerary:", itinerary)

if st.button("Refine Plan"):
    # Call the AI model and APIs here
    st.write("Generating your refined trip plan...")
    refined_itinerary = get_refined_reply(user_input, history)
    st.text_area("Your AI-generated refined itinerary:", refined_itinerary)


# user_message = st.text_input("Refine your plan by asking questions:")
# if user_message:
#     reply = conversation.run(input=user_message)
#     st.write(reply)
