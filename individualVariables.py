import requests
import json
import datetime
import pytz
import pyowm
import tkinter as tk
from tkinter import dialog
from tkinter import simpledialog
from tkinter import messagebox
import csv
import os.path
from os import path
from collections import OrderedDict

#this class will fetch and record weather forecast data for the given latitude and longetude
class weatherData():
    
    #class initialization method, takes in latitude, longetude, start hour, and length of event in hours as parameters
    def __init__(self, lat, lon, startHour, length):
        
        #set parameters as instance variables
        self.lat = lat
        self.lon = lon
        self.startHour = startHour
        self.length = length
        
        #set up pyowm api manager
        api_key = "67d5869737aeffc6b6eec4445bda7380"
        self.owm = pyowm.OWM(api_key)
        mgr = self.owm.weather_manager()
        
        #use api manager's one_call method to fetch all relevant weather data for next 48 hours
        self.oneCall = mgr.one_call(lat = self.lat, lon = self.lon, units = 'imperial')
        
        #pull hourly forecasts from self.oneCall variable
        hourly = self.oneCall.forecast_hourly
        fullForecast = dict(zip([hour.reference_time() for hour in hourly], [hour.temperature() for hour in hourly]))
        
        #create hourList list of all relevant hours based on start time and event length
        hourList = [int((self.startHour + datetime.timedelta(hours = i)).timestamp()) for i in range(self.length)]
        
        #create forecast dictionary that stores hourly forecasts only for relevant hours
        self.forecast = dict(zip(hourList, [fullForecast[hour] for hour in hourList]))
        
        #create separate lists for actual temp at each hour and "feels like" temp at each hour of event
        self.temp = [self.forecast[hour]['temp'] for hour in hourList]
        self.feels = [self.forecast[hour]['feels_like'] for hour in hourList]
        
        return
    
    #this method returns a list of strings of the datetime information for each hour in the self.forecast dictionary
    def getDtStrList(self):
        return [datetime.datetime.fromtimestamp(hour).strftime('%Y-%m-%d %H:%M:%S') for hour in self.forecast.keys()]
    
    #this method returns a list of datetime information in datetime format for each hour in the self.forecast dictionary
    def getDtList(self):
        return self.forecast.keys()
    
    #this method returns the self.temp list
    def getTempList(self):
        return self.temp
    
    #this method returns the self.feels list
    def getFeelsList(self):
        return self.feels
    
    #this method returns the full self.forecast dictionary
    def getForecast(self):
        return self.forecast
    
