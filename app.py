import pandas as pd
import streamlit as st
import json
import geopandas as gpd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Just another Malaysia COVID-19 Dashboard", page_icon="🦠", layout="wide", menu_items={'Report a Bug': "https://github.com/JustinTzeJi/malaysia-covid-dashboard/issues",'About': "An experiment"})

def map_plot(gdf,state_option=None):
	token = st.secrets["map_token"]
	if gdf['active_cases_per_pop'].max() > 1:
		zmax=gdf['active_cases_per_pop'].max()
	else:
		zmax = 1
	states=state_json()
	if state_option == None:
		fig = go.Figure(go.Choroplethmapbox(geojson=states, locations=gdf.state, z=gdf.active_cases_per_pop, featureidkey='properties.shapeName',
											colorscale="temps", zmax=zmax, zmin=0,
											marker_opacity=0.9, marker_line_width=1,
											hovertemplate="<b>%{location}</b><br>" + "Population with active cases: %{z:.2f}%" + "<extra></extra>"))
		fig.update_layout(mapbox_style="satellite", mapbox_accesstoken=token,
						mapbox_zoom=5, mapbox_center = {"lat": 4.1, "lon": 109.5})
		fig.add_trace(go.Scattermapbox(	
				lat=gdf.geometry.centroid.y,
				lon=gdf.geometry.centroid.x,
				text=gdf.cases_new.astype(str).to_list(),
				customdata=gdf.cases_recovered.astype(str).to_list(),
				texttemplate="▲%{text}  ▼%{customdata}",
				textfont={"color":"white","size":12, 'family':'Overpass'},
				mode="text",
				hoverinfo='none',
				showlegend=False,
				name="New Cases and Recovered Cases"
			))

		fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="New Cases", marker=dict(size=7, color="gray", symbol='triangle-up')))
		fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Recovered Cases", marker=dict(size=7, color="gray", symbol='triangle-down')))
		fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="right", x=1),margin={"r":0,"t":0,"l":0,"b":0},xaxis_showticklabels=False,yaxis_showticklabels=False)
	else:
		selected = gdf[gdf.state==state_option]
		fig = go.Figure(go.Choroplethmapbox(geojson=states, locations=selected.state, z=selected.active_cases_per_pop, featureidkey='properties.shapeName',
										colorscale="temps", zmax=zmax, zmin=0,
										marker_opacity=0.9, marker_line_width=1,
										hovertemplate="<b>%{location}</b><br>" + "Population with active cases: %{z:.2f}%" + "<extra></extra>"))
		fig.update_layout(mapbox_style="satellite", mapbox_accesstoken=token,
						mapbox_zoom=7, mapbox_center = {"lat": selected.geometry.centroid.y[0], "lon": selected.geometry.centroid.x[0]})
		fig.add_trace(go.Scattermapbox(	
				lat=selected.geometry.centroid.y,
				lon=selected.geometry.centroid.x,
				text=selected.cases_new.astype(str).to_list(),
				customdata=selected.cases_recovered.astype(str).to_list(),
				texttemplate="▲%{text}  ▼%{customdata}",
				textfont={"color":"white","size":12, 'family':'Overpass'},
				mode="text",
				hoverinfo='none',
				showlegend=False,
				name="New Cases and Recovered Cases"
			))

		fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="New Cases", marker=dict(size=7, color="gray", symbol='triangle-up')))
		fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Recovered Cases", marker=dict(size=7, color="gray", symbol='triangle-down')))
		fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="right", x=1),margin={"r":0,"t":0,"l":0,"b":0},xaxis_showticklabels=False,yaxis_showticklabels=False)
	return fig

