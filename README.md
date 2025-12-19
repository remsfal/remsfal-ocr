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
pip install .
```

This installs all dependencies from `pyproject.toml`.

### Environment Variables

The following environment variables can be used to override the default values:

- `KAFKA_BROKER` = `localhost:9092`
- `KAFKA_TOPIC_IN` = `ocr.documents.to_process`
- `KAFKA_TOPIC_OUT` = `ocr.documents.processed`
- `GROUP_ID` = `ocr-service`
- `MINIO_ENDPOINT` = `localhost:9000`
- `MINIO_ACCESS_KEY` = `minioadmin`
- `MINIO_SECRET_KEY` = `minioadminpassword`

Copy the example environment file:

```bash
cp .env.example .env
```

### Local Development

For local development and testing, you need Kafka and MinIO running. Use the provided Docker Compose configuration:

```bash
# Start Kafka, MinIO, and Kafka UI
docker compose up -d

# Check if services are running
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down
```

Services will be available at:
- **Kafka**: localhost:9092
- **Kafka UI**: http://localhost:8090 (for monitoring topics and messages)
- **MinIO API**: localhost:9000
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadminpassword)

### Run

Start the application with:

```bash
hatch run start
```

⚠️ A Kafka broker must be running and reachable at startup otherwise the service will fail to connect.

For instructions on running other microservices and Docker containers, please refer to the main [REMSFAL repository](https://github.com/remsfal/remsfal-backend/blob/main/README.md).

### Testing the OCR Service

After starting the Docker services and the OCR application, you can test the OCR functionality:

```bash
# Upload an image and send OCR request
hatch run python scripts/test_ocr.py test/resources/test-image.png
```

This script will:
1. Upload the image to MinIO bucket 'documents'
2. Send an OCR request message to Kafka topic 'ocr.documents.to_process'
3. Listen for the result on topic 'ocr.documents.processed'
4. Print the extracted text

You can also monitor the Kafka topics in the Kafka UI at http://localhost:8090.

### Running Tests

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

### Integration Tests

Integration tests use **testcontainers-python** to start real Kafka and MinIO containers, similar to Quarkus with Testcontainers. All tests (unit and integration) are in the `test/` directory and run together.

#### Prerequisites

- Docker must be running on your system
- Docker socket must be accessible

#### Running All Tests (Unit + Integration)

```bash
# Run all tests (unit + integration)
hatch run test

# Run all tests with coverage
hatch run test-cov

# Run specific integration test
hatch run test test/test_ocr_integration.py::test_kafka_container_starts
```

The integration tests will:
- Automatically start Kafka and MinIO containers
- Run tests against real services
- Clean up containers after tests complete
- Generate a combined coverage report with unit tests

#### What's tested

**Unit Tests:**
- OCR engine logic with mocks
- S3 client functionality
- Kafka consumer behavior

**Integration Tests:**
- Kafka container lifecycle
- MinIO container lifecycle
- Kafka message producer/consumer flow
- MinIO file upload/download
- Integration between Kafka and MinIO

For full end-to-end tests with the OCR service running, see comments in `test/test_ocr_integration.py`.

### Linting

Run linting checks:

```bash
hatch run lint
```

Generate a linting report:

```bash
hatch run lint-report
```

This will create `report/flake8-report.txt`.

### Run all checks

Run both linting and tests with coverage:

```bash
hatch run check
```

### Building the Project

Build the project (creates wheel and source distribution):

```bash
hatch build
```

The build artifacts will be in the `dist/` directory.

### Build Docker Image

```bash
docker build -t remsfal/remsfal-ocr:dev -f docker/Dockerfile .
```
