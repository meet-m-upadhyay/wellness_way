"""
Meal Templates - Cuisine-specific structural archetypes to ensure valid ingredient combinations.
"""

import random
from typing import Dict, List, Any

# Archetypes for Indian cuisine
INDIAN_TEMPLATES = [
    {
        "name": "Dal & {starch} Bowl / Dal Khichdi",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["dal", "lentil", "rajma", "chana", "chickpea", "moong", "soy", "soya"],
            "starch": ["rice", "quinoa", "millet", "dalia", "brown rice"],
            "vegetables": ["spinach", "tomato", "onion", "carrot", "peas", "gourd", "pumpkin", "okra", "cauliflower", "cabbage", "broccoli"],
            "fat": ["ghee", "oil", "coconut"]
        }
    },
    {
        "name": "Curry with {starch}",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["paneer", "tofu", "chicken", "soya", "soy", "egg", "kofta", "matar", "chana", "rajma", "chickpea", "mutton", "lamb", "fish", "prawn", "keema"],
            "starch": ["roti", "chapati", "paratha", "naan", "wheat", "bajra", "jowar"],
            "vegetables": ["bell pepper", "capsicum", "onion", "tomato", "spinach", "cauliflower", "potato", "broccoli"],
            "fat": ["ghee", "butter", "oil"]
        }
    },
    {
        "name": "Savory Breakfast ({starch})",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["peanut", "yogurt", "sprouts", "paneer", "egg"],
            "starch": ["poha", "upma", "semolina", "suji", "oats", "rice flakes", "millet"],
            "vegetables": ["onion", "tomato", "peas", "carrot", "potato", "chili"],
            "fat": ["oil", "ghee", "mustard oil"]
        }
    },
    {
        "name": "Stuffed {starch} with Yogurt",
        "meal_types": ["breakfast", "lunch", "snack"],
        "components": {
            "protein": ["yogurt", "curd", "paneer", "egg"],
            "starch": ["wheat", "paratha", "flour", "roti", "chapati", "bajra", "jowar", "naan"],
            "vegetables": ["potato", "cauliflower", "radish", "onion", "spinach", "fenugreek", "methi"],
            "fat": ["ghee", "butter", "oil"]
        }
    },
    {
        "name": "Sweet {starch} Porridge",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["milk", "almond milk", "soy milk", "yogurt", "protein powder"],
            "starch": ["oats", "rice", "quinoa", "vermicelli", "seviyan", "dalia"],
            "vegetables": ["apple", "banana", "berry", "mango", "pomegranate", "blueberry", "strawberry", "grape"], # Fruits
            "fat": ["almond", "walnut", "cashew", "chia", "flax", "coconut", "peanut"]
        }
    },
    {
        "name": "Dry Sabzi with {starch} and Protein side",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["yogurt", "curd", "sprouts", "dal", "paneer", "tofu", "egg"],
            "starch": ["roti", "chapati", "wheat", "bajra", "jowar", "paratha", "rice"],
            "vegetables": ["okra", "bhindi", "bitter gourd", "cabbage", "cauliflower", "green beans", "potato", "carrot", "capsicum", "lauki", "palak", "baingan"],
            "fat": ["mustard oil", "oil", "ghee"]
        }
    },
    {
        "name": "South Indian Breakfast ({starch})",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["yogurt", "curd", "sambar", "chutney", "egg", "paneer"],
            "starch": ["idli", "dosa", "uttapam", "rice", "puri", "vada"],
            "vegetables": ["tomato", "onion", "coconut", "curry leaves", "carrot", "potato"],
            "fat": ["coconut oil", "oil", "ghee"]
        }
    },
    {
        "name": "Rajma / Chole with {starch}",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["rajma", "chole", "kidney bean", "chickpea", "chana"],
            "starch": ["rice", "roti", "chapati", "naan", "paratha"],
            "vegetables": ["onion", "tomato", "spinach", "capsicum", "cucumber", "carrot"],
            "fat": ["ghee", "oil", "butter"]
        }
    },
    {
        "name": "Grilled {protein} with {starch}",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["chicken", "fish", "tikka", "tandoori", "mutton", "lamb", "prawn", "keema", "paneer"],
            "starch": ["rice", "roti", "naan", "paratha", "quinoa", "brown rice"],
            "vegetables": ["onion", "tomato", "capsicum", "spinach", "carrot", "broccoli", "bell pepper"],
            "fat": ["ghee", "butter", "oil"]
        }
    },
    {
        "name": "{protein} Biryani / Pulao",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["chicken", "mutton", "lamb", "keema", "prawn", "fish", "egg", "paneer", "soya"],
            "starch": ["rice", "brown rice", "quinoa"],
            "vegetables": ["onion", "tomato", "mint", "carrot", "peas", "potato"],
            "fat": ["ghee", "oil", "butter"]
        }
    },
    {
        "name": "Egg Breakfast ({starch})",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["egg", "omelette", "bhurji", "boiled"],
            "starch": ["paratha", "roti", "bread", "toast", "poha", "upma"],
            "vegetables": ["onion", "tomato", "capsicum", "chili", "spinach", "mushroom"],
            "fat": ["butter", "oil", "ghee"]
        }
    }
]

