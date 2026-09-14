import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from itertools import combinations
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------
# STEP 1: LOAD DATA
# ---------------------------------------------------------------
print("STEP 1: Loading data...")
df = pd.read_csv('netflix_titles.csv')
print(f"Loaded {len(df)} rows, {len(df.columns)} columns\n")

# ---------------------------------------------------------------
# STEP 2: DATA CLEANING
# ---------------------------------------------------------------
print("STEP 2: Cleaning data...")
print("Missing values before cleaning:")
print(df.isnull().sum())

df['director'] = df['director'].fillna('Unknown')
df['cast'] = df['cast'].fillna('Unknown')
df['country'] = df['country'].fillna('Unknown')
df['rating'] = df['rating'].fillna('Unrated')
df = df.dropna(subset=['date_added']).reset_index(drop=True)

df['duration_num'] = df['duration'].str.extract(r'(\d+)').astype(float)

print("\nMissing values after cleaning:")
print(df.isnull().sum())

df.to_csv('netflix_titles_cleaned.csv', index=False)
print("\nSaved cleaned dataset -> netflix_titles_cleaned.csv\n")

# ---------------------------------------------------------------
# STEP 3: BASIC NUMPY STATS
# ---------------------------------------------------------------
print("STEP 3: Numpy statistics on Movie duration...")
movie_durations = df.loc[df['type'] == 'Movie', 'duration_num'].dropna()
print("Average movie duration:", np.mean(movie_durations))
print("Median movie duration :", np.median(movie_durations))
print("Std deviation         :", np.std(movie_durations))
print()

RED, GOLD = '#B00610', '#D9A441'
SCREENSHOT_DIR = 'screenshots/'

# ---------------------------------------------------------------
# STEP 4: MOVIES VS TV SHOWS (PIE CHART)
# ---------------------------------------------------------------
print("STEP 4: Movies vs TV Shows chart...")
type_counts = df['type'].value_counts()
plt.figure(figsize=(6, 6))
plt.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%',
        colors=[RED, GOLD], startangle=90)
plt.title('Movies vs TV Shows')
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '01_movies_vs_tvshows.png', dpi=150)
plt.close()

# ---------------------------------------------------------------
# STEP 5: YEAR-WISE TREND (LINE CHART)
# ---------------------------------------------------------------
print("STEP 5: Year-wise content growth chart...")
yearly = df[(df['release_year'] >= 2008) & (df['release_year'] <= 2020)] \
    .groupby(['release_year', 'type']).size().unstack(fill_value=0)
plt.figure(figsize=(9, 5))
plt.plot(yearly.index, yearly['Movie'], marker='o', label='Movie', color=RED)
plt.plot(yearly.index, yearly['TV Show'], marker='o', label='TV Show', color=GOLD)
plt.title('Content Added Per Year')
plt.xlabel('Release Year')
plt.ylabel('Number of Titles')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '02_year_trend.png', dpi=150)
plt.close()

correlation = np.corrcoef(yearly['Movie'], yearly['TV Show'])[0, 1]
print("Correlation between Movie & TV Show yearly growth:", round(correlation, 2))

# ---------------------------------------------------------------
# STEP 6: RATING DISTRIBUTION (BAR CHART)
# ---------------------------------------------------------------
print("STEP 6: Rating distribution chart...")
rating_counts = df['rating'].value_counts().head(10)
plt.figure(figsize=(9, 5))
plt.bar(rating_counts.index, rating_counts.values, color=RED)
plt.title('Content Rating Distribution')
plt.ylabel('Number of Titles')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '03_rating_distribution.png', dpi=150)
plt.close()

# ---------------------------------------------------------------
# STEP 7: GENRE ANALYSIS
# ---------------------------------------------------------------
print("STEP 7: Top genres chart...")
genre_series = df['listed_in'].str.split(', ').explode()
top_genres = genre_series.value_counts().head(10)
plt.figure(figsize=(8, 5))
plt.barh(top_genres.index[::-1], top_genres.values[::-1], color=GOLD)
plt.title('Top 10 Genres')
plt.xlabel('Number of Titles')
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '04_top_genres.png', dpi=150)
plt.close()

