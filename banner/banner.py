# Required Libraries
import time
import pandas as pd
import getpass
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initiate_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    return driver

########

def login(driver):
    # This is the log in page for banner
    driver.get("https://banner.buffalostate.edu/pls/PROD/twbkwbis.P_WWWLogin")

    # Get user_name and password interactively
    user_name = getpass.getpass("user name: ")
    password = getpass.getpass("password: ")

    # Now log in with credentials
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserID")))
    element.send_keys(user_name)
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "PIN")))
    element.send_keys(password)
    element.send_keys(Keys.RETURN)
    
    # Go to the Faculty and Staff page
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Faculty and Staff'))).click()

def navigate_to_course(driver, TERM, CRN):
    dic = {}

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Select Term'))).click()
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'term')))
    element.send_keys(TERM)

    # The submit button is the second class="dedefault"
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "dedefault")))[2].click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Summary Class List'))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Enter CRN Directly'))).click()

    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "crn_input_id")))
    element.send_keys(CRN)
    element.send_keys(Keys.RETURN)

    # Create a key in the dictionary with the course name and crn
    dic[(TERM, CRN)] = pd.read_html(driver.page_source)[8]
    return dic

def get_emails(driver):
    # Extract emails before returning to menu
    email_list = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Email class'))).get_attribute("href").split('?Bcc=')[1].split(';')
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
    TERM=TERM.capitalize()
    print(TERM)
    driver = initiate_driver()
    driver.implicitly_wait(10)  # waits for 10 seconds
    login(driver)
    dic = navigate_to_course(driver, TERM, CRN)
    print(dic)
    email_list = get_emails(driver)
    
    # Return to menu for another search
    #driver.find_element_by_link_text('RETURN TO MENU').click()
    driver.find_element(By.LINK_TEXT,'RETURN TO MENU').click()

    print('got ', CRN)
    time.sleep(2)
    driver.close()

    Students_courses = process_data(dic)
    Students_courses=Students_courses.sort_index()
    
    if len(email_list) == len(Students_courses):
        Students_courses['Email'] = email_list
    else:
        print("Mismatch in number of students and emails.")

    print("DONE!")
    return Students_courses


def get_courses_matrix(crn_list, term):
    # Initialize an empty dictionary to store student data
    student_data = {}

    # Initiate the driver and log in
    driver = initiate_driver()
    login(driver)

    # Iterate through the CRNs and retrieve course data
    for crn in crn_list:
        dic = navigate_to_course(driver, term, crn)
        email_list = get_emails(driver)
        #driver.find_element_by_link_text('RETURN TO MENU').click()
        driver.find_element(By.LINK_TEXT,'RETURN TO MENU').click()

        print('got ', crn)

        Students_courses = process_data(dic)
        Students_courses = Students_courses.sort_index()
        if len(email_list) == len(Students_courses):
            Students_courses['Email'] = email_list
        else:
            print("Mismatch in number of students and emails.")

        # Iterate through the students in the course
        for student_name, row in Students_courses.iterrows():
            student_id = row['Banner ID']
            email = row['Email']
            # If the student name is not in the dictionary, add them
            if student_name not in student_data:
                student_data[student_name] = {'Banner ID': student_id, 'email': email, 'CRNs': {crn: 1}}
            else:
                # Otherwise, update the student's CRN entry
                student_data[student_name]['CRNs'][crn] = 1

    # Close the driver
    driver.close()

    # Create a DataFrame to store the matrix
    matrix_data = []
    for student_name, data in student_data.items():
        row_data = {'Student Name': student_name, 'Banner ID': data['Banner ID'], 'Email': data['email']}
        row_data.update({crn: data['CRNs'].get(crn, 0) for crn in crn_list})
        matrix_data.append(row_data)

    matrix_df = pd.DataFrame(matrix_data)
    matrix_df.set_index('Student Name', inplace=True)

    # Add the "Total" column, summing the values across the CRN columns
    matrix_df['Total'] = matrix_df[crn_list].sum(axis=1)

    # Calculate the sum for each CRN column (excluding "Banner ID" and "Email")
    enrollment_row = {'Banner ID': '', 'Email': ''}
    enrollment_row.update({crn: matrix_df[crn].sum() for crn in crn_list})
    enrollment_row['Total'] = matrix_df['Total'].sum()

    # Append the "Enrollment" row to the DataFrame
    enrollment_df = pd.DataFrame([enrollment_row], index=['Enrollment'])
    matrix_df = pd.concat([enrollment_df, matrix_df])

    # Reorder the columns to place the "Total" column at the end
    matrix_df = matrix_df[['Banner ID', 'Email'] + crn_list + ['Total']]

    print("DONE!")
    return matrix_df

def banner_test(x):
    print(x)