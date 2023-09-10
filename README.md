## TikTok Hackathon ##

This project has been done as part of the TikTok Hackathon Challenge 2023 and aims to optimize advertisement moderation. 
Authors: Sneha Kumar, Barnabas Ee, Huang Hongyi


To get the ad-moderator assignments: 
1. Run `pip install -r requirements.txt`
2. Run `python3.9 ad_moderation.py`.
3. The final assignments will be saved in `assignments.csv` in your local directory (an example from our run has been uploaded in this repo). 

Example of running the optimization:
![photo_2023-09-10 12 18 59](https://github.com/snehakumar27/TikTokHackathon/assets/75850030/2cf4b022-5c2d-4f0c-84ee-cf2ea569c786)

Initial Match Score represents the scoring of the assignments before running the optimization algorithm. 
Average Match Score represents the scoring of the assignments after running the optimization algorithm. 
The closer the score is to 0, the better the matches are (see `Matching.ipynb` for more details). 

The remaining python notebooks outline our steps of exploration and how we have come up with our final algorithm in the Python script. 

For more details on the background and algorithm see: https://devpost.com/software/optimizing-advertisement-moderation-yip7lg
