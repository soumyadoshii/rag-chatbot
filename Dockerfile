#FROM python:3.12
FROM python:3.12-slim
ARG UID=1002
ARG GID=1003
RUN groupadd -r -g $GID appgroup && useradd -r -u $UID -g appgroup -d /home/appuser -m appuser
ENV HOME=/home/appuser

WORKDIR /app
COPY . /app

RUN chown -R appuser:appgroup /app /home/appuser
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501

ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=17190

# Copy the custom entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER appuser

# Use the custom entrypoint script to start both Streamlit and Flask
ENTRYPOINT ["/entrypoint.sh"]
