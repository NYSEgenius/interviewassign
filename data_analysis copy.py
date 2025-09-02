# Lucid Assignment
# Author: Turner Cox
# Version: 11-26-2024
import pandas as pd

# Load datasets
visits = pd.read_csv("visits_-_analytics_hw_-_visits_-_analytics_hw.csv")
subscriptions = pd.read_csv("subscriptions_-_analytics_hw_-_subscriptions_-_analytics_hw.csv")
costs = pd.read_csv("costs_-_analytics_hw_-_costs_-_analytics_hw.csv")


# Helper function to format monetary values
def format_currency(value):
    return f"${value:,.2f}"


# Helper function to safely find the index of the max value
def safe_idxmax(series):
    return series.idxmax() if not series.empty else None


# Functions

# Q1: Calculate total revenue per region
def sum_revenue():
    merged_data = pd.merge(visits, subscriptions, on="ACCOUNT_ID", how="inner")
    region_revenue = merged_data.groupby("REGION")["REVENUE"].sum().reset_index().sort_values(by="REGION")
    region_revenue["REVENUE"] = region_revenue["REVENUE"].apply(format_currency)
    print(region_revenue)


# Q2: Identify the landing page with the highest conversion rate
def calculate_conversion():
    merged_data = pd.merge(visits, subscriptions, on="ACCOUNT_ID", how="left")
    grouped = merged_data.groupby("LANDING_PAGE").agg(
        total_visits=("VISIT_ID", "count"),
        total_subscriptions=("SUBSCRIPTION_START_DATE", "count")
    ).reset_index()

    # Calculate conversion rate for each landing page
    grouped["conversion_rate"] = grouped["total_subscriptions"] / grouped["total_visits"]
    # Find the highest conversion rate
    best_page = grouped.loc[safe_idxmax(grouped["conversion_rate"])]
    print(
        f"The landing page with the highest overall conversion rate is landing page {best_page['LANDING_PAGE']} "
        f"with a conversion rate of {best_page['conversion_rate']:.2%}."
    )


# Q3: Identify regions with different top converting landing pages compared to the overall best page
def regional_conversion():
    merged_data = pd.merge(visits, subscriptions, on="ACCOUNT_ID", how="left")
    grouped = merged_data.groupby(["REGION", "LANDING_PAGE"]).agg(
        total_visits=("VISIT_ID", "count"),
        total_subscriptions=("SUBSCRIPTION_START_DATE", "count")
    ).reset_index()

    # Calculate conversion rate for each region's landing page
    grouped["conversion_rate"] = grouped["total_subscriptions"] / grouped["total_visits"]
    # Find the top converting landing page in each region
    top_pages = grouped.loc[grouped.groupby("REGION")["conversion_rate"].apply(safe_idxmax)]
    # Determine the overall best converting landing page across all regions
    overall_best_page = grouped.groupby("LANDING_PAGE").agg(
        total_visits=("total_visits", "sum"),
        total_subscriptions=("total_subscriptions", "sum")
    ).reset_index()
    overall_best_page["conversion_rate"] = overall_best_page["total_subscriptions"] / overall_best_page["total_visits"]
    best_page = overall_best_page.loc[safe_idxmax(overall_best_page["conversion_rate"])]

    print("Regions with different top converting landing pages:\n")
    flag = False
    for _, row in top_pages.iterrows():
        if row["LANDING_PAGE"] != best_page["LANDING_PAGE"]:
            print(f"Region: {row['REGION']}")
            print(f"Top Landing Page: {row['LANDING_PAGE']}")
            print(f"Conversion Rate: {row['conversion_rate']:.2%}\n")
            flag = True
    if not flag:  # If there is no region with a different top converting landing page...
        print("There are no regions with different top converting landing pages.")


