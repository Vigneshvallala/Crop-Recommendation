from flask import Flask, render_template, request, send_file
import requests
import pandas as pd
from statistics import mean
import os

# Define app first
app = Flask(__name__)

# Debug: Show template folder path
print("Template folder path:", os.path.join(app.root_path, 'templates'))

def get_weather_data(api_key, location):
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/last100days/next15days?key={api_key}&unitGroup=metric"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            weather_data = [
                {
                    'date': day['datetime'],
                    'temperature': day['temp'],
                    'humidity': day['humidity'],
                    'weather': day['conditions']
                }
                for day in data['days']
            ]
            return weather_data
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None


def load_dataset(file_path):
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None


def recommend_crops(dataset, avg_temperature, avg_humidity):
    try:
        filtered_data = dataset[
            (dataset['Temperature (°C)'].between(avg_temperature - 5, avg_temperature + 5)) &
            (dataset['Humidity (%)'].between(avg_humidity - 10, avg_humidity + 10))
        ]
        if filtered_data.empty:
            return ["No suitable crops found for the given conditions."]
        recommended_crops = filtered_data['Recommended Crops'].value_counts().nlargest(5).index.tolist()
        return recommended_crops
    except Exception as e:
        print(f"Error recommending crops: {e}")
        return ["An error occurred during crop recommendation."]


@app.route('/', methods=['GET', 'POST'])
def index():
    recommended_crops = None
    weather_data = None
    avg_temperature = None
    avg_humidity = None

    if request.method == 'POST':
        api_key = 'HT5XSSGWQ3T27VSHLS37TA3PW'  
        location = request.form['location']
        dataset_file = 'weather_data_2000.xlsx'  # Path to the dataset
        dataset = load_dataset(dataset_file)

        if dataset is not None:
            weather_data = get_weather_data(api_key, location)
            if weather_data:
                avg_temperature = mean([day['temperature'] for day in weather_data])
                avg_humidity = mean([day['humidity'] for day in weather_data])
                recommended_crops = recommend_crops(dataset, avg_temperature, avg_humidity)

    return render_template('index.html', 
                           recommended_crops=recommended_crops, 
                           weather_data=weather_data, 
                           avg_temperature=avg_temperature, 
                           avg_humidity=avg_humidity)


@app.route('/save', methods=['POST'])
def save_weather_data():
    weather_data = request.form['weather_data']  # JSON string from the frontend
    try:
        df = pd.DataFrame(eval(weather_data))
        file_path = "weather_data.xlsx"
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"Error saving weather data: {e}")
        return "Error saving data", 500


if __name__ == "__main__":
    app.run(debug=True)
