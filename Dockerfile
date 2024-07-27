# Use the official Python image from the Docker Hub
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY src/requirements.txt /app/src/
COPY requirements-dev.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r src/requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy the rest of the application code into the container
COPY . /app/

# Install the web app as a local package
RUN pip install -e src

# # Set up the local database and seed it with test data
# RUN python ./src/fastapi_app/setup_postgres_database.py && \
#     python ./src/fastapi_app/setup_postgres_seeddata.py

# Expose the backend port
EXPOSE 8000

# Run the FastAPI backend with hot reloading
# CMD ["uvicorn", "fastapi_app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload"]
