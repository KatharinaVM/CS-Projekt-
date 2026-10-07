# creating filters that filter through hikes_data.json and return only the fitting hikes

# loading hiking data from the JSON file
import json 
with open("hikes_data.json", "r", encoding="utf-8") as file:
    hikes = json.load(file) # Code row 4, 5 and 6 from ChatGPT 


#Filters 

def filter_hikes (
    hikes,
    min_distance,
    max_distance, 
    min_ascent,
    max_ascent,
    min_descent,
    max_descent,
    max_duration,
    min_duration,
    selected_technical, 
    selected_endurance
):
    result = []

    for hike in hikes: 

        #Skip hikes with missing data 
        if (
            hike.get ("distance_km") is None
            or hike.get ("ascent_m") is None
            or hike.get ("descent_m") is None
            or hike.get ("duration_min") is None
            or hike.get ("technical_difficulty") is None
            or hike.get ("endurance_difficulty") is None
        ): 
            continue

        #Check the filters
        if (
            min_distance <= hike ["distance_km"] <= max_distance
            and min_ascent <= hike ["ascent_m"] <= max_ascent
            and min_descent <= hike ["descent_m"] <= max_descent
            and min_duration <= hike ["duration_min"] <= max_duration
            and (
                    not selected_technical
                    or hike["technical_difficulty"] in selected_technical
                )
            and (
                    not selected_endurance
                    or hike["endurance_difficulty"] in selected_endurance
                )
        ): 
            result.append (hike)
    return result 

# Test the filter_hikes function
filtered_hikes = filter_hikes(
    hikes,
    min_distance=1,
    max_distance=100,
    min_ascent=0,
    max_ascent=4000,
    min_descent=0,
    max_descent=3000,
    min_duration=0,
    max_duration=10000,
    selected_technical=[],
    selected_endurance=["medium","difficult","easy"]
)



# Print relevant information for each hike
for hike in filtered_hikes:
    print(f"Name: {hike['name']}")
    print(f"Distance: {hike['distance_km']} km")
    print(f"Ascent: {hike['ascent_m']} m")
    print(f"Descent: {hike['descent_m']} m")
    print(f"Duration: {hike['duration_min']} min")
    print(f"Technical difficulty: {hike['technical_difficulty']}")
    print(f"Endurance difficulty: {hike['endurance_difficulty']}")
    print("-" * 40)


# Print number of matching hikes
print(f"\nNumber of matching hikes: {len(filtered_hikes)}\n") ######## nutzen um in streamlit die Anzahl der Ausgegebenen Wanderungen anzuzeigen, muss dann allerdings aus wetter oder route kommen  

