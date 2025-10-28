# Sample Provider Adaptor Example

This is a clean example showing the structure of a generated adaptor.

## Generated Structure

```
sample-provider-adaptor/
├── anycost.py                    # Unified entry point
├── requirements.txt              # Dependencies
├── README.md                     # Generated documentation
├── env/
│   └── .env.example             # Environment template
├── src/
│   ├── sampleprovider_config.py     # Provider authentication
│   ├── sampleprovider_client.py     # API data fetching
│   ├── sampleprovider_transform.py  # CBF transformation
│   ├── sampleprovider_anycost_adaptor.py # Main adaptor
│   ├── cloudzero.py             # CloudZero client
│   └── csv_to_cbf.py           # CSV processing
├── input/                       # Raw data storage
├── output/                      # CBF output files
└── tests/                       # Test files
```

## Usage After Generation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure credentials  
cp env/.env.example env/.env
# Edit env/.env with your provider credentials

# Test connections
python anycost.py test

# Process data
python anycost.py sampleprovider --month 2024-08
```

## Implementation Steps

1. **Configure Authentication** (`sampleprovider_config.py`)
   - Add provider-specific environment variables
   - Implement connection validation

2. **Implement Data Fetching** (`sampleprovider_client.py`) 
   - Add API calls to fetch billing/usage data
   - Handle pagination, rate limiting

3. **Add Data Transformation** (`sampleprovider_transform.py`)
   - Map provider fields to CBF format
   - Handle data type conversions

4. **Test and Deploy**
   - Test with sample data
   - Configure CloudZero connection
   - Run production uploads