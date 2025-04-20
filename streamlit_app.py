import streamlit as st
# Import necessary Langchain and OpenAI components
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from openai import OpenAI
from functions import *

# --- Configuration ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    googlemaps_api_key = st.secrets["googlemaps_api_key"]
    openweather_api_key = st.secrets["openweather_api_key"]
except KeyError as e:
    st.error(f"Missing secret: {e}. Please configure secrets.")
    st.stop() # Stop execution if secrets are missing

# --- Initialize Session State ---
# Use session state to store history and generation status
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
    st.stop()

# Using LanChain's ChatMessageHistory to save Chat session history
#history = ChatMessageHistory()

# Generating a new prompt template to handle conversation history
conversation_prompt = ChatPromptTemplate.from_messages([("system", "You are a helpful travel planning assistant. Refine the itinerary based on the user's requests and the previous conversation history."),
                                                        ("placeholder", "{history}"), # Use placeholder for Langchain >= 0.1.0
                                                        ("human", "{input}"),
                                                        ])
# Create the chain (do this once)
refine_chain = LLMChain(llm=llm, prompt=conversation_prompt)

def generate_refined_plan(user_input):
    """
    Generates a refined trip plan based on user input by interacting with an AI model and APIs.

    Args:
        user_input (str): The user's input containing trip details or preferences.

    Functionality:
        - Calls an AI model using a predefined chain and prompt to generate a refined itinerary.
        - Updates the conversation history with the user's input and the AI's response.
        - Combines the conversation history and the refined itinerary into a single text.
        - Displays the full conversation and refined itinerary in the Streamlit app.

    Streamlit Outputs:
        - A message indicating that the refined trip plan is being generated.
        - A text area displaying the full conversation and refined itinerary.

    Note:
        This function assumes the existence of `LLMChain`, `get_refined_reply`, and `history` objects, 
        as well as a Streamlit (`st`) environment for displaying outputs.
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

def render_input_form():
    """Renders the input form elements and returns their values."""
    st.markdown("### Enter Your Trip Details")
    with st.form(key='trip_input_form'):
        destination = st.text_input("Enter your destination:")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        budget = st.number_input("Enter your budget (£):", min_value=1) # Min value 1
        interests = st.multiselect(
            "Select your interests:",
            ["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"]
        )
        submitted = st.form_submit_button("Generate Plan")
    return submitted, destination, start_date, end_date, budget, interests

def validate_user_inputs(destination, start_date, end_date, budget, interests, gmaps_client):
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

def handle_initial_generation(destination, start_date, end_date, budget, interests, geocode_result, client, gmaps_client, openweather_key):
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

def render_results_and_refinement():
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

def main():
    """
    Main function for the AI Trip Planner Streamlit application.
    Handles UI setup, input, validation, generation, and refinement.
    """
    st.set_page_config(page_title="AI Trip Planner", page_icon=":airplane:", layout="wide")
    st.title("AI Trip Planner")

    # --- Get API Clients (assuming these are initialized globally or passed) ---
    # Ensure gmaps, client, OPENAI_API_KEY, openweather_api_key are accessible here
    # For simplicity, assuming they are available in the scope as per the original code
    # If they are initialized outside main, ensure they are accessible.
    # Example: gmaps_client = gmaps, openai_client = client, etc.

    # --- Input Form ---
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
            handle_initial_generation(destination,
                                      start_date,
                                      end_date,
                                      budget,
                                      interests,
                                      geocode_result,
                                      client, # Pass the initialized OpenAI client
                                      gmaps,  # Pass the initialized Google Maps client
                                      openweather_api_key) # Pass the weather API key

    # --- Display Itinerary and Refinement Section ---
    # This part runs on every interaction if an itinerary exists
    render_results_and_refinement()

# --- Run the App ---
if __name__ == "__main__":
    # Ensure necessary clients/keys are initialized before main() if needed globally
    # Example initialization (should match your actual setup)
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        googlemaps_api_key = st.secrets["googlemaps_api_key"]
        openweather_api_key = st.secrets["openweather_api_key"]
        llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=OPENAI_API_KEY)
        client = OpenAI(api_key=OPENAI_API_KEY)
        gmaps = googlemaps.Client(key=googlemaps_api_key)
        # Initialize history and other session state defaults if not done elsewhere
        if 'history' not in st.session_state:
            st.session_state.history = ChatMessageHistory()
        if 'itinerary_generated' not in st.session_state:
            st.session_state.itinerary_generated = False
        if 'current_itinerary' not in st.session_state:
            st.session_state.current_itinerary = "" # Store the latest itinerary text

        # Setup refine_chain (assuming it depends on llm and prompt defined globally/outside main)
        conversation_prompt = ChatPromptTemplate.from_messages([("system", "You are a helpful travel planning assistant.You are given a list of places to visit and a budget. Refine the itinerary based on the user's requests and the previous conversation history."),
                                                                ("placeholder", "{history}"),
                                                                ("human", "{input}"),
        ])
        refine_chain = LLMChain(llm=llm, prompt=conversation_prompt)

        # Call main
        main()

    except KeyError as e:
        st.error(f"Missing secret: {e}. Please configure secrets.")
        st.stop() # Stop execution if secrets are missing
    except Exception as e:
        st.error(f"Error during initialization or execution: {e}")
        st.stop()