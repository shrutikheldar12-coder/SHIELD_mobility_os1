# data/maharashtra_data.py

DAMS = [
    {"name": "Koyna Dam", "river": "Koyna", "district": "Satara", "lat": 17.40, "lon": 73.75, "capacity": "105 TMC", "status": "Warning"},
    {"name": "Ujani Dam", "river": "Bhima", "district": "Solapur", "lat": 18.13, "lon": 75.13, "capacity": "117 TMC", "status": "Critical"},
    {"name": "Jayakwadi Dam", "river": "Godavari", "district": "Aurangabad", "lat": 19.48, "lon": 75.37, "capacity": "102 TMC", "status": "Safe"},
    {"name": "Bhatsa Dam", "river": "Bhatsa", "district": "Thane", "lat": 19.52, "lon": 73.22, "capacity": "15 TMC", "status": "Safe"},
    {"name": "Radhanagari Dam", "river": "Panchganga", "district": "Kolhapur", "lat": 16.40, "lon": 73.99, "capacity": "8 TMC", "status": "Safe"}
]

RIVERS = {
    "Godavari": {"coords": [[19.93, 73.53], [19.5, 75.0], [19.1, 77.0], [18.8, 79.5]], "basin": "Godavari Basin", "length": "1,465 km"},
    "Krishna": {"coords": [[17.92, 73.65], [17.5, 75.0], [16.9, 76.5], [16.5, 78.0]], "basin": "Krishna Basin", "length": "1,400 km"},
    "Bhima": {"coords": [[19.0, 73.8], [18.5, 75.0], [17.9, 76.5]], "basin": "Krishna Basin", "length": "861 km"},
    "Tapi": {"coords": [[21.0, 73.8], [21.0, 75.0], [21.1, 77.0]], "basin": "Tapi Basin", "length": "724 km"},
    "Kundalika": {"coords": [[18.4, 73.1], [18.3, 73.3], [18.2, 73.5]], "basin": "West Flowing", "length": "75 km"}
}

BRIDGES = [
    {"name": "Solapur Bridge", "loc": [17.66, 75.90], "river": "Bhima", "status": "Critical", "span": "120 m"},
    {"name": "Holkar Bridge", "loc": [19.99, 73.78], "river": "Godavari", "status": "Safe", "span": "85 m"},
    {"name": "Paithan Bridge", "loc": [19.48, 75.38], "river": "Godavari", "status": "Safe", "span": "150 m"},
    {"name": "Ulhas Bridge", "loc": [19.24, 73.12], "river": "Ulhas", "status": "Warning", "span": "95 m"},
    {"name": "Kundalika Bridge", "loc": [18.43, 73.12], "river": "Kundalika", "status": "Critical", "span": "60 m"}
]