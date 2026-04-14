import streamlit as st
import pandas as pd
import pickle
import numpy as np
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="Arizona Restaurant Analysis System", layout="wide")

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    required_files = ['restaurants.parquet', 'reviews.pkl', 'checkin.pkl']
    for f in required_files:
        if not os.path.exists(f"{SAVE_DIR}/{f}"):
            st.error(f"Missing data file: {f}")
            st.stop()
    
    df = pd.read_parquet(f"{SAVE_DIR}/restaurants.parquet")
    with open(f"{SAVE_DIR}/reviews.pkl", "rb") as f:
        reviews = pickle.load(f)
    with open(f"{SAVE_DIR}/checkin.pkl", "rb") as f:
        checkin = pickle.load(f)
    
    df["business_id"] = df["business_id"].astype(str)
    reviews = {str(k): v for k, v in reviews.items()}
    checkin = {str(k): v for k, v in checkin.items()}
    
    return df, reviews, checkin

df_restaurants, reviews_dict, checkin_dict = load_data()

POS_WORDS = ["delicious","friendly","clean","great","good","fresh","tasty","excellent","fast","nice","amazing","love","best"]
NEG_WORDS = ["slow","rude","dirty","bad","cold","overpriced","bland","wait","long","disappointing","terrible","awful"]

def get_sentiment_stats(reviews):
    total = len(reviews)
    if total == 0:
        return 0, 0, 0, 0, 0
    pos = sum(1 for r in reviews if r["stars"] >= 4)
    neg = sum(1 for r in reviews if r["stars"] <= 2)
    neu = total - pos - neg
    pos_rate = pos / total * 100 if total > 0 else 0
    return pos_rate, 0, pos, neg, neu

def get_keywords_table(reviews, top_n=10):
    pos_cnt, neg_cnt = Counter(), Counter()
    for r in reviews:
        txt = str(r.get("comment", "")).lower()
        for w in POS_WORDS:
            if w in txt:
                pos_cnt[w] += 1
        for w in NEG_WORDS:
            if w in txt:
                neg_cnt[w] += 1
    return pos_cnt.most_common(top_n), neg_cnt.most_common(top_n)

def get_monthly_trend(target_rest, reviews):
    if not reviews:
        return None, 0, 0
    
    target_data = []
    for r in reviews:
        d, s = r.get("date"), r.get("stars")
        if not d or not s:
            continue
        try:
            dt = pd.to_datetime(d, errors='coerce')
            if pd.isna(dt):
                continue
            target_data.append({"month": dt.strftime("%Y-%m"), "rating": float(s), "type": "This Restaurant"})
        except:
            continue
    
    if len(target_data) < 2:
        return None, len(target_data), 0
    
    cuisine = target_rest.get("cuisine", "Unknown")
    all_data = []
    for biz_id, rev_list in reviews_dict.items():
        rest = df_restaurants[df_restaurants["business_id"] == biz_id]
        if not rest.empty and rest.iloc[0].get("cuisine") == cuisine:
            for r in rev_list:
                d, s = r.get("date"), r.get("stars")
                if not d or not s:
                    continue
                try:
                    dt = pd.to_datetime(d, errors='coerce')
                    if pd.isna(dt):
                        continue
                    all_data.append({"month": dt.strftime("%Y-%m"), "rating": float(s), "type": "Cuisine Average"})
                except:
                    continue
    
    df_target = pd.DataFrame(target_data)
    df_all = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    target_monthly = df_target.groupby("month")["rating"].mean().reset_index()
    target_monthly["type"] = "This Restaurant"
    
    if not df_all.empty:
        all_monthly = df_all.groupby("month")["rating"].mean().reset_index()
        all_monthly["type"] = "Cuisine Average"
        combined = pd.concat([target_monthly, all_monthly], ignore_index=True)
    else:
        combined = target_monthly
    
    return combined, len(target_data), len(all_data)

