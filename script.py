import csv
from datetime import datetime, timedelta
import random
from mongoengine import connect
from app import Airport, Airline, Aircraft, Flight  # Your MongoEngine models

# Connect to MongoDB
connect(db="fastapi_jwt_auth", host="localhost", port=27017)

# Real-world data sources
REAL_AIRPORTS = [
    # Format: (IATA, Name, City, Country, Timezone)
    ("JFK", "John F. Kennedy International Airport", "New York", "United States", "America/New_York"),
    ("LAX", "Los Angeles International Airport", "Los Angeles", "United States", "America/Los_Angeles"),
    ("ORD", "O'Hare International Airport", "Chicago", "United States", "America/Chicago"),
    ("LHR", "Heathrow Airport", "London", "United Kingdom", "Europe/London"),
    ("CDG", "Charles de Gaulle Airport", "Paris", "France", "Europe/Paris"),
    ("DXB", "Dubai International Airport", "Dubai", "United Arab Emirates", "Asia/Dubai"),
    ("HND", "Haneda Airport", "Tokyo", "Japan", "Asia/Tokyo"),
    ("SYD", "Sydney Airport", "Sydney", "Australia", "Australia/Sydney"),
    ("PEK", "Beijing Capital International Airport", "Beijing", "China", "Asia/Shanghai"),
    ("DEL", "Indira Gandhi International Airport", "Delhi", "India", "Asia/Kolkata")
]

REAL_AIRLINES = [
    # Format: (IATA, Name, Logo URL)
    ("AA", "American Airlines", "https://logo.clearbit.com/aa.com"),
    ("DL", "Delta Air Lines", "https://logo.clearbit.com/delta.com"),
    ("UA", "United Airlines", "https://logo.clearbit.com/united.com"),
    ("BA", "British Airways", "https://logo.clearbit.com/britishairways.com"),
    ("AF", "Air France", "https://logo.clearbit.com/airfrance.com"),
    ("EK", "Emirates", "https://logo.clearbit.com/emirates.com"),
    ("SQ", "Singapore Airlines", "https://logo.clearbit.com/singaporeair.com"),
    ("LH", "Lufthansa", "https://logo.clearbit.com/lufthansa.com"),
    ("QF", "Qantas", "https://logo.clearbit.com/qantas.com"),
    ("CA", "Air China", "https://logo.clearbit.com/airchina.com.cn")
]

REAL_AIRCRAFTS = [
    # Format: (Model, ICAO, Manufacturer, Capacity)
    ("Boeing 737-800", "B738", "Boeing", 162),
    ("Boeing 747-400", "B744", "Boeing", 416),
    ("Boeing 777-300ER", "B77W", "Boeing", 396),
    ("Boeing 787-9 Dreamliner", "B789", "Boeing", 290),
    ("Airbus A320-200", "A320", "Airbus", 150),
    ("Airbus A330-300", "A333", "Airbus", 277),
    ("Airbus A350-900", "A359", "Airbus", 325),
    ("Airbus A380-800", "A388", "Airbus", 525),
    ("Embraer E190", "E190", "Embraer", 100),
    ("Bombardier CRJ900", "CRJ9", "Bombardier", 90)
]

def generate_real_airports():
    """Insert real-world airport data"""
    airports = []
    for code, name, city, country, tz in REAL_AIRPORTS:
        airports.append(Airport(
            code=code,
            name=name,
            city=city,
            country=country,
            timezone=tz
        ))
    Airport.objects.insert(airports, load_bulk=False)
    print(f"Inserted {len(airports)} real airports")

def generate_real_airlines():
    """Insert real-world airline data"""
    airlines = []
    for code, name, logo in REAL_AIRLINES:
        airlines.append(Airline(
            code=code,
            name=name,
            logo_url=logo
        ))
    Airline.objects.insert(airlines, load_bulk=False)
    print(f"Inserted {len(airlines)} real airlines")

def generate_real_aircrafts():
    """Insert real-world aircraft data"""
    aircrafts = []
    for model, icao, manufacturer, capacity in REAL_AIRCRAFTS:
        aircrafts.append(Aircraft(
            model=model,
            code=icao,
            manufacturer=manufacturer,
            capacity=capacity
        ))
    Aircraft.objects.insert(aircrafts, load_bulk=False)
    print(f"Inserted {len(aircrafts)} real aircrafts")

