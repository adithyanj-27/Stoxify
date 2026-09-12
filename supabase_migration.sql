-- Run once in the Supabase SQL Editor. Safe to run repeatedly.
-- Aligns the cloud order ledger with fields already used by the application.

ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS limit_price NUMERIC(15, 2) DEFAULT 0.0;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS order_tag TEXT NOT NULL DEFAULT 'NORMAL';

CREATE INDEX IF NOT EXISTS orders_user_status_symbol_idx
  ON public.orders (user_id, status, symbol);
CREATE INDEX IF NOT EXISTS holdings_user_symbol_idx
  ON public.holdings (user_id, symbol);
CREATE INDEX IF NOT EXISTS positions_user_symbol_idx
  ON public.positions (user_id, symbol);

-- ---------------------------------------------------------------------------
-- The application also writes the columns/tables below. They were missing from
-- supabase_schema.sql, so every sync touching them failed with 404/400 and the
-- error was swallowed by the surrounding try/except. Re-running this file is safe.
-- ---------------------------------------------------------------------------

-- users: columns written by create_user()/update_user()/mark_tour_completed()
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS auth_id TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS age INTEGER DEFAULT 18;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS experience TEXT DEFAULT 'None / Total Beginner';
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS has_completed_tour BOOLEAN DEFAULT FALSE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bank_balance NUMERIC(15, 2) DEFAULT 1000000.00;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bank_ifsc TEXT DEFAULT 'HDFC0001234';
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bank_upi_id TEXT DEFAULT '';

-- orders: contract-note fields written by execute_trade()
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS charges NUMERIC(15, 2) DEFAULT 0.0;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS net_amount NUMERIC(15, 2) DEFAULT 0.0;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS blocked_amount NUMERIC(15, 2) DEFAULT 0.0;

CREATE TABLE IF NOT EXISTS public.gtt_orders (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    product_type TEXT NOT NULL DEFAULT 'DELIVERY',
    action TEXT NOT NULL DEFAULT 'BUY',
    quantity NUMERIC(15, 4) NOT NULL,
    trigger_price NUMERIC(15, 2) NOT NULL,
    target_price NUMERIC(15, 2) DEFAULT 0.0,
    stop_loss_price NUMERIC(15, 2) DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.sips (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    fund_id TEXT NOT NULL,
    fund_name TEXT NOT NULL,
    monthly_amount NUMERIC(15, 2) NOT NULL,
    sip_day INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    next_installment_date TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.ipo_bids (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    ipo_id TEXT NOT NULL,
    ipo_name TEXT NOT NULL,
    lots INTEGER NOT NULL DEFAULT 1,
    shares INTEGER NOT NULL,
    bid_price NUMERIC(15, 2) NOT NULL,
    amount_blocked NUMERIC(15, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'APPLIED',
    upi_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.gtt_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ipo_bids ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public full access to gtt_orders" ON public.gtt_orders;
DROP POLICY IF EXISTS "Allow public full access to sips" ON public.sips;
DROP POLICY IF EXISTS "Allow public full access to ipo_bids" ON public.ipo_bids;

CREATE POLICY "Allow public full access to gtt_orders" ON public.gtt_orders FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to sips" ON public.sips FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to ipo_bids" ON public.ipo_bids FOR ALL USING (true) WITH CHECK (true);
