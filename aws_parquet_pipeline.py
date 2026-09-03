import os
import re
import sys
import threading
import time as _time
from datetime import datetime, timedelta, date, time, timezone
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config
import pandas as pd
import s3fs
import pyarrow as pa
import pyarrow.parquet as pq

# ============================================================
# ✅ GENERIC OPEN-SOURCE DATA PIPELINE OPTIMIZER
# ============================================================

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN", None)
AWS_REGION = "us-east-1"

START_DATE_STR = "2026-01-01"
END_DATE_STR   = "2026-01-07"
BUCKET_NAME = "open-source-analytics-bucket-demo"
PARQUET_DATE_COL = "source__modified"
CSV_NULL_TEXT = "NULL"

MAX_WORKERS = min(32, (os.cpu_count() or 8) * 4)
PROGRESS_EVERY = 25
QUICK_BENCHMARK_MODE = False
BENCHMARK_SAMPLE_SIZE = 30

S3_CONNECT_TIMEOUT = 10
S3_READ_TIMEOUT = 60
S3_MAX_ATTEMPTS = 5 

# Generic schema mapping for public repository demo
SALES_FIXED_COLS: List[str] = [
    "Id", "source__modified", "Origin", "ClosedDate", "CreatedDate",
    "Brand_Identifier", "Owner_Id", "SourceCategory", "TransactionNumber",
    "IsDeleted", "Inquiry_Type", "Product_Group", "QueryType"
]

LOGS_FIXED_COLS: List[str] = [
    "Id", "source__modified", "EventType", "SessionKey", "Agent_Name",
    "WaitTime", "CreatedDate", "QueueName", "IsDeleted", "WorkTime"
]

TRACKER_JOBS = [
    {
        "name": "sales_pipeline",
        "prefix": "parquet/v1/analytics/object=SalesData/",
        "csv_base": "processed_sales_data",
        "final_output_csv": "Sales_Cleaned.csv",
        "fixed_cols": SALES_FIXED_COLS,
    },
    {
        "name": "system_logs",
        "prefix": "parquet/v1/analytics/object=SystemLogs/",
        "csv_base": "processed_logs_data",
        "final_output_csv": "Logs_Cleaned.csv",
        "fixed_cols": LOGS_FIXED_COLS,
    },
]

def parse_yyyy_mm_dd(s: str) -> date:
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"Invalid date format '{s}'. Use YYYY-MM-DD.")

def build_s3_client():
    cfg = Config(
        max_pool_connections=64,
        retries={"max_attempts": S3_MAX_ATTEMPTS, "mode": "standard"},
        connect_timeout=S3_CONNECT_TIMEOUT,
        read_timeout=S3_READ_TIMEOUT,
    )
    return boto3.client(
        service_name="s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
        config=cfg
    )

print("Data pipeline components dynamically structured for open-source utility usage.")
