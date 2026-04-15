# Arizona Restaurant Analysis System

## 1. Problem & User 

**Problem:** Consumers face decision paralysis when navigating vast, complex restaurant data—thousands of options with scattered reviews, inconsistent ratings, and abstract metrics that lack concrete benchmarks for meaningful comparison.

**Target User:** Everyday consumers in Arizona seeking personalized, data-driven dining decisions that transform fragmented, hard-to-interpret data into clear, actionable standards for optimal restaurant selection and timing.

---

## 2. Data 

- **Source:** Yelp Open Dataset (https://www.yelp.com/dataset)
- **Dataset Last Updated:** February 16, 2021
- **Access Date:** April 9, 2026
- **Key Fields:**
  - `business_id`, `name`, `city`, `cuisine`: Restaurant identification
  - `stars`, `review_count`: Overall ratings
  - `reviews`: Individual reviews with date, stars, and text (max 30 per restaurant)
  - `checkin`: Hourly customer traffic patterns (0-23h, peak hour identified)

---

## 3. Methods 

1. **Data Screening & Cleaning:** Filter Arizona restaurants (`state = 'AZ'`) with active status (`is_open = 1`), minimum 3.0 stars, and at least 10 reviews. Standardize raw `categories` into 11 cuisine types via keyword mapping, excluding unclassified restaurants.

2. **Review Processing:** Collect maximum 30 reviews per restaurant from filtered pool, capped at 500,000 total reviews. Truncate comments to 300 characters for efficiency. Structure as dictionary keyed by `business_id` for fast lookup.

3. **Check-in Processing:** Parse first 100 check-in records per restaurant into hourly buckets (0-23), identify peak traffic hour, and store 24-hour distribution patterns.

4. **Sentiment Analysis:** Classify reviews as Positive (4-5★), Neutral (3★), Negative (1-2★). Extract keyword frequencies using predefined positive and negative word lists.

5. **Trend Analysis:** Calculate monthly average ratings versus cuisine-category benchmark. Classify trajectory as Improving, Stable, or Declining based on recent versus early period comparison.

6. **Hourly Analysis:** Correlate traffic volume with average ratings by hour. Identify optimal windows (high rating, low traffic) and problem hours (high traffic, low rating).

7. **Smart Score Calculation:** Weighted scoring combining Base Rating (40%), Review Quality (30%), Review Volume (10%), Check-in Activity (20%), and Peak Hour Bonus (5%).

8. **Total Assessment:** Integrate sentiment (25%), trend (25%), hourly experience (25%), and smart score (25%) into final 100-point grade: Highly Recommended, Recommended, Worth Considering, or Proceed with Caution.

---

## 4. Key Findings 

- Single metrics are misleading: Star ratings alone mask critical variations—some highly-rated restaurants suffer declining quality or peak-hour service drops revealed only through multi-dimensional analysis.

- Abstract data lacks comparability: Raw review counts, sentiment scores, and traffic patterns provide no intuitive baseline; the tool establishes concrete benchmarks (category averages, percentile grades) for meaningful interpretation.

- Timing significantly impacts experience: Specific "golden windows" exist (e.g., 2:00-4:00 PM) where consumers enjoy better service with shorter waits, transforming abstract hourly data into actionable visit recommendations.

- Keyword sentiment exposes hidden attributes: Specific strengths like "friendly staff" or weaknesses like "slow service" surface through text analysis, converting vague impressions into concrete evaluation criteria.

- The tool transforms overload into clarity: Fragmented, complex restaurant data with no common standard converts into unified, personalized grades and specific time recommendations, directly addressing choice paralysis.

---

## 5. How to run 

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

---

## 6. Product Link / Demo

- **Live Tool**: (https://acc102dataappuct-upwxyky4ni7hklvbaerz2r.streamlit.app/#arizona-restaurant-analysis-system)
- **Demo Video**: [1-3 minute screen recording showing full analysis workflow]

---

## 7. Limitations & Next Steps

### Data & Sampling Limitations

The dataset was last updated in February 2021, missing post-pandemic dining behavior shifts such as increased delivery reliance and outdoor seating preferences. To manage computational load, the analysis caps reviews at 500,000 total and 30 per restaurant, with check-ins limited to 100 per restaurant—this balanced sampling approach may miss rare events. Review comments are truncated to 300 characters, preserving core sentiment signals but potentially losing nuanced context.

### Data Gap Limitations

The dataset lacks price level information, preventing cost-effectiveness from factoring into recommendations. Amenities such as parking availability, Wi-Fi, accessibility features, and reservation systems are not included. Exact operating hours are unavailable, meaning "optimal visit time" recommendations assume standard schedules. Menu details and dietary restriction information are absent, limiting assessment of cuisine authenticity and accommodation needs.

### Demographic & Behavioral Biases

Yelp reviewers skew younger and more tech-savvy, potentially underrepresenting preferences of families, seniors, and non-English speakers. Check-in data reflects only Yelp user patterns, not all customers. The 2021 cutoff misses post-pandemic behavioral shifts including changed tipping norms and health protocol expectations.

### Methodological Limitations

Cuisine classification relies on keyword mapping that may misclassify hybrid restaurants such as "Asian Fusion." Sentiment analysis uses predefined word lists lacking contextual nuance compared to advanced NLP models. Smart Score weights are heuristic-based rather than validated through consumer preference research or machine learning optimization. Results are geographically limited to Arizona and do not generalize to other markets.

---

### Next Steps

#### High Priority (Immediate Improvements)

- Integrate Yelp API for real-time data, price/amenities filtering
- Optimize sampling & add outlier detection for data robustness
- Refine cuisine classification with conflict resolution & validation

#### Medium Priority (Mid-Term Enhancements)

- Upgrade sentiment analysis to context-aware NLP models
- Validate & optimize Smart Score weights via user testing
- Expand geographic coverage with regional calibration

#### Low Priority (Long-Term Enhancements)

- Develop multi-label cuisine classification
- Build mobile-optimized UI & real-time alert features
