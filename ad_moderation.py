import pandas as pd
import numpy as np
from tqdm import tqdm
import math
import random

#set appropriate working directory 
ads = pd.read_excel("Dataset.xlsx", skiprows=1, sheet_name=0)
rev = pd.read_excel("Dataset.xlsx", sheet_name=1)

##############################
#### Ads Priority Scoring ####
## Cleaning ##
#all NA punish nums are supposed to be 0
ads['punish_num'] = ads['punish_num'].fillna(0)

# Drop rows with missing values
ads.dropna(inplace = True, subset=['ad_revenue', 'start_time'])     ##keep NAs of queue_market (since later matching is based on deliver_country)

## Scoring ##
# Log transformation for 3 predictors - add a small value for log for 0 values
ads['punish_num'] += 0.1
ads['ad_revenue'] += 0.001
ads['avg_ad_revenue'] += 0.001

ads['v1'] = np.log(ads['punish_num'])
ads['v2'] = np.log(ads['ad_revenue'])
ads['v3'] = np.log(ads['avg_ad_revenue'])

# Compute the score column
ads['score'] = (2 * ads['v1'] + 0.5 * ads['v2'] + 0.5 * ads['v3']) * ads['baseline_st']

# Rescale the score column
def feature_scaling(X):
    min = X.min()
    max = X.max()
    output = (X - min) / (max-min)
    return output

ads['scaled_score'] = feature_scaling(ads['score'])


##############################
# Reviewers Priority Scoring #
## Cleaning ##
# Rename and change data type of accuracy column
rev = rev.rename(columns={' accuracy ': 'accuracy'})
rev['accuracy'] = rev['accuracy'].replace(rev['accuracy'].unique()[0], np.nan)
rev['accuracy'] = pd.to_numeric(rev['accuracy'], errors='coerce').astype('float64')

#Drop rows with missing values
rev.dropna(inplace = True)

## Scoring ##
rev['v1'] = np.sqrt(rev['Productivity'])
rev['v2'] = np.log(rev['accuracy'])
rev['v3'] = np.log(rev['handling time'])

# Compute the score column
rev['score'] = 0.6 * rev['v1'] - 0.5 * rev['v3'] + 15 * rev['accuracy']

#Rescale the score column
rev['scaled_score'] = feature_scaling(rev['score'])



##############################
########## Matching ##########
## Further Cleaning ##
#Store markets as a list
rev['market'] = rev['market'].apply(lambda x: eval(x))

#Set a max_cap of number of ads assigned
def cap(util):
  if 0 <= util <= 0.2:
    return 80
  elif 0.2 < util <= 0.4:
    return 64
  elif 0.4 < util <= 0.6:
    return 48
  elif 0.6 < util <= 0.8:
    return 32
  elif 0.8 < util < 1.0:
    return 16
  else:
    return 1

rev['max_cap'] = rev['Utilisation %'].apply(cap)

#Indexing for reviewers
rev.set_index('moderator', inplace = True)

#storing assigned ads to reviewer (initialize empty)
rev['assigned_ads'] = np.empty((len(rev), 0)).tolist()


##Stochastic Optimization ##
# Objective function

#closer to 0 = better match
def match_score(ad, reviewer):
  score_diff = (ads.loc[ad, 'scaled_score'] - rev.loc[reviewer, 'scaled_score']) ** 2 # We use square to penalize more if the priority scores of the ad and the reviewer are significant different
  market = int(ads.loc[ad, 'delivery_country'] in rev.loc[reviewer, 'market'])
  curr_util = max(rev.loc[reviewer, 'Utilisation %'], 1)
  assign_priority = len(rev.loc[reviewer, 'assigned_ads'])/rev.loc[reviewer, 'max_cap'] # The more ads currently assigned to this moderator, the higher this score; the more max assignments this moderator can have, the lower this score

  return score_diff + market + curr_util + assign_priority

# All ads and reviewers in a list
all_ads = ads.index.tolist()
all_reviewers = rev.index.tolist()

# Initial random assignment
initial = {}
for ad in all_ads:
  initial[ad] = random.choice(all_reviewers)
  rev.loc[initial[ad], 'assigned_ads'].append(ad)

def simulated_annealing(initial_assgn, T, alpha, max_iter):
  current = initial_assgn.copy()

  for iter in tqdm(range(max_iter)):
    #randomly select an ad to reassign
    re_ad = random.choice(all_ads)
    new_rev = random.choice(all_reviewers)
    while new_rev == current[re_ad]:
      new_rev = random.choice(all_reviewers)

    # Calculate the new score if reviewer reassigned
    difference = match_score(re_ad, new_rev) - match_score(re_ad, current[re_ad])

    # Swapping
    switch = False
    if difference <= 0:
        switch = True
    else:
      prob = math.exp(-difference/T)
      thresh = random.uniform(0,1)
      if prob > thresh:
          switch = True

    #Update to better score
    if switch:
        (rev.loc[current[re_ad], 'assigned_ads']).remove(re_ad)
        (rev.loc[new_rev, 'assigned_ads']).append(re_ad)
        current[re_ad] = new_rev

    #T decay
    T *= alpha

  return current

assignments = simulated_annealing(initial, T = 1000, alpha = 0.99, max_iter = 1000000)
print(assignments)

#write it to a csv file
import csv
csv_file = 'assignments.csv'

with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Headers
    writer.writerow(['Ad_index', 'Moderator_ID'])
    
    # Write data from the assignment dictionary
    for key, value in assignments.items():
        writer.writerow([key, value])
