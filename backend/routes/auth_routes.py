from fastapi import APIRouter, HTTPException, status
from models import User, UserCreate, UserLogin, AuthResponse
from auth import hash_password, verify_password, create_access_token
from fastapi import Response

router = APIRouter()

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    """
    Handle user registration.
    - Checks if a user with the given email already exists.
    - Hashes the password.
    - Stores the new user in the database.
    - Creates and returns a JWT token.
    """
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    
    # Hash the password
    hashed_pass = hash_password(user_in.password)
    
    # Create new user instance
    new_user = User(email=user_in.email, hashed_password=hashed_pass)
    await new_user.insert()
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return AuthResponse(
        jwt_token=access_token,
        email=new_user.email,
        status="success",
        message="account created successfully"
    )


@router.post("/login", response_model=AuthResponse)
async def login_for_access_token(form_data: UserLogin, response: Response):
    """
    Handle user login.
    - Verifies user credentials.
    - Returns JWT and sets it as an HttpOnly cookie.
    """
    user = await User.find_one(User.email == form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})

    # 👇 Store token in HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,         # ✅ Use True only if using HTTPS
        samesite="none",      # ✅ "none" for localhost:3000 ↔ localhost:8000
        max_age=60 * 60 * 24  # optional: 1 day
    )

    return AuthResponse(
        jwt_token=access_token,  # optional (can omit if not needed on frontend)
        email=user.email,
        status="success"
    )