# Archetypes for Mediterranean cuisine
MEDITERRANEAN_TEMPLATES = [
    {
        "name": "Mediterranean Salad Bowl",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["chickpea", "falafel", "chicken", "feta", "egg", "tuna", "bean", "lentil"],
            "starch": ["quinoa", "couscous", "bulgur", "pita", "bread", "pasta"],
            "vegetables": ["cucumber", "tomato", "spinach", "olive", "bell pepper", "onion", "lettuce", "greens"],
            "fat": ["olive oil", "tahini", "avocado", "feta", "oil"]
        }
    },
    {
        "name": "Wrap / Shawarma / Gyro",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["chicken", "paneer", "tofu", "falafel", "lamb", "egg", "hummus", "tuna", "beef"],
            "starch": ["pita", "wrap", "tortilla", "bread"],
            "vegetables": ["lettuce", "tomato", "cucumber", "onion", "pickles", "cabbage", "spinach"],
            "fat": ["olive oil", "tahini", "garlic sauce", "yogurt", "avocado"]
        }
    },
    {
        "name": "Hummus & Mezze Plate",
        "meal_types": ["lunch", "snack", "dinner"],
        "components": {
            "protein": ["hummus", "chickpea", "falafel", "yogurt", "egg", "feta", "bean", "labneh"],
            "starch": ["pita", "crackers", "bread", "quinoa", "rice"],
            "vegetables": ["carrot", "cucumber", "bell pepper", "tomato", "olive", "celery", "eggplant"],
            "fat": ["olive oil", "tahini", "walnut", "avocado"]
        }
    },
    {
        "name": "Grilled {protein} with Roasted Veg",
        "meal_types": ["dinner", "lunch"],
        "components": {
            "protein": ["chicken", "fish", "salmon", "tofu", "shrimp", "lamb", "beef", "paneer", "halloumi"],
            "starch": ["potato", "sweet potato", "rice", "quinoa", "couscous", "pasta"],
            "vegetables": ["zucchini", "eggplant", "bell pepper", "onion", "tomato", "asparagus", "broccoli"],
            "fat": ["olive oil", "butter", "oil"]
        }
    },
    {
        "name": "Mediterranean Breakfast Toast/Bowl",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["egg", "feta", "yogurt", "milk", "hummus", "labneh"],
            "starch": ["bread", "toast", "oats", "muesli", "pita"],
            "vegetables": ["tomato", "cucumber", "spinach", "berry", "apple", "banana", "avocado"], # Mixed veg/fruit
            "fat": ["olive oil", "avocado", "almond", "walnut", "chia"]
        }
    },
    {
        "name": "Shakshuka / Baked Eggs",
        "meal_types": ["breakfast", "lunch"],
        "components": {
            "protein": ["egg", "feta", "chickpea", "bean", "halloumi"],
            "starch": ["pita", "bread", "toast", "couscous"],
            "vegetables": ["tomato", "bell pepper", "onion", "spinach", "eggplant"],
            "fat": ["olive oil", "oil"]
        }
    },
    {
        "name": "Tabbouleh / Grain Bowl",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["falafel", "chickpea", "feta", "halloumi", "chicken", "fish"],
            "starch": ["bulgur", "couscous", "quinoa", "pita"],
            "vegetables": ["tomato", "cucumber", "parsley", "mint", "onion", "lettuce", "olive"],
            "fat": ["olive oil", "tahini", "pine nut"]
        }
    }
]

