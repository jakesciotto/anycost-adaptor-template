#!/usr/bin/env python3
"""
AnyCost Adaptor Template Generator (DEPRECATED)

This script is deprecated. Use the new generator instead:

    python -m anycost_generator generate --config CONFIG --output DIR
    python -m anycost_generator interactive
    python -m anycost_generator validate --config CONFIG

See the project README for full usage instructions.
"""

import os
import sys
import argparse
import yaml
import shutil
import warnings
from pathlib import Path
from typing import Dict, Any

warnings.warn(
    "generate_adaptor.py is deprecated. Use 'python -m anycost_generator' instead.",
    DeprecationWarning,
    stacklevel=2,
)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def generate_template_variables(config: Dict[str, Any]) -> Dict[str, str]:
    """Generate all template variables from config."""
    provider_name = config['provider']['name']
    provider_display_name = config['provider']['display_name']
    
    # Generate derived variables
    provider_class_name = ''.join(word.capitalize() for word in provider_name.split('_'))
    provider_upper = provider_name.upper().replace('-', '_')
    
    variables = {
        # Core provider info
        'PROVIDER_NAME': provider_name,
        'provider_name': provider_name,  # Add lowercase version
        'PROVIDER_DISPLAY_NAME': provider_display_name,
        'PROVIDER_CLASS_NAME': provider_class_name,
        'PROVIDER_UPPER': provider_upper,
        'SERVICE_TYPE': config['provider']['service_type'],
        
        # API configuration
        'API_BASE_URL': config['api']['base_url'],
        'AUTH_METHOD': config['api']['auth_method'],
        'RATE_LIMIT': str(config['api'].get('rate_limit', '10')),
        'API_TIMEOUT': str(config['api'].get('timeout', '30')),
        
        # Auth configuration
        'REQUIRED_ENV_VARS': format_env_vars_list(config['auth']['required_env_vars']),
        'OPTIONAL_ENV_VARS': format_env_vars_list(config['auth'].get('optional_env_vars', [])),
        
        # Dependencies (formatted as pyproject.toml array entries)
        'PROVIDER_DEPENDENCIES': '\n    '.join(f'"{dep}",' for dep in list(dict.fromkeys(config.get('dependencies', [])))),
        
        # Placeholders for user to fill in
        'PROVIDER_IMPORTS': f'# TODO: Add {provider_display_name} SDK imports here',
        'DATA_FETCHING_LOGIC': f'# TODO: Implement {provider_display_name} API data fetching',
        'SERVICE_DISCOVERY_LOGIC': f'# TODO: Implement service discovery for {provider_display_name}',
        'REGION_DISCOVERY_LOGIC': f'# TODO: Implement region discovery for {provider_display_name}',
        'VALIDATION_LOGIC': f'# TODO: Add {provider_display_name} config validation',
        'CLIENT_INITIALIZATION': f'# TODO: Initialize {provider_display_name} client',
        'CONNECTION_TEST': f'# TODO: Test {provider_display_name} connection',
        'REQUIRED_CONFIG_MAPPING': generate_config_mapping(config['auth']['required_env_vars'], required=True),
        'OPTIONAL_CONFIG_MAPPING': generate_config_mapping(config['auth'].get('optional_env_vars', []), required=False),
        'FIELD_EXTRACTION_LOGIC': f'# TODO: Extract fields from {provider_display_name} record',
        'TAG_EXTRACTION_LOGIC': f'# TODO: Extract tags from {provider_display_name} record',
        
        # CBF field mappings (new CloudZero format - placeholders)
        # Required fields
        'TIME_USAGE_START_MAPPING': "format_datetime(record.get('usage_start_time'))",
        'COST_COST_MAPPING': "format_cost(record.get('cost', 0))",
        'BILL_INVOICE_ID_MAPPING': "record.get('invoice_id', '')",
        
        # Line item columns (optional)
        'LINEITEM_ID_MAPPING': "generate_lineitem_id(record)",
        'LINEITEM_TYPE_MAPPING': "record.get('line_item_type', 'Usage')",
        'LINEITEM_DESCRIPTION_MAPPING': "record.get('description', '')",
        'LINEITEM_CLOUD_PROVIDER_MAPPING': f"'{provider_display_name}'",
        
        # Resource columns (optional) 
        'RESOURCE_ID_MAPPING': "record.get('resource_id', '')",
        'RESOURCE_SERVICE_MAPPING': "record.get('service_name', '')",
        'RESOURCE_ACCOUNT_MAPPING': "record.get('account_id', '')",
        'RESOURCE_REGION_MAPPING': "record.get('region', '')",
        'RESOURCE_USAGE_FAMILY_MAPPING': "record.get('usage_family', '')",
        
        # Action columns (optional)
        'ACTION_OPERATION_MAPPING': "record.get('operation', '')",
        'ACTION_USAGE_TYPE_MAPPING': "record.get('usage_type', '')",
        
        # Usage columns (optional)
        'USAGE_AMOUNT_MAPPING': "str(record.get('usage_amount', ''))",
        'USAGE_UNITS_MAPPING': "record.get('usage_unit', '')",
        
        # Additional cost columns (optional)
        'COST_DISCOUNTED_COST_MAPPING': "format_cost(record.get('discounted_cost'))",
        'COST_AMORTIZED_COST_MAPPING': "format_cost(record.get('amortized_cost'))",
        'COST_ON_DEMAND_COST_MAPPING': "format_cost(record.get('on_demand_cost'))",
        
        # Kubernetes columns (optional)
        'K8S_CLUSTER_MAPPING': "record.get('k8s_cluster', '')",
        'K8S_NAMESPACE_MAPPING': "record.get('k8s_namespace', '')",
        'K8S_DEPLOYMENT_MAPPING': "record.get('k8s_deployment', '')",
        'K8S_LABELS_MAPPING': "extract_k8s_labels(record)",
        
        # Provider ID key fields (for unique identification)
        'PROVIDER_ID_KEY_FIELDS': f'''record.get('resource_id', ''),
        record.get('service_name', ''),
        record.get('billing_date', ''),
        record.get('region', ''),
        '{provider_name}' ''',
        
        # Service category mapping (placeholder)
        'SERVICE_CATEGORY_MAPPING_DICT': f'''# TODO: Map {provider_display_name} services to categories
        # Example:
        # 'Compute Engine': 'Compute',
        # 'Cloud Storage': 'Storage',
        # 'Cloud SQL': 'Database',
        'unknown': 'Other' ''',
    }
    
    return variables


