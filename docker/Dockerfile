# Base image for both services
FROM python:3.9-slim AS base

# Add this before copying secrets.toml
RUN mkdir -p /app/.streamlit

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ..

COPY streamlit_app/config/.streamlit/secrets.toml /app/.streamlit/secrets.toml
EXPOSE 8501
CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]