# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./src /app

RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

CMD ["python", "main.py"]