#this class will generate the reccommendation to be given to the user that specifies how they should dress for the given weather conditions
class dressRec():
    
    #class initialization method, takes in weather (a weatherData class instance) and user (a userData class instance) as parameters
    def __init__(self, weather, user):
        
        #sets user as self.user instance variable
        self.user = user
        
        #sets self.outfitRange instance variable equal to a list of strings describing each of the outfit indexes
        self.outfitRange = ["a short-sleeved top and short bottoms.", "a short-sleeved top and long bottoms.", "a long-sleeved top and long bottoms.", "long bottoms and a jacket on top.", "long bottoms and a winter coat on top."]
        
        #uses the weather.getFeelsList() method to find min, max, and mean feels temp for event
        self.minTemp = min(weather.getFeelsList())
        self.maxTemp = max(weather.getFeelsList())
        self.meanTemp = round((sum([temp for temp in weather.feels])/len(weather.feels)), 2)
        
        #sets self.layers to False (to be changed upon implementation of layering functionality
        self.layers = False
        
        #sets self.rec equal to an empty string to begin
        self.rec = ""
        
        #runs self.generateRec() method to generate reccommendation information
        self.generateRec()
        
        #runs self.recMessage() method to generate reccommendation message
        self.recMessage()
        
        return
    
    #this method generates all necessary information to provide an accurate reccommendation to the user for their event
    def generateRec(self):
        
        #tempData holds a list of comfortIndex lists of outfitIndex lists which contain each temperature in the given outfitIndex in the user's dataHistory variable
        tempData = [[[dPoint.temp for dPoint in oIndex] for oIndex in cIndex] for cIndex in self.user.dataHistory]
        
        #sets upBoundDP to maximum and lowBoundDP to minimum, as well as upBoundOIndex and lowBoundOIndex to appropriate outfit indexes
        upBoundDP = self.user.dataHistory[2][0][(len(self.user.dataHistory[2][0])-1)]
        lowBoundDP = self.user.dataHistory[2][4][0]
        upBoundOIndex = 0
        lowBoundOIndex = 4
        
        #finds closest lower bound datapoint and records as lowBoundDP, as well as recording its outfit index as lowBoundOIndex
        for i in reversed(range(len(tempData[2]))):
            for j in reversed(range(len(tempData[2][i]))):
                if (tempData[2][i][j] < self.meanTemp):
                    lowBoundDP = self.user.dataHistory[2][i][j]
                    lowBoundOIndex = i
        
        #finds closest upper bound datapoint and records as upBoundDP, as well as recording its outfit index as upBoundOIndex         
        for i in range(len(tempData[2])):
            for j in range(len(tempData[2][i])):
                if (tempData[2][i][j] > self.meanTemp):
                    upBoundDP = self.user.dataHistory[2][i][j]
                    upBoundOIndex = i
        
        #if lowBoundOIndex and upBoundOIndex are the same, we will reccommend the user dress in that outfit index for their event
        if (lowBoundOIndex == upBoundOIndex):
            self.outfitIndex = lowBoundOIndex
        
        #if the upper bound datapoint is farther from the mean temp than the lower bound data point, we will reccommend the user dress in the lower bound outfit index for their event
        elif((abs(upBoundDP.temp - self.meanTemp)) > abs((self.meanTemp - lowBoundDP.temp))):
            self.outfitIndex = lowBoundOIndex
        
        #else, we will reccommend the user dress in the upper bound outfit index for their event
        else:
            self.outfitIndex = upBoundOIndex
        
        return
    
    #this method generates the reccommendation message that will print to the user, giving them all the information they need to dress appropriately for their event    
    def recMessage(self):
        
        #generate the reccommendation message, telling the user the max temp, min temp, mean temp, and reccommended outfit index
        self.recMes = ("The high temp during your event will feel like " + str(self.maxTemp) + " degrees Fahrenheit.\nThe low temp during your event will feel like " + str(self.minTemp) + " degrees Fahrenheit.\nI reccommend dressing for the mean temp, which will feel like " + str(self.meanTemp) + " degrees Fahrenheit.\nYou should be comfortable in an outfit that consists of " + self.outfitRange[self.outfitIndex])
        
        #the following is unfinished documentation for layering functionality integration
        '''
        if(self.maxTemp - self.minTemp > 10.0):
            #self.layers = True
        
        if(self.layers):
            #self.recMes = ("Dress for " + str(self.maxTemp) + " degree weather. Make sure to bring a layer that will keep you warm in weather as cold as " + minTemp + " degrees.")
        
        else:
            #self.recMes = ("Dress for " + str(self.meanTemp) + " degree weather. No need for extra layers.")
        '''
        
        return
    
    #this method returns the previously generated rec message        
    def getRecMes(self):
        
        return self.recMes
    
#this class utilizes the weatherData and dressRec classes to fetch and generate a reccommendation for an event for a specified user and prints relevant information to the user
class recEvent():
    
    #class initialization method, takes in city, state, day, start hour, length of event in hours, and user (userData class instance) as parameters
    def __init__(self, city, state, day, startHour, length, user):
        
        #sets up pyowm city registry object
        api_key = "67d5869737aeffc6b6eec4445bda7380"
        self.owm = pyowm.OWM(api_key)        
        reg = self.owm.city_id_registry()
        
        #finds and records city's latitude and longitude to be used to fetch weather data by weatherData class
        self.city = reg.locations_for(city, country=state)[0]
        lat = self.city.lat
        lon = self.city.lon
        
        #sets self.user instance variable equal to user parameter
        self.user = user
        
        #sets self.day instance variable equal to current datetime + day offset
        self.day = (datetime.datetime.now() + datetime.timedelta(days = day))
        #sets self.startTime instance variable equal to self.day datetime rounded to last whole hour
        self.startTime = datetime.datetime(self.day.year, self.day.month, self.day.day, startHour)
        
        #sets self.weather instance variable equal to appropriate weatherData object for given latitude, longetude, start time, and event length
        self.weather = weatherData(lat, lon, self.startTime, length)
        
        #sets self.rec instance variable equal to appropriate dressRec object for given weatherData and userData
        self.rec = dressRec(weather=self.weather, user=self.user)
        
        return
    
    #this method prints all generated reccommendation information to user's screen
    def printInfo(self):
        
        #print relevant info to user, with staggered line spacing
        print("The hours included in your event are:")
        print(self.weather.getDtStrList())
        print()
        print("The temp at each hour of your event will be:")
        print(self.weather.getTempList())
        print()
        print("The temp it will feel like at each hour of your event will be:")
        print(self.weather.getFeelsList())
        print()
        #print genrated rec message to user
        print(self.rec.getRecMes())
        print()
        
        return
    
