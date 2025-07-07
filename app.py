from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_jwt_auth import AuthJWT
from mongoengine import connect, Document, EmailField, StringField, ReferenceField, BooleanField, NotUniqueError
from pydantic import BaseModel, EmailStr
import uvicorn

connect(db="fastapi_jwt_auth", host="localhost", port=27017)


class User(Document):
    email = EmailField(required=True, unique=True)
    password  = StringField(required=True)
    username = StringField(max_length=50)
    is_active = BooleanField(default=True)

    def __str__(self):
        return f"{self.username} Account Updated"
    

class Profile(Document):
    user = ReferenceField(User, required=True, unique=True)
    bio = StringField(default="Hello! I'm new here..")
    link = StringField(default='https://youtube.com')

    def __str__(self):
        return f"{self.user.username}'s Profile is {'Active' if self.user.is_active else "Deactivate"}"
    

# Schemas
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    username: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class Settings(BaseModel):
    authjwt_secret_key:str = "AfsarKhan12"


app = FastAPI()

@AuthJWT.load_config
def get_config():
    return Settings()

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


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)