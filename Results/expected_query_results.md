# Expected SPARQL results

Computed in plain Python over the reasoned graph (`src/expected_results.py`). After running each `.rq` in GraphDB, the rows must match (GraphDB may order ties differently). Run `src/run_everything.py` to regenerate.

## q01 - CQ1 Airports in Pakistan (basic pattern)  (10 rows)

| iata | icao | name | lat | lon |
|---|---|---|---|---|
| CJL | OPCH | Chitral Airport | 35.8866 | 71.8006 |
| FSD | OPFA | Faisalabad International Airport | 31.365 | 72.9948 |
| GIL | OPGT | Gilgit Airport | 35.9188 | 74.3336 |
| ISB | OPIS | Islamabad International Airport | 33.5607 | 72.8516 |
| KDU | OPSD | Skardu International Airport | 35.3355 | 75.536 |
| KHI | OPKC | Jinnah International Airport | 24.9065 | 67.1608 |
| LHE | OPLA | Allama Iqbal International Airport | 31.5216 | 74.4036 |
| MUX | OPMT | Multan International Airport | 30.2032 | 71.4191 |
| PEW | OPPS | Bacha Khan International Airport | 33.9939 | 71.5146 |
| UET | OPQT | Quetta International Airport | 30.2514 | 66.9378 |

## q02 - CQ2 Runways longer than 3,500 m (FILTER)  (37 rows)

| iata | designator | length |
|---|---|---|
| DOH | 16R/34L | 4850 |
| DXB | 12L/30R | 4447 |
| DEL | 11/29 | 4430 |
| DOH | 16L/34R | 4250 |
| CDG | 08R/26L | 4215 |
| RUH | 15L/33R | 4205 |
| RUH | 15R/33L | 4205 |
| IKA | 11L/29R | 4200 |
| IKA | 11R/29L | 4200 |
| KUL | 14L/32R | 4124 |
| AUH | 13R/31L | 4100 |
| AUH | 13L/31R | 4100 |
| IST | 16L/34R | 4100 |
| SHJ | 12/30 | 4060 |
| BKK | 01L/19R | 4000 |
| DMM | 16R/34L | 4000 |
| DMM | 16L/34R | 4000 |
| DXB | 12R/30L | 4000 |
| FRA | 07C/25C | 4000 |
| JED | 16L/34R | 4000 |
| KUL | 14R/32L | 4000 |
| MCT | 08R/26L | 4000 |
| SIN | 02C/20C | 4000 |
| SIN | 02L/20R | 4000 |
| TAS | 08L/26R | 4000 |
| BAH | 12R/30L | 3964 |
| LHR | 09L/27R | 3902 |
| DEL | 10/28 | 3810 |
| DEL | 09/27 | 3810 |
| JED | 16R/34L | 3800 |
| PEK | 01/19 | 3800 |
| IST | 17R/35L | 3750 |
| BKK | 01R/19L | 3700 |
| LHR | 09R/27L | 3660 |
| ATQ | 16/34 | 3658 |
| ISB | 15/33 | 3658 |
| AMD | 05/23 | 3505 |

## q03 - CQ12 Hazards with optional affected segments (OPTIONAL)  (32 rows)

| hazard | type | severity | active | segment |
|---|---|---|---|---|
| Volcanic ash plume Arabian Sea (fictional, expired) | VolcanicAsh | 5 | false | AMD-DXB |
| Volcanic ash plume Arabian Sea (fictional, expired) | VolcanicAsh | 5 | false | BOM-LHR |
| Volcanic ash plume Arabian Sea (fictional, expired) | VolcanicAsh | 5 | false | DXB-BKK |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | ATQ-DXB |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | DEL-FRA |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | DEL-KBL |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | DEL-LHR |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | KHI-FSD |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-AUH |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-DOH |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-DXB |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-JED |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-KHI |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-MUX |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-RUH |
| Thunderstorm cell Punjab (fictional) | Thunderstorm | 4 | true | LHE-SHJ |
| Icing band Hindu Kush (fictional) | Icing | 3 | true | ISB-CJL |
| Icing band Hindu Kush (fictional) | Icing | 3 | true | ISB-TAS |
| Icing band Hindu Kush (fictional) | Icing | 3 | true | PEW-CJL |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | BAH-KWI |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | BOM-LHR |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DOH-KWI |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DXB-CDG |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DXB-FRA |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DXB-IST |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DXB-KWI |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | DXB-LHR |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | IKA-DOH |
| Thunderstorm line northern Gulf (fictional) | Thunderstorm | 3 | true | KHI-KWI |
| Moderate turbulence Karakoram (fictional) | Turbulence | 2 | true | ISB-GIL |
| Moderate turbulence Karakoram (fictional) | Turbulence | 2 | true | ISB-KDU |
| Moderate turbulence Karakoram (fictional) | Turbulence | 2 | true | KDU-GIL |

