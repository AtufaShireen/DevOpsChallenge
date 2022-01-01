from pickle import NONE
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import base64
from io import BytesIO
import squarify

class SegmentAnalysis():
    def __init__(self,df):
        self.df = df.copy()
        self.segment_label = 'ml_label'
        self.ltv='LTV'

    @staticmethod
    def __plot_config(**kwargs):
        # plt.figure(figsize=kwargs.get('figsize',(8,8)))
        # plt.figure(figsize=(18,8))
        plt.title(kwargs.get('title',''))
        tmpfile = BytesIO()
        plt.savefig(tmpfile, format='png')
        plt.close()
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')    
        return encoded

    def plot_cust_bar(self):
        # count the number of customers in each segment
        segments_counts = self.df[self.segment_label].value_counts().sort_values(ascending=True)

        fig, ax = plt.subplots()

        bars = ax.barh(range(len(segments_counts)),
                    segments_counts,
                    color='silver')
        ax.set_frame_on(False)
        ax.tick_params(left=False,
                    bottom=False,
                    labelbottom=False)
        ax.set_yticks(range(len(segments_counts)))
        ax.set_yticklabels(segments_counts.index)
        for i, bar in enumerate(bars):
            value = bar.get_width()
            if segments_counts.index[i].lower() in ['champion', 'loyal']:
                bar.set_color('firebrick')  
            ax.text(value,
                    bar.get_y() + bar.get_height()/2,
                    '{:,} ({:}%)'.format(int(value),
                                    int(value*100/segments_counts.sum())),
                    va='center',
                    ha='left'
                )
        img = self.__plot_config(title='Customer counts')
        return img


    def description(self,rfm_df=None,segment_label=None):
        if (rfm_df==None) | (segment_label==None):
            rfm_df = self.df
            segment_label = self.segment_label
        desc_df = rfm_df.groupby(segment_label,as_index=False).agg({
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': ['mean', 'count'],
            'LTV':'mean',
            'p_churn':'mean',
            'exp_purchases':'mean',
        }).round(1)
        
        # Print the aggregated dataset
        return desc_df
    def plot_cust_segment(self):
        desc_df = self.description()
        desc_df.columns = ['Label','Recencymean','Frequencymean', 'Monetarymean','Count','LTV','p_churn','exp_purchases']
        
        labels = desc_df['Label']
        ltvs = desc_df['LTV']
        zips_ = zip(labels,ltvs)
        label = [f"{l}\n LTV: {v}" for l,v in zips_]
        squarify.plot(sizes=desc_df['Count'], 
                    label=label, alpha=.9 ,pad = True)
        img = self.__plot_config(title='RFM Segments')
        return img

    def plot_clv(self):
        days = 30
        avg = f"avg: {round(self.df[self.ltv].mean(),2)}"
        print(avg)
        plt.plot(self.df[self.ltv],label='predicted')
        plt.gca().legend((avg,avg))
        img = self.__plot_config(title=f'CLV For next {days} days')
        return img

