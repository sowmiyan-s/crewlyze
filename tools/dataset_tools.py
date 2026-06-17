import pandas as pd
from crewai.tools import tool

class DatasetTools:
    @tool("Read Dataset Head")
    def read_dataset_head(file_path: str):
        """Reads the first 10 rows of the dataset to understand its structure."""
        try:
            df = pd.read_csv(file_path)
            return df.head(10).to_markdown(index=False)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @tool("Get Dataset Info")
    def get_dataset_info(file_path: str):
        """Returns basic information about the dataset: columns, data types, and missing values."""
        try:
            df = pd.read_csv(file_path)
            info = []
            info.append(f"Shape: {df.shape}")
            info.append("\nColumns and Types:")
            for col, dtype in df.dtypes.items():
                missing = df[col].isnull().sum()
                info.append(f"- {col}: {dtype} (Missing: {missing})")
            return "\n".join(info)
        except Exception as e:
            return f"Error analyzing file: {str(e)}"

    @tool("Get Correlation Matrix")
    def get_correlation_matrix(file_path: str):
        """Calculates the correlation matrix for numeric columns."""
        try:
            df = pd.read_csv(file_path)
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.empty:
                return "No numeric columns found."
            return numeric_df.corr().to_markdown()
        except Exception as e:
            return f"Error calculating correlation: {str(e)}"

    @tool("Clean Dataset with Python Code")
    def clean_dataset_with_python(file_path: str, python_code: str):
        """Cleans the dataset at file_path by executing python_code on it.
        The code is executed with the variable `df` representing the pandas DataFrame of the dataset.
        Your python_code should perform modifications directly on `df` (e.g., df['col'] = df['col'].fillna(0)).
        Do NOT try to load or save the file in your code; the tool will load it before execution and save the result automatically.
        Ensure you only write the cleaning logic. Do NOT include markdown code blocks.
        """
        try:
            df = pd.read_csv(file_path)
            local_vars = {'df': df, 'pd': pd}
            clean_code = python_code.strip()
            if clean_code.startswith("```python"):
                clean_code = clean_code[9:]
            elif clean_code.startswith("```"):
                clean_code = clean_code[3:]
            if clean_code.endswith("```"):
                clean_code = clean_code[:-3]
            clean_code = clean_code.strip()
            
            exec(clean_code, globals(), local_vars)
            cleaned_df = local_vars.get('df', df)
            cleaned_df.to_csv(file_path, index=False)
            return "Dataset cleaned successfully."
        except Exception as e:
            return f"Error executing cleaning code: {str(e)}"

    @tool("Execute Visualization Code")
    def execute_visualization_code(python_code: str):
        """Executes Python code to generate and save visualizations to the 'outputs' directory.
        The code should generate plots (using matplotlib or seaborn) and save them as PNG files in the 'outputs' folder.
        Example:
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        df = pd.read_csv('data/cleaned_csv.csv')
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='column_x', y='column_y')
        plt.savefig('outputs/plot1.png', bbox_inches='tight', dpi=150)
        plt.close()
        """
        try:
            import os
            os.makedirs("outputs", exist_ok=True)
            clean_code = python_code.strip()
            if clean_code.startswith("```python"):
                clean_code = clean_code[9:]
            elif clean_code.startswith("```"):
                clean_code = clean_code[3:]
            if clean_code.endswith("```"):
                clean_code = clean_code[:-3]
            clean_code = clean_code.strip()
            
            exec(clean_code, globals())
            return "Visualization code executed successfully. Plots saved to 'outputs' directory."
        except Exception as e:
            return f"Error executing visualization code: {str(e)}"
