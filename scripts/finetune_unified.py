#!/usr/bin/env python3
"""
Unified Fine-Tuning Script for CloudFuze Chatbot
Professional hybrid combining all features from manage_fine_tuning.py and finetune_from_langfuse.py

Features:
- Auto-detects data format (Langfuse or standard)
- Converts Langfuse exports automatically
- Validates data quality with scoring
- Deduplicates entries
- Real-time progress monitoring with live progress bar
- Status checking and monitoring
- Cleanup and merge commands
- Dry-run mode
- Handles large datasets efficiently

Usage:
    # Fine-tune with Langfuse export
    python scripts/finetune_unified.py start-langfuse FILE.jsonl
    
    # Fine-tune with standard corrections.jsonl
    python scripts/finetune_unified.py start
    
    # Auto-detect format and fine-tune
    python scripts/finetune_unified.py auto FILE.jsonl
    
    # Validate only
    python scripts/finetune_unified.py validate FILE.jsonl
    
    # Check status
    python scripts/finetune_unified.py status [JOB_ID]
    
    # Monitor live with progress bar
    python scripts/finetune_unified.py monitor [JOB_ID]
    
    # End-to-end: Start and auto-monitor until completion
    python scripts/finetune_unified.py auto FILE.jsonl --monitor
    
    # Cleanup old files
    python scripts/finetune_unified.py cleanup
    
    # Merge legacy files
    python scripts/finetune_unified.py merge
    
    # Dry-run
    python scripts/finetune_unified.py start-langfuse FILE.jsonl --dry-run
"""

import json
import os
import sys
import glob
import hashlib
import argparse
import time
import shutil
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ======================== CONFIGURATION ========================

DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
MIN_RECOMMENDED_SAMPLES = 10
OUTPUT_DIR = "./data/fine_tuning_dataset"
STATUS_FILE = "./data/fine_tuning_status.json"

SYSTEM_PROMPT = """You are an expert assistant specializing in Slack, Microsoft Teams, and Slack to Microsoft Teams migrations via CloudFuze. 

You help users with:
- Slack features, functionality, and best practices
- Microsoft Teams features, functionality, and best practices  
- Slack to Microsoft Teams migration processes, tools, and strategies
- Comparing Slack and Teams capabilities
- Migration planning, execution, and post-migration support

Provide accurate, helpful, and specific information. Use the context provided to give comprehensive answers. If a question is completely unrelated to Slack, Teams, or migrations, politely redirect to the support team."""

# ======================== FORMAT DETECTION ========================

