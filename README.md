# Prompt Engineering Benchmarking

This repository contains the code for benchmarking prompt engineering techniques.

## Prerequisites

- Python 3.x
- Docker (optional)

## Local Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/prompt-engineering-benchmarking.git
    ```

2. Navigate to the project directory:

    ```bash
    cd prompt-engineering-benchmarking
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the benchmark locally:

    ```bash
    python . benchmark
    ```

5. Grab the test_run_id and evaluate:

    ```bash
    python . evaluate --test-run-ids='["TEST_RUN_ID_GOES_HERE"]'
    ```

6. Make the graphs:

    ```bash
    python . analyze --test-run-ids='["TEST_RUN_ID_GOES_HERE"]'
    ```