# ---------------------------------------------------------------
# STEP 8: COUNTRY ANALYSIS
# ---------------------------------------------------------------
print("STEP 8: Top countries chart...")
country_series = df['country'].str.split(', ').explode().str.strip()
country_series = country_series[country_series != 'Unknown']
top_countries = country_series.value_counts().head(10)
plt.figure(figsize=(8, 5))
plt.barh(top_countries.index[::-1], top_countries.values[::-1], color=RED)
plt.title('Top 10 Countries by Content')
plt.xlabel('Number of Titles')
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '05_top_countries.png', dpi=150)
plt.close()

top10list = list(top_countries.index)
df_exp = df.assign(country=df['country'].str.split(', ')).explode('country')
df_exp['country'] = df_exp['country'].str.strip()
ct = df_exp[df_exp['country'].isin(top10list)].groupby(['country', 'type']) \
    .size().unstack(fill_value=0).reindex(top10list)
x = range(len(top10list))
plt.figure(figsize=(9, 5))
plt.bar([i - 0.2 for i in x], ct['Movie'], width=0.4, label='Movie', color=RED)
plt.bar([i + 0.2 for i in x], ct['TV Show'], width=0.4, label='TV Show', color=GOLD)
plt.xticks(list(x), top10list, rotation=35, ha='right')
plt.title('Movies vs TV Shows by Country (Top 10)')
plt.ylabel('Number of Titles')
plt.legend()
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '06_country_movie_vs_tv.png', dpi=150)
plt.close()

# ---------------------------------------------------------------
# STEP 9: COUNTRY COLLABORATION NETWORK
# ---------------------------------------------------------------
print("STEP 9: Country collaboration network...")
pairs = Counter()
node_counts = Counter()
for c in df['country']:
    countries = [x.strip() for x in c.split(',') if x.strip() and x.strip() != 'Unknown']
    for cc in countries:
        node_counts[cc] += 1
    if len(countries) > 1:
        for a, b in combinations(sorted(set(countries)), 2):
            pairs[(a, b)] += 1

top_pairs = pairs.most_common(40)
G = nx.Graph()
for (a, b), w in top_pairs:
    G.add_edge(a, b, weight=w)

sizes = [node_counts[n] * 3 for n in G.nodes()]
weights = [G[u][v]['weight'] for u, v in G.edges()]

plt.figure(figsize=(12, 10))
pos = nx.spring_layout(G, k=0.6, seed=42, weight='weight')
nx.draw_networkx_edges(G, pos, width=[w * 0.3 for w in weights], edge_color='red', alpha=0.5)
nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color='white', edgecolors='red', linewidths=1.5)
nx.draw_networkx_labels(G, pos, font_size=9)
plt.title('Netflix Country Collaboration Network')
plt.axis('off')
plt.tight_layout()
plt.savefig(SCREENSHOT_DIR + '07_country_collaboration_network.png', dpi=150)
plt.close()

print("Top 10 country collaborations:")
for (a, b), v in pairs.most_common(10):
    print(f"  {a} <-> {b}: {v}")
print()

# ---------------------------------------------------------------
# STEP 10: RECOMMENDATION SYSTEM
# ---------------------------------------------------------------
print("STEP 10: Building recommendation system...")
df['description'] = df['description'].fillna('')
df['listed_in'] = df['listed_in'].fillna('')
df['director'] = df['director'].fillna('')
df['cast'] = df['cast'].fillna('')
df['type'] = df['type'].fillna('')

df['combined_text'] = (
    df['listed_in'] + ' ' +
    df['description'] + ' ' +
    df['director'] + ' ' +
    df['cast'] + ' ' +
    df['type']
)

tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(df['combined_text'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)


def recommend(title, n=5):

    matches = df[df['title'].str.lower() == title.lower()]

    if matches.empty:
        return f"'{title}' not found in dataset"

    idx = matches.index[0]

    selected_type = df.loc[idx, 'type']

    selected_genres = set(
        g.strip() for g in df.loc[idx, 'listed_in'].split(',')
    )

    # Filter only same type
    filtered = df[df['type'] == selected_type]

    # Keep only titles having at least one common genre
    filtered = filtered[
        filtered['listed_in'].apply(
            lambda x: len(
                selected_genres.intersection(
                    set(g.strip() for g in x.split(','))
                )
            ) > 0
        )
    ]

    scores = []

    for i in filtered.index:
        if i == idx:
            continue

        scores.append((i, cosine_sim[idx][i]))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    top = [i[0] for i in scores[:n]]

    return df.loc[top, ['title', 'type', 'listed_in', 'release_year']]