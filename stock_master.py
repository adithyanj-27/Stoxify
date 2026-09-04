# Comprehensive Master Database of Indian Stocks & Mutual Funds
# Includes pre-seeded baseline quotes for instant zero-lag loading (<10ms)

STOCK_MASTER = [
    # --- Top NIFTY 50 & Large Caps ---
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy", "price": 1328.0, "change": 25.5, "change_pct": 1.96, "aliases": ["ril", "reliance", "mukesh ambani", "jio"]},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "IT", "price": 2308.7, "change": -11.4, "change_pct": -0.49, "aliases": ["tcs", "tata consultancy"]},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Banking", "price": 715.55, "change": 8.9, "change_pct": 1.26, "aliases": ["hdfc", "hdfc bank"]},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "IT", "price": 1129.0, "change": -6.2, "change_pct": -0.55, "aliases": ["infy", "infosys"]},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Banking", "price": 1245.8, "change": 14.3, "change_pct": 1.16, "aliases": ["icici", "icici bank"]},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking", "price": 1018.7, "change": 12.8, "change_pct": 1.27, "aliases": ["sbi", "sbin", "state bank"]},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "sector": "Telecom", "price": 1845.0, "change": 22.4, "change_pct": 1.23, "aliases": ["airtel", "bharti airtel"]},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "sector": "Consumer", "price": 472.3, "change": 3.1, "change_pct": 0.66, "aliases": ["itc", "itc hotels"]},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Infra", "price": 3560.0, "change": 38.5, "change_pct": 1.09, "aliases": ["l&t", "lt", "larsen"]},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "sector": "Finance", "price": 6820.0, "change": 85.0, "change_pct": 1.26, "aliases": ["bajaj finance", "bajfinance"]},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "sector": "Consumer", "price": 2385.0, "change": -8.5, "change_pct": -0.35, "aliases": ["hul", "unilever", "hindustan unilever"]},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "sector": "Auto", "price": 12480.0, "change": 140.0, "change_pct": 1.13, "aliases": ["maruti", "suzuki", "maruti suzuki"]},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Ind. Ltd", "sector": "Pharma", "price": 1785.0, "change": 18.2, "change_pct": 1.03, "aliases": ["sun pharma", "sun"]},
    {"symbol": "TITAN.NS", "name": "Titan Company Ltd", "sector": "Consumer", "price": 3340.0, "change": 28.0, "change_pct": 0.85, "aliases": ["titan", "tanishq", "fastrack"]},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals", "price": 142.6, "change": 2.1, "change_pct": 1.49, "aliases": ["tata steel", "tisco"]},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "sector": "Energy", "price": 2480.0, "change": 34.0, "change_pct": 1.39, "aliases": ["adani", "adani ent", "gautam adani"]},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports & SEZ Ltd", "sector": "Infra", "price": 1195.0, "change": 15.6, "change_pct": 1.32, "aliases": ["adani ports", "apsez"]},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "sector": "IT", "price": 492.0, "change": -2.4, "change_pct": -0.49, "aliases": ["wipro"]},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp of India", "sector": "Energy", "price": 298.5, "change": 4.2, "change_pct": 1.43, "aliases": ["powergrid", "power grid"]},
    {"symbol": "NTPC.NS", "name": "NTPC Ltd", "sector": "Energy", "price": 365.2, "change": 5.8, "change_pct": 1.61, "aliases": ["ntpc", "national thermal power"]},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp Ltd", "sector": "Energy", "price": 252.0, "change": 3.4, "change_pct": 1.37, "aliases": ["ongc"]},
    {"symbol": "COALINDIA.NS", "name": "Coal India Ltd", "sector": "Metals", "price": 412.0, "change": 6.2, "change_pct": 1.53, "aliases": ["coal india", "cil"]},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Auto", "price": 2840.0, "change": 45.0, "change_pct": 1.61, "aliases": ["m&m", "mahindra", "thar", "scorpio"]},
    {"symbol": "TMCV.NS", "name": "Tata Motors Ltd (Commercial)", "sector": "Auto", "price": 725.0, "change": 11.2, "change_pct": 1.57, "aliases": ["tata motors", "tatamotors", "tmcv", "tata commercial"]},
    {"symbol": "TMPV.NS", "name": "Tata Motors Passenger Vehicles Ltd", "sector": "Auto", "price": 385.0, "change": 7.8, "change_pct": 2.07, "aliases": ["tata motors", "tatamotors", "tmpv", "tata ev", "tata cars"]},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Banking", "price": 1085.0, "change": 16.5, "change_pct": 1.54, "aliases": ["axis", "axis bank"]},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "price": 1780.0, "change": 14.0, "change_pct": 0.79, "aliases": ["kotak", "kotak bank"]},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement Ltd", "sector": "Infra", "price": 11450.0, "change": 120.0, "change_pct": 1.06, "aliases": ["ultratech", "cement"]},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd", "sector": "Consumer", "price": 2290.0, "change": -12.0, "change_pct": -0.52, "aliases": ["asian paints", "paints"]},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto Ltd", "sector": "Auto", "price": 8940.0, "change": 110.0, "change_pct": 1.25, "aliases": ["bajaj auto", "pulsar"]},
    {"symbol": "TRENT.NS", "name": "Trent Ltd (Westside & Zudio)", "sector": "Consumer", "price": 2853.9, "change": 68.4, "change_pct": 2.45, "aliases": ["trent", "zudio", "westside"]},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "sector": "Finance", "price": 298.0, "change": 5.4, "change_pct": 1.85, "aliases": ["jio financial", "jiofin", "jfs"]},
    {"symbol": "ETERNAL.NS", "name": "Zomato Ltd (Eternal Ltd)", "sector": "Consumer", "price": 246.5, "change": 8.2, "change_pct": 3.44, "aliases": ["zomato", "blinkit", "eternal"]},

    # --- Defense & Aerospace & Shipbuilding ---
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "sector": "Defense", "price": 4900.9, "change": 125.0, "change_pct": 2.62, "aliases": ["hal", "tejas", "defense"]},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "sector": "Defense", "price": 296.5, "change": 6.8, "change_pct": 2.35, "aliases": ["bel", "defense"]},
    {"symbol": "MAZDOCK.NS", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defense", "price": 2498.0, "change": 82.0, "change_pct": 3.39, "aliases": ["mazagon", "mazdock", "shipbuilders"]},
    {"symbol": "COCHINSHIP.NS", "name": "Cochin Shipyard Ltd", "sector": "Defense", "price": 1420.0, "change": 45.0, "change_pct": 3.27, "aliases": ["cochin shipyard", "cochinship"]},
    {"symbol": "GRSE.NS", "name": "Garden Reach Shipbuilders Ltd", "sector": "Defense", "price": 1680.0, "change": 52.0, "change_pct": 3.19, "aliases": ["grse", "garden reach"]},
    {"symbol": "BDL.NS", "name": "Bharat Dynamics Ltd", "sector": "Defense", "price": 1150.0, "change": 28.0, "change_pct": 2.50, "aliases": ["bdl", "missiles"]},

    # --- Railways & PSUs ---
    {"symbol": "IRFC.NS", "name": "Indian Railway Finance Corp", "sector": "Railways", "price": 154.2, "change": 3.8, "change_pct": 2.53, "aliases": ["irfc", "railway finance"]},
    {"symbol": "IRCTC.NS", "name": "Indian Railway Catering & Tourism Corp", "sector": "Railways", "price": 862.0, "change": 12.5, "change_pct": 1.47, "aliases": ["irctc", "railway booking"]},
    {"symbol": "RVNL.NS", "name": "Rail Vikas Nigam Ltd", "sector": "Railways", "price": 415.0, "change": 16.0, "change_pct": 4.01, "aliases": ["rvnl", "rail vikas"]},
    {"symbol": "RAILTEL.NS", "name": "RailTel Corp of India Ltd", "sector": "Railways", "price": 382.0, "change": 9.5, "change_pct": 2.55, "aliases": ["railtel", "railway wifi"]},
    {"symbol": "BHEL.NS", "name": "Bharat Heavy Electricals Ltd", "sector": "Energy", "price": 245.0, "change": 6.8, "change_pct": 2.85, "aliases": ["bhel", "turbines"]},

    # --- Power, Renewable & Clean Energy ---
    {"symbol": "TATAPOWER.NS", "name": "Tata Power Company Ltd", "sector": "Energy", "price": 368.2, "change": 9.4, "change_pct": 2.62, "aliases": ["tata power", "ev charging", "solar"]},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy Ltd", "sector": "Energy", "price": 45.27, "change": 1.45, "change_pct": 3.31, "aliases": ["suzlon", "wind energy", "green power"]},
    {"symbol": "IREDA.NS", "name": "Indian Renewable Energy Dev Agency", "sector": "Energy", "price": 212.5, "change": 7.6, "change_pct": 3.71, "aliases": ["ireda", "green finance"]},
    {"symbol": "ADANIGREEN.NS", "name": "Adani Green Energy Ltd", "sector": "Energy", "price": 1050.0, "change": 22.0, "change_pct": 2.14, "aliases": ["adani green", "solar"]},
    {"symbol": "ADANIPOWER.NS", "name": "Adani Power Ltd", "sector": "Energy", "price": 542.0, "change": 14.5, "change_pct": 2.75, "aliases": ["adani power"]},
    {"symbol": "NHPC.NS", "name": "NHPC Ltd", "sector": "Energy", "price": 88.5, "change": 1.8, "change_pct": 2.08, "aliases": ["nhpc", "hydro power"]},
    {"symbol": "RECLTD.NS", "name": "REC Ltd", "sector": "Finance", "price": 512.0, "change": 11.0, "change_pct": 2.19, "aliases": ["rec", "rural electrification"]},
    {"symbol": "PFC.NS", "name": "Power Finance Corp Ltd", "sector": "Finance", "price": 465.0, "change": 9.5, "change_pct": 2.08, "aliases": ["pfc", "power finance"]},

    # --- Banking & Financial Services ---
    {"symbol": "BANKBARODA.NS", "name": "Bank of Baroda", "sector": "Banking", "price": 242.0, "change": 4.5, "change_pct": 1.90, "aliases": ["bob", "bank of baroda"]},
    {"symbol": "PNB.NS", "name": "Punjab National Bank", "sector": "Banking", "price": 104.5, "change": 2.1, "change_pct": 2.05, "aliases": ["pnb", "punjab national bank"]},
    {"symbol": "CANBK.NS", "name": "Canara Bank", "sector": "Banking", "price": 98.2, "change": 1.8, "change_pct": 1.87, "aliases": ["canara bank", "canbk"]},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank Ltd", "sector": "Banking", "price": 68.4, "change": 1.2, "change_pct": 1.79, "aliases": ["idfc", "idfc first"]},
    {"symbol": "FEDERALBNK.NS", "name": "The Federal Bank Ltd", "sector": "Banking", "price": 194.0, "change": 3.0, "change_pct": 1.57, "aliases": ["federal bank"]},
    {"symbol": "YESBANK.NS", "name": "Yes Bank Ltd", "sector": "Banking", "price": 20.8, "change": 0.45, "change_pct": 2.21, "aliases": ["yes bank"]},
    {"symbol": "CDSL.NS", "name": "Central Depository Services Ltd", "sector": "Finance", "price": 1540.0, "change": 32.0, "change_pct": 2.12, "aliases": ["cdsl", "demat"]},
    {"symbol": "BSE.NS", "name": "BSE Ltd", "sector": "Finance", "price": 2680.0, "change": 65.0, "change_pct": 2.49, "aliases": ["bse", "bombay stock exchange"]},

    # --- Auto & EV ---
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors Ltd (Royal Enfield)", "sector": "Auto", "price": 4920.0, "change": 75.0, "change_pct": 1.55, "aliases": ["eicher", "royal enfield", "bullet"]},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company Ltd", "sector": "Auto", "price": 2420.0, "change": 38.0, "change_pct": 1.60, "aliases": ["tvs", "apache", "jupiter"]},
    {"symbol": "ASHOKLEY.NS", "name": "Ashok Leyland Ltd", "sector": "Auto", "price": 224.0, "change": 4.2, "change_pct": 1.91, "aliases": ["ashok leyland", "trucks"]},

    # --- Tech & Internet ---
    {"symbol": "TATATECH.NS", "name": "Tata Technologies Ltd", "sector": "IT", "price": 890.0, "change": 14.0, "change_pct": 1.60, "aliases": ["tata tech", "tata technologies"]},
    {"symbol": "TATAELXSI.NS", "name": "Tata Elxsi Ltd", "sector": "IT", "price": 6780.0, "change": 85.0, "change_pct": 1.27, "aliases": ["tata elxsi", "design"]},
    {"symbol": "PAYTM.NS", "name": "One97 Communications (Paytm)", "sector": "IT", "price": 785.0, "change": 24.0, "change_pct": 3.15, "aliases": ["paytm", "one97", "upi"]},

    # --- Metals & Commodities ---
    {"symbol": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals", "price": 445.0, "change": 9.5, "change_pct": 2.18, "aliases": ["vedanta", "anil agarwal"]},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel Ltd", "sector": "Metals", "price": 965.0, "change": 14.0, "change_pct": 1.47, "aliases": ["jsw steel", "jindal"]},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "sector": "Metals", "price": 625.0, "change": 8.5, "change_pct": 1.38, "aliases": ["hindalco", "aluminium"]},

    # --- Pharma ---
    {"symbol": "CIPLA.NS", "name": "Cipla Ltd", "sector": "Pharma", "price": 1485.0, "change": 16.0, "change_pct": 1.09, "aliases": ["cipla"]},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharma", "price": 1280.0, "change": 12.5, "change_pct": 0.99, "aliases": ["dr reddy", "drreddy"]},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise", "sector": "Pharma", "price": 6840.0, "change": 90.0, "change_pct": 1.33, "aliases": ["apollo hospitals", "apollo pharmacy"]}
]

