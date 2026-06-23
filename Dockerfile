FROM python:3.11-slim

# Install ffmpeg system-wide (used by pydub on Linux)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]