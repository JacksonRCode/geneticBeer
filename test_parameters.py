"""
Parameter Testing and Algorithm Performance Evaluation
Tests different EA parameter combinations to find optimal settings.

Run with: python test_parameters.py
"""

import time
import json
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime

from evolutionary_algorithm import EvolutionaryAlgorithm
from database import IngredientDatabase


class ParameterTester:
    """Tests different parameter configurations and evaluates EA performance."""
    
    def __init__(self):
        self.db = IngredientDatabase()
        self.results = []
    
    def run_single_experiment(self, config: Dict, num_runs: int = 10) -> Dict:
        """
        Run a single configuration multiple times and average results.
        
        Args:
            config: Parameter configuration to test
            num_runs: Number of times to run this config
        
        Returns:
            Dictionary with aggregated results
        """
        print(f"\n{'='*70}")
        print(f"Testing Config: {config['name']}")
        print(f"{'='*70}")
        
        run_results = []
        
        # Prepare target_beer format based on fitness strategy
        target_beer = config['target_beer'].copy()
        fitness_strategy = config['fitness_strategy']
        
        # Convert target beer format if needed
        is_range_format = isinstance(target_beer['og'], tuple)
        
        if fitness_strategy == "range_penalty" and not is_range_format:
            # Convert point values to ranges
            target_beer_prepared = {
                "og": (target_beer['og'] * 0.95, target_beer['og'] * 1.05),
                "ibu": (max(0, target_beer['ibu'] * 0.9), target_beer['ibu'] * 1.1),
                "srm": (max(0, target_beer['srm'] * 0.9), target_beer['srm'] * 1.1)
            }
        elif fitness_strategy == "distance" and is_range_format:
            # Convert ranges to point values (midpoints)
            target_beer_prepared = {
                "og": (target_beer['og'][0] + target_beer['og'][1]) / 2,
                "ibu": (target_beer['ibu'][0] + target_beer['ibu'][1]) / 2,
                "srm": (target_beer['srm'][0] + target_beer['srm'][1]) / 2
            }
        else:
            # Format already matches strategy
            target_beer_prepared = target_beer
        
        for run_num in range(num_runs):
            print(f"  Run {run_num + 1}/{num_runs}...", end=" ", flush=True)
            
            start_time = time.time()
            
            # Initialize EA with config
            ea = EvolutionaryAlgorithm(
                target_beer=target_beer_prepared,
                population_size=config['population_size'],
                num_generations=config['num_generations'],
                fitness_strategy=fitness_strategy,
                min_malts=config['min_malts'],
                max_malts=config['max_malts'],
                min_hops=config['min_hops'],
                max_hops=config['max_hops'],
                tournament_size=config['tournament_size'],
                top_n_results=1,
                convergence_generations=config.get('convergence_generations', 20),
                ingredient_db=self.db
            )
            
            # Run algorithm
            top_recipes, history = ea.run()
            
            elapsed_time = time.time() - start_time
            
            # Extract metrics
            result = {
                'run': run_num + 1,
                'final_fitness': history['best_recipe'].fitness_score,
                'generations_actual': history['generations'],
                'converged': history['converged'],
                'generations_to_convergence': history['generations_to_convergence'] or history['generations'],
                'avg_diversity': sum(history['diversity']) / len(history['diversity']) if history['diversity'] else 0,
                'time_seconds': elapsed_time
            }
            
            run_results.append(result)
            
            og = top_recipes[0].calculate_original_gravity()
            ibu = top_recipes[0].calculate_ibu()
            srm = top_recipes[0].calculate_srm()
            print(f"Fitness: {result['final_fitness']:.4f} | OG: {og:.3f} | IBU: {ibu:.1f} | SRM: {srm:.1f} | Time: {elapsed_time:.1f}s")
        
        # Aggregate runs
        aggregated = {
            'config_name': config['name'],
            'config': config,
            'num_runs': num_runs,
            'final_fitness_avg': sum(r['final_fitness'] for r in run_results) / num_runs,
            'final_fitness_std': (sum((r['final_fitness'] - sum(r['final_fitness'] for r in run_results)/num_runs)**2 for r in run_results) / num_runs) ** 0.5,
            'final_fitness_best': min(r['final_fitness'] for r in run_results),
            'generations_avg': sum(r['generations_actual'] for r in run_results) / num_runs,
            'convergence_rate': sum(1 for r in run_results if r['converged']) / num_runs,
            'convergence_speed_avg': sum(r['generations_to_convergence'] for r in run_results) / num_runs,
            'avg_diversity_avg': sum(r['avg_diversity'] for r in run_results) / num_runs,
            'time_avg': sum(r['time_seconds'] for r in run_results) / num_runs,
            'individual_runs': run_results
        }
        
        return aggregated
    
    def run_experiments(self, configurations: List[Dict], num_runs: int = 10):
        """
        Run all parameter configurations.
        
        Args:
            configurations: List of parameter configurations to test
            num_runs: Number of runs per configuration
        """
        print("\n" + "="*70)
        print("PARAMETER TESTING AND PERFORMANCE EVALUATION")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(configurations)} configurations with {num_runs} runs each")
        print(f"Total experiments: {len(configurations) * num_runs}")
        
        for config in configurations:
            result = self.run_single_experiment(config, num_runs)
            self.results.append(result)
    
    def print_summary(self):
        """Print summary of all results."""
        print("\n" + "="*70)
        print("RESULTS SUMMARY")
        print("="*70 + "\n")
        
        # Create summary dataframe
        summary_data = []
        for result in self.results:
            cfg = result['config']
            summary_data.append({
                'Config': result['config_name'],
                'Pop Size': cfg['population_size'],
                'Tournament K': cfg['tournament_size'],
                'Min/Max Malts': f"{cfg['min_malts']}-{cfg['max_malts']}",
                'Min/Max Hops': f"{cfg['min_hops']}-{cfg['max_hops']}",
                'Fitness (Avg)': f"{result['final_fitness_avg']:.4f}",
                'Fitness (Best)': f"{result['final_fitness_best']:.4f}",
                'Convergence Rate': f"{result['convergence_rate']*100:.0f}%",
                'Conv. Speed (Gens)': f"{result['convergence_speed_avg']:.1f}",
                'Avg Diversity': f"{result['avg_diversity_avg']:.4f}",
                'Time (s)': f"{result['time_avg']:.2f}"
            })
        
        df = pd.DataFrame(summary_data)
        print(df.to_string(index=False))
        print()
    
    def find_best_config(self) -> Dict:
        """Find the best configuration based on fitness."""
        best = min(self.results, key=lambda x: x['final_fitness_avg'])
        print("\n" + "="*70)
        print("BEST CONFIGURATION")
        print("="*70)
        print(f"Name: {best['config_name']}")
        print(f"Final Fitness (avg): {best['final_fitness_avg']:.4f} ± {best['final_fitness_std']:.4f}")
        print(f"Best Fitness: {best['final_fitness_best']:.4f}")
        print(f"Convergence Rate: {best['convergence_rate']*100:.0f}%")
        print(f"Avg Convergence Speed: {best['convergence_speed_avg']:.1f} generations")
        print(f"Avg Diversity: {best['avg_diversity_avg']:.4f}")
        print(f"Avg Time: {best['time_avg']:.2f} seconds")
        print(f"\nParameters:")
        for key, value in best['config'].items():
            if key not in ['name', 'target_beer']:
                print(f"  {key}: {value}")
        print()
        return best
    
    def save_results(self, filename: str = "parameter_test_results.json"):
        """Save detailed results to JSON file."""
        # Convert to serializable format
        serializable_results = []
        for result in self.results:
            result_copy = result.copy()
            # Remove complex objects
            result_copy.pop('individual_runs', None)
            result_copy.pop('config', None)
            serializable_results.append(result_copy)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to {filename}")


