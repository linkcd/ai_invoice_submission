import sys
import os
import json
import boto3
from datetime import datetime
from src.bda_client import get_aws_account_id, invoke_data_automation, wait_for_data_automation_to_complete
from src.result_processor import process_bda_results

# Configuration
AWS_REGION = 'us-east-1'
BUCKET_NAME = 'lufng-bedrock-data-automation'
INPUT_PATH = 'BDA/Input/ruter_invoices'
OUTPUT_PATH = 'BDA/Output/ruter_invoices'

PROJECT_ID = 'a0fbb83f9473'
BLUEPRINT_NAME = 'ruter_invoice_blueprint'

# Fields to display
BLUEPRINT_FIELDS = [
    'invoice_amount',
    'purchase_date',
    'ticket_number'
]

def upload_file_to_s3(file_path, s3_key):
    """Upload file to S3"""
    s3 = boto3.client('s3', region_name=AWS_REGION)
    s3.upload_file(file_path, BUCKET_NAME, s3_key)

def append_result_to_batch(result_file_path, result_data):
    """Append result to batch result file"""
    if os.path.exists(result_file_path):
        with open(result_file_path, 'r') as f:
            results = json.load(f)
    else:
        results = []
    
    results.append(result_data)
    
    with open(result_file_path, 'w') as f:
        json.dump(results, f, indent=2)

def process_batch_folder(batch_name):
    """Process all files in a batch folder"""
    input_folder = f"input/{batch_name}"
    
    if not os.path.exists(input_folder):
        print(f"Error: Folder '{input_folder}' does not exist")
        return
    
    # Get only PDF files in the batch folder
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f)) and f.lower().endswith('.pdf')]
    total_files = len(files)
    
    if total_files == 0:
        print(f"No files found in '{input_folder}'")
        return
    
    # Create result filename in input folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"result_{timestamp}.json"
    result_file_path = os.path.join(input_folder, result_filename)
    
    print(f"Starting batch processing for '{batch_name}' with {total_files} files")
    print(f"Results will be saved to: {result_file_path}")
    
    aws_account_id = get_aws_account_id()
    data_automation_arn = f"arn:aws:bedrock:{AWS_REGION}:{aws_account_id}:data-automation-project/{PROJECT_ID}"
    processed_count = 0
    
    for i, filename in enumerate(files, 1):
        print(f"\nProcessing file {i}/{total_files}: {filename}")
        
        # Upload file to S3
        local_file_path = os.path.join(input_folder, filename)
        s3_key = f"{INPUT_PATH}/{batch_name}/{filename}"
        upload_file_to_s3(local_file_path, s3_key)
        print(f"Uploaded to S3: {s3_key}")
        
        # Process with Bedrock Data Automation
        input_s3_uri = f"s3://{BUCKET_NAME}/{s3_key}"
        output_s3_uri = f"s3://{BUCKET_NAME}/{OUTPUT_PATH}"
        
        print(f"Invoking Bedrock Data Automation for '{filename}'", end='', flush=True)
        
        try:
            data_automation_response = invoke_data_automation(input_s3_uri, output_s3_uri, data_automation_arn, aws_account_id, AWS_REGION)
            data_automation_status = wait_for_data_automation_to_complete(data_automation_response['invocationArn'], AWS_REGION)
            
            if data_automation_status['status'] == 'Success':
                job_metadata_s3_uri = data_automation_status['outputConfiguration']['s3Uri']
                result_data = process_bda_results(job_metadata_s3_uri, filename, BLUEPRINT_NAME, BLUEPRINT_FIELDS)
                
                # Append to batch result file
                if result_data:
                    append_result_to_batch(result_file_path, {
                        "filename": filename,
                        "purchase_date": result_data.get('purchase_date'),
                        "invoice_amount": result_data.get('invoice_amount'),
                        "ticket_number": result_data.get('ticket_number'),
                        "submitted": False
                    })
                
                processed_count += 1
            else:
                print(f"\nFailed to process {filename}: {data_automation_status['status']}")
                
        except Exception as e:
            print(f"\nError processing {filename}: {str(e)}")
    
    print(f"\nBatch processing completed: {processed_count}/{total_files} files processed successfully")
    print(f"Results saved to: {result_file_path}")

def main():
    if len(sys.argv) < 2:
        print("Please provide a batch folder name as command line argument")
        sys.exit(1)
      
    batch_name = sys.argv[1]
    process_batch_folder(batch_name)

if __name__ == "__main__":
    main()