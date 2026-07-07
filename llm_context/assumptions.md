Unknown

How should multiple trades within one second be handled?

Current assumption

Use latest trade within that second.

Reason

Assignment does not specify.



Current assumptions

Use nearest expiry.
Ignore brokerage.
Ignore slippage.
Ignore taxes.
Maximum position = 1.
End-of-day positions closed using final available market price.
Latest available market price is used whenever exact timestamps are unavailable.
Multiple ticks within the same second require a deterministic execution policy (currently assumed to use the latest trade within that second if strategy is evaluated once per second).

Also mention

These assumptions were made because the assignment specification leaves these details unspecified.

Assignment specification details already given:
We have one month of data here https://drive.google.com/file/d/1RvvX4jacGmhDNZ26LRjLqnhtIgkZowgq/view?usp=sharing



In the allData folder there are folders for each trading date. NSE_20221101 refers to data of 20221101 , NSE_20221102 for 20221102 and so on.


Each dated folder has two folders, options and futures. We will trade on options using options and futures data.


In the Options folder there are numerous files. Each file represents data for that day for that instrument. The file name ( without the csv extension is the instrument's name).  The instrument can be broken down into  its underlier , expiry date , strike price and option type. 


For eg




File

Underlier

Expiry Date

( Next 6 characters) 

Strike Price   ( Next character till first letter)

Option Type (Last 2 characters)

NIFTY22110314550PE.csv


NIFTY

221103

14550

PE

BANKNIFTY22112443200CE.csv


BANKNIFTY

221124

43200

CE

FINNIFTY22110719500CE.csv


FINNIFTY

221107

19500

CE



Each file has 5 columns. Date , Time , Price , Volume , Open Interest


The futures folder has files like NIFTY-I.csv , NIFTY-II.csv , NIFTY-III.csv and similarly for BANKNIFTY and FINNIFTY. We will only focus on -I.csv


Task


Create a backtest for a Simple Trading Strategy


What is a backtest : A backtest in a trading strategy is a process to measure performance of the trading strategy. It is typically agnostic to the strategy and only needs the orders as an input. It allows monitoring of pnl across time.


Simple Trading Strategy 
We only trade instruments which are expiring the closest to the current date. So for example if we are simulating for 20221101 , for NIFTY we only trade those instruments with files names as NIFTY221103*.csv. 
The maximum position we take in any one instrument is 1.
For each date from the start go through the whole day serially.
At every 1 sec, select the strike closest to the futures price ( mentioned in NIFTY-I.csv or BANKNIFTY-I.csv)
Select Buy both the CE and PE at the mentioned price.
Buy them and hold till the futures price changes that you need to change the strike. 
At that point, sell these instruments and buy the new instruments with the new strike.
At day end close all the positions
Repeat this process for the days
Do this process for both NIFTY and BANKNIFTY
You should generate backtesting results such as mark to market pnl at all times, instruments in which position is held at any time and such details
Try to think out of the box on how you can make this a flexible setup where different strategies can be easily plugged in.
Show some cumulative plots for pnl and other metrics. 
Please note the objective is not to maximize returns or make it profitable here.
You are free to use any AI tools.