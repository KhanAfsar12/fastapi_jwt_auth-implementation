from datetime import date, datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_jwt_auth import AuthJWT
from mongoengine import connect, Document, EmailField, StringField, ReferenceField, BooleanField, NotUniqueError, DateTimeField, IntField, DecimalField, EmbeddedDocument, EmbeddedDocumentField, ListField, FloatField
from pydantic import BaseModel, EmailStr, Field, validator
import uvicorn
import os

app = FastAPI()

# DB Connection
connect(db="fastapi_jwt_auth", host="localhost", port=27017)

# Template Configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=template_path)

# Middleware
app.add_middleware(
    CORSMiddleware, 
    allow_origins=['*'],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*']
    )

# Models
class User(Document):
    username = StringField(max_length=50)
    email = EmailField(required=True, unique=True)
    password  = StringField(required=True)
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    meta = {
        'indexes': ['email', 'username']
    }
    def __str__(self):
        return f"{self.username} Account Updated"
    
class Profile(Document):
    user = ReferenceField(User, required=True, unique=True)
    bio = StringField(default="Hello! I'm new here..")
    link = StringField(default='https://youtube.com')

    def __str__(self):
        return f"{self.user.username}'s Profile is {'Active' if self.user.is_active else "Deactivate"}"
    

class Passenger(EmbeddedDocument):
    id = StringField(primary_key=True, default=lambda: str(ObjectId()))
    first_name = StringField(required=True, max_length=50)
    last_name = StringField(required=True, max_length=50)
    passport_number = StringField(max_length=20)
    nationality = StringField(max_length=50)
    date_of_birth = DateTimeField()
    passenger_type = StringField(choices=('ADULT', 'CHILD', 'INFANT'), default='ADULT')


class Airport(Document):
    code = StringField(required=True, unique=True, max_length=3)  # IATA code
    name = StringField(required=True)
    city = StringField(required=True)
    country = StringField(required=True)
    timezone = StringField()
    latitude = FloatField()
    longitude = FloatField()
    meta = {
        'collection': 'airports'
    }

class Airline(Document):
    code = StringField(required=True, unique=True, max_length=2)  # IATA code
    name = StringField(required=True)
    logo_url = StringField()
    latitude = FloatField()
    longitude = FloatField()
    meta = {
        'collection': 'airlines'
    }

class Aircraft(Document):
    model = StringField(required=True)
    code = StringField(required=True, unique=True)  # ICAO code
    manufacturer = StringField()
    capacity = IntField(required=True)
    meta = {
        'collection': 'aircrafts'
    }

class Flight(Document):
    flight_number = StringField(required=True)
    airline = ReferenceField(Airline, required=True)
    aircraft = ReferenceField(Aircraft, required=True)
    departure_airport = ReferenceField(Airport, required=True)
    arrival_airport = ReferenceField(Airport, required=True)
    departure_time = DateTimeField(required=True)
    arrival_time = DateTimeField(required=True)
    duration = IntField()  # in minutes
    base_price = DecimalField(required=True, precision=2)
    available_seats = IntField(required=True)
    status = StringField(choices=(
        'SCHEDULED', 'DELAYED', 'DEPARTED', 
        'ARRIVED', 'CANCELLED'), default='SCHEDULED')
    meta = {
        'indexes': [
            'flight_number',
            'departure_airport',
            'arrival_airport',
            'departure_time'
        ],
        'collection': 'flights'
    }


class Seat(EmbeddedDocument):
    seat_number = StringField(required=True)
    seat_class = StringField(choices=('ECONOMY', 'BUSINESS', 'FIRST'), default='ECONOMY')
    is_available = BooleanField(default=True)
    price_modifier = DecimalField(precision=2, default=1.0)  # multiplier for base price

class Booking(Document):
    user = ReferenceField(User, required=True)
    flight = ReferenceField(Flight, required=True)
    passengers = ListField(EmbeddedDocumentField(Passenger))
    seats = ListField(EmbeddedDocumentField(Seat))
    total_price = DecimalField(required=True, precision=2)
    booking_reference = StringField(required=True, unique=True)
    booking_date = DateTimeField(default=datetime.utcnow)
    status = StringField(choices=(
        'CONFIRMED', 'CANCELLED', 'COMPLETED',
        'PENDING_PAYMENT', 'REFUNDED'), default='CONFIRMED')
    payment_status = StringField(choices=(
        'PENDING', 'PAID', 'FAILED', 'REFUNDED'), default='PENDING')
    meta = {
        'indexes': [
            'user',
            'flight',
            'booking_reference',
            'booking_date'
        ],
        'collection': 'bookings'
    }

