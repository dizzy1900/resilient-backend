"""
Batch Processing Engine for Portfolio Assets
Processes multiple climate risk assessments and updates Supabase database
"""

import logging
import os
import sys
from typing import Dict, Any, List

import pandas as pd
from supabase import create_client, Client
import requests

from physics_engine import simulate_maize_yield
from celery_app import celery_app

logger = logging.getLogger(__name__)

# Number of assets to update per Supabase round-trip to avoid timeouts.
SUPABASE_BATCH_SIZE = int(os.environ.get("SUPABASE_BATCH_SIZE", "50"))


@celery_app.task(bind=True, max_retries=3)
def run_batch_job(self, job_id: str) -> Dict[str, Any]:
    """
    Execute batch processing for all assets in a portfolio job.
    
    Args:
        job_id: The unique identifier for the batch job
        
    Returns:
        Dict with status and processing results
    """
    print(f"[BATCH] Starting job {job_id}", file=sys.stderr, flush=True)
    
    try:
        # Initialize Supabase client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"[BATCH] Connected to Supabase", file=sys.stderr, flush=True)
        
        # Fetch all assets for this job
        response = supabase.table('portfolio_assets').select('*').eq('job_id', job_id).execute()
        assets = response.data
        
        if not assets:
            print(f"[BATCH] No assets found for job {job_id}", file=sys.stderr, flush=True)
            return {
                'status': 'error',
                'message': f'No assets found for job_id {job_id}'
            }
        
        total_assets = len(assets)
        print(f"[BATCH] Processing {total_assets} assets", file=sys.stderr, flush=True)
        if total_assets > SUPABASE_BATCH_SIZE:
            logger.warning(
                "Job %s has %d assets; updates will be flushed in batches of %d",
                job_id, total_assets, SUPABASE_BATCH_SIZE,
            )
        
        # Stress test scenario: 35°C temperature, 400mm rainfall
        STRESS_TEMP = 35.0
        STRESS_RAIN = 400.0
        
        processed_count = 0
        errors = []
        pending_updates: List[Dict[str, Any]] = []
        
        def flush_updates(batch: List[Dict[str, Any]]) -> None:
            """Send a batch of updates to Supabase."""
            for item in batch:
                supabase.table('portfolio_assets').update(item['data']).eq('id', item['id']).execute()
        
        # Process each asset
        for asset in assets:
            try:
                asset_id = asset['id']
                
                # Run predictions for both seed types
                standard_yield = simulate_maize_yield(
                    temp=STRESS_TEMP,
                    rain=STRESS_RAIN,
                    seed_type=0  # Standard seed
                )
                
                resilient_yield = simulate_maize_yield(
                    temp=STRESS_TEMP,
                    rain=STRESS_RAIN,
                    seed_type=1  # Resilient seed
                )
                
                # Calculate avoided loss
                avoided_loss = resilient_yield - standard_yield
                percentage_improvement = (avoided_loss / standard_yield * 100) if standard_yield > 0 else 0.0
                
                pending_updates.append({
                    'id': asset_id,
                    'data': {
                        'standard_yield': round(standard_yield, 2),
                        'resilient_yield': round(resilient_yield, 2),
                        'avoided_loss': round(avoided_loss, 2),
                        'percentage_improvement': round(percentage_improvement, 2),
                        'stress_temp': STRESS_TEMP,
                        'stress_rain': STRESS_RAIN,
                        'processed': True,
                    },
                })
                processed_count += 1
                
                # Flush when batch is full
                if len(pending_updates) >= SUPABASE_BATCH_SIZE:
                    print(f"[BATCH] Flushing {len(pending_updates)} updates ({processed_count}/{total_assets})...",
                          file=sys.stderr, flush=True)
                    flush_updates(pending_updates)
                    pending_updates.clear()
                
            except Exception as asset_error:
                error_msg = f"Asset {asset.get('id', 'unknown')}: {str(asset_error)}"
                errors.append(error_msg)
                print(f"[BATCH ERROR] {error_msg}", file=sys.stderr, flush=True)
        
        # Flush remaining updates
        if pending_updates:
            print(f"[BATCH] Flushing final {len(pending_updates)} updates...",
                  file=sys.stderr, flush=True)
            flush_updates(pending_updates)
            pending_updates.clear()
        
        # Update batch_jobs table to mark as completed
        job_update = {
            'status': 'completed',
            'processed_count': processed_count,
            'error_count': len(errors),
            'completed_at': 'now()'
        }
        
        supabase.table('batch_jobs').update(job_update).eq('job_id', job_id).execute()
        print(f"[BATCH] Job {job_id} marked as completed", file=sys.stderr, flush=True)
        
        # Trigger N8N reporting webhook
        n8n_webhook = os.environ.get('N8N_REPORT_WEBHOOK')
        if n8n_webhook:
            try:
                # Fetch email recipient from batch_jobs table
                job_response = supabase.table('batch_jobs').select('email_recipient').eq('job_id', job_id).single().execute()
                email_recipient = job_response.data.get('email_recipient') if job_response.data else None
                
                webhook_payload = {
                    'job_id': job_id,
                    'email_recipient': email_recipient,
                    'processed_count': processed_count,
                    'error_count': len(errors)
                }
                
                webhook_response = requests.post(n8n_webhook, json=webhook_payload, timeout=10)
                webhook_response.raise_for_status()
                print(f"[BATCH] Webhook triggered successfully", file=sys.stderr, flush=True)
                
            except Exception as webhook_error:
                print(f"[BATCH WARNING] Webhook failed: {webhook_error}", file=sys.stderr, flush=True)
        else:
            print(f"[BATCH WARNING] N8N_REPORT_WEBHOOK not configured", file=sys.stderr, flush=True)
        
        result = {
            'status': 'success',
            'job_id': job_id,
            'processed_count': processed_count,
            'error_count': len(errors),
            'errors': errors if errors else None
        }
        
        print(f"[BATCH] Job {job_id} completed: {processed_count} assets processed, {len(errors)} errors",
              file=sys.stderr, flush=True)
        
        return result
        
    except Exception as e:
        error_msg = f"Batch job {job_id} failed: {str(e)}"
        print(f"[BATCH FATAL ERROR] {error_msg}", file=sys.stderr, flush=True)
        
        # Try to update job status to failed
        try:
            if 'supabase' in locals():
                supabase.table('batch_jobs').update({
                    'status': 'failed',
                    'error_message': str(e)
                }).eq('job_id', job_id).execute()
        except:
            pass
        
        return {
            'status': 'error',
            'job_id': job_id,
            'message': error_msg
        }