def format_env_vars_list(env_vars: list) -> str:
    """Format environment variables list for Python code."""
    if not env_vars:
        return "[]"
    formatted = [f"'{var}'" for var in env_vars]
    return "[\n            " + ",\n            ".join(formatted) + "\n        ]"


def generate_config_mapping(env_vars: list, required: bool = True) -> str:
    """Generate configuration mapping code."""
    if not env_vars:
        return "# No additional configuration needed"
    
    mappings = []
    for var in env_vars:
        # Convert env var to config key (e.g., MYCLOUD_API_KEY -> api_key)
        config_key = var.lower().replace(var.split('_')[0].lower() + '_', '').replace('_', '_')
        if required:
            mappings.append(f"config['{config_key}'] = os.getenv('{var}')")
        else:
            mappings.append(f"config['{config_key}'] = os.getenv('{var}')")
    
    return "\n        ".join(mappings)


def replace_template_variables(content: str, variables: Dict[str, str]) -> str:
    """Replace template variables in content."""
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    return content


def process_template_file(template_path: Path, output_path: Path, variables: Dict[str, str]):
    """Process a single template file."""
    # Read template content
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace template variables
    processed_content = replace_template_variables(content, variables)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write processed content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    
    print(f"Generated: {output_path}")


def generate_adaptor(config_path: str, output_dir: str):
    """Generate adaptor from template and config."""
    # Load configuration
    config = load_config(config_path)
    provider_name = config['provider']['name']
    
    # Generate template variables
    variables = generate_template_variables(config)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {config['provider']['display_name']} adaptor...")
    print(f"Output directory: {output_path.absolute()}")
    
    # Template file mappings (template_file -> output_file)
    template_mappings = {
        'src/provider_config.py.template': f'src/{provider_name}_config.py',
        'src/provider_client.py.template': f'src/{provider_name}_client.py', 
        'src/provider_transform.py.template': f'src/{provider_name}_transform.py',
        'src/provider_anycost_adaptor.py.template': f'src/{provider_name}_anycost_adaptor.py',
        'templates/anycost.py.template': 'anycost.py',
        'templates/pyproject.toml.template': 'pyproject.toml',
    }
    
    # Process template files
    current_dir = Path(__file__).parent
    for template_file, output_file in template_mappings.items():
        template_path = current_dir / template_file
        output_file_path = output_path / output_file
        
        if template_path.exists():
            process_template_file(template_path, output_file_path, variables)
        else:
            print(f"Warning: Template not found: {template_path}")
    
    # Copy generic files that don't need templating
    generic_files = [
        'src/cloudzero.py',
    ]
    
    for generic_file in generic_files:
        src_path = current_dir / generic_file
        dst_path = output_path / generic_file
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {dst_path}")
    
    # Create directory structure
    directories = ['env', 'input', 'output', 'tests']
    for directory in directories:
        (output_path / directory).mkdir(exist_ok=True)
    
    # Create .env template
    env_template_path = output_path / 'env' / '.env.example'
    env_content = generate_env_template(config)
    with open(env_template_path, 'w') as f:
        f.write(env_content)
    print(f"Generated: {env_template_path}")
    
    # Create basic README
    readme_path = output_path / 'README.md'
    readme_content = generate_readme(config)
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"Generated: {readme_path}")
    
    print(f"\n✅ Successfully generated {config['provider']['display_name']} adaptor!")
    print(f"\nNext steps:")
    print(f"1. cd {output_path}")
    print(f"2. cp env/.env.example env/.env")
    print(f"3. Edit env/.env with your {config['provider']['display_name']} credentials")
    print(f"4. pip install .")
    print(f"5. Customize the TODO sections in the generated files")
    print(f"6. python anycost.py test")