#this class interacts with a specified user to recieve all necessary event information, then utilizes the recEvent class to generate reccommendation information, and uses the dataPoint class to record data to the user's userData instance
class userEvent():
    
    #class initialization method, takes in user (userData class instance) as a parameter
    def __init__(self, user):
        
        #sets self.today instance variable equal to current datetime
        self.today = datetime.datetime.today()
        #sets self.dayOptions instance variable equal to list including current datetime, current datetime + 24 hr offset, and current datetime + 48 hour offset
        self.dayOptions = [self.today, self.today + datetime.timedelta(days = 1), self.today + datetime.timedelta(days = 2)]
        
        #sets self.parent equal to an instance of tk.Tk() to serve user dialog
        self.parent = tk.Tk()
        
        #sets self.user instance variable equal to self.user
        self.user = user
        
        #runs self.getCity(), self.getState(), self.getDay(), self.getStartTime(), and self.getEventLength() to collect all relevant information from user using tkinter dialogs
        self.getCity()
        self.getState()
        self.getDay()
        self.getStartTime()
        self.getEventLength()
        
        #set self.event instance variable equal to instance of recEvent class with all relevant information
        self.event = recEvent(city=self.city, state=self.state, day=self.day, startHour=self.startTime, length=self.length, user=self.user)
        #run self.event.printInfo() method to print all reccommendation information to the user's screen
        self.event.printInfo()
        
        #add a dataPoint object to self.user (userData instance) using addDataPoint() method to record relevant event information to user's data history
        self.user.addDataPoint(dataPoint(self.event.rec.outfitIndex, 5, self.event.rec.meanTemp, dressR=self.event.rec, city = self.city, date =self.dayOptions[self.day].strftime("%B %d, %Y"), startTime=self.startTime))
        
        return
    
    #this method uses a tkinter dialog to fetch city information from the user
    def getCity(self):
        
        self.city = simpledialog.askstring("In what city is your event taking place?", "Please enter city name:", parent = self.parent)

        return
    
    #this method uses a tkinter dialog to fetch state abbreviation information from user
    def getState(self):
        
        self.state = simpledialog.askstring("In what state is the city located?", "Please enter two-letter state abbreviation:", parent = self.parent)
        
        return
    
    #this method uses a tkinter dialog to warn the user that their event must conclude within 48 hours, and then fetches day information from user, then calculates whether the day is option 0, 1, or 2
    def getDay(self):
        
        #warns user their event must conclude within 48 hours
        messagebox.showinfo("Please Note", "Your event must conclude by " + self.dayOptions[2].strftime("%H:00 on %B %d, %Y"), parent = self.parent)
        
        #fetches event start date from user using tkinter dialog
        days = [day.strftime("%B %d") for day in self.dayOptions]
        dateD = dialog.Dialog(title="What day is your event taking place?", text=("Today, " + self.dayOptions[0].strftime("%B %d, %Y") + ", Tomorrow, " + self.dayOptions[1].strftime("%B %d, %Y") + ", or the following day, " + self.dayOptions[2].strftime("%B %d, %Y") + "?"), strings=days, bitmap = 'questhead', default = 0, parent = self.parent)
        date = days[dateD.num]
         
        #if, elif, and else statements calculate whether date given by user is day index 0, 1, or 2
        if (date == self.dayOptions[0].strftime("%B %d")):
            self.day = 0  
        elif (date == self.dayOptions[1].strftime("%B %d")):
            self.day = 1
        else:
            self.day = 2
            
        return
    
    #this method uses a tkinter dialog to fetch the event start time (in 24 hr format, to nearest hour) from user
    def getStartTime(self):
        
        #if/else statements ensure user is not able to enter a start time which has already passed
        if (self.day == 0):
            minHour = self.today.hour 
        else:
            minHour = 0
        
        #tkinter dialog fetches event start time from user
        self.startTime = simpledialog.askinteger("What time does your event start?", "Choose start time in 24hr format:", initialvalue=self.today.hour, minvalue=minHour, maxvalue=23, parent=self.parent)
        
        return
    
    #this method fetches event end date and end time from user, then uses them to calculate event length in hours 
    def getEventLength(self):
        
        #sets days equal to list of possible day options (days 0-2)
        days = [day.strftime("%B %d") for day in self.dayOptions]
        
        #if start date is day 0, event can conclude on day 0, 1, or 2
        if (self.day == 0):
            #tkinter dialog fetches end day from user
            endDateD = dialog.Dialog(title="What day does your event conclude?", text=("Today, " + self.dayOptions[0].strftime("%B %d, %Y") + ", Tomorrow, " + self.dayOptions[1].strftime("%B %d, %Y") + ", or the following day, " + self.dayOptions[2].strftime("%B %d, %Y") + "?"), strings=days, bitmap = 'questhead', default = 0, parent = self.parent)
            endDate = days[endDateD.num]
            
        #if start date is day 1, event can conclude on day 1 or 2
        elif (self.day == 1):
            ##tkinter dialog fetches end day from user
            endDateD = dialog.Dialog(title="What day does your event conclude?", text=("Tomorrow, " + self.dayOptions[1].strftime("%B %d, %Y") + ", or the following day, " + self.dayOptions[2].strftime("%B %d, %Y") + "?"), strings=days[1:], bitmap = 'questhead', default = 0, parent = self.parent)
            endDate = days[endDateD.num+1]
        
        #if start date is day 2, event must conclude on day 2
        else:
            endDate = 2
        
        #if/elif/else statement translates user reponse to day index to record endDay
        if (endDate == self.dayOptions[0].strftime("%B %d")):
            endDay = 0       
        elif (endDate == self.dayOptions[1].strftime("%B %d")):
            endDay = 1        
        else:
            endDay = 2        
        
        #if event concludes on day 2, it must conclude by current hour to be within 48 hour timeframe
        if (endDay == 2):
            maxHour = self.today.hour
        #else, no restriction on conclusion hour
        else:
            maxHour = 23
            
        #tkinter dialog fetches end hour from user
        endHour = simpledialog.askinteger("What time does your event end?", "Choose end time in 24hr format:", initialvalue=self.today.hour, minvalue=1, maxvalue=maxHour, parent=self.parent)
        
        #calculates event length in hours and records as self.length
        self.length = (((endDay-self.day)*24) + (endHour-self.startTime))
        
        return
        
