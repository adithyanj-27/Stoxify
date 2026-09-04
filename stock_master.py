# Master Directory of Indian Equities & Mutual Funds
# Metadata only: real-time prices are fetched live from yfinance (NSE) & AMFI API

STOCK_MASTER = [
    # --- NIFTY 50 & Top Equities ---
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy", "aliases": ["ril", "reliance", "mukesh ambani", "jio"]},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "IT", "aliases": ["tcs", "tata consultancy"]},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Banking", "aliases": ["hdfc", "hdfc bank"]},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "IT", "aliases": ["infy", "infosys"]},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Banking", "aliases": ["icici", "icici bank"]},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking", "aliases": ["sbi", "sbin", "state bank"]},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "sector": "Telecom", "aliases": ["airtel", "bharti airtel"]},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "sector": "Consumer", "aliases": ["itc", "itc hotels"]},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Infra", "aliases": ["l&t", "lt", "larsen"]},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "sector": "Finance", "aliases": ["bajaj finance", "bajfinance"]},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "sector": "Consumer", "aliases": ["hul", "unilever", "hindustan unilever"]},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "sector": "Auto", "aliases": ["maruti", "suzuki", "maruti suzuki"]},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Ind. Ltd", "sector": "Pharma", "aliases": ["sun pharma", "sun"]},
    {"symbol": "TITAN.NS", "name": "Titan Company Ltd", "sector": "Consumer", "aliases": ["titan", "tanishq", "fastrack"]},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals", "aliases": ["tata steel", "tisco"]},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "sector": "Energy", "aliases": ["adani", "adani ent", "gautam adani"]},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports & SEZ Ltd", "sector": "Infra", "aliases": ["adani ports", "apsez"]},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "sector": "IT", "aliases": ["wipro"]},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp of India", "sector": "Energy", "aliases": ["powergrid", "power grid"]},
    {"symbol": "NTPC.NS", "name": "NTPC Ltd", "sector": "Energy", "aliases": ["ntpc", "national thermal power"]},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp Ltd", "sector": "Energy", "aliases": ["ongc"]},
    {"symbol": "COALINDIA.NS", "name": "Coal India Ltd", "sector": "Metals", "aliases": ["coal india", "cil"]},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Auto", "aliases": ["m&m", "mahindra", "thar", "scorpio"]},
    {"symbol": "TMCV.NS", "name": "Tata Motors Ltd (Commercial)", "sector": "Auto", "aliases": ["tata motors", "tatamotors", "tmcv", "tata commercial"]},
    {"symbol": "TMPV.NS", "name": "Tata Motors Passenger Vehicles Ltd", "sector": "Auto", "aliases": ["tata motors", "tatamotors", "tmpv", "tata ev", "tata cars"]},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Banking", "aliases": ["axis", "axis bank"]},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "aliases": ["kotak", "kotak bank"]},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement Ltd", "sector": "Infra", "aliases": ["ultratech", "cement"]},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd", "sector": "Consumer", "aliases": ["asian paints", "paints"]},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto Ltd", "sector": "Auto", "aliases": ["bajaj auto", "pulsar"]},
    {"symbol": "TRENT.NS", "name": "Trent Ltd (Westside & Zudio)", "sector": "Consumer", "aliases": ["trent", "zudio", "westside"]},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "sector": "Finance", "aliases": ["jio financial", "jiofin", "jfs"]},
    {"symbol": "ETERNAL.NS", "name": "Zomato Ltd (Eternal Ltd)", "sector": "Consumer", "aliases": ["zomato", "blinkit", "eternal"]},

    # --- Defense & Aerospace & Shipbuilding ---
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "sector": "Defense", "aliases": ["hal", "tejas", "defense"]},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "sector": "Defense", "aliases": ["bel", "defense"]},
    {"symbol": "MAZDOCK.NS", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defense", "aliases": ["mazagon", "mazdock", "shipbuilders"]},
    {"symbol": "COCHINSHIP.NS", "name": "Cochin Shipyard Ltd", "sector": "Defense", "aliases": ["cochin shipyard", "cochinship"]},
    {"symbol": "GRSE.NS", "name": "Garden Reach Shipbuilders Ltd", "sector": "Defense", "aliases": ["grse", "garden reach"]},
    {"symbol": "BDL.NS", "name": "Bharat Dynamics Ltd", "sector": "Defense", "aliases": ["bdl", "missiles"]},

    # --- Railways & PSUs ---
    {"symbol": "IRFC.NS", "name": "Indian Railway Finance Corp", "sector": "Railways", "aliases": ["irfc", "railway finance"]},
    {"symbol": "IRCTC.NS", "name": "Indian Railway Catering & Tourism Corp", "sector": "Railways", "aliases": ["irctc", "railway booking"]},
    {"symbol": "RVNL.NS", "name": "Rail Vikas Nigam Ltd", "sector": "Railways", "aliases": ["rvnl", "rail vikas"]},
    {"symbol": "RAILTEL.NS", "name": "RailTel Corp of India Ltd", "sector": "Railways", "aliases": ["railtel", "railway wifi"]},
    {"symbol": "BHEL.NS", "name": "Bharat Heavy Electricals Ltd", "sector": "Energy", "aliases": ["bhel", "turbines"]},

    # --- Power, Renewable & Clean Energy ---
    {"symbol": "TATAPOWER.NS", "name": "Tata Power Company Ltd", "sector": "Energy", "aliases": ["tata power", "ev charging", "solar"]},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy Ltd", "sector": "Energy", "aliases": ["suzlon", "wind energy", "green power"]},
    {"symbol": "IREDA.NS", "name": "Indian Renewable Energy Dev Agency", "sector": "Energy", "aliases": ["ireda", "green finance"]},
    {"symbol": "ADANIGREEN.NS", "name": "Adani Green Energy Ltd", "sector": "Energy", "aliases": ["adani green", "solar"]},
    {"symbol": "ADANIPOWER.NS", "name": "Adani Power Ltd", "sector": "Energy", "aliases": ["adani power"]},
    {"symbol": "NHPC.NS", "name": "NHPC Ltd", "sector": "Energy", "aliases": ["nhpc", "hydro power"]},
    {"symbol": "RECLTD.NS", "name": "REC Ltd", "sector": "Finance", "aliases": ["rec", "rural electrification"]},
    {"symbol": "PFC.NS", "name": "Power Finance Corp Ltd", "sector": "Finance", "aliases": ["pfc", "power finance"]},

    # --- Banking & Financial Services ---
    {"symbol": "FEDERALBNK.NS", "name": "The Federal Bank Ltd", "sector": "Banking", "aliases": ["federal bank", "federalbank"]},
    {"symbol": "BANKBARODA.NS", "name": "Bank of Baroda", "sector": "Banking", "aliases": ["bob", "bank of baroda"]},
    {"symbol": "PNB.NS", "name": "Punjab National Bank", "sector": "Banking", "aliases": ["pnb", "punjab national bank"]},
    {"symbol": "CANBK.NS", "name": "Canara Bank", "sector": "Banking", "aliases": ["canara bank", "canbk"]},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank Ltd", "sector": "Banking", "aliases": ["idfc", "idfc first"]},
    {"symbol": "YESBANK.NS", "name": "Yes Bank Ltd", "sector": "Banking", "aliases": ["yes bank"]},
    {"symbol": "CDSL.NS", "name": "Central Depository Services Ltd", "sector": "Finance", "aliases": ["cdsl", "demat"]},
    {"symbol": "BSE.NS", "name": "BSE Ltd", "sector": "Finance", "aliases": ["bse", "bombay stock exchange"]},

    # --- Auto & EV ---
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors Ltd (Royal Enfield)", "sector": "Auto", "aliases": ["eicher", "royal enfield", "bullet"]},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company Ltd", "sector": "Auto", "aliases": ["tvs", "apache", "jupiter"]},
    {"symbol": "ASHOKLEY.NS", "name": "Ashok Leyland Ltd", "sector": "Auto", "aliases": ["ashok leyland", "trucks"]},

    # --- Tech & Internet ---
    {"symbol": "TATATECH.NS", "name": "Tata Technologies Ltd", "sector": "IT", "aliases": ["tata tech", "tata technologies"]},
    {"symbol": "TATAELXSI.NS", "name": "Tata Elxsi Ltd", "sector": "IT", "aliases": ["tata elxsi", "design"]},
    {"symbol": "PAYTM.NS", "name": "One97 Communications (Paytm)", "sector": "IT", "aliases": ["paytm", "one97", "upi"]},

    # --- Metals & Commodities ---
    {"symbol": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals", "aliases": ["vedanta", "anil agarwal"]},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel Ltd", "sector": "Metals", "aliases": ["jsw steel", "jindal"]},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "sector": "Metals", "aliases": ["hindalco", "aluminium"]},

    # --- Pharma ---
    {"symbol": "CIPLA.NS", "name": "Cipla Ltd", "sector": "Pharma", "aliases": ["cipla"]},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharma", "aliases": ["dr reddy", "drreddy"]},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise", "sector": "Pharma", "aliases": ["apollo hospitals", "apollo pharmacy"]}
]