# Q4: Calculate the direct subscription rate per region
def calculate_direct_subscription_rate():
    merged_data = pd.merge(visits, subscriptions, on="ACCOUNT_ID", how="left")
    direct_subscriptions = merged_data["SUBSCRIPTION_START_DATE"].notna() & merged_data["TRIAL_START_DATE"].isna()

    # Group by region and calculate total visits and direct subscriptions
    regional_stats = merged_data.groupby("REGION").agg(
        total_visits=("VISIT_ID", "count"),
        direct_subscriptions=("SUBSCRIPTION_START_DATE", lambda x: direct_subscriptions[x.index].sum())
    ).reset_index()

    # Calculate direct subscription rate for each region
    regional_stats["direct_subscription_rate"] = regional_stats["direct_subscriptions"] / regional_stats["total_visits"]
    # Identify the region with the highest direct subscription rate
    best_region = regional_stats.loc[safe_idxmax(regional_stats["direct_subscription_rate"])]

    print(f"The region with the highest direct subscription rate is {best_region['REGION']} "
          f"with a direct subscription rate of {best_region['direct_subscription_rate']:.2%}.")


# Q5: Calculate the trial conversion rate per region
def calculate_trial_conversion_rate():
    merged_data = pd.merge(visits, subscriptions, on="ACCOUNT_ID", how="left")
    trials = merged_data[merged_data["TRIAL_START_DATE"].notna()]
    regional_stats = trials.groupby("REGION").agg(
        total_trials=("TRIAL_START_DATE", "count"),
        converted_trials=("SUBSCRIPTION_START_DATE", lambda x: x.notna().sum())
    ).reset_index()

    # Calculate the trial conversion rate
    regional_stats["trial_conversion_rate"] = regional_stats["converted_trials"] / regional_stats["total_trials"]
    # Identify the region with the highest trial conversion rate
    best_region = regional_stats.loc[safe_idxmax(regional_stats["trial_conversion_rate"])]

    print(f"The region with the highest trial conversion rate is {best_region['REGION']} "
          f"with a trial conversion rate of {best_region['trial_conversion_rate']:.2%}.")


# Q6: Find the most profitable marketing channel in 2022
def most_profitable_channel_2022():
    # Filter visits for the year 2022
    visits_2022 = visits[pd.to_datetime(visits["DAY"]).dt.year == 2022]
    merged_data = pd.merge(visits_2022, subscriptions, on="ACCOUNT_ID", how="left")

    # Calculate revenue and expenses per channel
    revenue_by_channel = merged_data.groupby("CHANNEL")["REVENUE"].sum()
    visits_by_channel = visits_2022.groupby("CHANNEL")["VISIT_ID"].count()
    channel_data = costs.set_index("CHANNEL").join(
        revenue_by_channel.rename("total_revenue")
    ).join(visits_by_channel.rename("total_visits"))

    # Calculate total expenses and profit per channel
    channel_data["total_expenses"] = channel_data["FIXED_COST"] + channel_data["COST_PER_VISIT"] * channel_data[
        "total_visits"]
    channel_data["profit"] = channel_data["total_revenue"] - channel_data["total_expenses"]
    # Identify the most profitable channel
    most_profitable = channel_data.loc[safe_idxmax(channel_data["profit"])]

    print(f"The most profitable channel in 2022 is {most_profitable.name} "
          f"with an annual profit of {format_currency(most_profitable['profit'])}.")


# Q7: Calculate the average revenue per visit for the video channel
def average_revenue_per_visit_video():
    video_visits = visits[visits["CHANNEL"] == "video"]
    video_data = pd.merge(video_visits, subscriptions, on="ACCOUNT_ID", how="left")

    # Calculate total revenue and visits for the video channel
    total_revenue_video = video_data["REVENUE"].sum()
    total_visits_video = video_visits["VISIT_ID"].count()
    # Calculate average revenue per visit
    average_revenue = total_revenue_video / total_visits_video

    print(f"The average revenue per visit to the video channel is {format_currency(average_revenue)}.")


if __name__ == '__main__':
    print("Question 1:\n")
    sum_revenue()
    print("\nQuestion 2:\n")
    calculate_conversion()
    print("\nQuestion 3:\n")
    regional_conversion()
    print("\nQuestion 4:\n")
    calculate_direct_subscription_rate()
    print("\nQuestion 5:\n")
    calculate_trial_conversion_rate()
    print("\nQuestion 6:\n")
    most_profitable_channel_2022()
    print("\nQuestion 7:\n")
    average_revenue_per_visit_video()