# Archetypes for Italian cuisine
ITALIAN_TEMPLATES = [
    {
        "name": "{protein} Pasta with {starch}",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["mozzarella", "ricotta", "parmesan", "chicken", "sausage", "bean", "cannellini", "prosciutto"],
            "starch": ["penne", "spaghetti", "pasta", "orzo", "gnocchi"],
            "vegetables": ["tomato", "marinara", "mushroom", "spinach", "basil", "bell pepper", "zucchini", "asparagus"],
            "fat": ["olive oil", "pesto", "butter", "parmesan"]
        }
    },
    {
        "name": "Risotto with {protein}",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["parmesan", "chicken", "shrimp", "mushroom", "sausage", "mozzarella"],
            "starch": ["risotto", "arborio", "rice"],
            "vegetables": ["mushroom", "asparagus", "spinach", "peas", "tomato", "fennel", "zucchini"],
            "fat": ["olive oil", "butter", "parmesan"]
        }
    },
    {
        "name": "Italian Bruschetta / Toast",
        "meal_types": ["breakfast", "snack"],
        "components": {
            "protein": ["mozzarella", "ricotta", "egg", "prosciutto"],
            "starch": ["ciabatta", "bread", "toast", "focaccia"],
            "vegetables": ["tomato", "basil", "mushroom", "spinach", "cherry tomato"],
            "fat": ["olive oil", "pesto", "balsamic"]
        }
    },
    {
        "name": "Caprese / Italian Salad",
        "meal_types": ["lunch", "dinner", "snack"],
        "components": {
            "protein": ["mozzarella", "ricotta", "chicken", "bean", "cannellini", "prosciutto"],
            "starch": ["bread", "ciabatta", "focaccia", "crackers"],
            "vegetables": ["tomato", "basil", "arugula", "spinach", "olive", "bell pepper", "artichoke"],
            "fat": ["olive oil", "balsamic", "pesto", "pine nut"]
        }
    },
    {
        "name": "Polenta / Gnocchi Bowl",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["parmesan", "ricotta", "chicken", "sausage", "mushroom", "bean"],
            "starch": ["polenta", "gnocchi"],
            "vegetables": ["marinara", "tomato", "spinach", "mushroom", "bell pepper", "fennel"],
            "fat": ["olive oil", "butter", "pesto"]
        }
    },
    {
        "name": "Minestrone / Italian Bowl",
        "meal_types": ["lunch", "dinner"],
        "components": {
            "protein": ["cannellini", "bean", "chicken", "sausage", "lentil"],
            "starch": ["pasta", "bread", "ciabatta", "rice"],
            "vegetables": ["tomato", "zucchini", "carrot", "celery", "spinach", "cabbage", "fennel"],
            "fat": ["olive oil", "parmesan", "pesto"]
        }
    }
]

class TemplateRegistry:
    def __init__(self):
        self.templates = {
            "indian": INDIAN_TEMPLATES,
            "mediterranean": MEDITERRANEAN_TEMPLATES,
            "italian": ITALIAN_TEMPLATES
        }

    def get_template(self, cuisine: str, meal_type: str) -> Dict[str, Any]:
        """
        Get a random suitable template for the given cuisine and meal type.
        Falls back to a generic combination if not found.
        """
        cuisine_templates = self.templates.get(cuisine.lower(), INDIAN_TEMPLATES)
        
        # Filter templates that match the meal type (breakfast vs lunch/dinner)
        valid_templates = [t for t in cuisine_templates if meal_type in t["meal_types"]]
        
        if not valid_templates:
            # Fallback to any template if none strictly match the meal type
            valid_templates = cuisine_templates
            
        return random.choice(valid_templates)

    # Priority scores by user diet type → item diet tier.
    _DIET_PRIORITY = {
        "non-vegetarian": {"non-vegetarian": 4, "eggetarian": 3, "vegetarian": 2, "vegan": 1},
        "eggetarian":     {"eggetarian": 3, "vegetarian": 2, "vegan": 1},
        "vegetarian":     {"vegetarian": 2, "vegan": 1},
        "vegan":          {"vegan": 1},
    }

    @staticmethod
    def _item_diet_tier(diet_flags) -> str:
        """Determine the diet tier of a food item from its diet_flags."""
        flags = {f.lower() for f in (diet_flags or [])}
        if "non-vegetarian" in flags:
            return "non-vegetarian"
        if "eggetarian" in flags and "vegetarian" not in flags:
            return "eggetarian"
        if "vegetarian" in flags and "vegan" not in flags:
            return "vegetarian"
        return "vegan"

    def select_best_ingredient(
        self,
        available_items: List[Any],
        template_keywords: List[str],
        diet_type: str = None,
    ) -> Any:
        """
        Selects the best matching item from a category based on the template's keywords.
        Among keyword matches, picks from the highest diet-priority tier first
        (e.g. for a non-veg user: meat > egg > dairy > plant).
        Returns a random item if no keyword match is found.
        """
        if not available_items:
            return None

        # Shuffle for variety within a tier
        items = list(available_items)
        random.shuffle(items)

        # Collect items that match at least one template keyword
        matched = [
            item for item in items
            if any(kw in item.canonical_name.lower() for kw in template_keywords)
        ]

        if not matched:
            return random.choice(available_items)

        # If we have a diet_type with a priority map, pick from the
        # highest-priority tier among the matches.
        priority_map = self._DIET_PRIORITY.get(diet_type)
        if priority_map:
            tier_groups: Dict[int, List[Any]] = {}
            for item in matched:
                tier = self._item_diet_tier(item.diet_flags)
                score = priority_map.get(tier, 0)
                tier_groups.setdefault(score, []).append(item)
            best_score = max(tier_groups)
            return random.choice(tier_groups[best_score])

        # No diet_type — return any matched item
        return matched[0]

def get_template_registry() -> TemplateRegistry:
    return TemplateRegistry()
