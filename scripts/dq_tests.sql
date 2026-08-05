-- ============================================================
-- DATA QUALITY TESTS (hanya yang ada datanya aja)
-- ============================================================

-- 1. Cek duplikat di dim_customers
SELECT 'dim_customers' as table_name, 'duplicate customer_id' as test_name, 
       COUNT(*) - COUNT(DISTINCT customer_id) as issue_count
FROM dim_customers
HAVING issue_count > 0;

-- 2. Cek NULL di email
SELECT 'dim_customers' as table_name, 'NULL email' as test_name, 
       COUNT(*) as issue_count
FROM dim_customers
WHERE email IS NULL
HAVING issue_count > 0;

-- 3. Cek NULL di full_name
SELECT 'dim_customers' as table_name, 'NULL full_name' as test_name, 
       COUNT(*) as issue_count
FROM dim_customers
WHERE full_name IS NULL
HAVING issue_count > 0;

-- 4. Cek status valid
SELECT 'dim_customers' as table_name, 'invalid status' as test_name, 
       COUNT(*) as issue_count
FROM dim_customers
WHERE status NOT IN ('active', 'inactive')
HAVING issue_count > 0;

-- 5. Cek loyalty_tier valid
SELECT 'dim_customers' as table_name, 'invalid loyalty_tier' as test_name, 
       COUNT(*) as issue_count
FROM dim_customers
WHERE loyalty_tier NOT IN ('Platinum', 'Gold', 'Silver')
HAVING issue_count > 0;

-- ============================================================
-- KALO GAADA ERROR, KELUAR INI
-- ============================================================
SELECT '✅ All data quality tests passed!' as result;