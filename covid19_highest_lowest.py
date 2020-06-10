import matplotlib.pyplot as plt
import argparse
import pandas as pd
import collections
import platform
import datetime
from enum import Enum 
"""
COVID-19 (Coronavirus) Plotting Tool to Identify Highest and Lowest Daily Case Values 
for Countries, Regions, Provinces/States.

Written by Peter C. (https://github.com/map-nerd-peter/covid19-highest-lowest)

"""

# Define the data parameters that we need for our data filtering
class DataParameter(Enum):
    minimum = 1
    alt_minimum = 2
    maximum = 3
    alt_maximum = 4

# Define the type of location data based on Johns Hopkins COVID19 data schema
class DataLocation(Enum):
    province_state = 1
    country_region = 2

class Covid19Data:

    def __init__(self, location, url, data_location):
        """Constructor"""

        self._location = location
        self._url = url
        #Tells us if we're dealing with country or province/state data:
        self._data_location = data_location
        self._csv_date_format = None

        #Load the row that contains for specific state or province and its COVID-19 data
        df = pd.read_csv(url, error_bad_lines=False)

        if data_location == DataLocation.province_state:
            self._csv_row_data = df[df['Province/State'] == location]

        #Get country data
        elif data_location == DataLocation.country_region:
            self._csv_row_data = df[df['Country/Region'] == location].groupby('Country/Region').sum()

        #For Outputting readable dates on bar plots
        if platform.system() == 'Windows':
            self._csv_date_format = '%m/%d/%y'
            print('Using Python date format for Windows')
        elif platform.system() == 'Darwin' or platform.system() == 'Linux':
            self._csv_date_format = '%m/%d/%y'
            print('Using Python date format for MacOS or Linux')

    @property
    def location(self):
        return self._location

    @property
    def url(self):
        return self._url

    @property
    def data_location(self):
        return self._data_location

    @property 
    def csv_row_data(self):
       return self._csv_row_data

    @property
    def csv_date_format(self):
        return self._csv_date_format

    #Take the date format from Johns Hopkins csv column (e.g. 04/15/20) and return as a readable date to label the bar plot
    def get_date_label(self, csv_date):
        try:
            date_label = datetime.datetime.strptime(csv_date, self.csv_date_format)
            return datetime.datetime.strftime(date_label, '%b/%d/%Y') 
        except:
            return 'Invalid Date'

    def get_plot_data(self, DataParameter):

        plot_type = DataParameter

        #returns a named tuple with dates and confirmed daily_cases
        plot_data = collections.namedtuple('plot_data',['dates', 'daily_cases', 'label', 'alternate_label']) 
        plot_data.alternate_label = ""

        max_value_location = -1
        #Reserved for alternate peak value
        alt_max_value_location = -1

        min_value_location = -1
        #For alternate min value
        alt_min_value_location = -1

        #Only used if there is an alternate max or alternate min value in the dataset

        if self.data_location == DataLocation.province_state:
            data = self.csv_row_data.iloc[0,4:]
        elif self.data_location == DataLocation.country_region:
            data = self.csv_row_data.iloc[0,2:]

        print('Daily case numbers in the dataset: ')
        print(data.diff())

        rolling_data = data.diff().rolling(5, center=True).mean().round(3)

        #Determine maximum based on rolling averaged values so we know the max value in infection wave. Only take positive and 0 values for max and alternate max values.
        max_rolling_value = rolling_data.loc[lambda x : x>= 0].max()
        print('Max rolling value %.2f' %max_rolling_value)

        #There may be alternate max value that is a result of quirks or daily revision of data reporting, not the max value we want.
        alt_max_value = data.diff().loc[lambda x : x>= 0].max()
        print('Alt max value')
        print(alt_max_value)

        #Get column location of maximum value first
        for date_index, value in rolling_data.items():

            if value == max_rolling_value:
                #Get the date for max case value for that date
                max_rolling_value_location = list(self.csv_row_data).index(date_index)
                max_date = date_index
                print('Rolling Maximum column loc and dates: %s %s' %(max_rolling_value_location, max_date))
                break

        #Take data subset for the max value and its epidemiological wave
        print('Data subset containing max value:')        
        max_series_data = self.csv_row_data.iloc[0,max_rolling_value_location-7:max_rolling_value_location+7].diff()

        #This is likely the true max value of the epidemioliogical wave
        max_value = max_series_data.loc[lambda x : x>= 0].max()

        # Get values for max value location, maximum date, alternate max value location, and alternate max date.
        max_value_location, max_date = self.get_location_and_date(max_value, DataParameter.maximum.name, data)

        alt_max_value_location, alt_max_date  = self.get_location_and_date(alt_max_value, DataParameter.alt_maximum.name, data)

        print('Testing to see if we have 2 different maximum values %d %d' %(max_value, alt_max_value))

        duplicate_lines = 0
        if max_series_data.duplicated().any():
            for date, val in max_series_data.items():
                if date != max_date and val == max_value:
                    #Only have space to report 2 lines of duplicate max values.
                    if duplicate_lines == 2:
                        plot_data.alternate_label = plot_data.alternate_label + '\nAdditional Maximum Values were Detected!!'
                        break
                        
                    print('Duplicate Value Detected! This is also an Alternate max value: %s %d' %(date, val))
                    plot_data.alternate_label = plot_data.alternate_label + '\nAlternate Maximum value detected on %s: %d cases' %(self.get_date_label(date), val)
                    duplicate_lines +=1

        #if max_value == alt_max_value and max_date == alt_max_date:
        if max_value != alt_max_value and max_date != alt_max_date:
            plot_data.alternate_label = plot_data.alternate_label + '\nAlternate Maximum value detected on %s: %d cases' %(self.get_date_label(alt_max_date), alt_max_value)

        if plot_type == DataParameter.maximum:
            daily_cases = self.csv_row_data.iloc[0,max_value_location-8:max_value_location+8].diff()
            daily_cases = daily_cases.iloc[1:16]
            label = 'Maximum Value for Daily Cases on on %s: %d cases' %(self.get_date_label(max_date), max_value)

        # Get minimum or trough value after a peak value. 
        elif plot_type == DataParameter.minimum:
            
            #Reset alternate label so that we only report minimum values.
            plot_data.alternate_label = ""

            #Find the min value in the rolling data
            min_rolling_data = self.csv_row_data.iloc[0,max_value_location:].diff().rolling(5, center=True).mean().round(3)
            print(min_rolling_data)
            #min_rolling_data = min_rolling_data.where(lambda x : x>=0)
            #print(type(min_rolling_data))
            
 
            min_rolling_value = min_rolling_data.loc[lambda x : x>= 0].min() #Is this data frame filter by >=0 eg min_rolling_data >=0
            print(min_rolling_value)
            #exit()
            #df.loc[df['Budget'] > 0, 'Budget'].min()
            #e.g. https://stackoverflow.com/questions/53719450/how-to-find-the-pandas-record-with-positive-value-closest-to-zero
            print('Min rolling value %.2f' %min_rolling_value)

            #Get column location of minimum value
            for date_index, value in min_rolling_data.items():
                if value == min_rolling_value: 
                    min_rolling_value_location = list(self.csv_row_data).index(date_index)
                    min_date = date_index
                    print('Rolling Minimum column loc and dates: %s %s' %(min_rolling_value_location, min_date))
                    break

            min_series_data = self.csv_row_data.iloc[0,min_rolling_value_location-7:min_rolling_value_location+7].diff()

            min_data = self.csv_row_data.iloc[0,min_rolling_value_location-7:]

            #The likely Minimum value of the epidemiological wave. Only taking positive values and 0 values for minimums.
            min_value = min_series_data.loc[lambda x : x>= 0].min()

            #There may be alternate minimum value that is a result of quirks/daily revision of data reporting, we should still report this one.
            alt_min_value = min_data.diff().loc[lambda x : x>= 0].min()
            print(alt_min_value)

            min_value_location, min_date = self.get_location_and_date(min_value, DataParameter.minimum.name, min_data)

            alt_min_value_location, alt_min_date  = self.get_location_and_date(alt_min_value, DataParameter.alt_minimum.name, min_data)

            duplicate_lines = 0
            if min_series_data.duplicated().any():
                for date, val in min_series_data.items():
                    if date != min_date and val == min_value:
                        #Only have space to report 2 duplicate values
                        if duplicate_lines == 2:
                            plot_data.alternate_label = plot_data.alternate_label + '\nAdditional Minimum Values were detected!!'
                            break

                        print('Duplicate Value Detected! This is also an Alternate Minimum value: %s %d' %(date, val))
                        plot_data.alternate_label = plot_data.alternate_label + '\nAlternate Minimum value detected on %s: %d cases' %(self.get_date_label(date), val)
                        duplicate_lines +=1
            
            if min_value != alt_min_value and min_date != alt_min_date:
                plot_data.alternate_label = plot_data.alternate_label + '\nAlternate Minimum value detected on %s: %d cases' %(self.get_date_label(alt_min_date), alt_min_value)
            
            daily_cases = self.csv_row_data.iloc[0,min_value_location-8:min_value_location+8].diff()
            daily_cases = daily_cases.iloc[1:16]
            label = 'Minimum Value for Daily Cases on on %s: %d cases' %(self.get_date_label(min_date), min_value)

        #Get corresponding day for each case value
        dates = [day for day, value in daily_cases.iteritems()]

        plot_data.dates = dates
        plot_data.daily_cases = daily_cases
        plot_data.label = label

        return plot_data

    def get_location_and_date(self, value, DataParameter, data_series):
        """
        Get column location and date of infection case value.
        Parameters
        ----------
        value : float
            Case value
        Returns
        -------
        value_location : int
            Column location of the case value
        date : string
            Date of the case value
        """

        #parameters: value, date, Pandas data Series,
        #Depending on DataParameter maximum or minimum, 
    
        for date_index, val in data_series.diff().items():

        
            if val == value:
                value_location = list(self.csv_row_data).index(date_index)
                date = date_index
                print('%s column loc and date: %s %s' %(DataParameter, value_location, date))
                break


        return value_location, date

    def plot_bar_chart(self, plot_data):
        """
        Takes data to plot a bar chart 
        Parameters
        ----------
        plot_data : named_tuple
            plot_data contains Different components inside the named tuple
        plot_data.dates : list
            List of dates
        plot_data.daily_cases : list
            List of daily cases
        plot_data.label : string
            Label describing location and minimum or maximum value
        plot_data.alternate_label : string
            Label to report alternate maximum or minimum values
        """
        if plot_data.dates is not None and plot_data.daily_cases is not None:
            plt.bar(plot_data.dates, height = plot_data.daily_cases) 
            plt.xticks(plot_data.dates, [self.get_date_label(d) for d in plot_data.dates])
            plt.xlabel('Date')
            plt.ylabel('Number of New Cases')
            for i, v in enumerate(plot_data.daily_cases):
                plt.text(i, v, int(v), color='blue', ha='center') 
            if plot_data.alternate_label is not None:
                plt.title('COVID-19 Epidemic in %s\n%s' %(self.location, plot_data.label+plot_data.alternate_label))
            else:
                plt.title('COVID-19 Epidemic in %s\n%s' %(self.location, plot_data.label))
            plt.show()