@st.experimental_memo
def data():
	state_case = pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_state.csv')
	population = pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/static/population.csv')
	national_case = pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_malaysia.csv')
	national_death = pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/deaths_malaysia.csv')
	state_death =pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/deaths_state.csv')
	events = pd.read_csv('event.csv')

	state_case['date'] = pd.to_datetime(state_case['date'],  format='%Y-%m-%d').dt.date
	latest = state_case[state_case['date'] == state_case['date'].max()]

	latest_stat = pd.merge(latest[['date','state','cases_new','cases_active','cases_recovered']], population[['state','pop']], on="state")
	latest_stat['active_cases_per_pop'] = latest_stat['cases_active']/latest_stat['pop'] * 100
	latest_stat['new_cases_per_pop'] = latest_stat['cases_new']/latest_stat['pop'] * 100
	latest_stat['log_active_cases_per_pop'] = np.log10(latest_stat['active_cases_per_pop'])
	latest_stat['log_new_cases_per_pop'] = np.log10(latest_stat['new_cases_per_pop'])

	latest_national = national_case[national_case['date'] == national_case['date'].max()]
	latest_national['state']='Malaysia'
	latest_national = pd.merge(latest_national, population[['state','pop']], on="state")
	latest_national['active_cases_per_pop'] = latest_national['cases_active']/latest_national['pop'] * 100

	national_case['date'] = pd.to_datetime(national_case['date'],  format='%Y-%m-%d').dt.date
	state_death['date'] = pd.to_datetime(state_death['date'],  format='%Y-%m-%d').dt.date
	
	gdf = gpd.GeoDataFrame.from_features(state_json()).rename(columns={'shapeName':'state'}).merge(latest_stat, on="state").assign(lat=lambda d: d.geometry.centroid.y, lon=lambda d: d.geometry.centroid.x).set_index("state", drop=False)
	
	return gdf,national_case, national_death, events, state_death, state_case

def state_json():
	with open('malaysia.geojson') as r:
		states = json.load(r)
	return states

def timeline(state_option=None):

	colorlist = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
	fig2 = make_subplots(specs=[[{"secondary_y": True}]])
	if state_option==None:
		fig2.add_trace(go.Scatter(x=national_death.date,y=national_death.deaths_new_dod, mode='lines', name='Deaths'), secondary_y=True)
		fig2.add_trace(go.Scatter(x=national_case.date,y=national_case.cases_new,  mode='lines', name='Cases'),secondary_y=False)
	else:
		fig2.add_trace(go.Scatter(x=state_death[state_death['state']==st.session_state.state_option].date,y=state_death[state_death['state']==st.session_state.state_option].deaths_new_dod, mode='lines', name='Deaths'), secondary_y=True)
		fig2.add_trace(go.Scatter(x=state_case[state_case['state']==st.session_state.state_option].date,y=state_case[state_case['state']==st.session_state.state_option].cases_new,  mode='lines', name='Cases'),secondary_y=False)

	for index,event in events.iterrows():
		fig2.add_vrect(x0=event.x0, x1=event.x1,
					annotation_text=event.Event, 
					fillcolor=colorlist[index], opacity=0.25, line_width=0)
	#------------------- no fix for plotly vline in datetime graph with annotation -------------------------
	# event_vert = pd.read_csv('event_vert.csv')
	# for index,event in event_vert.iterrows():
	# 	fig2.add_vline(x=event.x, line_dash="dash", annotation_text=event.Event, annotation_font_size=12) 
	fig2.update_yaxes(title_text="New Cases", secondary_y=False,showgrid=False, zeroline=False)
	fig2.update_yaxes(title_text="Deaths", secondary_y=True,showgrid=False, zeroline=False)
	fig2.update_xaxes(rangeslider_visible=True,showgrid=False)

	return fig2

gdf,national_case, national_death, events, state_death, state_case = data()

st.title("Just another Malaysia COVID-19 Dashboard")
'''
    [![Repo](https://badgen.net/badge/icon/GitHub?icon=github&label)](https://github.com/JustinTzeJi/malaysia-covid-dashboard) 

'''
st.markdown("<br>",unsafe_allow_html=True)	
st.info("Data updated on: `" + str(gdf['date'].max()) + "`", icon="ℹ️")	