## q04 - CQ9a Neighbours of ISB (UNION)  (23 rows)

| iata | distance |
|---|---|
| PEW | 132.6 |
| FSD | 244.5 |
| LHE | 269.4 |
| CJL | 275.9 |
| GIL | 295.1 |
| KDU | 315.5 |
| KBL | 353.4 |
| MUX | 397.1 |
| UET | 668.4 |
| TAS | 911.9 |
| KHI | 1108.9 |
| MCT | 1799.9 |
| SHJ | 1908.0 |
| DXB | 1925.5 |
| AUH | 2035.8 |
| DOH | 2248.7 |
| RUH | 2702.0 |
| JED | 3553.0 |
| BKK | 3578.4 |
| PEK | 3921.2 |
| IST | 3944.0 |
| KUL | 4551.7 |
| LHR | 6053.3 |

## q05 - CQ3 Airports/runways per country (aggregation)  (21 rows)

| country | airports | runways |
|---|---|---|
| Pakistan | 10 | 12 |
| India | 5 | 8 |
| Saudi Arabia | 3 | 6 |
| United Arab Emirates | 3 | 5 |
| Afghanistan | 1 | 1 |
| Bahrain | 1 | 1 |
| Bangladesh | 1 | 1 |
| China | 1 | 2 |
| France | 1 | 2 |
| Germany | 1 | 2 |
| Iran | 1 | 2 |
| Kuwait | 1 | 2 |
| Malaysia | 1 | 2 |
| Oman | 1 | 1 |
| Qatar | 1 | 2 |
| Singapore | 1 | 2 |
| Sri Lanka | 1 | 1 |
| Thailand | 1 | 2 |
| Turkey | 1 | 2 |
| United Kingdom | 1 | 2 |
| Uzbekistan | 1 | 2 |

## q06 - CQ5 Blocked segments per cause (inference R2 + aggregation)  (5 rows)

| cause | label | blockedSegments |
|---|---|---|
| fdr:zone-RZ-ALPHA | Restricted Zone Alpha (fictional naval exercise area) | 15 |
| fdr:hazard-STORM-1 | Thunderstorm cell Punjab (fictional) | 13 |
| fdr:hazard-STORM-2 | Thunderstorm line northern Gulf (fictional) | 10 |
| fdr:zone-PZ-BRAVO | Prohibited Zone Bravo (fictional) | 7 |
| fdr:hazard-ICE-5 | Icing band Hindu Kush (fictional) | 3 |

## q07 - CQ6 Countries behind active hazards (multi-hop)  (14 rows)

| country | airportsAffected |
|---|---|
| Pakistan | 9 |
| India | 3 |
| United Arab Emirates | 3 |
| Saudi Arabia | 2 |
| Afghanistan | 1 |
| Bahrain | 1 |
| France | 1 |
| Germany | 1 |
| Iran | 1 |
| Kuwait | 1 |
| Qatar | 1 |
| Turkey | 1 |
| United Kingdom | 1 |
| Uzbekistan | 1 |

## q08 - CQ8 Reachable from ISB (property path)  (37 rows)

| iata |
|---|
| AMD |
| ATQ |
| AUH |
| BAH |
| BKK |
| BOM |
| CDG |
| CJL |
| CMB |
| DAC |
| DEL |
| DMM |
| DOH |
| DXB |
| FRA |
| FSD |
| GIL |
| IKA |
| IST |
| JAI |
| JED |
| KBL |
| KDU |
| KHI |
| KUL |
| KWI |
| LHE |
| LHR |
| MCT |
| MUX |
| PEK |
| PEW |
| RUH |
| SHJ |
| SIN |
| TAS |
| UET |

## q09 - CQ7 Two-leg feasible routes ISB->DXB for A380 (multi-hop + R4)  (30 rows)