#this class provides a framework for an individual data point which stores all relevant information for an individual userEvent and is utilized by the userData and userReview classes
class dataPoint():
    
    #class initialization method, takes outfit index, comfort index, and temp as required parameters, with dressR, city, date, and start time as optional parameters with given default values
    def __init__(self, outfitIndex, comfortIndex, temp, dressR=True, city='N/A', date='N/A', startTime = 'N/A'):
        
        #sets instance variables equal to given parameters
        self.outfitIndex = outfitIndex
        self.comfortIndex = comfortIndex
        self.temp = temp
        self.city = city
        self.date = date
        self.startTime = startTime
        
        #if dressR parameter is True, dataPoint is an initial point (recorded from user initialization survey as opposed to post-event survey)
        if(dressR==True):
            self.initialPoint = True
        #else, dataPoint is not an initial point (recorded from post-event user survey)
        else:
            self.initialPoint = False
        
        return
        
#this class stores and manages all relevant data collected for an individual user
class userData():
    
    #class initialization method, takes in user's name (string) as a parameter
    def __init__(self, name):
        
        #sets self.name instance variable equal to given name parameter
        self.name = name
        #sets self.fileName instance variable equal to correct userData file name for given name
        self.fileName = 'userData' + self.name + '.csv'
        
        #if user's file name already exists, use self.historyFromFile() method to fetch and record previous user data from file
        if(path.exists(self.fileName)):
            self.historyFromFile(name)
        
        #else, create a new user and prompt the user with initial data survey, then record to new userData file
        else:
            #set self.outfitRange to list of outfit strings at each corresponding outfit index
            self.outfitRange = ["a short-sleeved top and short bottoms", "a short-sleeved top and long bottoms", "a long-sleeved top and long bottoms", "long bottoms and a jacket on top", "long bottoms and a winter coat on top"]
            #set self.tkParent to tk.Tk() object to be used in user dialogs
            self.tkParent = tk.Tk()
            #runs self.newUser() method to initialize new user data by prompting user with initial data survey and recording to dataHistory
            self.newUser()
            #runs self.updateFile() method to update new user's data file with data collected from initial data survey
            self.updateFile(name)
        
        return
    
    #this method uses tkinter dialog to prompt user with initial data survey and record responses to self.dataHistory
    def newUser(self):
        
        #tkinter dialog prompts user with initial data survey and records responses to baseTempPrefs
        baseTempPrefs = [simpledialog.askfloat("Let's get an idea of your temperature preferences", ("At what temperature (in degrees Fahrenheit) would you be most comfortable wearing " + outfit + "?"), initialvalue=65.0, minvalue=0.0, maxvalue=100.0, parent=self.tkParent) for outfit in self.outfitRange]
        
        #initializes self.dataHistory instance variable and fills it appropriately with list of comfort index lists, containing lists of outfit index lists, containing individual datapoints. Also records datapoints collected from initial user survey
        self.dataHistory = [[[],[],[],[],[]], [[],[],[],[],[]], [[dataPoint(outfitIndex=i, comfortIndex=2, temp=baseTempPrefs[i])] for i in range(len(baseTempPrefs))], [[],[],[],[],[]], [[],[],[],[],[]], [[],[],[],[],[]]]
        
        return
    
    #this method ensures data in self.dataHistory is sorted in ascending temperature order
    def sortData(self):
        
        #helper function sortKey names temp variable as appropriate sort key for a given dataPoint
        def sortKey(dataP):
            return dataP.temp
        
        #for every outfit index list within every comfort index list in self.dataHistory, ensure datapoints are being sorted in ascending temperature order
        for i in self.dataHistory:
            for j in i:
                j.sort(key=sortKey)
                
        return
    
    #this method records a new dataPoint to user's data history
    def addDataPoint(self, dPoint):
        
        #append datapoint in appropriate outfit index list within appropriate comfort index list in self.dataHistory
        self.dataHistory[dPoint.comfortIndex][dPoint.outfitIndex].append(dPoint)
        
        #run self.sortData() to ensure data is sorted appropriately within self.dataHistory
        self.sortData()
        
        #run self.updateFile() to update user's data file to add new dataPoint
        self.updateFile(self.name)
        
        return
    
    #this method updates user's data file with current data stored within self.dataHistory
    def updateFile(self, name):
        
        #sets dataDicts equal to an empty list
        dataDicts = []
        
        #goes through every individual dataPoint in self.dataHistory and records relevant information to dataDicts list
        for comfortIndex in range(6):
            for outfitIndex in range(len(self.dataHistory[comfortIndex])):
                for dataP in self.dataHistory[comfortIndex][outfitIndex]:
                    dataDicts.append({'Initial Point':str(dataP.initialPoint), 'Comfort Index':str(dataP.comfortIndex), 'Outfit Index':str(dataP.outfitIndex), 'Temp':str(dataP.temp), 'City':dataP.city, 'Date':dataP.date, 'Start Time':dataP.startTime})
                
        #opens user's csv data file
        csvfile = open(self.fileName, 'w', newline='')
        
        #sets fields equal to the keys in a given data dictionary within dataDicts
        fields=list(dataDicts[0].keys())
        
        #records information in dataDicts to user's csv file
        obj=csv.DictWriter(csvfile, fieldnames=fields)
        obj.writeheader()
        obj.writerows(dataDicts)      
        
        #closes user's csv data file
        csvfile.close()
        
        return
    
    #this method initializes user's self.dataHistory variable from existing user data file
    def historyFromFile(self, name):
        
        #initializes self.dataHistory variable and fills it with the appropriate number of empty nested lists
        self.dataHistory = [[[] for i in range(5)] for j in range(6)]
        
        #opens users csv data file and sets obj equal to a file reader
        csvfile = open(self.fileName,'r', newline='')
        obj = csv.DictReader(csvfile)
        
        #records every row in user's csv data file as dataPoint in appropriate index in self.dataHistory initialized with all corresponding information
        for row in obj:
            
            dataDict = dict(row)
            
            if (dataDict['Initial Point'] == 'True'):
                self.dataHistory[int(dataDict['Comfort Index'])][int(dataDict['Outfit Index'])].append(dataPoint(outfitIndex=int(dataDict['Outfit Index']), comfortIndex=int(dataDict['Comfort Index']), temp=float(dataDict['Temp'])))
            
            else:
                self.dataHistory[int(dataDict['Comfort Index'])][int(dataDict['Outfit Index'])].append(dataPoint(outfitIndex=int(dataDict['Outfit Index']), comfortIndex=int(dataDict['Comfort Index']), temp=float(dataDict['Temp']), dressR=False, city=str(dataDict['City']), date=str(dataDict['Date']), startTime=int(dataDict['Start Time'])))
        
        #closes user's csv data file
        csvfile.close()
        
        #runs self.sortData() to ensure all data in self.dataHistory is sorted appropriately
        self.sortData()
        
        return
    
