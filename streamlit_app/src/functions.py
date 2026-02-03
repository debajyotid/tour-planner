
# Import necessary libraries
# Import necessary libraries
import math
import streamlit as st
import googlemaps
from googlemaps import exceptions
import googlemaps
import requests
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
# ----------------------------------------render_input_form()--------------------------------------------------------------------------------------------------------------
# Function to render the input form for trip details
def render_input_form():
    """
    Renders an input form for trip details using Streamlit and returns the user inputs.
    Returns:
        tuple: A tuple containing the following elements:
            - submitted (bool): Indicates whether the form was submitted.
            - destination (str): The destination entered by the user.
            - start_date (datetime.date): The start date of the trip.
            - end_date (datetime.date): The end date of the trip.
            - budget (int): The budget entered by the user in pounds (£).
            - interests (list of str): A list of selected interests from the predefined options.
    """
    st.markdown("### Enter Your Trip Details")
    with st.form(key='trip_input_form'):
        destination = st.text_input("Enter your destination:")
        no_of_adults = st.number_input("Number of adults:", min_value=1, step=1, format="%d") # Min value 1 adult
        no_of_children = st.number_input("Number of children:", min_value=0, step=1, format="%d")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        budget = st.number_input("Enter your budget in pounds(£):", min_value=100, step=50, format="%d") # Min value £100
        interests = st.multiselect("Select your interests:",["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"])
        # New accommodation preferences section
        st.markdown("### Accommodation Preferences")
        accommodation_type = st.multiselect("Preferred accommodation types:", ["Hotel", "Hostel", "Apartment", "Guesthouse", "Resort"])
        accommodation_rating = st.slider("Minimum accommodation rating:", 1.0, 5.0, 3.0, 0.5)
        show_hotels = st.checkbox("Show available hotel options within budget", value=True)
        submitted = st.form_submit_button("Generate Plan")
    return (
        submitted,
        destination,
        no_of_adults,
        no_of_children,
        start_date,
        end_date,
        budget,
        interests,
        accommodation_type,
        accommodation_rating,
        show_hotels,
    )
# Check if the destination is a valid city
# Validate the destination using a placeholder function
def is_valid_city(city, gmapsclient):
    """
    Validates if a given city is valid by attempting to geocode it using the Google Maps API.
    Args:
        city (str): The name of the city to validate.
        gmapsclient (googlemaps.Client): An instance of the Google Maps API client.
    Returns:
        bool: True if the city is valid (can be geocoded), False otherwise.
    """
    try:
        # Attempt to geocode the city
        if gmapsclient is None:
            return False
        result = gmapsclient.geocode(city)
    return result is not None and len(result) > 0
except Exception:  # Catch any exception during geocoding
    return False
def get_attractions(destination, gmapsclient):
    """Fetches a list of tourist attractions near a given destination using the Google Maps API.
    Args:
        destination (dict): A dictionary containing latitude ('lat') and longitude ('lng') of the destination.
    Returns:
        list[str]: A list of names of tourist attractions near the destination.
                 Returns an empty list if no attractions are found.
    Raises:
        googlemaps.exceptions.ApiError: If there is an issue with the Google Maps API request.
        ValueError: If the destination cannot be geocoded.
        KeyError: If the API key is not found in Streamlit secrets.
    Note:
        This function requires the 'googlemaps' and 'streamlit' libraries to be installed
        and a valid Google Maps API key stored in Streamlit secrets under the key
        "googlemaps_api_key".
    """
    if isinstance(destination, str):
        # If destination is a string, geocode it first
        try:
            geocode_result = gmapsclient.geocode(destination)
            if not geocode_result:
                raise ValueError("Could not geocode destination")
            lat_lng = (geocode_result[0]['geometry']['location']['lat'], geocode_result[0]['geometry']['location']['lng'])
        except Exception as e:
            raise ValueError(f"Could not geocode destination {destination}: {e}")
    else:
        # Destination is already a dict with lat/lng
        lat_lng = (destination['lat'], destination['lng'])

    # Using the "places_nearby" API to get tourist attractions, within a 5000m radius, of the latitude-longitude of the chosen destination
    try:
        places_result = gmapsclient.places_nearby(location=lat_lng, radius=5000, type='tourist_attraction', rank_by='prominence', language='en')
        return [place['name'] for place in places_result['results']]
    except Exception:
        return []
