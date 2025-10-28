#!/usr/bin/env python3
"""
Process bad traces and log corrected responses back to Langfuse for manual review

Workflow:
1. Read bad_responses.jsonl (exported from Langfuse with thumbs down feedback)
2. For each bad trace:
   - Extract question and bad response
   - Generate improved response using RAG (vectorstore + GPT-4o-mini)
   - Log correction to Langfuse as an observation/span
3. Review corrections in Langfuse UI
4. Manually add good corrections to Dataset in Langfuse
5. Export Dataset as JSONL
6. Fine-tune with scripts/finetune_unified.py

Usage:
    python scripts/process_bad_traces_and_log_to_langfuse.py [input_file.jsonl]
    
    Default input: data/bad_responses.jsonl
    
Example:
    python scripts/process_bad_traces_and_log_to_langfuse.py data/bad_responses.jsonl
"""

import json
import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.endpoints import generate_improved_response
from app.langfuse_integration import langfuse_tracker

async def process_single_trace(trace_data, line_num):
    """
    Process a single bad trace and generate correction
    
    Args:
        trace_data: Dictionary with trace data from JSONL
        line_num: Line number for logging
    
    Returns:
        tuple: (success, trace_id, question, bad_response, corrected_response)
    """
    try:
        # Extract fields from Langfuse export format
        trace_id = trace_data.get('id', '')
        question = trace_data.get('input', '')
        bad_response = trace_data.get('output', '')
        
        if not question or not bad_response:
            print(f"[WARNING] Line {line_num}: Missing input or output, skipping")
            return (False, trace_id, None, None, None, None)
        
        print(f"\n[{line_num}] Processing trace: {trace_id}")
        print(f"    Question: {question[:80]}...")
        
        # Generate improved response using RAG
        print(f"    => Generating improved response using RAG...")
        corrected_response, context_info = await generate_improved_response(
            user_query=question,
            bad_response=bad_response,
            user_comment="Auto-generated correction from manual review workflow"
        )
        
        print(f"    [OK] Generated correction ({len(corrected_response)} chars)")
        print(f"    [DEBUG] Retrieved {context_info.get('doc_count', 0)} documents for context")
        
        return (True, trace_id, question, bad_response, corrected_response, context_info)
        
    except Exception as e:
        print(f"[ERROR] Line {line_num}: {e}")
        import traceback
        traceback.print_exc()
        return (False, trace_data.get('id', ''), None, None, None, None)

def log_correction_to_langfuse(trace_id, question, bad_response, corrected_response, context_info=None):
    """
    Log the corrected response to Langfuse as an observation
    
    Args:
        trace_id: Original trace ID from Langfuse
        question: Original question
        bad_response: Original bad response
        corrected_response: Generated correction
        context_info: Debug info about retrieved context documents
    
    Returns:
        bool: True if successfully logged, False otherwise
    """
    if not langfuse_tracker or not langfuse_tracker.client:
        print(f"    [WARNING] Langfuse client not available, skipping logging")
        return False
    
    try:
        # Prepare input data (original Q&A)
        input_data = {
            "original_question": question,
            "bad_response": bad_response
        }
        
        # Prepare metadata with context debug info
        metadata = {
            "correction_type": "llm_generated",
            "status": "pending_review",
            "workflow": "correction_with_langfuse_review",
            "generated_at": datetime.now().isoformat()
        }
        
        # Add context debug info if available
        if context_info:
            metadata["context_info"] = context_info
        
        # Log observation to Langfuse
        success = langfuse_tracker.log_observation_to_trace(
            trace_id=trace_id,
            name="corrected_response",
            input_data=input_data,
            output_data=corrected_response,
            metadata=metadata
        )
        
        if success:
            print(f"    [OK] Logged to Langfuse trace: {trace_id}")
        else:
            print(f"    [WARNING] Failed to log to Langfuse")
        
        return success
        
    except Exception as e:
        print(f"    [ERROR] Failed to log to Langfuse: {e}")
        import traceback
        traceback.print_exc()
        return False

