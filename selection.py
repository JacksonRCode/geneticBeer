import random
import copy

def tournament_selection(population, k=2):
    """
    Parent Selection
    Pick k random recipes, return the one with the highest fitness (min square error)
    """
    candidate_solutions = random.sample(population, k)
    best_recipe = candidate_solutions[0]
    for recipe in candidate_solutions[1:]:
        if recipe.fitness_score < best_recipe.fitness_score:
            best_recipe = recipe
    return best_recipe
        
def survivor_selection(parents, offspring, mu):
    """
    (μ, λ) strategy: Select the best μ individuals from the offspring only.
    Lower fitness (error) is better.
    """
    # Make a copy so we don't modify the original list
    unselected_offspring = copy.deepcopy(offspring)
    selected_next_gen = []

    for parent_to_be_replaced in range(mu):
        # Find the individual with the lowest fitness
        best_offspring = unselected_offspring[0]
        for recipe in unselected_offspring[1:]:
            if recipe.fitness_score < best_offspring.fitness_score:
                best_offspring = recipe

        # Add the best to selected list
        selected_next_gen.append(best_offspring)
        # Remove from remaining so we don't pick it again
        unselected_offspring.remove(best_offspring)

    return selected_next_gen


