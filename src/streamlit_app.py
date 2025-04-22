"""
AI Trip Planner Streamlit Application
This Streamlit application serves as an AI-powered trip planner that allows users to input 
their travel preferences and generates a customized itinerary. Users can refine the itinerary 
based on their feedback, leveraging OpenAI's GPT model and external APIs like Google Maps 
and OpenWeather.
Modules and Functions:
----------------------
1. **generate_refined_plan(user_input)**:
    - Refines the trip itinerary based on user input and conversation history.
    - Updates session state with the refined itinerary and conversation history.
2. **render_input_form()**:
    - Renders a form for users to input trip details such as destination, dates, budget, 
      and interests.
    - Returns the user inputs and a submission flag.
3. **validate_user_inputs(destination, start_date, end_date, budget, interests, gmaps_client)**:
    - Validates user inputs for destination, travel dates, budget, and interests.
    - Uses Google Maps API to validate the destination city.
    - Returns a list of errors (if any) and geocoding results.
4. **handle_initial_generation(destination, start_date, end_date, budget, interests, geocode_result, client, gmaps_client, openweather_key)**:
    - Generates the initial itinerary using user inputs and external APIs.
    - Updates session state with the generated itinerary and resets conversation history.
5. **render_results_and_refinement()**:
    - Displays the generated itinerary and provides a section for users to refine the plan.
    - Handles user input for refinement and triggers the refinement process.
6. **main()**:
    - Entry point for the Streamlit application.
    - Configures the page layout, handles user input, validates inputs, generates the initial 
      itinerary, and provides options for refinement.
-------------
- Streamlit: For UI rendering and interaction.
- LangChain: For managing conversation history and prompt templates.
- OpenAI: For generating itineraries using GPT models.
- Google Maps API: For geocoding and validating destination cities.
- OpenWeather API: For weather-related data in the itinerary.
-------------------
- `history`: Stores the conversation history between the user and the AI.
- `itinerary_generated`: Boolean flag indicating whether an itinerary has been generated.
- `current_itinerary`: Stores the latest generated or refined itinerary.
- `refine_input`: Stores the user's refinement request.
Error Handling:
---------------
- Missing API keys or secrets are handled gracefully with error messages.
- Input validation ensures that invalid or incomplete inputs are flagged before processing.
- External API errors are caught and displayed to the user.
Usage:
------
1. Run the application using Streamlit.
2. Input trip details in the form and submit.
3. View the generated itinerary and refine it as needed.
4. Interact with the AI to customize the trip plan further.
"""
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

# Import necessary libraries
import streamlit as st
# Import necessary Langchain and OpenAI components
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from openai import OpenAI
from functions import *

# --- Global Configuration & Initialization ---
try:
    # --- Configuration ---
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        googlemaps_api_key = st.secrets["googlemaps_api_key"]
        openweather_api_key = st.secrets["openweather_api_key"]
    except KeyError as e:
        st.error(f"Missing secret: {e}. Please configure secrets.")
        st.stop() # Stop execution if secrets are missing

    # --- Initialize Session State ---
    # Use session state to store history and generation status (runs only once per session)
    if 'history' not in st.session_state:
        st.session_state.history = ChatMessageHistory()
    if 'itinerary_generated' not in st.session_state:
        st.session_state.itinerary_generated = False
    if 'current_itinerary' not in st.session_state:
        st.session_state.current_itinerary = "" # Store the latest itinerary text

    # --- LLM and Prompt Setup ---
    # Using OpenAI "gpt-3.5-turbo-0125" model
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=OPENAI_API_KEY)
        client = OpenAI(api_key=OPENAI_API_KEY) # OpenAI client for other potential uses
        gmaps = googlemaps.Client(key=googlemaps_api_key) # Google Maps client
    except Exception as e:
        st.error(f"Error initializing API clients: {e}")
        st.stop() # Stop execution if clients fail to initialize

    # Generating a new prompt template to handle conversation history
    conversation_prompt = ChatPromptTemplate.from_messages([("system", "You are a helpful travel planning assistant. Refine the itinerary based on the user's requests and the previous conversation history."),
                                                            ("placeholder", "{history}"), # Use placeholder for Langchain >= 0.1.0
                                                            ("human", "{input}"),
                                                            ])
    
    # Create the chain (do this once)
    refine_chain = LLMChain(llm=llm, prompt=conversation_prompt)

