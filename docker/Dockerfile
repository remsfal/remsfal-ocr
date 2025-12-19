FROM python:3.13

ENV APP_HOME=/home/app

# Create app user with home directory
RUN useradd --create-home --home-dir $APP_HOME app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y libgl1 libglib2.0-0 \
    && apt-get clean

# Install hatch and upgrade hatchling for Python 3.13 support
RUN pip install --no-cache-dir hatch && \
    pip install --no-cache-dir --upgrade hatchling

WORKDIR /usr/local/app

COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# Install project dependencies for production (only runtime deps, not dev/test)
RUN pip install --no-cache-dir .

WORKDIR /usr/local/app/src

# Ensure app user owns their home directory
RUN mkdir -p $APP_HOME/.paddleocr && \
    chown -R app:app $APP_HOME

USER app

# set number of threads
ENV OMP_NUM_THREADS=8

# download models for offline usage
RUN mkdir -p $APP_HOME/.paddleocr/models && python download_models.py

CMD ["hatch", "run", "start"]
