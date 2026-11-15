"""Writes the curated source CSVs into ../Dataset (single source of truth for the KG).

NOTE: Airport coordinates / runway lengths / aircraft figures are curated, rounded values
transcribed for a small regional study area (South Asia - Gulf - Europe - SE/E Asia). They are
representative of the public OurAirports / OpenFlights / OpenAP datasets but were NOT
machine-downloaded; verify them against those sources before final submission (see SOURCES.md).
Zones, hazards and scenarios are FICTIONAL / illustrative and are not real-world closures.
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Dataset")

# icao, iata, name, city, country_code, lat, lon, operational, category(I/R), [(designator, length_m)]
AIRPORTS = [
 ("OPIS","ISB","Islamabad International Airport","Islamabad","PK",33.5607,72.8516,True,"I",[("15/33",3658)]),
 ("OPKC","KHI","Jinnah International Airport","Karachi","PK",24.9065,67.1608,True,"I",[("07R/25L",3200),("07L/25R",3400)]),
 ("OPLA","LHE","Allama Iqbal International Airport","Lahore","PK",31.5216,74.4036,True,"I",[("18R/36L",3360),("18L/36R",2743)]),
 ("OPPS","PEW","Bacha Khan International Airport","Peshawar","PK",33.9939,71.5146,True,"I",[("17/35",2743)]),
 ("OPMT","MUX","Multan International Airport","Multan","PK",30.2032,71.4191,True,"I",[("18/36",3200)]),
 ("OPFA","FSD","Faisalabad International Airport","Faisalabad","PK",31.3650,72.9948,True,"I",[("03/21",3050)]),
 ("OPQT","UET","Quetta International Airport","Quetta","PK",30.2514,66.9378,True,"R",[("12/30",3000)]),
 ("OPSD","KDU","Skardu International Airport","Skardu","PK",35.3355,75.5360,True,"R",[("14/32",2743)]),
 ("OPGT","GIL","Gilgit Airport","Gilgit","PK",35.9188,74.3336,False,"R",[("07/25",1830)]),
 ("OPCH","CJL","Chitral Airport","Chitral","PK",35.8866,71.8006,True,"R",[("04/22",1524)]),
 ("OMDB","DXB","Dubai International Airport","Dubai","AE",25.2528,55.3644,True,"I",[("12L/30R",4447),("12R/30L",4000)]),
 ("OMAA","AUH","Zayed International Airport","Abu Dhabi","AE",24.4330,54.6511,True,"I",[("13L/31R",4100),("13R/31L",4100)]),
 ("OMSJ","SHJ","Sharjah International Airport","Sharjah","AE",25.3286,55.5172,True,"I",[("12/30",4060)]),
 ("OTHH","DOH","Hamad International Airport","Doha","QA",25.2731,51.6081,True,"I",[("16R/34L",4850),("16L/34R",4250)]),
 ("OBBI","BAH","Bahrain International Airport","Manama","BH",26.2708,50.6336,True,"I",[("12R/30L",3964)]),
 ("OKBK","KWI","Kuwait International Airport","Kuwait City","KW",29.2266,47.9689,True,"I",[("15R/33L",3500),("15L/33R",3400)]),
 ("OOMS","MCT","Muscat International Airport","Muscat","OM",23.5933,58.2844,True,"I",[("08R/26L",4000)]),
 ("OERK","RUH","King Khalid International Airport","Riyadh","SA",24.9576,46.6988,True,"I",[("15L/33R",4205),("15R/33L",4205)]),
 ("OEJN","JED","King Abdulaziz International Airport","Jeddah","SA",21.6796,39.1565,True,"I",[("16L/34R",4000),("16R/34L",3800)]),
 ("OEDF","DMM","King Fahd International Airport","Dammam","SA",26.4712,49.7979,True,"I",[("16L/34R",4000),("16R/34L",4000)]),
 ("VIDP","DEL","Indira Gandhi International Airport","Delhi","IN",28.5562,77.1000,True,"I",[("11/29",4430),("10/28",3810),("09/27",3810)]),
 ("VABB","BOM","Chhatrapati Shivaji Maharaj International Airport","Mumbai","IN",19.0887,72.8679,True,"I",[("09/27",3445),("14/32",2925)]),
 ("VIAR","ATQ","Sri Guru Ram Dass Jee International Airport","Amritsar","IN",31.7096,74.7973,True,"R",[("16/34",3658)]),
 ("VIJP","JAI","Jaipur International Airport","Jaipur","IN",26.8242,75.8122,True,"R",[("09/27",2743)]),
 ("VAAH","AMD","Sardar Vallabhbhai Patel International Airport","Ahmedabad","IN",23.0772,72.6347,True,"I",[("05/23",3505)]),
 ("OAKB","KBL","Hamid Karzai International Airport","Kabul","AF",34.5659,69.2123,True,"I",[("11/29",3500)]),
 ("OIIE","IKA","Imam Khomeini International Airport","Tehran","IR",35.4161,51.1522,True,"I",[("11R/29L",4200),("11L/29R",4200)]),
 ("UTTT","TAS","Islam Karimov Tashkent International Airport","Tashkent","UZ",41.2579,69.2812,True,"I",[("08L/26R",4000),("08R/26L",3000)]),
 ("LTFM","IST","Istanbul Airport","Istanbul","TR",41.2753,28.7519,True,"I",[("16L/34R",4100),("17R/35L",3750)]),
 ("EGLL","LHR","London Heathrow Airport","London","GB",51.4700,-0.4543,True,"I",[("09L/27R",3902),("09R/27L",3660)]),
 ("EDDF","FRA","Frankfurt Airport","Frankfurt","DE",50.0379,8.5622,True,"I",[("07C/25C",4000),("07L/25R",2800)]),
 ("LFPG","CDG","Paris Charles de Gaulle Airport","Paris","FR",49.0097,2.5479,True,"I",[("08R/26L",4215),("09L/27R",2700)]),
 ("VTBS","BKK","Suvarnabhumi Airport","Bangkok","TH",13.6900,100.7501,True,"I",[("01L/19R",4000),("01R/19L",3700)]),
 ("WSSS","SIN","Singapore Changi Airport","Singapore","SG",1.3644,103.9915,True,"I",[("02L/20R",4000),("02C/20C",4000)]),
 ("WMKK","KUL","Kuala Lumpur International Airport","Kuala Lumpur","MY",2.7456,101.7099,True,"I",[("14L/32R",4124),("14R/32L",4000)]),
 ("ZBAA","PEK","Beijing Capital International Airport","Beijing","CN",40.0799,116.6031,True,"I",[("01/19",3800),("18R/36L",3200)]),
 ("VGHS","DAC","Hazrat Shahjalal International Airport","Dhaka","BD",23.8433,90.3978,True,"I",[("14/32",3200)]),
 ("VCBI","CMB","Bandaranaike International Airport","Colombo","LK",7.1808,79.8841,True,"I",[("04/22",3350)]),
]

COUNTRIES = {
 "PK":"Pakistan","AE":"United Arab Emirates","QA":"Qatar","BH":"Bahrain","KW":"Kuwait","OM":"Oman",
 "SA":"Saudi Arabia","IN":"India","AF":"Afghanistan","IR":"Iran","UZ":"Uzbekistan","TR":"Turkey",
 "GB":"United Kingdom","DE":"Germany","FR":"France","TH":"Thailand","SG":"Singapore","MY":"Malaysia",
 "CN":"China","BD":"Bangladesh","LK":"Sri Lanka",
}

# id, label, icao type, class(Widebody/Narrowbody/Turboprop), range_km, min_runway_m, cruise_kmh
AIRCRAFT = [
 ("A380-800","Airbus A380-800","A388","Widebody",15200,3000,903),
 ("B777-300ER","Boeing 777-300ER","B77W","Widebody",13650,3050,905),
 ("B787-9","Boeing 787-9 Dreamliner","B789","Widebody",14010,2800,903),
 ("A320-200","Airbus A320-200","A320","Narrowbody",6150,2100,828),
 ("B737-800","Boeing 737-800","B738","Narrowbody",5436,2300,842),
 ("ATR72-600","ATR 72-600","AT76","Turboprop",1528,1333,510),
]

# Undirected route segments as IATA pairs (stored once; first = connectsFrom, second = connectsTo)
SEGMENT_PAIRS = """
ISB-KHI ISB-LHE ISB-PEW ISB-MUX ISB-UET ISB-KDU ISB-GIL ISB-FSD ISB-CJL LHE-KHI LHE-MUX LHE-FSD
KHI-UET KHI-MUX KHI-PEW KHI-FSD PEW-CJL KDU-GIL UET-MUX
ISB-DXB ISB-AUH ISB-DOH ISB-JED ISB-RUH ISB-MCT ISB-SHJ LHE-DXB LHE-AUH LHE-SHJ LHE-DOH LHE-JED LHE-RUH
KHI-DXB KHI-AUH KHI-SHJ KHI-DOH KHI-BAH KHI-KWI KHI-MCT KHI-JED KHI-DMM KHI-RUH
MUX-DXB MUX-SHJ PEW-DXB PEW-SHJ FSD-DXB FSD-SHJ UET-DXB
DXB-AUH DXB-SHJ DXB-DOH DXB-BAH DXB-KWI DXB-MCT DXB-JED DXB-RUH DXB-DMM AUH-DOH AUH-MCT AUH-RUH
DOH-BAH DOH-KWI DOH-JED DOH-RUH DOH-DMM DOH-MCT BAH-KWI BAH-DMM KWI-DMM KWI-RUH RUH-JED RUH-DMM
DXB-IST DOH-IST JED-IST KWI-IST DXB-LHR DOH-LHR DXB-FRA DOH-FRA DXB-CDG DOH-CDG AUH-LHR
IST-LHR IST-FRA IST-CDG LHR-FRA LHR-CDG FRA-CDG KHI-IST ISB-IST ISB-LHR LHE-LHR KHI-LHR
DEL-DXB BOM-DXB AMD-DXB JAI-DXB ATQ-DXB DEL-DOH BOM-DOH DEL-AUH BOM-AUH DEL-LHR BOM-LHR DEL-FRA
DEL-BKK DEL-SIN BOM-SIN DEL-DAC DEL-CMB BOM-CMB DEL-BOM DEL-AMD DEL-JAI DEL-ATQ BOM-AMD DEL-KBL
DXB-BKK DXB-SIN DXB-KUL DXB-PEK DXB-DAC DXB-CMB DOH-BKK DOH-SIN DOH-KUL BKK-SIN BKK-KUL SIN-KUL
BKK-PEK SIN-PEK KUL-PEK DAC-BKK CMB-SIN CMB-KUL ISB-PEK ISB-KUL ISB-BKK
ISB-KBL ISB-TAS PEW-KBL KBL-DXB KBL-TAS TAS-IST TAS-DXB KBL-IKA IKA-DXB IKA-IST IKA-DOH IKA-KWI IKA-TAS
""".split()

# FICTIONAL illustrative zones/hazards. polygon = [(lon, lat), ...]
# id, label, class, active, polygon
ZONES = [
 ("RZ-ALPHA","Restricted Zone Alpha (fictional naval exercise area)","RestrictedZone",True,
  [(61.0,23.0),(63.6,23.0),(63.6,25.4),(61.0,25.4)]),
 ("PZ-BRAVO","Prohibited Zone Bravo (fictional)","ProhibitedZone",True,
  [(58.0,33.0),(64.0,33.0),(64.0,36.5),(58.0,36.5)]),
 ("RZ-CHARLIE","Restricted Zone Charlie (fictional, currently inactive)","RestrictedZone",False,
  [(49.0,26.5),(52.0,26.5),(52.0,28.5),(49.0,28.5)]),
 ("AZ-DELTA","Advisory Area Delta (fictional, advisory only)","AdvisoryZone",True,
  [(74.0,32.0),(78.0,32.0),(78.0,36.5),(74.0,36.5)]),
]
# id, label, hazard type, severity(1-5), active, polygon
HAZARDS = [
 ("STORM-1","Thunderstorm cell Punjab (fictional)","Thunderstorm",4,True,
  [(72.0,29.8),(74.0,29.8),(74.0,31.0),(72.0,31.0)]),
 ("STORM-2","Thunderstorm line northern Gulf (fictional)","Thunderstorm",3,True,
  [(49.5,27.0),(52.0,27.0),(52.0,29.0),(49.5,29.0)]),
 ("TURB-3","Moderate turbulence Karakoram (fictional)","Turbulence",2,True,
  [(73.5,34.5),(76.5,34.5),(76.5,36.5),(73.5,36.5)]),
 ("ASH-4","Volcanic ash plume Arabian Sea (fictional, expired)","VolcanicAsh",5,False,
  [(66.0,22.0),(69.0,22.0),(69.0,24.0),(66.0,24.0)]),
 ("ICE-5","Icing band Hindu Kush (fictional)","Icing",3,True,
  [(71.0,34.4),(73.0,34.4),(73.0,35.5),(71.0,35.5)]),
]

# id, label, aircraft id, remaining range km, current lat, current lon
SCENARIOS = [
 ("S1","Engine-out diversion: A380 over Arabian Sea","A380-800",1500,25.0,64.0),
 ("S2","Weather diversion: ATR 72 near Chitral","ATR72-600",500,35.5,72.2),
 ("S3","Low-fuel diversion: B737-800 over northern Gulf","B737-800",1200,27.5,50.8),
 ("S4","Medical diversion: A320 over Eastern Turkey","A320-200",1500,38.5,40.0),
 ("S5","Long-haul diversion: B787-9 over western Afghanistan","B787-9",2500,34.5,63.0),
 ("S6","Edge case: A380 with 300 km remaining over open sea","A380-800",300,22.0,66.0),
]
DIST_WINDOW_FACTOR = 1.5   # PositionDistance nodes are materialised for airports within 1.5 x remaining range


def write_csvs():
    os.makedirs(OUT, exist_ok=True)
    def w(name, header, rows):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
            cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    w("airports.csv", ["icao","iata","name","city","country_code","latitude","longitude","operational","category"],
      [(a[0],a[1],a[2],a[3],a[4],a[5],a[6],str(a[7]).lower(),a[8]) for a in AIRPORTS])
    w("runways.csv", ["airport_icao","designator","length_m"],
      [(a[0],d,l) for a in AIRPORTS for d,l in a[9]])
    w("countries.csv", ["code","name"], sorted(COUNTRIES.items()))
    w("aircraft.csv", ["id","label","icao_type","class","range_km","min_runway_m","cruise_kmh"], AIRCRAFT)
    iata = {a[1]:a[0] for a in AIRPORTS}
    w("segments.csv", ["from_icao","to_icao"], [(iata[p.split('-')[0]], iata[p.split('-')[1]]) for p in SEGMENT_PAIRS])
    w("zones.csv", ["id","label","class","active","polygon_lonlat"],
      [(z[0],z[1],z[2],str(z[3]).lower(),";".join(f"{x},{y}" for x,y in z[4])) for z in ZONES])
    w("hazards.csv", ["id","label","hazard_type","severity","active","polygon_lonlat"],
      [(h[0],h[1],h[2],h[3],str(h[4]).lower(),";".join(f"{x},{y}" for x,y in h[5])) for h in HAZARDS])
    w("scenarios.csv", ["id","label","aircraft_id","remaining_range_km","current_lat","current_lon"], SCENARIOS)


if __name__ == "__main__":
    write_csvs()
    print("CSV files written to", os.path.abspath(OUT))
