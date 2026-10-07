# creating filters that filter through hikes_data.json and return only the fitting hikes

# loading hiking data from the JSON file
import json 
with open("hikes_data.json", "r", encoding="utf-8") as file:
    hikes = json.load(file) # Code row 4, 5 and 6 from ChatGPT 

#Diagnose
print("Total hikes:", len(hikes))

print(
    "Missing distance:",
    sum(1 for hike in hikes if hike.get("distance_km") is None)
)

print(
    "Missing ascent:",
    sum(1 for hike in hikes if hike.get("ascent_m") is None)
)

print(
    "Missing descent:",
    sum(1 for hike in hikes if hike.get("descent_m") is None)
)

print(
    "Complete data:",
    sum(
        1 for hike in hikes
        if hike.get("distance_km") is not None
        and hike.get("ascent_m") is not None
        and hike.get("descent_m") is not None
    )
)


#Filters 

def filter_hikes (
    hikes,
    min_distance,
    max_distance, 
    min_ascent,
    max_ascent,
    min_descent,
    max_descent
    
):
    result = []

    for hike in hikes: 

        #Skip hikes with missing data 
        if (
            hike.get ("distance_km") is None
            or hike.get ("ascent_m") is None
            or hike.get ("descent_m") is None
        ): 
            continue

        #Check the filters
        if (
            min_distance <= hike ["distance_km"] <= max_distance
            and min_ascent <= hike ["ascent_m"] <= max_ascent
            and min_descent <= hike ["descent_m"] <= max_descent

        ): 
            result.append (hike)
    return result 

# Test the filter_hikes function
filtered_hikes = filter_hikes(
    hikes,
    min_distance=1,
    max_distance=20,
    min_ascent=0,
    max_ascent=1500,
    min_descent=0,
    max_descent=1500
)



# Print relevant information for each hike
for hike in filtered_hikes:
    print(f"Name: {hike['name']}")
    print(f"Distance: {hike['distance_km']} km")
    print(f"Ascent: {hike['ascent_m']} m")
    print(f"Descent: {hike['descent_m']} m")
    print("-" * 40)


# Print number of matching hikes
print(f"\nNumber of matching hikes: {len(filtered_hikes)}\n")