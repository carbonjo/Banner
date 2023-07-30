# Required Libraries
import time
import pandas as pd
import getpass
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

def initiate_driver():
    option = webdriver.ChromeOptions()
    option.add_argument("--headless")
    driver = webdriver.Chrome(executable_path="/Users/carbonjo/Desktop/chromedriver", options=option)
    return driver

def login(driver):
    # This is the log in page for banner
    driver.get("https://banner.buffalostate.edu/pls/PROD/twbkwbis.P_WWWLogin")

    # Get user_name and password interactively
    user_name = getpass.getpass("user name: ")
    password = getpass.getpass("password: ")

    # Now log in with credentials
    element = driver.find_element_by_id("UserID")
    element.send_keys(user_name)
    element = driver.find_element_by_id("PIN")
    element.send_keys(password)
    element.send_keys(Keys.RETURN)
    
    # Go to the Faculty and Staff page
    driver.find_element_by_link_text('Faculty and Staff').click()

def navigate_to_course(driver, TERM, CRN):
    dic = {}

    driver.find_element_by_link_text('Select Term').click()
    driver.find_element_by_name('term').send_keys(TERM)

    # The submit button is the second class="dedefault"
    driver.find_elements_by_class_name("dedefault")[2].click()

    driver.find_element_by_link_text('Summary Class List').click()
    driver.find_element_by_link_text('Enter CRN Directly').click()

    element = driver.find_element_by_id("crn_input_id")
    element.send_keys(CRN)
    element.send_keys(Keys.RETURN)

    # Create a key in the dictionary with the course name and crn
    dic[(TERM, CRN)] = pd.read_html(driver.page_source)[8]
    return dic

def get_emails(driver):
    # Extract emails before returning to menu
    email_list = driver.find_element_by_link_text('Email class').get_attribute("href").split('?Bcc=')[1].split(';')
    return email_list

def process_data(dic):
    # Fixes the column names and keeps only name and id
    for k in dic.keys():
        dic[k] = dic[k][:]
        dic[k] = dic[k].iloc[:,[2,3]]
        dic[k].rename(columns=dic[k].iloc[0], inplace=True)
        dic[k].drop([0], axis=0, inplace=True)

    # Create a list of students    
    students = []
    for k in dic.keys():
        students += list(dic[k]['Student Name'].values)
    students = list(set(students))        

    nid = []
    for k in dic.keys():
        nid += zip(list(dic[k]['Student Name'].values), list(dic[k]['ID'].values))
    nid = dict(list(set(nid)))        

    # Create a DataFrame with the Banner ID and the email
    Students_courses = pd.DataFrame(list(nid.items()), columns=['Student Name', 'Banner ID'])
    Students_courses.set_index('Student Name', inplace=True)
    return Students_courses

def get_course(CRN, TERM):
    driver = initiate_driver()
    login(driver)
    dic = navigate_to_course(driver, TERM, CRN)
    email_list = get_emails(driver)
    
    # Return to menu for another search
    driver.find_element_by_link_text('RETURN TO MENU').click()
    print('got ', CRN)
    time.sleep(2)
    driver.close()

    Students_courses = process_data(dic)
    
    if len(email_list) == len(Students_courses):
        Students_courses['Email'] = email_list
    else:
        print("Mismatch in number of students and emails.")

    print("DONE!")
    return Students_courses
