from datetime import datetime
import googlemaps
import requests_cache

GOOGLE_API_KEY = 'AIzaSyAnNRFTu5qEotKzTm1-O83jLECmbOfQDaQ'

class Place:
    def __init__(self, google_location):
        self.name = google_location['name']
        self.rating = google_location['rating']
        self.num_ratings = google_location['user_ratings_total']
        self.place_id = google_location['place_id']
        self.geos = google_location['geometry']['location']
        self.formatted_address = google_location['formatted_address']
        self.related_locs = {}
        return
    
    def print_info(self, loc=False, places=True):
        print(f'Name: {self.name}')
        print(f'Rating: {self.rating} ({self.num_ratings} reviews)')
        if loc:
            print(f'Geos: {self.geos}')
        if places:
            print(f'Related places: {self.related_locs}')
        print()
        return
    
    def get_dict_info(self):

        record = {}

        record['name'] = self.name 
        record['rating'] = self.rating
        record['num_ratings'] = self.num_ratings
        record['address'] = self.formatted_address
        record['geos'] = self.geos
        for loc_type in self.related_locs:
            record[loc_type] = self.related_locs[loc_type]

        return record


class TransitStep:
    def __init__(self, step_info):
        self.start_location = step_info['start_location']
        self.end_location = step_info['end_location']
        
        self.distance_text = step_info['distance']['text']
        self.distance_val = step_info['distance']['value']

        self.duration_text = step_info['duration']['text']
        self.duration_seconds = step_info['duration']['value']
        self.duration_minutes = round(self.duration_seconds/60)

        return
    
    def print_info(self):
        
        print(f'Duration: {self.duration_text}')
        print(f'Duration: {self.duration_minutes}')
        print(f'Distance: {self.distance_text}')
        print(f'Start location: {self.start_location}')
        print(f'End location: {self.end_location}')
        print()
        
        return

class Transit:
    def __init__(self, transit_info):
        self.duration_text = transit_info['duration']['text']
        self.duration_seconds = transit_info['duration']['value']
        self.duration_minutes = round(self.duration_seconds/60)

        self.start_address = transit_info['start_address']
        self.start_loc = transit_info['start_location']

        self.end_address = transit_info['end_address']
        self.end_loc = transit_info['end_location']

        steps = []
        
        for step in transit_info['steps']:
            steps.append(TransitStep(step))

        self.steps = steps

        return


def find_places(gmaps_client, base_location:dict, query:str, min_rating:float = 4.3, max_places:int|bool = None):
    """
    Find a set of places with the given constraints, save key details in Place class and return a list
    """
    places = []
    locations = gmaps_client.places(location=base_location, query=query)
    for g_place in locations['results']:
        place = Place(g_place)
        if place.rating >= min_rating:
            places.append(place)
    
    if max_places:
        return places[:max_places]

    return places

def _find_steps(transit, reverse_steps = False, max_commute:int=30, minutes_offset:int=5):
    """
    """
    if reverse_steps:
        transit_steps = reversed(transit.steps)
    else:
        transit_steps = transit.steps

    target_commute = max_commute - minutes_offset

    if transit.duration_minutes > target_commute:
        target_length = transit.duration_minutes - target_commute
        
        done = False
        keep_steps = []
        for step in transit_steps:
            if done:
                keep_steps.append(step)
            else:
                target_length -= step.duration_minutes
                if target_length <= 0:
                    done = True
    else:
        keep_steps = transit_steps

    return keep_steps

def _find_route_locs(gmaps_client, start_loc, end_loc, max_start_commute, max_end_commute, departure_time, min_rating:float=4.0, travel_mode = 'transit', loc_query = 'apartments'):

    directions = gmaps_client.directions(origin = start_loc,
                                  destination = end_loc,
                                  mode=travel_mode,
                                  departure_time=departure_time)

    
    transit = Transit(directions[0]['legs'][0])
    
    # Using the waypoints and desired max commute times, identify a list of stops along each route that 
    # would fall within the (max commute - 5 mins) each way to work and the personal location
    start_steps = _find_steps(transit=transit, max_commute = max_start_commute, reverse_steps=True)
    
    end_steps = _find_steps(transit=transit, max_commute = max_end_commute)
        
    search_steps = []
    for step in end_steps:
        if step in start_steps:
            search_steps.append(step)

    loc_options = []
    for step in search_steps:
        loc_options.extend(find_places(gmaps_client = gmaps_client, 
                                     base_location = step.end_location, 
                                     query = 'apartment', 
                                     min_rating = min_rating))
    return loc_options


def find_apartments(work_location:dict|str, personal_location:str, max_work_commute:int, max_personal_commute:int, departure_time:datetime, max_personal_locs = 3,transit_style:str='transit', min_rating:float=4.3):
    
    """
    Goal of this function is to find apartments constrained by a set of conditions

    """

    # create a search session to use cached queries
    session = requests_cache.CachedSession('demo_cache')
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY, requests_session=session)

    apartments = []

    if isinstance(work_location, str):
         work_location = gmaps.geocode(work_location)[0]['geometry']['location']
            
    # Find the closest personal locations to the workplace, limiting things to the top 3 to stop it all getting out of hand
    personal_locations = find_places(gmaps_client = gmaps, base_location = work_location, query = personal_location, min_rating = min_rating, max_places = max_personal_locs)

    apartment_options = {}

    personal_loc_tag = personal_location.replace(' ','_')

    for personal_loc in personal_locations:

        end_loc = personal_loc.geos
    
        new_apartment_options = _find_route_locs(gmaps_client=gmaps,
                                                 start_loc=work_location, 
                                                 end_loc=end_loc, 
                                                 max_start_commute=max_work_commute, 
                                                 max_end_commute=max_personal_commute,
                                                 departure_time=departure_time, 
                                                 min_rating = min_rating,
                                                 travel_mode = 'transit', 
                                                 loc_query='apartments')

        for apt in new_apartment_options:

            if apt.name in apartment_options:
                apartment_options[apt.name].related_locs[personal_loc_tag].append(personal_loc.name)
                
            else:
                apt.related_locs[personal_loc_tag] = [personal_loc.name]
                apartment_options[apt.name] = apt

    return list(apartment_options.values())