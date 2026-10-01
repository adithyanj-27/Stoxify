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
    {"symbol": "ZENTEC.NS", "name": "Zen Technologies Ltd", "sector": "Defense", "aliases": ["zen", "zen tech", "zen technologies", "drones"]},
    {"symbol": "DATAPATTNS.NS", "name": "Data Patterns (India) Ltd", "sector": "Defense", "aliases": ["data patterns", "datapattns", "radar"]},

    # --- Railways & PSUs ---
    {"symbol": "IRFC.NS", "name": "Indian Railway Finance Corp", "sector": "Railways", "aliases": ["irfc", "railway finance"]},
    {"symbol": "IRCTC.NS", "name": "Indian Railway Catering & Tourism Corp", "sector": "Railways", "aliases": ["irctc", "railway booking"]},
    {"symbol": "RVNL.NS", "name": "Rail Vikas Nigam Ltd", "sector": "Railways", "aliases": ["rvnl", "rail vikas"]},
    {"symbol": "RAILTEL.NS", "name": "RailTel Corp of India Ltd", "sector": "Railways", "aliases": ["railtel", "railway wifi"]},
    {"symbol": "TITAGARH.NS", "name": "Titagarh Rail Systems Ltd", "sector": "Railways", "aliases": ["titagarh", "wagons", "trains"]},
    {"symbol": "BHEL.NS", "name": "Bharat Heavy Electricals Ltd", "sector": "Energy", "aliases": ["bhel", "turbines"]},

    # --- Power, Renewable & Clean Energy ---
    {"symbol": "TATAPOWER.NS", "name": "Tata Power Company Ltd", "sector": "Energy", "aliases": ["tata power", "ev charging", "solar"]},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy Ltd", "sector": "Energy", "aliases": ["suzlon", "wind energy", "green power"]},
    {"symbol": "IREDA.NS", "name": "Indian Renewable Energy Dev Agency", "sector": "Energy", "aliases": ["ireda", "green finance"]},
    {"symbol": "WAAREEENER.NS", "name": "Waaree Energies Ltd", "sector": "Energy", "aliases": ["waaree", "waaree energies", "solar panels"]},
    {"symbol": "PREMIERENE.NS", "name": "Premier Energies Ltd", "sector": "Energy", "aliases": ["premier energies", "premier", "solar cells"]},
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
    {"symbol": "NSE.BO", "name": "National Stock Exchange of India Ltd", "sector": "Finance", "aliases": ["nse", "national stock exchange", "nse india", "nse.bo"], "exchanges": ["BSE"]},

    # --- Auto & EV ---
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors Ltd (Royal Enfield)", "sector": "Auto", "aliases": ["eicher", "royal enfield", "bullet"]},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company Ltd", "sector": "Auto", "aliases": ["tvs", "apache", "jupiter"]},
    {"symbol": "ASHOKLEY.NS", "name": "Ashok Leyland Ltd", "sector": "Auto", "aliases": ["ashok leyland", "trucks"]},

    # --- Tech & Internet ---
    {"symbol": "TATATECH.NS", "name": "Tata Technologies Ltd", "sector": "IT", "aliases": ["tata tech", "tata technologies"]},
    {"symbol": "TATAELXSI.NS", "name": "Tata Elxsi Ltd", "sector": "IT", "aliases": ["tata elxsi", "design"]},
    {"symbol": "PAYTM.NS", "name": "One97 Communications (Paytm)", "sector": "IT", "aliases": ["paytm", "one97", "upi"]},
    {"symbol": "SWIGGY.NS", "name": "Swiggy Ltd", "sector": "Consumer", "aliases": ["swiggy", "instamart"]},

    # --- Metals & Commodities ---
    {"symbol": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals", "aliases": ["vedanta", "anil agarwal"]},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel Ltd", "sector": "Metals", "aliases": ["jsw steel", "jindal"]},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "sector": "Metals", "aliases": ["hindalco", "aluminium"]},

    # --- Pharma & Healthcare ---
    {"symbol": "CIPLA.NS", "name": "Cipla Ltd", "sector": "Pharma", "aliases": ["cipla"]},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharma", "aliases": ["dr reddy", "drreddy"]},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise", "sector": "Pharma", "aliases": ["apollo hospitals", "apollo pharmacy"]},
    {"symbol": "ZYDUSLIFE.NS", "name": "Zydus Lifesciences Ltd", "sector": "Pharma", "aliases": ["zydus", "zydus life", "cadila"]},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Laboratories Ltd", "sector": "Pharma", "aliases": ["divis", "divi", "divislab"]},
    {"symbol": "MANKIND.NS", "name": "Mankind Pharma Ltd", "sector": "Pharma", "aliases": ["mankind", "manforce"]},
    {"symbol": "TORNTPHARM.NS", "name": "Torrent Pharmaceuticals Ltd", "sector": "Pharma", "aliases": ["torrent pharma", "torntpharm"]},
    {"symbol": "LUPIN.NS", "name": "Lupin Ltd", "sector": "Pharma", "aliases": ["lupin"]},
    {"symbol": "AUROPHARMA.NS", "name": "Aurobindo Pharma Ltd", "sector": "Pharma", "aliases": ["aurobindo", "auropharma"]},
    {"symbol": "BIOCON.NS", "name": "Biocon Ltd", "sector": "Pharma", "aliases": ["biocon", "kiran mazumdar"]},

    # --- Consumer Electronics, Durables & EMS ---
    {"symbol": "DIXON.NS", "name": "Dixon Technologies (India) Ltd", "sector": "Consumer", "aliases": ["dixon", "dixon tech", "ems", "electronics"]},
    {"symbol": "HAVELLS.NS", "name": "Havells India Ltd", "sector": "Consumer", "aliases": ["havells", "lloyd", "electricals"]},
    {"symbol": "POLYCAB.NS", "name": "Polycab India Ltd", "sector": "Infra", "aliases": ["polycab", "cables", "wires"]},
    {"symbol": "KAYNES.NS", "name": "Kaynes Technology India Ltd", "sector": "IT", "aliases": ["kaynes", "semiconductor", "ems"]},
    {"symbol": "VOLTAS.NS", "name": "Voltas Ltd", "sector": "Consumer", "aliases": ["voltas", "ac", "air conditioner"]},
    {"symbol": "BLUESTARCO.NS", "name": "Blue Star Ltd", "sector": "Consumer", "aliases": ["blue star", "bluestar"]},

    # --- Consumer, Retail & E-Commerce ---
    {"symbol": "NYKAA.NS", "name": "FSN E-Commerce Ventures (Nykaa)", "sector": "Consumer", "aliases": ["nykaa", "fsn", "beauty", "cosmetics"]},
    {"symbol": "DMART.NS", "name": "Avenue Supermarts Ltd (DMart)", "sector": "Consumer", "aliases": ["dmart", "avenue supermarts", "radhakishan damani", "retail"]},
    {"symbol": "VBL.NS", "name": "Varun Beverages Ltd (PepsiCo)", "sector": "Consumer", "aliases": ["vbl", "varun beverages", "pepsi", "sting"]},
    {"symbol": "INDIGO.NS", "name": "InterGlobe Aviation Ltd (IndiGo)", "sector": "Consumer", "aliases": ["indigo", "interglobe", "airlines", "flight"]},
    {"symbol": "PAGEIND.NS", "name": "Page Industries Ltd (Jockey)", "sector": "Consumer", "aliases": ["page", "pageind", "jockey"]},
    {"symbol": "COLPAL.NS", "name": "Colgate-Palmolive (India) Ltd", "sector": "Consumer", "aliases": ["colgate", "colpal"]},
    {"symbol": "DABUR.NS", "name": "Dabur India Ltd", "sector": "Consumer", "aliases": ["dabur", "chyawanprash"]},
    {"symbol": "MARICO.NS", "name": "Marico Ltd", "sector": "Consumer", "aliases": ["marico", "parachute", "saffola"]},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India Ltd", "sector": "Consumer", "aliases": ["nestle", "maggi", "nescafe"]},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries Ltd", "sector": "Consumer", "aliases": ["britannia", "good day", "biscuits"]},
    {"symbol": "GODREJCP.NS", "name": "Godrej Consumer Products Ltd", "sector": "Consumer", "aliases": ["godrej cp", "godrej consumer", "good knight"]},
    {"symbol": "KALYANKJIL.NS", "name": "Kalyan Jewellers India Ltd", "sector": "Consumer", "aliases": ["kalyan", "kalyan jewellers", "gold"]},
    {"symbol": "JUBLFOOD.NS", "name": "Jubilant FoodWorks Ltd (Domino's)", "sector": "Consumer", "aliases": ["jubilant", "dominos", "pizza"]},
    {"symbol": "INDHOTEL.NS", "name": "The Indian Hotels Co Ltd (Taj)", "sector": "Consumer", "aliases": ["indhotel", "taj", "taj hotels", "ihcl"]},
    {"symbol": "BATAINDIA.NS", "name": "Bata India Ltd", "sector": "Consumer", "aliases": ["bata", "shoes"]},

    # --- Banking, Insurance & Broking ---
    {"symbol": "ANGELONE.NS", "name": "Angel One Ltd", "sector": "Finance", "aliases": ["angel one", "angel broking", "angelone"]},
    {"symbol": "POLICYBZR.NS", "name": "PB Fintech Ltd (Policybazaar)", "sector": "Finance", "aliases": ["policybazaar", "pb fintech", "policybzr"]},
    {"symbol": "MCX.NS", "name": "Multi Commodity Exchange of India", "sector": "Finance", "aliases": ["mcx", "commodity exchange", "gold futures"]},
    {"symbol": "IEX.NS", "name": "Indian Energy Exchange Ltd", "sector": "Energy", "aliases": ["iex", "power exchange"]},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance Co Ltd", "sector": "Finance", "aliases": ["hdfc life", "life insurance"]},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance Co Ltd", "sector": "Finance", "aliases": ["sbi life", "life insurance"]},
    {"symbol": "ICICIPRULI.NS", "name": "ICICI Prudential Life Insurance", "sector": "Finance", "aliases": ["icici pru", "icici life"]},
    {"symbol": "ICICIGI.NS", "name": "ICICI Lombard General Insurance", "sector": "Finance", "aliases": ["icici lombard", "general insurance"]},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank Ltd", "sector": "Banking", "aliases": ["indusind", "indusind bank"]},
    {"symbol": "AUBANK.NS", "name": "AU Small Finance Bank Ltd", "sector": "Banking", "aliases": ["au bank", "au small finance"]},
    {"symbol": "BANDHANBNK.NS", "name": "Bandhan Bank Ltd", "sector": "Banking", "aliases": ["bandhan bank", "bandhan"]},
    {"symbol": "MUTHOOTFIN.NS", "name": "Muthoot Finance Ltd", "sector": "Finance", "aliases": ["muthoot", "muthoot finance", "gold loan"]},
    {"symbol": "SHRIRAMFIN.NS", "name": "Shriram Finance Ltd", "sector": "Finance", "aliases": ["shriram", "shriram finance"]},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment & Finance", "sector": "Finance", "aliases": ["cholamandalam", "cholafin", "chola"]},
    {"symbol": "MOTILALOFS.NS", "name": "Motilal Oswal Financial Services", "sector": "Finance", "aliases": ["motilal", "motilal oswal", "mofs"]},

    # --- IT, Software & Digital ---
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies Ltd", "sector": "IT", "aliases": ["hcl", "hcl tech", "hcltech"]},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra Ltd", "sector": "IT", "aliases": ["tech mahindra", "techm"]},
    {"symbol": "LTIM.NS", "name": "LTIMindtree Ltd", "sector": "IT", "aliases": ["ltim", "ltimindtree", "mindtree", "l&t infotech"]},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems Ltd", "sector": "IT", "aliases": ["persistent", "persistent systems"]},
    {"symbol": "COFORGE.NS", "name": "Coforge Ltd", "sector": "IT", "aliases": ["coforge", "niit tech"]},
    {"symbol": "MPHASIS.NS", "name": "Mphasis Ltd", "sector": "IT", "aliases": ["mphasis"]},
    {"symbol": "KPITTECH.NS", "name": "KPIT Technologies Ltd", "sector": "IT", "aliases": ["kpit", "kpit tech", "auto software"]},
    {"symbol": "LTTS.NS", "name": "L&T Technology Services Ltd", "sector": "IT", "aliases": ["ltts", "l&t tech"]},
    {"symbol": "DELHIVERY.NS", "name": "Delhivery Ltd", "sector": "Consumer", "aliases": ["delhivery", "logistics", "courier"]},
    {"symbol": "NAUKRI.NS", "name": "Info Edge (India) Ltd (Naukri)", "sector": "IT", "aliases": ["naukri", "info edge", "jeevansathi", "99acres"]},

    # --- Realty & Infrastructure ---
    {"symbol": "DLF.NS", "name": "DLF Ltd", "sector": "Infra", "aliases": ["dlf", "real estate", "realty"]},
    {"symbol": "GODREJPROP.NS", "name": "Godrej Properties Ltd", "sector": "Infra", "aliases": ["godrej properties", "godrej prop"]},
    {"symbol": "LODHA.NS", "name": "Macrotech Developers Ltd (Lodha)", "sector": "Infra", "aliases": ["lodha", "macrotech"]},
    {"symbol": "PRESTIGE.NS", "name": "Prestige Estates Projects Ltd", "sector": "Infra", "aliases": ["prestige", "prestige estates"]},
    {"symbol": "OBEROIRLTY.NS", "name": "Oberoi Realty Ltd", "sector": "Infra", "aliases": ["oberoi realty", "oberoi"]},
    {"symbol": "GMRINFRA.NS", "name": "GMR Airports Infrastructure Ltd", "sector": "Infra", "aliases": ["gmr", "gmr infra", "airports"]},
    {"symbol": "IRB.NS", "name": "IRB Infrastructure Developers", "sector": "Infra", "aliases": ["irb", "irb infra", "highways", "toll"]},

    # --- Industrial, Engineering & Chemicals ---
    {"symbol": "SIEMENS.NS", "name": "Siemens Ltd", "sector": "Infra", "aliases": ["siemens", "engineering"]},
    {"symbol": "ABB.NS", "name": "ABB India Ltd", "sector": "Infra", "aliases": ["abb", "abb india", "automation"]},
    {"symbol": "CUMMINSIND.NS", "name": "Cummins India Ltd", "sector": "Infra", "aliases": ["cummins", "generators", "engines"]},
    {"symbol": "PIDILITIND.NS", "name": "Pidilite Industries Ltd", "sector": "Consumer", "aliases": ["pidilite", "fevicol", "m-seal", "dr fixit"]},
    {"symbol": "SRF.NS", "name": "SRF Ltd", "sector": "Metals", "aliases": ["srf", "chemicals", "packaging"]},
    {"symbol": "DEEPAKNTR.NS", "name": "Deepak Nitrite Ltd", "sector": "Metals", "aliases": ["deepak nitrite", "chemicals"]},
    {"symbol": "TATACHEM.NS", "name": "Tata Chemicals Ltd", "sector": "Metals", "aliases": ["tata chem", "tata chemicals", "soda ash"]},
    {"symbol": "ASTRAL.NS", "name": "Astral Ltd", "sector": "Infra", "aliases": ["astral", "astral pipes", "pipes"]},

    # --- Cement, Energy & EV ---
    {"symbol": "AMBUJACEM.NS", "name": "Ambuja Cements Ltd", "sector": "Infra", "aliases": ["ambuja", "ambuja cement"]},
    {"symbol": "ACC.NS", "name": "ACC Ltd", "sector": "Infra", "aliases": ["acc", "acc cement"]},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum Corp Ltd", "sector": "Energy", "aliases": ["bpcl", "bharat petroleum", "petrol"]},
    {"symbol": "IOC.NS", "name": "Indian Oil Corporation Ltd", "sector": "Energy", "aliases": ["ioc", "indian oil", "petrol"]},
    {"symbol": "GAIL.NS", "name": "GAIL (India) Ltd", "sector": "Energy", "aliases": ["gail", "gas authority"]},
    {"symbol": "OLAELEC.NS", "name": "Ola Electric Mobility Ltd", "sector": "Auto", "aliases": ["ola electric", "ola", "scooter"]}
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

