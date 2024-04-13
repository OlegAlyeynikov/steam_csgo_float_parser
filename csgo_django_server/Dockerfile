# Dockerfile for Django
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

# Copy the proxies_list.txt file into the container
COPY proxies_list.txt /app/

# Copy the current directory contents into the container at /app
COPY . /app/

# Create and activate a virtual environment
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"

# Expose port 8000 for the Django app
EXPOSE 8000

# Run database migrations and create a superuser
RUN python manage.py migrate

# CMD to launch Django
CMD ["/bin/bash", "-c", "source venv/bin/activate && python manage.py runserver 0.0.0.0:${PORT_DJANGO_SERVER:-8000}"]
