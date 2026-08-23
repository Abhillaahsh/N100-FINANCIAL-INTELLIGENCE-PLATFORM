# N100 Financial Intelligence Platform

A data-driven financial intelligence platform for analyzing **Nifty 100 companies** using financial statements, stock prices, financial ratios, company information, and data-quality validation.

## 📌 Project Overview

The **N100 Financial Intelligence Platform** is an end-to-end data engineering and analytics project built around financial data from Nifty 100 companies.

The project focuses on:

- Excel data ingestion
- Data normalization and cleaning
- SQLite database design
- ETL pipeline development
- Financial data quality validation
- Financial statement analysis
- Stock-price analysis
- Financial ratio analysis
- Exploratory SQL analysis
- Automated testing

The project is being developed incrementally using a **7-day Sprint 1 Data Foundation plan**.

---

# 🎯 Sprint 1 – Data Foundation

## Sprint Goal

Build a reliable financial-data foundation containing:

- Source Excel files
- Normalization utilities
- ETL loader
- SQLite database
- Data-quality validation
- Automated unit tests
- Exploratory SQL queries

### Sprint

**Sprint 1 · Day 01–07 · 34 Story Points**

---

# 🏗️ Project Architecture

```text
N100-FINANCIAL-INTELLIGENCE-PLATFORM/
│
├── data/
│   └── raw/
│       ├── companies.xlsx
│       ├── profitandloss.xlsx
│       ├── balancesheet.xlsx
│       ├── cashflow.xlsx
│       ├── analysis.xlsx
│       ├── documents.xlsx
│       ├── prosandcons.xlsx
│       ├── sectors.xlsx
│       ├── financial_ratios.xlsx
│       ├── peer_groups.xlsx
│       ├── market_cap.xlsx
│       └── stock_prices.xlsx
│
├── db/
│   ├── schema.sql
│   └── nifty100.db
│
├── notebooks/
│   └── exploratory_queries.sql
│
├── reports/
│   ├── load_audit.csv
│   └── validation_failures.csv
│
├── src/
│   └── etl/
│       ├── loader.py
│       ├── validator.py
│       └── normalise.py
│
├── tests/
│   └── etl/
│       └── test_normalise.py
│
├── .env
├── Makefile
├── requirements.txt
└── README.md
