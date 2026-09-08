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