def generate_real_flights(count=300):
    """Generate realistic flight schedules"""
    airports = list(Airport.objects.all())
    airlines = list(Airline.objects.all())
    aircrafts = list(Aircraft.objects.all())
    
    # Common flight routes between major hubs
    POPULAR_ROUTES = [
        ("JFK", "LAX"), ("LAX", "JFK"),
        ("LHR", "JFK"), ("JFK", "LHR"),
        ("DXB", "LHR"), ("LHR", "DXB"),
        ("SYD", "LAX"), ("LAX", "SYD"),
        ("HND", "PEK"), ("PEK", "HND")
    ]
    
    flights = []
    route_cache = {}
    
    for _ in range(count):
        # 70% chance to use popular route, 30% random
        if random.random() < 0.7 and POPULAR_ROUTES:
            dep_code, arr_code = random.choice(POPULAR_ROUTES)
            departure = next(a for a in airports if a.code == dep_code)
            arrival = next(a for a in airports if a.code == arr_code)
        else:
            departure, arrival = random.sample(airports, 2)
        
        # Ensure we don't create duplicate flights
        route_key = f"{departure.code}-{arrival.code}"
        if route_key in route_cache:
            route_cache[route_key] += 1
            flight_num = f"{route_cache[route_key]:03d}"
        else:
            route_cache[route_key] = 1
            flight_num = "001"
        
        airline = random.choice(airlines)
        flight_number = f"{airline.code}{flight_num}"
        
        # Generate realistic departure time (next 60 days)
        departure_time = datetime.now() + timedelta(days=random.randint(1, 60))
        
        # Set departure time to common flight hours (6am-10pm)
        departure_time = departure_time.replace(
            hour=random.choice([6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]),
            minute=random.choice([0,5,10,15,20,25,30,35,40,45,50,55])
        )
        
        # Calculate flight duration based on distance
        base_duration = random.randint(60, 720)  # 1-12 hours
        duration = base_duration + random.randint(-30, 30)  # Add some variance
        arrival_time = departure_time + timedelta(minutes=duration)
        
        # Calculate realistic pricing
        base_price = calculate_realistic_price(departure.code, arrival.code)
        
        flights.append(Flight(
            flight_number=flight_number,
            airline=airline,
            aircraft=random.choice(aircrafts),
            departure_airport=departure,
            arrival_airport=arrival,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            base_price=base_price,
            available_seats=random.randint(10, int(aircrafts[0].capacity * 0.9)),  # 10-90% capacity
            status="SCHEDULED"
        ))
    
    Flight.objects.insert(flights, load_bulk=False)
    print(f"Generated {len(flights)} realistic flights")

def calculate_realistic_price(dep_code, arr_code):
    """Calculate realistic flight prices based on route distance"""
    # Base prices for well-known routes (in USD)
    KNOWN_ROUTES = {
        ("JFK", "LAX"): 300,
        ("LAX", "JFK"): 300,
        ("LHR", "JFK"): 600,
        ("JFK", "LHR"): 600,
        ("DXB", "LHR"): 500,
        ("LHR", "DXB"): 500,
        ("SYD", "LAX"): 800,
        ("LAX", "SYD"): 800,
        ("HND", "PEK"): 400,
        ("PEK", "HND"): 400
    }
    
    if (dep_code, arr_code) in KNOWN_ROUTES:
        base_price = KNOWN_ROUTES[(dep_code, arr_code)]
    else:
        # Random base price for other routes
        base_price = random.randint(100, 1000)
    
    # Add random variation
    return base_price + random.randint(-50, 100)

def generate_all_data():
    """Generate all realistic data"""
    print("Deleting old data...")
    Airport.objects.delete()
    Airline.objects.delete()
    Aircraft.objects.delete()
    Flight.objects.delete()
    
    print("Generating new realistic data...")
    generate_real_airports()
    generate_real_airlines()
    generate_real_aircrafts()
    generate_real_flights(300)  # Generate 300 flights
    
    print("Realistic data generation complete!")

if __name__ == "__main__":
    generate_all_data()