import streamlit as st
import pandas as pd
import requests
import numpy as np
import json

session = requests.session()

st.title('FPL Pot Luck 2021/22')

DATE_COLUMN = 'date/time'

user_ids = [
  1998244,
  2100704,
  4297443,
  2215795,
  2054675,
  2065677,
  5415392,
  5859065
]

names = {
  1998244: "ultimos / Timothy Lui",
  2100704: "sainzz laurenzo / Lauren K",
  4297443: "O, Mane, Honey / Chen ming Cheong",
  2215795: "thierene / Joshua Jeyaraj",
  2054675: "Frootloops Avenger / Luke Wu",
  2065677: "Thierry Henry FC / Guillaume Charleton",
  5415392: "It ends in Tierneys / Henry Liu",
  5859065: "Lanheim Palace / ian chai"
}

@st.cache
def get_general_information():
  response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
  return response

@st.cache
def get_current_gameweek(gen_info):
  gen_info = json.loads(gen_info.text)
  current_gameweek = [ i for i in gen_info['events'] if i['is_current'] == True ][0]['id']
  current_gameweek = str(current_gameweek)
  return current_gameweek

@st.cache
def load_points(user_ids, event_num):
  points_dict = {}

  for user in user_ids:
    response = session.get(f'https://fantasy.premierleague.com/api/entry/{user}/event/{event_num}/picks/')
    # points = response.text['points']
    entry = json.loads(response.text)
    entry = entry['entry_history']
    points = entry['points']
    total_points = entry['total_points']
    transfers = entry['event_transfers']
    transfer_penalty = entry['event_transfers_cost']
    points_dict[names[user]] = [points, transfers, transfer_penalty, total_points]

  points_df = pd.DataFrame.from_dict(points_dict, orient='index', columns=['Points', 'Transfers', 'Transfer Penalty', 'Total Points'])
  return points_df

@st.cache
def load_history(user_ids):
  history_dict = {}
  for user in user_ids:
    response = session.get(f'https://fantasy.premierleague.com/api/entry/{user}/history/')
    entry = json.loads(response.text)
    history_dict[names[user]] = entry
  return history_dict

data_load_state = st.text('Loading data...')
gen_info = get_general_information()
current_gameweek = get_current_gameweek(gen_info)
history = load_history(user_ids)
points_df = load_points(user_ids, current_gameweek)
data_load_state.text("Data loaded")

st.header(f"Gameweek {current_gameweek} Summary")
points_df

dollar_values = [0.00, 0.50, 1.25, 2.00, 2.75, 3.50, 4.25, 5.00]
dollar_values_mapping = { n+1: v for n, v in enumerate(dollar_values) }

payout_struct = { n: v for n, v in enumerate(dollar_values) }
payout_structure_pd = pd.DataFrame.from_dict(payout_struct, orient='index', columns=['S$'])
payout_structure_pd['%'] = payout_structure_pd['S$'] / payout_structure_pd['S$'].sum()
total_weekly_pot = payout_structure_pd['S$'].sum()

st.header("Stats")
option = st.selectbox('Pick a metric',('Transfer Penalty', 'Points', 'Rank', 'Payout', 'Cumulative Points', 'Cumulative Rank', 'Points on Bench'))
st.write('You selected:', option)

weeks = [ i for i in range(1, int(current_gameweek)+1)]
# weeks

# history
# for k in history:
#   for i in history[k]["current"]:
#     st.write(i)
#     for l in i["event_transfers_cost"]:
#       st.write(k, l)


transfer_penalty_dict = { k: [ i["event_transfers_cost"] for i in history[k]["current"]] for k in history for i in history[k]["current"] }
points_dict = { k: [i['points'] for i in history[k]["current"]] for k in history for i in history[k]["current"] }
cumulative_pts_dict = { k: [i['total_points'] for i in history[k]["current"]] for k in history for i in history[k]["current"] }
points_bench_dict = { k: [i['points_on_bench'] for i in history[k]["current"]] for k in history for i in history[k]["current"] }

# transfer_penalty_dict
transfer_penalty_pd = pd.DataFrame.from_dict(transfer_penalty_dict, orient='index', columns=weeks)
points_pd = pd.DataFrame.from_dict(points_dict, orient='index', columns=weeks)
rank_pd = points_pd.rank(ascending=False).astype(int)
# rank_pd = points_pd.rank(ascending=False)

cumulative_pts_pd = pd.DataFrame.from_dict(cumulative_pts_dict, orient='index', columns=weeks)
payout_pd = rank_pd.applymap(lambda x: dollar_values_mapping[x])


cumulative_rank_pd = cumulative_pts_pd.rank(ascending=False).astype(int)
points_bench_pd = pd.DataFrame.from_dict(points_bench_dict, orient='index', columns=weeks)
# st.subheader("INSERT PAYOUT GRAPH")

if option == 'Transfer Penalty':
  transfer_penalty_pd
elif option == 'Points':
  points_pd
elif option == 'Rank':
  rank_pd
elif option == 'Cumulative Points':
  cumulative_pts_pd
elif option == 'Cumulative Rank':
  cumulative_rank_pd
elif option == 'Points on Bench':
  points_bench_pd
elif option == 'Payout':
  payout_pd

st.header("Payout Structure")

payout_structure_pd
st.number_input('Incremental (2nd to 8th)', None, None, 0.75, None, key="increment")
st.caption(f"Total weekly pot: {total_weekly_pot}")

mid_season_total= total_weekly_pot*5
end_season_total= total_weekly_pot*10
mid_season_values = payout_structure_pd['%']*mid_season_total
end_season_values = payout_structure_pd['%']*end_season_total

mid_season_struct = { n: v for n, v in enumerate(mid_season_values) }
mid_season_struct_pd = pd.DataFrame.from_dict(mid_season_struct, orient='index', columns=['S$'])
mid_season_struct_pd['%'] = payout_structure_pd['%']
st.subheader("Mid-season")
mid_season_struct_pd
st.caption(f"Total: {mid_season_total}")

end_season_struct = { n: v for n, v in enumerate(end_season_values) }
end_season_struct_pd = pd.DataFrame.from_dict(end_season_struct, orient='index', columns=['S$'])
end_season_struct_pd['%'] = payout_structure_pd['%']
st.subheader("End-season")
end_season_struct_pd
st.caption(f"Total: {end_season_total}")

total_pot = total_weekly_pot * 38 + mid_season_total + end_season_total
pot_person = total_pot / len(user_ids)
max_loss = dollar_values[-1] * 38 + mid_season_values.iloc[-1] + end_season_values.iloc[-1]
st.subheader(f"Total Pot: {total_pot}")
st.subheader(f"Pot/person: {pot_person}")
st.subheader(f"Max loss: {max_loss}")

st.header("Summary payout")


