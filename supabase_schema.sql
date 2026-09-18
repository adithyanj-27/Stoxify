-- =======================================================
-- STOXIFY: SUPABASE POSTGRESQL SCHEMA
-- Paste this entire script into Supabase SQL Editor and click RUN
-- =======================================================

CREATE TABLE IF NOT EXISTS public.users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT,
    phone TEXT,
    pan TEXT,
    dob DATE,
    bank_name TEXT DEFAULT 'HDFC Bank',
    bank_account TEXT DEFAULT '50100234567890',
    pin TEXT DEFAULT '',
    balance NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00,
    total_deposited NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00,
    avatar_color TEXT DEFAULT '#0EA5E9',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure newer columns exist if table was already created earlier:
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS dob DATE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS username TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS password TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS users_username_idx ON public.users (LOWER(username));

INSERT INTO public.users (id, name, username, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited)
VALUES (
    'default', 
    'Default Trader', 
    'default_trader',
    'trader@stoxify.com', 
    '9876543210', 
    'ABCDE1234F', 
    'HDFC Bank', 
    '50100234567890', 
    '', 
    1000000.00, 
    1000000.00
) ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.holdings (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    quantity NUMERIC(15, 4) NOT NULL,
    avg_price NUMERIC(15, 2) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_holding UNIQUE (user_id, symbol)
);

CREATE TABLE IF NOT EXISTS public.positions (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    quantity NUMERIC(15, 4) NOT NULL,
    avg_price NUMERIC(15, 2) NOT NULL,
    margin_used NUMERIC(15, 2) NOT NULL,
    product_type TEXT NOT NULL DEFAULT 'INTRADAY',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_position UNIQUE (user_id, symbol)
);

CREATE TABLE IF NOT EXISTS public.orders (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    order_type TEXT NOT NULL,
    product_type TEXT NOT NULL,
    quantity NUMERIC(15, 4) NOT NULL,
    price NUMERIC(15, 2) NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    status TEXT NOT NULL,
    order_variety TEXT NOT NULL DEFAULT 'MARKET',
    trigger_price NUMERIC(15, 2) DEFAULT 0.0,
    realized_pnl NUMERIC(15, 2) DEFAULT 0.0,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_watchlist UNIQUE (user_id, symbol)
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;

-- No permissive policies.
--
-- RLS is enabled above but these tables previously carried
--   FOR ALL USING (true) WITH CHECK (true)
-- which permits every operation on every row for any holder of the project's
-- publishable key — including reading and rewriting users.pin / users.password.
--
-- Nothing legitimately needs that access over the REST API: the browser never
-- talks to Supabase directly (no key is shipped in static/ or public/), and the
-- backend authenticates with the secret/service-role key, which bypasses RLS
-- entirely. So the correct configuration is *no* policy for anon/authenticated,
-- which makes the publishable key useless instead of omnipotent.
--
-- If a future feature needs browser-side Supabase access, add an explicit
-- per-user policy for that one table rather than reopening these:
--   CREATE POLICY "<table>_own_rows" ON public.<table>
--     FOR ALL TO authenticated
--     USING (EXISTS (SELECT 1 FROM public.users u
--                    WHERE u.id = <table>.user_id AND u.auth_id = auth.uid()::text))
--     WITH CHECK (EXISTS (SELECT 1 FROM public.users u
--                    WHERE u.id = <table>.user_id AND u.auth_id = auth.uid()::text));

-- Drop the permissive policies in case this file is re-applied to a project
-- that already has them.
DROP POLICY IF EXISTS "Allow public full access to users" ON public.users;
DROP POLICY IF EXISTS "Allow public full access to holdings" ON public.holdings;
DROP POLICY IF EXISTS "Allow public full access to positions" ON public.positions;
DROP POLICY IF EXISTS "Allow public full access to orders" ON public.orders;
DROP POLICY IF EXISTS "Allow public full access to watchlist" ON public.watchlist;