MUTUAL_FUND_MASTER = [
    {"code": "122639", "name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "category": "Flexi Cap", "fund_house": "PPFAS Mutual Fund", "price": 90.63, "change": 0.48, "change_pct": 0.53, "return_1y": 21.4, "rating": 5},
    {"code": "120828", "name": "Quant Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Quant Mutual Fund", "price": 245.12, "change": 1.85, "change_pct": 0.76, "return_1y": 32.8, "rating": 5},
    {"code": "118834", "name": "Mirae Asset Large & Midcap Fund - Direct Plan - Growth", "category": "Large & Mid Cap", "fund_house": "Mirae Asset", "price": 142.50, "change": 0.92, "change_pct": 0.65, "return_1y": 23.5, "rating": 4},
    {"code": "119803", "name": "Nippon India Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Nippon India", "price": 168.30, "change": 1.15, "change_pct": 0.69, "return_1y": 34.2, "rating": 5},
    {"code": "125354", "name": "Axis Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Axis Mutual Fund", "price": 105.40, "change": 0.68, "change_pct": 0.65, "return_1y": 22.8, "rating": 4},
    {"code": "119551", "name": "SBI Bluechip Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "SBI Mutual Fund", "price": 88.20, "change": 0.52, "change_pct": 0.59, "return_1y": 18.5, "rating": 4},
    {"code": "120503", "name": "HDFC Top 100 Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "HDFC Mutual Fund", "price": 1080.50, "change": 7.20, "change_pct": 0.67, "return_1y": 24.1, "rating": 4},
    {"code": "120586", "name": "ICICI Prudential Bluechip Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "ICICI Prudential", "price": 112.40, "change": 0.74, "change_pct": 0.66, "return_1y": 20.8, "rating": 4},
    {"code": "127042", "name": "Motilal Oswal Midcap Fund - Direct Plan - Growth", "category": "Mid Cap", "fund_house": "Motilal Oswal", "price": 94.60, "change": 0.85, "change_pct": 0.91, "return_1y": 36.4, "rating": 5},
    {"code": "135781", "name": "Tata Digital India Fund - Direct Plan - Growth", "category": "Thematic / Tech", "fund_house": "Tata Mutual Fund", "price": 52.80, "change": -0.15, "change_pct": -0.28, "return_1y": 19.2, "rating": 4},
    {"code": "120716", "name": "UTI Nifty 50 Index Fund - Direct Plan - Growth", "category": "Index Fund", "fund_house": "UTI Mutual Fund", "price": 178.40, "change": 0.95, "change_pct": 0.54, "return_1y": 17.6, "rating": 5},
    {"code": "148712", "name": "Navi Nifty 50 Index Fund - Direct Plan - Growth", "category": "Index Fund", "fund_house": "Navi Mutual Fund", "price": 16.80, "change": 0.09, "change_pct": 0.54, "return_1y": 17.5, "rating": 5}
]
