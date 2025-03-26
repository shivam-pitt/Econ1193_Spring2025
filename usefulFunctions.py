import os
import json
import requests
import pandas as pd
import typing
from matplotlib import pyplot as plt

def readJSONfile(fname):
    """
    Reads and parses a JSON file.

    Parameters:
    fname (str): The path to the JSON file as a string.

    Returns:
    dict: The parsed JSON content if the file is valid.
    str: An error message if the input is not a string, the file does not exist, 
         or the file does not contain valid JSON.

    Errors:
    - If fname is not a string, returns 'input should be a string'.
    - If the file does not exist, returns 'file does not exist'.
    - If the file content is not valid JSON, returns 'The file does not contain valid json'.
    """
    # First, check if fname is a string
    if type(fname) == str:  # the input is of type string 
        
        # Second, check if a file of the name fname exists
        if os.path.exists(fname):  # a file with the name stored in fname exists
            
            # Open the file
            with open(fname, 'r') as f:  # Use 'with' to ensure the file is properly closed
                content = f.read()  # Read file content
            
            # Third, verify that the content is valid JSON
            try:
                json_object = json.loads(content)  # Try converting the content to a dictionary
                return json_object
            except ValueError:  # Error occurred, it wasn't a valid JSON file
                return 'The file does not contain valid json'
        
        else:  # A file with the name stored in fname does not exist
            return 'file does not exist'
    
    else:  # The input is not of type string
        return 'input should be a string'


# import requests
# import json

def inflation(lag=0,varname='CUUR0000SA0',*,digits=2):
    
    """
    Computes the percent change in the level of prices (inflation) over a 12-month period,
    starting from '12 + lag' months ago and ending 'lag' months ago.

    Parameters:
    ----------
    lag : int, optional
        An integer indicating the lag in months (default is 0). 
        Must be between 0 and 12, inclusive.
    
    varname : str, optional
        A string representing the variable name for the BLS API request 
        (default is 'CUUR0000SA0', which represents the Consumer Price Index for All Urban Consumers).

    Returns:
    -------
    float
        The calculated inflation rate as a percentage.

    str
        An error message if input validation fails or the API request is unsuccessful.

    Notes:
    ------
    - The function retrieves data from the U.S. Bureau of Labor Statistics (BLS) API.
    - The API response is parsed to extract the most recent and past values for computing inflation.
    - If the API request fails, the function returns the error message from the API.

    Example:
    --------
    >>> inflation(3)
    Inflation in the period starting 3 months ago and ending 15 months ago was 2.3%
    2.3
    """    
    # Step 0: Check inputs
    if type(lag) != int:
        return 'lag should be an integer'
    if lag>12 or lag<0:
        return 'lag should be an integer between 0 and 12, including.'
    if type(varname) != str:
        return 'variable name should be a string (or left out)'
    
    # Step 1: API call
    base_url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    url = base_url + varname
    r = requests.get(url).json()
    
    # Step 2: Check whether the GET request was successful
    if r['status'] != 'REQUEST_SUCCEEDED':
        return r['message']
  
    
    # Step 3: Compute inflation
    new = float(r['Results']['series'][0]['data'][lag]['value'])
    old = float(r['Results']['series'][0]['data'][12+lag]['value'])
    
    change = round((new/old - 1)*100,digits)
    print('Inflation in the period starting ', lag, 'months ago and ending', 12+lag, 'months ago was ',round(change,1),'%')
    return change

def multiSeries(varList, myKey, first='2018', last='2023',*,verbose=True):
    """
    Fetches time series data from the U.S. Bureau of Labor Statistics (BLS) API.

    Parameters:
        varList (list of str): A list of BLS series IDs to request.
        myKey (str): BLS API key for authentication.
        first (str, optional): Starting year of the data request. Defaults to '2018'.
        last (str, optional): Ending year of the data request. Defaults to '2023'.

    Returns:
        pd.DataFrame: A DataFrame containing the requested time series data with:
                      - 'year' and 'period' as index columns
                      - Series values as separate columns

    Raises:
        ValueError: If the API request fails or the response is malformed.
    """

    base_url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    headers = {'Content-type': 'application/json'}

    parameters = {
        "seriesid": varList,
        "startyear": str(first),
        "endyear": str(last),
        "catalog": True,
        "calculations": False,
        "annualaverage": False,
        "aspects": False,
        "registrationkey": myKey
    }

    response = requests.post(base_url, data=json.dumps(parameters), headers=headers)

    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}")

    json_data = response.json()

    if 'Results' not in json_data or 'series' not in json_data['Results']:
        raise ValueError("Invalid API response format")

    series_data = json_data['Results']['series']
    
    # Create an empty DataFrame
    new_df = pd.DataFrame(columns=['year', 'period'])

    for series in series_data:
        series_id = series.get('seriesID', 'Unknown')
        data = series.get('data', [])
        
        if verbose :
            if not data:
                print(f"Series '{series_id}' does not exist or contains no data.")
                continue

            print(f"Series '{series_id}' retrieved with {len(data)} observations.")

        # Convert the API response to a DataFrame
        current_df = pd.DataFrame(data)[['year', 'period', 'value']].astype({'value': 'float64'})
        current_df.rename(columns={'value': series_id}, inplace=True)

        # Merge into the main DataFrame
        new_df = new_df.merge(current_df, on=['year', 'period'], how='outer')

    return new_df