ETF_MASTER = [
    # --- Commodities (Gold & Silver) ---
    {"symbol": "GOLDBEES.NS", "name": "Nippon India ETF Gold BeES", "category": "Gold & Silver", "sector": "Commodity / Gold", "aliases": ["gold", "goldbees", "gold bees", "nippon gold", "sona", "bullion", "etf"]},
    {"symbol": "SILVERBEES.NS", "name": "Nippon India ETF Silver BeES", "category": "Gold & Silver", "sector": "Commodity / Silver", "aliases": ["silver", "silverbees", "silver bees", "nippon silver", "chandi", "bullion", "etf"]},
    {"symbol": "HDFCGOLD.NS", "name": "HDFC Gold ETF", "category": "Gold & Silver", "sector": "Commodity / Gold", "aliases": ["hdfc gold", "gold", "hdfc etf", "etf"]},
    {"symbol": "SETFGOLD.NS", "name": "SBI Gold ETF", "category": "Gold & Silver", "sector": "Commodity / Gold", "aliases": ["sbi gold", "gold", "sbi etf", "setfgold", "etf"]},
    {"symbol": "HDFCSILVER.NS", "name": "HDFC Silver ETF", "category": "Gold & Silver", "sector": "Commodity / Silver", "aliases": ["hdfc silver", "silver", "etf"]},

    # --- Broad Market Index ETFs ---
    {"symbol": "NIFTYBEES.NS", "name": "Nippon India ETF Nifty BeES", "category": "Index", "sector": "Market Index", "aliases": ["nifty", "niftybees", "nifty 50", "index etf", "bees", "etf"]},
    {"symbol": "BANKBEES.NS", "name": "Nippon India ETF Bank BeES", "category": "Index", "sector": "Banking Index", "aliases": ["bankbees", "bank nifty", "bank bees", "etf"]},
    {"symbol": "JUNIORBEES.NS", "name": "Nippon India ETF Junior BeES", "category": "Index", "sector": "Nifty Next 50", "aliases": ["juniorbees", "next 50", "junior bees", "etf"]},
    {"symbol": "MID150BEES.NS", "name": "Nippon India ETF Nifty Midcap 150", "category": "Index", "sector": "Midcap Index", "aliases": ["midcap bees", "midcap", "mid150bees", "etf"]},

    # --- Sectoral & Thematic ETFs ---
    {"symbol": "ITBEES.NS", "name": "Nippon India ETF Nifty IT", "category": "Sectoral", "sector": "IT Sector", "aliases": ["itbees", "it bees", "tech etf", "it", "nifty it", "etf"]},
    {"symbol": "PHARMABEES.NS", "name": "Nippon India ETF Nifty Pharma", "category": "Sectoral", "sector": "Pharma Sector", "aliases": ["pharmabees", "pharma bees", "healthcare", "etf"]},
    {"symbol": "AUTOBEES.NS", "name": "Nippon India ETF Nifty Auto", "category": "Sectoral", "sector": "Auto Sector", "aliases": ["autobees", "auto bees", "automobiles", "etf"]},
    {"symbol": "CPSEETF.NS", "name": "CPSE ETF", "category": "Sectoral", "sector": "PSU Sector", "aliases": ["cpse", "cpse etf", "psu etf", "maharatna", "etf"]},

    # --- Global & US Tech ETFs ---
    {"symbol": "MON100.NS", "name": "Motilal Oswal Nasdaq 100 ETF", "category": "Global", "sector": "US Tech / Global", "aliases": ["nasdaq", "mon100", "us tech", "apple", "nvidia", "microsoft", "global etf", "etf"]},
    {"symbol": "MAFANG.NS", "name": "Mirae Asset NYSE FANG+ ETF", "category": "Global", "sector": "US Tech / Global", "aliases": ["fang", "mafang", "faang", "us tech", "meta", "google", "amazon", "etf"]}
]