def get_hourly_traffic(checkin):
    if not checkin or not isinstance(checkin, dict):
        return [0]*24, []
    hourly = checkin.get("hourly", {})
    if not hourly:
        return [0]*24, []
    
    counts = [0]*24
    for k, v in hourly.items():
        try:
            h = int(str(k).replace("h", "").replace("H", ""))
            if 0 <= h < 24:
                counts[h] = int(v)
        except:
            continue
    
    peaks = sorted(range(24), key=lambda x: counts[x], reverse=True)[:3]
    peaks = [h for h in peaks if counts[h] > 0]
    return counts, peaks

def calculate_smart_score(rest, reviews, checkin):
    stars = rest.get("stars", 0)
    base_score = round(stars * 8, 1)
    
    pos_rate, _, _, _, _ = get_sentiment_stats(reviews)
    quality_score = round(pos_rate * 0.3, 1)
    
    review_count = len(reviews)
    volume_score = round(min(review_count / 50 * 10, 10), 1)
    
    total_checkin = checkin.get("total_checkin", 0) if isinstance(checkin, dict) else 0
    activity_score = round(min(total_checkin / 200 * 20, 20), 1)
    
    peak_bonus = 5 if (isinstance(checkin, dict) and checkin.get("peak_hour")) else 0
    
    total = round(min(base_score + quality_score + volume_score + activity_score + peak_bonus, 100), 1)
    
    breakdown = {
        "Base Rating (40%)": base_score,
        "Review Quality (30%)": quality_score,
        "Review Volume (10%)": volume_score,
        "Check-in Activity (20%)": activity_score,
        "Peak Hour Bonus (5%)": peak_bonus,
        "Total": total
    }
    return total, breakdown

def evaluate_sentiment_level(pos_rate):
    if pos_rate >= 85:
        return "Excellent"
    elif pos_rate >= 70:
        return "Good"
    elif pos_rate >= 50:
        return "Average"
    else:
        return "Below Average"

def evaluate_trend(trend_df):
    if trend_df is None or trend_df.empty:
        return None
    target_data = trend_df[trend_df["type"] == "This Restaurant"]
    avg_data = trend_df[trend_df["type"] == "Cuisine Average"]
    if target_data.empty or avg_data.empty:
        return None
    
    merged = target_data.merge(avg_data, on="month", suffixes=("_target", "_avg"))
    above = (merged["rating_target"] > merged["rating_avg"]).sum()
    total = len(merged)
    ratio = above / total * 100 if total > 0 else 0
    
    recent = merged["rating_target"].iloc[-3:].mean() if len(merged) >= 3 else merged["rating_target"].mean()
    early = merged["rating_target"].iloc[:3:].mean() if len(merged) >= 3 else merged["rating_target"].mean()
    
    if recent > early + 0.15:
        direction = "Improving"
    elif recent > early - 0.15:
        direction = "Stable"
    else:
        direction = "Declining"
    
    return {
        "ratio": round(ratio, 1),
        "above_months": above,
        "total_months": total,
        "direction": direction,
        "latest": round(merged["rating_target"].iloc[-1], 2) if len(merged) > 0 else None
    }

def evaluate_hourly(reviews, hourly_counts):
    if not reviews:
        return None
    
    hourly_ratings = {}
    for r in reviews:
        try:
            dt = pd.to_datetime(r.get("date", ""))
            h = dt.hour
            if h not in hourly_ratings:
                hourly_ratings[h] = []
            hourly_ratings[h].append(r.get("stars", 0))
        except:
            continue
    
    stats = {}
    for h, ratings in hourly_ratings.items():
        if len(ratings) >= 3:
            stats[h] = {
                "avg": round(sum(ratings)/len(ratings), 2),
                "count": len(ratings),
                "traffic": hourly_counts[h] if h < len(hourly_counts) else 0
            }
    
    if not stats:
        return None
    
    best = [h for h, s in sorted(stats.items(), key=lambda x: x[1]["avg"], reverse=True) 
            if s["avg"] >= 4.0 and s["traffic"] < sum(hourly_counts)/24 * 0.7][:2]
    
    problems = [h for h, s in sorted(stats.items(), key=lambda x: x[1]["traffic"], reverse=True)[:3] 
                if s["avg"] < 3.5]
    
    return {
        "stats": stats,
        "best_hours": best,
        "problem_hours": problems
    }

