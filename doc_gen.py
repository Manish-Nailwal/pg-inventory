import json
import os
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()

# ---------------------------
# Config & Models
# ---------------------------

class ServerConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str

class TableMetadata(BaseModel):
    server: str
    database: str
    schema: str
    table: str
    postgres_version: str
    extensions: List[str]
    rowcount: int
    primary_keys: List[str]
    columns: List[Dict[str, Any]]
    indexes: List[str]
    foreign_keys: List[str]


# ---------------------------
# Helpers
# ---------------------------

def connect_and_fetch(server: ServerConfig) -> List[TableMetadata]:
    """Connects to one server and extracts metadata from all databases."""
    metadata = []
    try:
        conn = psycopg2.connect(
            host=server.host,
            port=server.port,
            user=server.username,
            password=server.password,
            dbname="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = [row[0] for row in cur.fetchall()]

        for db in databases:
            db_conn = psycopg2.connect(
                host=server.host,
                port=server.port,
                user=server.username,
                password=server.password,
                dbname=db,
                cursor_factory=RealDictCursor
            )
            db_cur = db_conn.cursor()

            # Get version
            db_cur.execute("SELECT version();")
            version = db_cur.fetchone()["version"]

            # Get extensions
            db_cur.execute("SELECT extname FROM pg_extension;")
            extensions = [r["extname"] for r in db_cur.fetchall()]

            # Get schemas & tables
            db_cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
            """)
            tables = db_cur.fetchall()

            for t in tables:
                schema, table = t["table_schema"], t["table_name"]

                # Row count (estimate)
                db_cur.execute(
                    f"SELECT reltuples::BIGINT AS estimate FROM pg_class WHERE relname = %s;",
                    (table,)
                )
                rowcount = db_cur.fetchone()["estimate"]

                # Columns
                db_cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s;
                """, (schema, table))
                columns = db_cur.fetchall()

                # Primary keys
                db_cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = %s AND tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY';
                """, (schema, table))
                primary_keys = [r["column_name"] for r in db_cur.fetchall()]

                # Indexes
                db_cur.execute(
                    "SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = %s;",
                    (schema, table)
                )
                indexes = [r["indexdef"] for r in db_cur.fetchall()]

                # Foreign keys
                db_cur.execute("""
                    SELECT conname, pg_get_constraintdef(c.oid) as definition
                    FROM pg_constraint c
                    JOIN pg_namespace n ON n.oid = c.connamespace
                    WHERE contype = 'f' AND conrelid = %s::regclass;
                """, (f"{schema}.{table}",))
                foreign_keys = [f"{r['conname']}: {r['definition']}" for r in db_cur.fetchall()]

                metadata.append(TableMetadata(
                    server=f"{server.host}:{server.port}",
                    database=db,
                    schema=schema,
                    table=table,
                    postgres_version=version,
                    extensions=extensions,
                    rowcount=rowcount,
                    primary_keys=primary_keys,
                    columns=columns,
                    indexes=indexes,
                    foreign_keys=foreign_keys,
                ))

            db_conn.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error scanning server {server.host}:{server.port} → {e}")
    return metadata


def save_results(output_dir: Path, metadata: List[TableMetadata]) -> None:
    """Save metadata to Markdown and JSONL."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    # JSONL
    with open(out_path / "postgres_inventory.jsonl", "w", encoding="utf-8") as f:
        for item in metadata:
            f.write(item.model_dump_json() + "\n")

    # Markdown
    with open(out_path / "postgres_inventory.md", "w", encoding="utf-8") as f:
        for item in metadata:
            f.write(f"## {item.server} · {item.database} · {item.schema}.{item.table}\n\n")
            f.write(f"- PostgreSQL Version: {item.postgres_version}\n")
            f.write(f"- Extensions: {', '.join(item.extensions)}\n")
            f.write(f"- Rowcount: {item.rowcount}\n")
            if item.primary_keys:
                f.write(f"- Primary Key: {', '.join(item.primary_keys)}\n")
            f.write("\n### Columns\n\n")
            f.write("| Name | Type | Nullable | Default |\n")
            f.write("|------|------|----------|---------|\n")
            for col in item.columns:
                f.write(f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} | {col['column_default'] or ''} |\n")
            if item.indexes:
                f.write("\n### Indexes\n")
                for idx in item.indexes:
                    f.write(f"- {idx}\n")
            if item.foreign_keys:
                f.write("\n### Foreign Keys\n")
                for fk in item.foreign_keys:
                    f.write(f"- {fk}\n")
            f.write("\n---\n\n")

    console.print(f"[green]✅ Results saved in {out_path}[/green]")


def generate_doc(servers: List[Dict[str, Any]], output_dir: Path, parallel: bool = True) -> None:
    """Main entrypoint to run inventory."""
    server_configs = [ServerConfig(**s) for s in servers]
    all_metadata: List[TableMetadata] = []

    if parallel:
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(connect_and_fetch, s): s for s in server_configs}
            for future in as_completed(futures):
                all_metadata.extend(future.result())
    else:
        for s in server_configs:
            all_metadata.extend(connect_and_fetch(s))

    save_results(output_dir, all_metadata)


# ---------------------------
# CLI entrypoint (optional)
# ---------------------------

if __name__ == "__main__":
    servers = [
        {"host": "localhost", "port": 5432, "username": "postgres", "password": "postgres"}
    ]
    OUTPUT_DIR = Path("./output")
    generate_doc(servers, OUTPUT_DIR, parallel=True)
