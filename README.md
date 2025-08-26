# 📊 pg-inventory
A Python tool to automatically scan PostgreSQL servers, extract metadata (databases, schemas, tables, columns, indexes, keys, row counts, extensions, version info), and generate structured documentation in **Markdown** and **JSONL** format.

---

## 🚀 Features
- Connect to one or more PostgreSQL servers.  
- Collects detailed metadata for each table.  
- Outputs both **human-readable docs (Markdown)** and **machine-readable data (JSONL)**.  
- Parallel scanning for faster results.  
- Option for accurate row counts (or fast estimates).  

---

## 📦 Installation
Clone the repo and install dependencies:

```bash
git clone https://github.com/Manish-Nailwal/pg-inventory.git
cd pg-inventory
pip install -r requirements.txt
```

### Dependencies
```
psycopg2
pydantic
rich
```

---

## ⚡ Usage

### 1. Import and Configure
```python
from pathlib import Path
from pg_inventory import generate_doc

servers = [
    {
        "host": "server_host",
        "port": "server_port",
        "username": "your_username",
        "password": "your_password",
    },
]

OUTPUT_DIR = Path("./out")
```

### 2. Run Inventory
```python
generate_doc(servers, OUTPUT_DIR)
```

### 3. Output
- A **Markdown file** (`postgres_inventory.md`) → Human-readable docs  
- A **JSONL file** (`postgres_inventory.jsonl`) → Machine-readable  
- Both are stored in a timestamped folder under your `OUTPUT_DIR`.

---

## 📂 Example Output (Markdown)

👉 Preview available in the `/example` folder


## 📜 License
MIT License.  
Feel free to use and contribute!  

---

## 🤝 Contributing
PRs are welcome!  
If you find a bug or have an idea, please open an issue.
