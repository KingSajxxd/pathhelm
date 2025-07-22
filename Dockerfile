# Dockerfile
FROM python:3.11-slim

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# This copies all project files (app/, model.pkl, dashboard.py, etc.)
# into the container's /code/ directory.
COPY . .

# run using uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]