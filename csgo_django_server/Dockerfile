# Dockerfile for mydjangoapp
FROM python:3.11

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose port 8000 for the Django app
EXPOSE 8000

# Run the Django development server with the specified port or default to 8000
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:${PORT:-8000}"]
