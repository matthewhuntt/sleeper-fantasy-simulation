import json
import numpy as np
import requests
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as ani
import pandas as pd
import matplotlib.image as mpimg
import urllib.request
from PIL import Image
from io import BytesIO
from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
import decimal

matplotlib.use('TKAgg')

#import log of simulations and pivot
probability_log_df = pd.read_csv('WeeklySeedProbabilityLog.csv')
#probability_df = probability_log_df 
probability_df = pd.pivot_table(probability_log_df, values='success %', index='week', columns='display_name')
#probability_df = probability_df.set_index('week')

with urllib.request.urlopen("https://api.sleeper.app/v1/league/597593297883566080/users") as url:
    owners = json.loads(url.read().decode())
for owner in range(len(owners)):
	for datapoint in owners[owner]["metadata"]:
		owners[owner][datapoint] = owners[owner]["metadata"][datapoint]
	del owners[owner]["metadata"]

owners_df = pd.DataFrame(owners)
print(owners_df[['display_name','avatar']])

image_dict = {'AndersonBC': None}

for index, owner in owners_df.iterrows():
	print(owner['display_name'])
	#if 'https://sleepercdn.com/uploads/' not in owner['avatar']:
	
	try:
		response = requests.get(owner['avatar'])
		img = Image.open(BytesIO(response.content))
		image_dict[owner['display_name']] = img
		#img.show()
	except:
		try:
			owners_df.loc[index, 'avatar'] = 'https://sleepercdn.com/avatars/thumbs/' + owners_df.loc[index, 'avatar']
			response = requests.get(owner['avatar'])
			img = Image.open(BytesIO(response.content))
			image_dict[owner['display_name']] = img
			#img.show()
		except:	
			#first line ust to get around no picture for Brad
			image_dict[owner['display_name']] = image_dict['mhuntt']
			print(owner['avatar'] + ' failed')

print(image_dict)

for owner, image in image_dict.items():
	filename =  owner + '.png'
	image.save(filename)

def interpolator(probability_df, gran):
	"""
	Interpolate data points between weeks for smoother animation

	Args:
		gran: granularity of interpolation (number of steps between weeks)

	Returns:
		probability_df: interpolated df
	"""
	step = 1 / gran
	for week in probability_df.index[:-1]:
		for i in np.linspace(week + step, week + 1, gran - 1, endpoint=False):
			#create blank week row
			probability_df = probability_df.append(pd.Series(np.empty(12), name=i, index=probability_df.columns))
			for team in probability_df.columns:
				lower_score = probability_df.loc[week, team]
				upper_score = probability_df.loc[week + 1, team]
				probability_df.loc[i, team] = lower_score + (upper_score - lower_score) * (i - week)
	probability_df = probability_df.sort_index()
	return probability_df

gran = 50
probability_df = interpolator(probability_df, gran)

annotations = []

def chart_builder(frame=int):
	global annotations
	#plt.legend(probability_df.columns, bbox_to_anchor=(0, 1), loc='upper left', fontsize='xx-small')
	p = plt.plot(probability_df[:(4 + (frame + 1) / gran)].index, probability_df[:(4 + (frame + 1) / gran)].values)
	for x in range(12):
		p[x].set_color(colors[x])
	#if frame != 0:
	for annotation in annotations:
		annotation.remove()
	annotations = []
	for team in probability_df.columns:
		filename = team + '.png'
		#fn = get_sample_data(filename, asfileobj=False)
		#for images: arr_img = plt.imread(filename, format='png')
		#for images: annotations.append(plt.annotate(plt.imshow(arr_img), (probability_df.index[frame], probability_df.loc[probability_df.index[frame], team])))
		annotations.append(plt.annotate(team, (probability_df.index[frame], probability_df.loc[probability_df.index[frame], team]), alpha=.5, fontsize='x-small'))
	#return annotations


colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan', 'black', 'brown', 'red']

#format the chart
plt.style.use('ggplot')
fig = plt.figure()
plt.ylabel('Playoff Probability')
plt.xlabel('Week')
plt.xlim(4,13)
plt.ylim(0,1)
plt.title("Probability of Making Playoffs Over Regular Season")


animator = ani.FuncAnimation(fig, chart_builder, interval = 100, frames=(9 * gran), repeat=False)

#save mp4 file
from matplotlib.animation import FFMpegWriter
writer = FFMpegWriter(metadata=dict(artist='Office of the ACMGCFLPFLOP Commissioner'), bitrate=-1, fps=15,)
animator.save("SimulationAnimation.mp4", writer=writer)
plt.show()
