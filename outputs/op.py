# Import necessary libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
data = pd.read_csv('data/cleaned_csv.csv')

# Define a function to create plots
def create_plots(relations):
    for relation in relations:
        if 'y' in relation:
            if relation['type'] == 'scatter':
                # Create scatter plot
                sns.scatterplot(x=relation['x'], y=relation['y'], data=data)
                plt.title(f'Scatter Plot of {relation["x"]} vs {relation["y"]}')
                plt.show()
            elif relation['type'] == 'bar':
                # Create bar plot
                sns.barplot(x=relation['x'], y=relation['y'], data=data)
                plt.title(f'Bar Plot of {relation["x"]} vs {relation["y"]}')
                plt.show()
            elif relation['type'] == 'box':
                # Create box plot
                sns.boxplot(x=relation['x'], y=relation['y'], data=data)
                plt.title(f'Box Plot of {relation["x"]} vs {relation["y"]}')
                plt.show()
            elif relation['type'] == 'heatmap':
                # Create heatmap
                plt.figure(figsize=(10,8))
                sns.heatmap(data.pivot_table(index=relation['x'], columns=relation['y'], aggfunc='size', fill_value=0), annot=True, cmap='Blues')
                plt.title(f'Heatmap of {relation["x"]} vs {relation["y"]}')
                plt.show()
            elif relation['type'] == 'line':
                # Create line plot
                sns.lineplot(x=relation['x'], y=relation['y'], data=data)
                plt.title(f'Line Plot of {relation["x"]} vs {relation["y"]}')
                plt.show()
        else:
            if relation['type'] == 'histogram':
                # Create histogram
                sns.histplot(data[relation['x']], kde=True)
                plt.title(f'Histogram of {relation["x"]}')
                plt.show()

# Define the relations
relations = [
    {"x":"age","y":"salary","type":"scatter"}, 
    {"x":"department","y":"salary","type":"bar"}, 
    {"x":"age","type":"histogram"}, 
    {"x":"salary","type":"histogram"}, 
    {"x":"department","y":"age","type":"box"}, 
    {"x":"age","y":"salary","type":"heatmap"}, 
    {"x":"department","y":"salary","type":"bar"}, 
    {"x":"age","type":"histogram"}
]

# Create the plots
create_plots(relations)