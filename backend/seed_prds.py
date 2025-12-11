#!/usr/bin/env python3
"""
Seed script to populate the database with test PRDs.
Run this script to add 20 sample PRDs for testing update/delete functionality.

Usage:
    python seed_prds.py <user_email>
    
Example:
    python seed_prds.py test@example.com
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Sample PRD data
SAMPLE_PRDS = [
    {"idea": "E-commerce marketplace for handmade crafts", "content": "# Handmade Crafts Marketplace\n\n## Overview\nA platform connecting artisans with buyers seeking unique handmade items.\n\n## Features\n- Seller storefronts\n- Payment processing\n- Reviews and ratings\n- Search and filtering"},
    {"idea": "Fitness tracking app with social features", "content": "# FitSocial App\n\n## Overview\nTrack workouts and compete with friends.\n\n## Features\n- Workout logging\n- Progress photos\n- Leaderboards\n- Challenge system"},
    {"idea": "Recipe sharing platform with AI suggestions", "content": "# AI Recipe Hub\n\n## Overview\nShare recipes and get AI-powered meal suggestions.\n\n## Features\n- Recipe database\n- AI meal planning\n- Grocery lists\n- Nutritional analysis"},
    {"idea": "Task management tool for remote teams", "content": "# RemoteTask Pro\n\n## Overview\nManage projects and tasks for distributed teams.\n\n## Features\n- Kanban boards\n- Time tracking\n- Team chat\n- File sharing"},
    {"idea": "Language learning app with native speakers", "content": "# LinguaConnect\n\n## Overview\nPractice languages with native speakers worldwide.\n\n## Features\n- Video calls\n- Text chat\n- Flashcards\n- Progress tracking"},
    {"idea": "Personal finance dashboard", "content": "# FinanceHub\n\n## Overview\nTrack spending, budgets, and investments.\n\n## Features\n- Bank sync\n- Budget categories\n- Investment tracking\n- Bill reminders"},
    {"idea": "Event planning and ticketing platform", "content": "# EventMaster\n\n## Overview\nCreate, manage, and sell tickets for events.\n\n## Features\n- Event creation\n- Ticket sales\n- Attendee management\n- Analytics"},
    {"idea": "Online learning platform for coding", "content": "# CodeAcademy Pro\n\n## Overview\nInteractive coding courses with real projects.\n\n## Features\n- Video lessons\n- Code editor\n- Project challenges\n- Certificates"},
    {"idea": "Pet care and veterinary booking app", "content": "# PetCare Plus\n\n## Overview\nManage pet health and book vet appointments.\n\n## Features\n- Health records\n- Vet booking\n- Medication reminders\n- Pet profiles"},
    {"idea": "Sustainable shopping recommendation engine", "content": "# EcoShop Guide\n\n## Overview\nFind eco-friendly alternatives to everyday products.\n\n## Features\n- Product scanner\n- Sustainability scores\n- Alternative suggestions\n- Carbon tracking"},
    {"idea": "Mental health journaling app", "content": "# MindSpace Journal\n\n## Overview\nDaily journaling with mood tracking and insights.\n\n## Features\n- Guided prompts\n- Mood analytics\n- Meditation timer\n- Privacy focused"},
    {"idea": "Freelancer portfolio and invoicing tool", "content": "# FreelanceHub\n\n## Overview\nShowcase work and manage freelance business.\n\n## Features\n- Portfolio builder\n- Invoice generation\n- Time tracking\n- Client management"},
    {"idea": "Book club management platform", "content": "# BookClub Central\n\n## Overview\nOrganize and run virtual book clubs.\n\n## Features\n- Reading schedules\n- Discussion forums\n- Video meetings\n- Book recommendations"},
    {"idea": "Home automation control center", "content": "# SmartHome Hub\n\n## Overview\nCentral control for all smart home devices.\n\n## Features\n- Device dashboard\n- Automation rules\n- Voice control\n- Energy monitoring"},
    {"idea": "Travel itinerary planner with AI", "content": "# TripGenius\n\n## Overview\nAI-powered travel planning and booking.\n\n## Features\n- Itinerary builder\n- Flight/hotel search\n- Local recommendations\n- Budget tracking"},
    {"idea": "Music collaboration platform", "content": "# BandMate Online\n\n## Overview\nCollaborate on music with artists worldwide.\n\n## Features\n- Cloud DAW\n- Version control\n- Real-time collab\n- Marketplace"},
    {"idea": "Neighborhood community app", "content": "# NeighborNet\n\n## Overview\nConnect with your local community.\n\n## Features\n- Local marketplace\n- Event calendar\n- Safety alerts\n- Service recommendations"},
    {"idea": "Habit tracking with gamification", "content": "# HabitQuest\n\n## Overview\nBuild habits through game mechanics.\n\n## Features\n- Daily streaks\n- Achievement badges\n- Friend competitions\n- Reward system"},
    {"idea": "Restaurant reservation and ordering system", "content": "# DineEasy\n\n## Overview\nBook tables and order ahead at restaurants.\n\n## Features\n- Table booking\n- Menu browsing\n- Pre-ordering\n- Loyalty rewards"},
    {"idea": "Job interview preparation platform", "content": "# InterviewPro\n\n## Overview\nPractice interviews with AI feedback.\n\n## Features\n- Mock interviews\n- AI analysis\n- Question bank\n- Resume review"},
]

async def seed_database(user_email: str):
    """Seed the database with sample PRDs for a given user."""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("Error: MONGO_URL and DB_NAME must be set in .env")
        sys.exit(1)
    
    client = AsyncIOMotorClient(mongo_url, tlsAllowInvalidCertificates=True)
    db = client[db_name]
    
    # Find the user
    user = await db.users.find_one({"email": user_email})
    if not user:
        print(f"Error: User with email '{user_email}' not found.")
        print("Please sign up first, then run this script.")
        sys.exit(1)
    
    user_id = user['id']
    print(f"Found user: {user_email} (ID: {user_id})")
    
    # Create PRD documents
    prds = []
    base_time = datetime.now(timezone.utc)
    
    for i, sample in enumerate(SAMPLE_PRDS):
        prd = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "idea": sample["idea"],
            "content": sample["content"],
            "created_at": (base_time - timedelta(hours=i)).isoformat()
        }
        prds.append(prd)
    
    # Insert all PRDs
    result = await db.saved_prds.insert_many(prds)
    print(f"Successfully inserted {len(result.inserted_ids)} PRDs!")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python seed_prds.py <user_email>")
        print("Example: python seed_prds.py test@example.com")
        sys.exit(1)
    
    user_email = sys.argv[1]
    asyncio.run(seed_database(user_email))
