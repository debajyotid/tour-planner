import streamlit as st

from openai import OpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from functions import *

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
googlemaps_api_key = st.secrets["googlemaps_api_key"]
openweather_api_key = st.secrets["openweather_api_key"]

# Using LanChain's ChatMessageHistory to save Chat session history
history = ChatMessageHistory()

# Using OpenAI "gpt-3.5-turbo-0125" model to generate the itinenary
llm = ChatOpenAI(model="gpt-3.5-turbo-0125",temperature=0,api_key=OPENAI_API_KEY)

# Generating a new prompt template to handle conversation history
conversation_prompt = ChatPromptTemplate.from_messages([("system", "You are a helpful travel planning assistant. Refine the itinerary as per the user's requests."),
                                                        ("ai", "{history}"),
                                                        ("human", "{input}"),])

def main():
    """
    Main function for the AI Trip Planner Streamlit application.

    This function creates a user interface for planning trips using AI. 
    Users can input their trip details, such as destination, dates, budget, 
    and interests, and generate an itinerary. They can also refine the 
    itinerary by providing feedback.

    Features:
    - Input fields for destination, start date, end date, budget, and interests.
    - Button to generate an AI-based trip itinerary.
    - Text input for user feedback to refine the itinerary.
    - Button to generate a refined itinerary based on user feedback.

    Note:
    - The `generate_itinerary` function is used to create the initial itinerary.
    - The `get_refined_reply` function is used to refine the itinerary based on user input.
    - The `history` object is used to maintain the conversation context.
    """

    st.title("AI Trip Planner")
    destination = st.text_input("Enter your destination:")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    budget = st.number_input("Enter your budget (£):", min_value=0)
    interests = st.multiselect("Select your interests:",["Nature", "History", "Food", "Adventure", "Shopping", "Relaxation"])

    if st.button("Generate Plan"):
        # Call the AI model and APIs here
        st.write("Generating your trip plan...")
        client = OpenAI(api_key=OPENAI_API_KEY)
        if not googlemaps_api_key:
            raise ValueError("Google Maps API key is missing.")
        gmaps = googlemaps.Client(key=googlemaps_api_key)
        itinerary = generate_itinerary(destination, start_date, end_date, budget, interests, client, gmaps, openweather_api_key)
        # Passing the generated itinenary to the Chat history
        history.add_ai_message(itinerary)
        #st.text_area("Your AI-generated itinerary:", itinerary)
        st.markdown("### Your AI-generated itinerary")
        st.write(itinerary)

    # User feedback box
    user_input = st.text_input("Ask for changes (e.g. 'Add more food experiences on Day 2'):")

    if st.button("Refine Plan") and user_input:
            # Call the AI model and APIs here
            st.write("Generating your refined trip plan...")
            chain = LLMChain(llm=llm, prompt=conversation_prompt)
            refined_itinerary = get_refined_reply(chain, user_input, history)
            # st.text_area("Your AI-generated refined itinerary:", refined_itinerary)
            st.markdown("### Your AI-generated refined itinerary")
            st.write(refined_itinerary)

if __name__ == "__main__":
    main()     