def calculate_total_score(pos_rate, trend_eval, hourly_eval, smart_score):
    s = 25 if pos_rate >= 85 else 20 if pos_rate >= 70 else 12 if pos_rate >= 50 else 5
    
    if trend_eval:
        t_base = 25 if trend_eval["ratio"] >= 80 else 20 if trend_eval["ratio"] >= 60 else 12 if trend_eval["ratio"] >= 40 else 5
        adj = 2 if trend_eval["direction"] == "Improving" else -3 if trend_eval["direction"] == "Declining" else 0
        t = max(0, min(25, t_base + adj))
    else:
        t = 15
    
    if hourly_eval:
        h_base = 25 if len(hourly_eval["best_hours"]) >= 2 else 20 if len(hourly_eval["best_hours"]) == 1 else 15
        h = max(0, h_base - len(hourly_eval["problem_hours"]) * 5)
    else:
        h = 15
    
    ss = round(min(25, smart_score / 4))
    total = s + t + h + ss
    
    grade = "Highly Recommended" if total >= 85 else "Recommended" if total >= 70 else "Worth Considering" if total >= 55 else "Proceed with Caution"
    
    return {
        "total": total,
        "grade": grade,
        "breakdown": [
            {"Component": "Review Sentiment (25%)", "Input": f"{pos_rate:.1f}% positive", "Score": s, "Max": 25},
            {"Component": "Rating Trend (25%)", "Input": f"{trend_eval['ratio']:.1f}% above avg, {trend_eval['direction']}" if trend_eval else "N/A", "Score": t, "Max": 25},
            {"Component": "Hourly Experience (25%)", "Input": f"{len(hourly_eval['best_hours'])} optimal hours, {len(hourly_eval['problem_hours'])} problem hours" if hourly_eval else "N/A", "Score": h, "Max": 25},
            {"Component": "Smart Score (25%)", "Input": f"{smart_score}/100", "Score": ss, "Max": 25}
        ],
        "formula": f"{s} + {t} + {h} + {ss} = {total}"
    }

# ========== MAIN ==========

st.title("Arizona Restaurant Analysis System")

st.subheader("Step 1: Select Cuisine")
cuisine_list = sorted(df_restaurants["cuisine"].dropna().unique())
selected_cuisine = st.selectbox("Cuisine Type", cuisine_list)

st.subheader("Step 2: Set Minimum Star Rating")
min_rating = st.slider("Minimum Stars", 2.0, 5.0, 3.5, 0.5)

filtered = df_restaurants[
    (df_restaurants["cuisine"] == selected_cuisine) &
    (df_restaurants["stars"] >= min_rating)
].copy()

st.subheader("Step 3: Restaurant List")
if filtered.empty:
    st.warning("No restaurants match your criteria.")
    st.stop()

show_df = filtered[["name","city","stars","review_count"]].reset_index(drop=True)
show_df.index = show_df.index + 1
st.dataframe(show_df, use_container_width=True, height=300)

st.subheader("Step 4: Select Restaurant")
options = [f"{idx} - {row['name']}" for idx, row in show_df.iterrows()]
selected_option = st.selectbox("Index", options)
idx = int(selected_option.split(' - ')[0])