tab1, tab2 = st.tabs(["Country", "State"])
with tab1:
	col1, col2, col3, col4 = st.columns(4)
	col5, col6, col7, col8 = st.columns(4)
	col1.metric("Current Active Cases", gdf['cases_active'].iloc[0].astype(str), (gdf['cases_new'].iloc[0]-gdf['cases_recovered'].iloc[0]).astype(str), 'inverse',help='Methodology for delta: ```new cases - cases recovered```')
	col2.metric("New Cases Today", gdf['cases_new'].iloc[0].astype(str))
	col3.metric("Recovered Cases Today", gdf['cases_recovered'].iloc[0].astype(str))
	col4.metric("Percentage of population infected", round(gdf['active_cases_per_pop'].iloc[0],3).astype(str)+'%', help='Methodology: ```active cases / population * 100%```')
	col5.metric("Total Deaths", national_death.deaths_new.sum(),national_death.deaths_new.iloc[-1].astype(str),'inverse',)
	col6.metric("Death Rate", round(national_death.deaths_new.sum()/national_case.cases_active.sum()*100,3).astype(str) +"%", help='Methodology: ```sum of deaths/sum of recorded cases * 100%```')

	with st.container():
		st.header('Infected population % by State')
		with st.expander('Methodology'):
			st.write('```active cases of state / population of state * 100%```')
		st.plotly_chart(map_plot(gdf,state_option=None), use_container_width=True)

	with st.container():
		st.header('Daily Reported Cases, Deaths and Timeline')
		st.plotly_chart(timeline(), use_container_width=True)


with tab2:
	col9, col10= st.columns([1,3])
	st.session_state.state_option = col9.selectbox('Select a State',gdf.state.unique())
	with st.container():
		col11, col12, col13, col14 = st.columns(4)
		col15, col16, col17, col18 = st.columns(4)
		col11.metric("Current Active Cases", gdf[gdf['state']==st.session_state.state_option]['cases_active'].iloc[0].astype(str), (gdf[gdf['state']==st.session_state.state_option]['cases_new'].iloc[0]-gdf[gdf['state']==st.session_state.state_option]['cases_recovered'].iloc[0]).astype(str), 'inverse',help='Methodology for delta: ```new cases - cases recovered```')
		col12.metric("New Cases Today", gdf[gdf['state']==st.session_state.state_option]['cases_new'].iloc[0].astype(str))
		col13.metric("Recovered Cases Today", gdf[gdf['state']==st.session_state.state_option]['cases_recovered'].iloc[0].astype(str))
		col14.metric("Percentage of population infected", round(gdf[gdf['state']==st.session_state.state_option]['active_cases_per_pop'].iloc[0],3).astype(str)+'%', help='Methodology: ```active cases / population * 100%```')
		col15.metric("Total Deaths", state_death[state_death['state']==st.session_state.state_option].deaths_new.sum(),state_death[state_death['state']==st.session_state.state_option].deaths_new.iloc[-1].astype(str),'inverse',)
		col16.metric("Death Rate", round(state_death[state_death['state']==st.session_state.state_option].deaths_new.sum()/state_case[state_case['state']==st.session_state.state_option].cases_active.sum()*100,3).astype(str) +"%", help='Methodology: ```sum of deaths/sum of recorded cases * 100%```')
		
		with st.container():
			st.header('Infected population % of ' + st.session_state.state_option)
			with st.expander('Methodology'):
				st.write('```active cases of state / population of state * 100%```')
			st.plotly_chart(map_plot(gdf,st.session_state.state_option), use_container_width=True)
		
		with st.container():
			st.header('Daily Reported Cases, Deaths and Timeline of '+ st.session_state.state_option)
			st.plotly_chart(timeline(st.session_state.state_option), use_container_width=True)

st.markdown("""
### Data Sources
1. Open data on COVID-19 in Malaysia, Ministry of Health Malaysia [[data repo](https://github.com/MoH-Malaysia/covid19-public)]
2. Malaysia - Subnational Administrative Boundaries, geoBoundaries [[website](https://www.geoboundaries.org)] [[data](https://data.humdata.org/dataset/geoboundaries-admin-boundaries-for-malaysia)]
3. Malaysian COVID-19 Timeline, Wikipedia [[Malaysian movement control order](https://en.wikipedia.org/wiki/Malaysian_movement_control_order)] [[COVID-19 vaccination in Malaysia](https://en.wikipedia.org/wiki/COVID-19_vaccination_in_Malaysia)]
""")	