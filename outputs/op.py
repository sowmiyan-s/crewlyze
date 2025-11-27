# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
df = pd.read_csv('data/cleaned_csv.csv')

# Create figure
plt.figure(figsize=(10, 6))

# Generate plots using the column names from the relations task
for plot_data in [{"x": col_x, "y": col_y, "type": plot_type} for col_x, col_y, plot_type in [
    {"x": "col_1", "y": "col_2", "type": "scatter"},
    {"x": "col_3", "y": "col_4", "type": "scatter"},
    {"x": "col_5", "y": "time", "type": "line"},
    {"x": "col_6", "type": "bar"},
    {"x": "col_7", "type": "histogram"},
    {"x": "col_8", "y": "col_1", "type": "box"}
]]:
    if plot_type == "scatter":
        plt.scatter(df[col_x], df[col_y])
    elif plot_type == "line":
        plt.plot(df[col_x], df[col_y])
    elif plot_type == "bar":
        plt.bar(df[col_x])
    elif plot_type == "histogram":
        plt.hist(df[col_x])
    elif plot_type == "box":
        plt.boxplot([df[col_x]], vert=False)

# Save the plot
plt.savefig('outputs/plot.png', bbox_inches='tight', dpi=300)

# Close the plot
plt.close()