import matplotlib.pyplot as plt
import argparse
import pandas as pd
import collections
import platform
import datetime
"""
COVID-19 (Coronavirus) Plotting Tool to Identify Highest and Lowest Daily Case Values 
for Countries, Regions, Provinces/States.

Written by Peter C. (https://github.com/map-nerd-peter/covid19_highest_lowest)

"""
class Covid19Data:

    def __init__(self, location, url, province_state_selected):
        """Constructor"""

        self._location = location
        self._url = url
        self._csv_date_format = None

        #Load the row that contains for specific state or province and its COVID-19 data
        df = pd.read_csv(url, error_bad_lines=False)

        if province_state_selected:
            self._csv_row_data = df[df['Province/State'] == location]

        #Get country data
        elif not province_state_selected:
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
        plot_data = collections.namedtuple('plot_data',['dates', 'daily_cases', 'label']) 

        max_value_col_location = -1
        min_value_col_location = -1

        print('Daily case numbers being calculated: ')
        print(self.csv_row_data.iloc[0,4:].diff())

        print('Maximum:')
        print(self.csv_row_data.iloc[0,4:].diff().max())

        #We need to determin maximum case value first
        max_daily_case_value = self.csv_row_data.iloc[0,4:].diff().max()

        #Get column location of maximum value first
        for date_index, value in self.csv_row_data.iloc[0,4:].diff().items():
            if value == max_daily_case_value:
                print(date_index+'  '+str(value)+'  %d' %(list(self.csv_row_data).index(date_index)))

                #Get first max value encountered
                max_value_col_location = list(self.csv_row_data).index(date_index)
                max_date = date_index
                break

        if maximum:
            daily_cases= self.csv_row_data.iloc[0,max_value_col_location-4:max_value_col_location+4].diff()
            daily_cases = daily_cases.iloc[1:8]
            label = 'Maximum Value for Daily Cases on ' + self.get_date_label(max_date)

        # Get minimum or trough value after a peak value. 
        elif maximum == False:
            print('Testing min. subset and actual min value:')
            min_data = self.csv_row_data.iloc[0,max_value_col_location:].diff()
            print(min_data)

            min_daily_case_value = min_data.min()
            print(min_daily_case_value)
            print('Located a Minimum daily case value after the peak %d:' %min_daily_case_value)
            print('Creating data subset to plot the minimum value after the peak...')

            for date_index, value in min_data.items():
                print('%s %s' %(date_index, str(value)))
                if value == min_daily_case_value:
                    min_value_col_location = list(self.csv_row_data).index(date_index)
                    min_date = date_index
                    break

            daily_cases= self.csv_row_data.iloc[0,min_value_col_location-4:min_value_col_location+4].diff()
            daily_cases = daily_cases.iloc[1:8]
            label = 'Minimum Value for Daily Cases on ' + self.get_date_label(min_date)

        #Get corresponding day for each case va
        dates= [day for day, value in daily_cases.iteritems()]

        plot_data.dates = dates
        plot_data.daily_cases = daily_cases
        plot_data.label = label

        return plot_data

    def plot_bar_chart(self, plot_data):

        #Check that dates (x-values) and daily case numbers are valid 
        if plot_data.dates is not None and plot_data.daily_cases is not None:
            plt.bar(plot_data.dates, height = plot_data.daily_cases) 
            plt.xticks(plot_data.dates, [self.get_date_label(d) for d in plot_data.dates])
            plt.xlabel('Date')
            plt.ylabel('Number of New Cases')
            for i, v in enumerate(plot_data.daily_cases):
                plt.text(i, v, str(v), color='blue', ha='center') 
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

        print(vars(args))

        if not (args.province_state or args.country_region) and not (args.url and args.type):
            print('Please provide a location (country or province_state), url of the Johns Hopkins COVID-19 data file, and the top of plot that you want (highest or lowest)')
            print('Instructions are available by typing: python covid19_highest_lowest.py --help')      
            print('Example commands and more info available at https://github.com/map-nerd-peter/covid19_highest_lowest')
            return

        if args.province_state:
            location = args.province_state
            province_state_selected = True
        elif args.country_region:
            location = args.country_region
            province_state_selected = False

        url = args.url

        covid_data = Covid19Data(location, url, province_state_selected)
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