except KeyError as e:
    st.error(f"CRITICAL ERROR: Missing secret: {e}. Please configure secrets in Streamlit.")
    st.stop() # Stop execution if secrets are missing during initial load
except Exception as e:
    st.error(f"CRITICAL ERROR during initialization: {e}")
    st.stop() # Stop execution on other critical init errors   

#-----------------------------------------generate_refined_plan()--------------------------------------------------------------------------------------------------------------
# Function to generate a refined trip plan based on user input
def generate_refined_plan(user_input):
    """
    Generates a refined trip plan based on user input and conversation history.
    This function interacts with an AI model or API to refine a trip itinerary. 
    It uses the session state to maintain conversation history and updates the 
    current itinerary. The refined itinerary is displayed to the user.
    Args:
        user_input (str): The user's input or request for refining the trip plan.
    Workflow:
        1. Retrieves the conversation history from the session state.
        2. Invokes the refinement chain with the history and user input.
        3. Extracts the refined itinerary from the chain's response.
        4. Updates the session state with the user's input and AI's response.
        5. Updates the current itinerary in the session state.
        6. Displays the refined itinerary to the user.
    Notes:
        - Ensure that `refine_chain` is properly initialized and compatible with 
          the expected input/output format.
        - The session state must have `history` and `current_itinerary` keys 
          initialized before calling this function.
        - Optional: Uncomment the section to display the full conversation history.
    Raises:
        KeyError: If required keys are missing in the session state.
        Exception: If the refinement chain invocation fails or returns an unexpected response.
    """
    # Call the AI model and APIs here
    with st.spinner("Generating your refined trip plan..."):

        # Use history from session state
        history_langchain_format = st.session_state.history.messages

        # Get refined reply using the chain
        # Note: Ensure get_refined_reply is adapted if needed, or use the chain directly
        # refined_itinerary = get_refined_reply(refine_chain, user_input, history_langchain_format) # If get_refined_reply is a wrapper
        # Or directly invoke the chain:
        response = refine_chain.invoke({"history": history_langchain_format,"input": user_input})
        
        refined_itinerary = response['text'] # Adjust based on actual chain output key

        # Add user input and AI response to session state history
        st.session_state.history.add_user_message(user_input)
        st.session_state.history.add_ai_message(refined_itinerary)

        # Update the current itinerary in session state
        st.session_state.current_itinerary = refined_itinerary

        # Display the latest refined itinerary (optional: display full history too)
        st.markdown("### Refined Itinerary")
        st.write(st.session_state.current_itinerary)

        # Optional: Display full conversation history
        # st.markdown("### Full Conversation History")
        # full_conversation = "\n\n".join([f"User: {msg.content}" if msg.type == 'human' else f"AI: {msg.content}"
        #                                  for msg in st.session_state.history.messages])
        # st.text_area("Conversation History", full_conversation, height=300, key="conversation_history_display")        

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
    """Renders the input form elements and returns their values."""
    st.markdown("### Enter Your Trip Details")
    with st.form(key='trip_input_form'):
        destination = st.text_input("Enter your destination:")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        budget = st.number_input("Enter your budget (£):", min_value=1) # Min value 1
        interests = st.multiselect("Select your interests:",
                                   ["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"])
        submitted = st.form_submit_button("Generate Plan")
    return submitted, destination, start_date, end_date, budget, interests

