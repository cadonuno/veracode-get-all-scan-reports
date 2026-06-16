# Veracode Get All Scan Reports

This repository contains `get-all-reports.py`, a utility script for downloading all available Veracode scan reports.

## Prerequisites

- Python 3.12 or later
- Valid Veracode API credentials

## Installation

1. Clone or copy this repository.
2. Ensure Python is installed.
3. Install any required dependencies.

```bash
pip install -r requirements.txt
```

## Usage

Run the script from the repository directory.

```bash
python get-all-reports.py --output ./folder-to-save --format format-to-save
```

### Options

- `--output` : Directory to write downloaded scan reports.
- `--format` : report format to fetch (XML or PDF).

## Output

Downloaded reports are saved under the specified output directory and organized in folders based on application name and policy/sandbox.
