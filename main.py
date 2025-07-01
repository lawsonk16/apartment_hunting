from google_maps_search import find_apartments
import pandas as pd

minimum_rating = 4.0
maximum_work_commute = 45
max_personal_commute = 15
max_personal_locs = 3

work_location = 'WAS17 Amazon'
personal_location = 'bouldering gym'
search_tag = 'was_apartments'

from datetime import datetime
departure_time = datetime(2025,9,3,10,1,1)

apartments = find_apartments(work_location = work_location, 
                            personal_location = personal_location, 
                            max_work_commute = maximum_work_commute, 
                            max_personal_commute = max_personal_commute, 
                            departure_time = departure_time, 
                            min_rating = minimum_rating,
                            max_personal_locs = max_personal_locs
                            )

print(f'{len(apartments)} options found')

apt_data = []

for apt in apartments:
    apt_data.append(apt.get_dict_info())

df = pd.DataFrame(apt_data)
df.to_excel(f'{search_tag}.xlsx')