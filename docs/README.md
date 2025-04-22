Building a Smart, AI-powered Trip Planner using OpenAI-Google Maps-OpenWeather APIs and Langchain for Conversational Support
----------------------
This AI-powered trip planner allows users to input their travel preferences and generates a customized itinerary. Users can refine the itinerary 
based on their feedback, leveraging OpenAI's GPT model and external APIs like Google Maps and OpenWeather.

Technical Implementation
----------------------
The system is built using:

1. OpenAI's gpt-3.5-turbo-0125 model for natural language processing
2. LangChain for managing conversation history and context
3. Google Maps API for location and attraction data
4. OpenWeather API for weather forecasts
5. Python libraries: streamlit, pandas, ipywidgets (for the notebook edition)

How It Works
----------------------
- Users input their travel preferences including destination, dates, and interests.
- The system fetches real-time data about local attractions and weather.
- An AI-generated itinerary is created based on all inputs.
- Users can refine the itinerary through natural conversation with the AI

Practical Applications
----------------------
This tool demonstrates the power of combining:

- Large Language Models (LLMs),
- Real-time data integration,
- Conversational AI,
- API orchestration

It is perfect for travel agencies, individual travelers, or anyone looking to plan a detailed, personalized trip.

----------------------

## This repository presents 3 ways of executing the travel planner.

### The 1st is through a streamlit app, and to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   
   ```
   
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
         
Libraries
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

#### Note: You will need to create a secrets.toml file, under a folder .streamlit in your local repository, with the below API Keys
- OPENAI_API_KEY      = API Key for using OpenAI APIs for using the "gpt-3.5-turbo-0125" model
- googlemaps_api_key  = API Key for using Google Map APIs for fetching tourist attractions, within a 5 km radius (parameterizable), around your trip destination
- openweather_api_key = API Key for using OpenWeather APIs for fetching forecasted weather patterns around your trip destination

#### Note: You can also access the above as a ready-to-use webapp via: https://debajyotidas88-aitourplanner.streamlit.app

----------------------


### The 2nd is through a jupyter notebook (currently configured as a Kaggle Notebook), but can be run locally as well

To run the file on your local system, comment the 'kaggle_secrets' codecell and provide your own 
OpenAI, Google Maps, and OpenWeather API Keys for OPENAIKEY, googlemaps_api_key, and openweather_api_key respectively

Libraries
-------------
- LangChain: For managing conversation history and prompt templates.
- OpenAI: For generating itineraries using GPT models.
- Google Maps API: For geocoding and validating destination cities.
- OpenWeather API: For weather-related data in the itinerary.
- ipywidgets: For generating widgets for accepting user inputs at runtime
-------------------
- `history`: Stores the conversation history between the user and the AI.
- `itinerary_generated`: Boolean flag indicating whether an itinerary has been generated.
- `current_itinerary`: Stores the latest generated or refined itinerary.
- `refine_input`: Stores the user's refinement request.

#### Note: You can execute the notebook as a Kaggle Notebook, in which case the API keys will not be needed, otherwise you will need the below API Keys
- OPENAI_API_KEY      = API Key for using OpenAI APIs for using the "gpt-3.5-turbo-0125" model
- googlemaps_api_key  = API Key for using Google Map APIs for fetching tourist attractions, within a 5 km radius (parameterizable), around your trip destination
- openweather_api_key = API Key for using OpenWeather APIs for fetching forecasted weather patterns around your trip destination

----------------------

### Lastly, the 3rd way is through Docker

1.	Build the Docker image and start services: `docker-compose -f docker/docker-compose.yml up --build`
2.	Access the app at `http://localhost:8501`
3.	To stop the containers: Press `Ctrl+C` in the terminal, then run: `docker-compose -f docker/docker-compose.yml down`

Required Environment Variables
-------------------
Replace these in your `.env` file:
- `OPENAI_API_KEY`: Your OpenAI API key
- `googlemaps_api_key`: Google Maps API key
- `openweather_api_key`: OpenWeatherMap API key