def main():

        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('-p',
                            '--province_state',
                            type=str,
                            help='Name of province or state to obtain the COVID-19 data')
        parser.add_argument('-c',
                            '--country_region',
                            type=str,
                            help='Name of country or region to obtain the COVID-19 data')
        parser.add_argument('-u',
                            '--url',
                            type=str,
                            help='URL of COVID-19 data file, e.g. https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
        
        # Must provide either highest or lowest as type of graph
        parser.add_argument('-t',
                            '--type',
                            choices=['highest', 'lowest'],
                            help='Set the type of graph required: either highest or lowest')

        args = parser.parse_args()

        if not (args.province_state or args.country_region) and not (args.url and args.type):
            print('Please provide a location (country or province_state), url of the Johns Hopkins COVID-19 data file, and the top of plot that you want (highest or lowest)')
            print('Instructions are available by typing: python covid19_highest_lowest.py --help')      
            print('Example commands and more info available at https://github.com/map-nerd-peter/covid19_highest_lowest')
            return

        if args.province_state:
            location = args.province_state
            data_location = DataLocation.province_state
        elif args.country_region:
            location = args.country_region
            data_location = DataLocation.country_region

        url = args.url

        covid_data = Covid19Data(location, url, data_location)
        print(covid_data)

        #Plot the maximum or high value of the data
        if args.type == 'highest':
            results = covid_data.get_plot_data(DataParameter.maximum)
        #Plot the minimum or low value of the data
        elif args.type == 'lowest':
            results = covid_data.get_plot_data(DataParameter.minimum)

        #url https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv
        covid_data.plot_bar_chart(results)

if __name__ == '__main__':
    main()