def create_test_configurations(db: IngredientDatabase) -> List[Dict]:
    """
    Create a set of parameter configurations to test.
    Modify this function to experiment with different parameters.
    """
    
    # Get a target beer for testing
    test_beer = db.target_beers.get("American Light Lager", db.target_beers[list(db.target_beers.keys())[0]])
    
    configurations = [
        # Baseline: moderate parameters
        {
            'name': 'Baseline (50 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Larger population
        {
            'name': 'Large Population (100 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 100,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Smaller population (faster)
        {
            'name': 'Small Population (30 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 30,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Higher tournament size (more selective)
        {
            'name': 'High Selection (50 pop, k=5)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 5,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Lower tournament size (less selective)
        {
            'name': 'Low Selection (50 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # More variation in ingredients
        {
            'name': 'High Variation (50 pop, 1-5 malts/hops)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 5,
            'min_hops': 1,
            'max_hops': 5,
            'convergence_generations': 20
        },
        
        # Less variation in ingredients
        {
            'name': 'Low Variation (50 pop, 2-3 malts/hops)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 2,
            'min_malts': 2,
            'max_malts': 3,
            'min_hops': 2,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Distance fitness function
        {
            'name': 'Distance Function (50 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Aggressive convergence
        {
            'name': 'Aggressive Conv. (50 pop, k=5, high conv threshold)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'range_penalty',
            'tournament_size': 5,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 10
        },
        
        # Baseline: moderate parameters
        {
            'name': 'Baseline (50 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Larger population
        {
            'name': 'Large Population (100 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 100,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Smaller population (faster)
        {
            'name': 'Small Population (30 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 30,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Higher tournament size (more selective)
        {
            'name': 'High Selection (50 pop, k=5)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 5,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Lower tournament size (less selective)
        {
            'name': 'Low Selection (50 pop, k=2)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # More variation in ingredients
        {
            'name': 'High Variation (50 pop, 1-5 malts/hops)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 1,
            'max_malts': 5,
            'min_hops': 1,
            'max_hops': 5,
            'convergence_generations': 20
        },
        
        # Less variation in ingredients
        {
            'name': 'Low Variation (50 pop, 2-3 malts/hops)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 2,
            'min_malts': 2,
            'max_malts': 3,
            'min_hops': 2,
            'max_hops': 3,
            'convergence_generations': 20
        },
        
        # Aggressive convergence
        {
            'name': 'Aggressive Conv. (50 pop, k=5, high conv threshold)',
            'target_beer': test_beer,
            'population_size': 50,
            'num_generations': 100,
            'fitness_strategy': 'distance',
            'tournament_size': 5,
            'min_malts': 1,
            'max_malts': 3,
            'min_hops': 1,
            'max_hops': 3,
            'convergence_generations': 10
        },
    ]
    
    return configurations


if __name__ == "__main__":
    # Initialize database
    db = IngredientDatabase()
    
    # Create parameter configurations
    configs = create_test_configurations(db)
    
    # Run experiments
    tester = ParameterTester()
    tester.run_experiments(configs, num_runs=10)
    
    # Print results
    tester.print_summary()
    best = tester.find_best_config()
    
    # Save detailed results
    tester.save_results()
    
    print("\n✅ Parameter testing complete!")
