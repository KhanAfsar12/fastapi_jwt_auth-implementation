import csv
from datetime import datetime, timedelta
from decimal import Decimal
import random
from faker import Faker
from mongoengine import connect
from app import Airport, Airline, Aircraft, Flight  # Your MongoEngine models

# Connect to MongoDB
connect(db="fastapi_jwt_auth", host="localhost", port=27017)
fake = Faker()

def generate_airports(count=50):
    """Generate airport records"""
    airports = []
    for _ in range(count):
        code = fake.unique.lexify(text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        city = fake.city()
        airport = Airport(
            code=code,
            name=f"{city} International Airport",
            city=city,
            country=fake.country(),
            timezone=fake.timezone(),
            latitude=fake.latitude(),
            longitude=fake.longitude()
        )
        airport.save()
        airports.append(airport)
    return airports

def generate_airlines(count=20):
    """Generate airline records with real logos"""
    airlines_data = [
        {"code": "AA", "name": "American Airlines", "logo": "https://logo.clearbit.com/aa.com"},
        {"code": "DL", "name": "Delta Air Lines", "logo": "https://logo.clearbit.com/delta.com"},
        {"code": "UA", "name": "United Airlines", "logo": "https://logo.clearbit.com/united.com"},
        {"code": "LH", "name": "Lufthansa", "logo": "https://logo.clearbit.com/lufthansa.com"},
        {"code": "BA", "name": "British Airways", "logo": "https://logo.clearbit.com/britishairways.com"},
        {"code": "AF", "name": "Air France", "logo": "https://logo.clearbit.com/airfrance.com"},
        {"code": "EK", "name": "Emirates", "logo": "https://logo.clearbit.com/emirates.com"},
        {"code": "SQ", "name": "Singapore Airlines", "logo": "https://logo.clearbit.com/singaporeair.com"},
        {"code": "QF", "name": "Qantas", "logo": "https://logo.clearbit.com/qantas.com.au"},
        {"code": "JL", "name": "Japan Airlines", "logo": "https://logo.clearbit.com/jal.co.jp"},
        {"code": "CX", "name": "Cathay Pacific", "logo": "https://logo.clearbit.com/cathaypacific.com"},
        {"code": "EY", "name": "Etihad Airways", "logo": "https://logo.clearbit.com/etihad.com"},
        {"code": "QR", "name": "Qatar Airways", "logo": "https://logo.clearbit.com/qatarairways.com"},
        {"code": "TK", "name": "Turkish Airlines", "logo": "https://logo.clearbit.com/turkishairlines.com"},
        {"code": "KL", "name": "KLM", "logo": "https://logo.clearbit.com/klm.com"},
        {"code": "VS", "name": "Virgin Atlantic", "logo": "https://logo.clearbit.com/virginatlantic.com"},
        {"code": "NH", "name": "ANA", "logo": "https://logo.clearbit.com/ana.co.jp"},
        {"code": "AC", "name": "Air Canada", "logo": "https://logo.clearbit.com/aircanada.com"},
        {"code": "LY", "name": "El Al", "logo": "https://logo.clearbit.com/elal.com"},
        {"code": "OZ", "name": "Asiana Airlines", "logo": "https://logo.clearbit.com/flyasiana.com"}
    ]
    
    airlines = []
    for data in airlines_data[:count]:
        airline = Airline(
            code=data["code"],
            name=data["name"],
            logo_url=data["logo"],
            latitude=fake.latitude(),
            longitude=fake.longitude()
        )
        airline.save()
        airlines.append(airline)
    return airlines

def generate_aircraft(count=30):
    """Generate aircraft records"""
    aircrafts = []
    models = [
        ("Boeing 737-800", "B738", "Boeing", 162),
        ("Airbus A320", "A320", "Airbus", 150),
        ("Boeing 787-9", "B789", "Boeing", 290),
        ("Airbus A350", "A350", "Airbus", 315),
        ("Boeing 777-300ER", "B77W", "Boeing", 396),
        ("Embraer E190", "E190", "Embraer", 100),
        ("Bombardier CRJ900", "CRJ9", "Bombardier", 90),
        ("Airbus A380", "A388", "Airbus", 555),
        ("Boeing 747-8", "B748", "Boeing", 410),
        ("Airbus A321neo", "A21N", "Airbus", 180),
        ("Boeing 737 MAX 8", "B38M", "Boeing", 178),
        ("Airbus A220-300", "A223", "Airbus", 130),
        ("Boeing 767-300", "B763", "Boeing", 218),
        ("Airbus A330-300", "A333", "Airbus", 277),
        ("Boeing 757-200", "B752", "Boeing", 200),
        ("Embraer E175", "E175", "Embraer", 76),
        ("Bombardier Q400", "DH4", "Bombardier", 78),
        ("ATR 72-600", "AT76", "ATR", 72),
        ("Boeing 737-700", "B737", "Boeing", 126),
        ("Airbus A319", "A319", "Airbus", 124)
    ]
    
    for i in range(count):
        model_data = models[i % len(models)]
        aircraft = Aircraft(
            model=model_data[0],
            code=f"{model_data[1]}{fake.unique.numerify(text='##')}",
            manufacturer=model_data[2],
            capacity=model_data[3]
        )
        aircraft.save()
        aircrafts.append(aircraft)
    return aircrafts

def generate_flights(count=500, airports=None, airlines=None, aircrafts=None):
    """Generate flight records"""
    status_choices = ['SCHEDULED', 'DELAYED', 'DEPARTED', 'ARRIVED', 'CANCELLED']
    
    for _ in range(count):
        airline = random.choice(airlines)
        aircraft = random.choice(aircrafts)
        
        # Ensure departure and arrival airports are different
        departure, arrival = random.sample(airports, 2)
        
        # Generate random departure time in the next 30 days
        departure_time = fake.date_time_between(start_date='now', end_date='+30d')
        
        # Generate duration between 30 minutes and 14 hours
        duration = random.randint(30, 14 * 60)
        arrival_time = departure_time + timedelta(minutes=duration)
        
        # Base price between $50 and $1500
        base_price = Decimal(random.randint(5000, 150000) / 100)
        
        flight = Flight(
            flight_number=f"{airline.code}{random.randint(100, 9999)}",
            airline=airline,
            aircraft=aircraft,
            departure_airport=departure,
            arrival_airport=arrival,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            base_price=base_price,
            available_seats=random.randint(0, aircraft.capacity),
            status=random.choice(status_choices)
        )
        flight.save()

def main():
    print("Generating data with real airline logos...")
    
    # Clear existing data
    Airport.drop_collection()
    Airline.drop_collection()
    Aircraft.drop_collection()
    Flight.drop_collection()
    
    # Generate new data
    airports = generate_airports(50)
    airlines = generate_airlines(20)
    aircrafts = generate_aircraft(30)
    generate_flights(500, airports, airlines, aircrafts)
    
    print("Data generation complete!")
    print(f"Created: {len(airports)} airports, {len(airlines)} airlines, {len(aircrafts)} aircraft, 500 flights")
    print("\nSample airlines with real logos:")
    for airline in Airline.objects[:5]:
        print(f"{airline.code} - {airline.name} - Logo: {airline.logo_url}")

if __name__ == "__main__":
    main()