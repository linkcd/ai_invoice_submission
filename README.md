# Amazon Bedrock Data Automation - Invoice Processing

This project demonstrates batch processing of invoice documents using Amazon Bedrock Data Automation. It processes multiple files from local folders, uploads them to S3, extracts invoice information, and generates consolidated results.

## Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS Account with Bedrock Data Automation access
- AWS CLI configured with appropriate credentials
- Amazon S3 bucket for storing input and output files

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd invoice-submission
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Configure AWS credentials:
   - Make sure you have AWS CLI installed and configured
   - Set up your AWS credentials with appropriate permissions for Bedrock and S3 services

## Project Structure

```
invoice_submission/
├── app.py                    # Main application
├── src/                      # Source code modules
│   ├── bda_client.py        # BDA operations
│   └── result_processor.py  # Result processing & JSON generation
├── input/                    # Local input folders (gitignored)
│   └── batch1/              # Example batch folder
│       ├── invoice1.pdf     # PDF files to process
│       ├── invoice2.pdf
│       └── result_*.json    # Generated results
└── pyproject.toml           # Project configuration
```

## Configuration

Before running the application, update the following variables in `app.py`:

- `AWS_REGION`: Your AWS region (e.g., 'us-east-1')
- `BUCKET_NAME`: Your S3 bucket name
- `PROJECT_ID`: Your Bedrock Data Automation project ID
- `BLUEPRINT_NAME`: The name of your data automation blueprint (default: 'ruter_invoice_blueprint')

## Usage

The application now processes batches of files from local folders:

1. Create a batch folder and place your invoice files:
```bash
mkdir -p input/batch1
# Copy your PDF files to input/batch1/
```

2. Run the application with a batch folder name:
```bash
uv sync
uv run python app.py batch1
```

The application will:
- Process only PDF files from `input/batch1/`
- Upload each PDF to S3
- Process each file using AWS Bedrock Data Automation
- Extract invoice information (amount, date, ticket number)
- Generate consolidated results in `input/batch1/result_TIMESTAMP.json`
- Show progress for each file (e.g., "Processing file 3/10")

## Batch Processing Output

### Console Output:
```
Starting batch processing for 'batch1' with 24 files
Results will be saved to: input/batch1/result_20251015_174514.json

Processing file 1/24: invoice1.pdf
Uploaded to S3: BDA/Input/ruter_invoices/batch1/invoice1.pdf
Invoking Bedrock Data Automation for 'invoice1.pdf'... Success

Processing file 2/24: invoice2.pdf
...

Batch processing completed: 24/24 files processed successfully
Results saved to: input/batch1/result_20251015_174514.json
```

### Generated JSON Output:
The application generates `input/{batch_name}/result_{timestamp}.json` containing an array of processed invoices:

```json
[
  {
    "filename": "invoice1.pdf",
    "purchase_date": "2025-08-26",
    "invoice_amount": 72,
    "ticket_number": "4144262946",
    "submitted": false
  },
  {
    "filename": "invoice2.pdf",
    "purchase_date": "2025-09-02",
    "invoice_amount": 68.4,
    "ticket_number": "4145491422",
    "submitted": false
  }
]
```

## Debug Mode

To enable detailed logging, set `DEBUG = True` in `src/bda_client.py`. This will print complete AWS service responses for troubleshooting.

## Error Handling

- Progress tracking shows successful vs failed processing
- Individual file errors don't stop batch processing
- Clear error messages for missing folders or AWS issues

## Development

### Using uv for Package Management

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Run the application
uv run python app.py batch1

# Activate virtual environment (alternative)
source .venv/bin/activate  # or uv shell
python app.py batch1
```

### Project Commands

```bash
# Process a batch
uv run python app.py batch1

# Check project structure
tree -I '__pycache__|.git|.venv'
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 