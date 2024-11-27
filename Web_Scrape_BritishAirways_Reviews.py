# Create a web crawler to get user review and ratings of British Airways

# Import libraries
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np

# Web page pretty Static :)
url = "https://www.airlinequality.com/airline-reviews/british-airways/?sortby=post_date%3ADesc&pagesize=100"
response = requests.get(url)
soup = bs(response.text, 'html.parser')


# Create a list to collect data
data = []

# Function to scrape reviews from The URL
def scrape_reviews(url):
    response = requests.get(url)
    soup = bs(response.text, 'html.parser')

    # Find all review containers
    for review_div in soup.find_all('article', itemprop='review'):
        rating_span = review_div.find('span', itemprop='ratingValue')

        if rating_span is not None:  # Check if the element was found. Some forgot to rate!
          ratings_value = rating_span.text.strip()
        else:
          ratings_value = None
        title = review_div.find('h2', class_='text_header').text.strip()
        review_text = review_div.find('div', class_='text_content').text.strip()
        rating_div = review_div.find('div', class_='review-stats')

        # Initialize additional info variables
        type_of_traveller = seat_type = route = date_flown = None
        seat_comfort = cabin_staff_service = food_beverages = ground_service = value_for_money = None
        recommended = None

        if rating_div:
            for row in rating_div.find_all('tr'):
                header = row.find('td', class_='review-rating-header').text.strip()
                if header == "Type Of Traveller":
                    type_of_traveller = row.find('td', class_='review-value').text.strip()
                elif header == "Seat Type":
                    seat_type = row.find('td', class_='review-value').text.strip()
                elif header == "Route":
                    route = row.find('td', class_='review-value').text.strip()
                elif header == "Date Flown":
                    date_flown = row.find('td', class_='review-value').text.strip()
                elif header == "Seat Comfort":
                    seat_comfort = len(row.find_all('span', class_='fill'))
                elif header == "Cabin Staff Service":
                    cabin_staff_service = len(row.find_all('span', class_='fill'))
                elif header == "Food & Beverages":
                    food_beverages = len(row.find_all('span', class_='fill'))
                elif header == "Ground Service":
                    ground_service = len(row.find_all('span', class_='fill'))
                elif header == "Value For Money":
                    value_for_money = len(row.find_all('span', class_='fill'))
                elif header == "Recommended":
                    recommended_td = row.find('td', class_='rating-no')
                    recommended = recommended_td.text.strip() if recommended_td else None

        # Append extracted data to the list as a single dictionary
        data.append({
            'Title': title,
            'Review': review_text,
            'Rating': ratings_value,
            'Type of Traveller': type_of_traveller,
            'Seat Type': seat_type,
            'Route': route,
            'Date Flown': date_flown,
            'Seat Comfort': seat_comfort,
            'Cabin Staff Service': cabin_staff_service,
            'Food & Beverages': food_beverages,
            'Ground Service': ground_service,
            'Value For Money': value_for_money,
            'Recommended': recommended,
        })

# Scrape specific page ranges using pagination links
page_number = 1
while True: # or page_number<= n | True
    print(f"Scraping page {page_number}...")
    current_url = f"https://www.airlinequality.com/airline-reviews/british-airways/page/{page_number}/?sortby=post_date%3ADesc&pagesize=100"
    scrape_reviews(current_url)

    # Check if there's a next page link
    response = requests.get(current_url)
    soup = bs(response.text, 'html.parser')

    # Find the pagination section to determine if there are more pages
    pagination_links = soup.select("article.comp.comp_reviews-pagination.querylist-pagination.position- ul li a")
    next_page_link_found = False

    for link in pagination_links:
        if link.text.strip() == str(page_number + 1):
            next_page_link_found = True
            break

    if not next_page_link_found:
        break  # Exit loop if no next page is found

    page_number += 1  

# Create a DataFrame from the collected data.
raw_reviews = pd.DataFrame(data)

#   Save the file          raw_reviews.to_csv('british_airways_reviews.csv', index=False)
#---------------------

# Now clean the df
df = raw_reviews.copy()

condition = df['Recommended'].isnull() & (df['Rating']>'5') # Unfortunately there are only 'no' in Recommended column so to replace with more confidence set this condition 
df.loc[condition, 'Recommended']= "Yes"
df.dropna(subset= ["Recommended", 'Date Flown'], axis = 0, inplace= True) # Get rid of the instances that cant be filled

# Still cleaning
def split_review(row):
    if '|' in row['Review']: # Some rows havn't got the infamous "|".
        # Split only if '|' is present
        verify_part = row['Review'].split('|')[0].replace('✅', '').replace('❎', '').strip()
        review_part = row['Review'].split('|')[1].strip()
        return pd.Series([verify_part, review_part])
    else:
        # If no '|', return NaN for Verify and keep original Review
        return pd.Series([np.nan, row['Review']])

df[['Verify', 'Review']] = df.apply(split_review, axis=1)

df['Origin'] = df['Route'].str.split('to').str[0].str.replace('to','',regex= False)
df['Destination'] = df['Route'].str.split('to').str[1]
df.drop('Route', axis = 1, inplace= True)

df['Month'] = df['Date Flown'].str.split(' ').str[0]
df[ 'Year'] = df['Date Flown'].str.split(' ').str[1]
df.drop('Date Flown', axis = 1, inplace= True)

df['Rating'] = df['Rating'].astype(float)
df['Value For Money'] = df['Value For Money'].astype(float)

df.replace('no', 'No', inplace= True)