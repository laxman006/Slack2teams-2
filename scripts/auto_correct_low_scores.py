#!/usr/bin/env python3
"""
Auto-Correction Script for Low-Scored Responses from Langfuse LLM Judge

This script polls Langfuse for traces where the LLM Judge (response_quality_judge) 
has given a score < 6, automatically generates improved responses using RAG,
and logs them back to Langfuse as observations.

Workflow:
1. Poll Langfuse for traces with evaluation score < 6
2. For each low-scored trace:
   - Extract question and bad response
   - Generate improved response using RAG (vectorstore + GPT-4o-mini)
   - Log correction to Langfuse as "improved_response" observation
3. Sleep and repeat

Usage:
    # Run once
    python scripts/auto_correct_low_scores.py
    
    # Run in continuous polling mode (checks every 5 minutes)
    python scripts/auto_correct_low_scores.py --poll --interval 300

Options:
    --poll              Enable continuous polling mode
    --interval SECONDS  Polling interval in seconds (default: 300 = 5 minutes)
    --min-score SCORE   Minimum score threshold (default: 6)
    --limit N           Max number of traces to process per run (default: 10)
    --dry-run           Show what would be corrected without actually doing it
"""

import json
import os
import sys
import asyncio
import argparse
import time
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.endpoints import generate_improved_response
from app.langfuse_integration import langfuse_tracker
from langfuse import Langfuse
from config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST


class AutoCorrectionProcessor:
    """Handles automatic correction of low-scored responses"""
    
    def __init__(self, min_score: int = 6, dry_run: bool = False):
        """
        Initialize the processor
        
        Args:
            min_score: Score threshold - process traces with score < this value
            dry_run: If True, show what would be done without actually doing it
        """
        self.min_score = min_score
        self.dry_run = dry_run
        self.client = langfuse_tracker.client if langfuse_tracker else None
        self.processed_traces = set()  # Track processed traces to avoid duplicates
        self.langfuse_host = LANGFUSE_HOST
        self.langfuse_public_key = LANGFUSE_PUBLIC_KEY
        self.langfuse_secret_key = LANGFUSE_SECRET_KEY
        
        if not self.client:
            raise ValueError("Langfuse client not initialized! Check your .env configuration.")
    
    def fetch_scores_via_rest_api(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch scores directly using Langfuse REST API
        This bypasses the SDK and gets scores that aren't populated in trace objects
        
        Args:
            limit: Maximum number of scores to fetch
            
        Returns:
            List of score dictionaries
        """
        try:
            url = f"{self.langfuse_host}/api/public/scores"
            
            auth = (self.langfuse_public_key, self.langfuse_secret_key)
            params = {
                "name": "response_quality_judge",
                "limit": limit
            }
            
            with httpx.Client() as client:
                response = client.get(url, auth=auth, params=params, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                scores = data.get('data', [])
                return scores
                
        except Exception as e:
            print(f"[WARNING] REST API fetch failed: {e}")
            return []
    
    def get_low_scored_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch traces with evaluation scores below threshold from Langfuse
        
        Args:
            limit: Maximum number of traces to fetch
            
        Returns:
            List of trace data dictionaries
        """
        try:
            print(f"\n[*] Fetching traces with score < {self.min_score}...")
            
            # ALTERNATIVE APPROACH: Fetch scores directly using REST API
            # This is more efficient and works better with the Langfuse API
            try:
                # If processing all (high limit), fetch many more scores
                # Langfuse API has a max limit, so we cap at 100
                fetch_limit = min(limit * 3, 100) if limit < 999999 else 100
                scores_data = self.fetch_scores_via_rest_api(limit=fetch_limit)
                
                if not scores_data:
                    print(f"[*] No scores available, trying alternative method...")
                    raise Exception("No scores from REST API")
                
                print(f"[*] Found {len(scores_data)} total scores from response_quality_judge")
                
                low_scored_traces = []
                processed_trace_ids = set()
                
                for score in scores_data:
                    # Skip if already processed
                    trace_id = score.get('traceId')
                    score_value = score.get('value')
                    
                    if not trace_id or score_value is None:
                        continue
                    
                    if trace_id in self.processed_traces or trace_id in processed_trace_ids:
                        continue
                    
                    # Check if score is below threshold
                    if score_value < self.min_score:
                        # Rate limiting
                        time.sleep(0.5)
                        
                        # Fetch the original trace details
                        try:
                            trace_response = self.client.fetch_trace(trace_id)
                            
                            if trace_response:
                                # Access the trace data from the response
                                trace_data = trace_response.data if hasattr(trace_response, 'data') else trace_response
                                
                                low_scored_traces.append({
                                    'trace_id': trace_id,  # Use the trace_id we already have
                                    'question': getattr(trace_data, 'input', None) or trace_data.get('input') if isinstance(trace_data, dict) else getattr(trace_data, 'input', ''),
                                    'bad_response': getattr(trace_data, 'output', None) or trace_data.get('output') if isinstance(trace_data, dict) else getattr(trace_data, 'output', ''),
                                    'score': score_value,
                                    'user_id': getattr(trace_data, 'user_id', None) or trace_data.get('user_id') if isinstance(trace_data, dict) else getattr(trace_data, 'user_id', ''),
                                    'session_id': getattr(trace_data, 'session_id', None) or trace_data.get('session_id') if isinstance(trace_data, dict) else getattr(trace_data, 'session_id', ''),
                                    'metadata': getattr(trace_data, 'metadata', None) or trace_data.get('metadata') if isinstance(trace_data, dict) else {},
                                    'timestamp': getattr(trace_data, 'timestamp', None) or trace_data.get('timestamp') if isinstance(trace_data, dict) else None
                                })
                                processed_trace_ids.add(trace_id)
                                
                                if len(low_scored_traces) >= limit:
                                    break
                        except Exception as trace_error:
                            print(f"[WARNING] Error fetching trace {trace_id[:8]}...: {str(trace_error)[:100]}")
                            continue
                
                print(f"[OK] Found {len(low_scored_traces)} traces with score < {self.min_score}")
                return low_scored_traces
                
            except Exception as api_error:
                # If REST API fails, fall back to old method
                print(f"[WARNING] REST API approach failed, using fallback method")
                pass
            
            # FALLBACK: Original method (fetch traces then check scores)
            print(f"[*] Using fallback method: fetching traces and checking scores...")
            traces = self.client.fetch_traces(
                tags=["chat"],
                limit=min(limit * 2, 20)
            )
            
            low_scored_traces = []
            api_call_count = 0
            
            for trace in traces.data:
                if trace.id in self.processed_traces:
                    continue
                
                try:
                    api_call_count += 1
                    time.sleep(0.5)
                    
                    if api_call_count % 5 == 0:
                        print(f"    [*] Pausing to respect rate limits...")
                        time.sleep(2)
                    
                    trace_detail = self.client.fetch_trace(trace.id)
                    
                    if trace_detail and hasattr(trace_detail, 'scores'):
                        for score in trace_detail.scores:
                            if score.name == "response_quality_judge":
                                evaluation_score = score.value
                                
                                if evaluation_score < self.min_score:
                                    low_scored_traces.append({
                                        'trace_id': trace.id,
                                        'question': trace.input,
                                        'bad_response': trace.output,
                                        'score': evaluation_score,
                                        'user_id': trace.user_id,
                                        'session_id': trace.session_id,
                                        'metadata': trace.metadata,
                                        'timestamp': trace.timestamp
                                    })
                                    
                                    if len(low_scored_traces) >= limit:
                                        break
                except Exception as e:
                    error_str = str(e).lower()
                    # Handle rate limit errors specifically
                    if "429" in str(e) or "rate limit" in error_str:
                        print(f"    [WARNING] Rate limit hit, waiting 10 seconds before continuing...")
                        time.sleep(10)
                        # Retry this trace once
                        try:
                            trace_detail = self.client.fetch_trace(trace.id)
                            if trace_detail and hasattr(trace_detail, 'scores'):
                                for score in trace_detail.scores:
                                    if score.name == "response_quality_judge":
                                        evaluation_score = score.value
                                        if evaluation_score < self.min_score:
                                            low_scored_traces.append({
                                                'trace_id': trace.id,
                                                'question': trace.input,
                                                'bad_response': trace.output,
                                                'score': evaluation_score,
                                                'user_id': trace.user_id,
                                                'session_id': trace.session_id,
                                                'metadata': trace.metadata,
                                                'timestamp': trace.timestamp
                                            })
                                            if len(low_scored_traces) >= limit:
                                                break
                        except Exception as retry_error:
                            print(f"    [WARNING] Retry failed for {trace.id}, skipping")
                            continue
                    else:
                        print(f"[WARNING] Error fetching trace details for {trace.id}: {e}")
                        continue
                
                if len(low_scored_traces) >= limit:
                    break
            
            print(f"[OK] Found {len(low_scored_traces)} traces with score < {self.min_score}")
            return low_scored_traces
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch traces from Langfuse: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def process_trace(self, trace_data: Dict[str, Any]) -> bool:
        """
        Process a single trace: generate correction and log to Langfuse
        
        Args:
            trace_data: Trace information dictionary
            
        Returns:
            True if successfully processed, False otherwise
        """
        trace_id = trace_data['trace_id']
        question = trace_data['question']
        bad_response = trace_data['bad_response']
        score = trace_data['score']
        
        print(f"\n[*] Processing trace: {trace_id}")
        print(f"    Score: {score:.1f}/{self.min_score}")
        print(f"    Question: {question[:80]}...")
        
        if self.dry_run:
            print(f"    [DRY-RUN] Would generate correction and log to Langfuse")
            return True
        
        try:
            # Generate improved response using RAG
            print(f"    => Generating improved response using RAG...")
            improved_response, context_info = await generate_improved_response(
                user_query=question,
                bad_response=bad_response,
                user_comment=f"Auto-correction triggered by LLM Judge score: {score}"
            )
            
            print(f"    [OK] Generated correction ({len(improved_response)} chars)")
            print(f"    [DEBUG] Retrieved {context_info.get('doc_count', 0)} documents for context")
            
            # Log correction to Langfuse as "improved_response" observation
            success = self.log_correction_to_langfuse(
                trace_id=trace_id,
                question=question,
                bad_response=bad_response,
                improved_response=improved_response,
                original_score=score,
                context_info=context_info
            )
            
            if success:
                # Mark as processed
                self.processed_traces.add(trace_id)
                print(f"    [OK] Logged to Langfuse trace: {trace_id}")
                return True
            else:
                print(f"    [ERROR] Failed to log to Langfuse")
                return False
                
        except Exception as e:
            print(f"    [ERROR] Failed to process trace: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def log_correction_to_langfuse(
        self,
        trace_id: str,
        question: str,
        bad_response: str,
        improved_response: str,
        original_score: float,
        context_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log the improved response to Langfuse as an observation
        
        Args:
            trace_id: Original trace ID from Langfuse
            question: Original question
            bad_response: Original bad response
            improved_response: Generated correction
            original_score: Score from LLM Judge that triggered correction
            context_info: Debug info about retrieved context documents
            
        Returns:
            True if successfully logged, False otherwise
        """
        try:
            # Get the existing trace
            trace = self.client.trace(
                id=trace_id,
                name="auto_correction_workflow"
            )
            
            # Prepare input data
            input_data = {
                "original_question": question,
                "bad_response": bad_response,
                "original_score": original_score,
                "triggered_by": "response_quality_judge"
            }
            
            # Prepare metadata
            metadata = {
                "correction_type": "auto_generated_from_judge",
                "status": "ready_for_review",
                "workflow": "automatic_correction_on_low_score",
                "generated_at": datetime.now().isoformat(),
                "original_score": original_score,
                "score_threshold": self.min_score,
                "judge_evaluator": "response_quality_judge"
            }
            
            # Add context debug info if available
            if context_info:
                metadata["context_info"] = context_info
            
            # Log as "improved_response" observation (span)
            trace.span(
                name="improved_response",
                input=input_data,
                output=improved_response,
                metadata=metadata
            )
            
            # Also add a score to track auto-corrections
            self.client.score(
                trace_id=trace_id,
                name="auto_correction_applied",
                value=1,
                comment=f"Auto-correction generated for score {original_score}"
            )
            
            return True
            
        except Exception as e:
            print(f"    [ERROR] Failed to log to Langfuse: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_once(self, limit: int = 10):
        """
        Run one iteration of processing
        
        Args:
            limit: Maximum number of traces to process
        """
        print(f"\n{'='*70}")
        print("AUTO-CORRECTION FOR LOW-SCORED RESPONSES")
        print(f"{'='*70}\n")
        print(f"Score threshold: < {self.min_score}")
        if limit >= 999999:
            print(f"Processing limit: ALL traces (no limit)")
        else:
            print(f"Processing limit: {limit} traces")
        print(f"Dry run: {self.dry_run}")
        
        # Fetch low-scored traces
        traces = self.get_low_scored_traces(limit=limit)
        
        if not traces:
            print(f"\n[OK] No traces found with score < {self.min_score}")
            return
        
        # Process each trace
        processed = 0
        failed = 0
        
        for trace_data in traces:
            success = await self.process_trace(trace_data)
            if success:
                processed += 1
            else:
                failed += 1
        
        # Print summary
        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"\n[OK] Successfully processed: {processed} traces")
        print(f"[WARNING] Failed: {failed} traces")
        
        if processed > 0 and not self.dry_run:
            print(f"\n{'='*70}")
            print("NEXT STEPS - REVIEW IN LANGFUSE")
            print(f"{'='*70}")
            print(f"\n1. Open Langfuse UI -> Tracing tab")
            print(f"\n2. Filter traces:")
            print(f"   - Name: 'auto_correction_workflow'")
            print(f"   - Look for 'improved_response' spans")
            print(f"\n3. Review each auto-correction:")
            print(f"   - Check quality of generated correction")
            print(f"   - Compare with original bad response")
            print(f"   - Review context_info metadata to see retrieved docs")
            print(f"\n4. For GOOD auto-corrections:")
            print(f"   - Add to Dataset in Langfuse")
            print(f"   - Export Dataset as JSONL")
            print(f"   - Fine-tune with: python scripts/finetune_unified.py auto DATASET.jsonl")
            print(f"\n{'='*70}\n")
    
    async def run_polling(self, interval: int = 300, limit: int = 10):
        """
        Run in continuous polling mode
        
        Args:
            interval: Seconds between polls
            limit: Maximum traces to process per iteration
        """
        print(f"\n{'='*70}")
        print("AUTO-CORRECTION POLLING MODE")
        print(f"{'='*70}\n")
        print(f"Polling interval: {interval} seconds ({interval/60:.1f} minutes)")
        print(f"Score threshold: < {self.min_score}")
        print(f"Traces per run: {limit}")
        print(f"Press Ctrl+C to stop")
        print(f"\n{'='*70}\n")
        
        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting iteration #{iteration}")
                
                await self.run_once(limit=limit)
                
                print(f"\n[*] Sleeping for {interval} seconds...")
                print(f"    Next check at: {(datetime.now() + timedelta(seconds=interval)).strftime('%Y-%m-%d %H:%M:%S')}")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n[*] Polling stopped by user")
            print(f"[OK] Processed {len(self.processed_traces)} unique traces in this session")


async def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Auto-correct low-scored responses from Langfuse LLM Judge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run once (default)
    python scripts/auto_correct_low_scores.py
    
    # Run in polling mode (checks every 5 minutes)
    python scripts/auto_correct_low_scores.py --poll --interval 300
    
    # Dry run to see what would be corrected
    python scripts/auto_correct_low_scores.py --dry-run
    
    # Process up to 20 traces with score < 7
    python scripts/auto_correct_low_scores.py --min-score 7 --limit 20
        """
    )
    
    parser.add_argument(
        '--poll',
        action='store_true',
        help='Enable continuous polling mode'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Polling interval in seconds (default: 300 = 5 minutes)'
    )
    
    parser.add_argument(
        '--min-score',
        type=int,
        default=6,
        help='Minimum score threshold - process traces with score < this value (default: 6)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of traces to process per run (default: 10, use 0 for unlimited)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all low-scored traces (same as --limit 0)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be corrected without actually doing it'
    )
    
    args = parser.parse_args()
    
    # Handle --all flag or limit=0 (process all traces)
    if args.all or args.limit == 0:
        limit = 999999  # Process all (very high limit)
        print(f"\n[*] Processing ALL low-scored traces (no limit)")
    else:
        limit = args.limit
    
    # Create processor
    try:
        processor = AutoCorrectionProcessor(
            min_score=args.min_score,
            dry_run=args.dry_run
        )
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print(f"\nPlease check your .env file for:")
        print(f"  - LANGFUSE_PUBLIC_KEY")
        print(f"  - LANGFUSE_SECRET_KEY")
        print(f"  - LANGFUSE_HOST")
        sys.exit(1)
    
    # Run in appropriate mode
    if args.poll:
        await processor.run_polling(interval=args.interval, limit=limit)
    else:
        await processor.run_once(limit=limit)


if __name__ == "__main__":
    asyncio.run(main())

