"""
Sample activities data for the RAG knowledge base.
This file contains hardcoded activity examples that will be embedded and stored
in the vector database for activity recommendations.
"""

SAMPLE_ACTIVITIES = [
    {
        "id": "outdoor_bike_1",
        "title": "Scenic Coastal Bike Ride",
        "description": "Go for a scenic bike ride along the coast, enjoying ocean views and fresh sea breeze. Perfect for morning or afternoon adventures.",
        "category": "outdoor_sports",
        "tags": ["biking", "outdoor", "scenic", "coast", "exercise", "nature"],
        "duration": "2-3 hours",
        "difficulty": "moderate",
        "group_size": "1-6 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "free"
    },
    {
        "id": "cultural_museum_1",
        "title": "Local Art Museum Visit",
        "description": "Visit the local art museum to explore contemporary and classical exhibitions. Great for rainy days and cultural enrichment.",
        "category": "cultural",
        "tags": ["museum", "art", "culture", "indoor", "educational", "relaxing"],
        "duration": "2-4 hours",
        "difficulty": "easy",
        "group_size": "1-8 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "low"
    },
    {
        "id": "dining_italian_1",
        "title": "New Italian Restaurant Experience",
        "description": "Try a new Italian restaurant in town, featuring authentic pasta dishes and wood-fired pizzas. Perfect for date nights or family dinners.",
        "category": "dining",
        "tags": ["restaurant", "italian", "food", "dining", "social", "evening"],
        "duration": "1-2 hours",
        "difficulty": "easy",
        "group_size": "2-8 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "medium"
    },
    {
        "id": "outdoor_hiking_1",
        "title": "Mountain Trail Hiking",
        "description": "Explore mountain trails with beautiful views and wildlife spotting opportunities. Bring water and wear comfortable hiking boots.",
        "category": "outdoor_sports",
        "tags": ["hiking", "mountains", "nature", "exercise", "adventure", "outdoor"],
        "duration": "3-5 hours",
        "difficulty": "moderate",
        "group_size": "2-10 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "free"
    },
    {
        "id": "entertainment_movie_1",
        "title": "Cinema Movie Night",
        "description": "Catch the latest blockbuster or indie film at the local cinema. Great for evening entertainment with friends or family.",
        "category": "entertainment",
        "tags": ["movies", "cinema", "entertainment", "indoor", "evening", "social"],
        "duration": "2-3 hours",
        "difficulty": "easy",
        "group_size": "2-12 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "medium"
    },
    {
        "id": "fitness_yoga_1",
        "title": "Outdoor Yoga Session",
        "description": "Join an outdoor yoga class in the park, connecting with nature while improving flexibility and mindfulness.",
        "category": "fitness",
        "tags": ["yoga", "fitness", "outdoor", "mindfulness", "health", "relaxing"],
        "duration": "1-2 hours",
        "difficulty": "easy",
        "group_size": "1-20 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "low"
    },
    {
        "id": "social_picnic_1",
        "title": "Park Picnic Gathering",
        "description": "Organize a picnic in the local park with homemade food, games, and good company. Perfect for sunny weekends.",
        "category": "social",
        "tags": ["picnic", "park", "outdoor", "food", "games", "social", "family"],
        "duration": "3-6 hours",
        "difficulty": "easy",
        "group_size": "4-15 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "low"
    },
    {
        "id": "cultural_concert_1",
        "title": "Live Music Concert",
        "description": "Attend a live music concert featuring local bands or touring artists. Check venue for genre and ticket availability.",
        "category": "entertainment",
        "tags": ["music", "concert", "live", "entertainment", "evening", "social"],
        "duration": "2-4 hours",
        "difficulty": "easy",
        "group_size": "2-100 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "medium"
    },
    {
        "id": "adventure_kayak_1",
        "title": "River Kayaking Adventure",
        "description": "Paddle down the river in kayaks, enjoying wildlife and peaceful water views. Equipment rental usually available.",
        "category": "outdoor_sports",
        "tags": ["kayaking", "river", "water", "adventure", "nature", "exercise"],
        "duration": "3-5 hours",
        "difficulty": "moderate",
        "group_size": "2-8 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "medium"
    },
    {
        "id": "hobby_cooking_1",
        "title": "Cooking Class Workshop",
        "description": "Learn to cook a new cuisine in a hands-on cooking class. Take home recipes and new culinary skills.",
        "category": "hobby",
        "tags": ["cooking", "learning", "food", "skills", "indoor", "social"],
        "duration": "2-3 hours",
        "difficulty": "easy",
        "group_size": "4-12 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "medium"
    },
    {
        "id": "relaxing_spa_1",
        "title": "Spa and Wellness Day",
        "description": "Treat yourself to a relaxing spa day with massages, facials, and wellness treatments. Perfect for self-care.",
        "category": "wellness",
        "tags": ["spa", "wellness", "relaxation", "self-care", "indoor", "peaceful"],
        "duration": "3-6 hours",
        "difficulty": "easy",
        "group_size": "1-4 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "high"
    },
    {
        "id": "family_zoo_1",
        "title": "Zoo Animal Adventure",
        "description": "Visit the local zoo to see exotic animals and learn about wildlife conservation. Great family activity with educational value.",
        "category": "family",
        "tags": ["zoo", "animals", "family", "educational", "outdoor", "children"],
        "duration": "3-5 hours",
        "difficulty": "easy",
        "group_size": "2-10 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "medium"
    },
    {
        "id": "adventure_climbing_1",
        "title": "Rock Climbing Experience",
        "description": "Try indoor or outdoor rock climbing with proper safety equipment and instruction. Great for building confidence and strength.",
        "category": "outdoor_sports",
        "tags": ["climbing", "adventure", "exercise", "challenge", "safety", "strength"],
        "duration": "2-4 hours",
        "difficulty": "challenging",
        "group_size": "2-6 people",
        "weather_dependent": False,
        "indoor_outdoor": "either",
        "budget": "medium"
    },
    {
        "id": "cultural_theater_1",
        "title": "Live Theater Performance",
        "description": "Enjoy a live theater performance featuring drama, comedy, or musical productions. Check local theater schedules.",
        "category": "cultural",
        "tags": ["theater", "performance", "culture", "entertainment", "evening", "arts"],
        "duration": "2-3 hours",
        "difficulty": "easy",
        "group_size": "2-50 people",
        "weather_dependent": False,
        "indoor_outdoor": "indoor",
        "budget": "medium"
    },
    {
        "id": "outdoor_beach_1",
        "title": "Beach Day Activities",
        "description": "Spend a day at the beach swimming, sunbathing, playing volleyball, or building sandcastles. Don't forget sunscreen!",
        "category": "outdoor_sports",
        "tags": ["beach", "swimming", "sun", "volleyball", "relaxation", "water"],
        "duration": "4-8 hours",
        "difficulty": "easy",
        "group_size": "1-20 people",
        "weather_dependent": True,
        "indoor_outdoor": "outdoor",
        "budget": "free"
    }
]

def get_activities_for_embedding():
    """
    Return activities formatted for embedding in the vector database.
    Each activity is converted to a text representation for semantic search.
    """
    embedded_activities = []
    
    for activity in SAMPLE_ACTIVITIES:
        # Create a comprehensive text representation for embedding
        text_representation = f"""
        Title: {activity['title']}
        Description: {activity['description']}
        Category: {activity['category']}
        Tags: {', '.join(activity['tags'])}
        Duration: {activity['duration']}
        Difficulty: {activity['difficulty']}
        Group Size: {activity['group_size']}
        Indoor/Outdoor: {activity['indoor_outdoor']}
        Budget: {activity['budget']}
        Weather Dependent: {'Yes' if activity['weather_dependent'] else 'No'}
        """.strip()
        
        embedded_activities.append({
            'id': activity['id'],
            'text': text_representation,
            'metadata': activity
        })
    
    return embedded_activities