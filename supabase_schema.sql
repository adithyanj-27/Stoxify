-- =======================================================
-- STOXIFY: SUPABASE POSTGRESQL SCHEMA
-- Paste this entire script into Supabase SQL Editor and click RUN
-- =======================================================

CREATE TABLE IF NOT EXISTS public.users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    pan TEXT,
    bank_name TEXT DEFAULT 'HDFC Bank',
    bank_account TEXT DEFAULT '50100234567890',
    pin TEXT DEFAULT '1234',
    balance NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00,
    total_deposited NUMERIC(15, 2) NOT NULL DEFAULT 1000000.00,
    avatar_color TEXT DEFAULT '#0EA5E9',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.users (id, name, email, phone, pan, bank_name, bank_account, pin, balance, total_deposited)
VALUES (
    'default', 
    'Default Trader', 
    'trader@stoxify.com', 
    '9876543210', 
    'ABCDE1234F', 
    'HDFC Bank', 
    '50100234567890', 
    '1234', 
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

CREATE POLICY "Allow public full access to users" ON public.users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to holdings" ON public.holdings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to positions" ON public.positions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to orders" ON public.orders FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public full access to watchlist" ON public.watchlist FOR ALL USING (true) WITH CHECK (true);