def fetch_bls_data(myKey: str, series_ids: list[str], start: str, end: str) -> dict:
    base_url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    headers = {'Content-type': 'application/json'}
    parameters = {
        "seriesid": series_ids,
        "startyear": start,
        "endyear": end,
        "catalog": True,
        "calculations": False,
        "annualaverage": False,
        "aspects": False,
        "registrationkey": myKey
    }
    response = requests.post(base_url, data=json.dumps(parameters), headers=headers)
    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}")
    json_data = response.json()
    if 'Results' not in json_data or 'series' not in json_data['Results']:
        raise ValueError("Invalid API response format")
    return json_data['Results']['series']

def parse_series_data(series_data: list[dict], seriesDict: dict[str, str], verbose: bool = False) -> pd.DataFrame:
    df = pd.DataFrame(columns=['year', 'period'])
    for series in series_data:
        series_id = series.get('seriesID', 'Unknown')
        data = series.get('data', [])
        if verbose:
            print(f"Series '{series_id}' retrieved with {len(data)} observations.")
        if not data:
            continue
        current_df = pd.DataFrame(data)[['year', 'period', 'value']].astype({'value': 'float64'})
        current_df.rename(columns={'value': series_id}, inplace=True)
        df = df.merge(current_df, on=['year', 'period'], how='outer')
    return df.rename(columns=seriesDict)

def prepare_dataframe(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    df['month'] = df['period'].apply(lambda x: int(x.replace('M', '')))
    df['time_label'] = df['year'].astype(str) + '-' + df['month'].astype(str)
    df = df.sort_values(by=['year', 'month'])
    df['change'] = df[target_col].pct_change(periods=12) * 100
    return df

def plot_changes(df: pd.DataFrame, label: str):
    plt.figure(figsize=(12, 5))
    plt.plot(df['time_label'], df['change'], label=label, marker='o', linestyle='-')
    plt.gca().set_facecolor((0.7, 0.85, 1, 0.2))
    plt.ylabel("Percentage Change (%)")
    plt.title(label)
    plt.legend(loc='upper left')

    if len(df['time_label']) >= 12:
        plt.xticks(ticks=range(11, len(df['time_label']), 3),
                   labels=df['time_label'].iloc[11::3],
                   rotation=45)

    last_idx = df['change'].last_valid_index()
    if last_idx is not None:
        x_val = df['time_label'][last_idx]
        y_val = df['change'][last_idx]
        plt.annotate(f"{y_val:.2f}%", (x_val, y_val),
                     textcoords="offset points", xytext=(10, -10),
                     ha='left', fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))

    plt.grid(axis='y', color='black', linestyle='--', linewidth=0.7, alpha=0.3)
    plt.yticks(range(int(df['change'].min()) - 2, int(df['change'].max()) + 3, 2))
    plt.figtext(0.1, -0.1, "Source: Bureau of Labor Statistics and own calculations",
                ha='left', fontsize=10, style='italic')
    plt.show()

def BLS(myKey: str, seriesDict: dict[str, str] = {"CUUR0000SA0": "CPI-U"}, *, 
        first: str = '2020', last: str = '2025', 
        verbose: bool = False, display: bool = False) -> pd.DataFrame | None:
    """
    Fetches and optionally plots time series data from the U.S. Bureau of Labor Statistics (BLS) API.

    Parameters:
        myKey (str): Your BLS API key required for authentication.
        seriesDict (Dict[str, str], optional): A dictionary mapping BLS series IDs to user-defined column names.
            Example: {"CUUR0000SA0": "CPI-U"}
            Only the first entry will be used for inflation calculations and plotting.
        first (str, optional): Start year of the data request (e.g., '2020'). Defaults to '2020'.
        last (str, optional): End year of the data request (e.g., '2025'). Defaults to '2025'.
        verbose (bool, optional): If True, prints status messages for each series. Defaults to False.
        display (bool, optional): If True, displays a plot of the 12-month percent change for the selected series. Defaults to False.

    Returns:
        pd.DataFrame or None: 
            - If display=False: returns a DataFrame with columns: 'year', 'period', series values, 'month', 'time_label', and 'change'.
            - If display=True: displays a plot and returns None.

    Raises:
        ValueError: If the API request fails or the response format is invalid.
    """    
    series_ids = list(seriesDict.keys())
    series_names = list(seriesDict.values())
    target_col = series_names[0]

    series_data = fetch_bls_data(myKey, series_ids, first, last)
    df = parse_series_data(series_data, seriesDict, verbose)
    df = prepare_dataframe(df, target_col)
    
    if display:
        plot_changes(df, target_col)
        return None
    return df

print("Functions uploaded: readJSONfile, inflation, BLS")