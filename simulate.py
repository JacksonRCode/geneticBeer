import random
from dataStrucs import Recipe, Malt, Hop
from database import IngredientDatabase
from fitness import fitness_distance, fitness_range_penalty

# ----- Load ingredient database -----
db = IngredientDatabase()
target = db.get_target_beer("IPA")  # Pick beer style
num_malts_in_recipe = 2
num_hops_in_recipe = 2


# ----- Create a single random recipe -----
malts = []
for i in range(num_malts_in_recipe):
    malt_dict = db.get_random_malt()

    malt = Malt(
        malt_dict["name"],
        malt_dict["yield_ppg"],
        malt_dict["color_srm"]
    )

    malts.append(malt)


hops = []
for i in range(num_hops_in_recipe):
    hop_dict = db.get_random_hop()

    hop = Hop(
        hop_dict["name"],
        hop_dict["alpha_acid_percent"]
    )

    hops.append(hop)

# Assign random masses and hop time
for m in malts:
    m.mass_lbs = random.uniform(5, 10)
for h in hops:
    h.mass_oz = random.uniform(0.5, 2)
    h.time_added_mins = random.choice([5, 15, 30, 60])

recipe = Recipe(malts, hops)

fitness_d = fitness_distance(recipe, target) #fitness based on regression strategy

target_range = {"og": (1.050, 1.080),"ibu": (55, 65), "srm": (5, 7)}
fitness_r = fitness_range_penalty(recipe, target_range) #fitness based on penalty strategy


print("Random Recipe Fitness Test")
print("**************************************************************")
print(f"Fitness (regression): {fitness_d}")
print(f"Fitness (penalty): {fitness_r}")
print(f"OG: {recipe.calculate_original_gravity()}")
print(f"IBU: {recipe.calculate_ibu()}")
print(f"SRM: {recipe.calculate_srm()}")