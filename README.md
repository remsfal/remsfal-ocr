# REMSFAL OCR Microservice

The _REMSFAL OCR Microservice_ is a stateless Python service for text extraction within the REMSFAL project. It is intended to work together with the **Remsfal Chat Microservice**.  
It listens for document processing requests sent by the chat service via Kafka, performs OCR, and returns the extracted text as a Kafka event.

By default:

- Kafka is expected to be available at `localhost:9092`
- MinIO is expected to be available at `localhost:9000`

## Setup

### Requirements

- Python >= 3.8
- Install dependencies:
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

Start the application with:

```bash
python src/main.py
```

⚠️ A Kafka broker must be running and reachable at startup otherwise the service will fail to connect.

For instructions on running other microservices and Docker containers, please refer to the main [REMSFAL repository](https://github.com/remsfal/remsfal-backend/blob/main/README.md).

### Running Tests

You can run all tests in the test/ folder using:

```bash
pytest test
```

#### Test Coverage

To run tests with coverage reporting in lcov format:

```bash
pytest test/ --cov=src --cov-report=lcov --cov-report=term-missing
```

Or use the provided script:

```bash
./run_tests_with_coverage.sh
```

This will generate:
- `coverage/coverage.lcov` - LCOV format coverage report
- `coverage/html/index.html` - HTML coverage report
- `coverage/coverage.xml` - XML format coverage report
- Terminal coverage summary

Current test coverage: **96%** of source code lines covered.

### Build Docker Image

```bash
docker build -t remsfal/remsfal-ocr:dev -f docker/Dockerfile .
```