MUTUAL_FUND_MASTER = [
    {"code": "122639", "name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "category": "Flexi Cap", "fund_house": "PPFAS Mutual Fund", "rating": 5},
    {"code": "120828", "name": "Quant Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Quant Mutual Fund", "rating": 5},
    {"code": "118834", "name": "Mirae Asset Large & Midcap Fund - Direct Plan - Growth", "category": "Large & Mid Cap", "fund_house": "Mirae Asset", "rating": 4},
    {"code": "119803", "name": "Nippon India Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Nippon India", "rating": 5},
    {"code": "125354", "name": "Axis Small Cap Fund - Direct Plan - Growth", "category": "Small Cap", "fund_house": "Axis Mutual Fund", "rating": 4},
    {"code": "119551", "name": "SBI Bluechip Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "SBI Mutual Fund", "rating": 4},
    {"code": "120503", "name": "HDFC Top 100 Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "HDFC Mutual Fund", "rating": 4},
    {"code": "120586", "name": "ICICI Prudential Bluechip Fund - Direct Plan - Growth", "category": "Large Cap", "fund_house": "ICICI Prudential", "rating": 4},
    {"code": "127042", "name": "Motilal Oswal Midcap Fund - Direct Plan - Growth", "category": "Mid Cap", "fund_house": "Motilal Oswal", "rating": 5},
    {"code": "135781", "name": "Tata Digital India Fund - Direct Plan - Growth", "category": "Thematic / Tech", "fund_house": "Tata Mutual Fund", "rating": 4},
    {"code": "120716", "name": "UTI Nifty 50 Index Fund - Direct Plan - Growth", "category": "Index Fund", "fund_house": "UTI Mutual Fund", "rating": 5},
    {"code": "148712", "name": "Navi Nifty 50 Index Fund - Direct Plan - Growth", "category": "Index Fund", "fund_house": "Navi Mutual Fund", "rating": 5}
]
