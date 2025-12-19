<img src="https://remsfal.de/logo_upscaled.png" width="60%">

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=remsfal_remsfal-ocr&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=remsfal_remsfal-ocr)
![Contributors](https://img.shields.io/github/contributors/remsfal/remsfal-ocr)

# REMSFAL OCR Microservice

The _REMSFAL OCR Microservice_ is a stateless Python service for text extraction within the REMSFAL project. It is intended to work together with the **Remsfal Chat Microservice**.  
It listens for document processing requests sent by the chat service via Kafka, performs OCR, and returns the extracted text as a Kafka event.

By default:

- Kafka is expected to be available at `localhost:9092`
- MinIO is expected to be available at `localhost:9000`

## Setup

### Requirements

- Python >= 3.8
- [Hatch](https://hatch.pypa.io/) (Python project manager)

### Installation

#### Using Hatch (Recommended)

1. Install Hatch:
   ```bash
   pip install hatch
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   hatch env create
   ```

   This will automatically create a virtual environment and install all project dependencies.

#### Using pip (Alternative)

If you prefer to use pip directly:

```bash
pip install -r requirements.txt
```

### Environment Variables

The following environment variables can be used to override the default values:

- `KAFKA_BROKER` = `localhost:9092`
- `KAFKA_TOPIC_IN` = `ocr.documents.to_process`
- `KAFKA_TOPIC_OUT` = `ocr.documents.processed`
- `GROUP_ID` = `ocr-service`
- `MINIO_ENDPOINT` = `localhost:9000`
- `MINIO_ACCESS_KEY` = `minioadmin`
- `MINIO_SECRET_KEY` = `minioadminpassword`

### Run

#### Using Hatch

Start the application with:

```bash
hatch run python src/main.py
```

#### Using Python directly

```bash
python src/main.py
```

⚠️ A Kafka broker must be running and reachable at startup otherwise the service will fail to connect.

For instructions on running other microservices and Docker containers, please refer to the main [REMSFAL repository](https://github.com/remsfal/remsfal-backend/blob/main/README.md).

### Running Tests

#### Using Hatch (Recommended)

Run all tests:

```bash
hatch run test
```

Run tests with coverage:

```bash
hatch run test-cov
```

Run tests with full coverage reports (LCOV, HTML, XML):

```bash
hatch run test-cov-full
```

This will generate:
- `coverage/coverage.lcov` - LCOV format coverage report
- `coverage/html/index.html` - HTML coverage report
- `coverage/coverage.xml` - XML format coverage report
- Terminal coverage summary

#### Using pytest directly

You can also run tests directly with pytest:

```bash
pytest test
```

Or with coverage:

```bash
pytest test/ --cov=src --cov-report=lcov --cov-report=term-missing
```

#### Using the test script

The provided script runs tests and linting:

```bash
./run_tests_with_coverage.sh
```

This generates all coverage reports and a Flake8 linting report.

Current test coverage: **96%** of source code lines covered.

### Linting

#### Using Hatch

Run linting checks:

```bash
hatch run lint
```

Generate a linting report:

```bash
hatch run lint-report
```

This will create `report/flake8-report.txt`.

#### Run all checks

Run both linting and tests with coverage:

```bash
hatch run check
```

### Building the Project

#### Using Hatch

Build the project (creates wheel and source distribution):

```bash
hatch build
```

The build artifacts will be in the `dist/` directory.

### Build Docker Image

```bash
docker build -t remsfal/remsfal-ocr:dev -f docker/Dockerfile .
```
