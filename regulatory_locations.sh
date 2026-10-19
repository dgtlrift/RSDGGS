#!/usr/bin/env bash

######------------------------------
###### 🌐 ITU Region 1: Europe, Africa, Middle East, and Northern Asia
######------------------------------

## 1. [United Kingdom](https://www.google.com/search?kgmid=/m/07ssc) (Ofcom / CEPT) 
#* Busiest Airport: [London Heathrow Airport (LHR)](https://www.google.com/search?kgmid=/m/03jn4) - 51.4700, -0.4543
#* Sub-GHz ISM Band: 863–870 MHz (Short Range Devices).
#* Regulatory Carve-outs: The entire 902–928 MHz spectrum is completely
#	prohibited for commercial ISM use due to intensive allocations for GSM-R
#	(railway signaling) and defense communications. 
cargo r -- encode 51.4700 -0.4543
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 51.4700 -0.4543 --truncate ${truncate}
done

### 2. [Ireland](https://www.google.com/search?kgmid=/m/03rt9) (ComReg)
#* Busiest Airport: [Dublin Airport (DUB)](https://www.google.com/search?kgmid=/m/01qykt) - 53.4273, -6.2436
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Standard CEPT ERC Rec 70-03 applies, but ComReg
#	enforces strict channel boundary policing to protect localized naval, maritime,
#	and defense telemetry services near coastal sectors.
cargo r -- encode 53.4273 -6.2436
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 53.4273 -6.2436 --truncate ${truncate}
done

### 3. [Netherlands](https://www.google.com/search?kgmid=/m/059j2) (Rijksinspectie Digitale Infrastructuur - RDI)
#* Busiest Airport: [Amsterdam Airport Schiphol (AMS)](https://www.google.com/search?kgmid=/m/073j2) - 52.3091, 4.7634
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Due to hyper-dense spectrum saturation from maritime
#	shipping lanes and international aviation networks, the RDI enforces strict
#	duty-cycle limits (down to 0.1% or 1%) to prevent signal desensitization.  
cargo r -- encode 52.3091 4.7634
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 52.3091 4.7634 --truncate ${truncate}
done

### 4. [Switzerland](https://www.google.com/search?kgmid=/m/06mzp) (OFCOM / BAKOM)
#* Busiest Airport: [Zurich Airport (ZRH)](https://www.google.com/search?kgmid=/m/01lk5k) - 47.4582, 8.5555
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Though harmonized with ETSI standards,
#	[Switzerland](https://www.google.com/search?kgmid=/m/06mzp) maintains unique
#	local power limitations (EIRP) and rigid channel boundaries to prevent
#	interference with alpine military radar and state emergency networks.  
cargo r -- encode 47.4582 8.5555
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 47.4582 8.5555 --truncate ${truncate}
done

### 5. [Hungary](https://www.google.com/search?kgmid=/m/03gj2) (NMHH)
#* Busiest Airport: Budapest Ferenc Liszt International Airport (BUD) - 47.4330, 19.2616
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Strictly adheres to the European framework, meaning
#	any deployment of North American 915 MHz protocols will cause a severe
#	regulatory violation for overlapping with active, licensed central European
#	cellular networks.
cargo r -- encode 47.4330 19.2616
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 47.4330 19.2616 --truncate ${truncate}
done

### 6. [Iceland](https://www.google.com/search?kgmid=/m/03rj0) (Fjarskiptastofa - ECO)  
#* Busiest Airport: Keflavík International Airport (KEF) - 63.9850, -22.6056
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Heavily harmonized under CEPT/ETSI regulations, but
#	[Fjarskiptastofa](https://www.google.com/search?kgmid=/g/11g0llbrxn) enforces
#	strict sub-GHz power restrictions around high-latitude coastal tracking arrays
#	and maritime navigation systems to preserve long-range search and rescue bands.  
cargo r -- encode 63.9850 -22.6056
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 63.9850 -22.6056 --truncate ${truncate}
done

### 7. [United Arab Emirates (TDRA)](https://www.google.com/search?kgmid=/g/1yg6c_hdm)
#* Busiest Airport: Dubai International Airport (DXB) - 25.2528, 55.3644
#* Sub-GHz ISM Band: 863–870 MHz.
#* Regulatory Carve-outs: Enforces rigid Effective Radiated Power (ERP)
#	restrictions across coastal areas to shield saturation-sensitive border radar
#	grids and military communications.  
cargo r -- encode 25.2528 55.3644
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 25.2528 55.3644 --truncate ${truncate}
done