def get_accommodations(destination, gmapsclient):
    """
    Fetches accommodation options near a given destination using the Google Maps API.
    
    Args:
        destination (dict): A dictionary containing the latitude ('lat') and longitude ('lng') of the destination, or a string name.
        gmapsclient (googlemaps.Client): An instance of the Google Maps API client.
        budget_per_night (float, optional): Maximum budget per night in pounds (£).
        
    Returns:
        list: A list of dictionaries containing information about accommodation options.
             Each dictionary includes 'name', 'rating', 'price_level', 'vicinity', and 'types'.
   
    Note:
        This function requires the 'googlemaps' and 'streamlit' libraries to be installed
        and a valid Google Maps API key stored in Streamlit secrets under the key
        "googlemaps_api_key".
    """
    try:
        # First, check if destination is a string (name) and geocode if needed
        if isinstance(destination, str):
            geocode_result = gmapsclient.geocode(destination)
            if not geocode_result:
                raise ValueError("Could not geocode destination")
            lat_lng = (geocode_result[0]['geometry']['location']['lat'], geocode_result[0]['geometry']['location']['lng'])
        else:
            lat_lng = (destination['lat'], destination['lng'])
            
    # Using places_nearby to get accommodation options within a 5000m radius
    accommodations_result = gmapsclient.places_nearby(location=lat_lng, radius=5000, type='lodging', rank_by='prominence',language='en')
    
    accommodations = []
    for place in accommodations_result['results']:
        accommodation = {'name': place['name'],
                        'rating': place.get('rating', 'Not rated'),
                        'price_level': place.get('price_level', 'Price not available'),
                        'vicinity': place.get('vicinity', 'Address not available'),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'types': place.get('types', [])
                        }
        accommodations.append(accommodation)
    
        return accommodations
