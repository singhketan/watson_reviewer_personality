import pandas as pd
import json
import requests

filename = 'input/input.json'
movie_um_filename = 'output/movie_um.xlsx'
personality_um_filename = 'output/personality.xlsx'
response_csv_filename = "temp/personality-insights.csv"
movie_um_fillna = True
data = []
username = "<YOUR USERNAME>"
password = "<YOUR PASSWORD>"
url = "<API URL>"
drop_list = ['sourceid']


request_data = {
    "contentItems": []
}

with open(filename) as f:
    lines = f.readlines()

for json_obj in lines:
    data.append(json.loads(json_obj))

df = pd.DataFrame(data)

# Combine fields and query the Watson API
df['text_content'] = df['reviewText'] + ". " + df['summary']
stacked_text = df.groupby(['reviewerID'])['text_content'].sum()
processed = pd.DataFrame(stacked_text)

for index, row in processed.iterrows():
	length = len(''.join(c if c.isalnum() else ' ' for c in row['text_content']).split())
	if  length > 99:
		request_data['contentItems'].append({
			'content' : row['text_content'],
			'userid' : index,
			'language' : "en"
		})
	else:
		print "Skipping user - " + index + ". Required no. of words is 100. But found only " + str(length)
print "--------------------------------------------"

request_data = json.dumps(request_data)


response = requests.post(url + "?headers=True",
    auth = (username, password),
    headers = {
        'Content-Type': 'application/json',
        'Accept': "text/csv"
    },
    data = request_data
)

print "Response received from WATSON API and saved in " + response_csv_filename
print "---------------------------"
with open(response_csv_filename, 'w') as f:
    print >> f, response.text

csv_df = pd.read_csv(response_csv_filename)


csv_df.drop(drop_list, axis = 1, inplace = True)
csv_df.set_index('userid')
writer = pd.ExcelWriter(personality_um_filename)
csv_df.to_excel(writer, 'Sheet1', index = False)
writer.save()
print "Personality Utility matrix saved in " + personality_um_filename
print "---------------------------"


#Generate and save the movie ratings utility matrix.
writer = pd.ExcelWriter(movie_um_filename)
stacked = df.groupby(['reviewerID', 'asin'])['overall'].sum()
um = stacked.unstack('asin')

if movie_um_fillna:
    um.fillna(value = 0)

um.to_excel(writer, sheet_name = 'Sheet1')
writer.save()
print "Movies Utility matrix saved in " + movie_um_filename
print "---------------------------"