### 8. [Russian Federation](https://www.google.com/search?kgmid=/m/06bnz) (GRFC / Roskomnadzor)
#* Busiest Airport: Sheremetyevo International Airport (SVO) - 55.9726, 37.4146
#* Sub-GHz ISM Band: Restricted to 868.7–869.2 MHz.
#* Regulatory Carve-outs: The 864.0–865.0 MHz block features massive localized
#	restrictions. The American 902–928 MHz band is strictly blocked and
#	aggressively prohibited for commercial use because it is reserved for state
#	military telemetry and tracking systems.
cargo r -- encode 55.9726 37.4146
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 55.9726 37.4146 --truncate ${truncate}
done

### 9. Egypt (National Telecom Regulatory Authority - NTRA)  
#* Busiest Airport: Cairo International Airport (CAI) - 30.1219, 31.4056
#* Sub-GHz ISM Band: Restricted to 433.05–434.79 MHz.
#* Regulatory Carve-outs: The standard Western 868 MHz and 915 MHz bands are
#	strictly illegal for commercial, unlicensed ISM applications. NTRA tightly
#	reserves those spaces for state security infrastructure, specialized government
#	telemetry, and military tracking matrices across North Africa.  
cargo r -- encode 30.1219 31.4056
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 30.1219 31.4056 --truncate ${truncate}
done

### 10. Liberia (Liberia Telecommunications Authority - LTA)
#* Busiest Airport: Roberts International Airport (ROB) - 6.2339, -10.3622
#* Sub-GHz ISM Band: Aligns with ITU Region 1 (863–870 MHz).
#* Regulatory Carve-outs: The LTA polices the sub-GHz spectrum to secure
#	primary telecommunications and state security vectors. Due to historical
#	maritime monitoring deployments along the West African coast, unlicensed
#	broad-spectrum frequency hopping must maintain specific channel spacing to
#	protect active defense radio relays.
cargo r -- encode  6.2339 -10.3622
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode  6.2339 -10.3622 --truncate ${truncate}
done

### 11. [South Africa](https://www.google.com/search?kgmid=/m/0hzlz) (ICASA)
#* Busiest Airport: O.R. Tambo International Airport (JNB) - -26.1367, 28.2460
#* Sub-GHz ISM Band: 915–921 MHz (for specific LPWAN/RFID applications).
#* Regulatory Carve-outs: The upper portion of the band (921–928 MHz) is
#	strictly carved out and illegal for unlicensed use to guard critical state-run
#	railway and government telemetry systems.
cargo r -- encode  -26.1367 28.2460
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode  -26.1367 28.2460 --truncate ${truncate}
done

######------------------------------
###### 🌐 ITU Region 2: The Americas and Greenland
######------------------------------

### 12. United States (FCC)
#* Busiest Airport: Hartsfield–Jackson Atlanta International Airport (ATL) - 33.6407, -84.4277
#* Sub-GHz ISM Band: 902–928 MHz (CFR Title 47 Part 15).
#* Regulatory Carve-outs: Unlicensed commercial operations must legally accept
#	interference from primary federal radiolocation systems (military radar).
#	Localized exclusions on specific frequency-hopping patterns exist near certain
#	coastal military installations.  
cargo r -- encode 33.6407 -84.4277
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 33.6407 -84.4277 --truncate ${truncate}
done

### 13. Canada (Innovation, Science and Economic Development - ISED)
#* Busiest Airport: Toronto Pearson International Airport (YYZ) - 43.6771, -79.6335
#* Sub-GHz ISM Band: 902–928 MHz (RSS-247).
#* Regulatory Carve-outs: Mirrors FCC rules but implements distinct receiver
#	sensitivity laws and localized power restrictions near northern/arctic defense
#	facilities to prevent interference with cross-border monitoring arrays.  
cargo r -- encode 43.6771 -79.6335
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 43.6771 -79.6335 --truncate ${truncate}
done

### 14. Mexico (Instituto Federal de Telecomunicaciones - IFT)  
#* Busiest Airport: Mexico City International Airport Benito Juárez (MEX) - 19.4363, -99.0721
#* Sub-GHz ISM Band: 902–928 MHz (regulated under NOM-208 / IFT-008).
#* Regulatory Carve-outs: While it physically overlaps with the standard US
#	band, Mexico mandates strict compliance under the National Frequency Allocation
#	Table (NTFA Note 128). ISM devices must protect low-speed fixed and mobile
#	weather tracking devices and avoid overlapping with multi-access loops used for
#	rural telephony networks.  
cargo r -- encode 19.4363 -99.0721
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 19.4363 -99.0721 --truncate ${truncate}
done