def get_available_hotels(destination, start_date, end_date, budget, total_travelers, gmaps_client, accommodation_type, accommodation_rating):
    """
    try:
        # Calculate trip duration
        trip_duration = (end_date - start_date).days
        if trip_duration <= 0:
            trip_duration = 1
        
        # Calculate budget breakdown
        budget_breakdown = {
            'food': budget * 0.2,
            'local_travel': budget * 0.3,
            'tickets': budget * 0.2,
            'lodging_budget': budget * 0.3
        }
        
        # Get available hotels (simplified - in real app, would integrate with hotel APIs)
        available_hotels = []
        return available_hotels, budget_breakdown, trip_duration
    except Exception as e:
        return [], {}, 1
def get_weather_data(destination, gmaps_client):
    """
    Gets weather data for destination (placeholder)
    """
    return "sunny"
def get_refined_reply(chain, user_input, history):
    """
    Refines a travel itinerary based on user input and conversation history.
    Args:
        user_input (str): The latest request or input from the user.
        history (list): An object that stores the conversation history, 
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
    
    # Format the conversation so far
    if not history:
        return ""
    conversation = "\n".join(f"{'User' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in history.messages)
    response = chain.run(history=conversation, input=user_input)
    return response
def generate_itinerary(destination, no_of_adults, no_of_children, start_date, end_date, budget, interests, location, client, gmaps_client, openweather_key, available_hotels=None, budget_breakdown=None, trip_duration=None):
    """
    Generates a complete itinerary for the trip.
    """
    try:
    """
    try:
        # Calculate trip duration
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        duration = (end_date - start_date).days
        
        # Fetching the tourist attractions for the destination
        tourist_attraction = get_attractions(location, gmaps_client)

        # Fetching the weather forecast for the destination
        try:
            # Simplified weather API call - in practice this would call an actual weather API
            weather_forecast = get_weather_data(location, gmaps_client)
        except Exception as e:
            print(f"Warning: Could not fetch weather data: {e}")
            weather_forecast = "Weather data not available"

        # Get accommodation options
        accommodations = available_hotels if available_hotels is not None else get_accommodations(location, gmaps_client)

        # Format attractions for the prompt (handle case where attractions may be empty)
        attractions_text = ", ".join(tourist_attraction) if tourist_attraction else "No specific attractions found"

        # Prepare accommodation text for prompt
        accommodation_text = ""
        if accommodations:
            accommodation_text = "Consider these accommodation options (sorted by reviews):\n"
            for i, acc in enumerate(accommodations[:5], 1):  # Limit to top 5 options
                price_level = "£" * acc.get('price_level', 1) if isinstance(acc.get('price_level'), int) else "Price unknown"
                nightly = acc.get("estimated_nightly_rate")
                total_stay = acc.get("estimated_total_stay_cost")
                cost_text = ""
                if nightly and total_stay and trip_duration:
                    cost_text = f", Est. £{nightly}/night, Est. total £{total_stay:.0f} for {trip_duration} nights"
                accommodation_text += f"{i}. {acc['name']} - Rating: {acc['rating']}, Reviews: {acc.get('user_ratings_total', 0)}, Price Level: {price_level}, Location: {acc['vicinity']}{cost_text}\n"
        
        if budget_breakdown:
            accommodation_text += (
                f"\nBudget guide: lodging budget ≈ £{budget_breakdown['lodging_budget']:.0f} "
                f"after allocating food (£{budget_breakdown['food']:.0f}), local travel (£{budget_breakdown['local_travel']:.0f}), "
                f"and tickets (£{budget_breakdown['tickets']:.0f}).\n"
            )

        prompt = f"""
    You are a helpful tour planner.
    Create a day-by-day itinerary, within 1000 words or less,
    for a trip to {destination},
    for {no_of_adults} adults and {no_of_children} children,
    from {start_date} to {end_date},
    within a budget of £{budget}, and 
    with focus on the below interests {', '.join(interests)}.
    Include places like, {attractions_text}, in the itinerary and
    factor the forecasted weather, like {weather_forecast} while building the itinerary.
    {accommodation_text}
    
    """
        # Added budget anchoring in the prompt template to ensure the model adheres to the budget constraint.
        prompt += f"STRICT RULE: Total cost MUST NOT exceed £{budget}. Prioritize free/cheap options first."  
        response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
                                                  messages=[
                                                              {
                                                                  "role": "developer",
                                                                  "content": prompt
                                                              }
                                                          ],
                                                  max_tokens=1000,
                                                  temperature=0)
        return response.choices[0].message.content, prompt
    except Exception as e:
        raise Exception(f"Error generating itinerary: {e}")
def suggest_accommodations(destination, start_date, end_date, total_budget, num_travelers, gmapsclient):
# def get_refined_reply(chain, user_input, history):
#     """
#     Refines a travel itinerary based on user input and conversation history.
#     Args:
#         user_input (str): The latest request or input from the user.
#         history (ConversationHistory): An object that stores the conversation history, 
#             including messages from both the user and the AI.
#     Returns:
#         str: The refined travel itinerary generated by the AI.
#     Functionality:
#         - Constructs a prompt template for refining the itinerary based on the user's 
#           requests and the conversation history.
#         - Updates the conversation history with the user's latest input.
#         - Formats the conversation history into a structured format for the AI model.
#         - Uses an LLMChain to process the prompt and generate a refined itinerary.
#         - Updates the conversation history with the AI's response.
#     """
    
#     # Add the user's new request to memory
#     history.add_user_message(user_input)
#     # Format the conversation so far
#     conversation = "\n".join(f"{'User' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in history.messages)
#     # Create the chain and run it
#     refined_itinerary = chain.run(history=conversation, input=user_input)
#     history.add_ai_message(refined_itinerary)
#     return refined_itinerary
    else:
        return "Weather data not available."
    
def suggest_accommodations(destination, start_date, end_date, total_budget, num_travelers, gmapsclient):
    """
    Suggests accommodation options based on trip details and budget constraints.
    
    Args:
        destination (dict): A dictionary containing location data.
        start_date (datetime.date): The start date of the trip.
        end_date (datetime.date): The end date of the trip.
        total_budget (float): Total budget for the trip in pounds (£).
        num_travelers (int): Total number of travelers (adults + children).
        gmapsclient (googlemaps.Client): Google Maps API client.
        
    Returns:
        dict: A dictionary containing recommended accommodations and budget allocation info.
    """
    # Calculate trip duration
    trip_duration = calculate_trip_duration(start_date, end_date)

    # Allocate approximately 40-45% of total budget to accommodation after other costs
    accommodation_budget = estimate_other_costs(total_budget)["lodging_budget"]
    budget_per_night = accommodation_budget / trip_duration

    # Adjust for number of travelers (assuming shared rooms)
    room_factor = (num_travelers // 2) + (num_travelers % 2)  # Calculate rooms needed
    budget_per_room = budget_per_night / room_factor

    # Get accommodations
    all_accommodations = get_accommodations(destination, gmapsclient)

    # Filter and categorize accommodations
    budget_options = []
    mid_range_options = []
    luxury_options = []

    # Since Google Places API doesn't provide exact prices, use price_level as a proxy
    for acc in all_accommodations:
        price_level = acc.get('price_level', 2)  # Default to mid-range if not specified

        if price_level in [1, 0]:
            budget_options.append(acc)
        elif price_level == 2:
            mid_range_options.append(acc)
        else:
            luxury_options.append(acc)

    # Determine which category fits the budget
    recommended_category = "budget"
    if budget_per_room >= 150:
        recommended_category = "luxury"
    elif budget_per_room >= 75:
        recommended_category = "mid_range"

    # Select recommendations based on budget category and ratings
    recommendations = []

    if recommended_category == "budget":
        options = budget_options or mid_range_options or luxury_options
    elif recommended_category == "mid_range":
        options = mid_range_options or budget_options or luxury_options
    else:
        options = luxury_options or mid_range_options or budget_options

    # Sort by rating and take top 3
    sorted_options = sorted(options, key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        return {"recommendations": recommendations,
                "budget_info": {"total_budget": total_budget,
                                "accommodation_budget": accommodation_budget,
                                "budget_per_night": budget_per_night,
                                "trip_duration": trip_duration
                                }
                }    

def get_weather(location, api_key):
    """
    Gets weather data for a location (placeholder implementation).
    In a real application, this would call a weather API.
    """
    return "sunny"

def calculate_trip_duration(start_date, end_date):
    """
    Calculates the duration of a trip between two dates.
    """
    try:
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        return (end_date - start_date).days
    except Exception:
        return 1

def estimate_other_costs(budget):
    """
    Estimates costs for food, travel, and tickets based on total budget.
    """
    return {
        'food': budget * 0.2,
        'local_travel': budget * 0.3,
        'tickets': budget * 0.2,
        'lodging_budget': budget * 0.3
    }

# # Function to refine the itinerary based on user's requests
def get_refined_reply(chain, user_input, history):
    """
    """Generates a day-by-day travel itinerary for a specified destination, date range, budget, and interests.

    Args:
        destination (str): The name of the destination for the trip.
        no_of_adults (int): The number of adults traveling.
        no_of_children (int): The number of children traveling.
        start_date (str): The start date of the trip in YYYY-MM-DD format.
        end_date (str): The end date of the trip in YYYY-MM-DD format.
        budget (float): The budget for the trip in GBP (£).
        interests (list of str): A list of interests to focus on during the trip (e.g., "history", "adventure").

    Returns:
        str: A detailed day-by-day itinerary as a string, considering the destination's tourist attractions,
             weather forecast, and user preferences.

    Returns:
        str: A detailed day-by-day itinerary as a string, considering the destination's tourist attractions,
             weather forecast, and user preferences.
    Notes:
        - Uses Google Maps API to fetch latitude and longitude for the destination.
        - Retrieves tourist attractions and weather forecast using external APIs.
        - Leverages OpenAI's GPT model to generate the itinerary based on the provided inputs."""

    # Fetching the tourist attractions for the destination
    tourist_attraction = get_attractions(location, gmapsclient)

    # Fetching the weather forecast for the destination
    weather_forecast = get_weather(location, openweather_api_key)

    # Get accommodation options
    accommodations = available_hotels if available_hotels is not None else get_accommodations(location, gmapsclient)

    # Format accommodations for the prompt
    accommodation_text = ""
    if accommodations:
        accommodation_text = "Consider these accommodation options (sorted by reviews):\n"
        for i, acc in enumerate(accommodations[:5], 1):  # Limit to top 5 options
            price_level = "£" * acc.get('price_level', 1) if isinstance(acc.get('price_level'), int) else "Price unknown"
            nightly = acc.get("estimated_nightly_rate")
            total_stay = acc.get("estimated_total_stay_cost")
            cost_text = ""
            if nightly and total_stay and trip_duration:
                cost_text = f", Est. £{nightly}/night, Est. total £{total_stay:.0f} for {trip_duration} nights"
            accommodation_text += f"{i}. {acc['name']} - Rating: {acc['rating']}, Reviews: {acc.get('user_ratings_total', 0)}, Price Level: {price_level}, Location: {acc['vicinity']}{cost_text}\n"

    if budget_breakdown:
        accommodation_text += (
            f"\nBudget guide: lodging budget ≈ £{budget_breakdown['lodging_budget']:.0f} "
            f"after allocating food (£{budget_breakdown['food']:.0f}), local travel (£{budget_breakdown['local_travel']:.0f}), "
            f"and tickets (£{budget_breakdown['tickets']:.0f}).\n"
        )

    prompt = f"""
    You are a helpful tour planner.
    Create a day-by-day itinerary, within 1000 words or less,
    for a trip to {destination},
    for {no_of_adults} adults and {no_of_children} children,
    from {start_date} to {end_date},
    within a budget of £{budget}, and 
    with focus on the below interests {', '.join(interests)}.
    Include places like, {tourist_attraction}, in the itinerary and
    factor the forecasted weather, like {weather_forecast} while building the itinerary.

    {accommodation_text}
    
    Start the itinerary with a section titled "RECOMMENDED ACCOMMODATION" that lists 1-3 suitable options based on the budget and trip details.
    For each accommodation, include the name, approximate price per night, and a brief explanation of why it's recommended (location to attractions, amenities, etc.)

    """
    # Added budget anchoring in the prompt template to ensure the model adheres to the budget constraint.
    prompt += f"STRICT RULE: Total cost MUST NOT exceed £{budget}. Prioritize free/cheap options first."  

    response = openaiclient.chat.completions.create(model="gpt-3.5-turbo-0125",
                                                    messages=[
                                                                {
                                                                    "role": "developer",
                                                                    "content": prompt
                                                                }
                                                            ],
                                                    max_tokens=1000,
                                                    temperature=0)
    return response.choices[0].message.content, prompt
# # Function to refine the itinerary based on user's requests
def get_refined_reply(chain, user_input, history):
    """
    Refines a travel itinerary based on user input and conversation history.
    Args:
        user_input (str): The latest request or input from the user.
        history (list): A list of conversation messages.
    Returns:
        str: The refined travel itinerary generated by the AI.
    """
    # Format the conversation so far
    conversation = "\n".join(f"{'User' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in history.messages)
    
    # Get refined reply through the chain
    response = chain.run(history=conversation, input=user_input)
    return response
#     return refined_itinerary
    
    # Function to get user feedback on itinerary
def get_user_feedback():
    """
    Function to get user feedback on the itinerary.
    This would typically be integrated with UI elements.
    """
    st.markdown("### How would you like to modify your itinerary?")
    feedback_options = [
        "Make it more budget-friendly",
        "Add more family activities",
        "Include more cultural experiences",
        "Focus on outdoor activities",
        "Modify the schedule",
        "Other (please specify)"
    ]
    user_choice = st.selectbox("Select a modification option:", feedback_options)
    if user_choice == "Other (please specify)":
        custom_input = st.text_input("Please describe your specific request:")
        return custom_input
    return user_choice
