import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_frost_dates(zip_code: str):
    url = f"https://www.almanac.com/gardening/frostdates/zipcode/{zip_code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table", id="frostdates_table")
    if not table:
        raise ValueError("Could not find table with id `frostdates_table` on the page")

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("Table has no <tbody>")

    row = tbody.find("tr")
    if not row:
        raise ValueError("No <tr> found in tbody")

    cells = row.find_all("td")
    if len(cells) != 5:
        raise ValueError(f"Expected 5 <td> cells, but found {len(cells)}")

    last_spring_frost = cells[2].get_text(strip=True)
    first_fall_frost = cells[3].get_text(strip=True)
    growing_season = cells[4].get_text(strip=True)

    return {
        "last_spring_frost": last_spring_frost,
        "first_fall_frost": first_fall_frost,
        "growing_season": growing_season
    }

def process_zipcode(row, progress_lock, completed, total):
    zipcode = row['zipcode']
    
    try:
        frost_data = get_frost_dates(zipcode)
        row['last_spring_frost'] = frost_data['last_spring_frost']
        row['first_fall_frost'] = frost_data['first_fall_frost']
        row['growing_season'] = frost_data['growing_season']
        
        with progress_lock:
            completed[0] += 1
            if completed[0] % 100 == 0 or completed[0] == total:
                logger.info(f"Progress: {completed[0]}/{total} ({completed[0]/total*100:.1f}%) - Last: {zipcode}")
        
        return row, None
    except Exception as e:
        logger.error(f"Error fetching data for {zipcode}: {e}")
        row['last_spring_frost'] = ''
        row['first_fall_frost'] = ''
        row['growing_season'] = ''
        
        with progress_lock:
            completed[0] += 1
            if completed[0] % 100 == 0 or completed[0] == total:
                logger.info(f"Progress: {completed[0]}/{total} ({completed[0]/total*100:.1f}%) - Last: {zipcode}")
        
        return row, str(e)

if __name__ == "__main__":
    input_file = "data/phzm_us_zipcode_2023.csv"
    output_file = "data/phzm_us_zipcode_2023.csv"
    max_workers = 10
    
    logger.info(f"Starting frost date collection with {max_workers} threads")
    
    rows = []
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) + ['last_spring_frost', 'first_fall_frost', 'growing_season']
        
        for row in reader:
            rows.append(row)
    
    total = len(rows)
    logger.info(f"Loaded {total} zipcodes to process")
    
    progress_lock = Lock()
    completed = [0]
    results = [None] * total
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(process_zipcode, row, progress_lock, completed, total): i 
            for i, row in enumerate(rows)
        }
        
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            result_row, error = future.result()
            results[index] = result_row
            if error:
                error_count += 1
    
    logger.info(f"Completed processing. Errors: {error_count}/{total}")
    logger.info(f"Writing results to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info("Done!")