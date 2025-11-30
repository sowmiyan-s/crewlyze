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
