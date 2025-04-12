# Dell Asset Tag API

A Python tool for interacting with Dell's API to retrieve asset and entitlement information.

## Features

- Authentication with Dell API using OAuth2
- Retrieve asset information using service tags
- Check warranty and entitlement status
- Export data to CSV format
- Import data from CSV files
- Debug mode for troubleshooting
- TLS certificate verification options

## Prerequisites

- Python 3.6 or higher
- Required Python packages (see requirements.txt)
- Dell API credentials (client ID and client secret)
- TLS certificate (if required by your environment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dell_asset_tag_api.git
cd dell_asset_tag_api
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Dell API credentials:
```
DELL_CLIENT_ID=your_client_id
DELL_CLIENT_SECRET=your_client_secret
DELL_API_BASE_URL=https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5
DELL_CA_CERT=/path/to/your/certificate.pem  # Optional: Path to your CA certificate
DELL_VERIFY_SSL=true  # Optional: Set to false to disable SSL verification (not recommended for production)
```

## Usage

### Check Asset Information

```bash
python dell_entitlement.py check-asset <service_tag> [--debug] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py check-asset 8CTY3W3 --debug
```

### Check Entitlement Information

```bash
python dell_entitlement.py check-entitlement <service_tag> [--debug] [--export] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py check-entitlement 8CTY3W3 --debug --export
```

### Import from CSV

You can import service tags from a CSV file. The CSV file should have the following format:

```csv
Name,Asset Tag,Warranty,Acquisition Date,Warranty Expiry Date
John Smith,ABC123,ProSupport,2021-01-10,2024-01-10
Jane Doe,DEF456,Basic Support,2021-02-15,2023-02-15
Bob Johnson,GHI789,Premium Support,2021-03-20,2025-03-20
```

To import and process multiple service tags from a CSV file:

```bash
python dell_entitlement.py import-csv <input_file.csv> [--debug] [--export] [--no-verify-ssl]
```

Example:
```bash
python dell_entitlement.py import-csv assets.csv --debug --export
```

### TLS Certificate Configuration

The tool supports several options for TLS certificate verification:

1. Using a custom CA certificate:
   - Set the `DELL_CA_CERT` environment variable to point to your certificate file
   - The certificate should be in PEM format
   - Example: `DELL_CA_CERT=/path/to/your/certificate.pem`

2. Disabling SSL verification (not recommended for production):
   - Set `DELL_VERIFY_SSL=false` in your `.env` file
   - Or use the `--no-verify-ssl` flag with any command
   - Example: `python dell_entitlement.py check-asset 8CTY3W3 --no-verify-ssl`

3. Using system certificates (default):
   - If no certificate is specified, the tool will use your system's certificate store
   - This is the recommended approach for most environments

### Export to CSV

When using the `--export` flag, the tool will create a CSV file with the following columns:
- itemNumber
- startDate
- endDate
- entitlementType
- serviceLevelCode
- serviceLevelDescription
- serviceLevelGroup

## Example Data

The repository includes an `example.csv` file with dummy data to demonstrate the expected format for both importing and exporting data.

## Security

- Never commit your `.env` file or any files containing sensitive information
- The `.gitignore` file is configured to exclude sensitive files and CSV outputs
- Only example files are included in the repository
- Always use proper TLS certificate verification in production environments
- Avoid disabling SSL verification unless absolutely necessary

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 