if st.button("Start Full Analysis", type="primary", use_container_width=True):
    target = filtered.iloc[idx - 1]
    biz_id = str(target["business_id"])
    
    reviews = reviews_dict.get(biz_id, [])
    checkin = checkin_dict.get(biz_id, {})
    hourly_counts, peaks = get_hourly_traffic(checkin)
    
    pos_rate, _, pos_cnt, neg_cnt, neu_cnt = get_sentiment_stats(reviews)
    sentiment_level = evaluate_sentiment_level(pos_rate)
    
    trend_df, _, _ = get_monthly_trend(target, reviews)
    trend_eval = evaluate_trend(trend_df)
    
    hourly_eval = evaluate_hourly(reviews, hourly_counts)
    
    smart_score, smart_breakdown = calculate_smart_score(target, reviews, checkin)
    
    total_eval = calculate_total_score(pos_rate, trend_eval, hourly_eval, smart_score)
    
    # OVERVIEW
    st.divider()
    st.header("Assessment Overview")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(total_eval["grade"])
        st.metric("Total Score", f"{total_eval['total']}/100")
        st.caption(f"Formula: {total_eval['formula']}")
    with col2:
        issues = []
        if pos_rate < 70:
            issues.append("sentiment below 70%")
        if trend_eval and trend_eval["ratio"] < 50:
            issues.append("trend below category average")
        if hourly_eval and hourly_eval["problem_hours"]:
            issues.append("service drops at peak hours")
        if trend_eval and trend_eval["direction"] == "Declining":
            issues.append("recent decline")
        
        if issues:
            st.warning("Note: " + "; ".join(issues))
    
    st.subheader("Score Calculation")
    st.dataframe(pd.DataFrame(total_eval["breakdown"]), hide_index=True)
    st.write(f"**Total: {total_eval['formula']}**")
    
    st.subheader("Performance Dimensions")
    dim = st.columns(4)
    
    with dim[0]:
        st.metric("Review Sentiment", sentiment_level)
        st.caption(f"{pos_rate:.1f}% positive")
    
    with dim[1]:
        if trend_eval:
            st.metric("Rating Trend", f"{trend_eval['ratio']}% above avg")
            st.caption(f"{trend_eval['direction']}, latest: {trend_eval['latest']} stars")
        else:
            st.metric("Rating Trend", "No data")
    
    with dim[2]:
        if hourly_eval and hourly_eval["best_hours"]:
            st.metric("Best Times", ", ".join([f"{h:02d}:00" for h in hourly_eval["best_hours"]]))
        else:
            st.metric("Best Times", "No data")
    
    with dim[3]:
        st.metric("Smart Score", f"{smart_score}/100")
        st.caption(f"Base: {smart_breakdown['Base Rating (40%)']}, Quality: {smart_breakdown['Review Quality (30%)']}")
    
    st.divider()
    
    # 1. SENTIMENT
    st.subheader("1. Review Sentiment Analysis")
    
    if pos_cnt + neg_cnt + neu_cnt > 0:
        total = pos_cnt + neg_cnt + neu_cnt
        st.write(f"**Total: {total} reviews** | Positive: {pos_cnt} ({pos_cnt/total*100:.1f}%) | Neutral: {neu_cnt} | Negative: {neg_cnt}")
        
        st.markdown("**Assessment:**")
        if pos_rate >= 80:
            st.write("Overall sentiment is **strongly positive**. Most customers report satisfactory experiences.")
        elif pos_rate >= 70:
            st.write("Overall sentiment is **positive**. Most customers are satisfied, though some issues exist.")
        elif pos_rate >= 60:
            st.write("Sentiment is **mixed**. Satisfied customers exist, but notable concerns appear.")
        else:
            st.write("Sentiment is **concerning**. Negative feedback is significant.")
        
        st.markdown("**Specific Concerns:**")
        concerns = []
        _, neg_top = get_keywords_table(reviews, 5)
        if neg_top:
            concerns.append(f"Negative terms: {', '.join([t for t, c in neg_top[:3]])}")
        if neg_cnt / total > 0.25:
            concerns.append(f"High negative proportion ({neg_cnt/total*100:.1f}%)")
        if trend_eval and trend_eval["direction"] == "Declining":
            concerns.append("Recent ratings declining")
        
        if concerns:
            for c in concerns:
                st.write(f"- {c}")
        else:
            st.write("- No major concern patterns identified")
        
        pie_df = pd.DataFrame({"Sentiment": ["Positive", "Negative", "Neutral"], "Count": [pos_cnt, neg_cnt, neu_cnt]})
        fig = px.pie(pie_df, values="Count", names="Sentiment", color="Sentiment",
                    color_discrete_map={"Positive": "#2ECC71", "Negative": "#E74C3C", "Neutral": "#F39C12"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No review data available.")
    
    st.divider()
    
    # 2. KEYWORDS
    st.subheader("2. Frequently Mentioned Terms")
    pos_top, neg_top = get_keywords_table(reviews, 10)
    
    kc = st.columns(2)
    with kc[0]:
        st.write("**Positive:**")
        if pos_top:
            st.dataframe(pd.DataFrame(pos_top, columns=["Term", "Count"]), hide_index=True)
        else:
            st.caption("None found")
    with kc[1]:
        st.write("**Negative:**")
        if neg_top:
            st.dataframe(pd.DataFrame(neg_top, columns=["Term", "Count"]), hide_index=True)
        else:
            st.caption("None found")
    
    st.divider()
    
    # 3. TREND
    st.subheader("3. Monthly Rating Trend")
    if trend_df is not None and not trend_df.empty:
        fig = px.line(trend_df, x="month", y="rating", color="type", markers=True)
        fig.add_hline(y=target["stars"], line_dash="dash", annotation_text="Overall Avg")
        st.plotly_chart(fig, use_container_width=True)
        
        if trend_eval:
            st.write(f"Above category average: {trend_eval['ratio']}% of months ({trend_eval['above_months']}/{trend_eval['total_months']})")
            st.write(f"Recent direction: {trend_eval['direction']}")
    else:
        st.info("Insufficient trend data.")
    
    st.divider()
    
    # 4. HOURLY
    st.subheader("4. Hourly Traffic and Service Quality")
    if sum(hourly_counts) > 0:
        hours = list(range(24))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"{h:02d}:00" for h in hours],
            y=hourly_counts,
            name="Traffic",
            marker_color=["#E74C3C" if h in peaks else "#3498DB" for h in hours]
        ))
        
        if hourly_eval and hourly_eval["stats"]:
            sat_x, sat_y = [], []
            for h, s in sorted(hourly_eval["stats"].items()):
                sat_x.append(f"{h:02d}:00")
                sat_y.append(s["avg"] * max(hourly_counts)/5)
            fig.add_trace(go.Scatter(x=sat_x, y=sat_y, name="Rating (scaled)", mode="lines+markers", yaxis="y2"))
        
        fig.update_layout(
            yaxis2=dict(title="Rating", overlaying="y", side="right", range=[0, max(hourly_counts)]),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if hourly_eval:
            if hourly_eval["best_hours"]:
                st.write(f"**Optimal visit times:** {', '.join([f'{h:02d}:00' for h in hourly_eval['best_hours']])} (good ratings, lower crowd)")
            if hourly_eval["problem_hours"]:
                st.write(f"**Caution:** Service quality drops during busy periods ({', '.join([f'{h:02d}:00' for h in hourly_eval['problem_hours']])})")
    else:
        st.info("No hourly data available.")
    
    st.divider()
    
    # 5. SMART SCORE
    st.subheader("5. Smart Score Breakdown")
    st.metric("Total", f"{smart_score}/100")
    score_table = [{"Component": k, "Score": v} for k, v in smart_breakdown.items() if k != "Total"]
    st.dataframe(pd.DataFrame(score_table), hide_index=True)
