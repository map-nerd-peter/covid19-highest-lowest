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

# Define the data's location based on Johns Hopkins COVID19 data schema
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

    def get_plot_data(self, maximum):

        #returns a named tuple with dates and confirmed daily_cases
        plot_data = collections.namedtuple('plot_data',['dates', 'daily_cases', 'label', 'alternate_label']) 

        max_value_col_location = -1

        #Reserved for alternate peak value
        alt_max_value_col_location = -1

        min_value_col_location = -1
        #For alternate min value
        alt_min_value_col_location = -1

        #Only used if there is an alternate max or alternate min value in the dataset

        if self.data_location == DataLocation.province_state:
            data = self.csv_row_data.iloc[0,4:]
        elif self.data_location == DataLocation.country_region:
            data = self.csv_row_data.iloc[0,2:]

        print('Daily case numbers being calculated: ')
        print(data.diff())


        print('Maximum:')
        print(data.diff().max())

        print('Getting the MEAN value of daily cases for Entire Series:')
        print(data.diff().mean())

        '''print('Rolling mean method of cells')
        for date_index, value in data.diff().rolling(5, center=True).mean().items():
            print('%s %.2f' %(date_index, value))'''

        rolling_data = data.diff().rolling(5, center=True).mean().round(3)

        #We need to determine maximum based on rolling averaged values so we know the max value in the infection wave
        max_rolling_value = rolling_data.max()
        print('Max rolling value %.2f' %max_rolling_value)

        #There may be alternate max value that is a result of quirks or daily revision of data reporting, not the max value we want.
        alt_max_value = data.diff().max()
        print('Alt max value')
        print(alt_max_value)

        #Get column location of maximum value first
        for date_index, value in rolling_data.items():

            if value == max_rolling_value:
                #print('Max date and roll value are %s %f' %(date_index, value))

                #Get the date for max case value for that date
                max_rolling_value_location = list(self.csv_row_data).index(date_index)
                max_date = date_index
                print('Rolling Maximum column loc and dates: %s %s' %(max_rolling_value_location, max_date))
                break

        #Take data subset for the max value and its epidemilogical wave
        print('Data subset containing max value:')        
        print(self.csv_row_data.iloc[0,max_rolling_value_location-7:max_rolling_value_location+7].diff())

        #This is likely the true max value of the epidemioliogical wave
        max_value = self.csv_row_data.iloc[0,max_rolling_value_location-7:max_rolling_value_location+7].diff().max()

        # Get values for max value location, maximum date, alternate max value location, and alternate max date.
        max_value_location, max_date, alt_max_value_location, alt_max_date  = self.get_values_and_dates(max_value, alt_max_value, DataParameter.maximum.name, data)

        print('Testing to see if we have 2 different maximum values %d %d' %(max_value, alt_max_value))

        #Comparing numpy.int64 max values,
        if max_value == alt_max_value:
            print('No alternate maximum detected!!')
            plot_data.alternate_label = None
        else:
            plot_data.alternate_label = '\nAlternate maximum value detected on %s: %d new cases' %(self.get_date_label(alt_max_date), alt_max_value)

        #if and else here

        if maximum:
            daily_cases= self.csv_row_data.iloc[0,max_value_location-4:max_value_location+4].diff()
            daily_cases = daily_cases.iloc[1:8]
            label = 'Maximum Value for Daily Cases on ' + self.get_date_label(max_date)

        # Get minimum or trough value after a peak value. 
        elif maximum == False:

            #Find the min value in the rolling data
            min_rolling_data = self.csv_row_data.iloc[0,max_value_location:].diff().rolling(5, center=True).mean().round(3)
            
            min_data = self.csv_row_data.iloc[0,max_value_location:].diff()

            min_rolling_value = min_rolling_data.min()
            print('Min rolling value %.2f' %min_rolling_value)

            #There may be alternate max value that is a result of quirks or daily revision of data reporting, not the max value we want.
            min_value = min_data.min()
            print('Minimum Value')
            print(min_value)

            alt_min_value = data.diff().max()
            print('Alt max value')
            print(alt_max_value)

            #Get column location of rolling value first
            for date_index, value in min_rolling_data.items():

                if value == min_rolling_value:
                    min_rolling_value_location = list(self.csv_row_data).index(date_index)
                    min_date = date_index
                    print('Rolling Maximum column loc and dates: %s %s' %(min_rolling_value_location, min_date))
                    break

            #Take data subset for the min value and its epidemilogical wave
            print('Data subset containing max value:')        
            print(self.csv_row_data.iloc[0,min_rolling_value_location-7:min_rolling_value_location+7].diff())

            #This is likely the true min within the epidemioliogical wave
            alt_min_value = self.csv_row_data.iloc[0,min_rolling_value_location-7:min_rolling_value_location+7].diff().min()

            #Possibly a different minimum value here
            min_value = min_data.min()

            #Identify Min Value and Possible Alternate Min value
            min_value_location, min_date, alt_min_value_location, alt_min_date  = self.get_values_and_dates(min_value, alt_min_value, DataParameter.minimum.name, data)

            if min_value == alt_min_value:
                print('No alternate minimum detected!!')
                plot_data.alternate_label = None
            else:
                plot_data.alternate_label = '\nAlternate minimum value detected on %s: %d new cases' %(self.get_date_label(alt_min_date), alt_min_value)

            daily_cases= self.csv_row_data.iloc[0,min_value_location-4:min_value_location+4].diff()
            daily_cases = daily_cases.iloc[1:8]
            label = 'Minimum Value for Daily Cases on ' + self.get_date_label(min_date)

        #Get corresponding day for each case va
        dates= [day for day, value in daily_cases.iteritems()]

        plot_data.dates = dates
        plot_data.daily_cases = daily_cases
        plot_data.label = label

        return plot_data

    def get_values_and_dates(self, value, alternate_value, DataParameter, data_series):

        #parameters: value and alternate_value, DataParameter maximum.name or minimum.name, Pandas data Series,
        #Depending on DataParameter maximum or minimum, 
        #it returns 4 variables: max_value_location, max_date, alt_max_value_location, alt_max_date or 
        #min_value_location, min_date, alt_min_value_location, alt_min_date

        #Identify Max Value and Possible Alternate max value
        for date_index, val in data_series.diff().items():

            if val == value:
                value_location = list(self.csv_row_data).index(date_index)
                date = date_index
                print('True %s column loc and date: %s %s' %(DataParameter, value_location, date))

            if val == alternate_value:
                alt_value_location = list(self.csv_row_data).index(date_index)
                alt_date = date_index
                print('Alternate %s column loc and date: %s %s' %(DataParameter, alt_value_location, alt_date))

        return value_location, date, alt_value_location, alt_date

    def plot_bar_chart(self, plot_data):

        #Check that dates (x-values) and daily case numbers are valid 
        if plot_data.dates is not None and plot_data.daily_cases is not None:
            plt.bar(plot_data.dates, height = plot_data.daily_cases) 
            plt.xticks(plot_data.dates, [self.get_date_label(d) for d in plot_data.dates])
            plt.xlabel('Date')
            plt.ylabel('Number of New Cases')
            for i, v in enumerate(plot_data.daily_cases):
                plt.text(i, v, str(v), color='blue', ha='center') 
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
            results = covid_data.get_plot_data(maximum = True)
        #Plot the minimum or low value of the data
        elif args.type == 'lowest':
            results = covid_data.get_plot_data(maximum = False)

        #url https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv
        covid_data.plot_bar_chart(results)

if __name__ == '__main__':
    main()
