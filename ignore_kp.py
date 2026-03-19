# simulate.py
from evolutionary_algorithm import EvolutionaryAlgorithm  # your EA class file
from database import IngredientDatabase  # your ingredient DB
import random

def main():
    # Define a target beer style as ranges for the penalty function
    target_beer_range = {
        "og": (1.045, 1.055),   # Original Gravity range
        "ibu": (30, 40),        # Bitterness range
        "srm": (8, 12)          # Color range
    }

    # Create ingredient database instance
    ingredient_db = IngredientDatabase()

    # Initialize the evolutionary algorithm with range_penalty
    ea = EvolutionaryAlgorithm(
        target_beer=target_beer_range,
        population_size=10,       # small population for testing
        num_generations=5,        # few generations for quick test
        fitness_strategy="range_penalty",  # use penalty fitness
        num_malts=2,
        num_hops=2,
        ingredient_db=ingredient_db
    )

    # Optional callback to print best recipe each generation
    def print_generation_stats(generation, best_fitness, avg_fitness, best_recipe):
        print(f"\n--- Generation {generation} ---")
        print(f"Best Fitness (penalty): {best_fitness:.4f} | Avg Fitness: {avg_fitness:.4f}")
        print("Best Recipe:")
        print("Malts:")
        for malt in best_recipe.malts:
            print(f"  {malt.name}, {malt.mass_lbs:.2f} lbs, {malt.color_srm} SRM")
        print("Hops:")
        for hop in best_recipe.hops:
            print(f"  {hop.name}, {hop.mass_oz:.2f} oz, {hop.alpha_acid_percent}% AA, {hop.time_added_mins} min")

    # Run the EA
    best_recipe, history = ea.run(callback=print_generation_stats)

    # Final best recipe summary
    print("\n=== FINAL BEST RECIPE ===")
    print(f"Fitness (penalty): {best_recipe.fitness_score:.4f}")
    print("Malts:")
    for malt in best_recipe.malts:
        print(f"  {malt.name}, {malt.mass_lbs:.2f} lbs, {malt.color_srm} SRM")
    print("Hops:")
    for hop in best_recipe.hops:
        print(f"  {hop.name}, {hop.mass_oz:.2f} oz, {hop.alpha_acid_percent}% AA, {hop.time_added_mins} min")

if __name__ == "__main__":
    main()