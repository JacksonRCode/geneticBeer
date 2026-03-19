# 🍺 Genetic Beer Optimizer - Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Web Dashboard

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```
   This will open your browser to `http://localhost:8501`

2. **The dashboard allows you to:**
   - **Select a target beer style** (IPA, Stout, Pilsner, Amber Ale)
   - **Enable custom target ranges** instead of exact values
   - **Adjust algorithm parameters:**
     - Population size (how many recipes per generation)
     - Number of generations (evolution iterations)
     - Number of malts and hops per recipe
   
3. **Click "🚀 Start Evolution"** to begin the optimization

4. **Watch in real-time:**
   - Progress bar showing generation completion
   - Fitness improvement across generations
   - Best recipe details and metrics
   - Ingredient selections

5. **Download your recipe** as a text file when complete!

## Features

### Real-Time Visualization
- **Fitness Evolution Chart**: Shows best and average fitness improving over generations
- **Gauge Charts**: Visual representation of OG, IBU, and SRM metrics
- **Malt Bill Table**: Exact grain selections and amounts
- **Hop Schedule Table**: Hop varieties, amounts, and boil times

### Two Fitness Strategies
- **Distance Strategy** (default): Minimizes squared distance to exact target values
- **Range Penalty Strategy**: Penalizes any values outside acceptable ranges

### Recipe Details
Each recipe displays:
- Original Gravity (OG) - sugar density
- IBU (Bitterness) - calculated via Tinseth formula
- SRM (Color) - calculated via Morey equation
- Complete malt bill with yields and colors
- Complete hop schedule with alpha acids and timing

## Behind the Scenes

### How It Works
1. **Initialization**: Creates a random population of recipes
2. **Fitness Evaluation**: Scores each recipe based on similarity to target
3. **Parent Selection**: Tournament selection picks best recipes to breed
4. **Variation**: 
   - **Recombination**: Swaps ingredients between parents
   - **Mutation**: Randomly adjusts amounts, boil times, and varieties
5. **Survivor Selection**: Keeps the best offspring for the next generation
6. **Repeat**: Generations evolve toward optimal recipes

### Key Files
- `app.py` - Interactive Streamlit dashboard
- `evolutionary_algorithm.py` - Main GA orchestration
- `dataStrucs.py` - Recipe, Malt, Hop classes
- `fitness.py` - Fitness evaluation functions
- `selection.py` - Parent and survivor selection
- `variation/` - Recombination and mutation operators
- `database.py` - Ingredient database
- `*.csv` - Ingredient and target beer data

## Tips for Best Results

1. **Start with more generations** (~100) for better convergence
2. **Use larger population sizes** (50+) for diversity, especially early on
3. **Enable custom ranges** if you're satisfied with approximate styles
4. **Experiment with different beer styles** to understand the algorithm's behavior
5. **Watch the fitness curve** - it should show improvement over time

## More Information

See `README.md` for details on the project architecture and team information.
