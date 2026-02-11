# AnyCost Adaptor Template

Create CloudZero AnyCost Stream adaptors for any provider in minutes.

## Quick Start

```bash
# 1. Generate your adaptor
pip install PyYAML
python generate_adaptor.py --config config/examples/splunk_config.yaml --output ../splunk-adaptor

# 2. Implement your provider
cd ../splunk-adaptor
pip install .
cp env/.env.example env/.env  # Add credentials
# Edit src/splunk_*.py files (replace TODO comments)

# 3. Deploy
python anycost.py test
python anycost.py splunk --month 2024-08
```

## How It Works

1. **Template files** (`src/*.template`) contain `{{VARIABLES}}`
2. **Generator script** replaces variables with your provider details  
3. **You implement** the TODO sections for authentication, API calls, data transformation
4. **Ready-to-use files** handle CloudZero upload, CSV processing, CLI

## Supported Providers

- **Cloud**: AWS, Azure, GCP, Oracle
- **Monitoring**: Splunk, DataDog, New Relic
- **Logging**: SumoLogic, Elasticsearch
- **Custom**: Any API with billing data

## What You Get

```
your-provider-adaptor/
├── anycost.py              # CLI (ready to use)
├── src/
│   ├── provider_config.py  # ← Add authentication  
│   ├── provider_client.py  # ← Add API calls
│   ├── provider_transform.py # ← Add data mapping
│   └── cloudzero.py        # CloudZero client (ready to use)
└── env/.env.example        # Environment template
```

## Commands

```bash
python anycost.py test                    # Test connections
python anycost.py myprovider --month 2024-08  # Upload data
python anycost.py daily                   # Daily automation
python anycost.py csv --input data.csv    # Process CSV files
```

## Examples

- **CSV Processing**: `config/examples/splunk_config.yaml` (DataDog/Splunk pattern)
- **API Basic Auth**: `config/examples/confluent_config.yaml` (Confluent pattern)  
- **API Enterprise**: `config/examples/heroku_config.yaml` (Heroku pattern)
- **Custom**: Copy `config/sample_provider_config.yaml`

## Support

- Examples in `config/examples/`
- Use `--dry-run` to test without uploading
- See CloudZero AnyCost Stream docs for setup