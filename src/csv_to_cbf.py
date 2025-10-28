#!/usr/bin/env python3
"""
Convert CSV billing data to Common Bill Format (CBF) and upload to CloudZero.
This script processes CSV files from the input/ directory.

Generic CSV processor that can be customized for any provider.
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any
import json


def read_billing_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Read billing CSV file and return list of records.
    
    Args:
        file_path: Path to the billing CSV file
        
    Returns:
        List of dictionaries representing billing records
    """
    print(f"Reading billing CSV file: {file_path}")
    
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        records = list(reader)
    
    print(f"✓ Read {len(records)} records from CSV")
    return records


def transform_csv_to_cbf(billing_records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Transform billing CSV records to Common Bill Format (CBF).
    
    This is a generic transformation that should be customized for your provider.
    
    Args:
        billing_records: List of billing records from CSV
        
    Returns:
        List of CBF-formatted rows
    """
    print(f"Transforming {len(billing_records)} records to CBF format...")
    
    cbf_rows = []
    
    for record in billing_records:
        # Skip empty rows
        if not any(record.values()):
            continue
            
        try:
            # Generic CBF transformation (CloudZero AnyCost format) - customize this for your provider
            cbf_record = {
                # Required fields
                'time/usage_start': format_datetime(record.get('usage_start_time') or record.get('billing_date', '')),
                'cost/cost': format_cost(record.get('cost', '0')),
                'bill/invoice_id': record.get('invoice_id', ''),
                
                # Line item columns (optional)
                'lineitem/id': generate_lineitem_id(record),
                'lineitem/type': record.get('line_item_type', 'Usage'),
                'lineitem/description': record.get('description', ''),
                'lineitem/cloud_provider': record.get('provider_name', 'Unknown'),
                
                # Resource columns (optional)
                'resource/id': record.get('resource_id', ''),
                'resource/service': record.get('service_name', ''),
                'resource/account': record.get('account_id', ''),
                'resource/region': record.get('region', ''),
                'resource/usage_family': record.get('usage_family', ''),
                
                # Action columns (optional)
                'action/operation': record.get('operation', ''),
                'action/usage_type': record.get('usage_type', ''),
                
                # Usage columns (optional)
                'usage/amount': record.get('usage_amount', ''),
                'usage/units': record.get('usage_unit', ''),
                
                # Additional cost columns (optional)
                'cost/discounted_cost': format_cost(record.get('discounted_cost')) if record.get('discounted_cost') else '',
                'cost/amortized_cost': format_cost(record.get('amortized_cost')) if record.get('amortized_cost') else '',
                'cost/on_demand_cost': format_cost(record.get('on_demand_cost')) if record.get('on_demand_cost') else '',
            }
            
            # Validate required fields
            if not cbf_record['cost/cost'] or cbf_record['cost/cost'] == '0.00':
                continue
                
            cbf_rows.append(cbf_record)
            
        except Exception as e:
            print(f"Error transforming record: {e}")
            print(f"Problematic record: {record}")
            continue
    
    print(f"✓ Transformed {len(cbf_rows)} records to CBF format")
    return cbf_rows


def format_cost(cost_str: str) -> str:
    """
    Format cost value to CBF standard (2 decimal places).
    
    Args:
        cost_str: Raw cost string
        
    Returns:
        Formatted cost string
    """
    if not cost_str or cost_str == '':
        return "0.00"
    
    try:
        cost_float = float(cost_str)
        return f"{cost_float:.2f}"
    except (ValueError, TypeError):
        print(f"Warning: Could not format cost value: {cost_str}")
        return "0.00"


def format_datetime(dt_str: str) -> str:
    """
    Format datetime string to CBF standard.
    
    Args:
        dt_str: Raw datetime string
        
    Returns:
        Formatted datetime string
    """
    if not dt_str:
        return ""
    
    try:
        # Try to parse and reformat to standard format
        if 'T' in dt_str:
            # ISO format
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            # Try common formats
            try:
                dt = datetime.strptime(dt_str, '%Y-%m-%d')
            except ValueError:
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    except Exception:
        print(f"Warning: Could not format datetime: {dt_str}")
        return dt_str


def format_tags(tags_str: str) -> str:
    """
    Format tags to JSON string.
    
    Args:
        tags_str: Raw tags string (JSON or key=value format)
        
    Returns:
        JSON formatted tags string
    """
    if not tags_str or tags_str == '':
        return "{}"
    
    try:
        # If already JSON, validate and return
        json.loads(tags_str)
        return tags_str
    except json.JSONDecodeError:
        # Try to parse key=value format
        try:
            tags = {}
            if ',' in tags_str:
                pairs = tags_str.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        tags[key.strip()] = value.strip()
            return json.dumps(tags)
        except:
            return "{}"


def generate_lineitem_id(record: Dict[str, str]) -> str:
    """
    Generate a unique line item ID for the record.
    
    Args:
        record: Billing record
        
    Returns:
        Unique line item ID string
    """
    import hashlib
    
    # Use key fields to generate unique ID
    key_fields = [
        record.get('resource_id', ''),
        record.get('service_name', ''),
        record.get('usage_start_time') or record.get('billing_date', ''),
        record.get('region', ''),
        'csv_import'
    ]
    
    combined = "|".join(str(field) for field in key_fields if field)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def generate_provider_id(record: Dict[str, str]) -> str:
    """
    Generate a unique provider ID for the record (legacy function).
    
    Args:
        record: Billing record
        
    Returns:
        Unique provider ID string
    """
    return generate_lineitem_id(record)


def main():
    """Main function for CSV to CBF conversion."""
    parser = argparse.ArgumentParser(
        description="Convert billing CSV to Common Bill Format (CBF)",
        epilog="""
Examples:
  python csv_to_cbf.py --input input/billing_data.csv
  python csv_to_cbf.py --input input/billing_data.csv --output output/cbf_data.csv
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--input", 
        required=True,
        help="Input CSV file path"
    )
    parser.add_argument(
        "--output", 
        default="output/csv_cbf_output.csv",
        help="Output CBF CSV file path (default: output/csv_cbf_output.csv)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip CloudZero upload"
    )
    
    args = parser.parse_args()
    
    # Check input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        # Read and transform CSV data
        billing_records = read_billing_csv(args.input)
        cbf_rows = transform_csv_to_cbf(billing_records)
        
        if not cbf_rows:
            print("No valid data to process. Exiting.")
            sys.exit(0)
        
        # Create output directory if needed
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Write CBF data to file
        print(f"Writing {len(cbf_rows)} CBF records to: {args.output}")
        
        # Get all unique field names
        all_fieldnames = set()
        for row in cbf_rows:
            all_fieldnames.update(row.keys())
        fieldnames = sorted(list(all_fieldnames))
        
        with open(args.output, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cbf_rows)
        
        print(f"✓ CBF data written to: {args.output}")
        print(f"  Total records: {len(cbf_rows)}")
        
        # Upload to CloudZero if requested
        if not args.no_upload:
            print("\n🚀 To upload to CloudZero, use:")
            print(f"python anycost.py csv --input {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()