### 15. Brazil (ANATEL)
#* Busiest Airport: São Paulo/Guarulhos International Airport (GRU) - -23.4356, -46.4731
#* Sub-GHz ISM Band: 902–907.5 MHz and 915–928 MHz.
#* Regulatory Carve-outs: The specific internal gap of 907.5–915 MHz is
#	strictly prohibited for commercial ISM use. This narrow block is legally carved
#	out and reserved exclusively for licensed mobile/cellular provider uplinks.  
cargo r -- encode -23.4356 -46.4731
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode -23.4356 -46.4731 --truncate ${truncate}
done

### 16. The Bahamas (Utilities Regulation and Competition Authority - URCA)
#* Busiest Airport: Lynden Pindling International Airport (NAS) - 25.0390, -77.4662
#* Sub-GHz ISM Band: 902–928 MHz.
#* Regulatory Carve-outs: Employs an FCC-aligned band framework, but URCA
#	implements strict peak-power and harmonic emission thresholds to safeguard
#	high-density maritime cruise ship communication frameworks and trans-Caribbean
#	aviation telemetry.  
cargo r -- encode 25.0390 -77.4662
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 25.0390 -77.4662 --truncate ${truncate}
done

### 17. British Virgin Islands (Telecommunications Regulatory Commission - TRC)
#* Busiest Airport: Terrance B. Lettsome International Airport (EIS) - 18.4485, -64.5430
#* Sub-GHz ISM Band: 902–928 MHz.
#* Regulatory Carve-outs: Operates as a distinct territorial jurisdiction.
#	While leveraging the 915 MHz spectrum, the TRC mandates tight emission masks
#	and reduced output power on channels adjacent to international shipping radar
#	links and search-and-rescue frequencies crossing overlapping territorial
#	waters.  
cargo r -- encode 18.4485 -64.5430
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 18.4485 -64.5430 --truncate ${truncate}
done

######------------------------------
###### 🌐 ITU Region 3: Asia-Pacific
######------------------------------

### 18. People's Republic of China (MIIT)
#* Busiest Airport: Shanghai Pudong International Airport (PVG) - 31.1443, 121.8083
#* Sub-GHz ISM Band: 779–787 MHz (Short Range Devices) and 920–925 MHz (RFID/LPWAN).
#* Regulatory Carve-outs: Completely rejects Western allocations. Using any
#	frequencies between 902–920 MHz or 925–928 MHz is strictly prohibited due to
#	active state, military, and governmental utility allocations.
cargo r -- encode 31.1443 121.8083
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 31.1443 121.8083 --truncate ${truncate}
done

### 19. Hong Kong SAR (OFCA City-State Jurisdiction)
#* Busiest Airport: Hong Kong International Airport (HKG) - 22.3080, 113.9185
#* Sub-GHz ISM Band: 920–925 MHz (HKCA 1049 parameters).
#* Regulatory Carve-outs: Operates independently of mainland China's broader
#	MIIT tracking system, but enforces highly precise channel spacing and tight
#	emission masks near the border to prevent cross-boundary bleed-over into
#	mainland cellular grids.  
cargo r -- encode 22.3080 113.9185
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 22.3080 113.9185 --truncate ${truncate}
done

### 20. India (Wireless Planning & Coordination - WPC)
#* Busiest Airport: Indira Gandhi International Airport (DEL) - 28.5562, 77.1000
#* Sub-GHz ISM Band: 865–867 MHz (de-licensed block).
#* Regulatory Carve-outs: Highly restrictive. Hardware must completely notch
#	out and block the standard European 868–870 MHz and American 915 MHz bands,
#	which are heavily utilized by domestic telecom carriers and defense networks.
cargo r -- encode 28.5562 77.1000
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 28.5562 77.1000 --truncate ${truncate}
done

### 21. Japan (MIC)
#* Busiest Airport: Tokyo Haneda Airport (HND) - 35.5494, 139.7798
#* Sub-GHz ISM Band: 915–928 MHz.
#* Regulatory Carve-outs: Sub-channels in the 926–928 MHz range strictly
#	require active Listen-Before-Talk (LBT) contention mitigation. This feature is
#	legally mandated to protect local smart grid utility infrastructure and
#	telemetry grids from aggregate noise.  
cargo r -- encode 35.5494 139.7798
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode 35.5494 139.7798 --truncate ${truncate}
done