def generate_env_template(config: Dict[str, Any]) -> str:
    """Generate .env template file."""
    lines = [
        f"# {config['provider']['display_name']} AnyCost Adaptor Configuration",
        "",
        f"# {config['provider']['display_name']} API Configuration"
    ]
    
    # Add required env vars
    for var in config['auth']['required_env_vars']:
        lines.append(f"{var}=your_{var.lower()}_here")
    
    # Add optional env vars
    optional_vars = config['auth'].get('optional_env_vars', [])
    if optional_vars:
        lines.append("")
        lines.append("# Optional Configuration")
        for var in optional_vars:
            lines.append(f"# {var}=optional_value")
    
    # Add CloudZero configuration
    lines.extend([
        "",
        "# CloudZero AnyCost Stream Configuration",
        "CLOUDZERO_API_KEY=your_cloudzero_api_key",
        "CLOUDZERO_CONNECTION_ID=your_anycost_stream_connection_id",
        "CLOUDZERO_API_URL=https://api.cloudzero.com"
    ])
    
    return "\n".join(lines) + "\n"


def generate_readme(config: Dict[str, Any]) -> str:
    """Generate basic README for the adaptor."""
    provider_name = config['provider']['name']
    provider_display = config['provider']['display_name']
    
    return f"""# {provider_display} AnyCost Stream Adaptor

Fetch billing data from {provider_display} and upload to CloudZero AnyCost Stream.

Generated from AnyCost Adaptor Template.

## Setup

1. **Install dependencies:**
   ```bash
   pip install .
   ```

2. **Configure credentials:**
   ```bash
   cp env/.env.example env/.env
   # Edit env/.env with your credentials
   ```

3. **Customize implementation:**
   - Edit `src/{provider_name}_config.py` - Add authentication logic
   - Edit `src/{provider_name}_client.py` - Add API data fetching
   - Edit `src/{provider_name}_transform.py` - Add data transformation

## Usage

```bash
# Test connections
python anycost.py test

# Process single month
python anycost.py {provider_name} --month 2024-08

# Process multiple months  
python anycost.py {provider_name} --months 2024-06,2024-07,2024-08

# Daily sync (yesterday's data)
python anycost.py daily

# Dry run (test without uploading)
python anycost.py {provider_name} --month 2024-08 --dry-run
```

## Implementation Status

- [ ] Authentication and configuration (`{provider_name}_config.py`)
- [ ] API client for data fetching (`{provider_name}_client.py`)  
- [ ] Data transformation to CBF (`{provider_name}_transform.py`)
- [ ] Test with sample data
- [ ] Production deployment

## Support

Review the template documentation and Oracle example for implementation guidance.
"""


def main():
    parser = argparse.ArgumentParser(description="Generate AnyCost Adaptor from template")
    parser.add_argument('--config', required=True, help='Path to template configuration YAML file')
    parser.add_argument('--output', required=True, help='Output directory for generated adaptor')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        sys.exit(1)
    
    try:
        generate_adaptor(args.config, args.output)
    except Exception as e:
        print(f"Error generating adaptor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()