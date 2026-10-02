from fastapi import HTTPException
from jose import jwt
from .auth import SECRET_KEY, ALGORITHM
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User, Property, Investment
from .auth import hash_password
from .auth import verify_password, create_access_token
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import Field
from typing import Dict
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from .payment import create_order
from .blockchain import mint_tokens

oauth2_scheme = HTTPBearer()


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class InvestRequest(BaseModel):
    property_id: int
    units: int = Field(gt=0)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class WalletRequest(BaseModel):
    wallet: str


router = APIRouter()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/signup", status_code=201)
def signup(user_data: UserSignup, db: Session = Depends(get_db)): # Uses Body schema
    # Check if user already exists to avoid 500 errors
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user = User(name=user_data.name, email=user_data.email, password=hash_password(user_data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created"}




@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password):
        # Use 401 Unauthorized instead of 200 with an error message
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}






@router.get("/properties")
def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).all()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    




@router.post("/invest", status_code=201)
def invest(
    data: InvestRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    property = db.query(Property).filter(Property.id == data.property_id).first()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")


    if property.available_units < data.units:
        raise HTTPException(status_code=400, detail="Not enough units available")

    amount = (property.total_value / property.total_units) * data.units

    investment = Investment(
        user_id=user_id,
        property_id=data.property_id,
        units=data.units,
        amount=amount
    )

    try:
        property.available_units -= data.units
        db.add(investment)
        db.commit()
        db.refresh(investment)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Investment successful", "amount": amount}





@router.get("/portfolio")
def portfolio(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investments = db.query(Investment).filter(
        Investment.user_id == user_id
    ).all()

    result = []
    total = 0

    for inv in investments:
        property = db.query(Property).filter(
        Property.id == inv.property_id).first()

        property_name = property.name if property else "Deleted property"

        total += inv.amount

        result.append({
            "property": property_name,
            "units": inv.units,
            "amount": inv.amount
        })

    return {
        "total_invested": total,
        "investments": result
    }




@router.post("/create-order")
def create_payment_order(
    data: InvestRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    property = db.query(Property).filter(Property.id == data.property_id).first()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    amount = (property.total_value / property.total_units) * data.units

    order = create_order(amount)

    return {
        "order_id": order["id"],
        "amount": amount
    }







@router.post("/verify-payment")
def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    data: InvestRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import razorpay

    client = razorpay.Client(auth=("YOUR_KEY_ID", "YOUR_KEY_SECRET"))

    # TEMPORARY bypass
    payment_verified = True
    '''try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature})
    except:
        raise HTTPException(status_code=400, detail="Payment verification failed")'''

    property = db.query(Property).filter(
        Property.id == data.property_id
    ).first()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    amount = (property.total_value / property.total_units) * data.units

    investment = Investment(
        user_id=user_id,
        property_id=data.property_id,
        units=data.units,
        amount=amount
    )

    property.available_units -= data.units
    db.add(investment)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    if not user.wallet:
        raise HTTPException(
            status_code=400,
            detail="User wallet not connected"
    )

    tx_hash = mint_tokens(
        user.wallet,
        data.property_id,
        data.units
    )

    return {
        "message": "Investment successful",
        "tx_hash": tx_hash
    }





@router.post("/set-wallet")
def set_wallet(
    data: WalletRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    user.wallet = data.wallet
    db.commit()

    return {"message": "Wallet saved"}