### 22. Australia (ACMA)
#* Busiest Airport: Sydney Kingsford Smith Airport (SYD) - -33.9461, 151.1772
#* Sub-GHz ISM Band: 915–928 MHz.
#* Regulatory Carve-outs: Implements highly unique channel spacing rules
#	compared to the US FCC layout. This configuration ensures that unlicensed
#	equipment stays clear of the lower 902–915 MHz block, which is used by
#	Australian defense tracking systems and licensed fixed communication links.
cargo r -- encode -33.9461 151.1772
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode -33.9461 151.1772 --truncate ${truncate}
done

### 23. New Zealand (Radio Spectrum Management - RSM)
#* Busiest Airport: Auckland Airport (AKL) - -37.0081, 174.7917
#* Sub-GHz ISM Band: 915–928 MHz.
#* Regulatory Carve-outs: Operating under the General User Radio Licence for
#	Short Range Devices, specific sub-bands near 921–923 MHz enforce mandatory
#	power reductions or active LBT to safeguard localized utility telemetry grids.
cargo r -- encode -37.0081 174.7917
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode -37.0081 174.7917 --truncate ${truncate}
done

######------------------------------
###### ❄️ Esoteric Framework: Antarctica
######------------------------------

### 24. McMurdo Station / Ross Dependency
#* Busiest Airfield: Phoenix Airfield (NZFX) - -77.9564, 166.7667
#* Regulatory Framework: Antarctic Treaty System (1959) via COMNAP / SCAR.
#* Regulatory Carve-outs: There is zero sovereign domestic jurisdiction. All
#	spectrum assignments must be logged under the Electronic Information Exchange
#	System (EIES). To protect nearby high-sensitivity cosmic ray detectors, radio
#	telescopes, and deep-space telemetry equipment, uncoordinated or unshielded
#	sub-GHz ISM transmissions (such as continuous, standard frequency-hopping at
#	868 or 915 MHz) are strictly prohibited across the continent to maintain a
#	pristine radio astronomy sanctuary.
cargo r -- encode  -77.9564 166.7667
for truncate in 7 6 5 4 3 2 1 ; do
cargo r -- encode  -77.9564 166.7667 --truncate ${truncate}
done

# Runs through a set of RSDGGS generated above to decode locations - not that
#	truncated values above will be assumed to be traversable at full resolution.
for rsdggs in 0x0121938c2682b918 0x0121938c00000000 0x01211d595159cbc3 0x01211d5900000000 0x0121ad06699c4d17 0x0121ad0600000000 0x012fe4ff7c309ea1 0x012fe4ff00000000 0x012d043814ca90cf 0x012d043800000000 0x0100bc091fcf0708 0x0100bc0900000000 0x034c172ce63a3b5b 0x034c172c00000000 0x0134be1dd7170d73 0x0134be1d00000000 0x050893fabed49c2a 0x050893fa00000000 0x041c3a3e7f07a67e 0x041c3a3e00000000 0x0535fbccf8d19eff 0x0535fbcc00000000 0x0211cdcbf192bb2c 0x0211cdcb00000000 0x020841d2ec3af86d 0x020841d200000000 0x02232f0b0934fb3a 0x02232f0b00000000 0x042a3755f0c37fff 0x042a375500000000 0x021fc38d83e7f48f 0x021fc38d00000000 0x044cdfd94086f28f 0x044cdfd900000000 0x032505ba867e910f 0x032505ba00000000 0x032606891af3312a 0x0326068900000000 0x03439e66ed9da37a 0x03439e6600000000 0x0627af65bf80b7ae 0x0627af6500000000 0x0a3689f8ec1cd7f3 0x0a3689f800000000 0x004b50ad29c68b83 0x004b50ad00000000 0x0023219607882da2 0x0023219600000000 ; do
   cargo run -- decode ${rsdggs}
   for truncate in 7 5 3 1 ; do
      cargo run -- decode ${rsdggs} --truncate ${truncate}
   done
done

# Run through some celestial bodies as a test
for rsdggs in 0x1121938c2682b918 0x141c3a3e7f07a67e 0x232505ba867e910f 0x2627af65bf80b7ae ; do
   cargo run -- decode ${rsdggs}
   for truncate in 7 5 3 1 ; do
      cargo run -- decode ${rsdggs} --truncate ${truncate}
   done
done


