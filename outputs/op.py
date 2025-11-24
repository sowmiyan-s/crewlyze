import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Load the dataset
df = pd.read_csv('C:\\\\Users\\\\Asus\\\\Documents\\\\DATA SETS\\\\CSV DATA SETS\\\\sugar.csv')

# Define the relations
relations = [
    {'x':'Age','y':'Pregnancies','type':'scatter'},
    {'x':'Age','y':'Glucose','type':'scatter'},
    {'x':'Age','y':'BloodPressure (mg/dL)','type':'scatter'},
    {'x':'Age','y':'SkinThickness','type':'scatter'},
    {'x':'Age','y':'Insulin','type':'scatter'},
    {'x':'Age','y':'BMI','type':'scatter'},
    {'x':'Age','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'Pregnancies','y':'Glucose','type':'scatter'},
    {'x':'Pregnancies','y':'BloodPressure (mg/dL)','type':'scatter'},
    {'x':'Pregnancies','y':'SkinThickness','type':'scatter'},
    {'x':'Pregnancies','y':'Insulin','type':'scatter'},
    {'x':'Pregnancies','y':'BMI','type':'scatter'},
    {'x':'Pregnancies','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'Glucose','y':'BloodPressure (mg/dL)','type':'scatter'},
    {'x':'Glucose','y':'SkinThickness','type':'scatter'},
    {'x':'Glucose','y':'Insulin','type':'scatter'},
    {'x':'Glucose','y':'BMI','type':'scatter'},
    {'x':'Glucose','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'BloodPressure (mg/dL)','y':'SkinThickness','type':'scatter'},
    {'x':'BloodPressure (mg/dL)','y':'Insulin','type':'scatter'},
    {'x':'BloodPressure (mg/dL)','y':'BMI','type':'scatter'},
    {'x':'BloodPressure (mg/dL)','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'SkinThickness','y':'Insulin','type':'scatter'},
    {'x':'SkinThickness','y':'BMI','type':'scatter'},
    {'x':'SkinThickness','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'Insulin','y':'BMI','type':'scatter'},
    {'x':'Insulin','y':'DiabetesPedigreeFunction','type':'scatter'},
    {'x':'BMI','y':'DiabetesPedigreeFunction','type':'scatter'}
]

# Create subplots for each relation
fig, axes = plt.subplots(nrows=len(relations), ncols=1, figsize=(10, 50))

# Loop over each relation
for i, relation in enumerate(relations):
    # Plot the scatter plot
    sns.scatterplot(x=relation['x'], y=relation['y'], data=df, ax=axes[i])
    axes[i].set_title(f"{relation['x']} vs {relation['y']}")

# Layout so plots do not overlap
plt.tight_layout()

# Show the plot
plt.show()