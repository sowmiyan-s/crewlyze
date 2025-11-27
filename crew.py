# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License


import logging
import sys
import os
from pathlib import Path
import pandas as pd
import webbrowser
from dotenv import load_dotenv

load_dotenv()

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# API key validation is now handled by the LLM config module

try:
    from crewai import Crew
except ImportError as e:
    print(f"ERROR: {e}\nRun: pip install crewai")
    sys.exit(1)


def run_crew(csv_path: str):
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Cleanup existing visualizations
    for existing_file in output_dir.glob("*.png"):
        existing_file.unlink()
    print("Cleaned up previous visualizations.")
    
    print("=" * 50)
    print("Multi Agent Data Analysis with Crew AI")
    print("=" * 50)
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}")
        return None

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns[:10])}...")

    # Data Cleaning
    print("\n--- Starting Data Cleaning ---")
    df = df.drop_duplicates()
    
    # Fill numeric missing values with mean
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    
    # Fill categorical missing values with mode
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val[0])
            else:
                df[col] = df[col].fillna("Unknown")

    cleaned_file_path = Path("data") / "cleaned_csv.csv"
    # Ensure data directory exists
    cleaned_file_path.parent.mkdir(exist_ok=True)
    df.to_csv(cleaned_file_path, index=False)
    print(f"Cleaned dataset saved to {cleaned_file_path}")
    
    # Update dataset path for agents
    a = str(cleaned_file_path.absolute())
    print("--- Data Cleaning Complete ---\n")

    from agents.cleaner import cleaner_agent
    from agents.validator import validator_agent
    from agents.relation import relation_agent
    from agents.insights import insights_agent
    from workflows.pipeline import (
        clean_task,
        validate_task,
        relation_task,
        insight_task,
    )

    crew = Crew(
        agents=[
            cleaner_agent,
            validator_agent,
            relation_agent,
            insights_agent,
        ],
        tasks=[
            clean_task,
            validate_task,
            relation_task,
            insight_task,
        ],
        verbose=True,
    )

    try:
        result = crew.kickoff()
    except Exception as e:
        print(f"Error during crew execution: {e}")
        return {
            'dataframe': df,
            'cleaning_steps': "Error during analysis",
            'validation': "Error during analysis",
            'relations': "Error during analysis",
            'code': "Error during analysis",
            'insights': f"Analysis failed: {str(e)}",
            'output_dir': output_dir
        }
    

    task_outputs = {}
    
   
    if hasattr(crew, 'tasks'):
        for i, task in enumerate(crew.tasks):
            if hasattr(task, 'output') and task.output:
                task_name = task.description.split()[0].lower()
                if hasattr(task.output, 'raw'):
                    task_outputs[task_name] = str(task.output.raw)
                else:
                    task_outputs[task_name] = str(task.output)
    
 
    if hasattr(result, 'raw'):
        final_output = str(result.raw)
    else:
        final_output = str(result)
    
 
    clean_output = task_outputs.get('clean', '')
    validate_output = task_outputs.get('validate', 'The Coloums in the datasets are' + str(df.columns))
    relation_output = task_outputs.get('identify', 'The Coloums in the datasets are' + str(df.columns))
    code_output = task_outputs.get('generate', 'The Coloums in the datasets are' + str(df.columns) + "and the path to database is : " + a)
    insights_output = task_outputs.get('produce', final_output)
    

    # Generate visualizations directly (no LLM code generation)
    print("\n--- Generating Visualizations ---")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        plot_count = 0
        
        # 1. Distribution plots for numeric columns (top 3)
        for col in numeric_cols[:3]:
            try:
                plt.figure(figsize=(10, 6))
                sns.histplot(df[col].dropna(), kde=True)
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Frequency')
                plt.tight_layout()
                plt.savefig(output_dir / f'plot_{plot_count}.png', dpi=300, bbox_inches='tight')
                plt.close()
                plot_count += 1
                print(f"Generated distribution plot for {col}")
            except Exception as e:
                print(f"Error generating distribution plot for {col}: {e}")
                plt.close()
        
        # 2. Correlation heatmap if we have multiple numeric columns
        if len(numeric_cols) >= 2:
            try:
                plt.figure(figsize=(12, 8))
                correlation_matrix = df[numeric_cols].corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
                plt.title('Correlation Heatmap')
                plt.tight_layout()
                plt.savefig(output_dir / f'plot_{plot_count}.png', dpi=300, bbox_inches='tight')
                plt.close()
                plot_count += 1
                print("Generated correlation heatmap")
            except Exception as e:
                print(f"Error generating correlation heatmap: {e}")
                plt.close()
        
        # 3. Scatter plot for top 2 numeric columns
        if len(numeric_cols) >= 2:
            try:
                plt.figure(figsize=(10, 6))
                sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1], alpha=0.6)
                plt.title(f'{numeric_cols[0]} vs {numeric_cols[1]}')
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
                plt.tight_layout()
                plt.savefig(output_dir / f'plot_{plot_count}.png', dpi=300, bbox_inches='tight')
                plt.close()
                plot_count += 1
                print(f"Generated scatter plot: {numeric_cols[0]} vs {numeric_cols[1]}")
            except Exception as e:
                print(f"Error generating scatter plot: {e}")
                plt.close()
        
        # 4. Bar plot for categorical vs numeric (if available)
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            try:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                
                # Limit categories to top 10
                top_categories = df[cat_col].value_counts().head(10).index
                filtered_df = df[df[cat_col].isin(top_categories)]
                
                plt.figure(figsize=(12, 6))
                sns.barplot(data=filtered_df, x=cat_col, y=num_col, errorbar=None)
                plt.title(f'{num_col} by {cat_col}')
                plt.xlabel(cat_col)
                plt.ylabel(num_col)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(output_dir / f'plot_{plot_count}.png', dpi=300, bbox_inches='tight')
                plt.close()
                plot_count += 1
                print(f"Generated bar plot: {cat_col} vs {num_col}")
            except Exception as e:
                print(f"Error generating bar plot: {e}")
                plt.close()
        
        # 5. Box plot for categorical vs numeric
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            try:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0] if len(numeric_cols) > 1 else numeric_cols[0]
                
                # Limit categories
                top_categories = df[cat_col].value_counts().head(8).index
                filtered_df = df[df[cat_col].isin(top_categories)]
                
                plt.figure(figsize=(12, 6))
                sns.boxplot(data=filtered_df, x=cat_col, y=num_col)
                plt.title(f'{num_col} Distribution by {cat_col}')
                plt.xlabel(cat_col)
                plt.ylabel(num_col)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(output_dir / f'plot_{plot_count}.png', dpi=300, bbox_inches='tight')
                plt.close()
                plot_count += 1
                print(f"Generated box plot: {cat_col} vs {num_col}")
            except Exception as e:
                print(f"Error generating box plot: {e}")
                plt.close()
        
        print(f"--- Generated {plot_count} visualizations ---\n")
        
    except Exception as e:
        print(f"Error during visualization generation: {e}")
        plot_count = 0

    # Return structured data instead of HTML
    return {
        'dataframe': df,
        'cleaning_steps': clean_output,
        'validation': validate_output,
        'relations': relation_output,
        'code': f"Generated {plot_count} automatic visualizations based on data types",
        'insights': insights_output,
        'output_dir': output_dir
    }


if __name__ == "__main__":
    default_path = (Path.cwd() / "data" / "TB_Burden_Country.csv").resolve()
    a = input(f"Enter the path to your CSV file (default: {default_path.name}): ") or str(default_path)
    report = run_crew(a)
    if report:
        print("\nAnalysis Complete.")
        print("Multi Agent Data Analysis with Crew AI")
        print("Prithiv.A.K  Sebin.S  Sowmiyan.s")
