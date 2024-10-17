
""" KEYWORD DETECTION FUNCTION """

import nltk
from rake_nltk import Rake
from nltk.corpus import words, wordnet
nltk.download('words')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
# Function to check if the user's input is valid
def is_valid_input(user_input, valid_user_ids, keywords):
    # Convert both user IDs and keywords to set for fast membership checking
    valid_user_ids = set(valid_user_ids)
    keywords = set(word.lower() for word in keywords)  # Ensure keywords are lowercase for comparison

    # Split the input into words
    tokens = nltk.word_tokenize(user_input)

    # Check each token if it's a word in WordNet, a valid numeric user ID, or a recognized keyword
    valid_tokens = [word for word in tokens 
                    if word.lower() in wordnet.words() or 
                       (word.isdigit() and int(word) in valid_user_ids) or 
                       word.lower() in keywords]

    # Return True if there are any valid tokens, otherwise False
    return len(valid_tokens) > 0

def extract_keywords(item):
    r = Rake()
    r.extract_keywords_from_text(item)
    query_keyword = r.get_ranked_phrases_with_scores()
    query_keyword_ls = [keyword[1] for keyword in query_keyword]
    return query_keyword_ls


""" RECOMMENDATION FUNCTIONS """
# Initializing data
import pandas as pd
catalouge = pd.read_csv('newData/flipkart_cleaned.csv')
purchase_history = pd.read_csv('newData/synthetic_v2.csv')

def get_recommendation(keywords_list): # getting the top 3 products based on keywords
    mask = catalouge['product_category_tree'].apply(lambda x: any(keyword in x for keyword in keywords_list))
    filtered = catalouge[mask]
    top_products = filtered.sort_values(by='overall_rating', ascending=False).head(3)

    # Formatting the output more clearly
    return "\n".join(
        f"**{idx + 1}. {row['product_name']}** - Discounted Price: {row['discounted_price']}, Description: {row['description']}"
        for idx, row in top_products.iterrows()
    )

def get_popular_items():
   
    # Load the dataset
    df = pd.read_csv("newData/top_5_most_popular.csv")

    popular_items_details = []
    for index, row in df.iterrows():
        item_details = f"- {row['product_name']} priced at Rs.{row['discounted_price']} (Rating: {row['User rating for the product']}/10)\n  Description: {row['description']}"
        popular_items_details.append(item_details)

    # Join all item details into a single string
    response_text = "Here are these week's popular items:\n" + "\n".join(popular_items_details)
    response_text += "\n\nWould you like to know more about any of these items? If not, please provide me the description of the item you are looking for."

    return response_text


""" CHAT BOT FUNCTION"""

import re

# Getting user intention
def getting_user_intention(user_input, intention_chain, previous_intention):
    user_intention = intention_chain.invoke({"input": user_input, "previous_intention": previous_intention})
    return user_intention

# Getting bot response
def getting_bot_response(user_intention, chain2):
    """
    previous intention is derived from the past conversation. 
    """
    item_availability_match = re.search(r'Available in Store:\s*(.+)', user_intention)
    item_availability = item_availability_match.group(1)

    if item_availability != "Yes.":
        response = re.search(r'Suggested Actions or Follow-Up Questions:\s*(.+)', user_intention, re.DOTALL)
        bot_response = response.group(1).strip()
        
    else:
        match = re.search(r'Actionable Goal \+ Specific Details:\s*(.+)', user_intention)
        item = match.group(1)

        # Getting recommendations from available products
        query_keyword_ls = extract_keywords(item)
        recommendations = get_recommendation(query_keyword_ls)
        #print("keywords: ", query_keyword_ls)
        #print("Time taken: ", time.time() - start_time)

        # Getting follow-up questions from previous LLM
        questions_match = re.search(r'Suggested Actions or Follow-Up Questions:\s*(.+)', user_intention, re.DOTALL)
        questions = questions_match.group(1).strip()
        bot_response = chain2.invoke({"recommendations": recommendations, "questions": questions})

    return bot_response