def detect_data_format(file_path: str) -> str:
    """
    Auto-detect whether file is Langfuse format or standard format.
    
    Returns:
        'langfuse' | 'standard' | 'unknown'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if not first_line:
                return 'unknown'
            
            data = json.loads(first_line)
            
            # Check for Langfuse format (has expectedOutput)
            if 'expectedOutput' in data and 'input' in data:
                return 'langfuse'
            # Check for standard format (has corrected_output)
            elif 'corrected_output' in data and 'input' in data:
                return 'standard'
            else:
                return 'unknown'
    except Exception as e:
        print(f"[ERROR] Could not detect format: {e}")
        return 'unknown'

# ======================== LANGFUSE CONVERSION ========================

def convert_langfuse_to_openai_format(langfuse_file: str) -> Tuple[List[Dict], Dict]:
    """Convert Langfuse dataset export to OpenAI fine-tuning format."""
    print(f"\n[*] Converting Langfuse export: {langfuse_file}")
    
    if not os.path.exists(langfuse_file):
        raise FileNotFoundError(f"File not found: {langfuse_file}")
    
    training_data = []
    skipped_count = 0
    invalid_count = 0
    seen_hashes = set()
    
    with open(langfuse_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                item = json.loads(line.strip())
                
                # Extract input and expected output
                input_text = item.get('input', '')
                expected_output = item.get('expectedOutput', '')
                
                # Validate
                if not input_text or not expected_output:
                    print(f"[WARNING] Line {line_num}: Missing input or expectedOutput")
                    invalid_count += 1
                    continue
                
                # Check for duplicates
                content_hash = hashlib.md5(f"{input_text}|||{expected_output}".encode()).hexdigest()
                if content_hash in seen_hashes:
                    skipped_count += 1
                    continue
                seen_hashes.add(content_hash)
                
                # Convert to OpenAI format
                training_example = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": input_text},
                        {"role": "assistant", "content": expected_output}
                    ]
                }
                
                training_data.append(training_example)
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] Line {line_num}: Invalid JSON - {e}")
                invalid_count += 1
            except Exception as e:
                print(f"[ERROR] Line {line_num}: {e}")
                invalid_count += 1
    
    # Statistics
    stats = {
        "total_lines": line_num,
        "valid_examples": len(training_data),
        "duplicates_removed": skipped_count,
        "invalid_entries": invalid_count,
        "success_rate": (len(training_data) / line_num * 100) if line_num > 0 else 0
    }
    
    print(f"\n[OK] Conversion complete:")
    print(f"   Valid examples: {stats['valid_examples']}")
    print(f"   Duplicates removed: {stats['duplicates_removed']}")
    print(f"   Invalid entries: {stats['invalid_entries']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    
    return training_data, stats

# ======================== STANDARD FORMAT LOADING ========================

def load_standard_corrections() -> Tuple[List[Dict], Dict]:
    """Load corrections from standard format (corrections.jsonl)."""
    print(f"\n[*] Loading from standard corrections format...")
    
    all_corrections = []
    seen_hashes = set()
    invalid_count = 0
    duplicates_count = 0
    
    # Load from unified file
    single_file = f"{OUTPUT_DIR}/corrections.jsonl"
    if os.path.exists(single_file):
        print(f"[*] Loading: {single_file}")
        with open(single_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    correction = json.loads(line.strip())
                    
                    # Check for required fields
                    if 'input' not in correction or 'corrected_output' not in correction:
                        invalid_count += 1
                        continue
                    
                    # Check for duplicates
                    content_hash = hashlib.md5(
                        f"{correction['input']}|||{correction['corrected_output']}".encode()
                    ).hexdigest()
                    
                    if content_hash in seen_hashes:
                        duplicates_count += 1
                        continue
                    seen_hashes.add(content_hash)
                    
                    all_corrections.append(correction)
                    
                except json.JSONDecodeError as e:
                    print(f"[WARNING] Line {line_num}: Invalid JSON - {e}")
                    invalid_count += 1
    
    # Also load legacy daily files if they exist
    legacy_files = glob.glob(f"{OUTPUT_DIR}/corrections_*.jsonl")
    if legacy_files:
        print(f"[TIP] Found {len(legacy_files)} legacy files. Run 'merge' command to consolidate")
        
        for file_path in legacy_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        correction = json.loads(line.strip())
                        if 'input' in correction and 'corrected_output' in correction:
                            content_hash = hashlib.md5(
                                f"{correction['input']}|||{correction['corrected_output']}".encode()
                            ).hexdigest()
                            if content_hash not in seen_hashes:
                                seen_hashes.add(content_hash)
                                all_corrections.append(correction)
                            else:
                                duplicates_count += 1
                    except:
                        invalid_count += 1
    
    stats = {
        "total_lines": len(all_corrections) + duplicates_count + invalid_count,
        "valid_examples": len(all_corrections),
        "duplicates_removed": duplicates_count,
        "invalid_entries": invalid_count,
        "success_rate": (len(all_corrections) / (len(all_corrections) + duplicates_count + invalid_count) * 100) 
                        if (len(all_corrections) + duplicates_count + invalid_count) > 0 else 0
    }
    
    print(f"\n[OK] Loading complete:")
    print(f"   Valid corrections: {stats['valid_examples']}")
    print(f"   Duplicates removed: {stats['duplicates_removed']}")
    print(f"   Invalid entries: {stats['invalid_entries']}")
    
    return all_corrections, stats

def prepare_training_data(corrections: List[Dict]) -> List[Dict]:
    """Prepare data in OpenAI fine-tuning format."""
    training_data = []
    
    for correction in corrections:
        training_example = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": correction["input"]},
                {"role": "assistant", "content": correction["corrected_output"]}
            ]
        }
        training_data.append(training_example)
    
    return training_data

# ======================== DATA QUALITY ANALYSIS ========================

def analyze_dataset_quality(training_data: List[Dict]) -> Dict[str, Any]:
    """Analyze dataset quality metrics."""
    
    if not training_data:
        return {"quality_score": 0, "quality_rating": "empty", "issues": []}
    
    # Extract data for analysis
    inputs = [ex["messages"][1]["content"] for ex in training_data]
    outputs = [ex["messages"][2]["content"] for ex in training_data]
    
    input_lengths = [len(text) for text in inputs]
    output_lengths = [len(text) for text in outputs]
    
    # Calculate metrics
    unique_inputs = len(set(inputs))
    diversity_ratio = unique_inputs / len(inputs)
    
    avg_input_len = sum(input_lengths) / len(input_lengths)
    avg_output_len = sum(output_lengths) / len(output_lengths)
    
    short_outputs = sum(1 for length in output_lengths if length < 100)
    very_long_outputs = sum(1 for length in output_lengths if length > 3000)
    
    # Quality scoring
    quality_score = 100
    issues = []
    
    if len(training_data) < MIN_RECOMMENDED_SAMPLES:
        quality_score -= 30
        issues.append(f"Small dataset size ({len(training_data)} < {MIN_RECOMMENDED_SAMPLES})")
    
    if diversity_ratio < 0.8:
        quality_score -= 20
        issues.append(f"Low input diversity ({diversity_ratio*100:.1f}%)")
    
    if short_outputs > len(training_data) * 0.3:
        quality_score -= 15
        issues.append(f"Many short outputs ({short_outputs} < 100 chars)")
    
    if very_long_outputs > len(training_data) * 0.2:
        quality_score -= 10
        issues.append(f"Many very long outputs ({very_long_outputs} > 3000 chars)")
    
    # Rating
    if quality_score >= 90:
        rating = "excellent"
    elif quality_score >= 70:
        rating = "good"
    elif quality_score >= 50:
        rating = "fair"
    else:
        rating = "poor"
    
    return {
        "total_examples": len(training_data),
        "unique_inputs": unique_inputs,
        "diversity_ratio": diversity_ratio,
        "avg_input_length": avg_input_len,
        "avg_output_length": avg_output_len,
        "min_input_length": min(input_lengths),
        "max_input_length": max(input_lengths),
        "min_output_length": min(output_lengths),
        "max_output_length": max(output_lengths),
        "short_outputs": short_outputs,
        "very_long_outputs": very_long_outputs,
        "quality_score": quality_score,
        "quality_rating": rating,
        "issues": issues
    }

def display_quality_report(analysis: Dict):
    """Display comprehensive quality report."""
    print("\n" + "=" * 70)
    print("DATASET QUALITY REPORT")
    print("=" * 70)
    
    print(f"\nDataset Statistics:")
    print(f"   Total examples: {analysis['total_examples']}")
    print(f"   Unique inputs: {analysis['unique_inputs']}")
    print(f"   Input diversity: {analysis['diversity_ratio']*100:.1f}%")
    
    print(f"\nLength Statistics:")
    print(f"   Average input: {analysis['avg_input_length']:.0f} characters")
    print(f"   Average output: {analysis['avg_output_length']:.0f} characters")
    print(f"   Input range: {analysis['min_input_length']} - {analysis['max_input_length']} chars")
    print(f"   Output range: {analysis['min_output_length']} - {analysis['max_output_length']} chars")
    
    print(f"\nQuality Assessment:")
    print(f"   Quality Score: {analysis['quality_score']}/100")
    print(f"   Quality Rating: {analysis['quality_rating'].upper()}")
    
    if analysis['issues']:
        print(f"\nQuality Issues:")
        for issue in analysis['issues']:
            print(f"   - {issue}")
    else:
        print(f"\n[OK] No quality issues detected!")
    
    print(f"\nRecommendations:")
    if analysis['total_examples'] < 50:
        print(f"   - Aim for 50-100 examples for production fine-tuning")
    elif analysis['total_examples'] >= 50:
        print(f"   - Excellent dataset size for high-quality fine-tuning!")
    
    if analysis['diversity_ratio'] < 0.8:
        print(f"   - Consider adding more diverse examples")
    
    if analysis['short_outputs'] > analysis['total_examples'] * 0.3:
        print(f"   - Review short outputs - ensure comprehensive responses")
    
    print("=" * 70)

# ======================== FINE-TUNING ========================

def save_training_file(training_data: List[Dict]) -> str:
    """Save training data to JSONL file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{OUTPUT_DIR}/training_data_{timestamp}.jsonl"
    
    print(f"\n[*] Saving training file: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        for example in training_data:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    file_size = os.path.getsize(filename) / 1024  # KB
    print(f"[OK] Saved {len(training_data)} examples ({file_size:.1f} KB)")
    
    return filename

def start_fine_tuning(training_file: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """Upload and start OpenAI fine-tuning job."""
    
    print(f"\n[*] Starting fine-tuning process...")
    print(f"   Model: {model}")
    print(f"   Training file: {training_file}")
    
    try:
        client = OpenAI()
        
        # Upload file
        print(f"\n[*] Uploading to OpenAI...")
        with open(training_file, 'rb') as f:
            upload_response = client.files.create(file=f, purpose="fine-tune")
        
        print(f"[OK] File uploaded: {upload_response.id}")
        
        # Start fine-tuning
        print(f"[*] Creating fine-tuning job...")
        fine_tune_response = client.fine_tuning.jobs.create(
            training_file=upload_response.id,
            model=model
        )
        
        print(f"[OK] Fine-tuning job started!")
        print(f"   Job ID: {fine_tune_response.id}")
        print(f"   Status: {fine_tune_response.status}")
        
        # Save status
        status_info = {
            "job_id": fine_tune_response.id,
            "status": fine_tune_response.status,
            "model": model,
            "training_file_id": upload_response.id,
            "local_training_file": training_file,
            "created_at": datetime.now().isoformat(),
            "training_examples": len(open(training_file, 'r', encoding='utf-8').readlines())
        }
        
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_info, f, indent=2, ensure_ascii=False)
        
        return fine_tune_response.id
        
    except Exception as e:
        print(f"[ERROR] Fine-tuning failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# ======================== STATUS CHECKING ========================

def check_fine_tuning_status(job_id: Optional[str] = None):
    """Check the status of fine-tuning jobs."""
    try:
        client = OpenAI()
        
        print("\n" + "=" * 70)
        print("FINE-TUNING JOBS STATUS")
        print("=" * 70)
        
        if job_id:
            try:
                job = client.fine_tuning.jobs.retrieve(job_id)
                display_job_status(job)
            except Exception as e:
                print(f"[ERROR] Could not retrieve job {job_id}: {e}")
        else:
            jobs = client.fine_tuning.jobs.list(limit=10)
            
            if not jobs.data:
                print("\n[*] No fine-tuning jobs found")
                return
            
            relevant_jobs = [job for job in jobs.data if "gpt-4o-mini" in job.model]
            
            if not relevant_jobs:
                print("\n[*] No relevant fine-tuning jobs found")
                return
            
            print(f"\n[*] Found {len(relevant_jobs)} fine-tuning job(s)\n")
            
            for idx, job in enumerate(relevant_jobs, 1):
                print(f"\n--- Job {idx} ---")
                display_job_status(job)
        
        # Display local status
        display_local_status()
        
    except Exception as e:
        print(f"[ERROR] Error checking status: {e}")
        import traceback
        traceback.print_exc()

def display_job_status(job):
    """Display formatted job status."""
    print(f"\nJob ID: {job.id}")
    print(f"Model: {job.model}")
    print(f"Status: {job.status}")
    print(f"Created: {datetime.fromtimestamp(job.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if job.fine_tuned_model:
        print(f"Fine-tuned Model: {job.fine_tuned_model}")
    
    if hasattr(job, 'trained_tokens') and job.trained_tokens:
        print(f"Trained Tokens: {job.trained_tokens:,}")
    
    # Status-specific messages
    if job.status == "succeeded":
        print(f"\n[SUCCESS] Job completed successfully!")
        print(f"   Fine-tuned model: {job.fine_tuned_model}")
        print(f"\n   To use this model, update app/endpoints.py:")
        print(f"   model_name=\"{job.fine_tuned_model}\"")
    elif job.status == "failed":
        print(f"\n[FAILED] Job failed")
        if hasattr(job, 'error') and job.error:
            print(f"   Error: {job.error}")
    elif job.status == "running":
        print(f"\n[IN PROGRESS] Job is running...")
        print(f"   Estimated time: 20 minutes to 2 hours")
    elif job.status == "validating_files":
        print(f"\n[VALIDATING] Validating training files...")
    elif job.status == "queued":
        print(f"\n[QUEUED] Job is queued and will start soon...")

def display_local_status():
    """Display local status file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                local_status = json.load(f)
            
            print(f"\n" + "-" * 70)
            print("LOCAL STATUS FILE:")
            print("-" * 70)
            print(f"Job ID: {local_status.get('job_id', 'N/A')}")
            print(f"Model: {local_status.get('model', 'N/A')}")
            print(f"Training Examples: {local_status.get('training_examples', 'N/A')}")
            print(f"Created: {local_status.get('created_at', 'N/A')}")
            print(f"Training File: {local_status.get('local_training_file', 'N/A')}")
        except Exception as e:
            print(f"[WARNING] Could not read local status: {e}")

# ======================== REAL-TIME MONITORING ========================

def draw_progress_bar(current: int, total: int, width: int = 50, loss: Optional[float] = None, elapsed: Optional[str] = None) -> str:
    """Draw a fancy progress bar."""
    if total == 0:
        percent = 0
    else:
        percent = int((current / total) * 100)
    
    filled = int((current / total) * width) if total > 0 else 0
    empty = width - filled
    
    bar = "█" * filled + "░" * empty
    
    # Build status line
    status_parts = [f"Step {current}/{total}"]
    if loss is not None:
        status_parts.append(f"Loss: {loss:.4f}")
    if elapsed:
        status_parts.append(f"Elapsed: {elapsed}")
    
    status_line = " | ".join(status_parts)
    
    # Calculate padding for centering
    term_width = 70
    status_padding = (term_width - len(status_line) - 4) // 2
    
    return f"""
┌{'─' * (term_width - 2)}┐
│ {bar} │ {percent}%
│ {status_line.center(term_width - 4)} │
└{'─' * (term_width - 2)}┘
"""

def monitor_fine_tuning_progress(job_id: str, continuous: bool = True):
    """
    Monitor fine-tuning job with real-time progress bar and updates.
    
    Args:
        job_id: Fine-tuning job ID
        continuous: If True, continuously monitor until completion
    """
    try:
        client = OpenAI()
        
        print("\n" + "=" * 70)
        print("REAL-TIME FINE-TUNING MONITOR")
        print("=" * 70)
        print(f"\nJob ID: {job_id}")
        print("Press Ctrl+C to stop monitoring\n")
        
        start_time = datetime.now()
        last_event_id = None
        last_step = 0
        last_loss = None
        total_steps = None
        parse_failures = 0
        
        # Compile regex patterns for more reliable parsing
        step_pattern = re.compile(r'step\s+(\d+)(?:/(\d+))?', re.IGNORECASE)
        loss_pattern = re.compile(r'loss[=:]\s*(\d+\.?\d*)', re.IGNORECASE)
        
        while True:
            try:
                # Get job status
                job = client.fine_tuning.jobs.retrieve(job_id)
                
                # Get recent events
                events = client.fine_tuning.jobs.list_events(job_id, limit=50)
                
                # Process new events
                new_events = []
                for event in reversed(events.data):
                    if last_event_id is None or event.created_at > (last_event_id or 0):
                        new_events.append(event)
                        
                        # Parse event message for step/loss info using regex
                        msg = event.message
                        
                        # Try to extract step information
                        step_match = step_pattern.search(msg)
                        if step_match:
                            try:
                                new_step = int(step_match.group(1))
                                # Validate: step should only increase (or equal)
                                if new_step >= last_step:
                                    last_step = new_step
                                    parse_failures = 0  # Reset failure counter
                                    
                                    # Extract total steps if available
                                    if step_match.group(2):
                                        new_total = int(step_match.group(2))
                                        # Validate: total should only stay same or increase
                                        if total_steps is None or new_total >= total_steps:
                                            total_steps = new_total
                                else:
                                    # Step decreased - likely out-of-order event
                                    pass
                            except (ValueError, IndexError) as e:
                                parse_failures += 1
                        
                        # Try to extract loss information
                        loss_match = loss_pattern.search(msg)
                        if loss_match:
                            try:
                                last_loss = float(loss_match.group(1))
                            except (ValueError, IndexError):
                                pass
                
                if new_events:
                    last_event_id = new_events[-1].created_at
                    
                    # Display new events
                    for event in new_events:
                        timestamp = datetime.fromtimestamp(event.created_at)
                        print(f"[{timestamp.strftime('%H:%M:%S')}] {event.message}")
                
                # Calculate elapsed time
                elapsed = datetime.now() - start_time
                elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
                
                # Display progress bar if we have step info
                if last_step > 0:
                    # Clear previous lines (move cursor up)
                    print("\033[F" * 5, end='')  # Move up 5 lines
                    
                    # Use actual total_steps if available, otherwise estimate
                    display_total = total_steps if total_steps else max(last_step + 50, 200)
                    
                    progress_bar = draw_progress_bar(
                        current=last_step,
                        total=display_total,
                        loss=last_loss,
                        elapsed=elapsed_str
                    )
                    print(progress_bar)
                    
                    # Add validation indicator
                    status_msg = f"Status: {job.status} | Model: {job.model.split('-')[0]}"
                    if total_steps:
                        status_msg += " | Tracking: ✓"
                    else:
                        status_msg += " | Tracking: ~ (estimated)"
                    print(status_msg)
                
                # Check if completed
                if job.status in ['succeeded', 'failed', 'cancelled']:
                    print("\n" + "=" * 70)
                    print(f"[COMPLETED] Status: {job.status.upper()}")
                    print("=" * 70)
                    
                    if job.status == 'succeeded':
                        print(f"\n✅ Fine-tuning completed successfully!")
                        print(f"   Fine-tuned model: {job.fine_tuned_model}")
                        print(f"   Training time: {elapsed_str}")
                        if job.trained_tokens:
                            print(f"   Trained tokens: {job.trained_tokens:,}")
                        if last_step > 0:
                            actual_total = total_steps if total_steps else last_step
                            print(f"   Training steps: {last_step}/{actual_total}")
                        
                        print(f"\n📝 Next step:")
                        print(f"   Update app/endpoints.py with:")
                        print(f"   model_name=\"{job.fine_tuned_model}\"")
                    elif job.status == 'failed':
                        print(f"\n❌ Fine-tuning failed")
                        if hasattr(job, 'error') and job.error:
                            print(f"   Error: {job.error}")
                    else:
                        print(f"\n⚠️  Fine-tuning was cancelled")
                    
                    print("\n" + "=" * 70)
                    break
                
                if not continuous:
                    break
                
                # Wait before next poll
                time.sleep(5)  # Poll every 5 seconds
                
            except KeyboardInterrupt:
                print("\n\n[*] Monitoring stopped by user")
                print(f"   Job is still running. Check status with:")
                print(f"   python scripts/finetune_unified.py status {job_id}")
                break
            except Exception as e:
                print(f"[ERROR] Monitoring error: {e}")
                time.sleep(10)
    
    except Exception as e:
        print(f"[ERROR] Could not start monitoring: {e}")
        import traceback
        traceback.print_exc()

def monitor_command(job_id: Optional[str] = None):
    """Monitor a fine-tuning job with real-time updates."""
    
    # Get job ID from status file if not provided
    if not job_id:
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                    job_id = status.get('job_id')
            except:
                pass
    
    if not job_id:
        print("[ERROR] No job ID provided")
        print("\nUsage:")
        print("  python scripts/finetune_unified.py monitor JOB_ID")
        print("  or run after starting a job (uses last job from status file)")
        return
    
    monitor_fine_tuning_progress(job_id, continuous=True)

# ======================== CLEANUP & MERGE ========================

def cleanup_old_training_files(keep_file: Optional[str] = None):
    """Clean up old training_data_*.jsonl files."""
    try:
        old_files = glob.glob(f"{OUTPUT_DIR}/training_data_*.jsonl")
        deleted_count = 0
        
        for old_file in old_files:
            if keep_file and old_file == keep_file:
                continue
            
            try:
                os.remove(old_file)
                print(f"[OK] Deleted: {os.path.basename(old_file)}")
                deleted_count += 1
            except Exception as e:
                print(f"[WARNING] Could not delete {os.path.basename(old_file)}: {e}")
        
        if deleted_count > 0:
            print(f"[OK] Cleaned up {deleted_count} old file(s)")
    
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

def cleanup_command():
    """Manual cleanup of old training files."""
    print("\n" + "=" * 70)
    print("CLEANUP OLD TRAINING FILES")
    print("=" * 70)
    
    old_files = glob.glob(f"{OUTPUT_DIR}/training_data_*.jsonl")
    
    if not old_files:
        print("\n[*] No training files to clean up")
        return
    
    print(f"\n[*] Found {len(old_files)} training file(s):")
    total_size = 0
    for f in old_files:
        size = os.path.getsize(f) / 1024  # KB
        total_size += size
        modified = datetime.fromtimestamp(os.path.getmtime(f))
        print(f"   - {os.path.basename(f)} ({size:.1f} KB, {modified.strftime('%Y-%m-%d %H:%M')})")
    
    print(f"\n[*] Total size: {total_size:.1f} KB")
    
    response = input("\nDelete all these files? (y/n): ")
    if response.lower() == 'y':
        cleanup_old_training_files()
        print("\n[SUCCESS] Cleanup complete!")
    else:
        print("\n[*] Cleanup cancelled")

def merge_command():
    """Merge legacy daily correction files into single unified file."""
    print("\n" + "=" * 70)
    print("MERGE CORRECTION FILES")
    print("=" * 70)
    
    single_file = f"{OUTPUT_DIR}/corrections.jsonl"
    legacy_files = glob.glob(f"{OUTPUT_DIR}/corrections_*.jsonl")
    
    if not legacy_files:
        print("\n[*] No legacy daily files to merge")
        return
    
    print(f"\n[*] Found {len(legacy_files)} legacy file(s)")
    
    # Count existing corrections in unified file
    existing_count = 0
    existing_trace_ids = set()
    if os.path.exists(single_file):
        with open(single_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        correction = json.loads(line.strip())
                        existing_count += 1
                        existing_trace_ids.add(correction.get('trace_id'))
                    except:
                        pass
        print(f"[*] Unified file already has {existing_count} corrections")
    
    # Load all legacy corrections
    all_corrections = []
    duplicates = 0
    for file_path in legacy_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        correction = json.loads(line.strip())
                        if correction.get('trace_id') in existing_trace_ids:
                            duplicates += 1
                        else:
                            all_corrections.append(correction)
                    except:
                        pass
    
    if not all_corrections:
        print(f"\n[*] All {duplicates} corrections already in unified file")
        print(f"[*] Safe to delete legacy files")
    else:
        print(f"\n[*] Will merge {len(all_corrections)} new corrections")
        if duplicates > 0:
            print(f"[*] Skipping {duplicates} duplicates")
    
    response = input("\nProceed with merge? (y/n): ")
    if response.lower() != 'y':
        print("\n[*] Merge cancelled")
        return
    
    # Append to unified file
    if all_corrections:
        with open(single_file, 'a', encoding='utf-8') as f:
            for correction in all_corrections:
                f.write(json.dumps(correction, ensure_ascii=False) + '\n')
        print(f"\n[OK] Merged {len(all_corrections)} corrections")
    
    # Ask to delete legacy files
    response = input("\nDelete legacy daily files? (y/n): ")
    if response.lower() == 'y':
        for file_path in legacy_files:
            os.remove(file_path)
            print(f"[OK] Deleted {os.path.basename(file_path)}")
        print(f"\n[SUCCESS] Merge complete!")
    else:
        print("\n[*] Legacy files kept")

# ======================== MAIN COMMANDS ========================

def start_langfuse_command(langfuse_file: str, dry_run: bool = False, validate_only: bool = False, model: str = DEFAULT_MODEL, auto_monitor: bool = False):
    """Start fine-tuning from Langfuse export."""
    print("\n" + "=" * 70)
    print("FINE-TUNING FROM LANGFUSE EXPORT")
    if dry_run:
        print("(DRY-RUN MODE)")
    if validate_only:
        print("(VALIDATION ONLY)")
    print("=" * 70)
    
    try:
        # Step 1: Convert Langfuse export
        print("\n[STEP 1] Converting Langfuse export to OpenAI format...")
        training_data, conv_stats = convert_langfuse_to_openai_format(langfuse_file)
        
        if not training_data:
            print("\n[ERROR] No valid training data extracted!")
            sys.exit(1)
        
        # Step 2: Analyze quality
        print("\n[STEP 2] Analyzing dataset quality...")
        analysis = analyze_dataset_quality(training_data)
        display_quality_report(analysis)
        
        # Quality gate
        if analysis['quality_score'] < 50 and not dry_run and not validate_only:
            print(f"\n[WARNING] Quality score is poor ({analysis['quality_score']}/100)")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                print("\n[*] Fine-tuning cancelled")
                return
        
        if validate_only:
            print(f"\n[SUCCESS] Validation complete!")
            print(f"Dataset is ready with {len(training_data)} examples.")
            return
        
        # Step 3: Save training file
        print("\n[STEP 3] Preparing training file...")
        training_file = save_training_file(training_data)
        
        if dry_run:
            print(f"\n[DRY-RUN] Training file ready: {training_file}")
            print(f"[DRY-RUN] Would start fine-tuning with {len(training_data)} examples")
            print(f"\nTo actually start fine-tuning, run without --dry-run flag")
            return
        
        # Step 4: Start fine-tuning
        print("\n[STEP 4] Starting OpenAI fine-tuning...")
        job_id = start_fine_tuning(training_file, model)
        
        if job_id:
            print("\n" + "=" * 70)
            print("[SUCCESS] FINE-TUNING JOB STARTED!")
            print("=" * 70)
            print(f"\nJob ID: {job_id}")
            print(f"Training examples: {len(training_data)}")
            print(f"Base model: {model}")
            
            if auto_monitor:
                print("\n" + "=" * 70)
                print("STARTING AUTOMATIC MONITORING...")
                print("=" * 70)
                time.sleep(3)  # Brief pause to let job initialize
                monitor_fine_tuning_progress(job_id, continuous=True)
            else:
                print(f"\nNext steps:")
                print(f"  1. Monitor live: python scripts/finetune_unified.py monitor {job_id}")
                print(f"  2. Or check on OpenAI: https://platform.openai.com/finetune")
                print(f"  3. Wait 20 mins - 2 hours for completion")
                print("=" * 70)
        else:
            print("\n[ERROR] Failed to start fine-tuning job")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

def start_standard_command(dry_run: bool = False, validate_only: bool = False, model: str = DEFAULT_MODEL, auto_monitor: bool = False):
    """Start fine-tuning from standard corrections.jsonl format."""
    print("\n" + "=" * 70)
    print("FINE-TUNING FROM STANDARD FORMAT")
    if dry_run:
        print("(DRY-RUN MODE)")
    if validate_only:
        print("(VALIDATION ONLY)")
    print("=" * 70)
    
    try:
        # Step 1: Load corrections
        print("\n[STEP 1] Loading corrections from standard format...")
        corrections, load_stats = load_standard_corrections()
        
        if not corrections:
            print("\n[ERROR] No corrections found!")
            print(f"   Place corrections in: {OUTPUT_DIR}/corrections.jsonl")
            return
        
        # Step 2: Prepare training data
        training_data = prepare_training_data(corrections)
        
        # Step 3: Analyze quality
        print("\n[STEP 2] Analyzing dataset quality...")
        analysis = analyze_dataset_quality(training_data)
        display_quality_report(analysis)
        
        # Quality gate
        if analysis['quality_score'] < 50 and not dry_run and not validate_only:
            print(f"\n[WARNING] Quality score is poor ({analysis['quality_score']}/100)")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                print("\n[*] Fine-tuning cancelled")
                return
        
        if validate_only:
            print(f"\n[SUCCESS] Validation complete!")
            print(f"Dataset is ready with {len(training_data)} examples.")
            return
        
        # Step 4: Save training file
        print("\n[STEP 3] Preparing training file...")
        training_file = save_training_file(training_data)
        
        if dry_run:
            print(f"\n[DRY-RUN] Training file ready: {training_file}")
            print(f"[DRY-RUN] Would start fine-tuning with {len(training_data)} examples")
            print(f"\nTo actually start fine-tuning, run without --dry-run flag")
            return
        
        # Step 5: Start fine-tuning
        print("\n[STEP 4] Starting OpenAI fine-tuning...")
        job_id = start_fine_tuning(training_file, model)
        
        if job_id:
            print("\n" + "=" * 70)
            print("[SUCCESS] FINE-TUNING JOB STARTED!")
            print("=" * 70)
            print(f"\nJob ID: {job_id}")
            print(f"Training examples: {len(training_data)}")
            print(f"Base model: {model}")
            
            if auto_monitor:
                print("\n" + "=" * 70)
                print("STARTING AUTOMATIC MONITORING...")
                print("=" * 70)
                time.sleep(3)  # Brief pause to let job initialize
                monitor_fine_tuning_progress(job_id, continuous=True)
            else:
                print(f"\nNext steps:")
                print(f"  1. Monitor live: python scripts/finetune_unified.py monitor {job_id}")
                print(f"  2. Or check on OpenAI: https://platform.openai.com/finetune")
                print(f"  3. Wait 20 mins - 2 hours for completion")
                print("=" * 70)
        else:
            print("\n[ERROR] Failed to start fine-tuning job")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

def auto_detect_command(file_path: str, dry_run: bool = False, validate_only: bool = False, model: str = DEFAULT_MODEL, auto_monitor: bool = False):
    """Auto-detect format and start fine-tuning."""
    print("\n[*] Auto-detecting data format...")
    
    format_type = detect_data_format(file_path)
    
    if format_type == 'langfuse':
        print(f"[OK] Detected Langfuse format")
        start_langfuse_command(file_path, dry_run, validate_only, model, auto_monitor)
    elif format_type == 'standard':
        print(f"[OK] Detected standard format")
        # Copy to standard location and process
        import shutil
        dest = f"{OUTPUT_DIR}/corrections.jsonl"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        shutil.copy(file_path, dest)
        start_standard_command(dry_run, validate_only, model, auto_monitor)
    else:
        print(f"[ERROR] Unknown format")
        print(f"   Expected either:")
        print(f"   - Langfuse format: {{'input': ..., 'expectedOutput': ...}}")
        print(f"   - Standard format: {{'input': ..., 'corrected_output': ...}}")
        sys.exit(1)

def validate_command(file_path: str):
    """Validate a dataset file."""
    format_type = detect_data_format(file_path)
    
    if format_type == 'langfuse':
        start_langfuse_command(file_path, dry_run=False, validate_only=True)
    elif format_type == 'standard':
        import shutil
        dest = f"{OUTPUT_DIR}/corrections.jsonl"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        shutil.copy(file_path, dest)
        start_standard_command(dry_run=False, validate_only=True)
    else:
        print(f"[ERROR] Unknown format - cannot validate")
        sys.exit(1)

# ======================== CLI ========================

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Unified Fine-Tuning Script - Supports both Langfuse and standard formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fine-tune with Langfuse export
  python scripts/finetune_unified.py start-langfuse FILE.jsonl
  
  # Fine-tune with standard format
  python scripts/finetune_unified.py start
  
  # Auto-detect format
  python scripts/finetune_unified.py auto FILE.jsonl
  
  # Validate only
  python scripts/finetune_unified.py validate FILE.jsonl
  
  # Dry-run
  python scripts/finetune_unified.py start-langfuse FILE.jsonl --dry-run
  
  # Auto-monitor (end-to-end: validate, start, and monitor until completion)
  python scripts/finetune_unified.py auto FILE.jsonl --monitor
  
  # Check status
  python scripts/finetune_unified.py status [JOB_ID]
  
  # Monitor live (with progress bar)
  python scripts/finetune_unified.py monitor [JOB_ID]
  
  # Cleanup
  python scripts/finetune_unified.py cleanup
  
  # Merge legacy files
  python scripts/finetune_unified.py merge
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start-langfuse', 'start', 'auto', 'validate', 'status', 'monitor', 'cleanup', 'merge'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'arg',
        nargs='?',
        help='File path or job ID (depends on command)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Prepare but do not upload to OpenAI'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Automatically monitor job progress after starting (runs until completion)'
    )
    
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help=f'Base model to fine-tune (default: {DEFAULT_MODEL})'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'start-langfuse':
            if not args.arg:
                print("[ERROR] Please provide Langfuse file path")
                sys.exit(1)
            start_langfuse_command(args.arg, args.dry_run, False, args.model, args.monitor)
        
        elif args.command == 'start':
            start_standard_command(args.dry_run, False, args.model, args.monitor)
        
        elif args.command == 'auto':
            if not args.arg:
                print("[ERROR] Please provide file path")
                sys.exit(1)
            auto_detect_command(args.arg, args.dry_run, False, args.model, args.monitor)
        
        elif args.command == 'validate':
            if not args.arg:
                print("[ERROR] Please provide file path to validate")
                sys.exit(1)
            validate_command(args.arg)
        
        elif args.command == 'status':
            check_fine_tuning_status(args.arg)
        
        elif args.command == 'monitor':
            monitor_command(args.arg)
        
        elif args.command == 'cleanup':
            cleanup_command()
        
        elif args.command == 'merge':
            merge_command()
    
    except KeyboardInterrupt:
        print("\n\n[*] Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

