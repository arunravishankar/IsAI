import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('df_sangeethapriya.csv', names = ["Concert ID","Track","Kriti","Ragam","Composer","Main Artist"])
columns = ['Kriti', 'Ragam', 'Composer', 'Main Artist']
data = df[columns]
data = data.dropna(axis='rows')
ragam_counts = data['Ragam'].value_counts()


def Cumulative(lists):
    cu_list = []
    length = len(lists)
    cu_list = [sum(lists[0:x:1]) for x in range(0, length+1)]
    return cu_list[1:]

x=[]
for item in ragam_counts.keys():
    x.append(len(data[data['Ragam']==item]))
cum_x = Cumulative(x)
cum_ratio_x = [item/cum_x[-1] for item in cum_x]


# create figure and axis objects with subplots()
fig,ax = plt.subplots()
# make a plot
ax.plot(x, color="red",alpha = 0.8)
# set x-axis label
ax.set_xlabel("Number of Ragams",fontsize=12)
# set y-axis label
ax.set_ylabel("Total clips",color="red",fontsize=10)
ax.set_title('Number of clips in major Ragams', fontsize = 16)
# twin object for two different y-axis on the sample plot
ax2=ax.twinx()
# make a plot with different y-axis using second axis object
ax2.plot(cum_ratio_x ,color="blue", alpha = 0.8)
ax2.set_ylabel("Cumulative proportion of clips",color="blue",fontsize=10)

plt.show()
# save the plot as a file
fig.savefig('clips_per_ragam.jpg',
            format='jpeg',
            dpi=100,
            bbox_inches='tight')