class Payment(Document):
    booking = ReferenceField(Booking, required=True)
    amount = DecimalField(required=True, precision=2)
    payment_method = StringField(required=True, choices=(
        'CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'BANK_TRANSFER'))
    transaction_id = StringField(required=True)
    status = StringField(required=True, choices=(
        'PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'))
    payment_date = DateTimeField(default=datetime.utcnow)
    meta = {
        'collection': 'payments'
    }


class Promotion(Document):
    code = StringField(required=True, unique=True)
    description = StringField()
    discount_type = StringField(choices=('PERCENTAGE', 'FIXED_AMOUNT'), default='PERCENTAGE')
    discount_value = DecimalField(required=True, precision=2)
    start_date = DateTimeField(required=True)
    end_date = DateTimeField(required=True)
    is_active = BooleanField(default=True)
    applicable_flights = ListField(ReferenceField(Flight))
    meta = {
        'collection': 'promotions'
    }

class Review(Document):
    user = ReferenceField(User, required=True)
    flight = ReferenceField(Flight, required=True)
    rating = IntField(required=True, min_value=1, max_value=5)
    comment = StringField()
    review_date = DateTimeField(default=datetime.utcnow)
    meta = {
        'collection': 'reviews'
    }


# Schemas
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class FlightSearch(BaseModel):
    departure_airport: str
    arrival_airport: str
    departure_date: datetime
    return_date: Optional[datetime] = None
    passengers: int = Field(1, ge=1, le=10)

class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None
    passenger_type: str = 'ADULT'

    @validator('date_of_birth', pre=True)
    def parse_date(cls, value):
        if value is None:
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

class BookingCreate(BaseModel):
    flight_id: str
    passengers: List[PassengerInfo]
    seat_class: str = 'ECONOMY'
    promotion_code: Optional[str] = None

class Settings(BaseModel):
    authjwt_secret_key:str = "AfsarKhan12"



@AuthJWT.load_config
def get_config():
    return Settings()


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    total_users = User.objects.count()
    total_flights = Flight.objects.count()
    total_airports = Airport.objects.count()
    total_airlines = Airline.objects.count()
    total_aircraft = Aircraft.objects.count()
    context = {
        "request": request,
        'total_users': total_users,
        'total_flights': total_flights,
        'total_airports': total_airports,
        'total_airlines': total_airlines,
        'total_aircraft': total_aircraft,
    }
    return templates.TemplateResponse("home.html", context)

@app.post('/register', status_code=status.HTTP_201_CREATED)
def register(user: RegisterSchema):

    if User.objects(email=user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this email is already exists.'
        )
    try:
        new_user = User(
            email=user.email, 
            password = generate_password_hash(user.password),
            username = user.username
            ).save()
    except NotUniqueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mai nahi bataunga"
        )
    Profile(user=new_user).save()
    response = {
        "Message": "User created succcessfully",
        "user": {
            "email": new_user.email,
            "username": new_user.username
        }
    }
    return jsonable_encoder(response)



@app.post("/login", status_code=status.HTTP_200_OK)
def login(user: LoginSchema, Authorize:AuthJWT=Depends()):
    user_record = User.objects(email = user.email).first()
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Email does not exists!'
        )
    if user and check_password_hash(user_record.password, user.password):
        access_token = Authorize.create_access_token(subject=user_record.email)
        refresh_token = Authorize.create_refresh_token(subject=user_record.email)

        response = {
            "access": access_token,
            "refresh": refresh_token
        }
        return jsonable_encoder(response)
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Invalid email or password'
    )

@app.get('/refresh')
def refresh_token(Authorize:AuthJWT=Depends()):
    try:
        Authorize.jwt_refresh_token_required()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Please provide valid refresh token'
        )
    current_user = Authorize.get_jwt_identity()
    access_token = Authorize.create_access_token(subject=current_user)
    return jsonable_encoder({"access": access_token})


@app.get('/profile')
def profile(Authorize: AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception:
        raise  HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Token'
        )
    current_user = Authorize.get_jwt_subject()
    print("current_user:", current_user)
    
    user = User.objects(email=current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    profile = Profile.objects(user=user).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Profile not found')
    profile_data = {
        "email": user.email,
        "username": user.username,
        "bio": profile.bio,
        "link": profile.link
    }
    return jsonable_encoder({"Profile":profile_data})


def custom_encoder(flight):
    return {
        "id": str(flight.id),
        "flight_number": flight.flight_number,
        "airline": {
            "code": flight.airline.code,
            "name": flight.airline.name,
            "logo_url": flight.airline.logo_url
        },
        "aircraft": {
            "model": flight.aircraft.model,
            "code": flight.aircraft.code,
        },
        "departure_airport": {
            "code": flight.departure_airport.code,
            "city": flight.departure_airport.city,
        },
        "arrival_airport": {
            "code": flight.arrival_airport.code,
            "city": flight.arrival_airport.city,
        },
        "departure_time": flight.departure_time.isoformat(),
        "arrival_time": flight.arrival_time.isoformat(),
        "duration": flight.duration,
        "base_price": float(flight.base_price),
        "available_seats": flight.available_seats,
        "status": flight.status
    }

@app.get('/flights', response_class=HTMLResponse)
def flights(request: Request):
    flights = Flight.objects.all()
    results = [custom_encoder(flight) for flight in flights]
    context = {
        'request': request,
        "flights": results
    }
    return templates.TemplateResponse('Analytics/flight.html', context)


@app.get('/flight_detail/{flight_id}', response_class=HTMLResponse)
def flight_detail(request: Request, flight_id: str):
    flight = Flight.objects(id=flight_id).first()
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Flight not found'
        )
    context = {
        "request": request,
        "flight": custom_encoder(flight)
    }
    return templates.TemplateResponse('Analytics/flight_detail.html', context)


