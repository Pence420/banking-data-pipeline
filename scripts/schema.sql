-- Tabel customers: data nasabah
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    address TEXT,
    loyalty_tier VARCHAR(20) DEFAULT 'Silver', -- Platinum/Gold/Silver, dipakai buat KPI dashboard nanti
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabel accounts: akun bank tiap nasabah
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- savings/checking, dll
    balance NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- buat tren buka/tutup akun di dashboard
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabel transactions: transaksi tiap akun
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id),
    transaction_type VARCHAR(20) NOT NULL, -- deposit/withdrawal/transfer
    amount NUMERIC(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'success', -- buat hitung success rate di dashboard
    transaction_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS di ketiga tabel
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Policy permisif: izinkan semua operasi (SELECT/INSERT/UPDATE/DELETE)
-- Catatan: ini OK untuk proyek simulasi lokal, TAPI jangan dipakai kalau
-- proyek ini nanti punya user publik asli
CREATE POLICY "allow_all_customers" ON customers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_accounts" ON accounts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_transactions" ON transactions FOR ALL USING (true) WITH CHECK (true);

ALTER PUBLICATION supabase_realtime ADD TABLE customers;
ALTER PUBLICATION supabase_realtime ADD TABLE accounts;
ALTER PUBLICATION supabase_realtime ADD TABLE transactions;