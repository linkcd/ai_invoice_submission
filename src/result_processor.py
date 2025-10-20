import json
from datetime import datetime
from .bda_client import get_json_object_from_s3_uri, log

def process_bda_results(job_metadata_s3_uri, filename, blueprint_name, blueprint_fields):
    """Process BDA results and generate JSON output"""
    job_metadata = get_json_object_from_s3_uri(job_metadata_s3_uri)
    log(job_metadata)
    
    extracted_data = {}

    for segment in job_metadata['output_metadata']:
        asset_id = segment['asset_id']
        print(f'\nAsset ID: {asset_id}')

        for segment_metadata in segment['segment_metadata']:
            # Standard output
            standard_output_path = segment_metadata['standard_output_path']
            standard_output_result = get_json_object_from_s3_uri(standard_output_path)
            log(standard_output_result)
            print('\n- Standard output')
            semantic_modality = standard_output_result['metadata']['semantic_modality']
            print(f"Semantic modality: {semantic_modality}")
            
            # Custom output
            if 'custom_output_status' in segment_metadata and segment_metadata['custom_output_status'] == 'MATCH':
                custom_output_path = segment_metadata['custom_output_path']
                custom_output_result = get_json_object_from_s3_uri(custom_output_path)
                fields = _print_custom_results(custom_output_result, blueprint_name, blueprint_fields)
                extracted_data.update(fields)
    
    # Return extracted data for batch processing
    # Individual JSON generation is now handled by batch processor
    
    return extracted_data

def _extract_fields_from_custom_output(custom_output_result, blueprint_name, blueprint_fields):
    """Extract field values from custom output result"""
    extracted_fields = {}
    if custom_output_result['matched_blueprint']['name'] == blueprint_name:
        inference_result = custom_output_result['inference_result']
        for field in blueprint_fields:
            extracted_fields[field] = inference_result.get(field)
    return extracted_fields

def _generate_result_json(filename, purchase_date, invoice_amount, ticket_number):
    """Generate timestamped JSON result file"""
    import os
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_data = {
        "filename": filename,
        "purchase_date": purchase_date,
        "invoice_amount": invoice_amount,
        "ticket_number": ticket_number,
        "submitted": False
    }
    
    os.makedirs('output', exist_ok=True)
    result_filename = f"output/result_{timestamp}.json"
    with open(result_filename, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"\nResult saved to: {result_filename}")
    return result_filename

def _print_custom_results(custom_output_result, blueprint_name, blueprint_fields):
    matched_blueprint_name = custom_output_result['matched_blueprint']['name']
    log(custom_output_result)
    print('\n- Custom output')
    print(f"Matched blueprint: {matched_blueprint_name}  Confidence: {custom_output_result['matched_blueprint']['confidence']}")
    print(f"Document class: {custom_output_result['document_class']['type']}")
    if matched_blueprint_name == blueprint_name:
        print('\n- Fields')
        for field_with_group in blueprint_fields:
            _print_field(field_with_group, custom_output_result)
    return _extract_fields_from_custom_output(custom_output_result, blueprint_name, blueprint_fields)

def _print_field(field_with_group, custom_output_result):
    inference_result = custom_output_result['inference_result']
    explainability_info = custom_output_result['explainability_info'][0]
    if '/' in field_with_group:
        # For fields part of a group
        (group, field) = field_with_group.split('/')
        inference_result = inference_result[group]
        explainability_info = explainability_info[group]
    else:
        field = field_with_group
    value = inference_result[field]
    confidence = explainability_info[field]['confidence']
    print(f'{field}: {value or '<EMPTY>'}  Confidence: {confidence}')