@app.get('/airport', response_class=HTMLResponse)
def airports(request: Request):
    airports = Airport.objects.all()
    results = []
    for airport in airports:
        results.append({
            "code": airport.code,
            "name": airport.name,
            "city": airport.city,
            "country": airport.country,
            "timezone": airport.timezone,
            "lat": airport.latitude,
            "lng": airport.longitude
        })
    
    context = {
        'request': request,
        "airports": results
    }
    return templates.TemplateResponse('Analytics/airport.html', context)


@app.get('/airlines')
def airlines(request: Request):
    airlines = Airline.objects.all()
    results = []
    for airline in airlines:
        results.append({
            "code": airline.code,
            "name": airline.name,
            "logo_url": airline.logo_url,
            "lat": airline.latitude,
            'lng': airline.longitude
        })
    context = {
        "request": request,
        "airlines": results
    }
    return templates.TemplateResponse("Analytics/airline.html", context)


@app.get('/aircraft')
def  aircrafts(request: Request):
    aircrafts = Aircraft.objects.all()
    results = []
    for aircraft in aircrafts:
        results.append({
            "model": aircraft.model,
            "code": aircraft.code,
            "manufacturer": aircraft.manufacturer,
            "capacity": aircraft.capacity
        })
    context = {
        'request': request,
        "aircrafts": results
    }
    return templates.TemplateResponse('Analytics/aircraft.html', context)

@app.post('/add_passenger')
def add_passenger(passenger: PassengerInfo, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Token'
        )
    
    current_user = Authorize.get_jwt_subject()
    user = User.objects(email=current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    
    try:
        passenger_data = passenger.dict()
        
        if passenger_data.get('date_of_birth'):
            if isinstance(passenger_data['date_of_birth'], str):
                passenger_data['date_of_birth'] = datetime.strptime(passenger_data['date_of_birth'], "%Y-%m-%d").date()
            passenger_data['date_of_birth'] = datetime.combine(
                passenger_data['date_of_birth'], 
                datetime.min.time()
            )
        
        new_passenger = Passenger(
            first_name=passenger_data['first_name'],
            last_name=passenger_data['last_name'],
            passport_number=passenger_data.get('passport_number'),
            nationality=passenger_data.get('nationality'),
            date_of_birth=passenger_data.get('date_of_birth'),
            passenger_type=passenger_data['passenger_type']
        )
        new_passenger.sa
        profile = Profile.objects(user=user).first()
        if not profile:
            profile = Profile(user=user)
        
        if not hasattr(profile, 'passengers'):
            profile.passengers = []
        
        # Check if passenger already exists
        if any(p.first_name == new_passenger.first_name and 
               p.last_name == new_passenger.last_name and
               p.passport_number == new_passenger.passport_number 
               for p in profile.passengers):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passenger already exists"
            )
        
        profile.passengers.append(new_passenger)
        profile.save()
        
        return {"message": "Passenger added successfully", "passenger_id": str(new_passenger.id)}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saving passenger: {str(e)}"
        )

@app.get('/get_passengers')
def get_passengers(Authorize: AuthJWT=Depends()):
    try:
        Authorize.jwt_required()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Token'
        )
    current_user = Authorize.get_jwt_subject()
    user = User.objects(email=current_user).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    profile = Profile.objects(user=user).first()
    if not profile or not hasattr(profile, 'passengers') or not profile.passengers:
        return []
    
    passengers = []
    for p in profile.passengers:
        passenger_dict = {
            "id": str(p.id),
            "first_name": p.first_name,
            "last_name": p.last_name,
            "passport_number": p.passport_number,
            "nationality": p.nationality,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "passenger_type": p.passenger_type
        }
        passengers.append(passenger_dict)
    
    return passengers

@app.delete('/delete_passenger/{passenger_id}')
def delete_passenger(passenger_id: str, Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Token'
        )
    
    current_user = Authorize.get_jwt_subject()
    user = User.objects(email=current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    
    profile = Profile.objects(user=user).first()
    if not profile or not hasattr(profile, 'passengers'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No passengers found'
        )
    
    initial_count = len(profile.passengers)
    profile.passengers = [p for p in profile.passengers if str(p.id) != passenger_id]

    if len(profile.passengers) == initial_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Passenger not found'
        )
    
    profile.save()
    return {"message": "Passenger deleted successfully"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)