async def process_bad_traces(input_file):
    """
    Main function to process all bad traces
    
    Args:
        input_file: Path to JSONL file with bad traces
    """
    print(f"\n{'='*70}")
    print("PROCESSING BAD TRACES AND LOGGING TO LANGFUSE")
    print(f"{'='*70}\n")
    print(f"Input file: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"\n[ERROR] File not found: {input_file}")
        print(f"\nUsage:")
        print(f"  python scripts/process_bad_traces_and_log_to_langfuse.py [input.jsonl]")
        print(f"\nExample:")
        print(f"  python scripts/process_bad_traces_and_log_to_langfuse.py data/bad_responses.jsonl")
        return
    
    # Check Langfuse connection
    if not langfuse_tracker or not langfuse_tracker.client:
        print(f"\n[WARNING] Langfuse client not initialized!")
        print(f"Corrections will be generated but NOT logged to Langfuse.")
        print(f"Check your .env file for LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        print(f"\nContinue anyway? Press Ctrl+C to cancel or wait 5 seconds...")
        await asyncio.sleep(5)
    else:
        print(f"\n[OK] Langfuse client initialized")
    
    processed = 0
    failed = 0
    logged_to_langfuse = 0
    
    print(f"\nStarting processing...\n")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                trace_data = json.loads(line.strip())
                
                # Process the trace and generate correction
                success, trace_id, question, bad_response, corrected_response, context_info = await process_single_trace(
                    trace_data, 
                    line_num
                )
                
                if not success:
                    failed += 1
                    continue
                
                # Log to Langfuse with context debug info
                logged = log_correction_to_langfuse(
                    trace_id=trace_id,
                    question=question,
                    bad_response=bad_response,
                    corrected_response=corrected_response,
                    context_info=context_info
                )
                
                if logged:
                    logged_to_langfuse += 1
                
                processed += 1
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] Line {line_num}: Invalid JSON - {e}")
                failed += 1
                continue
            except Exception as e:
                print(f"[ERROR] Line {line_num}: Unexpected error - {e}")
                import traceback
                traceback.print_exc()
                failed += 1
                continue
    
    # Print summary
    print(f"\n{'='*70}")
    print("PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"\n[OK] Successfully processed: {processed} traces")
    print(f"[INFO] Logged to Langfuse: {logged_to_langfuse} corrections")
    print(f"[WARNING] Failed: {failed} traces")
    
    if logged_to_langfuse > 0:
        print(f"\n{'='*70}")
        print("NEXT STEPS - MANUAL REVIEW IN LANGFUSE")
        print(f"{'='*70}")
        print(f"\n1. Open Langfuse UI -> Tracing tab")
        print(f"   URL: https://cloud.langfuse.com (or your Langfuse host)")
        print(f"\n2. Filter traces:")
        print(f"   - Name: 'manual_correction_review'")
        print(f"   - Look for 'corrected_response' spans")
        print(f"\n3. Review each correction:")
        print(f"   - Click on trace to see details")
        print(f"   - Check 'corrected_response' span")
        print(f"   - Review quality of generated correction")
        print(f"\n4. For GOOD corrections:")
        print(f"   a. Copy the corrected response text")
        print(f"   b. Go to Datasets tab -> Create/Open dataset")
        print(f"   c. Add new item:")
        print(f"      - input: <original question>")
        print(f"      - expectedOutput: <corrected response>")
        print(f"\n5. After curating dataset:")
        print(f"   a. Export Dataset as JSONL from Langfuse")
        print(f"   b. Run fine-tuning:")
        print(f"      python scripts/finetune_unified.py auto DATASET.jsonl --monitor")
        print(f"\n{'='*70}\n")
    else:
        print(f"\n[WARNING] No corrections were logged to Langfuse.")
        print(f"Check your Langfuse configuration in .env file.")
    
    print()

if __name__ == "__main__":
    # Get input file from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/bad_responses.jsonl"
    
    print(f"")
    print(f"{'='*70}")
    print(f"MANUAL CORRECTION WORKFLOW - BATCH PROCESSOR")
    print(f"{'='*70}")
    print(f"")
    print(f"This script will:")
    print(f"  1. Read bad traces from: {input_file}")
    print(f"  2. Generate corrections using RAG (vectorstore + GPT-4o-mini)")
    print(f"  3. Log corrections to Langfuse for manual review")
    print(f"")
    
    # Run async processing
    asyncio.run(process_bad_traces(input_file))