# ----------------------------------------validate_user_inputs()--------------------------------------------------------------------------------------------------------------
# Function to validate user inputs
def validate_user_inputs(destination, start_date, end_date, budget, interests, gmaps_client):
    """
    Validates user inputs for a travel planning application.

    This function checks the validity of the provided destination, travel dates, budget, 
    and interests. It also attempts to geocode the destination using the provided Google 
    Maps client to ensure it is a valid city.

    Args:
        destination (str): The name of the destination city.
        start_date (datetime.date): The start date of the trip.
        end_date (datetime.date): The end date of the trip.
        budget (float): The budget for the trip. Must be greater than zero.
        interests (list): A list of user-selected interests for the trip.
        gmaps_client (googlemaps.Client): A Google Maps client instance for geocoding.

    Returns:
        tuple: A tuple containing:
            - errors (list): A list of error messages, if any validation checks fail.
            - geocode_result (dict or None): The geocoding result for the destination 
              if it is valid, otherwise None.
    """
    """Validates the user inputs and returns a list of errors and geocode result."""
    errors = []
    geocode_result = None

    if not destination:
        errors.append("Please enter a destination.")
    if not start_date or not end_date:
        errors.append("Please select start and end dates.")
    elif start_date > end_date:
        errors.append("Start date must be before end date.")
    if budget <= 0:
        errors.append("Budget must be greater than zero.")
    if not interests:
        errors.append("Please select at least one interest.")

    # Only attempt geocoding if destination is provided and other basic checks pass
    if destination and not errors:
        try:
            geocode_result = is_valid_city(destination, gmaps_client)
            if not geocode_result:
                errors.append("Invalid destination. Please enter a valid city name.")
        except Exception as e: # Consider more specific exceptions if known
            st.error(f"Error validating destination: {e}") # Show immediate error for API issues
            errors.append(f"Could not validate destination: {destination}.") # Add to list

    return errors, geocode_result

# ----------------------------------------handle_initial_generation()--------------------------------------------------------------------------------------------------------------
# Function to handle the initial itinerary generation
def handle_initial_generation(destination, start_date, end_date, budget, interests, geocode_result, client, gmaps_client, openweather_key):
    """
    Generates the initial itinerary for a trip, handles potential errors, and updates the session state.

    This function interacts with external services to generate a travel itinerary based on the provided
    parameters. It also manages session state updates and error handling to ensure a smooth user experience.

    Args:
        destination (str): The destination for the trip.
        start_date (str): The start date of the trip in 'YYYY-MM-DD' format.
        end_date (str): The end date of the trip in 'YYYY-MM-DD' format.
        budget (float): The budget for the trip.
        interests (list): A list of user interests to tailor the itinerary.
        geocode_result (list): Geocoding result containing location data for the destination.
        client (object): The client object for interacting with the itinerary generation service.
        gmaps_client (object): The Google Maps client for geocoding and location data.
        openweather_key (str): The API key for accessing OpenWeather services.

    Raises:
        Exception: Catches and displays any errors that occur during itinerary generation.

    Session State Updates:
        - `st.session_state.itinerary_generated` (bool): Indicates whether the itinerary was successfully generated.
        - `st.session_state.history` (ChatMessageHistory): Resets and updates the chat history with the new itinerary.
        - `st.session_state.current_itinerary` (str): Stores the generated itinerary.

    Notes:
        - If location data cannot be extracted from `geocode_result`, the function stops execution and displays an error.
        - Ensure that all required external services (e.g., Google Maps, OpenWeather) are properly configured.
    """
    """Generates the initial itinerary, handles errors, and updates session state."""
    with st.spinner("Generating your trip plan..."):
        try:
            # Extract location data safely
            if not geocode_result or not geocode_result[0].get('geometry', {}).get('location'):
                 st.error("Could not extract location data for the destination.")
                 st.session_state.itinerary_generated = False
                 return # Stop generation if location is missing

            location = geocode_result[0]['geometry']['location']

            itinerary = generate_itinerary(destination,
                                           start_date,
                                           end_date,
                                           budget,
                                           interests,
                                           location,
                                           client,
                                           gmaps_client,
                                           openweather_key)

            # --- Update Session State ---
            st.session_state.history = ChatMessageHistory() # Reset history for a new plan
            st.session_state.history.add_ai_message(itinerary)
            st.session_state.itinerary_generated = True
            st.session_state.current_itinerary = itinerary

        except Exception as e: # Consider more specific exceptions
            st.error(f"Error generating itinerary: {e}")
            st.session_state.itinerary_generated = False # Ensure flag is false on error