| via | d1 | d2 | total |
|---|---|---|---|
| SHJ | 1908.0 | 17.5 | 1925.5 |
| UET | 668.4 | 1266.3 | 1934.7 |
| DXB | 1925.5 | 17.5 | 1943.0 |
| KBL | 353.4 | 1686.4 | 2039.8 |
| DXB | 1925.5 | 116.1 | 2041.6 |
| MUX | 397.1 | 1671.4 | 2068.5 |
| FSD | 244.5 | 1852.1 | 2096.6 |
| MCT | 1799.9 | 348.5 | 2148.4 |
| AUH | 2035.8 | 116.1 | 2151.9 |
| DXB | 1925.5 | 348.5 | 2274.0 |
| DXB | 1925.5 | 377.7 | 2303.2 |
| DXB | 1925.5 | 487.1 | 2412.6 |
| DXB | 1925.5 | 573.2 | 2498.7 |
| DOH | 2248.7 | 377.7 | 2626.4 |
| DXB | 1925.5 | 873.0 | 2798.5 |
| DXB | 1925.5 | 1199.9 | 3125.4 |
| DXB | 1925.5 | 1266.3 | 3191.8 |
| RUH | 2702.0 | 873.0 | 3575.0 |
| DXB | 1925.5 | 1671.4 | 3596.9 |
| DXB | 1925.5 | 1686.4 | 3611.9 |
| DXB | 1925.5 | 1699.0 | 3624.5 |
| DXB | 1925.5 | 1852.1 | 3777.6 |
| DXB | 1925.5 | 2183.2 | 4108.7 |
| DXB | 1925.5 | 3288.2 | 5213.7 |
| JED | 3553.0 | 1699.0 | 5252.0 |
| DXB | 1925.5 | 5549.2 | 7474.7 |
| DXB | 1925.5 | 5845.6 | 7771.1 |
| DXB | 1925.5 | 5846.6 | 7772.1 |
| PEK | 3921.2 | 5846.6 | 9767.8 |
| KUL | 4551.7 | 5549.2 | 10100.9 |

## q10 - CQ10 Diversion candidates scenario S1 (R5)  (18 rows)

| iata | name | distance |
|---|---|---|
| KHI | Jinnah International Airport | 318.8 |
| MCT | Muscat International Airport | 599.9 |
| UET | Quetta International Airport | 651.6 |
| SHJ | Sharjah International Airport | 854.4 |
| DXB | Dubai International Airport | 869.7 |
| AMD | Sardar Vallabhbhai Patel International Airport | 902.4 |
| MUX | Multan International Airport | 931.9 |
| AUH | Zayed International Airport | 946.2 |
| BOM | Chhatrapati Shivaji Maharaj International Airport | 1125.2 |
| FSD | Faisalabad International Airport | 1129.7 |
| KBL | Hamid Karzai International Airport | 1176.1 |
| DOH | Hamad International Airport | 1247.4 |
| LHE | Allama Iqbal International Airport | 1249.5 |
| ISB | Islamabad International Airport | 1280.7 |
| ATQ | Sri Guru Ram Dass Jee International Airport | 1292.2 |
| BAH | Bahrain International Airport | 1346.8 |
| DEL | Indira Gandhi International Airport | 1358.3 |
| DMM | King Fahd International Airport | 1431.2 |

## q11 - CQ11 ATR-only airports (R1 + NOT EXISTS)  (2 rows)

| iata | name | longestRunway |
|---|---|---|
| CJL | Chitral Airport | 1524 |
| GIL | Gilgit Airport | 1830 |

## q12 - CQ4 Suitable airports per aircraft (R0/R1 + aggregation)  (6 rows)

| aircraft | minRunway | suitableAirports |
|---|---|---|
| Boeing 777-300ER | 3050 | 32 |
| Airbus A380-800 | 3000 | 33 |
| Boeing 787-9 Dreamliner | 2800 | 33 |
| Boeing 737-800 | 2300 | 36 |
| Airbus A320-200 | 2100 | 36 |
| ATR 72-600 | 1333 | 38 |

## q13 - CQ13 ASK KHI->DXB feasible for B737-800  (1 rows)

| ask |
|---|
| false |

## q14 - CQ13 Why KHI->DXB is not feasible (explainability)  (1 rows)

| reasonType | reason |
|---|---|
| blocked by active zone/hazard | Restricted Zone Alpha (fictional naval exercise area) |

## q15 - CQ9 Airports 2 hops from ISB suitable for A380 (property path + inference)  (32 rows)

| iata | country |
|---|---|
| KBL | Afghanistan |
| BAH | Bahrain |
| DAC | Bangladesh |
| PEK | China |
| CDG | France |
| FRA | Germany |
| AMD | India |
| ATQ | India |
| BOM | India |
| DEL | India |
| IKA | Iran |
| KWI | Kuwait |
| KUL | Malaysia |
| MCT | Oman |
| FSD | Pakistan |
| KHI | Pakistan |
| LHE | Pakistan |
| MUX | Pakistan |
| UET | Pakistan |
| DOH | Qatar |
| DMM | Saudi Arabia |
| JED | Saudi Arabia |
| RUH | Saudi Arabia |
| SIN | Singapore |
| CMB | Sri Lanka |
| BKK | Thailand |
| IST | Turkey |
| AUH | United Arab Emirates |
| DXB | United Arab Emirates |
| SHJ | United Arab Emirates |
| LHR | United Kingdom |
| TAS | Uzbekistan |

## q16 - CQ15 Hub airports (R6)  (5 rows)

| iata | name | segments |
|---|---|---|
| DXB | Dubai International Airport | 34 |
| ISB | Islamabad International Airport | 23 |
| DOH | Hamad International Airport | 21 |
| KHI | Jinnah International Airport | 18 |
| DEL | Indira Gandhi International Airport | 14 |
