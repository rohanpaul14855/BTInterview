
# coding: utf-8

# In[39]:


"""
Exploratory analysis of SSF database
Employee turnover analysis

"""
import datetime
import pyodbc
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import f_oneway as anova


#Connect to MS SQL server
connection = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                            "Server=DESKTOP-KLSCAVN\SQLEXPRESS;"
                            "Database=SSF_PM_DB;"
                            "Trusted_Connection=yes;")

date_cols = ['Emphire', 'Empexit', 'Empcertdate','Empbirthday', 'EmpRemoteDate',
             'EmpPasswordLastChanged','Created', 'LastUpdated']

employee_df = pd.read_sql("SELECT * FROM employee", connection, 
                          parse_dates=date_cols, index_col='ID')


# number of days employees are employed
los = employee_df[['Empexit', 'Emphire']]
los['length'] = (los['Empexit'] - los['Emphire']).apply(lambda x: x.days)
#filter missing values
los = los[los['length'] == los['length']]


#plot
sns.distplot([k for k in los['length'] if k > 0])
plt.xlabel('Length of time employed (days)')
plt.ylabel('Frequency')
plt.title('Employment length')
plt.show()
plt.close()

#High turnover employees by department (employed less than 1 yr)
turnoverIDs = los[los['length'] < 365].index
depts = list(employee_df.loc[turnoverIDs]['Empdept'])
departments = sorted(list(set(depts)))
leave_count_by_dept = [depts.count(k) for k in departments]
num_ppl_by_dept = [len(employee_df[employee_df['Empdept'] == k].index) for k in departments]

plt.bar(departments, [i/j if j > 0 else 0 for i,j in zip(leave_count_by_dept, num_ppl_by_dept)])
plt.xlabel('Department Code')
plt.ylabel('Leave Frequency')
plt.title('Leave Frequency by department')
plt.show()

emp_age = datetime.datetime.now() - employee_df.loc[turnoverIDs]['Empbirthday']
ages = list(filter(lambda x: x == x, [k.days for k in emp_age])) #filter nans and convert ages to days
sns.distplot([k/365 for k in ages]) #convert ages to years
plt.xlabel('Age (years)')
plt.ylabel('Frequency of leaving')
plt.title('Frequency of termination by age group')
plt.show()

#Average age by department
age_by_dept = employee_df[['Empdept', 'Empbirthday']]
age_by_dept = age_by_dept[age_by_dept['Empbirthday'] == age_by_dept['Empbirthday']] #filter nans
age_by_dept['age'] = datetime.datetime.now() - age_by_dept['Empbirthday']
age_by_dept['age'] = age_by_dept['age'].apply(lambda x: x.days/365)
sns.boxplot(x='Empdept', y='age', data=age_by_dept)
plt.xlabel('Department')
plt.ylabel('Employee Age')
plt.title('Employee Age by Department')
plt.show()


f_stat, p_stat = anova(age_by_dept[age_by_dept['Empdept'] == 0]['age'], 
                       age_by_dept[age_by_dept['Empdept'] == 1]['age'], 
                       age_by_dept[age_by_dept['Empdept'] == 2]['age'], 
                       age_by_dept[age_by_dept['Empdept'] == 3]['age'], 
                       age_by_dept[age_by_dept['Empdept'] == 4]['age'], 
                       age_by_dept[age_by_dept['Empdept'] == 5]['age'],
                       age_by_dept[age_by_dept['Empdept'] == 12]['age'],
                       age_by_dept[age_by_dept['Empdept'] == 20]['age'],  
                       age_by_dept[age_by_dept['Empdept'] == 21]['age'],
                       age_by_dept[age_by_dept['Empdept'] == 22]['age'],
                       age_by_dept[age_by_dept['Empdept'] == 24]['age'])
print(f_stat, p_stat)

connection.close()


# In[31]:


'''
Exploratory analysis of SSF database
Analysis of CPE and employee performance
'''
#SQL connection interface
connection = pyodbc.connect('Driver={SQL Server Native Client 11.0};'
                            'Server=DESKTOP-KLSCAVN\SQLEXPRESS;'
                            'Database=SSF_PM_DB;'
                            'Trusted_Connection=yes;')

date_cols = ['Emphire', 'Empexit', 'Empcertdate','Empbirthday', 'EmpRemoteDate',
             'EmpPasswordLastChanged','Created', 'LastUpdated']

sum_query = '''
SELECT CpeEmpID, SUM(CpeHours) as TrainHrs
FROM CPE
GROUP BY CpeEmpID
ORDER BY CpeEmpID'''

WIP_query = '''
SELECT WempID, SUM(Wbilled) as Billed 
FROM WIP
GROUP BY WempID
ORDER BY WempID'''

employee_query = '''
SELECT ID, EmpCPEhours, Empbirthday
FROM Employee
'''

#CPE Training vs Billables
cpe_df = pd.read_sql(sum_query, connection, index_col='CpeEmpID')
wip_df = pd.read_sql(WIP_query, connection, index_col='WempID')
employee_df = pd.read_sql(employee_query, connection, index_col='ID', 
                          parse_dates=['Empbirthday'])

master = cpe_df.join(wip_df, how='inner').join(employee_df, how='inner')
master['age'] = datetime.datetime.now() - master['Empbirthday']
master['age'] = master['age'].apply(lambda x: x.days/365)
master['training'] = master['TrainHrs']/master['age']
sns.jointplot(x='training', y='Billed', data=master, kind='reg')
plt.show()

#Billables by CPE training category
cpehrs_by_category = '''
SELECT CpeCategory, SUM(CpeHours) as TrainHrs
FROM CPE INNER JOIN Employee on CPE.CpeEmpID=Employee.ID
GROUP BY CpeCategory
'''
cpebilled_by_category = '''
SELECT CpeCategory, SUM(w.Wbilled) as Billed
FROM CPE JOIN WIP w ON CPE.CpeEmpID=w.WempID
GROUP BY CpeCategory
'''
cpehrsbycat_df = pd.read_sql(cpehrs_by_category, connection)
cpebilledbycat_df = pd.read_sql(cpebilled_by_category, connection)
master_billables = pd.merge(cpehrsbycat_df, cpebilledbycat_df, on='CpeCategory')
master_billables['Billables/Training Hours'] = master_billables['Billed']/master_billables['TrainHrs']
master_billables = master_billables[master_billables.index != 12]

get_ipython().magic('matplotlib notebook')

sns.barplot(x='CpeCategory', y='Billables/Training Hours', data=master_billables)
plt.xticks(rotation=30)
plt.title('Billables by CPE Category')
plt.show()


get_ipython().magic('matplotlib inline')

#Leads analysis

leads_by_employee_query = '''
SELECT LDEmpId, COUNT(ldempid) as NumLeads
FROM Leads
GROUP BY LDEmpId'''

leadsbyemp_df = pd.read_sql(leads_by_employee_query, connection, index_col='LDEmpId')
master_leads = leadsbyemp_df.join(master, how='inner')
master_leads
sns.jointplot(x='training', y='NumLeads', data=master_leads)
plt.show()

connection.close()