#this class interacts with a specified user, enabling the user to review the reccommendation given for a past event so that the user's userData instance can be updated to increase future accuracy
class userReview():
    
    #class initialization method takes in user (a userData class instance) as parameter
    def __init__(self, user):
        
        #sets self.user instance variable equal to user parameter
        self.user = user
        #sets self.parent instance variable equal to tk.Tk() object for use in user dialog
        self.parent = tk.Tk()
        #sets self.outfitRange instance variable equal to list of outfit strings at appropriate outfit indexes
        self.outfitRange = ["a short-sleeved top and short bottoms", "a short-sleeved top and long bottoms", "a long-sleeved top and long bottoms", "long bottoms and a jacket on top", "long bottoms and a winter coat on top"]
        
        #sets self.needsReview instance variable equal to an empty dictionary
        self.needsReview = dict()
        
        #goes through every dataPoint in self.dataHistory in comfort index 5 (unreviewed) and records dataPoints needing to be reviewed in corresponding nested dictionaries in self.needsReview
        for i in range(len(self.user.dataHistory[5])):
            if (len(self.user.dataHistory[5][i]) > 0):
                self.needsReview[i] = dict()
                for j in range(len(self.user.dataHistory[5][i])):
                    self.needsReview[i][j] = self.user.dataHistory[5][i][j]
        
        #if there are no past events needing to be reviewed by the user, communicate this to the user via a tkinter dialog
        if(len(self.needsReview.keys()) == 0):
            messagebox.showinfo("You have no past events that need review", parent = self.parent)
        
        #else run self.getReview() and self.updateUserData() to record user's review for a past event and update the user's userData instance to reflect the review    
        else:
            self.getReview()
            self.updateUserData()
            
        return
    
    #this method prompts the user with a series of questions enabling them to review a past event's outfit reccommendation 
    def getReview(self):
        
        #eventLists is a list of nested dictionaries storing events needing review
        eventLists = [self.needsReview[key] for key in self.needsReview.keys()]
        #initialize self.events as an empty list
        self.events = []
        
        #fill events with all the events stored in eventLists' nested dictionaries
        for event in eventLists:
            self.events += [event[key] for key in event.keys()]
        
        #eventStrings is a list of strings identifying each event which can be relayed to the user
        eventStrings = [("Event starting at " + str(event.startTime) + ":00 on " + event.date) for event in self.events]
        
        #use tkinter dialog to ask user which event they would like to review, and record their choice in self.eventIndex instance variable
        eventIndexD = dialog.Dialog(title="What event would you like to review?", text="The following events are available to review:", strings=eventStrings, bitmap = 'questhead', default = 0, parent = self.parent)
        self.eventIndex = eventIndexD.num
        
        #comfortStrings is a list of strings describing each comfort index, stored at the appropriate comfort index within the list
        comfortStrings = ['Freezing', 'Uncomfortably Cold', 'Comfortable', 'Uncomfortably Warm', 'Excessively Hot']
        
        #use tkinter dialog to ask user how comfortable they felt in the reccommended outfit during their event, and record their choice in self.comfortSelection instance variable
        comfortSelectionD = dialog.Dialog(title="How did you feel during your event?", text="While wearing the reccommended outfit at your event, were you...", strings=comfortStrings, bitmap = 'questhead', default = 0, parent = self.parent)
        self.comfortSelection = comfortSelectionD.num
        
        #if the user did not record their comfort as "comfortable" see how they would have preferred to have dressed instead to improve future reccommendations
        if (self.comfortSelection != 2):
            
            #set outfitOptionStrings equal to an empty list
            outfitOptionStrings = []
            
            #if the user was too cold during their event, fill outfitOptionStrings with all warmer outfit options
            if (self.comfortSelection < 2) and (self.events[self.eventIndex].outfitIndex < 4):
                outfitOptionStrings = [outfit for outfit in self.outfitRange[self.events[self.eventIndex].outfitIndex+1:]]
            
            #if the user was too warm during their event, fill outfitOptionStrings with all cooler outfit options
            if (self.comfortSelection > 2) and (self.events[self.eventIndex].outfitIndex > 0):
                outfitOptionStrings = [outfit for outfit in self.outfitRange[:self.events[self.eventIndex].outfitIndex]]
            
            #if there are any alternative outfit options in outfitOptionStrings, ask the user what they feel they should have worn to be comfortable at their event    
            if (len(outfitOptionStrings) > 0):
                
                #if there is only one alternative outfit option, ask the user if they would have been more comfortable in a Yes/No format using tkinter dialog
                if (len(outfitOptionStrings) == 1):
                    comfortRefinementD = dialog.Dialog(title="In hindsight, what would you have needed to wear to be comfortable?", text=("Would you have been more comfortable in " + outfitOptionStrings[0] + "?"), strings=["Yes", "No"], bitmap = 'questhead', default = 0, parent = self.parent)
                
                #else use tkinter dialog to ask user which outfit option they would have been comfortable wearing
                else:
                    comfortRefinementD = dialog.Dialog(title="In hindsight, what would you have needed to wear to be comfortable?", text=("Would you have been more comfortable in one of the following?"), strings=(outfitOptionStrings + ["none of these"]), bitmap = 'questhead', default = 0, parent = self.parent)
                
                #if the user did not select the last option (which would mean there is no outfit they would have felt comfortable in) record their outfit choice as a new dataPoint in user.dataHistory using the addDataPoint() method to improve future reccommendations    
                if (comfortRefinementD.num != len(outfitOptionStrings)):
                    for i in range(len(self.outfitRange)):
                        if (self.outfitRange[i] == outfitOptionStrings[comfortRefinementD.num]):
                            fitIndex = i
                    self.user.addDataPoint(dataPoint(outfitIndex=fitIndex, comfortIndex=2, temp=self.events[self.eventIndex].temp, dressR=False, city=self.events[self.eventIndex].city, date=self.events[self.eventIndex].date, startTime=self.events[self.eventIndex].startTime))
            
        
        return
    
    #this method updates the user's userData instance to reflect their survey responses
    def updateUserData(self):
        
        #sets innerEventIndex equal to -1
        innerEventIndex = -1
        
        #utlizes one for loop nested within another for loop to identify which past event has been reviewed by the user and can thus be removed from the "needs review" category in their user data
        for outfit in self.needsReview.keys():
            for i in range(len(self.needsReview[outfit].keys())):
                innerEventIndex += 1
                if (innerEventIndex == self.eventIndex):
                    innerEventIndex = i
                    self.eventOutfitIndex = outfit
                    i = len(self.needsReview[outfit].keys())
        
        #sets event equal to the event reviewed by the user using the list pop() method, which also removes the event from the "needs review" category
        event = self.user.dataHistory[5][self.eventOutfitIndex].pop(innerEventIndex)
        
        #uses self.user.addDataPoint() method to record the event reviewed by the user at the newly specified comfort index
        self.user.addDataPoint(dataPoint(outfitIndex=self.eventOutfitIndex, comfortIndex=self.comfortSelection, temp=event.temp, dressR=False, city=event.city, date=event.date, startTime =event.startTime))
        
        return
    
Test = userData('Sam')
userEvent(Test)
#userReview(Test)