FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p ./storage
EXPOSE 5000
CMD ["python", "main.py"]
