-- Nifty100 Sprint 1 — Exploratory Queries
-- Day 07

-- 1. Total companies
SELECT COUNT(*) AS total_companies
FROM companies;

-- 2. Company list
SELECT id, company_name
FROM companies
ORDER BY company_name;

-- 3. P&L coverage by company
SELECT company_id, COUNT(DISTINCT year) AS years
FROM profitandloss
GROUP BY company_id
ORDER BY years DESC;

-- 4. Companies with fewer than 5 years
SELECT company_id, COUNT(DISTINCT year) AS years
FROM profitandloss
GROUP BY company_id
HAVING COUNT(DISTINCT year) < 5
ORDER BY years;

-- 5. P&L overall coverage
SELECT MIN(year) AS first_year,
       MAX(year) AS last_year,
       COUNT(DISTINCT year) AS years
FROM profitandloss;

-- 6. Balance Sheet overall coverage
SELECT MIN(year) AS first_year,
       MAX(year) AS last_year,
       COUNT(DISTINCT year) AS years
FROM balancesheet;

-- 7. Cash Flow overall coverage
SELECT MIN(year) AS first_year,
       MAX(year) AS last_year,
       COUNT(DISTINCT year) AS years
FROM cashflow;

-- 8. Top 10 net profits
SELECT company_id, year, net_profit
FROM profitandloss
WHERE year = (SELECT MAX(year) FROM profitandloss)
ORDER BY net_profit DESC
LIMIT 10;

-- 9. Stock-price coverage
SELECT COUNT(*) AS rows,
       COUNT(DISTINCT company_id) AS companies
FROM stock_prices;

-- 10. Foreign-key integrity
   PRAGMA foreign_key_check;
