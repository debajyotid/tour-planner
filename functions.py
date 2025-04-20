
import googlemaps
import requests

def get_attractions(destination, googlemapsapi):
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

def get_weather(destination,api_key):
    """Fetches the current weather description for a given destination using the OpenWeatherMap API.

        destination (dict): A dictionary containing the latitude ('lat') and longitude ('lng') of the destination.
        api_key (str): The API key required to authenticate with the OpenWeatherMap API.

             If weather data is unavailable, returns "Weather data not available."

    Raises:
        KeyError: If the expected keys are missing in the API response.
        requests.exceptions.RequestException: If there is an issue with the network or the API request.

    Note:
        - This function assumes the API key is securely stored and passed correctly.
        - Requires the 'requests' library to be installed and imported."""

    url = f"http://api.openweathermap.org/data/2.5/weather?lat={destination['lat']}&lon={destination['lng']}&appid={api_key}"
    response = requests.get(url).json()
    if response.get('weather'):
        return response['weather'][0]['description']
    else:
        return "Weather data not available."

def generate_itinerary(destination, start_date, end_date, budget, interests, openaiclient, gmapsclient, openweather_api_key):
    """Generates a day-by-day travel itinerary for a specified destination, date range, budget, and interests.

    Args:
        destination (str): The name of the destination for the trip.
        start_date (str): The start date of the trip in YYYY-MM-DD format.
        end_date (str): The end date of the trip in YYYY-MM-DD format.
        budget (float): The budget for the trip in GBP (£).
        interests (list of str): A list of interests to focus on during the trip (e.g., "history", "adventure").

    Returns:
        str: A detailed day-by-day itinerary as a string, considering the destination's tourist attractions,
             weather forecast, and user preferences.

    Raises:
        ValueError: If the destination cannot be geocoded.

    Notes:
        - Uses Google Maps API to fetch latitude and longitude for the destination.
        - Retrieves tourist attractions and weather forecast using external APIs.
        - Leverages OpenAI's GPT model to generate the itinerary based on the provided inputs."""

    # Generating the latitude and longitudes for the chosen destination using GoogleMaps APIs
    geocode_result = gmapsclient.geocode(destination)
    if not geocode_result:
        raise ValueError(f"Could not geocode destination: {destination}")
    location = geocode_result[0]['geometry']['location']

    # Fetching the tourist attractions for the destination
    tourist_attraction = get_attractions(location, gmapsclient)


    # Fetching the weather forecast for the destination
    weather_forecast = get_weather(location, openweather_api_key)

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
    response = openaiclient.chat.completions.create(model="gpt-3.5-turbo-0125",
                                                    messages=[
                                                                {
                                                                    "role": "developer",
                                                                    "content": prompt
                                                                }
                                                            ],
                                                    max_tokens=1000,
                                                    temperature=0)
    return response.choices[0].message.content

# Function to refine the itinerary based on user's requests
def get_refined_reply(chain, user_input, history):
    """
    Refines a travel itinerary based on user input and conversation history.
    Args:
        user_input (str): The latest request or input from the user.
        history (ConversationHistory): An object that stores the conversation history, 
            including messages from both the user and the AI.
    Returns:
        str: The refined travel itinerary generated by the AI.
    Functionality:
        - Constructs a prompt template for refining the itinerary based on the user's 
          requests and the conversation history.
        - Updates the conversation history with the user's latest input.
        - Formats the conversation history into a structured format for the AI model.
        - Uses an LLMChain to process the prompt and generate a refined itinerary.
        - Updates the conversation history with the AI's response.
    """
    
    # Add the user's new request to memory
    history.add_user_message(user_input)

    # Format the conversation so far
    conversation = "\n".join(f"{'User' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in history.messages)

    # Create the chain and run it
    refined_itinerary = chain.run(history=conversation, input=user_input)
    history.add_ai_message(refined_itinerary)
    return refined_itinerary