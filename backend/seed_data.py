import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import User, DanceStyle, Song, TutorialStep, UserSongStatus # Import all necessary models
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# The database URL is read from the environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Create a .env file.")

async def seed_data():
    """Initializes the database connection, clears old data, and inserts new seed data."""
    try:
        client = AsyncIOMotorClient(DATABASE_URL)
        # Use get_default_database() to get the database specified in the connection string
        await init_beanie(
            database=client.get_default_database(), 
            document_models=[User, DanceStyle, Song, TutorialStep, UserSongStatus]
        )
    except Exception as e:
        print(f"Failed to connect or initialize Beanie: {e}")
        return

    print("Connected to MongoDB successfully ✅")

    # --- Clear existing data ---
    await User.delete_all()
    await DanceStyle.delete_all()
    await Song.delete_all()
    await TutorialStep.delete_all()
    await UserSongStatus.delete_all()

    print("Cleared all existing data.")

    # ==============================================================================
    # 1. Create Dance Styles 
    # ==============================================================================
    bharatanatyam = DanceStyle(
        dance_name="Bharatanatyam",
        description="A major form of Indian classical dance, known for its grace, purity, and sculpturesque poses.",
        origin="Tamil Nadu, India",
        songs=2, # Count of songs
        img="https://storage.googleapis.com/natyavision-media/bharatanatan.jpg",
    )

    hiphop = DanceStyle(
        dance_name="Hip Hop",
        description="A style of dance that evolved as part of hip hop culture, often including breaking, locking, and popping.",
        origin="The Bronx, New York, USA",
        songs=1, # Count of songs
        img="https://storage.googleapis.com/natyavision-media/hiphop.jpg",
    )

    await bharatanatyam.insert()
    await hiphop.insert()

    print(f"Created Dance Styles: {bharatanatyam.dance_name}, {hiphop.dance_name}")

    # ==============================================================================
    # 2. Create Songs with Links to Dance Styles 
    #    FIX: Songs must be inserted individually to generate IDs 
    #    before they are linked in TutorialStep documents.
    # ==============================================================================
    song_bn_1 = Song(
        dance_style=bharatanatyam,
        name="Alarippu Tishra",
        description="A traditional invocation piece, perfect for beginners.",
        time=12,
        lessons=6,
        teacher="Guru Meena",
    )
    await song_bn_1.insert() 

    song_bn_2 = Song(
        dance_style=bharatanatyam,
        name="Thillana in Raga Khamas",
        description="A fast-paced, climactic piece demonstrating technical virtuosity.",
        time=18,
        lessons=10,
        teacher="Guru Meena",
    )
    await song_bn_2.insert() 
    
    song_hh_1 = Song(
        dance_style=hiphop,
        name="Groove Fundamentals",
        description="Basic hip-hop bounces and rocks.",
        time=7,
        lessons=4,
        teacher="B-Boy Flash",
    )
    await song_hh_1.insert() 

    print("Created Songs.")

    # ==============================================================================
    # 3. Create Tutorial Steps with Links to Songs 
    # ==============================================================================
    step_bn_1_1 = TutorialStep(
        song=song_bn_1, 
        name="Step 1: Samapada Stance",
        time=2,
        description="Learn the basic standing posture and foot position.",
    )
    step_bn_1_2 = TutorialStep(
        song=song_bn_1, 
        name="Step 2: Tatta Adavu (First Speed)",
        time=3,
        description="Introduction to the Tatta Adavu basic footwork.",
    )
    step_hh_1_1 = TutorialStep(
        song=song_hh_1, 
        name="Step 1: The Basic Bounce",
        time=1,
        description="Master the foundational rhythmic movement.",
    )
    step_hh_1_2 = TutorialStep(
        song=song_hh_1, 
        name="Step 2: Rocking",
        time=2,
        description="Practice body rocking and shoulder isolation.",
    )

    # Insert_many is fine here as the objects they link to are already saved.
    await TutorialStep.insert_many([step_bn_1_1, step_bn_1_2, step_hh_1_1, step_hh_1_2])
    print("Created Tutorial Steps.")

    print("Seed data insertion complete. Total documents created:")
    # FIX: Use .count() instead of .count_documents()
    print(f"  DanceStyles: {await DanceStyle.count()}")
    print(f"  Songs: {await Song.count()}")
    print(f"  TutorialSteps: {await TutorialStep.count()}")


if __name__ == "__main__":
    print("Starting database seeding...")
    asyncio.run(seed_data())
    print("Database seeding finished.")