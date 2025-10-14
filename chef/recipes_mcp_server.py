# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "fastmcp",
#     "fire",
# ]
# ///

from fastmcp import FastMCP
import fire

mcp = FastMCP()

# Hardcoded recipe data
RECIPES = [
    {
        "id": "recipe_001",
        "name": "Quinoa Buddha Bowl",
        "serving_size": "2 servings",
        "prep_time": "15 minutes",
        "cook_time": "15 minutes",
        "total_time": "30 minutes",
        "ingredients": [
            "1 cup quinoa, rinsed",
            "1 large avocado, sliced",
            "1 can (15 oz) chickpeas, drained and rinsed",
            "2 cups fresh spinach leaves",
            "1 large cucumber, diced",
            "1 cup cherry tomatoes, halved",
            "3 tbsp tahini",
            "2 tbsp fresh lemon juice",
            "1 tbsp olive oil",
            "Salt and pepper to taste"
        ],
        "steps": [
            "Cook quinoa: In a medium saucepan, bring 2 cups water to boil. Add quinoa, reduce heat to low, cover and simmer for 15 minutes until water is absorbed.",
            "Prepare vegetables: While quinoa cooks, wash spinach, dice cucumber, and halve cherry tomatoes. Slice avocado just before serving.",
            "Make tahini dressing: In a small bowl, whisk together tahini, lemon juice, olive oil, and 2-3 tbsp water until smooth. Season with salt and pepper.",
            "Assemble bowl: Divide cooked quinoa between 2 bowls. Top with spinach, chickpeas, cucumber, tomatoes, and avocado slices.",
            "Serve fresh: Drizzle tahini dressing over each bowl and serve immediately. Store leftover dressing refrigerated up to 5 days."
        ],
        "nutrition": {"calories": 420, "fat": 15, "carbs": 45, "protein": 16},
        "health_rating": "very_healthy"
    },
    {
        "id": "recipe_002", 
        "name": "Grilled Salmon with Vegetables",
        "serving_size": "4 servings",
        "prep_time": "10 minutes",
        "cook_time": "20 minutes",
        "total_time": "30 minutes",
        "ingredients": [
            "4 salmon fillets (6 oz each)",
            "2 cups broccoli florets",
            "2 bell peppers, cut into strips",
            "3 tbsp olive oil, divided",
            "3 cloves garlic, minced",
            "1 lemon, juiced and zested",
            "1 tsp dried herbs (thyme or oregano)",
            "Salt and black pepper to taste"
        ],
        "steps": [
            "Season salmon: Pat salmon fillets dry and season both sides with salt, pepper, and half the lemon zest. Let rest for 5 minutes.",
            "Prepare vegetables: Toss broccoli and bell peppers with 1 tbsp olive oil, minced garlic, salt, and pepper.",
            "Preheat grill: Heat grill or grill pan to medium-high heat. Brush grates with oil to prevent sticking.",
            "Grill salmon: Cook salmon skin-side down for 6-8 minutes, then flip and cook 4-6 minutes more until internal temp reaches 145°F.",
            "Steam vegetables: While salmon grills, steam vegetables in a steamer basket for 8-10 minutes until tender-crisp.",
            "Serve with lemon: Drizzle remaining olive oil and lemon juice over salmon and vegetables. Garnish with fresh herbs if desired."
        ],
        "nutrition": {"calories": 380, "fat": 18, "carbs": 8, "protein": 35},
        "health_rating": "very_healthy"
    },
    {
        "id": "recipe_003",
        "name": "Chocolate Chip Cookies",
        "serving_size": "24 cookies",
        "prep_time": "15 minutes",
        "cook_time": "12 minutes",
        "total_time": "27 minutes",
        "ingredients": [
            "2¼ cups all-purpose flour",
            "1 cup butter, softened",
            "¾ cup brown sugar, packed",
            "¼ cup granulated sugar",
            "2 large eggs",
            "2 tsp vanilla extract",
            "2 cups chocolate chips",
            "1 tsp baking soda",
            "1 tsp salt"
        ],
        "steps": [
            "Preheat oven: Heat oven to 375°F. Line baking sheets with parchment paper.",
            "Cream butter and sugars: In large bowl, beat softened butter with both sugars using electric mixer until light and fluffy (3-4 minutes).",
            "Add eggs and vanilla: Beat in eggs one at a time, then vanilla extract until well combined.",
            "Mix dry ingredients: In separate bowl, whisk together flour, baking soda, and salt. Gradually blend into butter mixture.",
            "Fold in chocolate chips: Stir in chocolate chips until evenly distributed throughout dough.",
            "Bake cookies: Drop rounded tablespoons of dough 2 inches apart on prepared baking sheets. Bake 10-12 minutes until golden brown. Cool on baking sheet 2 minutes before removing to wire rack."
        ],
        "nutrition": {"calories": 280, "fat": 12, "carbs": 28, "protein": 3},
        "health_rating": "unhealthy"
    },
    {
        "id": "recipe_004",
        "name": "Greek Salad",
        "serving_size": "4 servings",
        "prep_time": "15 minutes",
        "cook_time": "0 minutes",
        "total_time": "15 minutes",
        "ingredients": [
            "2 large cucumbers, diced",
            "4 medium tomatoes, cut into wedges",
            "1 medium red onion, thinly sliced",
            "8 oz feta cheese, crumbled",
            "½ cup Kalamata olives, pitted",
            "¼ cup extra virgin olive oil",
            "2 tbsp red wine vinegar",
            "1 tsp dried oregano",
            "Salt and pepper to taste"
        ],
        "steps": [
            "Prepare vegetables: Wash and dice cucumbers into ½-inch pieces. Cut tomatoes into wedges and thinly slice red onion.",
            "Make dressing: In small bowl, whisk together olive oil, red wine vinegar, oregano, salt, and pepper.",
            "Combine ingredients: In large serving bowl, combine cucumbers, tomatoes, and red onion.",
            "Add cheese and olives: Crumble feta cheese over vegetables and add olives.",
            "Dress salad: Pour dressing over salad and toss gently to coat all ingredients.",
            "Serve immediately: Let salad rest 5 minutes for flavors to meld, then serve at room temperature. Best enjoyed fresh."
        ],
        "nutrition": {"calories": 320, "fat": 22, "carbs": 12, "protein": 8},
        "health_rating": "healthy"
    },
    {
        "id": "recipe_005",
        "name": "Beef Stir Fry",
        "serving_size": "4 servings",
        "prep_time": "20 minutes",
        "cook_time": "15 minutes",
        "total_time": "35 minutes",
        "ingredients": [
            "1 lb beef sirloin, cut into thin strips",
            "3 tbsp soy sauce, divided",
            "1 tbsp fresh ginger, minced",
            "3 cloves garlic, minced",
            "2 bell peppers, sliced",
            "1 large onion, sliced",
            "2 tbsp sesame oil",
            "2 cups cooked jasmine rice",
            "2 tbsp vegetable oil",
            "1 tbsp cornstarch",
            "2 green onions, chopped"
        ],
        "steps": [
            "Prepare rice: Cook jasmine rice according to package directions and keep warm.",
            "Marinate beef: In bowl, combine beef strips with 2 tbsp soy sauce, cornstarch, and half the minced ginger. Let marinate 15 minutes.",
            "Prep vegetables: While beef marinates, slice bell peppers and onion. Mince remaining ginger and garlic.",
            "Heat wok: Heat vegetable oil in large wok or skillet over high heat until smoking.",
            "Stir fry beef: Add marinated beef and cook 3-4 minutes until browned. Remove beef and set aside.",
            "Cook vegetables: Add sesame oil to wok. Stir fry onions and peppers 3-4 minutes until tender-crisp. Add garlic and remaining ginger, cook 30 seconds.",
            "Combine and serve: Return beef to wok with remaining soy sauce. Stir fry 1-2 minutes until heated through. Serve over rice, garnished with green onions."
        ],
        "nutrition": {"calories": 450, "fat": 10, "carbs": 35, "protein": 28},
        "health_rating": "healthy"
    },
    {
        "id": "recipe_006",
        "name": "Avocado Toast",
        "serving_size": "2 servings",
        "prep_time": "8 minutes",
        "cook_time": "2 minutes",
        "total_time": "10 minutes",
        "ingredients": [
            "4 slices sourdough bread",
            "2 large ripe avocados",
            "2 tbsp fresh lime juice",
            "½ tsp sea salt",
            "¼ tsp black pepper",
            "1 cup cherry tomatoes, halved",
            "2 tbsp olive oil",
            "Red pepper flakes (optional)",
            "Everything bagel seasoning (optional)"
        ],
        "steps": [
            "Toast bread: Toast sourdough slices until golden brown and crispy, about 1-2 minutes per side.",
            "Prepare avocado: Cut avocados in half, remove pits, and scoop flesh into medium bowl.",
            "Mash avocado: Add lime juice, salt, and pepper to avocados. Mash with fork until desired consistency (leave some chunks for texture).",
            "Prepare tomatoes: Halve cherry tomatoes and season lightly with salt.",
            "Assemble toast: Spread mashed avocado evenly on toasted bread slices.",
            "Add toppings: Top with cherry tomatoes, drizzle with olive oil, and sprinkle with red pepper flakes or everything seasoning if desired. Serve immediately."
        ],
        "nutrition": {"calories": 340, "fat": 18, "carbs": 25, "protein": 6},
        "health_rating": "healthy"
    },
    {
        "id": "recipe_007",
        "name": "Vegetable Curry",
        "serving_size": "6 servings",
        "prep_time": "15 minutes",
        "cook_time": "25 minutes",
        "total_time": "40 minutes",
        "ingredients": [
            "1 can (14 oz) coconut milk",
            "2 tbsp curry powder",
            "1 large onion, diced",
            "4 cloves garlic, minced",
            "2 tbsp fresh ginger, grated",
            "1 head cauliflower, cut into florets",
            "1 cup frozen peas",
            "2 large carrots, sliced",
            "½ cup fresh cilantro, chopped",
            "3 cups cooked basmati rice",
            "2 tbsp vegetable oil",
            "1 tsp salt",
            "1 can (14 oz) diced tomatoes"
        ],
        "steps": [
            "Prepare rice: Cook basmati rice according to package instructions and keep warm.",
            "Sauté aromatics: Heat oil in large pot over medium heat. Add diced onion and cook 5 minutes until softened.",
            "Add spices: Stir in minced garlic, grated ginger, and curry powder. Cook 1 minute until fragrant.",
            "Add coconut milk: Pour in coconut milk and diced tomatoes. Bring to gentle simmer.",
            "Cook vegetables: Add cauliflower florets and sliced carrots. Simmer 15-18 minutes until vegetables are tender.",
            "Finish curry: Stir in frozen peas and cook 2-3 minutes until heated through. Season with salt.",
            "Serve hot: Garnish with fresh cilantro and serve over basmati rice. Leftovers keep refrigerated 3-4 days."
        ],
        "nutrition": {"calories": 390, "fat": 16, "carbs": 42, "protein": 9},
        "health_rating": "healthy"
    },
    {
        "id": "recipe_008",
        "name": "Pancakes",
        "serving_size": "4 servings (12 pancakes)",
        "prep_time": "10 minutes",
        "cook_time": "15 minutes",
        "total_time": "25 minutes",
        "ingredients": [
            "2 cups all-purpose flour",
            "1¾ cups whole milk",
            "2 large eggs",
            "3 tbsp granulated sugar",
            "2 tsp baking powder",
            "1 tsp salt",
            "4 tbsp butter, melted, plus extra for griddle",
            "½ cup pure maple syrup",
            "1 tsp vanilla extract"
        ],
        "steps": [
            "Mix dry ingredients: In large bowl, whisk together flour, sugar, baking powder, and salt.",
            "Prepare wet ingredients: In separate bowl, whisk together milk, eggs, melted butter, and vanilla until smooth.",
            "Combine mixtures: Pour wet ingredients into dry ingredients and stir gently just until combined. Don't overmix - lumps are okay.",
            "Heat griddle: Preheat griddle or large skillet over medium heat. Brush with butter.",
            "Cook pancakes: Pour ¼ cup batter per pancake onto hot griddle. Cook until bubbles form on surface (2-3 minutes), then flip.",
            "Finish cooking: Cook second side 1-2 minutes until golden brown. Keep warm in 200°F oven.",
            "Serve with syrup: Stack pancakes on plates and serve immediately with warm maple syrup and extra butter if desired."
        ],
        "nutrition": {"calories": 350, "fat": 8, "carbs": 38, "protein": 7},
        "health_rating": "moderately_unhealthy"
    },
    {
        "id": "recipe_009",
        "name": "Caesar Salad",
        "serving_size": "4 servings",
        "prep_time": "20 minutes",
        "cook_time": "5 minutes",
        "total_time": "25 minutes",
        "ingredients": [
            "2 heads romaine lettuce, chopped",
            "½ cup parmesan cheese, freshly grated",
            "2 cups homemade croutons",
            "4 anchovy fillets",
            "2 cloves garlic, minced",
            "1 lemon, juiced",
            "2 tbsp mayonnaise",
            "1 tbsp Dijon mustard",
            "3 tbsp olive oil",
            "Black pepper to taste"
        ],
        "steps": [
            "Make croutons: Cut day-old bread into cubes, toss with olive oil and bake at 400°F for 5-7 minutes until golden.",
            "Prepare lettuce: Wash romaine thoroughly, dry completely, and chop into bite-sized pieces. Chill until ready to serve.",
            "Make dressing: In small bowl, mash anchovy fillets and garlic into paste. Whisk in lemon juice, mayonnaise, and Dijon mustard.",
            "Emulsify dressing: Slowly drizzle in olive oil while whisking constantly until smooth and creamy.",
            "Assemble salad: Place chilled romaine in large serving bowl. Add half the parmesan and croutons.",
            "Dress and serve: Pour dressing over lettuce and toss gently to coat. Top with remaining parmesan, croutons, and fresh black pepper. Serve immediately."
        ],
        "nutrition": {"calories": 310, "fat": 24, "carbs": 8, "protein": 12},
        "health_rating": "moderately_healthy"
    },
    {
        "id": "recipe_010",
        "name": "Smoothie Bowl",
        "serving_size": "2 servings",
        "prep_time": "10 minutes",
        "cook_time": "0 minutes",
        "total_time": "10 minutes",
        "ingredients": [
            "2 cups frozen mixed berries",
            "1 large banana, sliced and frozen",
            "1 cup fresh spinach leaves",
            "½ cup unsweetened almond milk",
            "2 tbsp chia seeds, divided",
            "½ cup granola",
            "3 tbsp coconut flakes",
            "1 fresh banana, sliced",
            "2 tbsp almond butter",
            "1 tbsp honey (optional)"
        ],
        "steps": [
            "Prepare frozen ingredients: Ensure berries and banana slices are completely frozen for best texture.",
            "Blend smoothie base: In high-speed blender, combine frozen berries, frozen banana, spinach, and almond milk.",
            "Achieve consistency: Blend until thick and creamy, adding more almond milk 1 tbsp at a time if needed. Mixture should be thicker than regular smoothie.",
            "Add chia seeds: Blend in 1 tbsp chia seeds for extra nutrition and texture.",
            "Pour into bowls: Divide smoothie mixture between 2 serving bowls.",
            "Add toppings: Arrange fresh banana slices, granola, coconut flakes, and remaining chia seeds on top.",
            "Serve immediately: Drizzle with almond butter and honey if desired. Serve with spoons and enjoy as a nutritious breakfast or snack."
        ],
        "nutrition": {"calories": 380, "fat": 14, "carbs": 32, "protein": 11},
        "health_rating": "very_healthy"
    }
]

@mcp.tool
def list_recipes():
    """Returns a list of all available recipes with their names and IDs."""
    return [{"id": recipe["id"], "name": recipe["name"]} for recipe in RECIPES]

@mcp.tool
def get_recipe(recipe_id: str):
    """Given a recipe ID, returns the complete recipe details including name, serving size, prep/cook times, ingredients with amounts, detailed steps, nutrition, and health rating."""
    for recipe in RECIPES:
        if recipe["id"] == recipe_id:
            return {
                "id": recipe["id"],
                "name": recipe["name"],
                "serving_size": recipe["serving_size"],
                "prep_time": recipe["prep_time"],
                "cook_time": recipe["cook_time"],
                "total_time": recipe["total_time"],
                "ingredients": recipe["ingredients"],
                "steps": recipe["steps"],
                "nutrition": recipe["nutrition"],
                "health_rating": recipe["health_rating"]
            }
    return {"error": f"Recipe with ID '{recipe_id}' not found"}

def main(transport="stdio", host="0.0.0.0", port=8723):
    if transport in ["sse", "streamable-http"]:
        mcp.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise Exception(f"Invalid parameters {transport=} {host=} {port=}")


if __name__ == "__main__":
    fire.Fire(main)