# ----------------------------------------render_results_and_refinement()--------------------------------------------------------------------------------------------------------------
# Function to render the results and refinement section
def render_results_and_refinement():
    """
    Displays the generated itinerary and provides a section for users to refine the plan.

    This function checks if an itinerary has been generated by verifying the 
    `itinerary_generated` flag in the session state. If the flag is set, it displays 
    the current itinerary and provides a text input field for users to request changes 
    to the plan. Users can submit their refinement requests using a button, which 
    triggers the refinement process.

    Key Features:
    - Displays the AI-generated itinerary stored in the session state.
    - Provides a text input field for users to specify changes to the itinerary.
    - Includes a button to trigger the refinement process.
    - Validates user input and displays a warning if no input is provided.

    Session State Keys:
    - `itinerary_generated` (bool): Indicates whether an itinerary has been generated.
    - `current_itinerary` (str): Stores the current itinerary to be displayed.
    - `refine_input` (str): Stores the user's refinement request.

    Dependencies:
    - `generate_refined_plan(user_input_refine)`: A function that processes the user's 
        refinement request and updates the itinerary.

    Returns:
            None
    """
    """Displays the generated itinerary and the refinement section."""
    if not st.session_state.get('itinerary_generated', False):
        return

    st.markdown("### Your AI-generated itinerary")
    # Display the current itinerary safely using .get
    st.write(st.session_state.get('current_itinerary', "No itinerary generated yet."))

    st.markdown("---") # Separator
    st.markdown("### Refine Your Plan")
    # Use a unique key for the text input to avoid conflicts
    user_input_refine = st.text_input("Ask for changes (e.g. 'Add more food experiences on Day 2'):",key="refine_input")

    # Use the button click as the trigger
    if st.button("Refine Plan", key="refine_button"):
        if user_input_refine: # Check if there is input before refining
            # Call the refinement function (which uses session state)
            generate_refined_plan(user_input_refine)
        else:
            st.warning("Please enter your requested changes before refining.")

# ----------------------------------------main()--------------------------------------------------------------------------------------------------------------
# Main function to run the Streamlit app
def main():

    """
    This is the Main function for the AI Trip Planner Streamlit application.
    This function serves as the entry point for the Streamlit application. It sets up the 
    user interface, handles user input, validates the input, generates an initial itinerary, 
    and provides options for refining the itinerary.

    Key Features:
    - Configures the Streamlit page with a title, icon, and layout.
    - Displays an input form for users to provide trip details such as destination, dates, 
        budget, and interests.
    - Validates user inputs using external services like Google Maps and handles errors 
        gracefully.
    - Generates an initial trip itinerary using OpenAI's API and other external services 
        like Google Maps and OpenWeather.
    - Displays the generated itinerary and provides options for further refinement.

    Dependencies:
    - Streamlit for UI rendering and interaction.
    - External API clients (Google Maps, OpenAI, OpenWeather) for geocoding, itinerary 
        generation, and weather data.

    Parameters:
    None

    Returns:
    None
    """
    st.set_page_config(page_title="AI Trip Planner", page_icon=":airplane:", layout="wide")
    st.title("AI Trip Planner")

    # --- Get API Clients (assuming these are initialized globally or passed) ---
    # Ensure gmaps, client, OPENAI_API_KEY, openweather_api_key are accessible here
    # For simplicity, assuming they are available in the scope as per the original code
    # If they are initialized outside main, ensure they are accessible.
    # Example: gmaps_client = gmaps, openai_client = client, etc.

    # --- Input Form ---
    # Uses globally initialized gmaps, client, openweather_api_key   
    submitted, destination, start_date, end_date, budget, interests = render_input_form()

    # --- Handle Form Submission ---
    if submitted:
        # --- Input Validation ---
        # Pass the initialized gmaps client to the validation function
        errors, geocode_result = validate_user_inputs(destination, start_date, end_date, budget, interests, gmaps)

        if errors:
            for error in errors:
                st.error(error)
            # Reset generation flag if validation fails after a successful generation
            st.session_state.itinerary_generated = False
            st.session_state.current_itinerary = ""
        else:
            # --- Generate Initial Itinerary ---
            # Pass the globally initialized clients and keys
            handle_initial_generation(destination,
                                      start_date,
                                      end_date,
                                      budget,
                                      interests,
                                      geocode_result,
                                      client, # Global OpenAI client
                                      gmaps,  # Global Google Maps client
                                      openweather_api_key) # Global OpenWeather API key

    # --- Display Itinerary and Refinement Section ---
    # This part runs on every interaction if an itinerary exists
    render_results_and_refinement()

# --- Run the App ---
if __name__ == "__main__":
    #Call main function to run the Streamlit app
    main()
# --- End of Streamlit App ---