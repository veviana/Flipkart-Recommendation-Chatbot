import os
import time
from joblib import dump, load # to store matrix
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process

# File paths for saving/loading 
lsa_matrix_file = 'lsa_matrix.joblib'
product_data_file = 'newData/flipkart_cleaned.csv'


### content based rec sys aims to recommend items based on similarity between items
df = pd.read_csv(product_data_file)

# print(df.columns.values)
# ['uniq_id' 'product_name' 'product_category_tree' 'pid' 'retail_price'
# 'discounted_price' 'discount' 'description' 'overall_rating' 'brand'
# 'product_specifications']
# print(df.dtypes)

# Combining product_name and features into a single string
df['content'] = df['product_name'].astype(str) + ' ' + df['product_category_tree'].astype(str) + ' ' + df['retail_price'].astype(str) + ' ' + df['discounted_price'].astype(str) + ' ' + df['discount'].astype(str) + ' ' + df['description'].astype(str) + ' ' + df['overall_rating'].astype(str) + ' ' + df['brand'].astype(str) + ' ' + df['product_specifications'].astype(str)

df['content'] = df['content'].fillna('')

# Check if the LSA matrix needs to be recalculated (if there is modification to flipkart csv)
recalculate_lsa = False

if os.path.exists(lsa_matrix_file):
    # Compare modification times
    lsa_matrix_mtime = os.path.getmtime(lsa_matrix_file)
    product_data_mtime = os.path.getmtime(product_data_file)

    if product_data_mtime > lsa_matrix_mtime:
        print("Product information database was updated, recalculating lsa_matrix...")
        recalculate_lsa = True
else:
    print("lsa_matrix does not exist, computing...")
    recalculate_lsa = True

# Check if there is a need to compute LSA matrix
if recalculate_lsa:
    print("Computing LSA matrix...")

    # Create bag of words
    vectorizer = CountVectorizer()
    bow = vectorizer.fit_transform(df['content'])

    # Convert bag of words to TF-IDF
    tfidf_transformer = TfidfTransformer()
    tfidf = tfidf_transformer.fit_transform(bow)

    # Apply LSA 
    lsa = TruncatedSVD(n_components=100, algorithm='arpack')
    lsa.fit(tfidf) # train lsa model
    lsa_matrix = lsa.transform(tfidf) # project data onto learned components

    # Save the computed LSA matrix to file
    dump(lsa_matrix, lsa_matrix_file)
    print("LSA matrix saved to file.")
else:
    print("loading lsa_matrix from file...")
    lsa_matrix=load(lsa_matrix_file)

# Get the user input
user_product = input("Enter a product ")

# Start timer after user input
start_time = time.time()

# Use fuzzy matching to find the closest product name
match = process.extractOne(user_product, df['product_name'])
closest_match = match[0]
score = match[1]

print("closest match and score: ", closest_match, score)

if score < 70:
    print("No close match found")
else:
    # find the index of the closes product
    product_index = df[df['product_name'] == closest_match].index[0]

     # Compute the cosine similarities using the lsa_matrix
    similarity_scores = cosine_similarity(lsa_matrix[product_index].reshape(1, -1), lsa_matrix)

    # Get the top 10 most similar products
    similar_products = list(enumerate(similarity_scores[0]))
    sorted_similar_products = sorted(similar_products, key=lambda x: x[1], reverse=True)[1:10]

    # Print the top 10 similar products
    for i, score in sorted_similar_products:
        print("{}: {}".format(i, df.loc[i, 'product_name']))

# End timer for the entire program
end_time = time.time()

# Print time taken
print("Time taken to find recommendations: {:.2f} seconds".format(end_time - start_time))