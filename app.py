"""
Streamlit web dashboard for interactive beer recipe evolution visualization.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from database import IngredientDatabase
from evolutionary_algorithm import EvolutionaryAlgorithm


# Page configuration
st.set_page_config(
    page_title="Genetic Beer Optimizer",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍺 Genetic Beer Recipe Optimizer")
st.markdown("Evolve the perfect beer recipe using genetic algorithms")

# Initialize session state
if "running" not in st.session_state:
    st.session_state.running = False
if "history" not in st.session_state:
    st.session_state.history = None
if "top_recipes" not in st.session_state:
    st.session_state.top_recipes = None

# Load database
db = IngredientDatabase()

# ===== SIDEBAR: Configuration =====
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Beer Style Selection
    st.subheader("Target Beer Style")
    available_styles = list(db.target_beers.keys())
    selected_style = st.selectbox(
        "Select a beer style:",
        options=available_styles,
        help="Choose a predefined beer style to target"
    )
    
    target_beer = db.target_beers[selected_style].copy()
    
    # Detect if target_beer uses ranges or point values
    is_range_format = isinstance(target_beer['og'], tuple)
    
    # Show target stats
    st.subheader("Target Range")
    if is_range_format:
        st.write(f"**OG:** {target_beer['og'][0]:.3f} - {target_beer['og'][1]:.3f}")
        st.write(f"**IBU:** {target_beer['ibu'][0]:.0f} - {target_beer['ibu'][1]:.0f}")
        st.write(f"**SRM:** {target_beer['srm'][0]:.1f} - {target_beer['srm'][1]:.1f}")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("OG", f"{target_beer['og']:.3f}")
        with col2:
            st.metric("IBU", f"{target_beer['ibu']:.1f}")
        with col3:
            st.metric("SRM", f"{target_beer['srm']:.1f}")
    
    st.write("---")
    
    # Custom ranges option
    st.subheader("Advanced Options")
    use_custom_ranges = st.checkbox(
        "Customize ranges",
        value=False,
        help="Adjust the acceptable ranges for this beer style"
    )
    
    if use_custom_ranges and is_range_format:
        st.write("**Acceptable Ranges:**")
        
        og_min, og_max = st.slider(
            "OG Range",
            min_value=1.0,
            max_value=1.15,
            value=target_beer['og'],
            step=0.005,
            format="%.3f"
        )
        
        ibu_min, ibu_max = st.slider(
            "IBU Range",
            min_value=0.0,
            max_value=100.0,
            value=target_beer['ibu'],
            step=1.0
        )
        
        srm_min, srm_max = st.slider(
            "SRM Range",
            min_value=0.0,
            max_value=40.0,
            value=target_beer['srm'],
            step=0.5
        )
        
        # Convert to range format
        target_beer_config = {
            "og": (og_min, og_max),
            "ibu": (ibu_min, ibu_max),
            "srm": (srm_min, srm_max)
        }
        fitness_strategy = "range_penalty"
    elif is_range_format:
        # Use ranges from beer_styles.csv
        target_beer_config = target_beer
        fitness_strategy = "range_penalty"
    else:
        # Use point values from targets.csv
        target_beer_config = target_beer
        fitness_strategy = "distance"
    
    st.write("---")
    
    # Algorithm Parameters
    st.subheader("Algorithm Parameters")
    
    population_size = st.slider(
        "Population Size (μ)",
        min_value=10,
        max_value=100,
        value=50,
        step=5,
        help="Number of recipes in each generation"
    )
    
    num_generations = st.slider(
        "Number of Generations",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
        help="How many generations to evolve"
    )
    
    tournament_size = st.slider(
        "Tournament Size (k)",
        min_value=2,
        max_value=10,
        value=4,
        step=1,
        help="Number of random competitors in tournament selection"
    )
    
    st.write("---")
    
    # Ingredient Configuration
    st.subheader("Recipe Composition")
    
    st.write("**Malts per Recipe (range):**")
    min_malts, max_malts = st.slider(
        "Malts",
        min_value=1,
        max_value=5,
        value=(1, 4),
        step=1,
        help="Range of malt varieties per recipe"
    )
    
    st.write("**Hops per Recipe (range):**")
    min_hops, max_hops = st.slider(
        "Hops",
        min_value=1,
        max_value=5,
        value=(1, 4),
        step=1,
        help="Range of hop additions per recipe"
    )
    
    st.write("---")
    
    # Results Configuration
    st.subheader("Results")
    
    top_n_results = st.slider(
        "Show Top N Recipes",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Number of best recipes to display"
    )
    
    st.write("---")
    
    # Run button
    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("🚀 Start Evolution")
    with col2:
        clear_button = st.button("🔄 Clear Results")


# ===== MAIN CONTENT =====

if clear_button:
    st.session_state.history = None
    st.session_state.top_recipes = None
    st.experimental_rerun()

if start_button:
    st.session_state.running = True
    
    # Create progress placeholder
    progress_container = st.container()
    status_placeholder = progress_container.empty()
    progress_placeholder = progress_container.empty()
    
    # Initialize EA
    ea = EvolutionaryAlgorithm(
        target_beer=target_beer_config,
        population_size=population_size,
        num_generations=num_generations,
        fitness_strategy=fitness_strategy,
        min_malts=min_malts,
        max_malts=max_malts,
        min_hops=min_hops,
        max_hops=max_hops,
        tournament_size=tournament_size,
        top_n_results=top_n_results,
        ingredient_db=db
    )
    
    # Progress tracking
    def progress_callback(generation, best_fitness, avg_fitness, best_recipe, diversity):
        progress = generation / num_generations
        progress_placeholder.progress(progress)
        status_placeholder.info(f"Generation {generation}/{num_generations} | Best: {best_fitness:.4f} | Avg: {avg_fitness:.4f} | Diversity: {diversity:.4f}")
    
    # Run the algorithm
    top_recipes, history = ea.run(callback=progress_callback)
    
    # Store results
    st.session_state.history = history
    st.session_state.top_recipes = top_recipes
    st.session_state.running = False
    
    # Clear progress indicators
    progress_placeholder.empty()
    status_placeholder.empty()
    
    # Success message
    progress_container.success("✅ Evolution Complete!")


# ===== RESULTS DISPLAY =====

if st.session_state.history and st.session_state.top_recipes:
    st.write("---")
    st.header("📊 Results")
    
    history = st.session_state.history
    top_recipes = st.session_state.top_recipes
    best_recipe = top_recipes[0]
    
    # Display convergence info
    st.subheader("🎯 Evolution Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        if history['converged']:
            st.metric("Status", "✅ Converged", f"Gen {history['generations_to_convergence']}")
        else:
            st.metric("Status", "⏹️ Stopped", f"Gen {history['generations']}")
    with col2:
        avg_diversity = sum(history['diversity']) / len(history['diversity']) if history['diversity'] else 0
        st.metric(
            "Avg Recipe Diversity", 
            f"{avg_diversity:.4f}",
            help="Average distance between recipes in OG/IBU/SRM space (higher = more diverse)"
        )
    with col3:
        st.metric("Final Fitness", f"{best_recipe.fitness_score:.4f}", help="Lower is better")
    
    # Add explanation about recipe similarity
    if len(top_recipes) > 1:
        fitness_scores = [r.fitness_score for r in top_recipes]
        max_diff = max(fitness_scores) - min(fitness_scores)
        
        if max_diff < 0.001:
            st.info(
                "ℹ️ **Top recipes have very similar fitness scores** (diff < 0.001). "
                "This is expected when the algorithm converges—multiple recipes can achieve nearly the same quality. "
                "They may differ in specific ingredients but produce equivalent beer profiles."
            )
    
    st.write("---")
    
    # Create visualizations
    st.subheader("📈 Fitness & Diversity Evolution")
    
    best_fitness_list = list(history['best_fitness'])
    avg_fitness_list = list(history['avg_fitness'])
    diversity_list = list(history['diversity']) if 'diversity' in history else []
    generations = list(range(len(best_fitness_list)))
    
    # Create line chart with scatter points and secondary y-axis for diversity
    from plotly.subplots import make_subplots
    fig_fitness = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add best fitness trace
    fig_fitness.add_trace(go.Scatter(
        x=generations,
        y=best_fitness_list,
        mode='lines+markers',
        name='Best Fitness',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=5),
        hovertemplate='Generation: %{x}<br>Best Fitness: %{y:.4f}<extra></extra>'
    ), secondary_y=False)
    
    # Add average fitness trace
    fig_fitness.add_trace(go.Scatter(
        x=generations,
        y=avg_fitness_list,
        mode='lines',
        name='Average Fitness',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        hovertemplate='Generation: %{x}<br>Avg Fitness: %{y:.4f}<extra></extra>'
    ), secondary_y=False)
    
    # Add diversity trace on secondary axis
    if diversity_list:
        fig_fitness.add_trace(go.Scatter(
            x=generations,
            y=diversity_list,
            mode='lines',
            name='Recipe Diversity',
            line=dict(color='#2ca02c', width=2),
            hovertemplate='Generation: %{x}<br>Recipe Diversity: %{y:.4f}<extra></extra>'
        ), secondary_y=True)
    
    fig_fitness.update_xaxes(title_text="Generation")
    fig_fitness.update_yaxes(title_text="Fitness (lower is better)", secondary_y=False)
    if diversity_list:
        fig_fitness.update_yaxes(title_text="Recipe Diversity (OG/IBU/SRM distance)", secondary_y=True)
    
    fig_fitness.update_layout(
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig_fitness)
    
    st.write("---")
    
    # 3D Trajectory Plot - Show how OG, IBU, SRM evolved
    st.subheader("🌐 Recipe Evolution in 3D Space")
    
    # Extract OG, IBU, SRM from best recipes across generations
    og_trajectory = []
    ibu_trajectory = []
    srm_trajectory = []
    
    for best_recipe_gen in history.get('best_recipe_history', [best_recipe]):
        og_trajectory.append(best_recipe_gen.calculate_original_gravity())
        ibu_trajectory.append(best_recipe_gen.calculate_ibu())
        srm_trajectory.append(best_recipe_gen.calculate_srm())
    
    # If we only have the final recipe, also show it in 3D
    if len(og_trajectory) == 0:
        og_trajectory = [best_recipe.calculate_original_gravity()]
        ibu_trajectory = [best_recipe.calculate_ibu()]
        srm_trajectory = [best_recipe.calculate_srm()]
    
    # Create 3D scatter plot with better color gradient and target marker
    fig_3d = go.Figure()
    
    # Get target values - handle both range and point formats
    if isinstance(target_beer_config['og'], tuple):
        target_og = (target_beer_config['og'][0] + target_beer_config['og'][1]) / 2
        target_ibu = (target_beer_config['ibu'][0] + target_beer_config['ibu'][1]) / 2
        target_srm = (target_beer_config['srm'][0] + target_beer_config['srm'][1]) / 2
    else:
        target_og = target_beer_config['og']
        target_ibu = target_beer_config['ibu']
        target_srm = target_beer_config['srm']
    
    # Plot trajectory with generation-based colors
    gen_colors = generations[:len(og_trajectory)]
    
    # Add trajectory line
    fig_3d.add_trace(go.Scatter3d(
        x=og_trajectory,
        y=ibu_trajectory,
        z=srm_trajectory,
        mode='lines',
        line=dict(
            color=gen_colors,
            colorscale='Plasma',
            width=4,
            showscale=False
        ),
        name='Evolution Path',
        hoverinfo='skip'
    ))
    
    # Add generation points with color gradient
    fig_3d.add_trace(go.Scatter3d(
        x=og_trajectory,
        y=ibu_trajectory,
        z=srm_trajectory,
        mode='markers',
        marker=dict(
            size=7,
            color=gen_colors,
            colorscale='Plasma',
            colorbar=dict(title="Generation", thickness=15, len=0.7),
            showscale=True,
            line=dict(color='white', width=1)
        ),
        text=[f"Gen {g}<br>OG: {og:.3f}<br>IBU: {ib:.1f}<br>SRM: {sr:.1f}" 
              for g, og, ib, sr in zip(gen_colors, og_trajectory, ibu_trajectory, srm_trajectory)],
        hovertemplate='<b>%{text}</b><extra></extra>',
        name='Recipe Generations'
    ))
    
    # Add target point as a larger marker
    fig_3d.add_trace(go.Scatter3d(
        x=[target_og],
        y=[target_ibu],
        z=[target_srm],
        mode='markers+text',
        marker=dict(
            size=12,
            color='red',
            symbol='diamond',
            line=dict(color='darkred', width=2)
        ),
        text=['TARGET'],
        textposition='top center',
        name='Target Style',
        hovertemplate='<b>Target Style</b><br>OG: %{x:.3f}<br>IBU: %{y:.1f}<br>SRM: %{z:.1f}<extra></extra>'
    ))
    
    fig_3d.update_layout(
        title="🌐 Recipe Evolution in 3D Space (OG, IBU, SRM)",
        scene=dict(
            xaxis_title='Original Gravity (OG)',
            yaxis_title='Bitterness (IBU)',
            zaxis_title='Color (SRM)',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3)
            )
        ),
        height=600,
        showlegend=True,
        legend=dict(x=0.02, y=0.98)
    )
    st.plotly_chart(fig_3d)
    
    st.write("---")
    
    # Top Recipes Display
    st.subheader(f"🍻 Top {len(top_recipes)} Recipe(s)")
    
    # Create tabs for each top recipe
    recipe_counts = history.get('recipe_counts', {})
    tab_labels = []
    for i, recipe in enumerate(top_recipes):
        count = recipe_counts.get(id(recipe), 1)
        count_str = f" ({count} candidate{'s' if count != 1 else ''})" if count > 1 else ""
        tab_labels.append(f"Recipe #{i+1}{count_str}")
    
    recipe_tabs = st.tabs(tab_labels)
    
    for tab_idx, tab in enumerate(recipe_tabs):
        with tab:
            recipe = top_recipes[tab_idx]
            count = recipe_counts.get(id(recipe), 1)
            og = recipe.calculate_original_gravity()
            ibu = recipe.calculate_ibu()
            srm = recipe.calculate_srm()
            
            # Display candidate count if multiple match this recipe
            if count > 1:
                st.info(f"📊 **{count} candidates in the final population match this recipe** (within tolerance)")
            
            # Display as metrics in a clean row
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            # Format target display
            if isinstance(target_beer['og'], tuple):
                og_target = f"{target_beer['og'][0]:.3f}-{target_beer['og'][1]:.3f}"
                ibu_target = f"{target_beer['ibu'][0]:.0f}-{target_beer['ibu'][1]:.0f}"
                srm_target = f"{target_beer['srm'][0]:.1f}-{target_beer['srm'][1]:.1f}"
            else:
                og_target = f"Target: {target_beer['og']:.3f}"
                ibu_target = f"Target: {target_beer['ibu']:.1f}"
                srm_target = f"Target: {target_beer['srm']:.1f}"
            
            with metric_col1:
                st.metric(
                    "Original Gravity",
                    f"{og:.3f}",
                    og_target
                )
            
            with metric_col2:
                st.metric(
                    "IBU",
                    f"{ibu:.1f}",
                    ibu_target
                )
            
            with metric_col3:
                st.metric(
                    "Color (SRM)",
                    f"{srm:.1f}",
                    srm_target
                )
            
            with metric_col4:
                st.metric(
                    "Fitness Score",
                    f"{recipe.fitness_score:.4f}",
                    "Lower is better"
                )
            
            # Malt Bill
            st.subheader("Malt Bill")
            malt_data = []
            for malt in recipe.malts:
                malt_data.append({
                    "Grain": malt.name,
                    "Mass (lbs)": f"{malt.mass_lbs:.2f}",
                    "Yield (PPG)": malt.yield_ppg,
                    "Color (SRM)": malt.color_srm
                })
            
            if malt_data:
                df_malts = pd.DataFrame(malt_data)
                st.dataframe(df_malts)
            
            # Hop Schedule
            st.subheader("Hop Schedule")
            hop_data = []
            for hop in recipe.hops:
                hop_data.append({
                    "Hop": hop.name,
                    "Amount (oz)": f"{hop.mass_oz:.2f}",
                    "Boil Time (min)": hop.time_added_mins,
                    "Alpha Acid %": hop.alpha_acid_percent
                })
            
            if hop_data:
                df_hops = pd.DataFrame(hop_data)
                st.dataframe(df_hops)
            
            # Download button for this recipe
            if isinstance(target_beer['og'], tuple):
                target_og_str = f"{target_beer['og'][0]:.3f} - {target_beer['og'][1]:.3f}"
                target_ibu_str = f"{target_beer['ibu'][0]:.0f} - {target_beer['ibu'][1]:.0f}"
                target_srm_str = f"{target_beer['srm'][0]:.1f} - {target_beer['srm'][1]:.1f}"
            else:
                target_og_str = f"{target_beer['og']:.3f}"
                target_ibu_str = f"{target_beer['ibu']:.1f}"
                target_srm_str = f"{target_beer['srm']:.1f}"
            
            recipe_text = f"""
# {selected_style} Recipe #{tab_idx+1}

## Target Style
- OG: {target_og_str}
- IBU: {target_ibu_str}
- SRM: {target_srm_str}

## Generated Recipe
- OG: {og:.3f}
- IBU: {ibu:.1f}
- SRM: {srm:.1f}
- Fitness: {recipe.fitness_score:.4f}

## Malt Bill
"""
            for malt in recipe.malts:
                recipe_text += f"- {malt.name}: {malt.mass_lbs:.2f} lbs\n"
            
            recipe_text += "\n## Hop Schedule\n"
            for hop in recipe.hops:
                recipe_text += f"- {hop.name}: {hop.mass_oz:.2f} oz @ {hop.time_added_mins} min\n"
            
            st.download_button(
                label=f"📥 Download Recipe #{tab_idx+1}",
                data=recipe_text,
                file_name=f"{selected_style.replace(' ', '_')}_recipe_{tab_idx+1}.md",
                mime="text/markdown"
            )

else:
    st.info("👈 Configure parameters in the sidebar and click 'Start Evolution' to begin optimizing recipes!")
