import os
import time as _time
from datetime import datetime, timedelta, date, time, timezone
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config
import pandas as pd
import s3fs
import pyarrow.parquet as pq

# ============================================================
# ✅ OPEN-SOURCE PARQUET FOOTER DIAGNOSTIC UTILITY
# ============================================================

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN", None)
AWS_REGION = "us-east-1"
 
BUCKET_NAME = "oss-data-pipeline-validation-demo"
 
PARQUET_DATE_COL = "source__modified"
START_DATE_STR = "2026-03-30"
END_DATE_STR   = "2026-04-03"
 
def parse_yyyy_mm_dd(s: str) -> date:
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"Invalid date '{s}'. Use format YYYY-MM-DD.")
 
START_DATE: date = parse_yyyy_mm_dd(START_DATE_STR)
END_DATE: date = parse_yyyy_mm_dd(END_DATE_STR)
if END_DATE < START_DATE:
    raise ValueError(f"END_DATE_STR ({END_DATE_STR}) must be >= START_DATE_STR ({START_DATE_STR}).")
 
START_UTC = datetime.combine(START_DATE, time.min, tzinfo=timezone.utc)
END_UTC_EXCL = datetime.combine(END_DATE + timedelta(days=1), time.min, tzinfo=timezone.utc)
TODAY_UTC_DATE = datetime.now(timezone.utc).date()
DYNAMIC_LOOKBACK_DAYS = max(7, (TODAY_UTC_DATE - START_DATE).days + 3)
 
MAX_WORKERS = min(32, (os.cpu_count() or 8) * 4)
PROGRESS_EVERY = 50
SIZE_OUTLIER_MULTIPLIER = 5.0
 
# Generic Job Config mapping out distributed object partitions
JOBS = [
    {
        "name": "transaction_records",
        "prefix": "parquet/v2/dataset=transactions/object=RecordStore/",
        "report_csv": "slow_file_candidates_transactions.csv",
    },
    {
        "name": "production_logs",
        "prefix": "parquet/v2/dataset=system_logs/object=EventStore/",
        "report_csv": "slow_file_candidates_logs.csv",
    },
]

def build_s3_client():
    cfg = Config(
        max_pool_connections=64,
        retries={"max_attempts": 5, "mode": "standard"},
        connect_timeout=10,
        read_timeout=60,
    )
    return boto3.client(
        service_name="s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
        config=cfg
    )

def build_s3fs():
    fs_kwargs = dict(
        key=AWS_ACCESS_KEY,
        secret=AWS_SECRET_KEY,
        token=AWS_SESSION_TOKEN,
        client_kwargs={"region_name": AWS_REGION},
        config_kwargs={
            "max_pool_connections": 64,
            "retries": {"max_attempts": 5, "mode": "standard"},
            "connect_timeout": 10,
            "read_timeout": 60,
        },
        default_fill_cache=False,
    )
    return s3fs.S3FileSystem(**fs_kwargs)

print("[SUCCESS] Open-source parquet metadata structures initialized safely.")
