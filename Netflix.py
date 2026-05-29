import pandas as pd
import regex as re

file_path = r"C:\Users\rohan\Downloads\NetflixViewingHistory(2).csv"
df = pd.read_csv(file_path)

def split_title(title):
    title = str(title)
    parts = [p.strip() for p in title.split(':')]
    
    if len(parts) <= 2:
        return pd.Series([parts[0] if len(parts)==2 else None, parts[-1]])
    num = r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)'    
    season_keywords = ['season', 'book', 'volume', 'series']
    split_index = -1
    
    for i, part in enumerate(parts):
        if any(re.search(rf'\b{kw}\b\s*{num}', part, re.IGNORECASE) for kw in season_keywords):
            split_index = i
            break
        if i > 0:
            if re.match(rf'^{re.escape(parts[0])}\s*{num}$', part, re.IGNORECASE):
                split_index = i
                break
                
    if split_index != -1 and split_index < len(parts) - 1:
        season = ': '.join(parts[:split_index + 1])
        episode = ': '.join(parts[split_index + 1:])
        return pd.Series([season, episode])
    else:
        for i, part in enumerate(parts):
            if re.search(rf'\b(chapter|episode|part)\b\s*{num}', part, re.IGNORECASE):
                if i > 0:
                    season = ': '.join(parts[:i])
                    episode = ': '.join(parts[i:])
                    return pd.Series([season, episode])
        return pd.Series([': '.join(parts[:-1]), parts[-1]])


def build_summary(data):
    rows = []
    
    # Handle shows (Season is not null)
    shows = data[data['Season'].notna()]
    for season, group in shows.groupby('Season'):
        rows.append({
            'Title': season,
            'Type': 'Show',
            'First Date': group['Date'].min(),
            'Last Date': group['Date'].max(),
            'Episodes': len(group)
        })
    
    # Handle movies (Season is null, Title holds the name)
    movies = data[data['Season'].isna()]
    for title, group in movies.groupby('Title'):
        rows.append({
            'Title': title,
            'Type': 'Movie',
            'First Date': group['Date'].min(),
            'Last Date': group['Date'].max(),
            'Episodes': len(group)
        })

    return pd.DataFrame(rows)

df[['Season', 'Title']] = df['Title'].apply(split_title)
df['Season'] = df['Season'].str.strip().str.replace(r'\s+', ' ', regex=True)
df_split = df[['Season', 'Title', 'Date']]
df_split['Date'] = pd.to_datetime(df_split['Date'])

df_movies = df_split[df_split['Season'].isna()].copy()
df_shows = df_split[df_split['Season'].notna()].copy()

# Filter out shows with only 1 episode, but keep all movies
df_shows_filtered = df_shows.groupby('Season').filter(lambda x: len(x) > 1)
df_final = pd.concat([df_shows_filtered, df_movies])
# Build summary from the correctly filtered df_final
summary = build_summary(df_final)
summary = summary.sort_values(by=['Type', 'Title']).reset_index(drop=True)
with pd.option_context('display.max_rows', None, 'display.max_columns', None,
                       'display.width', None, 'display.max_colwidth', None):
    print(summary)